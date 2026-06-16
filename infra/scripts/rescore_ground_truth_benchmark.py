#!/usr/bin/env python3
"""Re-score saved benchmark JSONs with ground_truth_scorer (no new API calls)."""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ground_truth_scorer import (
    ES_CANONICAL_JUSTIFICATIONS,
    ES_CANONICAL_MAP,
    ScoreResult,
    canonicalize_shift_type,
    extract_emotion_prediction,
    parse_json_object,
    score_observation,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_DIR = ROOT / "infra" / "benchmarks" / "reports" / "overnight_20260614"
GT_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"

STAGES = [
    "emotion_shift",
    "process_adherence",
    "nli_policy",
    "rag_judge",
    "text_to_sql",
    "fast_classification",
]


def _percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * (p / 100.0)
    f = int(math.floor(k))
    c = min(f + 1, len(s) - 1)
    return s[f] if f == c else s[f] + (s[c] - s[f]) * (k - f)


def load_gt_index() -> dict[str, dict[str, dict[str, Any]]]:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    index: dict[str, dict[str, dict[str, Any]]] = {}
    for stage in STAGES:
        index[stage] = {s["sample_id"]: s for s in data.get(stage, [])}
    return index


def dedupe_rows_per_model_sample(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per (model, sample_id); last row in file wins (matches checkpoint resume)."""
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        by_key[(row["model"], row["sample_id"])] = row
    return list(by_key.values())


def load_checkpoint_deduped(report_dir: Path, stage: str) -> list[dict[str, Any]]:
    ckpt = report_dir / f"{stage}.checkpoint.jsonl"
    if not ckpt.exists():
        return []
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for line in ckpt.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        by_key[(row["model"], row["sample_id"])] = row
    return list(by_key.values())


def rescore_stage(
    report_dir: Path,
    stage: str,
    gt_index: dict[str, dict[str, dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]:
    src = report_dir / f"{stage}.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    rows = dedupe_rows_per_model_sample(data.get("results", []))
    gt_by_id = gt_index[stage]
    out_rows: list[dict[str, Any]] = []

    for row in rows:
        sid = row.get("sample_id", "")
        ref = gt_by_id.get(sid)
        if not ref:
            sr = ScoreResult(0.0, "unparseable", details=f"unknown sample {sid}")
        else:
            sr = score_observation(stage, row.get("raw_response", ""), ref, row)

        new_row = dict(row)
        new_row["gt_score"] = sr.gt_score
        new_row["match_type"] = sr.match_type
        if sr.precision is not None:
            new_row["gt_precision"] = sr.precision
            new_row["gt_recall"] = sr.recall
            new_row["gt_f1"] = sr.f1
        if sr.details:
            new_row["gt_details"] = sr.details
        out_rows.append(new_row)

    out_path = report_dir / f"{stage}_groundtruth.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "scoring_method": "ground_truth_comparison",
        "source": str(src),
        "results": out_rows,
        "summary": aggregate_by_model(out_rows),
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return out_rows, payload["summary"]


def aggregate_by_model(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)

    summary: dict[str, dict[str, float]] = {}
    for model, rs in by_model.items():
        n = len(rs)
        exact = sum(1 for r in rs if r.get("match_type") == "exact")
        unparse = sum(1 for r in rs if r.get("match_type") == "unparseable")
        parseable = n - unparse
        scores = [float(r.get("gt_score", 0)) for r in rs]
        lats = [float(r.get("total_latency_ms", 0)) for r in rs]
        old = [float(r.get("judge_score_0_to_10") or 0) for r in rs if r.get("judge_score_0_to_10") is not None]
        summary[model] = {
            "observation_count": n,
            "exact_match_rate": exact / n if n else 0.0,
            "parseable_rate": parseable / n if n else 0.0,
            "exact_match_rate_among_parseable": exact / parseable if parseable else 0.0,
            "gt_score_avg": sum(scores) / n if n else 0.0,
            "unparseable_rate": unparse / n if n else 0.0,
            "p50_total_latency_ms": _percentile(lats, 50),
            "p95_total_latency_ms": _percentile(lats, 95),
            "old_judge_avg": sum(old) / len(old) if old else 0.0,
        }
        if any(r.get("gt_f1") is not None for r in rs):
            f1s = [float(r["gt_f1"]) for r in rs if r.get("gt_f1") is not None]
            summary[model]["gt_f1_avg"] = sum(f1s) / len(f1s) if f1s else 0.0
            # errors_as_0: extraction errors now carry f1=0.0; mean over all n
            all_f1 = [float(r.get("gt_f1") or 0.0) for r in rs]
            summary[model]["gt_f1_avg_incl_errors"] = sum(all_f1) / n if n else 0.0
            valid = [r for r in rs if not str(r.get("gt_details", "")).startswith("extraction_error")]
            summary[model]["gt_f1_avg_excl_errors"] = (
                sum(float(r["gt_f1"]) for r in valid) / len(valid) if valid else 0.0
            )
            summary[model]["extraction_error_count"] = sum(
                1 for r in rs if str(r.get("gt_details", "")).startswith("extraction_error")
            )
            # Legacy key: routing uses incl_errors
            summary[model]["gt_f1_avg"] = summary[model]["gt_f1_avg_incl_errors"]
    return summary


def score_emotion_shift_canonical_rows(
    rows: list[dict[str, Any]],
    gt_by_id: dict[str, dict[str, Any]],
):
    for row in rows:
        ref = gt_by_id[row["sample_id"]]
        sr = score_observation(
            "emotion_shift",
            row.get("raw_response", ""),
            ref,
            row,
            use_canonicalization=True,
        )
        yield row, sr


def collect_emotion_shift_label_stats(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, int], dict[str, int]]:
    """Return (ambiguous_term_counts, unmapped_term_counts) from parseable JSON."""
    ambiguous: dict[str, int] = defaultdict(int)
    unmapped: dict[str, int] = defaultdict(int)
    for row in rows:
        data = parse_json_object(row.get("raw_response", ""))
        if not data:
            continue
        pred_type, _, _ = extract_emotion_prediction(data)
        if not pred_type:
            continue
        _, status = canonicalize_shift_type(pred_type)
        if status == "ambiguous":
            ambiguous[pred_type] += 1
        elif status == "unknown":
            unmapped[pred_type] += 1
    return dict(ambiguous), dict(unmapped)


def compare_divergences(
    all_rows: dict[str, list[dict[str, Any]]],
    gt_index: dict[str, dict[str, dict[str, Any]]],
    top_n: int = 3,
) -> list[dict[str, Any]]:
    divergences: list[dict[str, Any]] = []
    for stage, rows in all_rows.items():
        for r in rows:
            old = r.get("judge_score_0_to_10")
            if old is None:
                continue
            old_f = float(old)
            new_f = float(r.get("gt_score", 0))
            gap = abs(old_f - new_f)
            if gap >= 4.0:
                divergences.append(
                    {
                        "stage": stage,
                        "model": r["model"],
                        "sample_id": r["sample_id"],
                        "old_judge": old_f,
                        "gt_score": new_f,
                        "match_type": r.get("match_type"),
                        "gap": gap,
                        "raw_preview": (r.get("raw_response") or "")[:300],
                        "reference": gt_index[stage].get(r["sample_id"], {}).get("reference_answer", "")[:200],
                        "judge_reasoning": (r.get("judge_reasoning") or "")[:200],
                        "gt_details": r.get("gt_details", ""),
                    }
                )
    divergences.sort(key=lambda x: -x["gap"])
    return divergences[:top_n]


def write_full_report_v5(
    report_dir: Path,
    summaries: dict[str, dict[str, dict[str, float]]],
    divergences: list[dict[str, Any]],
    unparseable_flags: list[str],
    pa_verdict: str,
    v3_recs: dict[str, str],
    gt_recs: dict[str, str],
) -> Path:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# VocalMind Ollama Cloud Benchmark — FULL_REPORT_v5",
        "",
        f"**Generated:** {now}",
        "**Primary metric:** ground-truth exact match (objective comparison, no LLM judge)",
        "**Source:** Re-scored from saved raw responses in `overnight_20260614/` (zero new API calls)",
        "",
        "## Run status (unchanged from v3)",
        "",
        "| Stage | Observations | Errors |",
        "|---|---:|---:|",
    ]
    for stage in STAGES:
        p = report_dir / f"{stage}.json"
        if p.exists():
            n = len(json.loads(p.read_text(encoding="utf-8")).get("results", []))
            errs = sum(1 for r in json.loads(p.read_text(encoding="utf-8")).get("results", []) if r.get("error"))
            lines.append(f"| {stage} | {n} | {errs} |")

    lines.extend(["", "## Per-stage results (ground-truth scoring)", ""])

    for stage in STAGES:
        sm = summaries.get(stage, {})
        if not sm:
            continue
        lines.append(f"### {stage}")
        if stage == "text_to_sql":
            lines.append("> Execution-based scoring (unchanged from v3).")
        elif stage == "process_adherence":
            lines.append("> F1-based set match on missing SOP steps (precision/recall).")
        else:
            lines.append("> Exact/partial match against reference label or structured answer.")
        lines.append("")
        lines.append("| Model | Exact match % | GT score avg | Unparseable % | p50 ms | p95 ms | n |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for model in sorted(sm, key=lambda m: sm[m]["exact_match_rate"], reverse=True):
            s = sm[model]
            lines.append(
                f"| {model} | {s['exact_match_rate']:.0%} | {s['gt_score_avg']:.2f} | "
                f"{s['unparseable_rate']:.0%} | {s['p50_total_latency_ms']:.0f} | "
                f"{s['p95_total_latency_ms']:.0f} | {int(s['observation_count'])} |"
            )
        if stage == "process_adherence":
            lines.append("")
            for model in sorted(sm, key=lambda m: sm[m].get("gt_f1_avg", 0), reverse=True):
                if "gt_f1_avg" in sm[model]:
                    lines.append(f"- **{model}** mean F1: {sm[model]['gt_f1_avg']:.3f}")
        lines.append("")

    lines.extend(
        [
            "## Recommendation table (exact-match driven)",
            "",
            "| Role | Model | Exact match | Notes |",
            "|---|---|---:|---|",
        ]
    )
    for role, (model, rate) in gt_recs.items():
        lines.append(f"| {role} | `{model}` | {rate} | Primary metric |")

    lines.extend(
        [
            "",
            "## What changed vs v3 (judge-driven)",
            "",
            "| Stage | v3 judge winner | v5 GT winner | Changed? |",
            "|---|---|---|---|",
        ]
    )
    for stage in STAGES:
        v3m = v3_recs.get(stage, ("n/a",))[0]
        gtm = gt_recs.get(
            {
                "emotion_shift": "Heavy (emotion_shift)",
                "nli_policy": "Heavy (nli_policy)",
                "process_adherence": "Heavy (process_adherence)",
                "rag_judge": "RAG judge",
                "fast_classification": "Fast classification",
                "text_to_sql": "text_to_sql",
            }.get(stage, stage),
            ("n/a", ""),
        )[0]
        changed = "Yes" if v3m != gtm else "No"
        lines.append(f"| {stage} | {v3m} | {gtm} | {changed} |")

    lines.extend(
        [
            "",
            f"## process_adherence finding",
            "",
            pa_verdict,
            "",
            "## Unparseable responses (>10% threshold)",
            "",
        ]
    )
    if unparseable_flags:
        for flag in unparseable_flags:
            lines.append(f"- {flag}")
    else:
        lines.append("- None above 10% after parsing (see appendix for per-model rates).")

    lines.extend(["", "## Largest judge vs ground-truth divergences", ""])
    for d in divergences:
        lines.extend(
            [
                f"### {d['stage']} / {d['model']} / {d['sample_id']}",
                f"- Old judge: **{d['old_judge']}** | GT score: **{d['gt_score']}** ({d['match_type']})",
                f"- Reference: {d['reference']}",
                f"- GT details: {d.get('gt_details', '')}",
                f"- Judge said: {d.get('judge_reasoning', '')}",
                "",
            ]
        )

    lines.extend(
        [
            "## Appendix: Judge scores (secondary / subjective)",
            "",
            "Judge scores from v3 retained for transparency only — not used for recommendations above.",
            "",
            "| Stage | Model | Old judge avg | GT exact match | GT score avg |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for stage in STAGES:
        sm = summaries.get(stage, {})
        for model in sorted(sm):
            s = sm[model]
            lines.append(
                f"| {stage} | {model} | {s.get('old_judge_avg', 0):.2f} | "
                f"{s['exact_match_rate']:.0%} | {s['gt_score_avg']:.2f} |"
            )

    out = report_dir / "FULL_REPORT_v5.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _split_metrics_table_lines(sm: dict[str, dict[str, float]]) -> list[str]:
    lines = [
        "| Model | Exact (all) | Exact (parseable) | Parseable % | GT score avg | p50 ms | n |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model in sorted(sm, key=lambda m: sm[m]["exact_match_rate"], reverse=True):
        s = sm[model]
        lines.append(
            f"| {model} | {s['exact_match_rate']:.0%} | {s['exact_match_rate_among_parseable']:.0%} | "
            f"{s['parseable_rate']:.0%} | {s['gt_score_avg']:.2f} | {s['p50_total_latency_ms']:.0f} | "
            f"{int(s['observation_count'])} |"
        )
    return lines


def write_full_report_v5_1(
    report_dir: Path,
    summaries: dict[str, dict[str, dict[str, float]]],
    es_canonical_summary: dict[str, dict[str, float]],
    ambiguous_counts: dict[str, int],
    unmapped_counts: dict[str, int],
    divergences: list[dict[str, Any]],
    unparseable_flags: list[str],
    pa_verdict: str,
    v3_recs: dict[str, str],
    gt_recs: dict[str, str],
    es_recommendation: str,
    pipeline_retry_note: str,
) -> Path:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# VocalMind Ollama Cloud Benchmark — FULL_REPORT_v5.1",
        "",
        f"**Generated:** {now}",
        "**Primary metric:** ground-truth exact match (objective comparison, no LLM judge)",
        "**Source:** Re-scored from saved raw responses in `overnight_20260614/` (zero new API calls)",
        "",
        "## Metric definitions (read together)",
        "",
        '**Exact (all)** — fraction of all samples with an exact ground-truth match. This is the headline '
        "comparability number from v5 (includes unparseable as non-exact).",
        "",
        '**Exact (parseable)** — among samples where output was scoreable, what fraction matched exactly. '
        "This isolates reasoning quality from formatting/schema failures.",
        "",
        "**Parseable %** — fraction of samples where the scorer could extract a verdict at all "
        "(1 − unparseable rate). Low parseable % means the model ignored output schema, not necessarily "
        "that it reasoned incorrectly.",
        "",
        "These three numbers must be read together: a model can score high on accuracy-when-parseable but "
        "low on exact-all if it frequently returns unparseable output.",
        "",
        "## Run status (unchanged from v3)",
        "",
        "| Stage | Observations | Errors |",
        "|---|---:|---:|",
    ]
    for stage in STAGES:
        p = report_dir / f"{stage}.json"
        if p.exists():
            n = len(json.loads(p.read_text(encoding="utf-8")).get("results", []))
            errs = sum(1 for r in json.loads(p.read_text(encoding="utf-8")).get("results", []) if r.get("error"))
            lines.append(f"| {stage} | {n} | {errs} |")

    lines.extend(["", "## Part 1 — Split metrics (all stages)", ""])

    for stage in STAGES:
        sm = summaries.get(stage, {})
        if not sm:
            continue
        lines.append(f"### {stage}")
        if stage == "text_to_sql":
            lines.append("> Execution-based scoring (unchanged from v3). Parseable ≈ 100%.")
        elif stage == "process_adherence":
            lines.append("> F1-based set match on missing SOP steps.")
        else:
            lines.append("> Exact/partial match against reference label or structured answer.")
        lines.append("")
        lines.extend(_split_metrics_table_lines(sm))
        if stage == "process_adherence":
            lines.append("")
            for model in sorted(sm, key=lambda m: sm[m].get("gt_f1_avg", 0), reverse=True):
                if "gt_f1_avg" in sm[model]:
                    lines.append(f"- **{model}** mean F1: {sm[model]['gt_f1_avg']:.3f}")
        lines.append("")

    # Part 2 — canonicalization
    lines.extend(
        [
            "## Part 2 — emotion_shift label canonicalization",
            "",
            "Benchmark models use inconsistent shift-type vocabulary. The v5 scorer used alias/fuzzy matching; "
            "v5.1 adds an explicit conservative synonym map (not partial credit for wrong answers).",
            "",
            "### Rubric reference",
            "",
            '- Task (prompts.py): "Detect cross-modal contradictions between text and acoustic emotion."',
            '- Classification (prompts.py): "classify type (e.g., Sarcasm, Passive-Aggression)." ',
            "- Ground-truth categories: `sarcasm`, `passive_aggression`, `cross_modal`, `none`.",
            "",
            "### Mappings applied",
            "",
        ]
    )
    by_target: dict[str, list[str]] = defaultdict(list)
    for variant, target in sorted(ES_CANONICAL_MAP.items(), key=lambda x: (x[1], x[0])):
        if variant.replace(" ", "_").replace("-", "_") == target:
            continue
        by_target[target].append(f"`{variant}` → `{target}`")
    for target in ("cross_modal", "sarcasm", "passive_aggression", "none"):
        if target in by_target:
            lines.append(f"**{target}** — {ES_CANONICAL_JUSTIFICATIONS.get(target, '')}")
            for m in by_target[target][:20]:
                lines.append(f"- {m}")
            if len(by_target[target]) > 20:
                lines.append(f"- … and {len(by_target[target]) - 20} more variants")
            lines.append("")

    amb_total = sum(ambiguous_counts.values())
    unmapped_total = sum(unmapped_counts.values())
    lines.extend(
        [
            "### Ambiguous / not mapped",
            "",
            f"- **Ambiguous terms (explicit blocklist):** {amb_total} sample-label occurrences across all models",
            f"- **Unknown unmapped terms:** {unmapped_total} occurrences",
            "",
        ]
    )
    if ambiguous_counts:
        lines.append("Top ambiguous labels seen in parseable JSON:")
        for term, c in sorted(ambiguous_counts.items(), key=lambda x: -x[1])[:12]:
            lines.append(f"- `{term}`: {c}")
        lines.append("")
    if unmapped_counts:
        lines.append("Top unmapped labels (left as no_match):")
        for term, c in sorted(unmapped_counts.items(), key=lambda x: -x[1])[:12]:
            lines.append(f"- `{term}`: {c}")
        lines.append("")

    lines.extend(["### emotion_shift before / after canonicalization", ""])
    lines.append(
        "| Model | Exact (all) | Exact (all) canon | Exact (parseable) | Exact (parseable) canon | Parseable % |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|")
    es_sm = summaries.get("emotion_shift", {})
    for model in sorted(es_sm, key=lambda m: es_sm[m]["exact_match_rate"], reverse=True):
        old = es_sm[model]
        new = es_canonical_summary.get(model, {})
        lines.append(
            f"| {model} | {old['exact_match_rate']:.0%} | {new.get('exact_match_rate', 0):.0%} | "
            f"{old['exact_match_rate_among_parseable']:.0%} | "
            f"{new.get('exact_match_rate_among_parseable', 0):.0%} | {old['parseable_rate']:.0%} |"
        )
    lines.append("")

    # Part 3 — recommendations
    lines.extend(
        [
            "## Part 3 — Recommendations (split-metric framing)",
            "",
            "### Production pipeline: parse failure behavior",
            "",
            pipeline_retry_note,
            "",
            "**Framing for emotion_shift:** reliability-first — parse failures degrade to `dissonance_type=Unknown` "
            "with no re-prompt; parseable % matters as much as accuracy-among-parseable.",
            "",
            es_recommendation,
            "",
            "### Recommendation table",
            "",
            "| Stage | Model | Exact (all) | Exact (parseable) | Parseable % | Verdict |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    role_map = {
        "emotion_shift": "Heavy (emotion_shift)",
        "nli_policy": "Heavy (nli_policy)",
        "process_adherence": "Heavy (process_adherence)",
        "rag_judge": "RAG judge",
        "fast_classification": "Fast classification",
        "text_to_sql": "text_to_sql",
    }
    for stage in STAGES:
        sm = summaries.get(stage, {})
        if not sm:
            continue
        if stage == "process_adherence":
            best = max(sm, key=lambda m: (sm[m].get("gt_f1_avg", 0), sm[m]["exact_match_rate"]))
            verdict = f"GT winner (F1={sm[best].get('gt_f1_avg', 0):.2f})"
        elif stage == "emotion_shift":
            # reliability-first: weight parseable then exact among parseable
            best = max(
                sm,
                key=lambda m: (sm[m]["parseable_rate"], sm[m]["exact_match_rate_among_parseable"], sm[m]["exact_match_rate"]),
            )
            verdict = "GT winner (reliability-first)"
        else:
            best = max(sm, key=lambda m: (sm[m]["exact_match_rate"], sm[m]["gt_score_avg"]))
            verdict = "GT winner"
        s = sm[best]
        lines.append(
            f"| {stage} | `{best}` | {s['exact_match_rate']:.0%} | "
            f"{s['exact_match_rate_among_parseable']:.0%} | {s['parseable_rate']:.0%} | {verdict} |"
        )

    lines.extend(
        [
            "",
            "## What changed vs v3 (judge-driven)",
            "",
            "| Stage | v3 judge winner | v5.1 GT winner | Changed? |",
            "|---|---|---|---|",
        ]
    )
    for stage in STAGES:
        v3m = v3_recs.get(stage, ("n/a",))[0]
        gtm = gt_recs.get(role_map.get(stage, stage), ("n/a", ""))[0]
        changed = "Yes" if v3m != gtm else "No"
        lines.append(f"| {stage} | {v3m} | {gtm} | {changed} |")

    lines.extend(["", "## process_adherence finding", "", pa_verdict, "", "## Unparseable responses (>10%)", ""])
    if unparseable_flags:
        for flag in unparseable_flags:
            lines.append(f"- {flag}")
    else:
        lines.append("- None above 10% after parsing.")

    lines.extend(["", "## Largest judge vs ground-truth divergences", ""])
    for d in divergences:
        lines.extend(
            [
                f"### {d['stage']} / {d['model']} / {d['sample_id']}",
                f"- Old judge: **{d['old_judge']}** | GT score: **{d['gt_score']}** ({d['match_type']})",
                f"- Reference: {d['reference']}",
                f"- GT details: {d.get('gt_details', '')}",
                "",
            ]
        )

    lines.extend(
        [
            "## Appendix: Judge scores (secondary)",
            "",
            "| Stage | Model | Old judge avg | Exact (all) | Exact (parseable) | Parseable % |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for stage in STAGES:
        sm = summaries.get(stage, {})
        for model in sorted(sm):
            s = sm[model]
            lines.append(
                f"| {stage} | {model} | {s.get('old_judge_avg', 0):.2f} | "
                f"{s['exact_match_rate']:.0%} | {s['exact_match_rate_among_parseable']:.0%} | "
                f"{s['parseable_rate']:.0%} |"
            )

    out = report_dir / "FULL_REPORT_v5.1.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def pick_winner(summaries: dict[str, dict[str, dict[str, float]]], stage: str) -> tuple[str, str]:
    sm = summaries.get(stage, {})
    if not sm:
        return ("n/a", "n/a")
    if stage == "process_adherence":
        best = max(sm, key=lambda m: (sm[m].get("gt_f1_avg", 0), sm[m]["exact_match_rate"]))
        rate = f"F1={sm[best].get('gt_f1_avg', 0):.2f}, exact={sm[best]['exact_match_rate']:.0%}"
    elif stage == "emotion_shift":
        best = max(
            sm,
            key=lambda m: (sm[m]["parseable_rate"], sm[m]["exact_match_rate_among_parseable"], sm[m]["exact_match_rate"]),
        )
        rate = (
            f"exact={sm[best]['exact_match_rate']:.0%}, "
            f"parseable={sm[best]['parseable_rate']:.0%}, "
            f"exact|parseable={sm[best]['exact_match_rate_among_parseable']:.0%}"
        )
    else:
        best = max(sm, key=lambda m: (sm[m]["exact_match_rate"], sm[m]["gt_score_avg"]))
        rate = f"{sm[best]['exact_match_rate']:.0%}"
    return best, rate


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-score benchmark with ground-truth comparison")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    args = parser.parse_args()
    report_dir = Path(args.report_dir)

    gt_index = load_gt_index()
    all_rows: dict[str, list[dict[str, Any]]] = {}
    summaries: dict[str, dict[str, dict[str, float]]] = {}

    total_rescored = 0
    for stage in STAGES:
        rows, sm = rescore_stage(report_dir, stage, gt_index)
        all_rows[stage] = rows
        summaries[stage] = sm
        total_rescored += len(rows)
        print(f"{stage}: wrote {len(rows)} rows -> {stage}_groundtruth.json")

    # Part 4 comparison table
    print("\n=== Judge vs Ground Truth (split metrics) ===")
    print(
        f"{'Stage':<22} {'Model':<20} {'ExactAll':>8} {'ExactPar':>8} {'Parse':>7} {'Unparse':>8}"
    )
    for stage in STAGES:
        for model, s in sorted(summaries.get(stage, {}).items(), key=lambda x: -x[1]["exact_match_rate"]):
            print(
                f"{stage:<22} {model:<20} {s['exact_match_rate']:7.0%} "
                f"{s['exact_match_rate_among_parseable']:7.0%} {s['parseable_rate']:6.0%} "
                f"{s['unparseable_rate']:7.0%}"
            )

    # emotion_shift canonical re-score
    es_rows = all_rows.get("emotion_shift", [])
    es_canonical_scored = list(score_emotion_shift_canonical_rows(es_rows, gt_index["emotion_shift"]))
    es_canonical_summary = aggregate_by_model(
        [{"model": row["model"], "match_type": sr.match_type, "gt_score": sr.gt_score} for row, sr in es_canonical_scored]
    )
    ambiguous_counts, unmapped_counts = collect_emotion_shift_label_stats(es_rows)

    print("\n=== emotion_shift canonical vs pre-canonical ===")
    for model in sorted(summaries["emotion_shift"], key=lambda m: -summaries["emotion_shift"][m]["exact_match_rate"]):
        old = summaries["emotion_shift"][model]
        new = es_canonical_summary[model]
        print(
            f"{model}: exact_all {old['exact_match_rate']:.0%}->{new['exact_match_rate']:.0%} | "
            f"exact_parseable {old['exact_match_rate_among_parseable']:.0%}->"
            f"{new['exact_match_rate_among_parseable']:.0%} | parseable {old['parseable_rate']:.0%}"
        )

    unparseable_flags = []
    for stage in STAGES:
        for model, s in summaries.get(stage, {}).items():
            if s["unparseable_rate"] > 0.10:
                unparseable_flags.append(f"{stage}/{model}: {s['unparseable_rate']:.0%} unparseable")

    divergences = compare_divergences(all_rows, gt_index, top_n=5)

    # PA verdict
    pa_sm = summaries.get("process_adherence", {})
    if pa_sm:
        avg_judge = sum(s.get("old_judge_avg", 0) for s in pa_sm.values()) / len(pa_sm)
        avg_f1 = sum(s.get("gt_f1_avg", 0) for s in pa_sm.values()) / len(pa_sm)
        avg_exact = sum(s["exact_match_rate"] for s in pa_sm.values()) / len(pa_sm)
        if avg_f1 >= 0.5 or avg_exact >= 0.4:
            pa_verdict = (
                f"F1-based GT scoring shows **better-than-judge-suggested** step identification "
                f"(mean F1={avg_f1:.2f}, exact-match={avg_exact:.0%}) vs mean judge avg={avg_judge:.2f}. "
                "The judge was likely penalizing format/schema differences more than content."
            )
        else:
            pa_verdict = (
                f"F1-based GT scoring **confirms models genuinely struggle** on process_adherence "
                f"(mean F1={avg_f1:.2f}, exact-match={avg_exact:.0%}, judge avg={avg_judge:.2f}). "
                "Low scores are not primarily a judge artifact."
            )
    else:
        pa_verdict = "No process_adherence data."

    v3_recs = {
        "emotion_shift": ("ministral-3:14b", ""),
        "process_adherence": ("qwen3.5:cloud", ""),
        "nli_policy": ("kimi-k2.5:cloud", ""),
        "rag_judge": ("ministral-3:8b", ""),
        "text_to_sql": ("qwen3.5:cloud", ""),
        "fast_classification": ("ministral-3:14b", ""),
    }
    gt_recs = {
        "Heavy (emotion_shift)": pick_winner(summaries, "emotion_shift"),
        "Heavy (nli_policy)": pick_winner(summaries, "nli_policy"),
        "Heavy (process_adherence)": pick_winner(summaries, "process_adherence"),
        "RAG judge": pick_winner(summaries, "rag_judge"),
        "Fast classification": pick_winner(summaries, "fast_classification"),
        "text_to_sql": pick_winner(summaries, "text_to_sql"),
    }

    out = write_full_report_v5(
        report_dir, summaries, divergences, unparseable_flags, pa_verdict, v3_recs, gt_recs
    )
    print(f"\nWrote {out}")

    es_sm = summaries["emotion_shift"]
    es_winner = pick_winner(summaries, "emotion_shift")[0]
    kimi = es_sm.get("kimi-k2.5:cloud", {})
    ministral = es_sm.get("ministral-3:14b", {})
    es_recommendation = (
        f"**Updated emotion_shift winner: `{es_winner}`** (reliability-first).\n\n"
        f"- `kimi-k2.5:cloud`: {kimi.get('exact_match_rate', 0):.0%} exact (all) / "
        f"{kimi.get('exact_match_rate_among_parseable', 0):.0%} among parseable / "
        f"{kimi.get('parseable_rate', 0):.0%} parseable — highest accuracy when scoreable, but "
        f"{kimi.get('unparseable_rate', 0):.0%} unparseable.\n"
        f"- `ministral-3:14b`: {ministral.get('exact_match_rate', 0):.0%} exact (all) / "
        f"{ministral.get('exact_match_rate_among_parseable', 0):.0%} among parseable / "
        f"{ministral.get('parseable_rate', 0):.0%} parseable — more reliable JSON, lower reasoning accuracy.\n"
        f"- Production (`service.py`) does **not** retry on JSON parse failure; failures fall back to "
        f"`dissonance_type=Unknown`. Recommend `{es_winner}` unless prompt/schema is tightened to "
        "raise kimi-k2.5 parseable % (stricter JSON-only instruction)."
    )
    pipeline_retry_note = (
        "`chains.py` `_invoke_chain_with_retry` retries only **transient API errors** (429, timeout, connection) "
        "up to 3× — **not** JSON/Pydantic parse failures. `analyze_emotion_shift` catches any chain failure "
        "(including parse errors) and returns degraded `EmotionShiftAnalysis` with `dissonance_type=\"Unknown\"` "
        "and `insufficient_evidence=True`. **No re-prompt on parse failure.**"
    )

    out51 = write_full_report_v5_1(
        report_dir,
        summaries,
        es_canonical_summary,
        ambiguous_counts,
        unmapped_counts,
        divergences,
        unparseable_flags,
        pa_verdict,
        v3_recs,
        gt_recs,
        es_recommendation,
        pipeline_retry_note,
    )
    print(f"Wrote {out51}")
    print(f"Total observations re-scored: {total_rescored} (150 text_to_sql carried execution scores)")


if __name__ == "__main__":
    main()
