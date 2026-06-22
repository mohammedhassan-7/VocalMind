"""
Edge-case coverage for the Manager Assistant SQL guardrails.

These tests target the validator/guard helpers directly (pure functions, no DB,
no LLM) so they exercise the boundary between "safe analytics query we must let
through" and "unsafe / malformed query we must reject". They complement the
HTTP-level tests in test_assistant_sql_structure_guard.py.
"""
import pytest

from app.api.routes.assistant import (
    _build_ordinal_followup_sql,
    _deterministic_ordinal_answer,
    _is_org_scoped_sql,
    _neutralize_func_from,
    _ordinal_followup_offset,
    _parse_sql_from_model_output,
    _validate_sql_structure,
)
from uuid import UUID

ORG = "a0000000-0000-0000-0000-000000000001"
OTHER_ORG = "b0000000-0000-0000-0000-000000000002"


def _scoped(body: str) -> str:
    """Wrap a WHERE-bearing query body that already references ORG."""
    return body


# ---------------------------------------------------------------------------
# Aggregates and functions the prompt actively encourages must be ACCEPTED.
# (Regression guard for the COUNT(*) / function-name / EXTRACT bugs.)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "sql",
    [
        # COUNT(*) — the single most common aggregate, and a built-in few-shot example.
        f"SELECT emotion, COUNT(*) AS count FROM utterances u "
        f"JOIN interactions i ON u.interaction_id = i.id "
        f"WHERE u.speaker_role = 'customer' AND i.organization_id = '{ORG}' "
        f"GROUP BY emotion ORDER BY count DESC LIMIT 10",
        # COUNT(*) with no alias / no GROUP BY.
        f"SELECT COUNT(*) AS c FROM interactions WHERE organization_id = '{ORG}' LIMIT 1",
        # Scalar function in WHERE.
        f"SELECT u.name FROM users u WHERE LOWER(u.name) LIKE 'a%' "
        f"AND u.organization_id = '{ORG}' LIMIT 50",
        # EXTRACT(field FROM column) — inner FROM must not read as a table.
        f"SELECT EXTRACT(MONTH FROM i.interaction_date) AS m, COUNT(*) AS c "
        f"FROM interactions i WHERE i.organization_id = '{ORG}' GROUP BY m LIMIT 12",
        # TO_CHAR formatting.
        f"SELECT TO_CHAR(i.interaction_date, 'YYYY-MM') AS ym, COUNT(*) AS n "
        f"FROM interactions i WHERE i.organization_id = '{ORG}' GROUP BY ym LIMIT 50",
        # CASE expression + SUM over a joined alias.
        f"SELECT u.name, SUM(CASE WHEN s.was_resolved THEN 1 ELSE 0 END) AS resolved "
        f"FROM users u JOIN interactions i ON i.agent_id = u.id "
        f"JOIN interaction_scores s ON s.interaction_id = i.id "
        f"WHERE i.organization_id = '{ORG}' GROUP BY u.id, u.name LIMIT 50",
        # date_trunc + COALESCE.
        f"SELECT date_trunc('week', i.interaction_date) AS wk, "
        f"COALESCE(AVG(s.overall_score), 0) AS avg FROM interactions i "
        f"JOIN interaction_scores s ON s.interaction_id = i.id "
        f"WHERE i.organization_id = '{ORG}' GROUP BY wk LIMIT 50",
    ],
)
def test_validator_accepts_legitimate_analytics_sql(sql):
    # Should not raise.
    _validate_sql_structure(sql)


# ---------------------------------------------------------------------------
# Unsafe / malformed queries must still be REJECTED.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "sql,needle",
    [
        # Sensitive column, qualified.
        (f"SELECT u.password_hash FROM users u WHERE u.organization_id = '{ORG}' LIMIT 5",
         "password_hash"),
        # Sensitive column, bare.
        (f"SELECT password_hash FROM users WHERE organization_id = '{ORG}' LIMIT 5",
         "password_hash"),
        # Wildcard projection.
        (f"SELECT * FROM interactions WHERE organization_id = '{ORG}' LIMIT 50",
         "Wildcard"),
        # Qualified wildcard.
        (f"SELECT i.* FROM interactions i WHERE i.organization_id = '{ORG}' LIMIT 50",
         "Wildcard"),
        # Second statement smuggled in.
        (f"SELECT id FROM interactions WHERE organization_id = '{ORG}' LIMIT 5; DROP TABLE users",
         "one statement"),
        # Missing LIMIT.
        (f"SELECT COUNT(*) FROM interactions WHERE organization_id = '{ORG}'",
         "LIMIT"),
        # LIMIT over the cap.
        (f"SELECT id FROM interactions WHERE organization_id = '{ORG}' LIMIT 9999",
         "exceeds"),
        # Unknown table.
        (f"SELECT secret FROM admin_secrets WHERE organization_id = '{ORG}' LIMIT 1",
         "disallowed tables"),
        # Reference to an alias that was never defined.
        (f"SELECT x.name FROM users u WHERE u.organization_id = '{ORG}' LIMIT 5",
         "unknown table alias"),
    ],
)
def test_validator_rejects_unsafe_sql(sql, needle):
    with pytest.raises(ValueError) as exc:
        _validate_sql_structure(sql)
    assert needle.lower() in str(exc.value).lower()


