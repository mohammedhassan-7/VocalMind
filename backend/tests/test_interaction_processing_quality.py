from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlmodel import SQLModel, Session, create_engine, select

import app.models  # noqa: F401
from app.core import interaction_processing as ip
from app.models.emotion_event import EmotionEvent
from app.models.enums import ProcessingStatus, SpeakerRole
from app.models.enums import JobStatus, JobStage
from app.models.interaction import Interaction
from app.models.organization import Organization
from app.models.processing import ProcessingJob
from app.models.transcript import Transcript
from app.models.utterance import Utterance
from app.models.user import User
from app.models.enums import UserRole


class _SyncResult:
    def __init__(self, result):
        self._result = result

    def first(self):
        return self._result.first()

    def all(self):
        return self._result.all()


class _AsyncSessionAdapter:
    def __init__(self, wrapped: Session):
        self._wrapped = wrapped

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def exec(self, statement):
        return _SyncResult(self._wrapped.exec(statement))

    async def get(self, *args, **kwargs):
        return self._wrapped.get(*args, **kwargs)

    def add(self, instance):
        self._wrapped.add(instance)

    async def flush(self):
        self._wrapped.flush()

    async def commit(self):
        self._wrapped.commit()

    async def rollback(self):
        self._wrapped.rollback()


@pytest.mark.asyncio
async def test_process_interaction_uses_stable_role_mapping(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'interaction-quality.db'}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)

    org_id = uuid4()
    manager_id = uuid4()
    agent_id = uuid4()
    interaction_id = uuid4()
    session.add(
        Organization(
            id=org_id,
            name="Nexa",
            slug="nexa",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
    )
    session.add(
        User(
            id=manager_id,
            organization_id=org_id,
            email="manager@example.com",
            password_hash="hash",
            name="Manager",
            role=UserRole.manager,
            is_active=True,
        )
    )
    session.add(
        User(
            id=agent_id,
            organization_id=org_id,
            email="agent@example.com",
            password_hash="hash",
            name="Agent",
            role=UserRole.agent,
            is_active=True,
        )
    )
    session.add(
        Interaction(
            id=interaction_id,
            organization_id=org_id,
            agent_id=agent_id,
            uploaded_by=manager_id,
            audio_file_path=str(Path(tmp_path / "call.wav")),
            processing_status=ProcessingStatus.pending,
            duration_seconds=0,
            file_size_bytes=10,
            file_format="wav",
            interaction_date=datetime.now(timezone.utc).replace(tzinfo=None),
        )
    )
    session.add(Transcript(interaction_id=interaction_id, full_text=""))
    session.commit()

    monkeypatch.setattr(ip, "AsyncSession", lambda *args, **kwargs: _AsyncSessionAdapter(session))
    monkeypatch.setattr(ip, "engine", SimpleNamespace())
    monkeypatch.setattr(ip, "evaluate_interaction_triggers", AsyncMock(return_value=None))
    monkeypatch.setattr(ip, "relabel_segments_with_speaker_model", lambda segments: segments)

    async def _fake_fetch(_path):
        return b"RIFF0000WAVEfmt ", "call.wav"

    async def _fake_analyze(_audio, _filename, _content_type):
        return {
            "language": "en",
            "text": "",
            "top_score": 0.88,
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "How can I help you today?",
                    "speaker": "SPEAKER_01",
                    "speaker_meta": {"source": "diarization"},
                    "emotion": "neutral",
                    "emotion_scores": [{"label": "neutral", "score": 0.8}],
                },
                {
                    "start": 2.2,
                    "end": 4.5,
                    "text": "I need help with my account.",
                    "speaker": "SPEAKER_00",
                    "speaker_meta": {"source": "diarization"},
                    "emotion": "frustrated",
                    "emotion_scores": [{"label": "frustrated", "score": 0.9}],
                },
                {
                    "start": 4.7,
                    "end": 7.0,
                    "text": "I still cannot access it.",
                    "speaker": "SPEAKER_00",
                    "speaker_meta": {"source": "diarization"},
                    "emotion": "frustrated",
                    "emotion_scores": [{"label": "frustrated", "score": 0.9}],
                },
            ],
        }

    monkeypatch.setattr(ip, "fetch_audio_bytes", _fake_fetch)
    monkeypatch.setattr(ip.full_client, "analyze_bytes", _fake_analyze)

    await ip.process_interaction(interaction_id)

    utterances = session.exec(
        select(Utterance).where(Utterance.interaction_id == interaction_id).order_by(Utterance.sequence_index)
    ).all()
    assert [u.speaker_role for u in utterances] == [SpeakerRole.agent, SpeakerRole.customer, SpeakerRole.customer]

    emotion_events = session.exec(select(EmotionEvent).where(EmotionEvent.interaction_id == interaction_id)).all()
    assert len(emotion_events) == 1
    assert emotion_events[0].new_emotion == "frustrated"


