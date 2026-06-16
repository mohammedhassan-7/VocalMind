#!/usr/bin/env python3
"""Prompt 22: Diagnose ES verify-script parseable rate vs overnight baseline."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

from langchain_core.output_parsers import PydanticOutputParser  # noqa: E402

from app.llm_trigger.schemas import EmotionShiftAnalysis  # noqa: E402
from ground_truth_scorer import score_emotion_shift  # noqa: E402

CK = ROOT / "infra/benchmarks/reports/overnight_20260614/emotion_shift.checkpoint.jsonl"
GT = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"


def strict_production_parse(raw: str) -> bool:
    """Same check as _verify_json_mode_fix.count_parser_success."""
    parser = PydanticOutputParser(pydantic_object=EmotionShiftAnalysis)
    try:
        parser.parse(raw)
        return True
    except Exception:
        return False


def benchmark_parseable(raw: str, ref: dict) -> bool:
    """Benchmark overnight 'parseable' = GT scorer does not return unparseable."""
    sr = score_emotion_shift(raw, ref)
    return sr.match_type != "unparseable"


def main() -> None:
    lines = [json.loads(l) for l in CK.read_text(encoding="utf-8").splitlines() if l.strip()]
    gt = {s["sample_id"]: s for s in json.loads(GT.read_text(encoding="utf-8"))["emotion_shift"]}

    print(f"Total checkpoint lines: {len(lines)}")
    models = sorted({e.get("model") for e in lines})
    print(f"Models: {models}\n")

    # Replicate verify-script sample selection bug
    seen: set[str] = set()
    first20_sids: list[str] = []
    for row in lines:
        sid = row.get("sample_id", "")
        if sid in seen or sid not in gt:
            continue
        seen.add(sid)
        first20_sids.append(sid)
        if len(first20_sids) >= 20:
            break
    print(f"Verify script 'first 20 unique sample_ids' (any model): {first20_sids[:5]}... ({len(first20_sids)} total)")

    for model in ("kimi-k2.6:cloud", "kimi-k2.5:cloud"):
        model_rows = [e for e in lines if e.get("model") == model]
        # last-write-wins per sample_id
        by_sid: dict[str, dict] = {}
        for e in model_rows:
            by_sid[e["sample_id"]] = e
        unique = list(by_sid.values())
        strict_ok = sum(1 for e in unique if strict_production_parse(e.get("raw_response", "")))
        bench_ok = sum(
            1
            for e in unique
            if e["sample_id"] in gt and benchmark_parseable(e.get("raw_response", ""), gt[e["sample_id"]])
        )
        print(f"\n=== {model} (unique samples={len(unique)}) ===")
        print(f"  strict EmotionShiftAnalysis Pydantic parse: {strict_ok}/{len(unique)} ({100*strict_ok/len(unique):.1f}%)")
        print(f"  benchmark GT scorer parseable:            {bench_ok}/{len(unique)} ({100*bench_ok/len(unique):.1f}%)")

        # Verify-script subset: first 20 sids looked up in THIS model's responses
        v_ok = v_total = 0
        for sid in first20_sids:
            raw = by_sid.get(sid, {}).get("raw_response", "")
            if not raw:
                continue
            v_total += 1
            if strict_production_parse(raw):
                v_ok += 1
        print(f"  verify-script 20 sids with {model} raw: strict parse {v_ok}/{v_total}")

    # Root cause demo: es_001 kimi-k2.6 parses as JSON but fails strict schema
    e = next(e for e in lines if e.get("model") == "kimi-k2.6:cloud" and e.get("sample_id") == "es_001")
    raw = e["raw_response"]
    print("\n=== es_001 kimi-k2.6:cloud sample ===")
    print(f"  benchmark parseable: {benchmark_parseable(raw, gt['es_001'])}")
    print(f"  strict Pydantic parse: {strict_production_parse(raw)}")
    parser = PydanticOutputParser(pydantic_object=EmotionShiftAnalysis)
    try:
        parser.parse(raw)
    except Exception as exc:
        print(f"  strict parse error: {exc}")
    print(f"  raw keys in JSON: {list(json.loads(raw.strip().strip('`').split('```')[0] if False else raw) if raw.strip().startswith('{') else [])}")
    import re
    from ground_truth_scorer import parse_json_object
    data = parse_json_object(raw)
    if data:
        print(f"  parsed JSON top-level keys: {list(data.keys())}")


if __name__ == "__main__":
    main()
