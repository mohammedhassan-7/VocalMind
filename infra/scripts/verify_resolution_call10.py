#!/usr/bin/env python3
"""Verify manager accept/reject on CALL_10 without clearing CALL_09 pending flags."""

import asyncio
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / "backend" / ".env")
API = "http://localhost:8000/api/v1"


def login(email: str, password: str) -> str:
    form = urllib.parse.urlencode({"username": email, "password": password}).encode()
    req = urllib.request.Request(
        f"{API}/auth/login/access-token",
        data=form,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read())["access_token"]


def api(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


async def is_flagged(table: str, row_id: str) -> bool | None:
    url = os.environ["SUPABASE_DB_URL"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        return await conn.fetchval(f"SELECT is_flagged FROM {table} WHERE id = $1", row_id)
    finally:
        await conn.close()


async def main() -> None:
    agent = login("agent.daniel@nexalink.com", "NexaLink2026!")
    _, interactions = api("GET", "/interactions", agent)
    call = next(i for i in interactions if "CALL_10" in (i.get("audioFilePath") or ""))
    _, detail = api("GET", f"/interactions/{call['id']}?includeLLMTriggers=true", agent)
    cid = detail["policyViolations"][0]["id"]

    code, _ = api(
        "POST",
        f"/policy-compliance/{cid}/dispute",
        agent,
        {"agent_flag_note": "Resolution test on CALL_10 — safe to accept/reject."},
    )
    print("flag CALL_10:", code)

    mgr = login("operations@vocalmind.dev", "NexaLink2026!")
    code, decision = api(
        "POST",
        f"/reviews/compliance/{cid}",
        mgr,
        {"decision": "reject", "manager_note": "Resolution test reject."},
    )
    print("reject:", code, decision)

    flagged = await is_flagged("policy_compliance", cid)
    print("is_flagged after reject:", flagged)
    assert flagged is False, "expected is_flagged=false after reject"
    print("PASS resolution chain on CALL_10")


if __name__ == "__main__":
    asyncio.run(main())
