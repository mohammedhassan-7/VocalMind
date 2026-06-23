"""Knowledge-base versioning: snapshots, rollback, tagging, tenant isolation."""

from uuid import UUID

import pytest
from sqlalchemy.sql.sqltypes import Uuid
from sqlmodel import SQLModel, Session, create_engine, select

from app.api.deps import get_current_user, get_db, get_session
from app.models.enums import UserRole
from app.models.knowledge_version import KnowledgeVersion
from app.models.organization import Organization
from app.models.policy import CompanyPolicy
from app.models.user import User

# ── SQLite UUID compatibility shim (string UUIDs from path params) ───────────
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

ORG_A_ID = UUID("c0000000-0000-0000-0000-000000000001")
ORG_B_ID = UUID("c0000000-0000-0000-0000-000000000002")
USER_A_ID = UUID("c0000000-0000-0000-0000-0000000000a1")
USER_B_ID = UUID("c0000000-0000-0000-0000-0000000000b1")
AGENT_A_ID = UUID("c0000000-0000-0000-0000-0000000000a2")


@pytest.fixture
def versions_client(client, tmp_path):
    db_path = tmp_path / "kb_versions.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    test_session = Session(engine)

    test_session.add_all([
        Organization(id=ORG_A_ID, name="Org A", slug="org-a"),
        Organization(id=ORG_B_ID, name="Org B", slug="org-b"),
        User(id=USER_A_ID, organization_id=ORG_A_ID, email="a@org.local", password_hash="h",
             name="Mgr A", role=UserRole.manager, is_active=True),
        User(id=USER_B_ID, organization_id=ORG_B_ID, email="b@org.local", password_hash="h",
             name="Mgr B", role=UserRole.manager, is_active=True),
        User(id=AGENT_A_ID, organization_id=ORG_A_ID, email="agent@org.local", password_hash="h",
             name="Agent A", role=UserRole.agent, is_active=True),
    ])
    test_session.commit()

    from tests.conftest import AsyncSessionAdapter
    adapter = AsyncSessionAdapter(test_session)

    async def _override_get_db():
        yield adapter

    async def _override_get_session():
        yield adapter

    state = {"user_id": USER_A_ID}

    async def _override_current_user():
        return test_session.exec(select(User).where(User.id == state["user_id"])).first()

    client.app.dependency_overrides[get_current_user] = _override_current_user
    client.app.dependency_overrides[get_db] = _override_get_db
    client.app.dependency_overrides[get_session] = _override_get_session

    yield client, test_session, state

    client.app.dependency_overrides.pop(get_current_user, None)
    client.app.dependency_overrides.pop(get_db, None)
    client.app.dependency_overrides.pop(get_session, None)
    test_session.close()


def _create_policy(client, title, content="abc"):
    return client.post(
        "/api/v1/knowledge/policies",
        json={"title": title, "category": "Guidelines", "content": content},
    )


def test_mutation_creates_new_active_version(versions_client):
    client, session, _ = versions_client
    assert _create_policy(client, "Refund").status_code == 201
    assert _create_policy(client, "Privacy").status_code == 201

    resp = client.get("/api/v1/knowledge/versions")
    assert resp.status_code == 200
    versions = resp.json()
    # Baseline v1 (lazy) + one per create.
    numbers = sorted(v["versionNumber"] for v in versions)
    assert numbers[-1] == max(numbers)
    active = [v for v in versions if v["isActive"]]
    assert len(active) == 1
    assert active[0]["versionNumber"] == max(numbers)


def test_activate_restores_previous_snapshot(versions_client):
    client, session, _ = versions_client
    _create_policy(client, "Refund", content="v1 content")
    versions = client.get("/api/v1/knowledge/versions").json()
    snapshot_version_id = next(v["id"] for v in versions if v["isActive"])

    # Add a second policy → the snapshot above no longer reflects live state.
    _create_policy(client, "Privacy")
    assert session.exec(select(CompanyPolicy)).all().__len__() == 2

    # Re-activate the earlier version → second policy is pruned from live tables.
    resp = client.post(f"/api/v1/knowledge/versions/{snapshot_version_id}/activate")
    assert resp.status_code == 200
    titles = {p.policy_title for p in session.exec(select(CompanyPolicy)).all()}
    assert titles == {"Refund"}

    active = client.get("/api/v1/knowledge/versions/active").json()
    assert active["isActive"] is True


def test_activate_rejects_cross_org(versions_client):
    client, session, state = versions_client
    _create_policy(client, "Refund")
    org_a_version_id = client.get("/api/v1/knowledge/versions").json()[0]["id"]

    state["user_id"] = USER_B_ID  # switch to the other org's manager
    resp = client.post(f"/api/v1/knowledge/versions/{org_a_version_id}/activate")
    assert resp.status_code == 404


def test_versions_requires_manager(versions_client):
    client, session, state = versions_client
    state["user_id"] = AGENT_A_ID
    assert client.get("/api/v1/knowledge/versions").status_code == 403


def test_baseline_seeded_for_org_without_versions(versions_client):
    client, session, _ = versions_client
    # No mutations yet — listing should lazily seed a v1 baseline.
    versions = client.get("/api/v1/knowledge/versions").json()
    assert len(versions) == 1
    assert versions[0]["versionNumber"] == 1
    assert versions[0]["isActive"] is True
    assert session.exec(select(KnowledgeVersion)).first() is not None
