#!/usr/bin/env python3
"""Build judge calibration set: ministral-3:8b outputs + gemma3:12b scores for human review."""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

from benchmark_ollama_cloud import STAGES, call_ollama_cloud, judge_response  # noqa: E402

GT_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth.json"
OUT_MD = ROOT / "infra" / "benchmarks" / "calibration" / "judge_calibration_set.md"
OUT_JSON = ROOT / "infra" / "benchmarks" / "calibration" / "judge_calibration_set.json"

CALIBRATION_MODEL = "ministral-3:8b"
JUDGE_MODEL = "gemma3:12b"
SAMPLES_PER_STAGE = 8


def _label_key(stage: str, sample: dict) -> str:
    if sample.get("_label"):
        return str(sample["_label"])
    if stage == "nli_policy":
        ref = sample.get("reference_answer", "")
        if "Verdict:" in ref:
            return ref.split("Verdict:")[1].split(".")[0].strip()
    if stage == "emotion_shift":
        crit = sample.get("scoring_criteria", "").lower()
        if "sarcasm" in crit:
            return "sarcasm"
        if "passive" in crit:
            return "passive_aggression"
        if "cross-modal" in crit:
            return "cross_modal"
        return "none"
    if stage == "fast_classification":
        ref = sample.get("reference_answer", "")
        if "topic:" in ref:
            return ref.split("topic:")[1].split(",")[0].strip()
    if stage == "process_adherence":
        missing = sample.get("_missing")
        if missing is not None:
            n = len(missing)
            return f"missing_{min(n, 3)}"
        return "missing_0" if "No missing" in sample.get("reference_answer", "") else "missing_unknown"
    if stage == "text_to_sql":
        return "hand" if sample["sample_id"] in {f"sql_{i:03d}" for i in range(1, 6)} else "generated"
    if stage == "rag_judge":
        return "compliant" if "Compliant" in sample.get("reference_answer", "") else "non_compliant"
    return "default"


def _pick_stratified(stage: str, samples: list[dict], rng: random.Random, n: int) -> list[dict]:
    by_label: dict[str, list[dict]] = defaultdict(list)
    for s in samples:
        if s.get("tier") == "noisy":
            continue
        by_label[_label_key(stage, s)].append(s)
    picked: list[dict] = []
    labels = sorted(by_label.keys())
    per = max(1, n // max(len(labels), 1))
    for lbl in labels:
        pool = by_label[lbl][:]
        rng.shuffle(pool)
        picked.extend(pool[:per])
    if len(picked) < n:
        rest = [s for s in samples if s not in picked and s.get("tier") != "noisy"]
        rng.shuffle(rest)
        picked.extend(rest[: n - len(picked)])
    return picked[:n]


def _truncate(text: str, limit: int = 3500) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 20] + "\n\n... [truncated] ..."


def build_markdown(rows: list[dict]) -> str:
    lines = [
        "# Judge Calibration Set — Human Scoring",
        "",
        f"**Model outputs:** `{CALIBRATION_MODEL}` (single model, fast baseline)",
        f"**Automated judge scores:** `{JUDGE_MODEL}` (same judge used in benchmark)",
        "",
        "Instructions:",
        "1. For each sample, read the **Input**, **Model output**, and **Reference**.",
        "2. Compare the model output to the reference and scoring criteria.",
        "3. Fill in **Your score (0-10):** with your own judgment (ignore the judge score while scoring).",
        "4. Save this file and return it for correlation analysis.",
        "",
        "---",
        "",
    ]
    for i, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"## Sample {i} — {row['stage']} / {row['sample_id']} / label={row.get('label', '?')}",
                "",
                "### Input",
                "```",
                _truncate(row["input"]),
                "```",
                "",
                "### Model output (ministral-3:8b)",
                "```",
                _truncate(row["model_output"]),
                "```",
                "",
                "### Reference answer",
                "```",
                _truncate(row["reference_answer"]),
                "```",
                "",
                f"**Scoring criteria:** {row.get('scoring_criteria', 'n/a')}",
                "",
                f"**Gemma3:12b judge score:** {row.get('judge_score_0_to_10')} — {row.get('judge_reasoning', '')}",
                "",
                "**Your score (0-10):** _____",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground-truth", default=str(GT_PATH))
    parser.add_argument("--ollama-cloud-key", default="")
    parser.add_argument("--ollama-base-url", default="https://ollama.com/v1")
    parser.add_argument("--judge-model", default=JUDGE_MODEL)
    parser.add_argument("--dry-run", action="store_true", help="Pick samples only, no API calls")
    args = parser.parse_args()

    gt = json.loads(Path(args.ground_truth).read_text(encoding="utf-8"))
    rng = random.Random(20260613)
    rows: list[dict] = []

    for stage_name, stage_cfg in STAGES.items():
        samples = gt.get(stage_name, [])
        picked = _pick_stratified(stage_name, samples, rng, SAMPLES_PER_STAGE)
        for sample in picked:
            rows.append(
                {
                    "stage": stage_name,
                    "sample_id": sample["sample_id"],
                    "label": _label_key(stage_name, sample),
                    "input": sample["input"],
                    "reference_answer": sample["reference_answer"],
                    "scoring_criteria": sample.get("scoring_criteria", ""),
                }
            )

    if args.dry_run:
        print(json.dumps([{"stage": r["stage"], "sample_id": r["sample_id"], "label": r["label"]} for r in rows], indent=2))
        return

    key = args.ollama_cloud_key or os.environ.get("OLLAMA_API_KEY", "")
    if not key:
        raise SystemExit("OLLAMA_API_KEY required")

    for row in rows:
        stage_cfg = STAGES[row["stage"]]
        print(f"Running {CALIBRATION_MODEL} on {row['stage']}/{row['sample_id']}", flush=True)
        call = call_ollama_cloud(
            model=CALIBRATION_MODEL,
            system=stage_cfg["system_prompt"],
            user=row["input"],
            api_key=key,
            base_url=args.ollama_base_url,
        )
        row["model_output"] = call["raw_response"]
        row["total_latency_ms"] = call["total_latency_ms"]
        judged = judge_response(
            stage=row["stage"],
            response=call["raw_response"],
            reference=row["reference_answer"],
            criteria=row["scoring_criteria"],
            latency_ms=call["total_latency_ms"],
            judge_model=args.judge_model,
            judge_api_key=key,
            judge_base_url=args.ollama_base_url,
            pass_threshold=stage_cfg["pass_threshold"],
        )
        row.update(judged)

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(build_markdown(rows), encoding="utf-8")
    OUT_JSON.write_text(json.dumps({"samples": rows}, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_MD} ({len(rows)} samples)")


if __name__ == "__main__":
    main()
