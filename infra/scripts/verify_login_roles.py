#!/usr/bin/env python3
"""Verify auth returns role via /users/me for login routing."""

import http.cookiejar
import json
import urllib.parse
import urllib.request

API = "http://localhost:8000/api/v1"
ACCOUNTS = [
    ("operations@vocalmind.dev", "NexaLink2026!", "manager"),
    ("agent.daniel@nexalink.com", "NexaLink2026!", "agent"),
]


def check(email: str, password: str, expected: str) -> bool:
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    form = urllib.parse.urlencode({"username": email, "password": password}).encode()
    req = urllib.request.Request(
        f"{API}/auth/login/access-token",
        data=form,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    opener.open(req, timeout=30)
    me = json.loads(opener.open(urllib.request.Request(f"{API}/users/me"), timeout=30).read())
    role = me.get("role")
    ok = role == expected
    print(f"{'PASS' if ok else 'FAIL'} {email}: role={role} (expected {expected})")
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if all(check(e, p, r) for e, p, r in ACCOUNTS) else 1)
