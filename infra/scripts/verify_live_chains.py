#!/usr/bin/env python3
"""Prompt 24: Live json_mode smoke test (n=5) for ES / PA / NLI production chains."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ── env must be set before backend imports ──
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

GT_PATH = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=5, help="calls per stage")
    p.add_argument("--offline-only", action="store_true")
    return p.parse_args()


def _load_gt() -> dict[str, list[dict]]:
    return json.loads(GT_PATH.read_text(encoding="utf-8"))


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


def parse_pa_input(text: str) -> dict[str, str]:
    topic_m = re.search(r"Topic hint:\s*(.+)", text)
    topic = topic_m.group(1).strip() if topic_m else "general"
    transcript_m = re.search(
        r"Transcript:\s*(.+?)(?:\n\nRetrieved SOP:|\n\nExpected resolution|\Z)",
        text,
        re.S,
    )
    transcript = transcript_m.group(1).strip() if transcript_m else text
    sop_m = re.search(r"Retrieved SOP:\s*(.+?)(?:\nExpected resolution graph|\Z)", text, re.S)
    sop = sop_m.group(1).strip() if sop_m else "No SOP context found."
    steps_m = re.search(r"Expected resolution graph steps:\s*(.+)", text, re.S)
    steps_block = steps_m.group(1).strip() if steps_m else "- No explicit graph available."
    return {
        "topic_hint": topic.split("\n")[0].strip(),
        "transcript_text": transcript,
        "retrieved_sop": sop,
        "expected_resolution_graph": steps_block,
    }


def parse_nli_input(text: str) -> dict[str, str]:
    pol_m = re.search(r"Ground truth policy:\s*(.+?)(?:\n\nAgent statement:|\Z)", text, re.S)
    stmt_m = re.search(r"Agent statement:\s*(.+)", text, re.S)
    return {
        "ground_truth_policy": (pol_m.group(1).strip() if pol_m else ""),
        "agent_statement": (stmt_m.group(1).strip() if stmt_m else text),
    }


def bound_response_format(model: Any) -> object | None:
    """Read response_format from a LangChain bound ChatOpenAI."""
    for attr in ("kwargs", "model_kwargs"):
        kw = getattr(model, attr, None)
        if isinstance(kw, dict) and "response_format" in kw:
            return kw["response_format"]
    first = getattr(model, "first", None)
    if first is not None:
        return bound_response_format(first)
    return None


async def smoke_stage(
    stage: str,
    chain,
    samples: list[tuple[str, dict]],
    n: int,
    ok_type: type,
    *,
    get_model_for_stage,
    _resolve_chain_model,
    _with_json_object_mode,
) -> dict[str, Any]:
    model_name = get_model_for_stage(stage)
    llm = _resolve_chain_model(stage, None)
    rf = bound_response_format(_with_json_object_mode(llm))
    print(f"\n=== {stage} | model={model_name} | response_format={rf} ===")

    ok = fail = 0
    errors: list[str] = []
    for sid, inputs in samples[:n]:
        try:
            result = await chain.ainvoke(inputs)
            if isinstance(result, ok_type):
                ok += 1
                summary = getattr(result, "dissonance_type", None) or getattr(result, "nli_category", None)
                if summary is None and hasattr(result, "missing_sop_steps"):
                    summary = f"missing={len(result.missing_sop_steps)}"
                print(f"  {sid}: OK {summary}")
            else:
                fail += 1
                errors.append(f"{sid}: wrong type {type(result)}")
                print(f"  {sid}: FAIL wrong type")
        except Exception as exc:
            fail += 1
            msg = str(exc).replace("\n", " ")[:300]
            errors.append(f"{sid}: {msg}")
            print(f"  {sid}: FAIL {msg}")
    rate = ok / n if n else 0.0
    print(f"  -> live parse OK: {ok}/{n} ({100*rate:.0f}%)")
    return {"stage": stage, "model": model_name, "ok": ok, "n": n, "response_format": rf, "errors": errors}


async def main() -> None:
    args = _parse_args()
    if not os.environ.get("OLLAMA_CLOUD_API_KEY"):
        print("ERROR: set OLLAMA_CLOUD_API_KEY")
        sys.exit(1)

    from app.core.config import settings  # noqa: E402
    from app.llm_trigger.chains import (  # noqa: E402
        _resolve_chain_model,
        _with_json_object_mode,
        build_emotion_shift_chain,
        build_nli_policy_chain,
        build_process_adherence_chain,
        get_model_for_stage,
    )
    from app.llm_trigger.schemas import (  # noqa: E402
        EmotionShiftAnalysis,
        NLIEvaluation,
        ProcessAdherenceReport,
    )

    print("LLM_PROVIDER:", settings.LLM_PROVIDER)
    print("Per-stage models:")
    for st in ("emotion_shift", "process_adherence", "nli_policy"):
        print(f"  {st}: {get_model_for_stage(st)}")

    gt = _load_gt()
    n = args.n

    es_samples = [
        (s["sample_id"], parse_es_input(s["input"]))
        for s in gt["emotion_shift"][:n]
    ]
    pa_samples = [
        (s["sample_id"], parse_pa_input(s["input"]))
        for s in gt["process_adherence"][:n]
    ]
    nli_samples = [
        (s["sample_id"], parse_nli_input(s["input"]))
        for s in gt["nli_policy"][:n]
    ]

    results = []
    results.append(
        await smoke_stage(
            "emotion_shift",
            build_emotion_shift_chain(),
            es_samples,
            n,
            EmotionShiftAnalysis,
            get_model_for_stage=get_model_for_stage,
            _resolve_chain_model=_resolve_chain_model,
            _with_json_object_mode=_with_json_object_mode,
        )
    )
    results.append(
        await smoke_stage(
            "process_adherence",
            build_process_adherence_chain(),
            pa_samples,
            n,
            ProcessAdherenceReport,
            get_model_for_stage=get_model_for_stage,
            _resolve_chain_model=_resolve_chain_model,
            _with_json_object_mode=_with_json_object_mode,
        )
    )
    results.append(
        await smoke_stage(
            "nli_policy",
            build_nli_policy_chain(),
            nli_samples,
            n,
            NLIEvaluation,
            get_model_for_stage=get_model_for_stage,
            _resolve_chain_model=_resolve_chain_model,
            _with_json_object_mode=_with_json_object_mode,
        )
    )

    print("\n=== SUMMARY ===")
    for r in results:
        print(
            f"{r['stage']:<20} {r['model']:<22} {r['ok']}/{r['n']} OK  "
            f"response_format={r['response_format']}"
        )

    if any(r["ok"] < r["n"] for r in results):
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
