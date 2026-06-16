#!/usr/bin/env python3
"""Spot-check PA calibration outliers under new GT F1 extractor."""
from __future__ import annotations

import json
from pathlib import Path

from ground_truth_scorer import extract_pa_predicted_missing, parse_json_object, parse_pa_ref_missing, score_process_adherence

ROOT = Path(__file__).resolve().parents[2]
CK = ROOT / "infra/benchmarks/reports/overnight_20260614/process_adherence.checkpoint.jsonl"
CAL = ROOT / "infra/benchmarks/calibration/judge_calibration_set.json"
GT_PATH = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"

TARGETS = {"pa_075", "pa_052", "pa_032"}


def main() -> None:
    cal = {e["sample_id"]: e for e in json.loads(CAL.read_text(encoding="utf-8"))["samples"] if e["stage"] == "process_adherence"}
    gt = {s["sample_id"]: s for s in json.loads(GT_PATH.read_text(encoding="utf-8"))["process_adherence"]}

    ck_rows: dict[tuple[str, str], dict] = {}
    for line in CK.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        ck_rows[(e["model"], e["sample_id"])] = e

    for sid in sorted(TARGETS):
        cal_e = cal.get(sid)
        if not cal_e:
            print(f"\n=== {sid}: not in calibration set ===")
            continue
        # calibration entries use model from benchmark - find matching checkpoint row
        model = None
        for (m, s), row in ck_rows.items():
            if s == sid:
                model = m
                break
        ref = gt[sid]
        ref_missing = parse_pa_ref_missing(ref)
        row = ck_rows.get((model, sid)) if model else None
        raw = cal_e.get("model_output") or (row or {}).get("raw_response", "")
        data = parse_json_object(raw)
        pred, err = extract_pa_predicted_missing(raw, data)
        sr = score_process_adherence(raw, ref)
        print(f"\n=== {sid} | model={model} | label={cal_e.get('label')} ===")
        print(f"reference missing steps: {sorted(ref_missing)}")
        print(f"judge_score_0_to_10: {cal_e.get('judge_score_0_to_10')} | human_score: {cal_e.get('human_score')}")
        print(f"new GT F1: {sr.f1} | precision={sr.precision} recall={sr.recall} | {sr.details}")
        print(f"extracted pred missing: {sorted(pred or [])} | extract_err={err}")
        if isinstance(data, dict):
            print(f"raw_response top-level keys: {list(data.keys())[:8]}")


if __name__ == "__main__":
    main()
