from datetime import datetime
from types import SimpleNamespace
from uuid import UUID

from sqlmodel import SQLModel, Session, create_engine

from app.api.deps import get_current_user, get_db, get_session
from app.llm_trigger.schemas import EmotionShiftAnalysis, NLIEvaluation, ProcessAdherenceReport
from app.models.enums import SpeakerRole, UserRole
from app.models.interaction import Interaction
from app.models.organization import Organization
from app.models.transcript import Transcript
from app.models.user import User
from app.models.utterance import Utterance


def test_llm_trigger_run_blocks_cross_org_access(client, tmp_path, monkeypatch):
    db_path = tmp_path / "llm_trigger_cross_org.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)

    org_a = Organization(
        id=UUID("a0000000-0000-0000-0000-000000000001"),
        name="Org A",
        slug="org-a",
    )
    org_b = Organization(
        id=UUID("a0000000-0000-0000-0000-000000000002"),
        name="Org B",
        slug="org-b",
    )
    user_a = User(
        id=UUID("b0000000-0000-0000-0000-000000000001"),
        organization_id=org_a.id,
        email="a@org.local",
        password_hash="hash",
        name="Manager A",
        role=UserRole.manager,
        is_active=True,
    )
    user_b_agent = User(
        id=UUID("b0000000-0000-0000-0000-000000000002"),
        organization_id=org_b.id,
        email="agent@orgb.local",
        password_hash="hash",
        name="Agent B",
        role=UserRole.agent,
        is_active=True,
    )
    interaction_b = Interaction(
        id=UUID("c0000000-0000-0000-0000-000000000001"),
        organization_id=org_b.id,
        agent_id=user_b_agent.id,
        uploaded_by=user_b_agent.id,
        audio_file_path="org-b/call.wav",
        file_size_bytes=1234,
        duration_seconds=60,
        file_format="wav",
        interaction_date=datetime.utcnow(),
    )
    transcript_b = Transcript(
        id=UUID("d0000000-0000-0000-0000-000000000001"),
        interaction_id=interaction_b.id,
        full_text="customer: refund please\nagent: I can help",
    )
    utterance_b = Utterance(
        id=UUID("e0000000-0000-0000-0000-000000000001"),
        interaction_id=interaction_b.id,
        transcript_id=transcript_b.id,
        speaker_role=SpeakerRole.customer,
        sequence_index=0,
        start_time_seconds=0.0,
        end_time_seconds=1.0,
        text="refund please",
        emotion="frustrated",
        emotion_confidence=0.9,
    )
    session.add_all([org_a, org_b, user_a, user_b_agent, interaction_b, transcript_b, utterance_b])
    session.commit()

    from tests.conftest import AsyncSessionAdapter
    adapter = AsyncSessionAdapter(session)

    async def _override_get_db():
        yield adapter

    async def _override_get_session():
        yield adapter

    async def _override_current_user():
        return user_a

    client.app.dependency_overrides[get_db] = _override_get_db
    client.app.dependency_overrides[get_session] = _override_get_session
    client.app.dependency_overrides[get_current_user] = _override_current_user

    async def _fake_emotion_pipeline(**_kwargs):
        return EmotionShiftAnalysis(
            is_dissonance_detected=False,
            dissonance_type="None",
            root_cause="none",
            counterfactual_correction="none",
            evidence_quotes=[],
            citations=[],
        )

    async def _fake_grounded_checks(**_kwargs):
        return (
            ProcessAdherenceReport(
                detected_topic="refund_request",
                is_resolved=True,
                efficiency_score=9,
                justification="ok",
                missing_sop_steps=[],
                evidence_quotes=[],
                citations=[],
            ),
            NLIEvaluation(
                nli_category="Entailment",
                justification="ok",
                evidence_quotes=[],
                citations=[],
                confidence_score=0.95,
            ),
        )

    async def _fake_transcript_policy(**_kwargs):
        return None

    async def _fake_policy_context(**_kwargs):
        return SimpleNamespace(
            text="policy",
            version=None,
            effective_at=None,
            category=None,
            conflict_resolution_applied=False,
        )

    monkeypatch.setattr("app.llm_trigger.service._evaluate_emotion_pipeline", _fake_emotion_pipeline)
    monkeypatch.setattr("app.llm_trigger.service._evaluate_policy_and_sop_trigger_checks", _fake_grounded_checks)
    monkeypatch.setattr("app.llm_trigger.service._evaluate_transcript_policy_pipeline", _fake_transcript_policy)
    monkeypatch.setattr("app.llm_trigger.service._resolve_active_policy_context", _fake_policy_context)
    monkeypatch.setattr("app.llm_trigger.service.retrieve_policy_chunks", lambda **_kwargs: [])

    response = client.post(f"/api/v1/llm-trigger/interaction/{interaction_b.id}/run", json={})

    client.app.dependency_overrides.pop(get_current_user, None)
    client.app.dependency_overrides.pop(get_db, None)
    client.app.dependency_overrides.pop(get_session, None)
    session.close()

    assert response.status_code == 404
