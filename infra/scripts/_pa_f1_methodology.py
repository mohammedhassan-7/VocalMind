#!/usr/bin/env python3
"""Prompt 21: PA mean-F1 methodology — both conventions side by side."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GT_PATH = ROOT / "infra/benchmarks/reports/overnight_20260614/process_adherence_groundtruth.json"


def is_extraction_error(row: dict) -> bool:
    return str(row.get("gt_details", "")).startswith("extraction_error")


def f1_value(row: dict) -> float | None:
    v = row.get("gt_f1")
    return float(v) if v is not None else None


def aggregate(rows: list[dict]) -> dict:
    n = len(rows)
    errors = sum(1 for r in rows if is_extraction_error(r))
    valid_f1s = [f1_value(r) for r in rows if f1_value(r) is not None]
    sum_valid = sum(valid_f1s)
    # Convention (a): exclude errors from denominator — current rescore script
    f1_excl = sum_valid / len(valid_f1s) if valid_f1s else 0.0
    # Convention (b): errors count as F1=0 over full n
    f1_incl = sum_valid / n if n else 0.0
    return {
        "n": n,
        "extraction_errors": errors,
        "valid_scored": len(valid_f1s),
        "sum_f1_valid": sum_valid,
        "F1_excl_errors": f1_excl,
        "F1_incl_errors_as_0": f1_incl,
    }


def main() -> None:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    by_model: dict[str, list[dict]] = defaultdict(list)
    for row in data["results"]:
        by_model[row["model"]].append(row)

    print("=== How current 'mean F1' is computed (rescore_ground_truth_benchmark.aggregate_by_model) ===")
    print(
        "Lines 124-126: f1s = [r['gt_f1'] for r in rs if r.get('gt_f1') is not None]; "
        "gt_f1_avg = sum(f1s)/len(f1s)"
    )
    print(
        "=> extraction_error rows return ScoreResult with f1=None => EXCLUDED from mean entirely (convention a).\n"
    )

    stats = {m: aggregate(rs) for m, rs in by_model.items()}

    def print_table(sort_key: str, title: str) -> list[str]:
        print(f"=== {title} (sorted by {sort_key}) ===")
        print(
            f"{'model':<22} | {'n':>4} | {'errors':>6} | {'valid':>5} | "
            f"{'F1_excl':>8} | {'F1_incl0':>8}"
        )
        print("-" * 72)
        ranked = sorted(stats, key=lambda m: stats[m][sort_key], reverse=True)
        for m in ranked:
            s = stats[m]
            print(
                f"{m:<22} | {s['n']:4d} | {s['extraction_errors']:6d} | {s['valid_scored']:5d} | "
                f"{s['F1_excl_errors']:8.3f} | {s['F1_incl_errors_as_0']:8.3f}"
            )
        print(f"Winner: {ranked[0]}\n")
        return ranked

    excl_rank = print_table("F1_excl_errors", "Convention (a): exclude extraction errors")
    incl_rank = print_table("F1_incl_errors_as_0", "Convention (b): errors_as_0 over full n")

    print("=== Side-by-side rankings ===")
    print(f"{'model':<22} | rank_excl | rank_incl")
    for m in sorted(stats):
        print(
            f"{m:<22} | {excl_rank.index(m)+1:9d} | {incl_rank.index(m)+1:9d}"
        )

    print("\n=== qwen3.5 vs kimi-k2.6 breakdown ===")
    for m in ("qwen3.5:cloud", "kimi-k2.6:cloud", "ministral-3:8b"):
        s = stats[m]
        print(f"\n{m}:")
        print(f"  n={s['n']}, extraction_errors={s['extraction_errors']}, valid_scored={s['valid_scored']}")
        print(f"  sum F1 over valid entries = {s['sum_f1_valid']:.3f}")
        print(f"  F1_excl_errors (mean over {s['valid_scored']} valid) = {s['F1_excl_errors']:.3f}")
        print(f"  F1_incl_errors_as_0 (mean over {s['n']} all)     = {s['F1_incl_errors_as_0']:.3f}")

    print("\n=== RECOMMENDATION ===")
    print("Use F1_incl_errors_as_0 for production routing.")
    print(f"Winner under errors_as_0: {incl_rank[0]} (F1={stats[incl_rank[0]]['F1_incl_errors_as_0']:.3f})")


if __name__ == "__main__":
    main()
