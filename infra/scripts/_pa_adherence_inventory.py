#!/usr/bin/env python3
"""Inventory PA checkpoint output shapes and adherence vocabulary."""
from __future__ import annotations

import collections
import json
import pathlib

from ground_truth_scorer import parse_json_object

ROOT = pathlib.Path(__file__).resolve().parents[2]
ck = ROOT / "infra" / "benchmarks" / "reports" / "overnight_20260614" / "process_adherence.checkpoint.jsonl"
lines = [json.loads(l) for l in ck.read_text(encoding="utf-8").strip().split("\n") if l.strip()]

values: collections.Counter[str] = collections.Counter()
shapes: collections.Counter[str] = collections.Counter()
for e in lines:
    rr_raw = e.get("raw_response", "")
    rr = parse_json_object(rr_raw) if isinstance(rr_raw, str) else rr_raw
    if not isinstance(rr, dict):
        shapes["unparseable"] += 1
        continue
    eval_block = rr.get("evaluation")
    just: dict | list | None = None
    if isinstance(eval_block, dict):
        just = eval_block.get("justifications")
    if "missing_sop_steps" in rr:
        shapes["flat_missing_sop_steps"] += 1
    if just:
        shapes["nested_evaluation_justifications"] += 1
        items = just.items() if isinstance(just, dict) else enumerate(just) if isinstance(just, list) else []
        for k, v in items:
            adh = v.get("adherence") if isinstance(v, dict) else v
            values[str(adh)] += 1
    if not just and "missing_sop_steps" not in rr:
        shapes["neither"] += 1

print("Output shapes across all checkpoint entries:", dict(shapes))
print("Distinct 'adherence' values seen:", dict(values))
