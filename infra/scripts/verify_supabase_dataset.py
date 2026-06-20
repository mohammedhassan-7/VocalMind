#!/usr/bin/env python3
"""Verify telecom dataset on Supabase (direct pooler, not local Docker Postgres)."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO_ROOT / "storage" / "audio" / "nexalink" / "evaluation"
sys.path.insert(0, str(REPO_ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / "backend" / ".env")

MANAGER_EMAIL = "operations@vocalmind.dev"
MANAGER_PASSWORD = "NexaLink2026!"
DATASET_ORG_SLUG = "nexalink-operations"
CALL_RE = re.compile(r"CALL_(0[1-9]|1[0-9]|20)_", re.I)
RULE_RE = re.compile(r"\b((?:CS|FIN|SEC)-RULE-\d+)\b", re.I)

# Calls with known GT coverage FAIL notes (Prompt 56 mapping).
EXPECTED_VIOLATION_CALLS = {
    "02",
    "06",
    "07",
    "09",
    "10",
    "11",
}


def supabase_dsn() -> str:
    url = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL", "")
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    if "supabase.com" not in url:
        raise RuntimeError("SUPABASE_DB_URL / DATABASE_URL must point at Supabase pooler")
    return url


def expected_violation_summary(call_num: str) -> str:
    gt_path = None
    for path in EVAL_DIR.glob(f"CALL_{call_num}_*.json"):
        gt_path = path
        break
    if not gt_path or not gt_path.is_file():
        return "unknown"
    gt = json.loads(gt_path.read_text(encoding="utf-8"))
    rules: list[str] = []
    for item in gt.get("coverage") or []:
        notes = item.get("notes") or ""
        if "fail" in notes.lower():
            rules.extend(rid.upper() for rid in RULE_RE.findall(notes))
    ref = gt.get("expected_outcome") or ""
    extras: list[str] = []
    if "interruption" in ref.lower() or "talks over" in ref.lower():
        extras.append("interruption")
    if "dismissive" in ref.lower():
        extras.append("dismissive_tone")
    if "forbidden phrase" in ref.lower():
        extras.append("forbidden_phrase")
    parts = sorted(set(rules)) + extras
    return ", ".join(parts) if parts else "none"


async def check_audio_resolves(audio_path: str | None) -> bool:
    if not audio_path:
        return False
    try:
        from app.core.audio_resolver import supabase_object_exists
    except Exception:
        return bool(audio_path.startswith("recordings/"))

    return await supabase_object_exists(audio_path)


async def db_verify(conn: asyncpg.Connection) -> dict:
    org = await conn.fetchrow(
        "SELECT id, name, slug FROM organizations WHERE slug = $1", DATASET_ORG_SLUG
    )
    mgr = await conn.fetchrow(
        "SELECT id, email, organization_id, role FROM users WHERE email = $1", MANAGER_EMAIL
    )
    if not org or not mgr:
        return {"error": "missing org or manager", "org": bool(org), "manager": bool(mgr)}

    interactions = await conn.fetch(
        """
        SELECT id, audio_file_path
        FROM interactions
        WHERE organization_id = $1
        ORDER BY audio_file_path
        """,
        org["id"],
    )

    per_call: list[dict] = []
    for row in interactions:
        path = row["audio_file_path"] or ""
        match = CALL_RE.search(path)
        if not match:
            continue
        call_num = match.group(1)
        viol_count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM policy_compliance pc
            WHERE pc.interaction_id = $1 AND pc.is_compliant = false
            """,
            row["id"],
        )
        viol_titles = await conn.fetch(
            """
            SELECT cp.policy_title, pc.evidence_text
            FROM policy_compliance pc
            JOIN company_policies cp ON cp.id = pc.policy_id
            WHERE pc.interaction_id = $1 AND pc.is_compliant = false
            ORDER BY cp.policy_title
            """,
            row["id"],
        )
        audio_ok = await check_audio_resolves(path)
        expected = expected_violation_summary(call_num)
        per_call.append(
            {
                "call": f"CALL_{call_num}",
                "expected": expected,
                "actual_count": viol_count,
                "actual_titles": [r["policy_title"] for r in viol_titles],
                "audio_present": audio_ok,
                "audio_path": path,
            }
        )

    call_nums = [row["call"].split("_")[1] for row in per_call]

    trees = await conn.fetchrow(
        """
        SELECT
          (SELECT COUNT(*) FROM interactions i WHERE i.organization_id = $1) AS interactions,
          (SELECT COUNT(*) FROM policy_compliance pc
             JOIN interactions i ON i.id = pc.interaction_id
             WHERE i.organization_id = $1 AND pc.is_compliant = false) AS policy_violations,
          (SELECT COUNT(*) FROM interaction_scores s
             JOIN interactions i ON i.id = s.interaction_id WHERE i.organization_id = $1) AS scores,
          (SELECT COUNT(*) FROM transcripts t
             JOIN interactions i ON i.id = t.interaction_id WHERE i.organization_id = $1) AS transcripts,
          (SELECT COUNT(*) FROM utterances u
             JOIN interactions i ON i.id = u.interaction_id WHERE i.organization_id = $1) AS utterances,
          (SELECT COUNT(*) FROM emotion_events e
             JOIN interactions i ON i.id = e.interaction_id WHERE i.organization_id = $1) AS emotion_events,
          (SELECT COUNT(*) FROM interaction_llm_trigger_cache c
             JOIN interactions i ON i.id = c.interaction_id WHERE i.organization_id = $1) AS llm_cache
        """,
        org["id"],
    )

    nexalink_count = await conn.fetchval(
        """
        SELECT COUNT(*) FROM interactions i
        JOIN organizations o ON o.id = i.organization_id
        WHERE o.slug = 'nexalink'
        """
    )

    violation_mismatches = [
        row
        for row in per_call
        if row["call"].split("_")[1] in EXPECTED_VIOLATION_CALLS and row["actual_count"] == 0
    ]
    audio_missing = [row for row in per_call if not row["audio_present"]]

    return {
        "org_id": str(org["id"]),
        "org_slug": org["slug"],
        "manager_org_match": str(mgr["organization_id"]) == str(org["id"]),
        "interaction_count": len(interactions),
        "call_numbers": sorted(set(call_nums), key=int),
        "expected_calls": len(set(call_nums)) == 20 and set(call_nums) == {f"{n:02d}" for n in range(1, 21)},
        "trees": dict(trees) if trees else {},
        "per_call": per_call,
        "violation_mismatches": violation_mismatches,
        "audio_missing_count": len(audio_missing),
        "nexalink_org_interaction_count_unchanged_check": nexalink_count,
    }


