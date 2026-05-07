"""
Generate gold-standard evaluation fixtures from the 5 NexaLink ground-truth call JSONs.

Reads:  storage/audio/nexalink/evaluation/CALL_0{1-5}_*.json
Writes: infra/benchmarks/expected/{transcript,emotion,policy,rag,resolution}_gold.json

Run from any directory:
    python infra/scripts/eval/generate_nexalink_gold.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[3]
EVAL_DIR = ROOT / "storage" / "audio" / "nexalink" / "evaluation"
EXPECTED_DIR = ROOT / "infra" / "benchmarks" / "expected"

CALL_FILES = sorted(EVAL_DIR.glob("CALL_0*.json"))

# ---------------------------------------------------------------------------
# Emotion label normalization
# Raw call JSONs use a rich vocabulary; map to the 6-label tier used by the
# VocalMind acoustic/text emotion models so gold and predictions align.
# ---------------------------------------------------------------------------
_EMOTION_MAP: dict[str, str] = {
    "neutral": "neutral",
    "professional": "neutral",
    "empathetic": "neutral",
    "apologetic": "neutral",
    "calm": "neutral",
    "assertive": "neutral",
    "cooperative": "happy",
    "happy": "happy",
    "grateful": "happy",
    "grateful_relieved": "happy",
    "relieved": "happy",
    "satisfied": "happy",
    "enthusiastic": "happy",
    "frustrated": "frustrated",
    "mild_frustrated": "frustrated",
    "confused": "frustrated",
    "worried": "frustrated",
    "concerned": "frustrated",
    "impatient": "frustrated",
    "anxious": "frustrated",
    "curt": "frustrated",
    "angry": "angry",
    "hostile": "angry",
    "abusive": "angry",
    "resigned": "sad",
    "sad": "sad",
    "tired": "sad",
    "afraid": "sad",
    "fearful": "sad",
}


def _map_emotion(raw: str) -> str:
    return _EMOTION_MAP.get(raw.lower().strip(), "neutral")


def _map_speaker(raw: str) -> str:
    return "agent" if raw.upper() == "AGENT" else "customer"


def _parse_id_list(raw: str) -> list[str]:
    """'[CS-RULE-001, FIN-RULE-001]' → ['CS-RULE-001', 'FIN-RULE-001']"""
    stripped = raw.strip().lstrip("[").rstrip("]")
    return [tok.strip() for tok in stripped.split(",") if tok.strip()]


def _is_tier1_resolved(expected_outcome: str) -> bool:
    outcome = expected_outcome.lower()
    # "No escalation" is an explicit Tier 1 resolution marker — check before
    # the general "escalat" substring so we don't false-positive on it.
    escalated = (
        "tier 2" in outcome
        or "tier 3" in outcome
        or ("escalat" in outcome and "no escalat" not in outcome)
    )
    return not escalated


# ---------------------------------------------------------------------------
# Per-call extraction helpers
# ---------------------------------------------------------------------------

def _extract_transcript(call: dict[str, Any]) -> dict[str, Any]:
    turns_raw = call.get("turns", [])
    turns: list[dict[str, str]] = []
    texts: list[str] = []
    for t in turns_raw:
        text = t.get("text", "").strip()
        speaker = _map_speaker(t.get("speaker", "CUSTOMER"))
        turns.append({"speaker": speaker, "text": text})
        texts.append(text)
    return {
        "id": call["call_id"],
        "text": " ".join(texts),
        "turns": turns,
    }


def _extract_emotion(call: dict[str, Any]) -> dict[str, Any]:
    emotions = [_map_emotion(t.get("emotion", "neutral")) for t in call.get("turns", [])]
    return {"id": call["call_id"], "turn_emotions": emotions}


def _extract_policy(call: dict[str, Any]) -> dict[str, Any]:
    # All 5 NexaLink calls demonstrate CORRECT procedure; no violations.
    return {
        "id": call["call_id"],
        "violations": [],
        "violated_policy_ids": [],
    }


def _extract_rag(call: dict[str, Any]) -> dict[str, Any]:
    evidence_ids: list[str] = []
    for ref_field in ("policy_refs", "kb_refs"):
        raw = call.get(ref_field, "")
        if raw:
            evidence_ids.extend(_parse_id_list(raw))
    # Add the primary SOP as an evidence ID
    sop_primary = call.get("sop_primary", "")
    if sop_primary:
        sop_match = re.match(r"(SOP-\d+)", sop_primary)
        if sop_match:
            sop_id = sop_match.group(1)
            if sop_id not in evidence_ids:
                evidence_ids.insert(0, sop_id)
    return {
        "id": call["call_id"],
        "is_correct": True,  # agents correctly follow relevant SOPs/KBs
        "evidence_ids": evidence_ids,
    }


def _extract_resolution(call: dict[str, Any]) -> dict[str, Any]:
    expected_outcome = call.get("expected_outcome", "")
    is_resolved = _is_tier1_resolved(expected_outcome)
    return {
        "id": call["call_id"],
        "is_resolved": is_resolved,
        "missing_steps": [],  # all 5 scripts follow the SOP correctly
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate() -> None:
    transcript_samples: list[dict[str, Any]] = []
    emotion_samples: list[dict[str, Any]] = []
    policy_samples: list[dict[str, Any]] = []
    rag_samples: list[dict[str, Any]] = []
    resolution_samples: list[dict[str, Any]] = []

    for path in CALL_FILES:
        call = json.loads(path.read_text(encoding="utf-8"))
        transcript_samples.append(_extract_transcript(call))
        emotion_samples.append(_extract_emotion(call))
        policy_samples.append(_extract_policy(call))
        rag_samples.append(_extract_rag(call))
        resolution_samples.append(_extract_resolution(call))
        print(f"  processed {call['call_id']} ({len(call.get('turns', []))} turns)")

    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)

    def _save(name: str, samples: list[dict[str, Any]]) -> None:
        out = {"samples": samples}
        path = EXPECTED_DIR / name
        path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)} ({len(samples)} samples)")

    _save("transcript_gold.json", transcript_samples)
    _save("emotion_gold.json", emotion_samples)
    _save("policy_gold.json", policy_samples)
    _save("rag_gold.json", rag_samples)
    _save("resolution_gold.json", resolution_samples)
    print("Done.")


if __name__ == "__main__":
    generate()
