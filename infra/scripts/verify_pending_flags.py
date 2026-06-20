#!/usr/bin/env python3
"""Verify pending flags + notifications in Supabase and via API."""

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


async def main() -> None:
    url = os.environ["SUPABASE_DB_URL"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        priya = await conn.fetchrow(
            "SELECT email, organization_id, role FROM users WHERE email = $1",
            "agent.priya@nexalink.com",
        )
        org = None
        if priya:
            org = await conn.fetchrow(
                "SELECT id, slug FROM organizations WHERE id = $1",
                priya["organization_id"],
            )
        flags = await conn.fetch(
            "SELECT id, is_flagged, agent_flag_note FROM policy_compliance WHERE is_flagged = true"
        )
        emo = await conn.fetch(
            "SELECT id, is_flagged, agent_flag_note FROM emotion_events WHERE is_flagged = true"
        )
        notifs = await conn.fetch(
            """
            SELECT id, type, read_at, payload
            FROM notifications
            WHERE type = 'agent_flag_pending'
            ORDER BY created_at DESC
            LIMIT 10
            """
        )
    finally:
        await conn.close()

    print("PRIYA:", dict(priya) if priya else None)
    print("ORG:", dict(org) if org else None)
    print("FLAGGED COMPLIANCE:", [dict(r) for r in flags])
    print("FLAGGED EMOTION:", [dict(r) for r in emo])
    print("NOTIFICATIONS:", [dict(r) for r in notifs])

    mgr = login("operations@vocalmind.dev", "NexaLink2026!")
    req = urllib.request.Request(
        f"{API}/notifications/unread-count",
        headers={"Authorization": f"Bearer {mgr}"},
    )
    print("UNREAD COUNT:", json.loads(urllib.request.urlopen(req).read()))
    req = urllib.request.Request(
        f"{API}/reviews/queue",
        headers={"Authorization": f"Bearer {mgr}"},
    )
    q = json.loads(urllib.request.urlopen(req).read())
    print(
        "QUEUE:",
        len(q.get("emotion", [])),
        "emotion,",
        len(q.get("compliance", [])),
        "compliance",
    )


if __name__ == "__main__":
    asyncio.run(main())
