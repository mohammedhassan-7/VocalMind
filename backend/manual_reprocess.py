import asyncio
from sqlmodel import select, delete
from app.api.deps import get_db
from app.models.interaction import Interaction
from app.models.organization import Organization
from app.models.interaction_score import InteractionScore
from app.llm_trigger.service import evaluate_interaction_triggers
from app.llm_trigger.scoring import compute_scores
from app.core.interaction_processing import ensure_organization_policies_from_source

async def main():
    async for session in get_db():
        # Get calls for NexaLink (since the screenshot shows Priya, Hannah, Marcus)
        org_result = await session.exec(select(Organization).where(Organization.slug == "nexalink"))
        org = org_result.first()
        if not org:
            print("NexaLink not found")
            return
            
        stmt = select(Interaction).where(Interaction.organization_id == org.id)
        interactions = (await session.exec(stmt)).all()
        
        for interaction in interactions:
            print(f"\nProcessing {interaction.id}...")
            # Clean old scores
            await session.exec(delete(InteractionScore).where(InteractionScore.interaction_id == interaction.id))
            
            try:
                report = await asyncio.wait_for(
                    evaluate_interaction_triggers(
                        session=session,
                        interaction_id=interaction.id,
                        org_filter=org.slug,
                        requester_organization_id=interaction.organization_id,
                        force_rerun=True,
                    ),
                    timeout=600,
                )
            except Exception as e:
                print(f"FAILED on {interaction.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
                
            if not report:
                print(f"No report for {interaction.id}")
                continue
                
            await ensure_organization_policies_from_source(session, org.id)

            # Recompute scores via the shared scorer (0.0–1.0 scale, sets was_resolved)
            # so this script matches the production pipeline exactly.
            scores = compute_scores(report)
            new_score = InteractionScore(
                interaction_id=interaction.id,
                overall_score=scores.overall,
                empathy_score=scores.empathy,
                policy_score=scores.policy,
                resolution_score=scores.resolution,
                total_silence_seconds=0.0,
                avg_response_time_seconds=1.0,
                was_resolved=scores.was_resolved,
            )
            session.add(new_score)
            await session.commit()
            print(
                f"SUCCESS: Policy={scores.policy * 100:.0f}% "
                f"Empathy={scores.empathy * 100:.0f}% "
                f"Res={scores.resolution * 100:.0f}% "
                f"Overall={scores.overall * 100:.0f}% "
                f"resolved={scores.was_resolved}"
            )

if __name__ == "__main__":
    asyncio.run(main())
