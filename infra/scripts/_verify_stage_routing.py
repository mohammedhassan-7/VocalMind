#!/usr/bin/env python3
"""Verify per-stage model routing fallback and override."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

os.environ["LLM_PROVIDER"] = "ollama_cloud"
os.environ["OLLAMA_CLOUD_HEAVY_MODEL"] = "heavy-default"
os.environ.pop("OLLAMA_EMOTION_SHIFT_MODEL", None)
os.environ.pop("OLLAMA_PROCESS_ADHERENCE_MODEL", None)
os.environ.pop("OLLAMA_NLI_MODEL", None)

from importlib import reload  # noqa: E402

import app.core.config as config_mod  # noqa: E402
import app.llm_trigger.chains as chains_mod  # noqa: E402

reload(config_mod)
reload(chains_mod)

print("=== No per-stage overrides (expect heavy-default) ===")
for stage in ("emotion_shift", "process_adherence", "nli_policy"):
    print(f"  {stage}: {chains_mod.get_model_for_stage(stage)}")

os.environ["OLLAMA_EMOTION_SHIFT_MODEL"] = "test-model"
reload(config_mod)
reload(chains_mod)

print("\n=== OLLAMA_EMOTION_SHIFT_MODEL=test-model ===")
print(f"  emotion_shift: {chains_mod.get_model_for_stage('emotion_shift')}")
print(f"  process_adherence: {chains_mod.get_model_for_stage('process_adherence')}")
print(f"  nli_policy: {chains_mod.get_model_for_stage('nli_policy')}")
