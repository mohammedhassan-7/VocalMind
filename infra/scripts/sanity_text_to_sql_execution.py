#!/usr/bin/env python3
"""Sanity-check execution scorer on sql_001-005 vs prior LLM judge scores."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GT = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth.json"
REPORT = ROOT / "infra" / "benchmarks" / "reports" / "benchmark_subset_20260613_1648.json"

import sys

sys.path.insert(0, str(ROOT / "infra" / "scripts"))
from text_to_sql_execution import score_sql_execution  # noqa: E402


def main() -> None:
    gt = json.loads(GT.read_text(encoding="utf-8"))
    by_id = {s["sample_id"]: s for s in gt["text_to_sql"]}
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    old: dict[str, list[float]] = {}
    model_sql: dict[str, str] = {}
    for row in report["results"]:
        if row["stage"] != "text_to_sql" or row["model"] != "qwen3.5:cloud":
            continue
        sid = row["sample_id"]
        if sid not in {f"sql_{i:03d}" for i in range(1, 6)}:
            continue
        old.setdefault(sid, []).append(float(row.get("judge_score_0_to_10") or 0))
        model_sql[sid] = row.get("raw_response", "")

    print("sql_001-005 execution sanity (reference self-score + qwen model vs reference)\n")
    for i in range(1, 6):
        sid = f"sql_{i:03d}"
        ref = by_id[sid]["reference_answer"]
        self_score = score_sql_execution(ref, ref)
        model_score = score_sql_execution(model_sql.get(sid, ""), ref)
        avg_old = sum(old.get(sid, [0])) / max(len(old.get(sid, [])), 1)
        print(
            f"{sid}: ref_self={self_score['judge_score_0_to_10']} | "
            f"qwen_exec={model_score['judge_score_0_to_10']} ({model_score['judge_reasoning'][:60]}) | "
            f"old_judge_avg={avg_old:.1f}"
        )


if __name__ == "__main__":
    main()
