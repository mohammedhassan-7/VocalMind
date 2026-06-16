#!/usr/bin/env python3
"""Validate PA fuzzy scorer on 20-sample validation set + optional full re-score."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from diagnose_pa_validation import classify_sample, _extract_pred_keys, _ref_missing
from ground_truth_scorer import (
    PA_FUZZY_MATCH_LOG,
    clear_pa_fuzzy_match_log,
    parse_json_object,
    score_process_adherence,
)

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "infra/benchmarks/reports/overnight_20260614/_validate_process_adherence.json"
OLD_GT = ROOT / "infra/benchmarks/reports/overnight_20260614/process_adherence_groundtruth.json"
GT_PATH = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"
OUT = ROOT / "infra/benchmarks/reports/overnight_20260614/PA_FUZZY_VALIDATION.md"

V51_F1 = {
    "kimi-k2.6:cloud": 0.508,
    "kimi-k2.5:cloud": 0.443,
    "qwen3.5:cloud": 0.421,
    "ministral-3:8b": 0.192,
    "ministral-3:14b": 0.138,
}
V51_EXACT = {
    "kimi-k2.6:cloud": 0.35,
    "kimi-k2.5:cloud": 0.33,
    "qwen3.5:cloud": 0.31,
    "ministral-3:8b": 0.06,
    "ministral-3:14b": 0.03,
}
BASELINE_VAL_F1 = 0.450  # validation n=20 pre-fix


def score_validation() -> tuple[float, list[dict], list[dict]]:
    gt = {s["sample_id"]: s for s in json.loads(GT_PATH.read_text(encoding="utf-8"))["process_adherence"]}
    old_rows = {
        r["sample_id"]: r
        for r in json.loads(OLD_GT.read_text(encoding="utf-8"))["results"]
        if r["model"] == "kimi-k2.6:cloud"
    }
    new_rows = {
        r["sample_id"]: r
        for r in json.loads(VALIDATE.read_text(encoding="utf-8"))["results"]
        if r["model"] == "kimi-k2.6:cloud"
    }

    clear_pa_fuzzy_match_log()
    per_sample: list[dict] = []
    closer_rows: list[dict] = []

    for sid in sorted(new_rows.keys()):
        new_row = new_rows[sid]
        old_row = old_rows.get(sid)
        ref = gt[sid]
        ref_missing = _ref_missing(ref)

        new_raw = new_row.get("raw_response", "")
        old_raw = old_row.get("raw_response", "") if old_row else ""
        new_data = parse_json_object(new_raw)
        old_data = parse_json_object(old_raw) if old_row else None

        old_sr = score_process_adherence(old_raw, ref) if old_row else None
        new_sr = score_process_adherence(new_raw, ref)

        old_f1 = old_sr.f1 if old_sr else 0.0
        new_keys = _extract_pred_keys(new_raw, new_data)
        old_keys = _extract_pred_keys(old_raw, old_data) if old_row else []
        cat = classify_sample(
            ref_missing,
            old_sr or new_sr,
            new_sr,
            old_keys,
            new_keys,
            old_raw,
            new_raw,
        )

        entry = {
            "sample_id": sid,
            "category": cat,
            "old_f1": old_f1,
            "new_f1": new_sr.f1,
            "delta": (new_sr.f1 or 0) - (old_f1 or 0),
            "ref_missing": list(ref_missing),
            "new_keys": new_keys,
        }
        per_sample.append(entry)
        if cat == "CLOSER":
            closer_rows.append(entry)

    mean_f1 = sum(e["new_f1"] or 0 for e in per_sample) / len(per_sample)
    return mean_f1, per_sample, closer_rows


def check_overmatching() -> list[dict]:
    """Flag borderline fuzzy matches (0.85-0.92) for manual review."""
    flags = []
    for m in PA_FUZZY_MATCH_LOG:
        sim = float(m["similarity"])
        if 0.85 <= sim <= 0.92:
            flags.append(dict(m))
    return flags


def main() -> None:
    mean_f1, per_sample, closer_rows = score_validation()
    overmatch = check_overmatching()

    lines = [
        "# PA Fuzzy Scorer Validation",
        "",
        "## Part 2 — 20-sample re-score (kimi-k2.6 validation set)",
        "",
        f"- Fuzzy threshold: **0.85**",
        f"- Mean F1: **{BASELINE_VAL_F1:.3f} → {mean_f1:.3f}**",
        f"- Fuzzy matches logged: **{len(PA_FUZZY_MATCH_LOG)}**",
        "",
        "## Part 3 — CLOSER samples (11)",
        "",
        "| sample | model_key(s) | fuzzy match | sim | old F1 | new F1 | Δ |",
        "|---|---|---|---:|---:|---:|---:|",
    ]

    for e in closer_rows:
        sid = e["sample_id"]
        keys = ", ".join(f"`{k}`" for k in e["new_keys"][:4])
        matches = [m for m in PA_FUZZY_MATCH_LOG if m["model_key"] in e["new_keys"]]
        if matches:
            mm = matches[0]
            match_str = f"`{mm['model_key']}`→`{mm['matched_key']}`"
            sim = mm["similarity"]
        else:
            match_str = "(exact or ref-parse fix)"
            sim = "—"
        lines.append(
            f"| {sid} | {keys} | {match_str} | {sim} | {e['old_f1']:.2f} | {e['new_f1']:.2f} | {e['delta']:+.2f} |"
        )

    lines.extend(["", "## Over-matching review (similarity 0.85–0.92)", ""])
    if overmatch:
        lines.append("**Borderline matches found — review for semantic correctness:**")
        for m in overmatch:
            lines.append(
                f"- `{m['model_key']}` → `{m['matched_key']}` ({m['matched_label']}) sim={m['similarity']}"
            )
        lines.append("")
        lines.append("**Over-matching found:** review required (see above)")
    else:
        lines.append("**Over-matching found:** no — all fuzzy matches were exact or >0.92")

    recommend_full = mean_f1 >= 0.48 or (mean_f1 - BASELINE_VAL_F1) >= 0.08
    lines.extend(
        [
            "",
            f"**Recommend full re-score (765 obs):** {'yes' if recommend_full else 'no'}",
            "",
        ]
    )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Mean F1: {BASELINE_VAL_F1:.3f} -> {mean_f1:.3f}")
    print(f"Recommend full re-score: {recommend_full}")

    if recommend_full:
        subprocess.run(
            [sys.executable, str(ROOT / "infra/scripts/rescore_ground_truth_benchmark.py")],
            cwd=str(ROOT),
            check=True,
        )
        # summarize from new groundtruth
        pa_gt = json.loads(
            (ROOT / "infra/benchmarks/reports/overnight_20260614/process_adherence_groundtruth.json").read_text(
                encoding="utf-8"
            )
        )["summary"]
        lines.extend(["", "## Part 4 — Full PA re-score (765 obs)", ""])
        lines.append("| Model | v5.1 F1 | fuzzy F1 | v5.1 exact% | fuzzy exact% |")
        lines.append("|---|---:|---:|---:|---:|")
        best_m, best_f1 = "", 0.0
        for model in sorted(pa_gt, key=lambda m: pa_gt[m].get("gt_f1_avg", 0), reverse=True):
            f1 = pa_gt[model].get("gt_f1_avg", 0)
            ex = pa_gt[model].get("exact_match_rate", 0)
            lines.append(
                f"| {model} | {V51_F1.get(model, 0):.3f} | {f1:.3f} | "
                f"{V51_EXACT.get(model, 0):.0%} | {ex:.0%} |"
            )
            if f1 > best_f1:
                best_m, best_f1 = model, f1
        lines.extend(["", f"**New PA winner:** `{best_m}` — F1={best_f1:.3f}", ""])
        OUT.write_text("\n".join(lines), encoding="utf-8")
        print(f"Full re-score done. Winner: {best_m} F1={best_f1:.3f}")


if __name__ == "__main__":
    main()
