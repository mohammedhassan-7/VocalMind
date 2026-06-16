#!/usr/bin/env python3
"""Aggregate overnight stage JSON files into FULL_REPORT_v3.md (+ PDF)."""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRIAGE = ROOT / "infra" / "benchmarks" / "model_triage_v1.json"
GT_V2 = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"
CAL_MD = ROOT / "infra" / "benchmarks" / "calibration" / "judge_calibration_set.md"

STAGES = [
    "emotion_shift",
    "process_adherence",
    "nli_policy",
    "rag_judge",
    "text_to_sql",
    "fast_classification",
]


def _percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * (p / 100.0)
    f = int(math.floor(k))
    c = min(f + 1, len(s) - 1)
    return s[f] if f == c else s[f] + (s[c] - s[f]) * (k - f)


def _dedupe_results(rows: list[dict]) -> list[dict]:
    """Keep last observation per (stage, model, sample_id, repeat)."""
    by_key: dict[tuple, dict] = {}
    for r in rows:
        key = (r.get("stage"), r.get("model"), r.get("sample_id"), int(r.get("repeat", 0)))
        by_key[key] = r
    return list(by_key.values())


def _load_stage_rows(report_dir: Path, stage: str) -> list[dict]:
    path = report_dir / f"{stage}.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return _dedupe_results([r for r in data.get("results", []) if r.get("stage") == stage])
    ckpt = report_dir / f"{stage}.checkpoint.jsonl"
    if not ckpt.exists():
        return []
    rows: list[dict] = []
    by_key: dict[tuple, dict] = {}
    for line in ckpt.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("stage") != stage:
            continue
        key = (r.get("stage"), r.get("model"), r.get("sample_id"), int(r.get("repeat", 0)))
        by_key[key] = r
    return list(by_key.values())


def _stage_status(stage: str, path: Path, report_dir: Path, expected_samples: int, repeats: int, n_models: int) -> dict:
    rows = _load_stage_rows(report_dir, stage)
    done = len(rows)
    expected = expected_samples * n_models * repeats
    if done >= expected:
        status = "complete"
    elif done > 0:
        status = f"partial ({done}/{expected})"
    else:
        status = "missing"
    return {"stage": stage, "status": status, "done": done, "expected": expected, "repeats": repeats}


def _model_stats(rows: list[dict]) -> dict[str, dict]:
    by_model: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)
    out = {}
    for model, mr in by_model.items():
        scores = [float(r["judge_score_0_to_10"]) for r in mr if r.get("judge_score_0_to_10") is not None]
        lats = [float(r.get("total_latency_ms", 0)) for r in mr]
        repeat_groups: dict[str, list[float]] = defaultdict(list)
        for r in mr:
            if r.get("judge_score_0_to_10") is not None:
                repeat_groups[r["sample_id"]].append(float(r["judge_score_0_to_10"]))
        stdevs = []
        for vals in repeat_groups.values():
            if len(vals) > 1:
                m = sum(vals) / len(vals)
                stdevs.append(math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals)))
        out[model] = {
            "avg_score": sum(scores) / len(scores) if scores else 0.0,
            "score_stdev_across_repeats": sum(stdevs) / len(stdevs) if stdevs else 0.0,
            "p50_ms": _percentile(lats, 50),
            "p95_ms": _percentile(lats, 95),
            "p99_ms": _percentile(lats, 99),
            "n": len(mr),
        }
    return out


def _calibration_status() -> str:
    if not CAL_MD.exists():
        return "pending — judge_calibration_set.md not found"
    text = CAL_MD.read_text(encoding="utf-8")
    filled = len(re.findall(r"\*\*Your score \(0-10\):\*\*\s*[0-9.]+", text))
    total = len(re.findall(r"\*\*Your score \(0-10\):\*\*", text))
    if filled >= total and total > 0:
        return f"filled ({filled}/{total}) — run compute_judge_calibration.py"
    return f"pending human scoring ({filled}/{total} filled)"


def build_report(report_dir: Path) -> str:
    triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
    gt = json.loads(GT_V2.read_text(encoding="utf-8"))
    plan_path = report_dir / "repeat_plan.json"
    repeats = json.loads(plan_path.read_text(encoding="utf-8"))["repeats"] if plan_path.exists() else {s: 1 for s in STAGES}

    lines = [
        "# VocalMind Ollama Cloud Benchmark — FULL_REPORT_v3",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source directory:** `{report_dir.name}`",
        "",
        "## Run status",
        "",
        "| Stage | Status | Observations | Expected | Repeats |",
        "|---|---|---|---|---|",
    ]

    all_rows: list[dict] = []
    for stage in STAGES:
        stage_file = report_dir / f"{stage}.json"
        expected_n = len(gt.get(stage, []))
        n_models = len(triage["stage_models"][stage])
        rep = repeats.get(stage, 1)
        st = _stage_status(stage, stage_file, report_dir, expected_n, rep, n_models)
        lines.append(f"| {stage} | {st['status']} | {st['done']} | {st['expected']} | {rep} |")
        all_rows.extend(_load_stage_rows(report_dir, stage))

    all_rows = _dedupe_results(all_rows)
    lines.extend(["## Judge calibration", "", _calibration_status(), ""])

    lines.extend(["", "## Per-stage quality (v2 pool)", ""])
    for stage in STAGES:
        rows = [r for r in all_rows if r.get("stage") == stage]
        if not rows:
            lines.append(f"### {stage}\n\n_No data._\n")
            continue
        lines.append(f"### {stage}")
        if stage == "text_to_sql":
            lines.append("\n> **Note:** Scores from DB execution comparison (seeded BENCHMARK_ORG), not LLM judge.\n")
        stats = _model_stats(rows)
        lines.append("| Model | Avg score | Repeat stdev | p50 ms | p95 ms | p99 ms | n |")
        lines.append("|---|---|---|---|---|---|---|")
        for model, s in sorted(stats.items(), key=lambda x: -x[1]["avg_score"]):
            lines.append(
                f"| {model} | {s['avg_score']:.2f} | {s['score_stdev_across_repeats']:.2f} | "
                f"{s['p50_ms']:.0f} | {s['p95_ms']:.0f} | {s['p99_ms']:.0f} | {s['n']} |"
            )
        lines.append("")

    lines.extend(["## Stability analysis (repeats >= 2)", ""])
    for stage in STAGES:
        if repeats.get(stage, 1) < 2:
            continue
        rows = [r for r in all_rows if r.get("stage") == stage]
        stats = _model_stats(rows)
        flagged = [m for m, s in stats.items() if s["score_stdev_across_repeats"] > 1.5]
        lines.append(f"- **{stage}**: flagged high repeat variance: {', '.join(flagged) if flagged else 'none'}")
    lines.append("")

    lines.extend([
        "## Config recommendation",
        "",
        "Review per-stage tables above. Default production stack unless larger-n results contradict:",
        "- Heavy: `kimi-k2.6:cloud`",
        "- Fast: `ministral-3:8b`",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", required=True)
    args = parser.parse_args()
    report_dir = Path(args.report_dir)
    md_path = report_dir / "FULL_REPORT_v3.md"
    md_text = build_report(report_dir)
    md_text = md_text.replace("\u2014", "-").replace("\u2013", "-")
    md_path.write_text(md_text, encoding="utf-8")
    pdf_path = report_dir / "FULL_REPORT_v3.pdf"
    try:
        subprocess.run(
            ["pandoc", str(md_path), "-o", str(pdf_path), "--pdf-engine=wkhtmltopdf"],
            check=True,
            capture_output=True,
        )
        print(f"Wrote {pdf_path}")
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"PDF skipped: {exc}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
