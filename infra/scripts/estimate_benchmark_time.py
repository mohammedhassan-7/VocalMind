#!/usr/bin/env python3
"""Estimate overnight benchmark time with per-stage repeat counts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"
TRIAGE = ROOT / "infra" / "benchmarks" / "model_triage_v1.json"
SUBSET_REPORT = ROOT / "infra" / "benchmarks" / "reports" / "benchmark_subset_20260613_1648.json"
PARALLEL_SPEEDUP = 2.5
NOISY_LATENCY_FACTOR = 1.15
BUDGET_HOURS = 10.0


def _avg_latency_by_stage(report_path: Path) -> dict[str, float]:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    buckets: dict[str, list[float]] = {}
    for row in data.get("results", []):
        buckets.setdefault(row["stage"], []).append(float(row.get("total_latency_ms", 0)))
    return {s: sum(v) / len(v) / 1000 for s, v in buckets.items() if v}


def _serial_hours(repeats: dict[str, int], triage: dict, gt: dict, lat: dict[str, float]) -> float:
    total = 0.0
    for stage, models in triage["stage_models"].items():
        samples = gt.get(stage, [])
        if not isinstance(samples, list):
            continue
        n_clean = sum(1 for s in samples if s.get("tier", "clean") == "clean")
        n_noisy = len(samples) - n_clean
        base = lat.get(stage, 8.0)
        per_sample = n_clean * base + n_noisy * base * NOISY_LATENCY_FACTOR
        total += len(models) * per_sample * repeats.get(stage, 1)
    return total / 3600


def _apply_fallback(
    repeats: dict[str, int],
    triage: dict,
    gt: dict,
    lat: dict[str, float],
) -> list[str]:
    steps: list[str] = []
    while _serial_hours(repeats, triage, gt, lat) / PARALLEL_SPEEDUP > BUDGET_HOURS:
        if repeats.get("rag_judge", 1) > 1 or repeats.get("fast_classification", 1) > 1:
            if repeats.get("rag_judge", 1) > 1:
                repeats["rag_judge"] = 1
            if repeats.get("fast_classification", 1) > 1:
                repeats["fast_classification"] = 1
            steps.append("A: rag_judge + fast_classification -> repeats=1")
            continue
        if repeats.get("text_to_sql", 1) > 1:
            repeats["text_to_sql"] = 1
            steps.append("B: text_to_sql -> repeats=1")
            continue
        if repeats.get("emotion_shift", 1) > 1:
            repeats["emotion_shift"] = 1
            steps.append("C: emotion_shift -> repeats=1")
            continue
        if repeats.get("process_adherence", 1) > 1:
            repeats["process_adherence"] = 1
            steps.append("D: process_adherence -> repeats=1")
            continue
        break
    return steps


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", default="", help="Write repeat plan JSON for run_overnight.ps1")
    args = parser.parse_args()

    triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
    gt = json.loads(V2.read_text(encoding="utf-8"))
    lat = _avg_latency_by_stage(SUBSET_REPORT)

    repeats = {s: 2 for s in triage["stage_models"]}
    initial_h = _serial_hours(repeats, triage, gt, lat) / PARALLEL_SPEEDUP
    steps = _apply_fallback(repeats, triage, gt, lat)
    final_h = _serial_hours(repeats, triage, gt, lat) / PARALLEL_SPEEDUP

    print(f"Initial (repeats=2 all stages): {initial_h:.2f} h parallel est.")
    print(f"Fallback steps applied: {steps or 'none'}")
    print("Final per-stage repeats:")
    for s in triage["stage_models"]:
        print(f"  {s}={repeats[s]}")
    print(f"Final total estimate: {final_h:.2f} h")

    plan = {"repeats": repeats, "initial_hours": initial_h, "final_hours": final_h, "fallback_steps": steps}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(plan, indent=2), encoding="utf-8")
        print(f"Wrote plan to {args.json_out}")
