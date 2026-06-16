from uuid import UUID

from app.api.deps import get_current_user
from app.models.enums import UserRole
from app.models.user import User


def test_rag_query_internal_error_is_sanitized(client, monkeypatch):
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

    class _BrokenEngine:
        def query_answer(self, question: str, org_filter: str | None = None):  # noqa: ARG002
            raise RuntimeError("Qdrant tcp://internal-host:6333 unreachable")

        def query_compliance(self, text: str, org_filter: str | None = None):  # noqa: ARG002
            raise RuntimeError("Qdrant tcp://internal-host:6333 unreachable")

    client.app.dependency_overrides[get_current_user] = _override_current_user
    monkeypatch.setattr("app.api.routes.rag._get_engine", lambda: _BrokenEngine())

    response = client.post("/api/v1/rag/query", json={"query": "show policy", "mode": "answer"})

    client.app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 500
    body = response.json()
    assert "internal-host" not in str(body)
    assert "qdrant" not in str(body).lower()
    assert "detail" in body
    assert "Reference ID:" in body["detail"]
