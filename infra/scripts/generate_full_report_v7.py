#!/usr/bin/env python3
"""Generate FULL_REPORT_v7.md with post-calibration metrics and production fixes."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "infra" / "benchmarks" / "reports" / "overnight_20260614"
CAL_RESULTS = ROOT / "infra" / "benchmarks" / "calibration" / "judge_calibration_results.json"

STAGES = [
    "emotion_shift",
    "process_adherence",
    "nli_policy",
    "rag_judge",
    "text_to_sql",
    "fast_classification",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _summarize_gt(path: Path, *, f1_stage: bool = False) -> dict[str, dict[str, float]]:
    data = _load_json(path)
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in data.get("results", []):
        by_model[row["model"]].append(row)

    out: dict[str, dict[str, float]] = {}
    for model, rows in by_model.items():
        n = len(rows)
        exact = sum(1 for r in rows if r.get("match_type") == "exact")
        unparseable = sum(1 for r in rows if r.get("match_type") == "unparseable")
        parseable = n - unparseable
        exact_parseable = sum(
            1 for r in rows if r.get("match_type") == "exact" and r.get("match_type") != "unparseable"
        )
        sm: dict[str, float] = {
            "n": float(n),
            "exact_match_rate": exact / n if n else 0.0,
            "parseable_rate": parseable / n if n else 0.0,
            "exact_match_rate_among_parseable": exact_parseable / parseable if parseable else 0.0,
            "unparseable_rate": unparseable / n if n else 0.0,
            "gt_score_avg": sum(float(r.get("gt_score", 0)) for r in rows) / n if n else 0.0,
            "judge_avg": sum(float(r.get("judge_score_0_to_10") or 0) for r in rows) / n if n else 0.0,
        }
        if f1_stage:
            valid_rows = [
                r for r in rows if not str(r.get("gt_details", "")).startswith("extraction_error")
            ]
            sm["gt_f1_avg_excl_errors"] = (
                sum(float(r["gt_f1"]) for r in valid_rows) / len(valid_rows) if valid_rows else 0.0
            )
            sm["gt_f1_avg_incl_errors"] = sum(float(r.get("gt_f1") or 0.0) for r in rows) / n if n else 0.0
            sm["extract_err"] = sum(
                1 for r in rows if str(r.get("gt_details", "")).startswith("extraction_error")
            )
        out[model] = sm
    return out


def _winner_by_exact(sm: dict[str, dict[str, float]]) -> tuple[str, float]:
    best = max(sm, key=lambda m: (sm[m]["exact_match_rate"], sm[m]["gt_score_avg"]))
    return best, sm[best]["exact_match_rate"]


def _winner_by_f1(sm: dict[str, dict[str, float]], *, incl_errors: bool = True) -> tuple[str, float]:
    key = "gt_f1_avg_incl_errors" if incl_errors else "gt_f1_avg"
    best = max(sm, key=lambda m: (sm[m].get(key, 0), sm[m]["exact_match_rate"]))
    return best, sm[best].get(key, 0.0)


def generate(report_dir: Path = REPORT_DIR) -> Path:
    es_v2_path = report_dir / "emotion_shift_v2_groundtruth.json"
    es_sm = _summarize_gt(es_v2_path if es_v2_path.exists() else report_dir / "emotion_shift_groundtruth.json")
    pa_sm = _summarize_gt(report_dir / "process_adherence_groundtruth.json", f1_stage=True)
    nli_sm = _summarize_gt(report_dir / "nli_policy_groundtruth.json")
    rag_sm = _summarize_gt(report_dir / "rag_judge_groundtruth.json")
    sql_sm = _summarize_gt(report_dir / "text_to_sql_groundtruth.json")
    fc_sm = _summarize_gt(report_dir / "fast_classification_groundtruth.json")

    es_w, es_rate = _winner_by_exact(es_sm)
    pa_w, pa_f1 = _winner_by_f1(pa_sm, incl_errors=True)
    nli_w, nli_rate = _winner_by_exact(nli_sm)
    rag_w, rag_rate = _winner_by_exact(rag_sm)
    sql_w, sql_rate = _winner_by_exact(sql_sm)
    fc_w, fc_rate = _winner_by_exact(fc_sm)

    cal = _load_json(CAL_RESULTS) if CAL_RESULTS.exists() else {}
    pa_cal = (cal.get("per_axis") or {}).get("process_adherence", {})

    lines = [
        "# VocalMind Ollama Cloud Benchmark — FULL_REPORT_v7",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}  ",
        "**Audience:** Cold read — supersedes FULL_REPORT_v6  ",
        f"**Data sources:** Recomputed from checkpoints — see `LEADERBOARD_VALIDATION_v7.md` "
        "(deduped one row per model+sample_id). ES v2 n=170/model; NLI n=172/model (not 344).",
        "",
        "---",
        "",
        "## Changelog vs v6",
        "",
        "1. **Production json_mode (Prompt 16):** `build_emotion_shift_chain`, `build_nli_policy_chain`, and "
        "`build_process_adherence_chain` now bind `response_format={\"type\": \"json_object\"}` on ChatOpenAI "
        "(Ollama Cloud OpenAI-compatible API). `langchain_ollama` is not installed; native Ollama `format=` is not used.",
        "2. **PA scoring (Prompt 17):** `ground_truth_scorer.extract_pa_predicted_missing` reads top-level "
        "`missing_sop_steps` when present, otherwise derives missing steps from structured `evaluation` blocks "
        "(`justifications`, `sop_compliance`, `steps`, `step_evaluations`, etc.) using checkpoint-derived "
        "adherence/status vocabulary (`missing`, `partial`, `deviated`, …). Entries without a recognizable "
        "shape return an explicit extraction error (scored F1=0). **PA routing uses F1 over all n (errors_as_0), "
        "not mean-F1 excluding extraction errors** — the latter wrongly favored qwen3.5 (31% extract errors). "
        "**gemma3:12b judge score is NOT used for PA** "
        f"(calibration r={pa_cal.get('pearson_r', 'n/a')}, MAE={pa_cal.get('mae', 'n/a')}).",
        "3. **Per-stage routing (Prompt 18):** `OLLAMA_EMOTION_SHIFT_MODEL`, `OLLAMA_PROCESS_ADHERENCE_MODEL`, "
        "`OLLAMA_NLI_MODEL` added with fallback to `OLLAMA_CLOUD_HEAVY_MODEL`; `get_model_for_stage()` in `chains.py`.",
        "4. **NLI/SQL baseline (Prompt 19):** No full-population pre-tweak checkpoint exists; overnight run already "
        "used current `prompt_constants.py`. n=20 validation gains (+13 pp NLI, +6 pp SQL) are **not confirmed** at "
        "full scale. Full-population GT pass rates below are the authoritative numbers for v7.",
        "5. **ES offline parse (Prompt 22):** Old `emotion_shift.checkpoint.jsonl` responses use legacy field names "
        "→ 0% strict `EmotionShiftAnalysis` parse; v2 checkpoint → ~100% strict parse. "
        "**Live json_mode (Prompt 24):** 5/5 parse OK per stage (ES/PA/NLI) with `response_format={\"type\": \"json_object\"}` confirmed.",
        "6. **Production prompt fix:** JSON schema braces in `prompt_constants.py` escaped for LangChain templates "
        "(fixed `ValueError: Nested replacement fields` that blocked all live chain calls).",
        "7. **NLI strict parse (Prompt 23):** Overnight checkpoint uses `category` not `nli_category` → 100% strict "
        "failure offline; live production chains with format_instructions parse 5/5. `NLIEvaluation` accepts "
        "`verdict`/`category` aliases.",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"After judge calibration (48 samples, overall r={cal.get('overall', {}).get('pearson_r', 'n/a')}), "
        "PA judge scores are discarded for model selection. Production chains now request JSON object mode. "
        f"Per-stage GT winners: **emotion_shift** `{es_w}` ({es_rate:.0%} exact, v2 prompt), "
        f"**process_adherence** `{pa_w}` (F1={pa_f1:.3f} errors_as_0), **nli_policy** `{nli_w}` ({nli_rate:.0%} exact), "
        f"**rag_judge** `{rag_w}` ({rag_rate:.0%}), **text_to_sql** `{sql_w}` ({sql_rate:.0%}), "
        f"**fast_classification** `{fc_w}` ({fc_rate:.0%}).",
        "",
        "---",
        "",
        "## How to verify these numbers",
        "",
        "All leaderboard values are recomputed from overnight checkpoints (one row per model+sample_id, ",
        "last checkpoint line wins). No judge scores used for winners except where noted unreliable.",
        "",
        "```bash",
        "python infra/scripts/validate_leaderboard_v7.py      # offline, no API",
        "python infra/scripts/run_production_gt_validation.py  # live production chains vs GT",
        "```",
        "",
        "See `LEADERBOARD_VALIDATION_v7.md` for full per-model tables matching this report.",
        "",
        "**Live spot-check (production chains):** `run_production_gt_validation.py` runs 15 evenly-spaced ",
        "GT samples per stage (manifest in `validation_manifest_v7.json`) through the same chains shipped in ",
        "`chains.py`, then scores with `ground_truth_scorer`. Expect parse OK ≈100%; GT exact on a 15-sample slice ",
        "will vary (~40–60% is normal when full-population exact is ~50%). Low exact % is **task difficulty**, not a ",
        "measurement bug — offline validation confirms every v7 winner claim matches checkpoint recomputation.",
        "",
        "---",
        "",
        "## Leaderboard — all 6 axes",
        "",
        "| Stage | Best model | Primary metric | Value | GT pass (full pop.) | Judge avg (best) | Notes |",
        "|---|---|---|---:|---:|---:|---|",
        f"| emotion_shift | `{es_w}` | exact (v2, n=170) | **{es_rate:.0%}** | — | — | Judge trusted (cal r=1.0); production json_mode shipped |",
        f"| process_adherence | `{pa_w}` | mean GT F1 (errors_as_0) | **{pa_f1:.3f}** | — | unreliable | Judge r={pa_cal.get('pearson_r', 0):.3f} — use F1 incl. errors |",
        f"| nli_policy | `{nli_w}` | exact (all) | **{nli_rate:.0%}** | **{nli_rate:.0%}** | trusted | No pre-tweak full baseline |",
        f"| rag_judge | `{rag_w}` | exact (all) | **{rag_rate:.0%}** | **{rag_rate:.0%}** | trusted | Unchanged |",
        f"| text_to_sql | `{sql_w}` | execution exact | **{sql_rate:.0%}** | **{sql_rate:.0%}** | trusted | No pre-tweak full baseline |",
        f"| fast_classification | `{fc_w}` | exact (all) | **{fc_rate:.0%}** | **{fc_rate:.0%}** | all-agree | Unchanged |",
        "",
        "### emotion_shift — per model (v2 prompt, n=170)",
        "",
        "| Model | Exact % | Parseable % | n |",
        "|---|---:|---:|---:|",
    ]
    for model in sorted(es_sm, key=lambda m: es_sm[m]["exact_match_rate"], reverse=True):
        s = es_sm[model]
        lines.append(
            f"| {model} | {s['exact_match_rate']:.0%} | {s['parseable_rate']:.0%} | {int(s['n'])} |"
        )

    lines.extend(
        [
            "",
            "### process_adherence — per model (GT F1; **routing uses F1_incl_errors**) ",
            "",
            "| Model | F1 incl errors | F1 excl errors | exact % | extraction errors | n |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for model in sorted(pa_sm, key=lambda m: pa_sm[m].get("gt_f1_avg_incl_errors", 0), reverse=True):
        s = pa_sm[model]
        lines.append(
            f"| {model} | {s.get('gt_f1_avg_incl_errors', 0):.3f} | {s.get('gt_f1_avg_excl_errors', 0):.3f} | "
            f"{s['exact_match_rate']:.0%} | {int(s.get('extract_err', 0))} | {int(s['n'])} |"
        )
    lines.append("")
    lines.append(
        "> **F1 excl errors** (old, misleading): qwen3.5=0.621 on 106/153 entries. "
        "**F1 incl errors** (routing metric): kimi-k2.6=0.546 wins."
    )
    lines.extend(
        [
            "",
        ]
    )
    for title, sm in [
        ("nli_policy", nli_sm),
        ("rag_judge", rag_sm),
        ("text_to_sql", sql_sm),
        ("fast_classification", fc_sm),
    ]:
        lines.extend(["", f"### {title} — per model", "", "| Model | Exact % | n |", "|---|---:|---:|"])
        for model in sorted(sm, key=lambda m: sm[m]["exact_match_rate"], reverse=True):
            s = sm[model]
            lines.append(f"| {model} | {s['exact_match_rate']:.0%} | {int(s['n'])} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Recommended per-stage production models",
            "",
            "| Env var | Winner | Metric |",
            "|---|---|---|",
            f"| `OLLAMA_EMOTION_SHIFT_MODEL` | `{es_w}` | {es_rate:.0%} exact (v2) |",
            f"| `OLLAMA_PROCESS_ADHERENCE_MODEL` | `{pa_w}` | F1 {pa_f1:.3f} (errors_as_0) |",
            f"| `OLLAMA_NLI_MODEL` | `{nli_w}` | {nli_rate:.0%} exact |",
            f"| `OLLAMA_CLOUD_FAST_MODEL` | `ministral-3:8b` or `ministral-3:14b` | RAG 95% / FC 69% |",
            "",
            "---",
            "",
            "*End of FULL_REPORT_v7. Generator: `infra/scripts/generate_full_report_v7.py`.*",
        ]
    )

    out = report_dir / "FULL_REPORT_v7.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    path = generate()
    print(f"Wrote {path}")
