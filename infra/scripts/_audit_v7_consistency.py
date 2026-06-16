#!/usr/bin/env python3
"""End-to-end consistency checks for prompts 16-23 artifacts."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

from ground_truth_scorer import score_process_adherence  # noqa: E402

REPORT = ROOT / "infra/benchmarks/reports/overnight_20260614"
PA_GT = REPORT / "process_adherence_groundtruth.json"
ENV_EX = ROOT / "backend/.env.example"
V7 = REPORT / "FULL_REPORT_v7.md"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(f"{label}: {detail}")


def pa_f1_by_model() -> dict[str, dict]:
    rows = json.loads(PA_GT.read_text(encoding="utf-8"))["results"]
    by: dict[str, list] = defaultdict(list)
    for r in rows:
        by[r["model"]].append(r)

    out = {}
    for model, rs in by.items():
        n = len(rs)
        err = sum(1 for r in rs if str(r.get("gt_details", "")).startswith("extraction_error"))
        valid = [r for r in rs if not str(r.get("gt_details", "")).startswith("extraction_error")]
        f1_incl = sum(float(r.get("gt_f1") or 0) for r in rs) / n
        f1_excl = sum(float(r.get("gt_f1") or 0) for r in valid) / len(valid) if valid else 0.0
        # Verify extraction errors score f1=0
        err_f1s = [float(r.get("gt_f1") or 0) for r in rs if str(r.get("gt_details", "")).startswith("extraction_error")]
        out[model] = {
            "n": n,
            "errors": err,
            "f1_incl": f1_incl,
            "f1_excl": f1_excl,
            "err_all_zero": all(f == 0.0 for f in err_f1s),
        }
    return out


def main() -> None:
    print("=== VocalMind v7 consistency audit ===\n")

    pa = pa_f1_by_model()
    winner_incl = max(pa, key=lambda m: pa[m]["f1_incl"])
    winner_excl = max(pa, key=lambda m: pa[m]["f1_excl"])

    check("PA winner (errors_as_0)", winner_incl == "kimi-k2.6:cloud", f"got {winner_incl} F1={pa[winner_incl]['f1_incl']:.3f}")
    check("PA NOT qwen3.5 under errors_as_0", winner_incl != "qwen3.5:cloud", f"qwen3.5 F1_incl={pa['qwen3.5:cloud']['f1_incl']:.3f}")
    check("qwen3.5 wins only under excl-errors", winner_excl == "qwen3.5:cloud", f"excl F1={pa['qwen3.5:cloud']['f1_excl']:.3f}")
    check("kimi-k2.6 F1_incl ~0.546", abs(pa["kimi-k2.6:cloud"]["f1_incl"] - 0.546) < 0.01, f"got {pa['kimi-k2.6:cloud']['f1_incl']:.3f}")
    check("extraction errors have f1=0", all(s["err_all_zero"] for s in pa.values()))

    env_text = ENV_EX.read_text(encoding="utf-8")
    check(".env.example PA=kimi-k2.6", "OLLAMA_PROCESS_ADHERENCE_MODEL=kimi-k2.6:cloud" in env_text)
    check(".env.example PA not qwen3.5", "OLLAMA_PROCESS_ADHERENCE_MODEL=qwen3.5" not in env_text)
    check(".env.example ES=kimi-k2.5", "OLLAMA_EMOTION_SHIFT_MODEL=kimi-k2.5:cloud" in env_text)
    check(".env.example NLI=ministral-3:8b", "OLLAMA_NLI_MODEL=ministral-3:8b" in env_text)

    v7 = V7.read_text(encoding="utf-8")
    check("FULL_REPORT_v7 PA winner kimi-k2.6", "process_adherence** `kimi-k2.6:cloud`" in v7 or "process_adherence | `kimi-k2.6:cloud`" in v7)
    check("FULL_REPORT_v7 warns qwen3.5 excl-errors", "qwen3.5=0.621" in v7)
    check("FULL_REPORT_v7 no PA winner qwen3.5", "OLLAMA_PROCESS_ADHERENCE_MODEL` | `qwen3.5" not in v7)

    # Spot-check scorer returns f1=0 on error
    sr = score_process_adherence("not json at all", {"reference_answer": "Missing SOP steps: [foo]"})
    check("scorer extraction_error -> f1=0", sr.f1 == 0.0 and "extraction_error" in sr.details)

    print("\n=== PA F1 table ===")
    print(f"{'model':<22} | incl    | excl    | errors")
    for m in sorted(pa, key=lambda x: pa[x]["f1_incl"], reverse=True):
        s = pa[m]
        print(f"{m:<22} | {s['f1_incl']:.3f}   | {s['f1_excl']:.3f}   | {s['errors']}")

    print(f"\n{'ALL CHECKS PASSED' if not FAILURES else f'{len(FAILURES)} CHECK(S) FAILED'}")
    if FAILURES:
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
