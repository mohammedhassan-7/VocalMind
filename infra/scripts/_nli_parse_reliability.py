#!/usr/bin/env python3
"""Prompt 23: NLI raw-output reliability per model (strict NLIEvaluation parse)."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

from langchain_core.output_parsers import PydanticOutputParser  # noqa: E402

from app.llm_trigger.schemas import NLIEvaluation  # noqa: E402
from ground_truth_scorer import score_nli_policy  # noqa: E402

CK = ROOT / "infra/benchmarks/reports/overnight_20260614/nli_policy.checkpoint.jsonl"
GT_PATH = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"


def strict_nli_parse(raw: str) -> bool:
    parser = PydanticOutputParser(pydantic_object=NLIEvaluation)
    try:
        parser.parse(raw)
        return True
    except Exception:
        return False


def benchmark_parseable(raw: str, ref: dict) -> bool:
    return score_nli_policy(raw, ref).match_type != "unparseable"


def main() -> None:
    lines = [json.loads(l) for l in CK.read_text(encoding="utf-8").splitlines() if l.strip()]
    gt = {s["sample_id"]: s for s in json.loads(GT_PATH.read_text(encoding="utf-8"))["nli_policy"]}

    by_model: dict[str, dict[str, dict]] = defaultdict(dict)
    for e in lines:
        by_model[e["model"]][e["sample_id"]] = e

    print(f"{'model':<22} | {'n':>4} | {'strict_err':>10} | {'strict_err%':>11} | {'bench_unparse%':>14} | {'judge_avg':>9} | {'GT_exact%':>9}")
    print("-" * 95)

    rows = []
    for model in sorted(by_model):
        entries = list(by_model[model].values())
        n = len(entries)
        strict_err = sum(1 for e in entries if not strict_nli_parse(e.get("raw_response", "")))
        bench_unparse = sum(
            1
            for e in entries
            if e["sample_id"] in gt and benchmark_parseable(e.get("raw_response", ""), gt[e["sample_id"]]) is False
        )
        judges = [float(e["judge_score_0_to_10"]) for e in entries if e.get("judge_score_0_to_10") is not None]
        judge_avg = sum(judges) / len(judges) if judges else 0.0
        gt_exact = sum(
            1
            for e in entries
            if e["sample_id"] in gt and score_nli_policy(e.get("raw_response", ""), gt[e["sample_id"]]).match_type == "exact"
        )
        rows.append((model, n, strict_err, strict_err / n, bench_unparse / n, judge_avg, gt_exact / n))
        print(
            f"{model:<22} | {n:4d} | {strict_err:10d} | {100*strict_err/n:10.1f}% | "
            f"{100*bench_unparse/n:13.1f}% | {judge_avg:9.2f} | {100*gt_exact/n:8.1f}%"
        )

    print("\n=== Decision notes ===")
    ms = next(r for r in rows if r[0] == "ministral-3:8b")
    k6 = next(r for r in rows if r[0] == "kimi-k2.6:cloud")
    print(f"ministral-3:8b strict parse error rate: {100*ms[3]:.1f}%")
    print(f"kimi-k2.6:cloud strict parse error rate: {100*k6[3]:.1f}%")


if __name__ == "__main__":
    main()
