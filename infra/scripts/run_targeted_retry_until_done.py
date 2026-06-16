#!/usr/bin/env python3
"""Keep targeted retry benchmark running until successful completion."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / "backend" / ".env"


def _load_key_from_env_file() -> str | None:
    if not ENV_PATH.exists():
        return None
    for raw in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == "OLLAMA_API_KEY":
            return v.strip().strip('"').strip("'")
    return None


def _build_cmd() -> list[str]:
    return [
        sys.executable,
        "infra/scripts/benchmark_ollama_cloud.py",
        "--ground-truth",
        "infra/benchmarks/ollama_cloud_ground_truth_v2.json",
        "--stages",
        "emotion_shift,nli_policy,process_adherence,fast_classification,rag_judge",
        "--models",
        "kimi-k2.5:cloud,ministral-3:8b,qwen3.5:cloud",
        "--skip-judge",
        "--serial-models",
        "--max-requests-per-minute",
        "3",
        "--max-retries",
        "8",
        "--retry-errors-from",
        "infra/benchmarks/reports/overnight_20260614/targeted_retry_errors_v20.json",
        "--output",
        "infra/benchmarks/reports/overnight_20260614/targeted_retry_run_v20.json",
    ]


def main() -> int:
    env = os.environ.copy()
    if not env.get("OLLAMA_API_KEY"):
        key = _load_key_from_env_file()
        if key:
            env["OLLAMA_API_KEY"] = key

    if not env.get("OLLAMA_API_KEY"):
        print("Missing OLLAMA_API_KEY; cannot start retry loop.", flush=True)
        return 2

    cmd = _build_cmd()
    attempt = 0
    while True:
        attempt += 1
        print(f"[retry-loop] attempt={attempt} starting", flush=True)
        rc = subprocess.call(cmd, cwd=ROOT, env=env)
        if rc == 0:
            print("[retry-loop] completed successfully", flush=True)
            return 0
        print(f"[retry-loop] attempt={attempt} failed rc={rc}; restarting in 10s", flush=True)
        time.sleep(10)


if __name__ == "__main__":
    raise SystemExit(main())
