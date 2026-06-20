#!/usr/bin/env python3
import json
import urllib.parse
import urllib.request

API = "http://localhost:8000/api/v1"


def main() -> None:
    form = urllib.parse.urlencode({"username": "operations@vocalmind.dev", "password": "NexaLink2026!"}).encode()
    token = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                f"{API}/auth/login/access-token",
                data=form,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        ).read()
    )["access_token"]
    rows = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"{API}/interactions", headers={"Authorization": f"Bearer {token}"})
        ).read()
    )
    for tag in ("CALL_01", "CALL_05", "CALL_12"):
        row = next(r for r in rows if tag in (r.get("audioFilePath") or ""))
        req = urllib.request.Request(
            f"{API}/interactions/{row['id']}/audio",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            head = resp.read(12)
        print(tag, "ctype=", resp.headers.get("Content-Type"), "len=", resp.headers.get("Content-Length"), "magic=", head[:4])


if __name__ == "__main__":
    main()
