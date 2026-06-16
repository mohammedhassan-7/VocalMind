from uuid import UUID

from app.api.deps import get_current_user, get_db, get_session
from app.models.enums import UserRole
from app.models.user import User


def test_emotion_comparison_query_is_joined_with_interaction_org_scope(client):
    seen_statements = []

    class _FakeExecResult:
        def __init__(self, first_value=None, all_values=None):
            self._first = first_value
            self._all = all_values or []

        def first(self):
            return self._first

        def all(self):
            return self._all

    class _FakeSession:
        async def exec(self, statement):
            seen_statements.append(str(statement))
            if len(seen_statements) == 1:
                return _FakeExecResult(first_value=object())
            return _FakeExecResult(all_values=[])

    async def _override_get_db():
        yield _FakeSession()

    async def _override_get_session():
        yield _FakeSession()

    async def _override_current_user():
        return User(
            id=UUID("b0000000-0000-0000-0000-000000000001"),
            organization_id=UUID("a0000000-0000-0000-0000-000000000001"),
            email="manager@orga.local",
            password_hash="hash",
            name="Manager A",
            role=UserRole.manager,
            is_active=True,
        )

    client.app.dependency_overrides[get_db] = _override_get_db
    client.app.dependency_overrides[get_session] = _override_get_session
    client.app.dependency_overrides[get_current_user] = _override_current_user

    response = client.get("/api/v1/interactions/c0000000-0000-0000-0000-000000000001/emotion-comparison")

    client.app.dependency_overrides.pop(get_current_user, None)
    client.app.dependency_overrides.pop(get_db, None)
    client.app.dependency_overrides.pop(get_session, None)

    assert response.status_code == 200
    assert len(seen_statements) >= 2
    utterance_query = seen_statements[1].lower()
    assert "join interactions" in utterance_query
    assert "interactions.organization_id" in utterance_query
