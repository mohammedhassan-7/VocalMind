#!/usr/bin/env python3
"""
Recompute FULL_REPORT_v7 leaderboard from checkpoints + ground truth (single source of truth).

Methodology (documented in output):
- One observation per (model, sample_id); last checkpoint line wins.
- emotion_shift: emotion_shift_v2.checkpoint.jsonl (v2 production prompt, n=170/model).
- All other stages: overnight_{stage}.checkpoint.jsonl.
- PA primary metric: mean GT F1 with extraction errors scored as 0 (errors_as_0).
- Other stages: exact match rate vs ollama_cloud_ground_truth_v2.json.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ground_truth_scorer import score_observation

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "infra" / "benchmarks" / "reports" / "overnight_20260614"
GT_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"
OUT_PATH = REPORT_DIR / "LEADERBOARD_VALIDATION_v7.md"

STAGE_SOURCES = {
    "emotion_shift": "emotion_shift_v2.checkpoint.jsonl",
    "process_adherence": "process_adherence.checkpoint.jsonl",
    "nli_policy": "nli_policy.checkpoint.jsonl",
    "rag_judge": "rag_judge.checkpoint.jsonl",
    "text_to_sql": "text_to_sql.checkpoint.jsonl",
    "fast_classification": "fast_classification.checkpoint.jsonl",
}

V7_CLAIMS = {
    "emotion_shift": ("kimi-k2.5:cloud", "exact", 0.53),
    "process_adherence": ("kimi-k2.6:cloud", "f1_incl", 0.546),
    "nli_policy": ("ministral-3:8b", "exact", 0.52),
    "rag_judge": ("ministral-3:8b", "exact", 0.95),
    "text_to_sql": ("qwen3.5:cloud", "exact", 0.54),
    "fast_classification": ("ministral-3:14b", "exact", 0.69),
}


def load_gt() -> dict[str, dict[str, dict]]:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    return {stage: {s["sample_id"]: s for s in data.get(stage, [])} for stage in STAGE_SOURCES}


def load_deduped_checkpoint(stage: str) -> list[dict]:
    path = REPORT_DIR / STAGE_SOURCES[stage]
    by: dict[tuple[str, str], dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        by[(row["model"], row["sample_id"])] = row
    return list(by.values())


def score_rows(stage: str, rows: list[dict], gt: dict[str, dict]) -> list[dict]:
    scored = []
    for row in rows:
        sid = row["sample_id"]
        ref = gt.get(sid)
        if not ref:
            continue
        sr = score_observation(stage, row.get("raw_response", ""), ref, row)
        scored.append({**row, "sr": sr})
    return scored


def aggregate(stage: str, scored: list[dict]) -> dict[str, dict[str, float]]:
    by_model: dict[str, list] = defaultdict(list)
    for row in scored:
        by_model[row["model"]].append(row)

    out: dict[str, dict[str, float]] = {}
    for model, rs in by_model.items():
        n = len(rs)
        exact = sum(1 for r in rs if r["sr"].match_type == "exact")
        unparse = sum(1 for r in rs if r["sr"].match_type == "unparseable")
        f1_incl = sum(float(r["sr"].f1 or 0) for r in rs) / n if n else 0.0
        valid = [r for r in rs if not str(r["sr"].details).startswith("extraction_error")]
        f1_excl = sum(float(r["sr"].f1 or 0) for r in valid) / len(valid) if valid else 0.0
        extract_err = sum(1 for r in rs if str(r["sr"].details).startswith("extraction_error"))
        out[model] = {
            "n": n,
            "exact_rate": exact / n if n else 0.0,
            "parseable_rate": (n - unparse) / n if n else 0.0,
            "f1_incl": f1_incl,
            "f1_excl": f1_excl,
            "extract_err": extract_err,
        }
    return out


def pick_winner(stage: str, agg: dict[str, dict[str, float]]) -> tuple[str, float, str]:
    if stage == "process_adherence":
        best = max(agg, key=lambda m: (agg[m]["f1_incl"], agg[m]["exact_rate"]))
        return best, agg[best]["f1_incl"], "f1_incl"
    best = max(agg, key=lambda m: (agg[m]["exact_rate"], agg[m]["parseable_rate"]))
    return best, agg[best]["exact_rate"], "exact"


def main() -> None:
    gt = load_gt()
    lines = [
        "# Leaderboard validation v7 (recomputed from checkpoints)",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Ground truth:** `{GT_PATH.name}`  ",
        "**Dedup:** one row per `(model, sample_id)`, last checkpoint line wins.",
        "",
        "## Summary vs FULL_REPORT_v7 claims",
        "",
        "| Stage | Claimed winner | Claimed | Recomputed winner | Recomputed | Match? |",
        "|---|---|---:|---|---:|---|",
    ]

    for stage in STAGE_SOURCES:
        rows = load_deduped_checkpoint(stage)
        scored = score_rows(stage, rows, gt[stage])
        agg = aggregate(stage, scored)
        winner, val, metric = pick_winner(stage, agg)
        claim_model, claim_metric, claim_val = V7_CLAIMS[stage]
        if claim_metric == "f1_incl":
            claim_actual = agg.get(claim_model, {}).get("f1_incl", 0)
        else:
            claim_actual = agg.get(claim_model, {}).get("exact_rate", 0)
        match = winner == claim_model and abs(claim_actual - claim_val) < 0.015
        lines.append(
            f"| {stage} | `{claim_model}` | {claim_val:.3f} | `{winner}` | {val:.3f} | "
            f"{'YES' if match else '**NO**'} |"
        )

        lines.extend(["", f"### {stage} — per model", ""])
        if stage == "process_adherence":
            lines.append("| Model | n | exact % | F1 incl | F1 excl | extract_err |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for m in sorted(agg, key=lambda x: agg[x]["f1_incl"], reverse=True):
                a = agg[m]
                lines.append(
                    f"| {m} | {int(a['n'])} | {a['exact_rate']:.1%} | {a['f1_incl']:.3f} | "
                    f"{a['f1_excl']:.3f} | {int(a['extract_err'])} |"
                )
        else:
            lines.append("| Model | n | exact % | parseable % |")
            lines.append("|---|---:|---:|---:|")
            for m in sorted(agg, key=lambda x: agg[x]["exact_rate"], reverse=True):
                a = agg[m]
                lines.append(
                    f"| {m} | {int(a['n'])} | {a['exact_rate']:.1%} | {a['parseable_rate']:.1%} |"
                )
        lines.append("")

    lines.append("## Data sources")
    lines.append("")
    for stage, fname in STAGE_SOURCES.items():
        lines.append(f"- **{stage}:** `{fname}`")
    lines.append("")
    lines.append(
        "Re-run: `python infra/scripts/validate_leaderboard_v7.py`  "
        "(no API calls; scores saved `raw_response` from overnight run)."
    )

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(OUT_PATH.read_text(encoding="utf-8").split("## Summary")[1][:1200])


if __name__ == "__main__":
    main()
