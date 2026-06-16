#!/usr/bin/env python3
"""Sample PA checkpoint output shapes."""
import json
import pathlib
from ground_truth_scorer import parse_json_object

ck = pathlib.Path(__file__).resolve().parents[1] / "benchmarks/reports/overnight_20260614/process_adherence.checkpoint.jsonl"
lines = [json.loads(l) for l in ck.read_text(encoding="utf-8").strip().split("\n") if l.strip()]

keys_counter = {}
for e in lines[:50]:
    rr = parse_json_object(e.get("raw_response", ""))
    if not isinstance(rr, dict):
        continue
    for k in rr:
        keys_counter[k] = keys_counter.get(k, 0) + 1
print("Top-level keys (first 50 parseable):", keys_counter)

# find one with missing_sop_steps
for e in lines:
    rr = parse_json_object(e.get("raw_response", ""))
    if isinstance(rr, dict) and "missing_sop_steps" in rr:
        print("\nflat missing_sop_steps example:", e["sample_id"], rr.get("missing_sop_steps")[:3])
        break

# find evaluation.justification.step_by_step
for e in lines:
    rr = parse_json_object(e.get("raw_response", ""))
    if not isinstance(rr, dict):
        continue
    ev = rr.get("evaluation", {})
    if isinstance(ev, dict):
        j = ev.get("justification", {})
        if isinstance(j, dict) and "step_by_step" in j:
            print("\nstep_by_step example:", e["sample_id"])
            for sk, sv in list(j["step_by_step"].items())[:2]:
                print(" ", sk, sv.get("adherence") if isinstance(sv, dict) else sv)
            break
