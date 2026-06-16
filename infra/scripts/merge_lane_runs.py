#!/usr/bin/env python3
"""Merge lane benchmark JSON outputs into one combined benchmark JSON."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

from benchmark_ollama_cloud import _aggregate_results  # noqa: E402


def _load_results(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("results", [])
    if isinstance(data, list):
        return data
    return []


def main() -> None:
    report_dir = ROOT / "infra" / "benchmarks" / "reports" / "overnight_20260614"
    lane_paths = [
        report_dir / "final_run_laneA_kimi_v19.json",
        report_dir / "final_run_laneB_ministral_v19.json",
        report_dir / "final_run_laneC_qwen_v19.json",
    ]
    missing = [str(p) for p in lane_paths if not p.exists()]
    if missing:
        raise SystemExit(f"Missing lane output(s): {missing}")

    merged_results: list[dict] = []
    for lane in lane_paths:
        merged_results.extend(_load_results(lane))

    summary = _aggregate_results(merged_results)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_lanes": [str(p) for p in lane_paths],
        "results": merged_results,
        "summary": summary,
    }
    out_path = report_dir / "final_run_all_triggers_stage_routed_v19.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