def test_neutralize_func_from_handles_multiple_extracts():
    sql = (
        "SELECT EXTRACT(YEAR FROM i.interaction_date), "
        "EXTRACT(MONTH FROM i.interaction_date) FROM interactions i LIMIT 5"
    )
    out = _neutralize_func_from(sql)
    # Inner FROMs replaced; the real table-source FROM (before `interactions`) stays.
    assert "from i.interaction_date" not in out.lower()
    assert "from interactions" in out.lower()


# ---------------------------------------------------------------------------
# Tenant scoping guard.
# ---------------------------------------------------------------------------

def test_org_scope_accepts_scoped_query():
    sql = f"SELECT id FROM interactions WHERE organization_id = '{ORG}' LIMIT 5"
    assert _is_org_scoped_sql(sql, UUID(ORG)) is True


def test_org_scope_rejects_unscoped_query():
    sql = "SELECT id, email FROM users LIMIT 10"
    assert _is_org_scoped_sql(sql, UUID(ORG)) is False


def test_org_scope_rejects_wrong_org():
    sql = f"SELECT id FROM interactions WHERE organization_id = '{OTHER_ORG}' LIMIT 5"
    assert _is_org_scoped_sql(sql, UUID(ORG)) is False


def test_org_scope_ignores_org_id_hidden_in_string_literal():
    # The caller's org id appearing only inside an unrelated string literal must
    # NOT satisfy the scoping requirement.
    sql = (
        f"SELECT id FROM interactions WHERE language_detected = '{ORG}' "
        f"AND organization_id = '{OTHER_ORG}' LIMIT 5"
    )
    assert _is_org_scoped_sql(sql, UUID(ORG)) is False


# ---------------------------------------------------------------------------
# Ordinal follow-up helpers.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "question,expected",
    [
        ("who is the second one", 1),
        ("show the 3rd result", 2),
        ("first one please", 0),
        ("the FIFTH agent", 4),
        ("top agents", None),
        ("", None),
    ],
)
def test_ordinal_offset_parsing(question, expected):
    assert _ordinal_followup_offset(question) == expected


def test_ordinal_followup_sql_strips_limit_and_offset_then_reapplies():
    prev = "SELECT name FROM leaderboard ORDER BY score DESC LIMIT 10 OFFSET 5"
    out = _build_ordinal_followup_sql(prev, 2)
    assert out is not None
    assert "WITH prev AS (SELECT name FROM leaderboard ORDER BY score DESC)" in out
    assert out.rstrip().endswith("OFFSET 2")


def test_ordinal_followup_sql_returns_none_on_empty():
    assert _build_ordinal_followup_sql("", 1) is None


def test_deterministic_ordinal_answer_handles_empty_rows():
    answer = _deterministic_ordinal_answer(1, [])
    assert "second" in answer.lower()
    assert "couldn't" in answer.lower()


def test_deterministic_ordinal_answer_uses_real_values():
    answer = _deterministic_ordinal_answer(0, [{"name": "Sara", "avg_score": 9.1}])
    assert "Sara" in answer
    assert "9.1" in answer


# ---------------------------------------------------------------------------
# SQL extraction from messy model output.
# ---------------------------------------------------------------------------

def test_parse_sql_returns_none_for_prose_only():
    assert _parse_sql_from_model_output("I cannot answer that question.") is None


def test_parse_sql_returns_none_for_empty():
    assert _parse_sql_from_model_output("") is None
    assert _parse_sql_from_model_output(None) is None


def test_parse_sql_prefers_top_level_with_cte():
    raw = "```sql\nWITH t AS (SELECT 1 AS n) SELECT n FROM t LIMIT 1\n```"
    assert _parse_sql_from_model_output(raw) == "WITH t AS (SELECT 1 AS n) SELECT n FROM t LIMIT 1"


def test_parse_sql_drops_trailing_semicolon():
    raw = "SELECT id FROM users LIMIT 1;"
    assert _parse_sql_from_model_output(raw) == "SELECT id FROM users LIMIT 1"
