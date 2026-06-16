#!/usr/bin/env python3
import json, pathlib
from ground_truth_scorer import parse_json_object
ck = pathlib.Path(__file__).resolve().parents[1] / "benchmarks/reports/overnight_20260614/process_adherence.checkpoint.jsonl"
for line in ck.read_text(encoding="utf-8").splitlines()[:200]:
    e = json.loads(line)
    rr = parse_json_object(e.get("raw_response",""))
    if not isinstance(rr, dict):
        continue
    ev = rr.get("evaluation")
    just = ev.get("justifications") if isinstance(ev, dict) else None
    sb = ev.get("justification",{}).get("step_by_step") if isinstance(ev, dict) and isinstance(ev.get("justification"), dict) else None
    if "missing_sop_steps" not in rr and not just and not sb:
        print("neither sample", e["sample_id"], "keys", list(rr.keys())[:8])
        if "step_evaluations" in rr:
            print("  step_eval[0]", rr["step_evaluations"][0])
        break