def test_assign_cluster_roles_handles_agent_speaking_first_as_speaker_00():
    """Regression: WhisperX assigns SPEAKER_00 to whichever voice it hears first.
    When the agent answers (speaks first), the agent voice gets SPEAKER_00 — the
    old endswith("00") heuristic mislabeled the agent as customer.
    """
    segments = [
        {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00",
         "text": "Thank you for calling NexaLink Telecommunications. My name is Priya. Who do I have the pleasure of speaking with today?"},
        {"start": 5.5, "end": 8.0, "speaker": "SPEAKER_01",
         "text": "Hi, this is Marcus Whitfield."},
        {"start": 8.5, "end": 14.0, "speaker": "SPEAKER_00",
         "text": "Hello, Mr. Whitfield. How can I help you today?"},
        {"start": 14.5, "end": 22.0, "speaker": "SPEAKER_01",
         "text": "My internet was out for two days. I want a credit on my bill."},
    ]
    role_map = ip.assign_cluster_roles_from_text(segments, agent_name="Priya")
    assert role_map["SPEAKER_00"] == SpeakerRole.agent, "Agent who speaks first must not be mislabeled as customer"
    assert role_map["SPEAKER_01"] == SpeakerRole.customer


def test_assign_cluster_roles_handles_three_clusters_warm_transfer():
    """Tier 2 warm transfer: 2 agents + 1 customer. The customer must be the
    cluster with the lowest net agent score, not the lowest cluster ID.
    """
    segments = [
        {"start": 0.0, "end": 4.0, "speaker": "SPEAKER_01",
         "text": "Thank you for calling. My name is Daniel. How can I help you?"},
        {"start": 4.5, "end": 12.0, "speaker": "SPEAKER_02",
         "text": "I was charged $247. My bill is wrong. I cannot believe this."},
        {"start": 12.5, "end": 20.0, "speaker": "SPEAKER_01",
         "text": "I understand. Let me pull up your account. I'll need to verify a few details."},
        {"start": 600.0, "end": 610.0, "speaker": "SPEAKER_00",
         "text": "Hi Daniel, this is Sarah Chen taking the transfer. I can help."},
    ]
    role_map = ip.assign_cluster_roles_from_text(segments, agent_name="Daniel")
    assert role_map["SPEAKER_02"] == SpeakerRole.customer
    assert role_map["SPEAKER_01"] == SpeakerRole.agent
    assert role_map["SPEAKER_00"] == SpeakerRole.agent  # Tier 2 escalation agent


def test_assign_cluster_roles_honors_explicit_agent_customer_labels():
    """If diarization (or DistilBERT relabeler) already labeled segments as
    'agent'/'customer', cluster scoring must not re-decide them.
    """
    segments = [
        {"start": 0.0, "end": 5.0, "speaker": "agent", "text": "Thank you for calling."},
        {"start": 5.5, "end": 10.0, "speaker": "customer", "text": "Hi, my account is locked."},
    ]
    role_map = ip.assign_cluster_roles_from_text(segments, agent_name="Priya")
    assert role_map == {}  # explicit labels are passed through unchanged


def test_first_speaker_greeting_prior_pins_agent_on_mistranscribed_opener():
    """First-speaker prior: the cluster that owns the earliest segment within
    the first 8 s of audio is anchored as agent regardless of whether WhisperX
    transcribed the scripted greeting correctly. Without this prior, a garbled
    opener can flip the cluster assignment when the customer has stronger
    keyword signal in the rest of the call.
    """
    segments = [
        # Mistranscribed greeting — no scripted keywords land
        {"start": 0.5, "end": 2.0, "speaker": "SPEAKER_00",
         "text": "Hello good morning broadband line"},
        # Strong customer cues on the other cluster
        {"start": 2.5, "end": 6.0, "speaker": "SPEAKER_01",
         "text": "Hi I would like a refund I was overcharged this is unacceptable"},
        # Real agent verification phrase (so the score gap is closed)
        {"start": 6.5, "end": 10.0, "speaker": "SPEAKER_00",
         "text": "Could you please confirm your account number for verification"},
    ]
    role_map = ip.assign_cluster_roles_from_text(segments, agent_name=None)
    assert role_map["SPEAKER_00"] == SpeakerRole.agent
    assert role_map["SPEAKER_01"] == SpeakerRole.customer


