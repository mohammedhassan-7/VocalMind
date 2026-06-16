#!/usr/bin/env python3
"""Generate benchmark_summary_v2.md from re-audit + original emotion_shift/rag_judge."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

HEAVY_STAGES = ("emotion_shift", "process_adherence", "nli_policy")
FAST_STAGES = ("fast_classification", "rag_judge")
ORIGINAL_ONLY = ("emotion_shift", "rag_judge")
REAUDIT_STAGES = ("text_to_sql", "fast_classification", "nli_policy", "process_adherence")

LATENCY_THRESHOLDS_MS = {
    "fast_classification": 200,
    "emotion_shift": 3000,
    "process_adherence": 3000,
    "nli_policy": 3000,
    "rag_judge": 5000,
    "text_to_sql": 2000,
}


def _heavy_avg(summary: dict, model: str) -> float:
    scores = []
    for stage in HEAVY_STAGES:
        row = summary.get(stage, {}).get(model)
        if row:
            scores.append(row["avg_score"])
    return sum(scores) / len(scores) if scores else 0.0


def _fast_avg(summary: dict, model: str) -> float:
    scores = []
    for stage in FAST_STAGES:
        row = summary.get(stage, {}).get(model)
        if row:
            scores.append(row["avg_score"])
    return sum(scores) / len(scores) if scores else 0.0


def main() -> None:
    original_path = ROOT / "infra/benchmarks/reports/benchmark_20260613_1324.json"
    reaudit_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if reaudit_path is None:
        candidates = sorted((ROOT / "infra/benchmarks/reports").glob("benchmark_REAUDIT_*.json"))
        if not candidates:
            raise SystemExit("No benchmark_REAUDIT_*.json found")
        reaudit_path = candidates[-1]

    original = json.loads(original_path.read_text(encoding="utf-8"))
    reaudit = json.loads(reaudit_path.read_text(encoding="utf-8"))

    merged_summary: dict[str, dict] = {}
    for stage in ORIGINAL_ONLY:
        merged_summary[stage] = original["summary"].get(stage, {})
    for stage in REAUDIT_STAGES:
        merged_summary[stage] = reaudit["summary"].get(stage, {})

    models = reaudit.get("candidate_models") or sorted(
        {r["model"] for r in reaudit["results"]}
    )
    judge = reaudit.get("judge_model", "?")

    lines = [
        "# VocalMind Ollama Cloud Model Benchmark Summary v2",
        "",
        f"Re-audit source: `{reaudit_path.name}` (judge: `{judge}` via Ollama Cloud)",
        f"Original source (emotion_shift, rag_judge): `{original_path.name}`",
        "",
        "Stages marked **(re-audit)** used fixed harness + neutral judge. "
        "Stages marked **(original)** retain first-run results.",
        "",
        "## Per-stage results",
        "",
    ]

    for stage in [
        "emotion_shift",
        "process_adherence",
        "nli_policy",
        "rag_judge",
        "text_to_sql",
        "fast_classification",
    ]:
        tag = "(original)" if stage in ORIGINAL_ONLY else "(re-audit)"
        lines += [f"### Stage: {stage} {tag}", ""]
        extra = " | Latency SLA 200ms" if stage == "fast_classification" else ""
        lines.append(
            "| Model | Avg Score /10 | Pass Rate | Avg TTFT ms | Avg Total ms | "
            f"Groq-equiv $/1k | OpenAI-equiv $/1k | Latency flag{extra} |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        threshold = LATENCY_THRESHOLDS_MS.get(stage)
        stage_rows = merged_summary.get(stage, {})
        for model in sorted(stage_rows, key=lambda m: stage_rows[m]["avg_score"], reverse=True):
            s = stage_rows[model]
            flag = f"EXCEEDS {threshold}ms" if threshold and s["avg_total_ms"] > threshold else ""
            sla = ""
            if stage == "fast_classification":
                sla_rate = s.get("latency_sla_200ms_pass_rate", 0)
                sla = f"{sla_rate:.0%} pass" if sla_rate is not None else "n/a"
            lines.append(
                f"| {model} | {s['avg_score']:.1f} | {s['pass_rate']:.0%} | "
                f"{s['avg_ttft_ms']:.0f} | {s['avg_total_ms']:.0f} | "
                f"${s['groq_cost_per_1k']:.2f} | ${s['openai_cost_per_1k']:.2f} | {flag} | {sla} |"
            )
        lines.append("")

    # Recommendations
    heavy_scores = {m: _heavy_avg(merged_summary, m) for m in models}
    heavy_best = max(heavy_scores, key=heavy_scores.get) if heavy_scores else "?"
    fast_scores = {m: _fast_avg(merged_summary, m) for m in models}
    fast_best = max(fast_scores, key=fast_scores.get) if fast_scores else "?"
    sql_best = max(
        merged_summary.get("text_to_sql", {}),
        key=lambda m: merged_summary["text_to_sql"][m]["avg_score"],
        default="?",
    )

    es = merged_summary.get("emotion_shift", {})
    k26_heavy = heavy_scores.get("kimi-k2.6:cloud", 0)
    k25_heavy = heavy_scores.get("kimi-k2.5:cloud", 0)
    m8_es = es.get("ministral-3:8b", {}).get("avg_score", 0)
    m8_lat = es.get("ministral-3:8b", {}).get("avg_total_ms", 0)
    k26_es = es.get("kimi-k2.6:cloud", {})
    change_heavy = heavy_best != "kimi-k2.6:cloud"

    lines += [
        "## Recommendations",
        "",
        "### Heavy model (emotion_shift, process_adherence, nli_policy)",
        f"- Current production: `kimi-k2.6:cloud`",
        f"- kimi-k2.6 heavy composite: **{k26_heavy:.1f}/10**",
        f"- kimi-k2.5 heavy composite: **{k25_heavy:.1f}/10**",
        f"- Top scorer: **`{heavy_best}`** at **{heavy_scores.get(heavy_best, 0):.1f}/10**",
        f"- emotion_shift: ministral-3:8b tied top at **{m8_es:.1f}/10** with avg latency **{m8_lat:.0f}ms** "
        f"vs kimi-k2.6 **{k26_es.get('avg_total_ms', 0):.0f}ms**",
        "",
        f"**Recommendation to change OLLAMA_CLOUD_HEAVY_MODEL from kimi-k2.6:cloud: "
        f"{'YES' if change_heavy else 'NO'}** — "
        + (
            f"switch to `{heavy_best}` based on corrected re-audit."
            if change_heavy
            else "keep kimi-k2.6:cloud; corrected data does not justify a swap."
        ),
        "",
        "### Fast model (fast_classification, rag_judge)",
        f"- Current production: `ministral-3:8b`",
        f"- Top fast composite: **`{fast_best}`** at **{fast_scores.get(fast_best, 0):.1f}/10**",
        "",
        "### Text-to-SQL",
        f"- Best corrected score: **`{sql_best}`** at "
        f"**{merged_summary.get('text_to_sql', {}).get(sql_best, {}).get('avg_score', 0):.1f}/10**",
        "",
    ]

    sql_top = merged_summary.get("text_to_sql", {}).get(sql_best, {}).get("avg_score", 0)
    sql_ready = sql_top >= 7.0
    lines.append(
        f"**Text-to-SQL production readiness: {'ready' if sql_ready else 'not ready'}** — "
        + (
            f"top model meets pass threshold ({sql_top:.1f}/10)."
            if sql_ready
            else f"best corrected score {sql_top:.1f}/10; needs more prompt/harness work or higher sample count."
        )
    )
    lines.append("")

    out = ROOT / "infra/benchmarks/reports/benchmark_summary_v2.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
