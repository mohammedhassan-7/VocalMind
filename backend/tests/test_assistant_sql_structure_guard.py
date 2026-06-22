from uuid import UUID

from app.api.deps import get_current_user
from app.models.enums import UserRole
from app.models.user import User


def _override_manager():
    async def _inner():
        return User(
            id=UUID("b0000000-0000-0000-0000-000000000001"),
            organization_id=UUID("a0000000-0000-0000-0000-000000000001"),
            email="manager@test.local",
            password_hash="hash",
            name="Manager",
            role=UserRole.manager,
            is_active=True,
        )

    return _inner


class _FakeRow:
    def __init__(self, d):
        self._mapping = d

class _FakeResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def __iter__(self):
        return iter([_FakeRow(r) for r in self._rows])

    def all(self):
        return self._rows

    def scalar(self):
        from uuid import UUID
        return UUID("c0000000-0000-0000-0000-000000000001")


class _FakeConn:
    def __init__(self, rows=None):
        self._rows = rows or []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, _statement, *_args, **_kwargs):
        return _FakeResult(self._rows)

    async def commit(self):
        return None

    async def rollback(self):
        return None


class _FakeEngine:
    def __init__(self, rows=None):
        self._rows = rows or []

    def connect(self):
        return _FakeConn(self._rows)


def test_assistant_rejects_select_star_exfiltration(client, monkeypatch):
    async def _fake_resolve_sql(_self, _q, _org_id, _conversation_block="", **_kwargs):
        return "SELECT * FROM interactions WHERE organization_id = 'a0000000-0000-0000-0000-000000000001' LIMIT 50"

    monkeypatch.setattr("app.api.routes.assistant.engine", _FakeEngine())
    monkeypatch.setattr("app.api.routes.assistant.IntentResolver.resolve_sql", _fake_resolve_sql)
    client.app.dependency_overrides[get_current_user] = _override_manager()

    response = client.post("/api/v1/assistant/query", json={"query_text": "show all", "mode": "chat"})

    client.app.dependency_overrides.pop(get_current_user, None)
    body = response.json()
    assert response.status_code == 200
    assert body.get("success") is False
    assert "safe analytics queries" in body.get("content", "").lower()
    assert "wildcard projection" in body.get("content", "").lower()


def test_assistant_rejects_multi_statement_injection(client, monkeypatch):
    async def _fake_resolve_sql(_self, _q, _org_id, _conversation_block="", **_kwargs):
        return (
            "SELECT id FROM interactions WHERE organization_id = 'a0000000-0000-0000-0000-000000000001' LIMIT 10; "
            "DROP TABLE users"
        )

    monkeypatch.setattr("app.api.routes.assistant.engine", _FakeEngine())
    monkeypatch.setattr("app.api.routes.assistant.IntentResolver.resolve_sql", _fake_resolve_sql)
    client.app.dependency_overrides[get_current_user] = _override_manager()

    response = client.post("/api/v1/assistant/query", json={"query_text": "do attack", "mode": "chat"})

    client.app.dependency_overrides.pop(get_current_user, None)
    body = response.json()
    assert response.status_code == 200
    assert body.get("success") is False
    assert "safe analytics queries" in body.get("content", "").lower()
    assert "exactly one statement" in body.get("content", "").lower()


def test_assistant_accepts_valid_prompt_examples(client, monkeypatch):
    async def _fake_resolve_sql(_self, _q, _org_id, _conversation_block="", **_kwargs):
        return (
            "SELECT u.name, ROUND(AVG(s.overall_score)::NUMERIC * 10, 1) AS avg_score "
            "FROM users u JOIN interactions i ON i.agent_id = u.id AND i.organization_id = 'a0000000-0000-0000-0000-000000000001' "
            "JOIN interaction_scores s ON s.interaction_id = i.id WHERE u.role = 'agent' "
            "GROUP BY u.id, u.name ORDER BY avg_score DESC LIMIT 5"
        )

    monkeypatch.setattr("app.api.routes.assistant.engine", _FakeEngine())
    monkeypatch.setattr("app.api.routes.assistant.assistant_sql_engine", _FakeEngine([{"name": "Agent A", "avg_score": 8.5}]))
    monkeypatch.setattr("app.api.routes.assistant.IntentResolver.resolve_sql", _fake_resolve_sql)
    monkeypatch.setattr("app.api.routes.assistant.IntentResolver.synthesize_answer", lambda *_a, **_k: "synthesized answer")
    client.app.dependency_overrides[get_current_user] = _override_manager()

    response = client.post("/api/v1/assistant/query", json={"query_text": "show top agents", "mode": "chat"})

    client.app.dependency_overrides.pop(get_current_user, None)
    body = response.json()
    assert response.status_code == 200
    # Should be success since valid aliases and type casts are used
    assert body.get("success") is True


def test_assistant_rejects_restricted_column_in_where(client, monkeypatch):
    async def _fake_resolve_sql(_self, _q, _org_id, _conversation_block="", **_kwargs):
        return (
            "SELECT u.id FROM users u WHERE u.password_hash LIKE 'a%' AND u.organization_id = 'a0000000-0000-0000-0000-000000000001' LIMIT 50"
        )

    monkeypatch.setattr("app.api.routes.assistant.engine", _FakeEngine())
    monkeypatch.setattr("app.api.routes.assistant.IntentResolver.resolve_sql", _fake_resolve_sql)
    client.app.dependency_overrides[get_current_user] = _override_manager()

    response = client.post("/api/v1/assistant/query", json={"query_text": "attack", "mode": "chat"})

    client.app.dependency_overrides.pop(get_current_user, None)
    body = response.json()
    assert response.status_code == 200
    assert body.get("success") is False
    assert "safe analytics queries" in body.get("content", "").lower()
    assert "password_hash" in body.get("content", "").lower()
