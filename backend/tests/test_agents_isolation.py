from datetime import datetime
from uuid import UUID

from sqlalchemy.sql.sqltypes import Uuid
from sqlmodel import SQLModel, Session, create_engine

from app.api.deps import get_current_user, get_db, get_session
from app.models.enums import ProcessingStatus, UserRole
from app.models.interaction import Interaction
from app.models.interaction_score import InteractionScore
from app.models.organization import Organization
from app.models.user import User

_original_uuid_bind_processor = Uuid.bind_processor


def _sqlite_safe_uuid_bind_processor(self, dialect):
    processor = _original_uuid_bind_processor(self, dialect)
    if processor is None:
        return None

    def safe_process(value):
        if value is not None and isinstance(value, str):
            try:
                value = UUID(value)
            except ValueError:
                pass
        return processor(value)

    return safe_process


Uuid.bind_processor = _sqlite_safe_uuid_bind_processor


def test_agent_profile_excludes_cross_org_interactions(client, tmp_path):
    db_path = tmp_path / "agents_cross_org.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    session = Session(engine)

    org_a = Organization(id=UUID("a0000000-0000-0000-0000-000000000001"), name="Org A", slug="org-a")
    org_b = Organization(id=UUID("a0000000-0000-0000-0000-000000000002"), name="Org B", slug="org-b")

    manager_a = User(
        id=UUID("b0000000-0000-0000-0000-000000000001"),
        organization_id=org_a.id,
        email="manager@orga.local",
        password_hash="hash",
        name="Manager A",
        role=UserRole.manager,
        is_active=True,
    )
    shared_agent_id = UUID("b0000000-0000-0000-0000-000000000010")
    agent_a = User(
        id=shared_agent_id,
        organization_id=org_a.id,
        email="agent@orga.local",
        password_hash="hash",
        name="Agent Shared",
        role=UserRole.agent,
        is_active=True,
    )
    # Deliberately malformed legacy-style row to simulate collision/drift:
    # same agent UUID appears in org B interactions and should not be counted for org A manager.
    agent_b_shadow = User(
        id=UUID("b0000000-0000-0000-0000-000000000020"),
        organization_id=org_b.id,
        email="agent@orgb.local",
        password_hash="hash",
        name="Agent B",
        role=UserRole.agent,
        is_active=True,
    )
    session.add_all([org_a, org_b, manager_a, agent_a, agent_b_shadow])
    session.commit()

    interaction_a = Interaction(
        id=UUID("c0000000-0000-0000-0000-000000000001"),
        organization_id=org_a.id,
        agent_id=shared_agent_id,
        uploaded_by=manager_a.id,
        audio_file_path="org-a/a.wav",
        file_size_bytes=100,
        duration_seconds=60,
        file_format="wav",
        interaction_date=datetime.utcnow(),
        processing_status=ProcessingStatus.completed,
    )
    interaction_b = Interaction(
        id=UUID("c0000000-0000-0000-0000-000000000002"),
        organization_id=org_b.id,
        agent_id=shared_agent_id,
        uploaded_by=agent_b_shadow.id,
        audio_file_path="org-b/b.wav",
        file_size_bytes=100,
        duration_seconds=60,
        file_format="wav",
        interaction_date=datetime.utcnow(),
        processing_status=ProcessingStatus.completed,
    )
    session.add_all([interaction_a, interaction_b])
    session.commit()

    score_a = InteractionScore(
        id=UUID("d0000000-0000-0000-0000-000000000001"),
        interaction_id=interaction_a.id,
        overall_score=0.8,
        empathy_score=0.8,
        policy_score=0.8,
        resolution_score=0.8,
        avg_response_time_seconds=2.0,
        was_resolved=True,
    )
    score_b = InteractionScore(
        id=UUID("d0000000-0000-0000-0000-000000000002"),
        interaction_id=interaction_b.id,
        overall_score=0.0,
        empathy_score=0.0,
        policy_score=0.0,
        resolution_score=0.0,
        avg_response_time_seconds=30.0,
        was_resolved=False,
    )
    session.add_all([score_a, score_b])
    session.commit()

    from tests.conftest import AsyncSessionAdapter
    adapter = AsyncSessionAdapter(session)

    async def _override_get_db():
        yield adapter

    async def _override_get_session():
        yield adapter

    async def _override_current_user():
        return manager_a

    client.app.dependency_overrides[get_db] = _override_get_db
    client.app.dependency_overrides[get_session] = _override_get_session
    client.app.dependency_overrides[get_current_user] = _override_current_user

    response = client.get(f"/api/v1/agents/{shared_agent_id}")

    client.app.dependency_overrides.pop(get_current_user, None)
    client.app.dependency_overrides.pop(get_db, None)
    client.app.dependency_overrides.pop(get_session, None)
    session.close()

    assert response.status_code == 200
    payload = response.json()
    assert payload["totalCalls"] == 1
    assert payload["resolutionRate"] == 100
