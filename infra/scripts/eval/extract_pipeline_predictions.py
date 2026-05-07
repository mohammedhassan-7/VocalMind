"""
Extract pipeline predictions from the VocalMind backend API for the 5 NexaLink calls.

Prerequisites:
  1. Upload and process all 5 NexaLink WAV files via the VocalMind UI or API.
  2. Obtain a JWT access token (copy from browser DevTools → Application → localStorage).
  3. Build the call → interaction mapping (see --help).

Usage:
    # Provide mapping as JSON file {"CALL_01_refund_outage": "<uuid>", ...}
    python infra/scripts/eval/extract_pipeline_predictions.py \\
        --token <JWT>  --map infra/benchmarks/fixtures/nexalink_id_map.json

    # Or inline as key=value pairs
    python infra/scripts/eval/extract_pipeline_predictions.py \\
        --token <JWT>  \\
        --pair CALL_01_refund_outage=<uuid1> \\
        --pair CALL_02_billing_dispute_escalation=<uuid2>

Writes: infra/benchmarks/fixtures/baseline_predictions.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = ROOT / "infra" / "benchmarks" / "fixtures"
OUTPUT_PATH = FIXTURES_DIR / "baseline_predictions.json"

DEFAULT_BASE_URL = "http://localhost:8000"

# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only — no external deps needed)
# ---------------------------------------------------------------------------

def _get(url: str, token: str, retries: int = 3) -> dict[str, Any]:
    for attempt in range(retries):
        try:
            req = Request(url, headers={"Authorization": f"Bearer {token}"})
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} {url}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"Network error {url}: {exc.reason}") from exc
    raise RuntimeError(f"Max retries exceeded for {url}")


# ---------------------------------------------------------------------------
# Prediction extractors — one per eval component
# ---------------------------------------------------------------------------

def _transcript_prediction(interaction_id: str, call_id: str, detail: dict) -> dict:
    utterances = detail.get("utterances", [])
    turns = [
        {"speaker": u.get("speaker", "customer"), "text": u.get("text", "")}
        for u in utterances
    ]
    full_text = " ".join(u.get("text", "") for u in utterances)
    return {"id": call_id, "text": full_text, "turns": turns}


def _emotion_prediction(interaction_id: str, call_id: str, detail: dict) -> dict:
    utterances = detail.get("utterances", [])
    # Use fusedEmotion when available; fall back to acoustic emotion
    turn_emotions = [
        (u.get("fusedEmotion") or u.get("emotion") or "neutral")
        for u in utterances
    ]
    return {"id": call_id, "turn_emotions": turn_emotions}


def _policy_prediction(interaction_id: str, call_id: str, detail: dict) -> dict:
    violations_raw = detail.get("policyViolations", []) or []
    violations = [v.get("policyName", "") for v in violations_raw if v.get("policyName")]
    violated_policy_ids = [v.get("policyTitle", "") for v in violations_raw if v.get("policyTitle")]
    return {
        "id": call_id,
        "violations": violations,
        "violated_policy_ids": violated_policy_ids,
    }


def _rag_prediction(interaction_id: str, call_id: str, detail: dict) -> dict:
    rag = detail.get("ragCompliance") or {}
    process_adherence = rag.get("processAdherence") or {}
    explainability = rag.get("explainability") or {}
    # is_correct: processAdherence.isResolved tells us if the agent resolved the issue
    is_correct = bool(process_adherence.get("isResolved", False))
    # evidence_ids: from claim provenance policyReference references
    evidence_ids: list[str] = []
    for claim in (explainability.get("claimProvenance") or []):
        ref = (claim.get("retrievedPolicy") or {}).get("reference", "")
        if ref and ref not in evidence_ids:
            evidence_ids.append(ref)
    for attr in (explainability.get("triggerAttributions") or []):
        ref = (attr.get("policyReference") or {}).get("reference", "")
        if ref and ref not in evidence_ids:
            evidence_ids.append(ref)
    return {"id": call_id, "is_correct": is_correct, "evidence_ids": evidence_ids}


def _resolution_prediction(interaction_id: str, call_id: str, detail: dict) -> dict:
    rag = detail.get("ragCompliance") or {}
    process_adherence = rag.get("processAdherence") or {}
    # Fallback to interaction-level resolved flag
    interaction_resolved = detail.get("interaction", {}).get("resolved", False)
    is_resolved = bool(process_adherence.get("isResolved", interaction_resolved))
    missing_steps = list(process_adherence.get("missingSopSteps") or [])
    return {"id": call_id, "is_resolved": is_resolved, "missing_steps": missing_steps}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fetch_predictions(
    call_map: dict[str, str],
    token: str,
    base_url: str,
) -> dict[str, Any]:
    transcript_samples: list[dict] = []
    emotion_samples: list[dict] = []
    policy_samples: list[dict] = []
    rag_samples: list[dict] = []
    resolution_samples: list[dict] = []

    for call_id, interaction_id in call_map.items():
        print(f"  fetching {call_id} → interaction {interaction_id}")
        url = (
            f"{base_url}/api/interactions/{interaction_id}"
            "?include_llm_triggers=true"
        )
        try:
            detail = _get(url, token)
        except RuntimeError as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            # Insert empty predictions so the eval can still run for other calls
            detail = {}

        transcript_samples.append(_transcript_prediction(interaction_id, call_id, detail))
        emotion_samples.append(_emotion_prediction(interaction_id, call_id, detail))
        policy_samples.append(_policy_prediction(interaction_id, call_id, detail))
        rag_samples.append(_rag_prediction(interaction_id, call_id, detail))
        resolution_samples.append(_resolution_prediction(interaction_id, call_id, detail))

    return {
        "transcript": {"samples": transcript_samples},
        "emotion": {"samples": emotion_samples},
        "policy": {"samples": policy_samples},
        "rag": {"samples": rag_samples},
        "resolution": {"samples": resolution_samples},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract VocalMind pipeline predictions for the 5 NexaLink evaluation calls.")
    parser.add_argument("--token", required=True, help="Bearer JWT token (copy from browser DevTools).")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"API base URL (default: {DEFAULT_BASE_URL}).")
    parser.add_argument("--map", type=Path, default=None, help='JSON file {"call_id": "interaction_uuid", ...}.')
    parser.add_argument("--pair", action="append", default=[], metavar="CALL_ID=UUID",
                        help="Inline call_id=interaction_uuid pairs (repeatable).")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    call_map: dict[str, str] = {}
    if args.map:
        call_map.update(json.loads(args.map.read_text(encoding="utf-8")))
    for pair in args.pair:
        if "=" not in pair:
            parser.error(f"--pair must be CALL_ID=UUID, got: {pair!r}")
        k, v = pair.split("=", 1)
        call_map[k.strip()] = v.strip()

    if not call_map:
        parser.error("Provide at least one call→interaction mapping via --map or --pair.")

    base_url = args.base_url.rstrip("/")
    print(f"Fetching predictions from {base_url} for {len(call_map)} calls…")
    predictions = fetch_predictions(call_map, args.token, base_url)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(predictions, indent=2), encoding="utf-8")
    print(f"Wrote {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
