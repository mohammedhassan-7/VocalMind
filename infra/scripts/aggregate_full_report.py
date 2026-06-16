#!/usr/bin/env python3
"""Aggregate existing benchmark JSON into stats for FULL_REPORT.md."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "infra" / "benchmarks" / "reports"

MODELS = [
    "kimi-k2.6:cloud",
    "kimi-k2.5:cloud",
    "ministral-3:14b",
    "ministral-3:8b",
    "qwen3.5:cloud",
]
STAGES = [
    "emotion_shift",
    "process_adherence",
    "nli_policy",
    "rag_judge",
    "text_to_sql",
    "fast_classification",
]

GROQ_HEAVY = {"input": 0.59, "output": 0.79}  # llama-3.3-70b per 1M
GROQ_FAST = {"input": 0.05, "output": 0.08}  # llama-3.1-8b
OAI_MINI = {"input": 0.15, "output": 0.60}


def load(name: str) -> dict | None:
    p = REPORTS / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def es_label(s: dict) -> str:
    if s.get("_label"):
        return s["_label"]
    ref = s.get("reference_answer", "")
    if "No cross-modal" in ref:
        return "none"
    if "Sarcasm" in ref or "sarcasm" in ref.lower():
        return "sarcasm"
    if "passive" in ref.lower():
        return "passive_aggression"
    return "cross_modal"


def nli_label(s: dict) -> str:
    if s.get("_label"):
        return s["_label"]
    for lbl in ("Entailment", "Benign Deviation", "Contradiction", "Policy Hallucination"):
        if lbl in s.get("reference_answer", ""):
            return lbl
    return "unknown"


def stage_rows(data: dict | None, stage: str) -> list[dict]:
    if not data:
        return []
    return [r for r in data.get("results", []) if r.get("stage") == stage]


def avg_scores(data: dict | None, stage: str) -> tuple[dict[str, float | None], int]:
    rows = stage_rows(data, stage)
    out: dict[str, float | None] = {}
    for m in MODELS:
        mr = [r for r in rows if r["model"] == m and r.get("judge_score_0_to_10") is not None]
        out[m] = sum(r["judge_score_0_to_10"] for r in mr) / len(mr) if mr else None
    n = len({r["sample_id"] for r in rows})
    return out, n


def timing_stats(data: dict | None, stage: str) -> dict:
    rows = stage_rows(data, stage)
    by_sample: dict[str, dict[str, float]] = defaultdict(dict)
    per_model: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        per_model[r["model"]].append(r)
        by_sample[r["sample_id"]][r["model"]] = float(r.get("total_latency_ms") or 0)

    serial_ms = sum(float(r.get("total_latency_ms") or 0) for r in rows)
    parallel_ms = sum(max(d.values()) for d in by_sample.values()) if by_sample else 0
    model_stats = {}
    for m in MODELS:
        mr = per_model.get(m, [])
        if not mr:
            continue
        lats = [float(r.get("total_latency_ms") or 0) for r in mr]
        ttfts = [float(r.get("time_to_first_token_ms") or 0) for r in mr]
        model_stats[m] = {
            "avg_ttft": sum(ttfts) / len(ttfts),
            "avg_total": sum(lats) / len(lats),
            "min_total": min(lats),
            "max_total": max(lats),
            "avg_prompt": sum(r.get("prompt_tokens", 0) for r in mr) / len(mr),
            "avg_completion": sum(r.get("completion_tokens", 0) for r in mr) / len(mr),
            "groq_per_call": sum(r.get("groq_equivalent_cost_usd", 0) for r in mr) / len(mr),
            "oai_per_call": sum(r.get("openai_equivalent_cost_usd", 0) for r in mr) / len(mr),
        }
    return {
        "n_samples": len(by_sample),
        "serial_ms": serial_ms,
        "parallel_ms": parallel_ms,
        "models": model_stats,
    }


def main() -> None:
    gt = json.loads((ROOT / "infra/benchmarks/ollama_cloud_ground_truth.json").read_text())
    sub = json.loads((ROOT / "infra/benchmarks/ollama_cloud_subset_v1.json").read_text())
    subset_run = load("benchmark_subset_20260613_1648.json")
    rag_rejudge = load("benchmark_rag_rejudge_20260613.json")
    pa_rejudge = load("benchmark_PA_rejudge_20260613.json")
    orig = load("benchmark_20260613_1324.json")
    reaudit = load("benchmark_REAUDIT_20260613_1455.json")

    src_map = {
        "emotion_shift": subset_run,
        "process_adherence": subset_run,  # timing from subset; scores from pa_rejudge
        "nli_policy": subset_run,
        "rag_judge": rag_rejudge,
        "text_to_sql": subset_run,
        "fast_classification": subset_run,
    }
    score_src = {
        "emotion_shift": subset_run,
        "process_adherence": pa_rejudge,
        "nli_policy": subset_run,
        "rag_judge": rag_rejudge,
        "text_to_sql": subset_run,
        "fast_classification": subset_run,
    }
    score_n = {
        "emotion_shift": 25,
        "process_adherence": 10,
        "nli_policy": 25,
        "rag_judge": 20,
        "text_to_sql": 20,
        "fast_classification": 20,
    }

    out: dict = {"stages": {}, "totals": {}}

    total_par = 0
    total_serial = 0
    proj_total = 0

    for st in STAGES:
        data = src_map[st]
        ts = timing_stats(data, st)
        sc, _ = avg_scores(score_src[st], st)
        out["stages"][st] = {
            "pool_n": len(gt[st]),
            "subset_n": len(sub[st]),
            "score_n": score_n[st],
            "scores": sc,
            "timing": ts,
            "avg_input_chars": round(sum(len(s.get("input", "")) for s in sub[st]) / len(sub[st])),
        }
        total_par += ts["parallel_ms"]
        total_serial += ts["serial_ms"]
        avg_sample_par = ts["parallel_ms"] / max(1, ts["n_samples"])
        proj_total += avg_sample_par * len(gt[st])

    out["totals"] = {
        "subset_parallel_min": total_par / 60000,
        "subset_serial_equiv_min": total_serial / 60000,
        "projected_550_parallel_min": proj_total / 60000,
        "actual_wall_clock_min": 124.7,
    }

    # before fix
    before: dict[str, dict[str, float]] = {}
    for st in ("text_to_sql", "fast_classification", "process_adherence", "rag_judge"):
        src = reaudit if st in ("text_to_sql", "fast_classification", "process_adherence") else orig
        sc, n = avg_scores(src, st)
        before[st] = {"n": n, "scores": sc}

    out["before_fix"] = before

    # monthly cost model N=100
    # 24 heavy calls/interaction (3 chains × 8 windows), 5 fast calls/interaction
    heavy_stages = ("emotion_shift", "process_adherence", "nli_policy")
    fast_stages = ("fast_classification", "rag_judge", "text_to_sql")
    heavy_model = "kimi-k2.6:cloud"
    fast_model = "ministral-3:8b"

    def cost_per_call(stage: str, model: str) -> tuple[float, float]:
        ts = out["stages"][stage]["timing"]["models"].get(model, {})
        if not ts:
            return 0.0, 0.0
        return ts.get("groq_per_call", 0), ts.get("oai_per_call", 0)

    monthly_groq = 0.0
    monthly_oai = 0.0
    for st in heavy_stages:
        g, o = cost_per_call(st, heavy_model)
        monthly_groq += g * 24 * 100
        monthly_oai += o * 24 * 100
    for st in fast_stages:
        g, o = cost_per_call(st, fast_model)
        monthly_groq += g * 100  # ~1 call per stage type per interaction avg; use 5 total below
    # 5 fast calls per interaction: fc + rag + sql + misc ≈ use measured per-stage once each + 2 extra fc-like
    monthly_groq = 0.0
    monthly_oai = 0.0
    calls_heavy = 24
    for st in heavy_stages:
        g, o = cost_per_call(st, heavy_model)
        monthly_groq += g * calls_heavy * 100
        monthly_oai += o * calls_heavy * 100
    # fast: 1 fc + 1 rag + 1 sql + 2 rolling = 5 (approx)
    fast_call_weights = {"fast_classification": 2, "rag_judge": 1, "text_to_sql": 1}
    for st, w in fast_call_weights.items():
        g, o = cost_per_call(st, fast_model)
        monthly_groq += g * w * 100
        monthly_oai += o * w * 100

    out["monthly_n100"] = {"groq_equiv_usd": monthly_groq, "openai_equiv_usd": monthly_oai}
    out["breakeven_groq_pro"] = 20 / (monthly_groq / 100) if monthly_groq else None
    out["breakeven_groq_max"] = 100 / (monthly_groq / 100) if monthly_groq else None
    out["breakeven_oai_pro"] = 20 / (monthly_oai / 100) if monthly_oai else None
    out["breakeven_oai_max"] = 100 / (monthly_oai / 100) if monthly_oai else None

    # stage time pct (use actual 124.7 min proportional to parallel est if mismatch)
    scale = (124.7 * 60000) / total_par if total_par else 1
    out["stage_time_pct"] = {
        st: round(100 * out["stages"][st]["timing"]["parallel_ms"] * scale / (124.7 * 60000), 1)
        for st in STAGES
    }

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
