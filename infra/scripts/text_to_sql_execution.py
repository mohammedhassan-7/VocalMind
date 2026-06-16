#!/usr/bin/env python3
"""Execute and compare text_to_sql queries against the dev Postgres DB."""
from __future__ import annotations

import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if "```" in text:
        for part in text.split("```"):
            cleaned = part.strip()
            if cleaned.lower().startswith("sql"):
                cleaned = cleaned[3:].strip()
            if cleaned.upper().startswith(("SELECT", "WITH")):
                return cleaned.rstrip(";")
    return text.rstrip(";")


def _normalize_cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.4f}"
    if isinstance(v, Decimal):
        return f"{float(v):.4f}"
    return str(v).strip()


def execute_sql(sql: str, *, cwd: Path | None = None) -> tuple[list[str], list[tuple[str, ...]], str | None]:
    """Run SQL via docker compose psql; return (columns, rows, error)."""
    # SECURITY NOTE: This helper is benchmark/dev-only infrastructure and is not a
    # production execution path. Do not wire this to live tenant-facing databases.
    sql = _strip_fences(sql)
    if not sql.strip():
        return [], [], "empty sql"
    if FORBIDDEN.search(sql):
        return [], [], "forbidden write/ddl keyword"
    cwd = cwd or ROOT
    proc = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            "vocalmind",
            "-d",
            "vocalmind",
            "-t",
            "-A",
            "-F",
            "\t",
            "-c",
            sql,
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "psql error").strip().split("\n")[0]
        return [], [], err[:300]
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    if not lines:
        return [], [], None
    # psql -A -F tab: first line may be header if not -t only... with -t no headers
    # Use JSON output instead for clarity
    proc2 = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            "vocalmind",
            "-d",
            "vocalmind",
            "-c",
            f"SELECT COALESCE(json_agg(t), '[]'::json) FROM ({sql}) t",
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc2.returncode != 0:
        return [], [], (proc2.stderr or "json wrap failed")[:300]
    raw_out = proc2.stdout
    # psql wraps long JSON across lines with '+' continuation markers
    cleaned = re.sub(r"\s*\+\s*", "", raw_out)
    cleaned = re.sub(r"\([^)]*\)", "", cleaned)  # strip row count footer
    m = re.search(r"(\[.*\])", cleaned, re.DOTALL)
    if not m:
        return [], [], "no json result"
    json_blob = m.group(1).replace("\n", " ").strip()
    try:
        data = json.loads(json_blob)
    except json.JSONDecodeError as exc:
        return [], [], f"json parse: {exc}"
    if not data:
        return [], [], None
    if not isinstance(data, list):
        return [], [], "unexpected json shape"
    cols = list(data[0].keys()) if data and isinstance(data[0], dict) else []
    rows = [tuple(_normalize_cell(row.get(c)) for c in cols) for row in data if isinstance(row, dict)]
    return cols, rows, None


def _normalize_columns(cols: list[str]) -> list[str]:
    return [c.lower().split(".")[-1] for c in cols]


def compare_result_sets(
    ref_cols: list[str],
    ref_rows: list[tuple[str, ...]],
    got_cols: list[str],
    got_rows: list[tuple[str, ...]],
) -> tuple[int, str]:
    """Return (score 0|3|7|10, reasoning)."""
    if not ref_cols and not ref_rows and not got_cols and not got_rows:
        return 10, "both result sets empty (match)"
    if not ref_cols and not ref_rows:
        return 0, "reference query returned no parseable result"
    rc = _normalize_columns(ref_cols)
    gc = _normalize_columns(got_cols)
    if len(ref_rows) != len(got_rows):
        return 3, f"row count mismatch: ref={len(ref_rows)} got={len(got_rows)}"
    if len(rc) != len(gc):
        return 3, f"column count mismatch: ref={len(rc)} got={len(gc)}"
    ref_sorted = sorted(ref_rows)
    if set(rc) == set(gc):
        idx = [gc.index(c) for c in rc]
        got_aligned = [tuple(r[i] for i in idx) for r in got_rows]
    else:
        # Allow alias differences when column counts match — compare positionally after sort
        got_aligned = list(got_rows)
    got_sorted = sorted(got_aligned)
    if ref_sorted == got_sorted:
        if set(rc) == set(gc):
            return 10, "result sets match (columns + rows)"
        return 10, f"result sets match (rows; alias diff ref={rc} got={gc})"
    mismatches = sum(1 for a, b in zip(ref_sorted, got_sorted) if a != b)
    ratio = mismatches / max(len(ref_sorted), 1)
    if ratio <= 0.2:
        return 7, f"minor value mismatches ({mismatches}/{len(ref_sorted)} rows differ)"
    return 3, f"value mismatch on {mismatches}/{len(ref_sorted)} rows"


def score_sql_execution(model_sql: str, reference_sql: str) -> dict[str, Any]:
    ref_cols, ref_rows, ref_err = execute_sql(reference_sql)
    if ref_err:
        return {
            "judge_score_0_to_10": None,
            "judge_pass": False,
            "judge_reasoning": f"reference_sql_failed: {ref_err}",
            "error": "reference_sql_failed",
            "scoring_method": "execution",
        }
    got_cols, got_rows, got_err = execute_sql(model_sql)
    if got_err:
        return {
            "judge_score_0_to_10": 0.0,
            "judge_pass": False,
            "judge_reasoning": f"model_sql_error: {got_err}",
            "scoring_method": "execution",
        }
    score, reason = compare_result_sets(ref_cols, ref_rows, got_cols, got_rows)
    return {
        "judge_score_0_to_10": float(score),
        "judge_pass": score >= 7,
        "judge_reasoning": reason,
        "scoring_method": "execution",
        "ref_row_count": len(ref_rows),
        "got_row_count": len(got_rows),
    }


if __name__ == "__main__":
    import sys

    ref = sys.argv[1] if len(sys.argv) > 2 else "SELECT 1 AS one"
    got = sys.argv[2] if len(sys.argv) > 2 else "SELECT 1 AS one"
    print(json.dumps(score_sql_execution(got, ref), indent=2))
