#!/usr/bin/env python3
"""Run agent flag -> manager review queue E2E checks against live API + Supabase."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / "backend" / ".env")

API = "http://localhost:8000/api/v1"
MANAGER_EMAIL = "operations@vocalmind.dev"
MANAGER_PASSWORD = "NexaLink2026!"
AGENT_EMAIL = "agent.daniel@nexalink.com"
AGENT_PASSWORD = "NexaLink2026!"
TARGET_CALL = "CALL_09"


def login(email: str, password: str) -> str:
    form = urllib.parse.urlencode({"username": email, "password": password}).encode()
    req = urllib.request.Request(
        f"{API}/auth/login/access-token",
        data=form,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["access_token"]


def api(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


async def supabase_counts(compliance_id: str) -> dict:
    url = os.environ["SUPABASE_DB_URL"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        row = await conn.fetchrow(
            "SELECT is_flagged, agent_flagged_by, agent_flag_note FROM policy_compliance WHERE id = $1",
            compliance_id,
        )
        notif = await conn.fetchval(
            "SELECT count(*) FROM notifications WHERE type = 'agent_flag_pending' AND payload->>'compliance_id' = $1",
            compliance_id,
        )
        return {"compliance": dict(row) if row else None, "notifications": notif}
    finally:
        await conn.close()


async def main() -> int:
    results: list[str] = []

    # Agent login
    try:
        agent_token = login(AGENT_EMAIL, AGENT_PASSWORD)
        results.append(f"PASS agent login ({AGENT_EMAIL})")
    except Exception as exc:
        results.append(f"FAIL agent login: {exc}")
        print("\n".join(results))
        return 1

    code, interactions = api("GET", "/interactions", agent_token)
    if code != 200:
        results.append(f"FAIL agent list interactions HTTP {code}")
        print("\n".join(results))
        return 1
    call = next((i for i in interactions if TARGET_CALL in (i.get("audioFilePath") or "")), None)
    if not call:
        results.append(f"FAIL agent cannot see {TARGET_CALL}")
        print("\n".join(results))
        return 1
    results.append(f"PASS agent sees {TARGET_CALL} ({call['id']})")

    code, detail = api("GET", f"/interactions/{call['id']}?includeLLMTriggers=true", agent_token)
    if code != 200:
        results.append(f"FAIL agent detail HTTP {code}")
        print("\n".join(results))
        return 1
    violations = detail.get("policyViolations") or []
    if not violations:
        results.append("FAIL no policy violations on CALL_09 to flag")
        print("\n".join(results))
        return 1
    compliance_id = violations[0]["id"]
    results.append(f"PASS found compliance row {compliance_id}")

    code, flag_resp = api(
        "POST",
        f"/policy-compliance/{compliance_id}/dispute",
        agent_token,
        {"agent_flag_note": "Prompt 60 E2E: Daniel disputes this AI compliance verdict."},
    )
    if code not in (200, 201):
        results.append(f"FAIL flag POST HTTP {code}: {flag_resp}")
        print("\n".join(results))
        return 1
    results.append(f"PASS agent flagged compliance ({flag_resp})")

    db = await supabase_counts(compliance_id)
    if not db["compliance"] or not db["compliance"]["is_flagged"]:
        results.append(f"FAIL Supabase is_flagged not true: {db}")
    else:
        results.append("PASS Supabase policy_compliance.is_flagged=true")
    if not db["notifications"]:
        results.append(f"FAIL Supabase notification missing: {db}")
    else:
        results.append(f"PASS Supabase notification count={db['notifications']}")

    mgr_token = login(MANAGER_EMAIL, MANAGER_PASSWORD)
    results.append("PASS manager login")

    code, unread = api("GET", "/notifications/unread-count", mgr_token)
    if code == 200 and unread.get("unread", 0) > 0:
        results.append(f"PASS manager unread notifications={unread['unread']}")
    else:
        results.append(f"FAIL manager unread count: HTTP {code} {unread}")

    code, queue = api("GET", "/reviews/queue", mgr_token)
    if code != 200:
        results.append(f"FAIL review queue HTTP {code}")
    else:
        comp = [x for x in queue.get("compliance", []) if x.get("review_id") == compliance_id]
        if comp:
            results.append(f"PASS review queue contains flag ({len(comp)} item)")
        else:
            results.append(f"FAIL review queue missing flag: {queue}")

    code, decision = api(
        "POST",
        f"/reviews/compliance/{compliance_id}",
        mgr_token,
        {"decision": "reject", "manager_note": "Prompt 60 E2E: manager rejects agent flag."},
    )
    if code not in (200, 201):
        results.append(f"FAIL manager reject HTTP {code}: {decision}")
    else:
        results.append(f"PASS manager rejected flag ({decision})")

    db_after = await supabase_counts(compliance_id)
    if db_after["compliance"] and not db_after["compliance"]["is_flagged"]:
        results.append("PASS Supabase is_flagged cleared after reject")
    else:
        results.append(f"FAIL flag still set after reject: {db_after}")

    print("\n".join(results))
    return 0 if all(r.startswith("PASS") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
