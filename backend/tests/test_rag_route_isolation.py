from types import SimpleNamespace
from uuid import UUID

from app.api.deps import get_current_user
from app.models.enums import UserRole
from app.models.user import User


def test_rag_query_ignores_client_org_filter_and_uses_current_user_org(client, monkeypatch):
    org_a = UUID("a0000000-0000-0000-0000-000000000001")
    org_b = UUID("a0000000-0000-0000-0000-000000000002")

    async def _override_current_user():
        return User(
            id=UUID("b0000000-0000-0000-0000-000000000001"),
            organization_id=org_a,
            email="manager@orga.local",
            password_hash="hash",
            name="Manager A",
            role=UserRole.manager,
            is_active=True,
        )

    client.app.dependency_overrides[get_current_user] = _override_current_user

    observed_org_filters: list[str | None] = []

    class FakeEngine:
        def query_compliance(self, text: str, org_filter: str | None = None):
            observed_org_filters.append(org_filter)
            return {"response": "ok", "chunks": [], "timing": {}}

        def query_answer(self, question: str, org_filter: str | None = None):
            observed_org_filters.append(org_filter)
            return {
                "response": "ok",
                "chunks": [
                    {
                        "rank": 1,
                        "score": 0.9,
                        "metadata": {"org": str(org_filter), "doc_type": "policy", "source_file": "policy.md"},
                        "text": "Scoped chunk",
                    }
                ],
                "timing": {"retrieval": 0.01, "synthesis": 0.0, "total": 0.01},
            }

    monkeypatch.setattr("app.api.routes.rag._get_engine", lambda: FakeEngine())

    response = client.post(
        "/api/v1/rag/query",
        json={
            "query": "show policy",
            "mode": "answer",
            "org_filter": str(org_b),
        },
    )

    client.app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    body = response.json()
    assert observed_org_filters == [str(org_a)]
    assert body["chunks"][0]["metadata"]["org"] == str(org_a)
