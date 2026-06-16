#!/usr/bin/env python3
"""
Live production-chain validation against ground truth (fixed sample manifest, not random).

Uses per-stage models from env (.env.example winners):
  OLLAMA_EMOTION_SHIFT_MODEL=kimi-k2.5:cloud
  OLLAMA_PROCESS_ADHERENCE_MODEL=kimi-k2.6:cloud
  OLLAMA_NLI_MODEL=ministral-3:8b

Manifest: evenly spaced sample_ids from GT ∩ checkpoint (see validation_manifest_v7.json).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

_env_file = BACKEND / ".env"
if _env_file.exists():
    for line in _env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"')
        if k and k not in os.environ:
            os.environ[k] = v

os.environ.setdefault("LLM_PROVIDER", "ollama_cloud")
os.environ.setdefault("OLLAMA_EMOTION_SHIFT_MODEL", "kimi-k2.5:cloud")
os.environ.setdefault("OLLAMA_PROCESS_ADHERENCE_MODEL", "kimi-k2.6:cloud")
os.environ.setdefault("OLLAMA_NLI_MODEL", "ministral-3:8b")


def _stub_llm_trigger_package() -> None:
    """Import chains without loading service/retrieval (qdrant, sqlmodel, …)."""
    import types

    if "app.llm_trigger" not in sys.modules:
        pkg = types.ModuleType("app.llm_trigger")
        pkg.__path__ = [str(BACKEND / "app" / "llm_trigger")]
        sys.modules["app.llm_trigger"] = pkg


_stub_llm_trigger_package()

from benchmark_input import normalize_emotion_shift_input, normalize_nli_input

REPORT_DIR = ROOT / "infra" / "benchmarks" / "reports" / "overnight_20260614"
GT_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"
MANIFEST_PATH = ROOT / "infra" / "benchmarks" / "validation_manifest_v7.json"
OUT_PATH = REPORT_DIR / "LIVE_GT_VALIDATION_v8.md"

STAGES = ("emotion_shift", "process_adherence", "nli_policy")


def build_manifest(live_per_stage: int = 15) -> dict:
    gt = json.loads(GT_PATH.read_text(encoding="utf-8"))
    ck_sources = {
        "emotion_shift": "emotion_shift_v2.checkpoint.jsonl",
        "process_adherence": "process_adherence.checkpoint.jsonl",
        "nli_policy": "nli_policy.checkpoint.jsonl",
    }
    manifest: dict = {"live_per_stage": live_per_stage, "stages": {}}
    for stage, ck_name in ck_sources.items():
        sids_in_ck: set[str] = set()
        for line in (REPORT_DIR / ck_name).read_text(encoding="utf-8").splitlines():
            if line.strip():
                sids_in_ck.add(json.loads(line)["sample_id"])
        gt_sids = sorted(s["sample_id"] for s in gt[stage] if s["sample_id"] in sids_in_ck)
        step = max(1, len(gt_sids) // live_per_stage)
        live_ids = [gt_sids[i] for i in range(0, len(gt_sids), step)][:live_per_stage]
        manifest["stages"][stage] = {
            "checkpoint": ck_name,
            "population_n": len(gt_sids),
            "live_sample_ids": live_ids,
        }
    return manifest


def parse_es(text: str) -> dict[str, str]:
    text = normalize_emotion_shift_input(text)
    agent = customer = acoustic = ""
    m = re.search(r"Agent context:\s*(.+?)(?:\nCustomer text:|\Z)", text, re.S)
    if m:
        agent = m.group(1).strip()
    m = re.search(r"Customer text:\s*(.+?)(?:\nAcoustic emotion:|\Z)", text, re.S)
    if m:
        customer = m.group(1).strip()
    m = re.search(r"Acoustic emotion:\s*(.+?)(?:\n\nTranscript|\n\nTask:|\Z)", text, re.S)
    if m:
        acoustic = m.group(1).strip()
    full_m = re.search(r"Transcript \(full\):\s*(.+)", text, re.S)
    if full_m:
        block = full_m.group(1).strip()
        customer = f"{customer}\n\n{block}".strip() if customer else block
    return {
        "agent_context": agent,
        "customer_text": customer,
        "acoustic_emotion": acoustic or "neutral",
        "detected_emotion": acoustic or "neutral",
    }


def parse_pa(text: str) -> dict[str, str]:
    topic_m = re.search(r"Topic hint:\s*(.+)", text)
    topic = topic_m.group(1).strip().split("\n")[0] if topic_m else "general"
    transcript_m = re.search(
        r"Transcript:\s*(.+?)(?:\n\nRetrieved SOP:|\n\nExpected resolution|\Z)", text, re.S
    )
    transcript = transcript_m.group(1).strip() if transcript_m else text
    sop_m = re.search(r"Retrieved SOP:\s*(.+?)(?:\nExpected resolution graph|\Z)", text, re.S)
    sop = sop_m.group(1).strip() if sop_m else "No SOP context found."
    steps_m = re.search(r"Expected resolution graph steps:\s*(.+)", text, re.S)
    steps = steps_m.group(1).strip() if steps_m else "- No explicit graph available."
    return {
        "topic_hint": topic,
        "transcript_text": transcript,
        "retrieved_sop": sop,
        "expected_resolution_graph": steps,
    }


def parse_nli(text: str) -> dict[str, str]:
    pol_m = re.search(r"Ground truth policy:\s*(.+?)(?:\n\nAgent statement:|\Z)", text, re.S)
    stmt_m = re.search(r"Agent statement:\s*(.+)", text, re.S)
    return {
        "ground_truth_policy": pol_m.group(1).strip() if pol_m else "",
        "agent_statement": stmt_m.group(1).strip() if stmt_m else text,
    }


def chain_inputs(stage: str, gt_input: str) -> dict:
    if stage == "emotion_shift":
        return parse_es(gt_input)
    if stage == "process_adherence":
        return parse_pa(gt_input)
    return parse_nli(normalize_nli_input(gt_input))


async def run_stage(stage: str, sample_ids: list[str], gt_by_id: dict, model_name: str) -> list[dict]:
    from app.llm_trigger.chains import (
        build_emotion_shift_chain,
        build_nli_policy_chain,
        build_process_adherence_chain,
        get_model_for_stage,
    )
    from ground_truth_scorer import score_observation

    builders = {
        "emotion_shift": build_emotion_shift_chain,
        "process_adherence": build_process_adherence_chain,
        "nli_policy": build_nli_policy_chain,
    }
    chain = builders[stage]()
    routed = get_model_for_stage(stage)
    if routed != model_name:
        print(f"  WARN: env routes {stage} to {routed}, expected {model_name}")

    results = []
    for sid in sample_ids:
        ref = gt_by_id[sid]
        inputs = chain_inputs(stage, ref["input"])
        row: dict = {"sample_id": sid, "model": routed, "stage": stage}
        try:
            out = await chain.ainvoke(inputs)
            # Serialize for scorer: use model_dump_json as proxy for production parse success
            raw = json.dumps(out.model_dump(mode="json"))
            row["parse_ok"] = True
            row["raw_response"] = raw
        except Exception as exc:
            row["parse_ok"] = False
            row["raw_response"] = ""
            row["error"] = str(exc)[:400]
        sr = score_observation(stage, row.get("raw_response", ""), ref, row) if row["parse_ok"] else None
        row["gt_match"] = sr.match_type if sr else "unparseable"
        row["gt_exact"] = sr.match_type == "exact" if sr else False
        row["gt_f1"] = sr.f1 if sr and sr.f1 is not None else None
        results.append(row)
        status = "EXACT" if row.get("gt_exact") else row.get("gt_match", "FAIL")
        print(f"    {sid}: parse={row['parse_ok']} gt={status}", flush=True)
    return results


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-per-stage", type=int, default=15)
    parser.add_argument("--write-manifest-only", action="store_true")
    args = parser.parse_args()

    os.environ.setdefault("LLM_PROVIDER", "ollama_cloud")
    manifest = build_manifest(args.live_per_stage)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote manifest: {MANIFEST_PATH}")
    if args.write_manifest_only:
        return

    if not (os.environ.get("OLLAMA_CLOUD_API_KEY") or os.environ.get("OLLAMA_API_KEY")):
        print("ERROR: set OLLAMA_CLOUD_API_KEY or OLLAMA_API_KEY (backend/.env or env var)")
        sys.exit(1)
    if not os.environ.get("OLLAMA_CLOUD_API_KEY") and os.environ.get("OLLAMA_API_KEY"):
        os.environ["OLLAMA_CLOUD_API_KEY"] = os.environ["OLLAMA_API_KEY"]

    from app.llm_trigger.chains import (  # noqa: E402
        build_emotion_shift_chain,
        build_nli_policy_chain,
        build_process_adherence_chain,
        get_model_for_stage,
    )

    expected_models = {
        "emotion_shift": os.environ.get("OLLAMA_EMOTION_SHIFT_MODEL", "kimi-k2.5:cloud"),
        "process_adherence": os.environ.get("OLLAMA_PROCESS_ADHERENCE_MODEL", "kimi-k2.6:cloud"),
        "nli_policy": os.environ.get("OLLAMA_NLI_MODEL", "ministral-3:8b"),
    }
    gt_data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    gt_index = {s: {x["sample_id"]: x for x in gt_data[s]} for s in STAGES}

    lines = [
        "# Live production GT validation v8 (prompt + input normalization)",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Manifest:** `validation_manifest_v7.json` ({args.live_per_stage} evenly-spaced samples/stage)  ",
        "**Method:** production chains + `ground_truth_scorer` on fresh API responses.",
        "",
    ]

    for stage in STAGES:
        sids = manifest["stages"][stage]["live_sample_ids"]
        pop_n = manifest["stages"][stage]["population_n"]
        model = get_model_for_stage(stage)
        print(f"\n=== {stage} | {model} | live n={len(sids)} (population {pop_n}) ===", flush=True)
        rows = await run_stage(stage, sids, gt_index[stage], expected_models[stage])
        parse_ok = sum(1 for r in rows if r["parse_ok"])
        exact = sum(1 for r in rows if r.get("gt_exact"))
        lines.extend([
            f"## {stage}",
            "",
            f"- **Model:** `{model}`",
            f"- **Live samples:** {len(sids)} (from population n={pop_n})",
            f"- **Parse OK:** {parse_ok}/{len(sids)} ({100*parse_ok/len(sids):.0f}%)",
            f"- **GT exact:** {exact}/{len(sids)} ({100*exact/len(sids):.0f}%)",
            "",
            "| sample_id | parse | GT match |",
            "|---|---|---|",
        ])
        for r in rows:
            lines.append(f"| {r['sample_id']} | {r['parse_ok']} | {r.get('gt_match', 'n/a')} |")
        lines.append("")

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
