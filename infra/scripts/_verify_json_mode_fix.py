#!/usr/bin/env python3
"""Verify json_mode fix on production emotion_shift chain (offline + optional live)."""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

os.environ.setdefault("LLM_PROVIDER", "ollama_cloud")

from langchain_core.output_parsers import PydanticOutputParser  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.llm_trigger.chains import (  # noqa: E402
    _with_json_object_mode,
    build_emotion_shift_chain,
    build_llm,
    get_model_for_stage,
)
from app.llm_trigger.schemas import EmotionShiftAnalysis  # noqa: E402
from ground_truth_scorer import score_emotion_shift  # noqa: E402

CK_OLD = ROOT / "infra/benchmarks/reports/overnight_20260614/emotion_shift.checkpoint.jsonl"
CK_V2 = ROOT / "infra/benchmarks/reports/overnight_20260614/emotion_shift_v2.checkpoint.jsonl"
GT = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"


def parse_es_input(text: str) -> dict[str, str]:
    agent = customer = acoustic = ""
    m = re.search(r"Agent context:\s*(.+?)(?:\nCustomer text:|\Z)", text, re.S)
    if m:
        agent = m.group(1).strip()
    m = re.search(r"Customer text:\s*(.+?)(?:\nAcoustic emotion:|\Z)", text, re.S)
    if m:
        customer = m.group(1).strip()
    m = re.search(r"Acoustic emotion:\s*(\S+)", text)
    if m:
        acoustic = m.group(1).strip()
    if not customer and "Transcript chunk" in text:
        customer = text
        agent = "See transcript."
    return {
        "agent_context": agent,
        "customer_text": customer,
        "acoustic_emotion": acoustic or "neutral",
    }


def strict_production_parse(raw: str) -> bool:
    """Production path: PydanticOutputParser → EmotionShiftAnalysis."""
    parser = PydanticOutputParser(pydantic_object=EmotionShiftAnalysis)
    try:
        parser.parse(raw)
        return True
    except Exception:
        return False


def benchmark_parseable(raw: str, ref: dict) -> bool:
    """Overnight benchmark 'parseable' (loose GT scorer, not production schema)."""
    return score_emotion_shift(raw, ref).match_type != "unparseable"


def load_checkpoint_rows(ck_path: Path, model: str) -> dict[str, dict]:
    by_sid: dict[str, dict] = {}
    for line in ck_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("model") != model:
            continue
        by_sid[row["sample_id"]] = row
    return by_sid


def report_offline(ck_path: Path, model: str, gt: dict[str, dict], label: str) -> None:
    rows = load_checkpoint_rows(ck_path, model)
    if not rows:
        print(f"\n{label}: no rows for model={model}")
        return
    n = len(rows)
    strict_ok = bench_ok = 0
    for sid, row in rows.items():
        raw = row.get("raw_response", "")
        ref = gt.get(sid)
        if strict_production_parse(raw):
            strict_ok += 1
        if ref and benchmark_parseable(raw, ref):
            bench_ok += 1
    print(f"\n{label} | model={model} | n={n}")
    print(f"  production strict (EmotionShiftAnalysis): {strict_ok}/{n} ({100*strict_ok/n:.1f}%)")
    print(f"  benchmark GT scorer parseable:            {bench_ok}/{n} ({100*bench_ok/n:.1f}%)")


async def run_live(samples: list[tuple[str, dict[str, str]]], n: int = 5) -> tuple[int, int]:
    model = _with_json_object_mode(build_llm(fast=False, stage="emotion_shift"))
    chain = build_emotion_shift_chain(model=model)
    ok = fail = 0
    for sid, inputs in samples[:n]:
        try:
            result = await chain.ainvoke(inputs)
            if isinstance(result, EmotionShiftAnalysis) and (result.dissonance_type or "").strip().lower() != "unknown":
                ok += 1
                print(f"  {sid}: OK type={result.dissonance_type}")
            else:
                fail += 1
                print(f"  {sid}: parsed but Unknown/invalid")
        except Exception as exc:
            fail += 1
            print(f"  {sid}: failed: {exc}")
    return ok, fail


async def main() -> None:
    gt_list = json.loads(GT.read_text(encoding="utf-8"))["emotion_shift"]
    gt = {s["sample_id"]: s for s in gt_list}

    es_model = get_model_for_stage("emotion_shift")
    print(f"OLLAMA_EMOTION_SHIFT_MODEL / stage routing -> {es_model}")
    print(f"OLLAMA_CLOUD_HEAVY_MODEL (fallback) -> {settings.OLLAMA_CLOUD_HEAVY_MODEL}")

    print("\n=== OFFLINE parse rates (saved checkpoint raw_response) ===")
    print("Root cause note: old overnight checkpoint uses legacy JSON field names")
    print("(contradiction_type, etc.) -> 0% strict production parse. v2 checkpoint uses")
    print("production EmotionShiftAnalysis schema -> ~100% strict parse (v2 prompt run).")

    report_offline(CK_OLD, "kimi-k2.6:cloud", gt, "OLD checkpoint (pre-v2 prompt)")
    report_offline(CK_OLD, "kimi-k2.5:cloud", gt, "OLD checkpoint (pre-v2 prompt)")
    if CK_V2.exists():
        report_offline(CK_V2, "kimi-k2.5:cloud", gt, "V2 checkpoint (post-prompt-fix)")

    # Legacy bug demo: first-20 sample_ids from ANY model, looked up in kimi-k2.6 only
    seen: set[str] = set()
    first20: list[str] = []
    for line in CK_OLD.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        sid = row.get("sample_id", "")
        if sid in seen or sid not in gt:
            continue
        seen.add(sid)
        first20.append(sid)
        if len(first20) >= 20:
            break
    k26 = load_checkpoint_rows(CK_OLD, "kimi-k2.6:cloud")
    v_ok = sum(1 for sid in first20 if sid in k26 and strict_production_parse(k26[sid].get("raw_response", "")))
    print(f"\nLegacy verify-script bug (first-20 sids × kimi-k2.6 only): strict {v_ok}/20")
    print("(Misleading 0/20 — not representative; use full-model counts above.)")

    if not settings.OLLAMA_CLOUD_API_KEY:
        print("\nSKIP live chain (OLLAMA_CLOUD_API_KEY not set).")
        return

    samples = [(s["sample_id"], parse_es_input(s["input"])) for s in gt_list[:5]]
    es_model = get_model_for_stage("emotion_shift")
    print(f"\n=== LIVE ES (n=5) json_mode model={es_model} ===")
    ok, fail = await run_live(samples, n=5)
    print(f"Live parse OK: {ok}/5")
    print("For full 3-stage live smoke: infra/scripts/verify_live_chains.py --n 5")


if __name__ == "__main__":
    asyncio.run(main())
