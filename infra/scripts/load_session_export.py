#!/usr/bin/env python3
"""Load NexaLink telecom dataset (CALL_01–CALL_20) into Postgres and bind org users."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = Path(__file__).resolve().parent / "session_export.json"
sys.path.insert(0, str(REPO_ROOT / "backend"))

from sqlmodel import select  # noqa: E402
from sqlmodel.ext.asyncio.session import AsyncSession  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.llm_trigger.schemas import InteractionLLMTriggerReport  # noqa: E402
from app.llm_trigger.service import CACHE_SCHEMA_VERSION  # noqa: E402
from app.models.enums import ProcessingStatus, SpeakerRole, UserRole  # noqa: E402
from app.models.interaction import Interaction  # noqa: E402
from app.models.interaction_score import InteractionScore  # noqa: E402
from app.models.llm_trigger_cache import InteractionLLMTriggerCache  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.transcript import Transcript  # noqa: E402
from app.models.user import User as UserModel  # noqa: E402
from app.models.utterance import Utterance  # noqa: E402
from app.models.emotion_event import EmotionEvent  # noqa: E402
from app.models.policy import PolicyCompliance  # noqa: E402
from app.core.policy_violation_mapping import (  # noqa: E402
    ViolationMappingInput,
    derive_violation_specs,
    ensure_organization_policies_from_source,
    persist_policy_violations,
)
from app.core.knowledge_seed import ensure_organization_knowledge_from_source  # noqa: E402

MANAGER_EMAIL = "operations@vocalmind.dev"
MANAGER_PASSWORD = "NexaLink2026!"
AGENT_PASSWORD = "NexaLink2026!"
MANAGER_NAME = "NexaLink Operations"

# Dedicated org for the 20-call telecom dataset (separate from demo `nexalink` org).
DATASET_ORG_NAME = "NexaLink Operations"
DATASET_ORG_SLUG = "nexalink-operations"

AGENT_PROFILES: dict[str, str] = {
    "Priya": "agent.priya@nexalink.com",
    "Daniel": "agent.daniel@nexalink.com",
    "Marcus": "agent.marcus@nexalink.com",
    "Aisha": "agent.aisha@nexalink.com",
    "Hannah": "agent.hannah@nexalink.com",
}

DATASET_STORAGE_PREFIX = "nexalink-operations/telecom-dataset"
DATASET_AUDIO_BUCKET = "recordings"
LOCAL_AUDIO_DIR = REPO_ROOT / "storage" / "audio" / "nexalink"
CALL_AUDIO_RE = re.compile(r"CALL_(0[1-9]|1[0-9]|20)_", re.I)


def _attribution_to_snake(item: dict[str, Any]) -> dict[str, Any]:
    policy_ref = item.get("policyReference") or item.get("policy_reference")
    snake_ref = None
    if policy_ref:
        snake_ref = {
            "source": policy_ref.get("source"),
            "reference": policy_ref.get("reference"),
            "clause": policy_ref.get("clause"),
            "doc_type": policy_ref.get("docType") or policy_ref.get("doc_type"),
            "doc_id": policy_ref.get("docId") or policy_ref.get("doc_id"),
            "rule_id": policy_ref.get("ruleId") or policy_ref.get("rule_id"),
            "step_number": policy_ref.get("stepNumber") or policy_ref.get("step_number"),
            "severity": policy_ref.get("severity"),
            "policy_ref": policy_ref.get("policyRef") or policy_ref.get("policy_ref") or [],
            "version": policy_ref.get("version"),
            "category": policy_ref.get("category"),
            "provenance": policy_ref.get("provenance"),
        }
    span = item.get("evidenceSpan") or item.get("evidence_span")
    snake_span = None
    if span:
        snake_span = {
            "utterance_index": span.get("utteranceIndex") or span.get("utterance_index"),
            "speaker": span.get("speaker"),
            "quote": span.get("quote"),
            "timestamp": span.get("timestamp"),
            "start_seconds": span.get("startSeconds") or span.get("start_seconds"),
            "end_seconds": span.get("endSeconds") or span.get("end_seconds"),
        }
    return {
        "attribution_id": item.get("attributionId") or item.get("attribution_id"),
        "family": item.get("family"),
        "trigger_type": item.get("triggerType") or item.get("trigger_type"),
        "title": item.get("title"),
        "verdict": item.get("verdict"),
        "confidence": item.get("confidence"),
        "evidence_span": snake_span,
        "policy_reference": snake_ref,
        "reasoning": item.get("reasoning"),
        "evidence_chain": item.get("evidenceChain") or item.get("evidence_chain") or [],
        "supporting_quotes": item.get("supportingQuotes") or item.get("supporting_quotes") or [],
    }


def normalize_storage_object_path(audio_path: str, filename: str) -> str:
    path = (audio_path or "").replace("\\", "/").strip("/")
    bucket_prefix = f"{DATASET_AUDIO_BUCKET}/"
    if path.startswith(bucket_prefix):
        path = path[len(bucket_prefix) :]
    if path.endswith(filename) and path.count("/") >= 1:
        return path
    return f"{DATASET_STORAGE_PREFIX}/{filename}"


def normalize_interaction_audio_path(filename: str) -> str:
    return f"{DATASET_AUDIO_BUCKET}/{DATASET_STORAGE_PREFIX}/{filename}"


def call_number_from_path(audio_path: str | None) -> str | None:
    match = CALL_AUDIO_RE.search(audio_path or "")
    if not match:
        return None
    return match.group(1)


def parse_duration(duration: str) -> int:
    parts = (duration or "0:0").split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return int(parts[0]) if parts else 0


def parse_interaction_date(date_str: str, time_str: str) -> datetime:
    combined = f"{date_str} {time_str}"
    for fmt in ("%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(combined, fmt)
        except ValueError:
            continue
    return datetime.now()


def pct_to_db_score(value: float | int | None) -> float:
    if value is None:
        return 0.0
    return max(0.0, min(1.0, float(value) / 100.0))


def _citations_to_snake(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items or []:
        rows.append(
            {
                "source": item.get("source"),
                "speaker": item.get("speaker"),
                "quote": item.get("quote"),
                "utterance_index": item.get("utteranceIndex"),
            }
        )
    return rows


def llm_triggers_to_cache_payload(interaction_id: UUID, llm: dict[str, Any] | None) -> dict[str, Any] | None:
    if not llm or not llm.get("available"):
        return None
    es = llm.get("emotionShift") or {}
    pa = llm.get("processAdherence") or {}
    nli = llm.get("nliPolicy") or {}
    derived = llm.get("derived") or {}
    payload = {
        "interaction_id": str(interaction_id),
        "emotion_shift": {
            "is_dissonance_detected": bool(es.get("isDissonanceDetected")),
            "dissonance_type": es.get("dissonanceType") or "none",
            "root_cause": es.get("rootCause") or "insufficient evidence",
            "counterfactual_correction": es.get("counterfactualCorrection")
            or "If the agent had clarified next steps, closure would have been clearer.",
            "evidence_quotes": es.get("evidenceQuotes") or [],
            "citations": _citations_to_snake(es.get("citations")),
            "current_customer_emotion": es.get("currentCustomerEmotion") or "neutral",
            "current_emotion_reasoning": es.get("currentEmotionReasoning") or "insufficient evidence",
            "insufficient_evidence": bool(es.get("insufficientEvidence")),
            "confidence_score": es.get("confidenceScore"),
        },
        "process_adherence": {
            "detected_topic": pa.get("detectedTopic") or "general_inquiry",
            "is_resolved": bool(pa.get("isResolved")),
            "efficiency_score": int(pa.get("efficiencyScore") or 7),
            "justification": pa.get("justification") or "",
            "missing_sop_steps": pa.get("missingSopSteps") or [],
            "evidence_quotes": pa.get("evidenceQuotes") or [],
            "citations": _citations_to_snake(pa.get("citations")),
            "insufficient_evidence": bool(pa.get("insufficientEvidence")),
            "confidence_score": pa.get("confidenceScore"),
        },
        "nli_policy": {
            "nli_category": nli.get("nliCategory") or "Entailment",
            "justification": nli.get("justification") or "",
            "evidence_quotes": nli.get("evidenceQuotes") or [],
            "citations": _citations_to_snake(nli.get("citations")),
            "policy_version": nli.get("policyVersion"),
            "policy_effective_at": nli.get("policyEffectiveAt"),
            "policy_category": nli.get("policyCategory"),
            "conflict_resolution_applied": bool(nli.get("conflictResolutionApplied")),
            "insufficient_evidence": bool(nli.get("insufficientEvidence")),
            "confidence_score": nli.get("confidenceScore"),
            "policy_alignment_score": nli.get("policyAlignmentScore"),
        },
        "derived_customer_text": derived.get("customerText") or "",
        "derived_acoustic_emotion": derived.get("acousticEmotion") or "neutral",
        "derived_fused_emotion": derived.get("fusedEmotion") or "neutral",
        "derived_agent_statement": derived.get("agentStatement") or "",
        "explainability": {
            "trigger_attributions": [
                _attribution_to_snake(item)
                for item in (llm.get("explainability") or {}).get("triggerAttributions") or []
            ],
            "claim_provenance": [],
        },
        "_schema_version": CACHE_SCHEMA_VERSION,
    }
    InteractionLLMTriggerReport.model_validate(payload)
    return payload


async def get_or_create_org(session: AsyncSession) -> Organization:
    result = await session.exec(
        select(Organization).where(Organization.slug == DATASET_ORG_SLUG)
    )
    org = result.first()
    if org:
        return org
    org = Organization(name=DATASET_ORG_NAME, slug=DATASET_ORG_SLUG)
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org


async def get_or_create_manager(session: AsyncSession, org_id: UUID) -> UserModel:
    result = await session.exec(select(UserModel).where(UserModel.email == MANAGER_EMAIL))
    user = result.first()
    if user:
        user.organization_id = org_id
        user.role = UserRole.manager
        user.name = MANAGER_NAME
        user.password_hash = get_password_hash(MANAGER_PASSWORD)
        user.is_active = True
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    user = UserModel(
        email=MANAGER_EMAIL,
        name=MANAGER_NAME,
        password_hash=get_password_hash(MANAGER_PASSWORD),
        organization_id=org_id,
        role=UserRole.manager,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def resolve_agents(session: AsyncSession, org_id: UUID) -> dict[str, UserModel]:
    """Resolve agent profiles in the dataset org; re-home existing users when needed."""
    agents: dict[str, UserModel] = {}
    pwd_hash = get_password_hash(AGENT_PASSWORD)
    for display_name, email in AGENT_PROFILES.items():
        result = await session.exec(select(UserModel).where(UserModel.email == email))
        agent = result.first()
        if not agent:
            agent = UserModel(
                email=email,
                name=display_name,
                password_hash=pwd_hash,
                organization_id=org_id,
                role=UserRole.agent,
                is_active=True,
            )
            session.add(agent)
            await session.commit()
            await session.refresh(agent)
        else:
            agent.organization_id = org_id
            agent.password_hash = pwd_hash
            agent.role = UserRole.agent
            agent.is_active = True
            agent.name = display_name
            session.add(agent)
            await session.commit()
            await session.refresh(agent)
        agents[display_name] = agent
    return agents


async def remove_duplicate_call_rows(
    session: AsyncSession,
    org_id: UUID,
    *,
    keep_id: UUID,
    call_number: str | None,
    audio_path: str,
) -> None:
    """Drop stale rows for the same CALL_XX within the dataset org only."""
    existing = await session.exec(select(Interaction).where(Interaction.organization_id == org_id))
    for row in existing.all():
        if row.id == keep_id:
            continue
        same_path = row.audio_file_path == audio_path
        same_call = call_number and call_number_from_path(row.audio_file_path) == call_number
        if same_path or same_call:
            await delete_interaction_tree(session, row.id)


async def delete_interaction_tree(session: AsyncSession, interaction_id: UUID) -> None:
    from sqlalchemy import delete

    await session.exec(delete(PolicyCompliance).where(PolicyCompliance.interaction_id == interaction_id))
    await session.exec(delete(InteractionLLMTriggerCache).where(InteractionLLMTriggerCache.interaction_id == interaction_id))
    await session.exec(delete(EmotionEvent).where(EmotionEvent.interaction_id == interaction_id))
    await session.exec(delete(Utterance).where(Utterance.interaction_id == interaction_id))
    await session.exec(delete(Transcript).where(Transcript.interaction_id == interaction_id))
    await session.exec(delete(InteractionScore).where(InteractionScore.interaction_id == interaction_id))
    await session.exec(delete(Interaction).where(Interaction.id == interaction_id))
    await session.flush()


def _local_audio_candidates(audio_path: str) -> list[Path]:
    name = Path(audio_path).name
    search_roots = [
        LOCAL_AUDIO_DIR,
        REPO_ROOT / "storage" / "audio" / "nexalink",
        REPO_ROOT / "audio_import" / "audio" / "nexalink",
        REPO_ROOT / "audio_import",
    ]
    candidates: list[Path] = []
    seen: set[Path] = set()
    for root in search_roots:
        if not root.is_dir():
            continue
        direct = root / name
        if direct.is_file() and direct not in seen:
            candidates.append(direct)
            seen.add(direct)
        for match in sorted(root.glob(f"**/{name}")):
            if match.is_file() and match not in seen:
                candidates.append(match)
                seen.add(match)

    eval_dir = REPO_ROOT / "storage" / "audio" / "nexalink" / "evaluation"
    if eval_dir.is_dir():
        for match in sorted(eval_dir.glob(f"*{name}*")):
            if match.is_file() and match not in seen:
                candidates.append(match)
                seen.add(match)
    return candidates


def _resolve_local_audio(audio_path: str) -> Path | None:
    return _best_audio_file(_local_audio_candidates(audio_path))


def _best_audio_file(candidates: list[Path]) -> Path | None:
    files = [path for path in candidates if path.is_file()]
    if not files:
        return None
    unique = list({path.resolve(): path for path in files}.values())
    return max(unique, key=lambda path: path.stat().st_size)


def _ensure_playable_wav(
    local_dir: Path,
    filename: str,
    duration_seconds: int,
    *,
    allow_generated_audio: bool,
) -> Path | None:
    """Use checked-in WAV when present; optionally synthesize a silent clip."""
    resolved = _resolve_local_audio(normalize_interaction_audio_path(filename))
    if resolved:
        return resolved
    if not allow_generated_audio:
        return None
    try:
        from app.api.routes.interactions import generate_dummy_wav
    except Exception:
        return None
    local_dir.mkdir(parents=True, exist_ok=True)
    target = local_dir / filename
    seconds = max(30, min(int(duration_seconds or 120), 600))
    target.write_bytes(generate_dummy_wav(seconds))
    return target


def upload_audio_files(
    audio_paths: list[str],
    *,
    bucket: str = "recordings",
    durations: dict[str, int] | None = None,
    allow_generated_audio: bool = False,
) -> dict[str, Any]:
    import mimetypes
    import os

    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None  # type: ignore[assignment]

    if load_dotenv:
        load_dotenv(REPO_ROOT / "backend" / ".env", override=False)

    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not url or not key:
        return {"uploaded": 0, "skipped": len(audio_paths), "error": "Supabase credentials missing"}

    from supabase import create_client

    sb = create_client(url, key)
    uploaded = 0
    missing: list[str] = []
    synthesized: list[str] = []
    for audio_path in audio_paths:
        filename = Path(audio_path).name
        local_path = _resolve_local_audio(audio_path)
        synthesized_this = False
        if not local_path:
            duration = (durations or {}).get(filename, 120)
            local_path = _ensure_playable_wav(LOCAL_AUDIO_DIR, filename, duration, allow_generated_audio=allow_generated_audio)
            synthesized_this = local_path is not None and allow_generated_audio
        if not local_path:
            missing.append(filename)
            continue
        if synthesized_this:
            synthesized.append(filename)
        object_path = normalize_storage_object_path(audio_path, filename)
        ctype = mimetypes.guess_type(local_path.name)[0] or "audio/wav"
        sb.storage.from_(bucket).upload(
            object_path,
            local_path.read_bytes(),
            file_options={"content-type": ctype, "upsert": "true"},
        )
        uploaded += 1
    return {"uploaded": uploaded, "missing_local": missing, "synthesized": synthesized, "bucket": bucket}


async def load_dataset(
    *,
    api_base: str | None,
    upload_audio: bool,
    allow_generated_audio: bool = False,
) -> dict[str, Any]:
    raw = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    details: dict[str, dict[str, Any]] = raw["details"]
    summaries: list[dict[str, Any]] = raw["interactions"]
    summary_by_id = {row["id"]: row for row in summaries}

    loaded_ids: list[str] = []
    audio_paths: list[str] = []
    duration_by_name: dict[str, int] = {}

    async with AsyncSession(engine, expire_on_commit=False) as session:
        org = await get_or_create_org(session)
        manager = await get_or_create_manager(session, org.id)
        agents = await resolve_agents(session, org.id)
        await ensure_organization_policies_from_source(session, org.id, source_org_slug="nexalink")
        kb_seed = await ensure_organization_knowledge_from_source(session, org.id, source_org_slug="nexalink")
        await session.commit()

        for iid, detail in details.items():
            summary = summary_by_id.get(iid)
            if not summary:
                continue
            interaction_id = UUID(iid)
            agent_name = summary.get("agentName") or detail["interaction"].get("agentName")
            agent = agents.get(agent_name)
            if not agent:
                raise RuntimeError(f"No agent mapping for {agent_name}")

            audio_path = summary.get("audioFilePath") or detail["interaction"].get("audioFilePath")
            audio_paths.append(audio_path)
            call_number = call_number_from_path(audio_path)

            await remove_duplicate_call_rows(
                session,
                org.id,
                keep_id=interaction_id,
                call_number=call_number,
                audio_path=audio_path,
            )
            await delete_interaction_tree(session, interaction_id)

            duration_seconds = parse_duration(summary.get("duration") or "0:00")
            duration_by_name[Path(audio_path).name] = duration_seconds
            interaction = Interaction(
                id=interaction_id,
                organization_id=org.id,
                agent_id=agent.id,
                uploaded_by=manager.id,
                audio_file_path=audio_path,
                file_size_bytes=max(1, duration_seconds * 8000),
                duration_seconds=duration_seconds,
                file_format=Path(audio_path).suffix.lstrip(".") or "wav",
                interaction_date=parse_interaction_date(summary["date"], summary["time"]),
                processing_status=ProcessingStatus.completed,
                language_detected=summary.get("language") or "en",
                has_overlap=bool(summary.get("hasOverlap")),
            )
            session.add(interaction)
            await session.flush()

            scores = detail.get("scores") or {}
            session.add(
                InteractionScore(
                    interaction_id=interaction_id,
                    overall_score=pct_to_db_score(scores.get("overallScore")),
                    empathy_score=pct_to_db_score(scores.get("empathyScore")),
                    policy_score=pct_to_db_score(scores.get("policyScore")),
                    resolution_score=pct_to_db_score(scores.get("resolutionScore")),
                    was_resolved=bool(scores.get("resolved")),
                    total_silence_seconds=scores.get("totalSilenceSeconds"),
                    avg_response_time_seconds=scores.get("avgResponseTimeSeconds"),
                )
            )

            utterances = detail.get("utterances") or []
            full_text = "\n".join(u.get("text") or "" for u in utterances)
            transcript = Transcript(
                interaction_id=interaction_id,
                full_text=full_text,
                overall_confidence=0.9,
            )
            session.add(transcript)
            await session.flush()

            utt_id_map: dict[str, UUID] = {}
            for utt in utterances:
                utt_uuid = UUID(utt["id"])
                utt_id_map[utt["id"]] = utt_uuid
                speaker = (utt.get("speaker") or "customer").lower()
                session.add(
                    Utterance(
                        id=utt_uuid,
                        interaction_id=interaction_id,
                        transcript_id=transcript.id,
                        speaker_role=SpeakerRole.agent if speaker == "agent" else SpeakerRole.customer,
                        user_id=agent.id if speaker == "agent" else None,
                        sequence_index=int(utt.get("sequenceIndex") or 0),
                        start_time_seconds=float(utt.get("startTime") or 0),
                        end_time_seconds=float(utt.get("endTime") or 0),
                        text=utt.get("text") or "",
                        emotion=utt.get("acousticEmotion") or utt.get("emotion") or "neutral",
                        emotion_confidence=float(utt.get("fusedConfidence") or utt.get("confidence") or 0.5),
                    )
                )
            await session.flush()

            for event in detail.get("emotionEvents") or []:
                jump = float(event.get("jumpToSeconds") or 0)
                linked_utt = min(
                    utterances,
                    key=lambda u: abs(float(u.get("startTime") or 0) - jump),
                )
                speaker = (event.get("speaker") or "customer").lower()
                session.add(
                    EmotionEvent(
                        id=UUID(event["id"]),
                        interaction_id=interaction_id,
                        utterance_id=utt_id_map[linked_utt["id"]],
                        previous_emotion=event.get("previousEmotion") or "neutral",
                        new_emotion=event.get("newEmotion") or "neutral",
                        emotion_delta=float(event.get("delta") or 0),
                        speaker_role=SpeakerRole.agent if speaker == "agent" else SpeakerRole.customer,
                        llm_justification=event.get("llmJustification") or event.get("justification"),
                        jump_to_seconds=jump,
                        confidence_score=float(event.get("confidenceScore") or 0),
                    )
                )

            cache_payload = llm_triggers_to_cache_payload(interaction_id, detail.get("llmTriggers"))
            if cache_payload:
                session.add(
                    InteractionLLMTriggerCache(
                        interaction_id=interaction_id,
                        org_filter=DATASET_ORG_SLUG,
                        report_payload=cache_payload,
                    )
                )

            llm = detail.get("llmTriggers") or {}
            es = llm.get("emotionShift") or {}
            pa = llm.get("processAdherence") or {}
            nli = llm.get("nliPolicy") or {}
            detected = bool(es.get("isDissonanceDetected"))
            dtype = (es.get("dissonanceType") or "none").strip()
            effective_dissonance = (detected, dtype if detected else "none")

            gt_coverage: list[dict[str, Any]] = []
            call_id = detail.get("_callId")
            if call_id:
                gt_path = REPO_ROOT / "storage" / "audio" / "nexalink" / "evaluation" / f"{call_id}.json"
                if gt_path.is_file():
                    gt_coverage = json.loads(gt_path.read_text(encoding="utf-8")).get("coverage") or []

            violation_input = ViolationMappingInput.from_dataset_payload(
                emotion_shift=es,
                process_adherence=pa,
                nli_policy=nli,
                explainability=llm.get("explainability") or {},
                coverage=gt_coverage,
                reference_dissonance=effective_dissonance,
            )
            violation_specs = derive_violation_specs(violation_input)
            await persist_policy_violations(
                session,
                interaction_id=interaction_id,
                organization_id=org.id,
                specs=violation_specs,
                replace_existing=True,
            )

            loaded_ids.append(iid)
            summary["agentId"] = str(agent.id)
            detail["interaction"]["agentId"] = str(agent.id)

        await session.commit()

    audio_upload_result: dict[str, Any] | None = None
    unique_paths = sorted(set(audio_paths))
    duration_by_name = {
        Path(path).name: parse_duration(summary_by_id.get(iid, {}).get("duration") or "0:00")
        for iid, path in zip(loaded_ids, audio_paths)
    }
    if upload_audio and unique_paths:
        audio_upload_result = upload_audio_files(
            unique_paths,
            durations=duration_by_name,
            allow_generated_audio=allow_generated_audio,
        )

    # Write back association ids for exports (same file, no extra metadata keys).
    raw["interactions"] = summaries
    raw["details"] = details
    DATASET_PATH.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")

    verify: dict[str, Any] = {
        "organization_id": str(org.id),
        "manager_id": str(manager.id),
        "manager_email": MANAGER_EMAIL,
        "loaded_interactions": len(loaded_ids),
        "api_list_count": None,
        "login_ok": None,
        "audio_upload": audio_upload_result,
    }

    if api_base:
        verify.update(_verify_api(api_base, MANAGER_EMAIL, MANAGER_PASSWORD, len(loaded_ids)))

    return verify


def _verify_api(base: str, email: str, password: str, expected: int) -> dict[str, Any]:
    form = urllib.parse.urlencode({"username": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{base.rstrip('/')}/auth/login/access-token",
        data=form,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            token = json.loads(resp.read().decode("utf-8"))["access_token"]
    except urllib.error.HTTPError as exc:
        return {"login_ok": False, "api_error": f"login HTTP {exc.code}"}

    list_req = urllib.request.Request(
        f"{base.rstrip('/')}/interactions",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(list_req, timeout=60) as resp:
        rows = json.loads(resp.read().decode("utf-8"))

    telecom_rows = [
        r
        for r in rows
        if CALL_AUDIO_RE.search(r.get("audioFilePath") or "")
    ]
    return {
        "login_ok": True,
        "api_list_count": len(rows),
        "telecom_call_count": len(telecom_rows),
        "expected_telecom": expected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Load telecom dataset into Postgres.")
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000/api/v1",
        help="Backend API base for post-load verification (set empty to skip).",
    )
    parser.add_argument(
        "--upload-audio",
        action="store_true",
        help="Upload local WAV files to Supabase Storage when present.",
    )
    parser.add_argument(
        "--reupload-audio-only",
        action="store_true",
        help="Only re-upload WAV fixtures from disk to Supabase (skip DB reload).",
    )
    parser.add_argument(
        "--allow-generated-audio",
        action="store_true",
        help="When local WAV is missing, upload a silent placeholder (not recommended).",
    )
    args = parser.parse_args()
    if not DATASET_PATH.is_file():
        print(f"Missing dataset: {DATASET_PATH}. Run build_session_export.py first.", file=sys.stderr)
        return 1

    if args.reupload_audio_only:
        raw = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
        paths = sorted(
            {
                row.get("audioFilePath")
                for row in raw.get("interactions", [])
                if row.get("audioFilePath")
            }
        )
        duration_by_name = {
            Path(path).name: parse_duration(row.get("duration") or "0:00")
            for row in raw.get("interactions", [])
            for path in [row.get("audioFilePath")]
            if path
        }
        result = upload_audio_files(
            paths,
            durations=duration_by_name,
            allow_generated_audio=args.allow_generated_audio,
        )
        print("\n--- audio re-upload complete ---")
        print(json.dumps(result, indent=2))
        return 0 if result.get("uploaded", 0) > 0 and not result.get("missing_local") else 1

    api_base = args.api_base.strip() or None
    result = asyncio.run(
        load_dataset(
            api_base=api_base,
            upload_audio=args.upload_audio,
            allow_generated_audio=args.allow_generated_audio,
        )
    )

    print("\n--- load complete ---")
    print(f"organization_id: {result['organization_id']}")
    print(f"manager_id:      {result['manager_id']}")
    print(f"interactions:    {result['loaded_interactions']}")
    if result.get("login_ok") is not None:
        print(f"login_ok:        {result['login_ok']}")
        print(f"api_list_count:  {result.get('api_list_count')}")
        print(f"telecom_calls:   {result.get('telecom_call_count')} (expected {result.get('expected_telecom')})")
    if result.get("audio_upload") is not None:
        print(f"audio_upload:    {result['audio_upload']}")
    print("\nSign in at http://localhost:3000 with:")
    print(f"  Email:    {MANAGER_EMAIL}")
    print(f"  Password: {MANAGER_PASSWORD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
