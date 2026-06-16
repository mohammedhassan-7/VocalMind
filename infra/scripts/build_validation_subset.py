#!/usr/bin/env python3
"""Build stratified 20-sample validation subset per weak stage."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GT_PATH = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"
OUT_PATH = ROOT / "infra/benchmarks/validation_subset_v1.json"


def _nli_label(sample: dict) -> str:
    ref = sample.get("reference_answer", "")
    if ref.startswith("Verdict:"):
        return ref.split(".")[0].replace("Verdict:", "").strip()
    if "Entailment" in ref[:40]:
        return "Entailment"
    if "Benign" in ref:
        return "Benign Deviation"
    if "Hallucination" in ref:
        return "Policy Hallucination"
    if "Contradiction" in ref:
        return "Contradiction"
    return "other"


def _pick_stratified(samples: list[dict], bucket_fn, per_bucket: int, total: int) -> list[dict]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for s in samples:
        buckets[bucket_fn(s)].append(s)
    picked: list[dict] = []
    for bucket in sorted(buckets):
        picked.extend(buckets[bucket][:per_bucket])
    if len(picked) < total:
        seen = {s["sample_id"] for s in picked}
        for s in samples:
            if s["sample_id"] not in seen:
                picked.append(s)
            if len(picked) >= total:
                break
    return picked[:total]


def main() -> None:
    gt = json.loads(GT_PATH.read_text(encoding="utf-8"))
    out: dict[str, list] = {}

    es = gt["emotion_shift"]
    out["emotion_shift"] = _pick_stratified(
        es, lambda s: s.get("_label", "unknown"), per_bucket=5, total=20
    )

    pa = gt["process_adherence"]
    out["process_adherence"] = _pick_stratified(
        pa,
        lambda s: "missing" if s.get("_missing") else "complete",
        per_bucket=10,
        total=20,
    )

    nli = gt["nli_policy"]
    out["nli_policy"] = _pick_stratified(nli, _nli_label, per_bucket=5, total=20)

    sql = gt["text_to_sql"]
    out["text_to_sql"] = sql[:20]

    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    for stage, samples in out.items():
        print(f"  {stage}: {len(samples)} samples")


if __name__ == "__main__":
    main()
