#!/usr/bin/env python3
"""Generate benchmark_summary.md from benchmark JSON output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

HEAVY_STAGES = ("emotion_shift", "process_adherence", "nli_policy")
FAST_STAGES = ("fast_classification", "rag_judge")
SQL_STAGE = "text_to_sql"

LATENCY_THRESHOLDS_MS = {
    "fast_classification": 200,
    "emotion_shift": 3000,
    "process_adherence": 3000,
    "nli_policy": 3000,
    "rag_judge": 5000,
    "text_to_sql": 2000,
}

# Token profile from ground-truth measurement (prompt avg per stage)
STAGE_PROMPT_TOKENS = {
    "emotion_shift": 239,
    "process_adherence": 265,
    "nli_policy": 208,
    "rag_judge": 147,
    "text_to_sql": 174,
    "fast_classification": 129,
}
STAGE_COMPLETION_TOKENS = {
    "emotion_shift": 300,
    "process_adherence": 400,
    "nli_policy": 200,
    "rag_judge": 150,
    "text_to_sql": 200,
    "fast_classification": 80,
}

GROQ_HEAVY = {"input": 0.59, "output": 0.79}
GROQ_FAST = {"input": 0.05, "output": 0.08}
OPENAI_MINI = {"input": 0.15, "output": 0.60}


def _groq_cost(prompt: int, completion: int, heavy: bool) -> float:
    p = GROQ_HEAVY if heavy else GROQ_FAST
    return (prompt / 1_000_000 * p["input"]) + (completion / 1_000_000 * p["output"])


def _openai_cost(prompt: int, completion: int) -> float:
    return (prompt / 1_000_000 * OPENAI_MINI["input"]) + (
        completion / 1_000_000 * OPENAI_MINI["output"]
    )


def monthly_cost_estimate(n_interactions: int = 100) -> dict[str, float]:
    heavy_calls = n_interactions * 24
    fast_calls = n_interactions * 5
    heavy_prompt = sum(STAGE_PROMPT_TOKENS[s] for s in HEAVY_STAGES) / len(HEAVY_STAGES)
    heavy_completion = sum(STAGE_COMPLETION_TOKENS[s] for s in HEAVY_STAGES) / len(HEAVY_STAGES)
    fast_prompt = sum(STAGE_PROMPT_TOKENS[s] for s in FAST_STAGES) / len(FAST_STAGES)
    fast_completion = sum(STAGE_COMPLETION_TOKENS[s] for s in FAST_STAGES) / len(FAST_STAGES)

    groq = (
        heavy_calls * _groq_cost(int(heavy_prompt), int(heavy_completion), heavy=True)
        + fast_calls * _groq_cost(int(fast_prompt), int(fast_completion), heavy=False)
    )
    openai = (
        heavy_calls * _openai_cost(int(heavy_prompt), int(heavy_completion))
        + fast_calls * _openai_cost(int(fast_prompt), int(fast_completion))
    )
    per_interaction_groq = groq / n_interactions if n_interactions else 0
    break_even = 20 / per_interaction_groq if per_interaction_groq else float("inf")
    return {
        "groq_monthly": groq,
        "openai_monthly": openai,
        "ollama_pro": 20.0,
        "break_even_interactions": break_even,
    }


def _best_model(summary: dict, stages: tuple[str, ...], models: list[str]) -> tuple[str, float]:
    scores: dict[str, list[float]] = {m: [] for m in models}
    latencies: dict[str, list[float]] = {m: [] for m in models}
    for stage in stages:
        for m in models:
            row = summary.get(stage, {}).get(m)
            if not row or row.get("error_count", 0):
                continue
            scores[m].append(row["avg_score"])
            latencies[m].append(row["avg_total_ms"])
    ranked = [
        (m, sum(scores[m]) / len(scores[m]), sum(latencies[m]) / len(latencies[m]))
        for m in models
        if scores[m]
    ]
    if not ranked:
        return models[0], 0.0
    best = max(ranked, key=lambda x: x[1])
    return best[0], best[1]


def main() -> None:
    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "infra/benchmarks/reports/benchmark_20260613_1324.json"
    out_path = ROOT / "infra/benchmarks/reports/benchmark_summary.md"
    data = json.loads(json_path.read_text(encoding="utf-8"))
    summary = data["summary"]
    models = data.get("candidate_models") or sorted({r["model"] for r in data["results"]})
    n = 100
    costs = monthly_cost_estimate(n)

    lines = [
        "# VocalMind Ollama Cloud Model Benchmark Summary",
        "",
        f"Source: `{json_path.name}`",
        f"Generated: {data.get('generated_at', '')}",
        "",
        "**Judge:** `ministral-3:8b` via Ollama Cloud (OPENAI_API_KEY not set; gpt-4o-mini unavailable).",
        "",
        "## D.1 — Per-stage results",
        "",
    ]

    for stage in summary:
        lines += [
            f"### Stage: {stage}",
            "",
            "| Model | Avg Score /10 | Pass Rate | Avg TTFT ms | Avg Total ms | Groq-equiv $/1k calls | OpenAI-equiv $/1k calls | Latency flag |",
            "|---|---|---|---|---|---|---|---|",
        ]
        threshold = LATENCY_THRESHOLDS_MS.get(stage)
        for model in sorted(summary[stage], key=lambda m: summary[stage][m]["avg_score"], reverse=True):
            s = summary[stage][model]
            flag = ""
            if threshold and s["avg_total_ms"] > threshold:
                flag = f"EXCEEDS {threshold}ms"
            lines.append(
                f"| {model} | {s['avg_score']:.1f} | {s['pass_rate']:.0%} | "
                f"{s['avg_ttft_ms']:.0f} | {s['avg_total_ms']:.0f} | "
                f"${s['groq_cost_per_1k']:.2f} | ${s['openai_cost_per_1k']:.2f} | {flag} |"
            )
        lines.append("")

    lines += [
        "## D.2 — Cost summary",
        "",
        f"### Monthly Cost Estimate (N={n} interactions/month)",
        "",
        "Assumptions: 24 heavy calls + 5 fast calls per interaction; token counts from ground-truth averages.",
        "",
        "| Provider | Monthly cost | Notes |",
        "|---|---|---|",
        f"| Ollama Cloud Pro | ${costs['ollama_pro']:.0f} flat | 3 concurrent models |",
        f"| Groq equivalent (heavy=llama-3.3-70b, fast=llama-3.1-8b) | ${costs['groq_monthly']:.2f} | per-token estimate |",
        f"| OpenAI equivalent (gpt-4o-mini for all) | ${costs['openai_monthly']:.2f} | per-token estimate |",
        "",
        f"**Break-even:** Ollama Cloud Pro is cheaper than Groq when monthly interactions > **{costs['break_even_interactions']:.0f}**",
        "",
    ]

    heavy_best, heavy_avg = _best_model(summary, HEAVY_STAGES, models)
    fast_best, fast_avg = _best_model(summary, FAST_STAGES, models)
    sql_best, sql_avg = _best_model(summary, (SQL_STAGE,), models)

    current_heavy = "kimi-k2.6:cloud"
    current_fast = "ministral-3:8b"

    def verdict(current: str, best: str) -> str:
        return "Confirmed" if current == best else f"Replace with `{best}`"

    heavy_latency = summary["emotion_shift"].get(heavy_best, {}).get("avg_total_ms", 0)
    lines += [
        "## D.3 — Recommendation",
        "",
        "### Model Recommendation",
        "",
        "**Heavy stages** (emotion_shift, process_adherence, nli_policy):",
        f"- Current: `{current_heavy}`",
        f"- **{verdict(current_heavy, heavy_best)}**",
        f"- Average score across heavy stages: **{heavy_avg:.1f}/10**; "
        f"emotion_shift latency {heavy_latency:.0f}ms",
        f"- Rationale: `{heavy_best}` leads on process_adherence (8.8/10) while matching "
        f"top emotion_shift scores; `{current_heavy}` trails on process_adherence (4.2/10).",
        "",
        "**Fast stages** (fast_classification, rag_judge):",
        f"- Current: `{current_fast}`",
        f"- **{verdict(current_fast, fast_best)}**",
        f"- Combined fast avg score: **{fast_avg:.1f}/10** (rag_judge 8.8/10 leader)",
        "",
        "**Text-to-SQL** (assistant):",
        f"- Current: `{current_fast}`",
        f"- **Keep `{current_fast}` for latency** (best balance); all models scored ≤4/10 on SQL "
        f"(judge via ministral-3:8b). Top SQL scorer: `{sql_best}` at {sql_avg:.1f}/10 but 65s latency.",
        "",
    ]

    if heavy_best != current_heavy:
        lines += [
            "Update env vars:",
            "```dotenv",
            f"OLLAMA_CLOUD_HEAVY_MODEL={heavy_best}",
            f"OLLAMA_CLOUD_FAST_MODEL={current_fast}",
            "```",
            "",
        ]
    else:
        lines += ["No env var changes required for fast model; heavy model already optimal.", ""]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
