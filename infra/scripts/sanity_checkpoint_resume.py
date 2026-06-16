#!/usr/bin/env python3
"""Verify checkpoint resume: partial run then restart skips completed keys."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "infra/benchmarks/reports/sanity_checkpoint_test.json"
GT = ROOT / "infra/benchmarks/sanity_checkpoint_gt.json"


def _count_checkpoint(path: Path) -> int:
    ck = path.with_suffix(".checkpoint.jsonl")
    if not ck.exists():
        return 0
    return sum(1 for ln in ck.read_text(encoding="utf-8").splitlines() if ln.strip())


def main() -> None:
    key = os.environ.get("OLLAMA_API_KEY", "")
    if not key:
        print("SKIP: OLLAMA_API_KEY not set")
        sys.exit(0)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    ck = OUT.with_suffix(".checkpoint.jsonl")
    if ck.exists():
        ck.unlink()
    if OUT.exists():
        OUT.unlink()

    cmd = [
        sys.executable,
        str(ROOT / "infra/scripts/benchmark_ollama_cloud.py"),
        "--ground-truth",
        str(GT),
        "--models",
        "ministral-3:8b,kimi-k2.6:cloud,ministral-3:14b",
        "--stages",
        "fast_classification",
        "--repeats",
        "2",
        "--serial-models",
        "--judge-model",
        "gemma3:12b",
        "--judge-base-url",
        "https://ollama.com/v1",
        "--judge-api-key",
        key,
        "--output",
        str(OUT),
    ]

    p1 = subprocess.Popen(cmd, cwd=ROOT)
    time.sleep(25)
    p1.terminate()
    try:
        p1.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p1.kill()

    n_partial = _count_checkpoint(OUT)
    print(f"After interrupt: {n_partial} checkpoint rows")

    p2 = subprocess.run(cmd, cwd=ROOT)
    n_final = _count_checkpoint(OUT)
    data = json.loads(OUT.read_text(encoding="utf-8"))
    expected = 2 * 3 * 2  # samples * models * repeats
    has_pctl = "p50_total_latency_ms" in json.dumps(data.get("summary", {}))
    print(f"Final checkpoint rows: {n_final} (expected {expected})")
    print(f"Summary has percentiles: {has_pctl}")
    ok = n_final == expected and has_pctl and p2.returncode == 0
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
