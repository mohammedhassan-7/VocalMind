#!/usr/bin/env python3
"""Bucket GT failures from overnight checkpoints for prompt tuning."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from ground_truth_scorer import (
    extract_emotion_prediction,
    extract_nli_prediction,
    parse_emotion_ref,
    parse_json_object,
    parse_nli_ref,
    score_observation,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "infra/benchmarks/reports/overnight_20260614"
GT_PATH = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"

STAGE_CONFIG = {
    "emotion_shift": {
        "checkpoint": "emotion_shift_v2.checkpoint.jsonl",
        "gt_key": "emotion_shift",
        "winner": "kimi-k2.5:cloud",
    },
    "nli_policy": {
        "checkpoint": "nli_policy.checkpoint.jsonl",
        "gt_key": "nli_policy",
        "winner": "ministral-3:8b",
    },
}


def dedupe_checkpoint(stage: str, fname: str) -> list[dict]:
    by: dict[tuple[str, str], dict] = {}
    path = REPORT_DIR / fname
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("stage") != stage:
            continue
        by[(row["model"], row["sample_id"])] = row
    return list(by.values())


def analyze_stage(stage: str, model: str | None = None) -> dict:
    cfg = STAGE_CONFIG[stage]
    model = model or cfg["winner"]
    gt_data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    gt_idx = {x["sample_id"]: x for x in gt_data[cfg["gt_key"]]}
    rows = [r for r in dedupe_checkpoint(stage, cfg["checkpoint"]) if r["model"] == model]

    buckets: Counter[str] = Counter()
    confusion: Counter[tuple[str, str]] = Counter()
    examples: dict[tuple[str, str], list[str]] = defaultdict(list)

    for row in rows:
        ref = gt_idx[row["sample_id"]]
        raw = row.get("raw_response", "")
        sr = score_observation(stage, raw, ref, row)
        buckets[sr.match_type] += 1

        if sr.match_type == "exact":
            continue

        if stage == "emotion_shift":
            ref_label, _ = parse_emotion_ref(ref)
            data = parse_json_object(raw) or {}
            pred, _, _ = extract_emotion_prediction(data)
            pred_s = pred or "NONE"
        else:
            ref_label = parse_nli_ref(ref)
            data = parse_json_object(raw) or {}
            pred = extract_nli_prediction(data, raw)
            pred_s = pred or "NONE"

        key = (ref_label, pred_s)
        confusion[key] += 1
        if len(examples[key]) < 3:
            examples[key].append(row["sample_id"])

    return {
        "stage": stage,
        "model": model,
        "n": len(rows),
        "buckets": dict(buckets),
        "confusion": [(k, v, examples[k]) for k, v in confusion.most_common()],
    }


def write_report(results: list[dict], out: Path) -> None:
    lines = ["# Stage failure analysis", ""]
    for r in results:
        exact = r["buckets"].get("exact", 0)
        n = r["n"]
        lines.extend([
            f"## {r['stage']} — `{r['model']}` (n={n})",
            "",
            f"- **Exact:** {exact}/{n} ({100*exact/n:.1f}%)",
            f"- **Partial:** {r['buckets'].get('partial', 0)}",
            f"- **No match:** {r['buckets'].get('no_match', 0)}",
            f"- **Unparseable:** {r['buckets'].get('unparseable', 0)}",
            "",
            "| GT | Predicted | Count | Example IDs |",
            "|---|---|---:|---|",
        ])
        for (gt, pred), count, sids in r["confusion"][:15]:
            lines.append(f"| {gt} | {pred} | {count} | {', '.join(sids)} |")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=REPORT_DIR / "FAILURE_ANALYSIS_v7.md")
    args = parser.parse_args()

    results = [analyze_stage(s) for s in STAGE_CONFIG]
    write_report(results, args.out)

    for r in results:
        exact = r["buckets"].get("exact", 0)
        print(f"{r['stage']}: {exact}/{r['n']} exact ({100*exact/r['n']:.1f}%)")


if __name__ == "__main__":
    main()
