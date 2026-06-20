#!/usr/bin/env python3
"""Leave pending agent flags on CALL_09 for manual browser verification."""

import json
import urllib.parse
import urllib.request

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


def main() -> None:
    agent = login("agent.daniel@nexalink.com", "NexaLink2026!")
    rows = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"{API}/interactions", headers={"Authorization": f"Bearer {agent}"})
        ).read()
    )
    call = next(r for r in rows if "CALL_09" in (r.get("audioFilePath") or ""))
    iid = call["id"]
    detail = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                f"{API}/interactions/{iid}?includeLLMTriggers=true",
                headers={"Authorization": f"Bearer {agent}"},
            )
        ).read()
    )

    cid = detail["policyViolations"][0]["id"]
    body = json.dumps(
        {"agent_flag_note": "PENDING REVIEW — Daniel flagged CALL_09 compliance for manager walkthrough."}
    ).encode()
    req = urllib.request.Request(
        f"{API}/policy-compliance/{cid}/dispute",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {agent}", "Content-Type": "application/json"},
    )
    print("compliance flag:", json.loads(urllib.request.urlopen(req).read()))

    if detail.get("emotionEvents"):
        eid = detail["emotionEvents"][0]["id"]
        body = json.dumps(
            {"agent_flag_note": "PENDING REVIEW — Daniel flagged CALL_09 emotion shift."}
        ).encode()
        req = urllib.request.Request(
            f"{API}/interactions/emotion-events/{eid}/dispute",
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {agent}", "Content-Type": "application/json"},
        )
        print("emotion flag:", json.loads(urllib.request.urlopen(req).read()))

    mgr = login("operations@vocalmind.dev", "NexaLink2026!")
    queue = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"{API}/reviews/queue", headers={"Authorization": f"Bearer {mgr}"})
        ).read()
    )
    print("queue:", json.dumps(queue, indent=2))


if __name__ == "__main__":
    main()