def test_emotion_min_duration_gate_inherits_prev_for_short_segments():
    """Sub-threshold segments inherit the previous segment's emotion so that
    low-confidence emotion2vec outputs on brief interjections don't pollute
    the call-level distribution. Segments at or above the threshold keep
    their own emotion.
    """
    segments = [
        {"start": 0.0, "end": 3.0, "emotion": "happy",
         "emotion_scores": [{"label": "happy", "score": 0.9}]},
        {"start": 3.0, "end": 3.4, "emotion": "neutral",  # 0.4 s → inherit
         "emotion_scores": [{"label": "neutral", "score": 0.3}]},
        {"start": 3.5, "end": 7.5, "emotion": "sad",      # 4 s → keep
         "emotion_scores": [{"label": "sad", "score": 0.85}]},
        {"start": 7.5, "end": 8.2, "emotion": "neutral",  # 0.7 s → inherit
         "emotion_scores": [{"label": "neutral", "score": 0.3}]},
    ]
    out = ip.apply_emotion_min_duration_gate([dict(s) for s in segments], min_secs=1.0)
    assert [s["emotion"] for s in out] == ["happy", "happy", "sad", "sad"]
    assert out[1].get("_emotion_inherited") is True
    assert out[1].get("_emotion_original") == "neutral"
    assert "_emotion_inherited" not in out[0]
    assert "_emotion_inherited" not in out[2]


def test_emotion_min_duration_gate_first_segment_has_no_prior():
    """When the first segment is itself sub-threshold there is nothing to
    inherit from — it must keep its own emotion (or 'neutral' default).
    """
    segments = [
        {"start": 0.0, "end": 0.3, "emotion": "neutral",
         "emotion_scores": [{"label": "neutral", "score": 0.2}]},
    ]
    out = ip.apply_emotion_min_duration_gate([dict(s) for s in segments], min_secs=1.0)
    assert out[0]["emotion"] == "neutral"
    assert "_emotion_inherited" not in out[0]


def test_emotion_min_duration_gate_disabled_when_threshold_zero():
    segments = [
        {"start": 0.0, "end": 3.0, "emotion": "happy", "emotion_scores": []},
        {"start": 3.0, "end": 3.2, "emotion": "neutral", "emotion_scores": []},
    ]
    out = ip.apply_emotion_min_duration_gate([dict(s) for s in segments], min_secs=0.0)
    assert [s["emotion"] for s in out] == ["happy", "neutral"]


@pytest.mark.asyncio
async def test_mark_interaction_failed_stage_status_transaction_rolls_back_on_mid_loop_failure(monkeypatch, tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'interaction-failed-rollback.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)

    org_id = uuid4()
    manager_id = uuid4()
    agent_id = uuid4()
    interaction_id = uuid4()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(Organization(id=org_id, name="Org", slug="org", created_at=now))
    session.add(
        User(
            id=manager_id,
            organization_id=org_id,
            email="manager@org.local",
            password_hash="hash",
            name="Manager",
            role=UserRole.manager,
            is_active=True,
        )
    )
    session.add(
        User(
            id=agent_id,
            organization_id=org_id,
            email="agent@org.local",
            password_hash="hash",
            name="Agent",
            role=UserRole.agent,
            is_active=True,
        )
    )
    session.add(
        Interaction(
            id=interaction_id,
            organization_id=org_id,
            agent_id=agent_id,
            uploaded_by=manager_id,
            audio_file_path=str(Path(tmp_path / "call.wav")),
            processing_status=ProcessingStatus.processing,
            duration_seconds=1,
            file_size_bytes=1,
            file_format="wav",
            interaction_date=now,
        )
    )
    for stage in ip.STAGE_ORDER:
        session.add(
            ProcessingJob(
                interaction_id=interaction_id,
                stage=stage,
                status=JobStatus.pending,
            )
        )
    session.commit()

    original_set_job_status = ip._set_job_status
    call_counter = {"n": 0}

    async def _exploding_set_job_status(session_obj, interaction_id_obj, stage, status, error_message=None):
        await original_set_job_status(session_obj, interaction_id_obj, stage, status, error_message)
        if status == JobStatus.failed:
            call_counter["n"] += 1
            if call_counter["n"] == 3:
                raise RuntimeError("simulated mid-loop failure")

    monkeypatch.setattr(
        ip,
        "AsyncSession",
        lambda *args, **kwargs: _AsyncSessionAdapter(session),
    )
    monkeypatch.setattr(ip, "engine", SimpleNamespace())
    monkeypatch.setattr(ip, "_set_job_status", _exploding_set_job_status)

    with pytest.raises(RuntimeError, match="simulated mid-loop failure"):
        await ip.mark_interaction_failed(interaction_id, "boom")

    jobs = session.exec(
        select(ProcessingJob).where(ProcessingJob.interaction_id == interaction_id)
    ).all()
    assert all(job.status == JobStatus.pending for job in jobs)
