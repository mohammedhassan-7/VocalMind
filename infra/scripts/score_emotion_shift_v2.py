#!/usr/bin/env python3
"""Score emotion_shift_v2.json and compare to v5.1 baselines."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from ground_truth_scorer import score_observation

ROOT = Path(__file__).resolve().parents[2]
V2_PATH = ROOT / "infra/benchmarks/reports/overnight_20260614/emotion_shift_v2.json"
GT_PATH = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"
OUT_PATH = ROOT / "infra/benchmarks/reports/overnight_20260614/EMOTION_SHIFT_V2_REPORT.md"

V51_BASELINE = {
    "kimi-k2.5:cloud": {"exact_all": 0.37, "parseable": 0.54, "exact_parseable": 0.68},
    "kimi-k2.6:cloud": {"exact_all": 0.24, "parseable": 0.33, "exact_parseable": 0.71},
    "ministral-3:14b": {"exact_all": 0.26, "parseable": 0.78, "exact_parseable": 0.34},
}


def aggregate(rows: list[dict]) -> dict[str, dict]:
    by_model: dict[str, list] = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)
    out = {}
    for model, rs in by_model.items():
        n = len(rs)
        exact = sum(1 for r in rs if r["match_type"] == "exact")
        unparse = sum(1 for r in rs if r["match_type"] == "unparseable")
        parseable = n - unparse
        scores = [r["gt_score"] for r in rs]
        out[model] = {
            "n": n,
            "exact_all": exact / n,
            "parseable": parseable / n,
            "exact_parseable": exact / parseable if parseable else 0,
            "gt_avg": sum(scores) / n,
        }
    return out


def pick_winner(metrics: dict[str, dict]) -> tuple[str, str]:
    # reliability-first if parseable gap > 10pp, else accuracy among parseable
    best = max(
        metrics,
        key=lambda m: (
            metrics[m]["parseable"],
            metrics[m]["exact_parseable"],
            metrics[m]["exact_all"],
        ),
    )
    m = metrics[best]
    kimi = metrics.get("kimi-k2.5:cloud", {})
    if (
        kimi.get("parseable", 0) >= 0.85
        and kimi.get("exact_parseable", 0) > m.get("exact_parseable", 0) + 0.10
    ):
        return "kimi-k2.5:cloud", (
            f"High parseable ({kimi['parseable']:.0%}) + best accuracy when parseable "
            f"({kimi['exact_parseable']:.0%})"
        )
    return best, (
        f"parseable={m['parseable']:.0%}, exact(parseable)={m['exact_parseable']:.0%}, "
        f"exact(all)={m['exact_all']:.0%}"
    )


def main() -> None:
    if not V2_PATH.exists():
        raise SystemExit(f"Missing {V2_PATH}")

    data = json.loads(V2_PATH.read_text(encoding="utf-8"))
    gt = {s["sample_id"]: s for s in json.loads(GT_PATH.read_text(encoding="utf-8"))["emotion_shift"]}
    scored = []
    for row in data.get("results", []):
        ref = gt.get(row["sample_id"])
        if not ref:
            continue
        sr = score_observation("emotion_shift", row.get("raw_response", ""), ref, row)
        scored.append({**row, "gt_score": sr.gt_score, "match_type": sr.match_type, "gt_details": sr.details})

    metrics = aggregate(scored)
    winner, reason = pick_winner(metrics)

    lines = [
        "# emotion_shift v2 Full Re-run Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source:** `emotion_shift_v2.json` ({data.get('generated_at', '')})",
        "**Prompt:** closed label set + JSON mode (prompt_constants.py)",
        "",
        "## Comparison vs v5.1",
        "",
        "| Model | v5.1 exact(all) | v2 exact(all) | v5.1 parseable% | v2 parseable% | v5.1 exact(parseable) | v2 exact(parseable) | GT avg |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model in ["kimi-k2.5:cloud", "kimi-k2.6:cloud", "ministral-3:14b"]:
        old = V51_BASELINE.get(model, {})
        new = metrics.get(model, {})
        if not new:
            continue
        lines.append(
            f"| {model} | {old.get('exact_all', 0):.0%} | {new['exact_all']:.0%} | "
            f"{old.get('parseable', 0):.0%} | {new['parseable']:.0%} | "
            f"{old.get('exact_parseable', 0):.0%} | {new['exact_parseable']:.0%} | {new['gt_avg']:.2f} |"
        )

    lines.extend(["", f"**New recommended winner:** `{winner}` — {reason}", ""])
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")

    out_gt = V2_PATH.with_name("emotion_shift_v2_groundtruth.json")
    out_gt.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "stage": "emotion_shift",
                "scoring_method": "ground_truth_comparison",
                "source": str(V2_PATH),
                "results": scored,
                "summary": metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {out_gt}")
    for model, m in metrics.items():
        print(f"{model}: exact_all={m['exact_all']:.0%} parseable={m['parseable']:.0%} exact_par={m['exact_parseable']:.0%}")


if __name__ == "__main__":
    main()
