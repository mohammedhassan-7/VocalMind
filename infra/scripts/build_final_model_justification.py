#!/usr/bin/env python3
"""Build final ES+NLI model justification report from completed benchmark JSON."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

from ground_truth_scorer import score_observation  # noqa: E402

REPORT_DIR = ROOT / "infra" / "benchmarks" / "reports" / "overnight_20260614"
GT_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"


def _load_rows() -> tuple[list[dict], str]:
    run_path = REPORT_DIR / "final_run_es_nli_8models_v10.json"
    checkpoint_path = REPORT_DIR / "final_run_es_nli_8models_v10.checkpoint.jsonl"
    if run_path.exists():
        data = json.loads(run_path.read_text(encoding="utf-8"))
        return data.get("results", []), str(run_path)
    if checkpoint_path.exists():
        rows = [json.loads(line) for line in checkpoint_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return rows, str(checkpoint_path)
    raise SystemExit(f"Missing both run + checkpoint files under {REPORT_DIR}")


def _dedupe(rows: list[dict]) -> list[dict]:
    by_key: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        by_key[(row.get("stage", ""), row.get("model", ""), row.get("sample_id", ""))] = row
    return list(by_key.values())


def _score_stage(stage: str, rows: list[dict], gt_index: dict[str, dict]) -> dict[str, dict[str, float]]:
    by_model: dict[str, list[tuple[dict, object]]] = defaultdict(list)
    for row in rows:
        if row.get("stage") != stage:
            continue
        sid = row.get("sample_id")
        ref = gt_index.get(stage, {}).get(sid)
        if not ref:
            continue
        sr = score_observation(stage, row.get("raw_response", ""), ref, row)
        by_model[row["model"]].append((row, sr))

    agg: dict[str, dict[str, float]] = {}
    for model, pairs in by_model.items():
        n = len(pairs)
        exact = sum(1 for _, sr in pairs if getattr(sr, "match_type", "") == "exact")
        unparseable = sum(1 for _, sr in pairs if getattr(sr, "match_type", "") == "unparseable")
        lat = sorted(float(r.get("total_latency_ms") or 0) for r, _ in pairs)
        p50 = lat[len(lat) // 2] if lat else 0.0
        avg_score = sum(float(getattr(sr, "gt_score", 0.0)) for _, sr in pairs) / n if n else 0.0
        agg[model] = {
            "n": n,
            "exact_rate": exact / n if n else 0.0,
            "parseable_rate": (n - unparseable) / n if n else 0.0,
            "p50_ms": p50,
            "gt_score_avg": avg_score,
        }
    return agg


def _sorted_models(agg: dict[str, dict[str, float]]) -> list[tuple[str, dict[str, float]]]:
    return sorted(
        agg.items(),
        key=lambda kv: (kv[1]["exact_rate"], kv[1]["parseable_rate"], -kv[1]["p50_ms"]),
        reverse=True,
    )


def main() -> None:
    loaded_rows, source_path = _load_rows()
    rows = _dedupe(loaded_rows)
    gt = json.loads(GT_PATH.read_text(encoding="utf-8"))
    gt_index = {
        "emotion_shift": {s["sample_id"]: s for s in gt.get("emotion_shift", [])},
        "nli_policy": {s["sample_id"]: s for s in gt.get("nli_policy", [])},
    }

    es = _score_stage("emotion_shift", rows, gt_index)
    nli = _score_stage("nli_policy", rows, gt_index)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Final Model Justification v10",
        "",
        f"**Generated:** {now}  ",
        "**Scope:** full-population `emotion_shift` (170) + `nli_policy` (172), 8 models",
        f"**Source:** `{source_path}`  ",
        f"**Rows after de-dup:** {len(rows)}",
        "",
        "## Selection Criteria",
        "",
        "1. Primary: exact match rate vs GT",
        "2. Tie-breaker: parseable rate",
        "3. Operational tie-breaker: p50 latency",
        "",
        "## emotion_shift (friction diagnosis)",
        "",
        "| Model | n | exact % | parseable % | p50 ms | GT avg |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model, stats in _sorted_models(es):
        lines.append(
            f"| {model} | {int(stats['n'])} | {stats['exact_rate']:.1%} | "
            f"{stats['parseable_rate']:.1%} | {stats['p50_ms']:.0f} | {stats['gt_score_avg']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## nli_policy",
            "",
            "| Model | n | exact % | parseable % | p50 ms | GT avg |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for model, stats in _sorted_models(nli):
        lines.append(
            f"| {model} | {int(stats['n'])} | {stats['exact_rate']:.1%} | "
            f"{stats['parseable_rate']:.1%} | {stats['p50_ms']:.0f} | {stats['gt_score_avg']:.2f} |"
        )

    es_winner = _sorted_models(es)[0][0] if es else "n/a"
    nli_winner = _sorted_models(nli)[0][0] if nli else "n/a"
    lines.extend(
        [
            "",
            "## Recommended Production Models",
            "",
            f"- `OLLAMA_EMOTION_SHIFT_MODEL={es_winner}`",
            f"- `OLLAMA_NLI_MODEL={nli_winner}`",
            "",
            "Justification: highest exact with strong parseability and acceptable latency on full-population samples.",
        ]
    )

    out_path = REPORT_DIR / "FINAL_MODEL_JUSTIFICATION_v10.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
