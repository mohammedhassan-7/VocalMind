"""
Generate oracle (perfect) predictions by mirroring the gold files.

Useful for:
  - Verifying eval scripts are wired correctly (should yield 100% scores)
  - Smoke-testing the eval pipeline before real backend predictions exist

Writes: infra/benchmarks/fixtures/oracle_predictions.json
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXPECTED_DIR = ROOT / "infra" / "benchmarks" / "expected"
FIXTURES_DIR = ROOT / "infra" / "benchmarks" / "fixtures"


def _load(name: str) -> dict:
    return json.loads((EXPECTED_DIR / name).read_text(encoding="utf-8"))


def main() -> None:
    transcript_gold = _load("transcript_gold.json")
    emotion_gold = _load("emotion_gold.json")
    policy_gold = _load("policy_gold.json")
    rag_gold = _load("rag_gold.json")
    resolution_gold = _load("resolution_gold.json")

    oracle = {
        "transcript": transcript_gold,
        "emotion": emotion_gold,
        "policy": policy_gold,
        "rag": rag_gold,
        "resolution": resolution_gold,
    }

    out = FIXTURES_DIR / "oracle_predictions.json"
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(oracle, indent=2), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
