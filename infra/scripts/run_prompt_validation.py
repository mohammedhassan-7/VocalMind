#!/usr/bin/env python3
"""Run small prompt-validation benchmark + ground-truth scoring vs v5.1 baselines."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infra" / "scripts"
REPORT_DIR = ROOT / "infra/benchmarks/reports/overnight_20260614"
SUBSET_PATH = ROOT / "infra/benchmarks/validation_subset_v1.json"
V5_BASELINES = {
    "emotion_shift": {
        "model": "kimi-k2.5:cloud",
        "exact_all": 0.37,
        "exact_parseable": 0.68,
        "parseable": 0.54,
        "f1": None,
    },
    "process_adherence": {
        "model": "kimi-k2.6:cloud",
        "exact_all": 0.35,
        "exact_parseable": 0.35,
        "parseable": 1.0,
        "f1": 0.508,
    },
    "nli_policy": {
        "model": "ministral-3:8b",
        "exact_all": 0.52,
        "exact_parseable": 0.52,
        "parseable": 1.0,
        "f1": None,
    },
    "text_to_sql": {
        "model": "qwen3.5:cloud",
        "exact_all": 0.54,
        "exact_parseable": 0.54,
        "parseable": 1.0,
        "f1": None,
    },
}

STAGES = ["emotion_shift", "process_adherence", "nli_policy", "text_to_sql"]


def _aggregate(rows: list[dict]) -> dict[str, float]:
    n = len(rows)
    exact = sum(1 for r in rows if r.get("match_type") == "exact")
    unparse = sum(1 for r in rows if r.get("match_type") == "unparseable")
    parseable = n - unparse
    f1s = [float(r["gt_f1"]) for r in rows if r.get("gt_f1") is not None]
    return {
        "n": n,
        "exact_all": exact / n if n else 0,
        "parseable": parseable / n if n else 0,
        "exact_parseable": exact / parseable if parseable else 0,
        "f1_avg": sum(f1s) / len(f1s) if f1s else None,
    }


def _verdict(old: dict, new: dict, stage: str) -> str:
    if stage == "emotion_shift":
        improved = new["parseable"] > old["parseable"] + 0.05 or (
            new["exact_parseable"] > old["exact_parseable"] + 0.05 and new["parseable"] >= old["parseable"] - 0.05
        )
        worse = new["parseable"] < old["parseable"] - 0.05 or new["exact_parseable"] < old["exact_parseable"] - 0.10
    elif stage == "process_adherence":
        improved = (new.get("f1_avg") or 0) > (old.get("f1") or 0) + 0.05 or new["exact_all"] > old["exact_all"] + 0.05
        worse = (new.get("f1_avg") or 0) < (old.get("f1") or 0) - 0.05 and new["exact_all"] < old["exact_all"] - 0.05
    else:
        improved = new["exact_all"] > old["exact_all"] + 0.05
        worse = new["exact_all"] < old["exact_all"] - 0.05
    if improved:
        return "IMPROVED (worth full re-run)"
    if worse:
        return "WORSE"
    return "NO CHANGE"


def main() -> None:
    sys.path.insert(0, str(SCRIPTS))
    from ground_truth_scorer import score_observation  # noqa: E402

    if not SUBSET_PATH.exists():
        subprocess.run([sys.executable, str(SCRIPTS / "build_validation_subset.py")], check=True)

    subset = json.loads(SUBSET_PATH.read_text(encoding="utf-8"))
    api_key = os.environ.get("OLLAMA_API_KEY", "")
    if not api_key:
        env_path = ROOT / "backend/.env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("OLLAMA_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not api_key:
        raise SystemExit("OLLAMA_API_KEY not set")

    results: dict[str, list[dict]] = {}
    for stage in STAGES:
        model = V5_BASELINES[stage]["model"]
        out_json = REPORT_DIR / f"_validate_{stage}.json"
        print(f"\n=== Running {stage} / {model} (n=20) ===", flush=True)
        cmd = [
            sys.executable,
            str(SCRIPTS / "benchmark_ollama_cloud.py"),
            "--ground-truth",
            str(SUBSET_PATH),
            "--models",
            model,
            "--stages",
            stage,
            "--max-samples",
            "20",
            "--repeats",
            "1",
            "--max-requests-per-minute",
            "20",
            "--ollama-cloud-key",
            api_key,
            "--output",
            str(out_json),
            "--serial-models",
            "--skip-judge",
        ]
        subprocess.run(cmd, check=True, cwd=str(ROOT))
        rows = json.loads(out_json.read_text(encoding="utf-8")).get("results", [])
        gt_by_id = {s["sample_id"]: s for s in subset[stage]}
        scored = []
        for row in rows:
            ref = gt_by_id[row["sample_id"]]
            sr = score_observation(stage, row.get("raw_response", ""), ref, row)
            scored.append(
                {
                    **row,
                    "gt_score": sr.gt_score,
                    "match_type": sr.match_type,
                    "gt_f1": sr.f1,
                }
            )
        results[stage] = scored

    lines = [
        "# Prompt Validation Report (n=20 per stage)",
        "",
        "Tightened production prompts validated on stratified 20-sample subsets.",
        "",
        "## Part 1–4: Prompt changes",
        "",
        "- **emotion_shift**: closed label set (`sarcasm|passive_aggression|cross_modal|none`), strict JSON schema, 3 few-shot examples, JSON mode in benchmark.",
        "- **process_adherence**: full RESOLUTION_GRAPH step_key catalog, `missing_sop_steps` must use snake_case keys only, few-shot example.",
        "- **nli_policy**: Benign Deviation vs Contradiction distinguishing rule + nli_003-style example, strict `verdict` JSON.",
        "- **text_to_sql**: 3 few-shot join/aggregate examples added to benchmark + production schema block.",
        "",
        "Files: `backend/app/llm_trigger/prompt_constants.py`, `prompts.py`, `benchmark_ollama_cloud.py`.",
        "",
        "## Part 5: Validation results",
        "",
        "| Stage | Model | Metric | v5.1 full (baseline) | n=20 new | Verdict |",
        "|---|---|---|---:|---:|---|",
    ]

    for stage in STAGES:
        old = V5_BASELINES[stage]
        new = _aggregate(results[stage])
        v = _verdict(old, new, stage)
        model = old["model"]
        if stage == "emotion_shift":
            lines.append(
                f"| {stage} | {model} | parseable | {old['parseable']:.0%} | {new['parseable']:.0%} | {v} |"
            )
            lines.append(
                f"| {stage} | {model} | exact (parseable) | {old['exact_parseable']:.0%} | {new['exact_parseable']:.0%} | |"
            )
            lines.append(
                f"| {stage} | {model} | exact (all) | {old['exact_all']:.0%} | {new['exact_all']:.0%} | |"
            )
        elif stage == "process_adherence":
            lines.append(
                f"| {stage} | {model} | exact (all) | {old['exact_all']:.0%} | {new['exact_all']:.0%} | {v} |"
            )
            lines.append(
                f"| {stage} | {model} | F1 avg | {old['f1']:.3f} | {(new['f1_avg'] or 0):.3f} | |"
            )
        else:
            lines.append(
                f"| {stage} | {model} | exact (all) | {old['exact_all']:.0%} | {new['exact_all']:.0%} | {v} |"
            )

    lines.extend(["", "## Summary", ""])
    for stage in STAGES:
        old = V5_BASELINES[stage]
        new = _aggregate(results[stage])
        v = _verdict(old, new, stage)
        if stage == "emotion_shift":
            lines.append(
                f"- **{stage}/{old['model']}**: parseable {old['parseable']:.0%}→{new['parseable']:.0%}, "
                f"exact(parseable) {old['exact_parseable']:.0%}→{new['exact_parseable']:.0%} — **{v}**"
            )
        elif stage == "process_adherence":
            lines.append(
                f"- **{stage}/{old['model']}**: exact {old['exact_all']:.0%}→{new['exact_all']:.0%}, "
                f"F1 {old['f1']:.3f}→{(new['f1_avg'] or 0):.3f} — **{v}**"
            )
        else:
            lines.append(
                f"- **{stage}/{old['model']}**: exact {old['exact_all']:.0%}→{new['exact_all']:.0%} — **{v}**"
            )

    out_md = REPORT_DIR / "PROMPT_VALIDATION_REPORT.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_md}")


if __name__ == "__main__":
    main()
