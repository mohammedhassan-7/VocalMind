#!/usr/bin/env python3
"""Deep inventory of adherence fields in PA checkpoints."""
import collections
import json
import pathlib
from ground_truth_scorer import parse_json_object

ck = pathlib.Path(__file__).resolve().parents[1] / "benchmarks/reports/overnight_20260614/process_adherence.checkpoint.jsonl"
lines = [json.loads(l) for l in ck.read_text(encoding="utf-8").strip().split("\n") if l.strip()]

values: collections.Counter[str] = collections.Counter()
paths: collections.Counter[str] = collections.Counter()
flat = nested_just = step_by_step = neither = unparseable = 0

NOT_FOLLOWED = {
    "missing", "partial", "incomplete", "not completed", "not_completed", "failed",
    "skipped", "absent", "insufficient evidence", "insufficient_evidence",
    "not_evaluable", "low", "none",
    "partially", "incomplete",
}


def walk(obj, prefix: str = "") -> None:
    global values, paths
    if isinstance(obj, dict):
        adh = obj.get("adherence")
        if adh is not None:
            paths[prefix or "root"] += 1
            values[str(adh).lower()] += 1
        status = obj.get("status")
        if status is not None and "adherence" not in obj:
            paths[(prefix + ".status") if prefix else "status"] += 1
            values[f"status:{str(status).lower()}"] += 1
        for k, v in obj.items():
            walk(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            walk(item, f"{prefix}[{i}]")


for e in lines:
    rr = parse_json_object(e.get("raw_response", ""))
    if not isinstance(rr, dict):
        unparseable += 1
        continue
    if "missing_sop_steps" in rr and isinstance(rr["missing_sop_steps"], list):
        flat += 1
    ev = rr.get("evaluation")
    just = ev.get("justifications") if isinstance(ev, dict) else None
    sb = None
    if isinstance(ev, dict) and isinstance(ev.get("justification"), dict):
        sb = ev["justification"].get("step_by_step")
    if just:
        nested_just += 1
    if sb:
        step_by_step += 1
    if not ("missing_sop_steps" in rr) and not just and not sb:
        neither += 1
    walk(rr)

print(f"entries={len(lines)} flat_missing={flat} nested_justifications={nested_just} step_by_step={step_by_step} neither={neither} unparseable={unparseable}")
print("adherence path hits (top 15):", dict(paths.most_common(15)))
print("adherence values (top 25):", dict(values.most_common(25)))
