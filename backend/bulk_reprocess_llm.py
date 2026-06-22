"""One-off: re-run LLM trigger evaluation + scores for all completed interactions.

Repopulates interaction_llm_trigger_cache (emotion/process/policy) and recomputes
InteractionScore using the now-working Gemini provider. Run from backend/ with the
vocalmind_gpu interpreter and the same env as the native backend.
"""
import asyncio

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import engine
from app.core.interaction_processing import ensure_organization_policies_from_source
from app.llm_trigger.scoring import compute_scores
from app.llm_trigger.service import evaluate_interaction_triggers
from app.models.interaction import Interaction
from app.models.interaction_score import InteractionScore
from app.models.organization import Organization
from app.models.enums import ProcessingStatus


async def main() -> None:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        org_slugs = {
            o.id: o.slug
            for o in (await session.exec(select(Organization))).all()
        }
        interactions = (
            await session.exec(
                select(Interaction).where(
                    Interaction.processing_status == ProcessingStatus.completed
                )
            )
        ).all()
        print(f"Reprocessing LLM triggers for {len(interactions)} completed interactions")

        ok = degraded = failed = 0
        for inter in interactions:
            slug = org_slugs.get(inter.organization_id)
            try:
                report = await asyncio.wait_for(
                    evaluate_interaction_triggers(
                        session=session,
                        interaction_id=inter.id,
                        org_filter=slug,
                        requester_organization_id=inter.organization_id,
                        force_rerun=True,
                    ),
                    timeout=600,
                )
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"  FAIL {inter.id}: {exc}")
                await session.rollback()
                continue

            await ensure_organization_policies_from_source(session, inter.organization_id)
            scores = compute_scores(report)
            existing = (
                await session.exec(
                    select(InteractionScore).where(
                        InteractionScore.interaction_id == inter.id
                    )
                )
            ).first()
            target = existing or InteractionScore(interaction_id=inter.id)
            target.overall_score = scores.overall
            target.empathy_score = scores.empathy
            target.policy_score = scores.policy
            target.resolution_score = scores.resolution
            target.was_resolved = scores.was_resolved
            if target.total_silence_seconds is None:
                target.total_silence_seconds = 0.0
            if target.avg_response_time_seconds is None:
                target.avg_response_time_seconds = 1.0
            session.add(target)
            await session.commit()

            is_degraded = "DEGRADED" in (
                report.process_adherence.justification + report.emotion_shift.root_cause
            )
            degraded += int(is_degraded)
            ok += 1
            flag = " [DEGRADED]" if is_degraded else ""
            print(
                f"  OK {inter.id} {slug}: policy={scores.policy*100:.0f} "
                f"emp={scores.empathy*100:.0f} res={scores.resolution*100:.0f} "
                f"overall={scores.overall*100:.0f}{flag}"
            )

        print(f"\nDone. ok={ok} degraded={degraded} failed={failed}")


if __name__ == "__main__":
    asyncio.run(main())
