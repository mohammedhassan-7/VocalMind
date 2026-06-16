#!/usr/bin/env python3
"""Re-score PA checkpoint entries with fixed GT F1 extractor (no API calls)."""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

from ground_truth_scorer import extract_pa_predicted_missing, parse_json_object, score_process_adherence

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "infra" / "benchmarks" / "reports" / "overnight_20260614"
CK = REPORT_DIR / "process_adherence.checkpoint.jsonl"
GT_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"


def load_gt() -> dict[str, dict]:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    return {s["sample_id"]: s for s in data["process_adherence"]}


def main() -> None:
    gt = load_gt()
    # last-write-wins per (model, sample_id)
    rows: dict[tuple[str, str], dict] = {}
    for line in CK.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        rows[(e["model"], e["sample_id"])] = e

    by_model: dict[str, list] = defaultdict(list)
    errors_by_model: dict[str, int] = defaultdict(int)

    for (model, sid), row in rows.items():
        ref = gt.get(sid)
        if not ref:
            continue
        raw = row.get("raw_response", "")
        sr = score_process_adherence(raw, ref)
        if sr.details.startswith("extraction_error"):
            errors_by_model[model] += 1
        by_model[model].append(sr)

    print(f"{'model':<22} | {'n':>4} | {'precision':>9} | {'recall':>7} | {'F1':>6} | {'extract_err':>12}")
    print("-" * 80)
    leaderboard = []
    for model in sorted(by_model):
        scores = by_model[model]
        n = len(scores)
        p = sum(s.precision or 0 for s in scores) / n
        r = sum(s.recall or 0 for s in scores) / n
        f1 = sum(s.f1 or 0 for s in scores) / n
        err = errors_by_model[model]
        print(f"{model:<22} | {n:4d} | {p:9.3f} | {r:7.3f} | {f1:6.3f} | {err:12d}")
        leaderboard.append((model, n, p, r, f1, err))

    best = max(leaderboard, key=lambda x: x[4])
    print(f"\nBest F1: {best[0]} ({best[4]:.3f})")


if __name__ == "__main__":
    main()
