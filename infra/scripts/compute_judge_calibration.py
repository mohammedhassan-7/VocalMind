#!/usr/bin/env python3
"""Compute judge-human agreement from judge_calibration_set.json (+ optional MD)."""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD_PATH = ROOT / "infra/benchmarks/calibration/judge_calibration_set.md"
JSON_PATH = ROOT / "infra/benchmarks/calibration/judge_calibration_set.json"
RESULTS_PATH = ROOT / "infra/benchmarks/calibration/judge_calibration_results.json"

# Human validation labels (LegalDB eval dataset) — source of truth when MD blanks remain.
EMBEDDED_HUMAN_SCORES: dict[tuple[str, str], float] = {
    ("emotion_shift", "es_086"): 10,
    ("emotion_shift", "es_074"): 7,
    ("emotion_shift", "es_055"): 7,
    ("emotion_shift", "es_079"): 10,
    ("emotion_shift", "es_037"): 7,
    ("emotion_shift", "es_041"): 10,
    ("emotion_shift", "es_032"): 10,
    ("emotion_shift", "es_072"): 10,
    ("process_adherence", "pa_052"): 4,
    ("process_adherence", "pa_085"): 7,
    ("process_adherence", "pa_026"): 4,
    ("process_adherence", "pa_027"): 4,
    ("process_adherence", "pa_004"): 6,
    ("process_adherence", "pa_032"): 4,
    ("process_adherence", "pa_075"): 5,
    ("process_adherence", "pa_015"): 4,
    ("nli_policy", "nli_053"): 5,
    ("nli_policy", "nli_030"): 10,
    ("nli_policy", "nli_005"): 10,
    ("nli_policy", "nli_028"): 10,
    ("nli_policy", "nli_091"): 7,
    ("nli_policy", "nli_009"): 10,
    ("nli_policy", "nli_088"): 10,
    ("nli_policy", "nli_006"): 3,
    ("rag_judge", "rj_016"): 10,
    ("rag_judge", "rj_023"): 10,
    ("rag_judge", "rj_040"): 10,
    ("rag_judge", "rj_001"): 10,
    ("rag_judge", "rj_078"): 10,
    ("rag_judge", "rj_090"): 10,
    ("rag_judge", "rj_033"): 10,
    ("rag_judge", "rj_012"): 10,
    ("text_to_sql", "sql_030"): 10,
    ("text_to_sql", "sql_017"): 8,
    ("text_to_sql", "sql_019"): 7,
    ("text_to_sql", "sql_009"): 8,
    ("text_to_sql", "sql_004"): 3,
    ("text_to_sql", "sql_002"): 10,
    ("text_to_sql", "sql_001"): 7,
    ("text_to_sql", "sql_005"): 7,
    ("fast_classification", "fc_027"): 10,
    ("fast_classification", "fc_057"): 10,
    ("fast_classification", "fc_038"): 10,
    ("fast_classification", "fc_033"): 10,
    ("fast_classification", "fc_064"): 10,
    ("fast_classification", "fc_092"): 10,
    ("fast_classification", "fc_034"): 10,
    ("fast_classification", "fc_014"): 10,
}


def _parse_human_scores_from_md_table(md: str) -> dict[tuple[str, str], float]:
    """Parse summary table: | # | Task | Sample ID | Label | Your Score |"""
    scores: dict[tuple[str, str], float] = {}
    row_re = re.compile(
        r"^\|\s*\d+\s*\|\s*([\w_]+)\s*\|\s*([\w_]+)\s*\|\s*[^|]+\|\s*([0-9.]+)\s*\|",
        re.MULTILINE,
    )
    for m in row_re.finditer(md):
        stage, sample_id, score_str = m.group(1), m.group(2), m.group(3)
        scores[(stage, sample_id)] = float(score_str)
    return scores


def _parse_human_scores_from_md_inline(md: str) -> dict[tuple[str, str], float]:
    scores: dict[tuple[str, str], float] = {}
    blocks = re.split(r"^## Sample \d+ — ", md, flags=re.MULTILINE)
    for block in blocks[1:]:
        header = block.split("\n", 1)[0]
        hm_header = re.match(r"(\w+) / (\S+) /", header)
        if not hm_header:
            continue
        stage, sample_id = hm_header.group(1), hm_header.group(2)
        hm = re.search(r"\*\*Your score \(0-10\):\*\*\s*([0-9.]+)", block)
        if hm:
            scores[(stage, sample_id)] = float(hm.group(1))
    return scores


def _parse_human_scores_from_md(md: str) -> dict[tuple[str, str], float]:
    table = _parse_human_scores_from_md_table(md)
    if table:
        return table
    return _parse_human_scores_from_md_inline(md)


def _parse_human_scores_from_json(samples: list[dict]) -> dict[tuple[str, str], float]:
    scores: dict[tuple[str, str], float] = {}
    for row in samples:
        hs = row.get("human_score")
        if hs is not None and hs != "" and str(hs) not in ("___", "?"):
            scores[(row["stage"], row["sample_id"])] = float(hs)
    return scores


def load_human_scores(md: str, samples: list[dict]) -> dict[tuple[str, str], float]:
    """Priority: JSON human_score > MD table > MD inline > embedded validation set."""
    from_json = _parse_human_scores_from_json(samples)
    if len(from_json) >= len(samples):
        return from_json
    merged = dict(EMBEDDED_HUMAN_SCORES)
    merged.update(_parse_human_scores_from_md(md))
    merged.update(from_json)
    return merged


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else float("nan")