def api_verify(base: str, expected: int = 20) -> dict:
    form = urllib.parse.urlencode({"username": MANAGER_EMAIL, "password": MANAGER_PASSWORD}).encode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/auth/login/access-token",
        data=form,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            token = json.loads(resp.read().decode())["access_token"]
    except urllib.error.HTTPError as exc:
        return {"login_ok": False, "error": f"HTTP {exc.code}"}

    list_req = urllib.request.Request(
        f"{base.rstrip('/')}/interactions",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(list_req, timeout=60) as resp:
        rows = json.loads(resp.read().decode())

    paths = [r.get("audioFilePath") or "" for r in rows]
    calls = sorted({CALL_RE.search(p).group(1) for p in paths if CALL_RE.search(p)}, key=int)

    sample_violations: dict[str, int] = {}
    for call_label in ("09", "11", "04"):
        match_row = next((r for r in rows if f"CALL_{call_label}_" in (r.get("audioFilePath") or "")), None)
        if not match_row:
            continue
        detail_req = urllib.request.Request(
            f"{base.rstrip('/')}/interactions/{match_row['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(detail_req, timeout=60) as resp:
            detail = json.loads(resp.read().decode())
        sample_violations[f"CALL_{call_label}"] = len(detail.get("policyViolations") or [])

    return {
        "login_ok": True,
        "list_count": len(rows),
        "call_numbers": calls,
        "exactly_20": len(rows) == expected and len(calls) == expected,
        "sample_policy_violation_counts": sample_violations,
    }


def print_summary_table(per_call: list[dict]) -> None:
    print("\n=== Call summary ===")
    print(f"{'Call':<10} {'Expected':<45} {'Actual#':<8} {'Audio':<6}")
    print("-" * 90)
    for row in sorted(per_call, key=lambda r: r["call"]):
        print(
            f"{row['call']:<10} {row['expected'][:44]:<45} {row['actual_count']:<8} "
            f"{'yes' if row['audio_present'] else 'no':<6}"
        )


async def main() -> int:
    conn = await asyncpg.connect(supabase_dsn())
    db = await db_verify(conn)
    await conn.close()
    print("=== Supabase direct ===")
    print(json.dumps({k: v for k, v in db.items() if k != "per_call"}, indent=2, default=str))
    if db.get("per_call"):
        print_summary_table(db["per_call"])

    api = api_verify("http://localhost:8000/api/v1")
    print("\n=== Manager API (localhost:8000) ===")
    print(json.dumps(api, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