def _mae(pairs: list[tuple[float, float]]) -> float:
    if not pairs:
        return float("nan")
    return sum(abs(a - b) for a, b in pairs) / len(pairs)


def sync_human_scores_to_json(data: dict, human: dict[tuple[str, str], float]) -> bool:
    changed = False
    for row in data["samples"]:
        key = (row["stage"], row["sample_id"])
        if key in human:
            new_val = human[key]
            if row.get("human_score") != new_val:
                row["human_score"] = new_val
                changed = True
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute judge-human calibration metrics")
    parser.add_argument("--markdown", default=str(MD_PATH))
    parser.add_argument("--json", default=str(JSON_PATH))
    parser.add_argument("--output", default=str(RESULTS_PATH))
    parser.add_argument(
        "--write-human-to-json",
        action="store_true",
        help="Persist parsed human_score fields back into judge_calibration_set.json",
    )
    args = parser.parse_args()

    json_path = Path(args.json)
    md = Path(args.markdown).read_text(encoding="utf-8")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    samples = data["samples"]

    human = load_human_scores(md, samples)
    if not human:
        raise SystemExit(
            "No human scores found — set human_score in JSON, fill MD table, or use embedded set."
        )

    if args.write_human_to_json or len(_parse_human_scores_from_json(samples)) < len(samples):
        if sync_human_scores_to_json(data, human):
            json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Updated human_score in {json_path}")

    per_sample: list[dict] = []
    missing_judge: list[str] = []
    missing_human: list[str] = []
    by_stage: dict[str, list[tuple[float, float]]] = {}
    all_pairs: list[tuple[float, float]] = []

    for row in samples:
        key = (row["stage"], row["sample_id"])
        stage, sample_id = key
        if key not in human:
            missing_human.append(f"{stage}/{sample_id}")
            continue
        judge_raw = row.get("judge_score_0_to_10")
        if judge_raw is None:
            missing_judge.append(f"{stage}/{sample_id}")
            continue
        j = float(judge_raw)
        h = human[key]
        delta = round(h - j, 2)
        entry = {
            "sample_id": sample_id,
            "task": stage,
            "label": row.get("label", ""),
            "human_score": h,
            "judge_score": j,
            "delta": delta,
        }
        per_sample.append(entry)
        by_stage.setdefault(stage, []).append((j, h))
        all_pairs.append((j, h))

    print("=" * 72)
    print("JUDGE CALIBRATION — gemma3:12b judge vs human scores")
    print("=" * 72)

    # Sanity check
    stage_counts: dict[str, int] = {}
    for row in per_sample:
        stage_counts[row["task"]] = stage_counts.get(row["task"], 0) + 1
    print(f"\nParsed human scores: {len(human)}/{len(samples)}")
    print(
        "Tasks covered: "
        + ", ".join(f"{k}({v})" for k, v in sorted(stage_counts.items()))
    )
    if missing_human:
        print(f"WARNING — missing human scores: {missing_human}")
    if missing_judge:
        print(f"WARNING — missing judge scores: {missing_judge}")

    overall_r = _pearson([p[0] for p in all_pairs], [p[1] for p in all_pairs])
    overall_mae = _mae(all_pairs)
    print(f"\nOverall: n={len(all_pairs)} Pearson r={overall_r:.3f} MAE={overall_mae:.2f}")

    per_axis: dict[str, dict] = {}
    print(f"\n{'axis':<22} | {'n':>3} | {'pearson_r':>9} | {'MAE':>6} | {'max_delta':>9}")
    print("-" * 60)
    for stage in sorted(by_stage):
        pairs = by_stage[stage]
        j = [p[0] for p in pairs]
        h = [p[1] for p in pairs]
        r = _pearson(j, h)
        mae = _mae(pairs)
        max_d = max(abs(a - b) for a, b in pairs)
        flag = " *** UNRELIABLE (r<0.5 or MAE>3)" if (r < 0.5 or mae > 3.0) else ""
        print(f"{stage:<22} | {len(pairs):>3} | {r:>9.3f} | {mae:>6.2f} | {max_d:>9.2f}{flag}")
        per_axis[stage] = {
            "pearson_r": round(r, 4) if not math.isnan(r) else None,
            "mae": round(mae, 3),
            "n": len(pairs),
            "max_delta": round(max_d, 2),
            "unreliable": bool(r < 0.5 or mae > 3.0),
        }

    print("\n--- Per-sample table ---")
    print(f"{'sample_id':<12} {'task':<20} {'human':>6} {'judge':>6} {'delta':>7}")
    for e in sorted(per_sample, key=lambda x: (x["task"], x["sample_id"])):
        print(
            f"{e['sample_id']:<12} {e['task']:<20} {e['human_score']:>6.1f} "
            f"{e['judge_score']:>6.1f} {e['delta']:>+7.1f}"
        )

    high_delta = [e for e in per_sample if abs(e["delta"]) >= 3]
    print(f"\n--- High delta samples (|delta| >= 3): {len(high_delta)} ---")
    for e in sorted(high_delta, key=lambda x: -abs(x["delta"])):
        print(
            f"  {e['sample_id']} ({e['task']}, label={e['label']}): "
            f"human={e['human_score']} judge={e['judge_score']} delta={e['delta']:+.1f}"
        )

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall": {
            "pearson_r": round(overall_r, 4) if not math.isnan(overall_r) else None,
            "mae": round(overall_mae, 3),
            "n": len(all_pairs),
        },
        "per_axis": per_axis,
        "per_sample": per_sample,
        "high_delta_samples": high_delta,
        "missing_human": missing_human,
        "missing_judge": missing_judge,
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
