#!/usr/bin/env python3
"""Diagnose process_adherence validation regression (no API calls)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from ground_truth_scorer import (
    ScoreResult,
    parse_json_object,
    score_process_adherence,
)

ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "infra/benchmarks/reports/overnight_20260614/_validate_process_adherence.json"
OLD_GT = ROOT / "infra/benchmarks/reports/overnight_20260614/process_adherence_groundtruth.json"
GT_PATH = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"
OUT_MD = ROOT / "infra/benchmarks/reports/overnight_20260614/PA_DIAGNOSIS.md"


def _norm_keys(steps: list[str]) -> set[str]:
    return {re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") for s in steps if s}


def _ref_missing(ref: dict) -> list[str]:
    if ref.get("_missing") is not None:
        return list(ref["_missing"])
    ans = ref.get("reference_answer", "")
    if "No missing" in ans or "no missing" in ans.lower():
        return []
    m = re.search(r"Missing SOP steps:\s*\[(.*?)\]", ans, re.I | re.S)
    if not m:
        return []
    inner = m.group(1)
    return [p.strip() for p in re.split(r",(?=[A-Z])", inner) if p.strip()]


def _extract_pred_keys(raw: str, data: dict | None) -> list[str]:
    keys: list[str] = []
    if data:
        for field in ("missing_sop_steps", "missing_steps", "missed_sop_steps"):
            val = data.get(field)
            if isinstance(val, list):
                keys.extend(str(x) for x in val if x)
        # nested
        for v in data.values():
            if isinstance(v, dict):
                for field in ("missing_sop_steps", "missing_steps"):
                    val = v.get(field)
                    if isinstance(val, list):
                        keys.extend(str(x) for x in val if x)
    return keys


def _key_overlap(pred_keys: list[str], ref_keys: list[str]) -> float:
    """Best substring/fuzzy overlap between predicted keys and reference keys."""
    if not ref_keys or not pred_keys:
        return 0.0
    ref_n = _norm_keys(ref_keys)
    pred_n = _norm_keys(pred_keys)
    hits = 0
    for r in ref_n:
        for p in pred_n:
            if r == p or r in p or p in r:
                hits += 1
                break
    return hits / len(ref_n)


def classify_sample(
    ref_missing: list[str],
    old_sr: ScoreResult,
    new_sr: ScoreResult,
    old_keys: list[str],
    new_keys: list[str],
    old_raw: str,
    new_raw: str,
) -> str:
    old_f1 = old_sr.f1 or 0.0
    new_f1 = new_sr.f1 or 0.0
    old_overlap = _key_overlap(old_keys, ref_missing)
    new_overlap = _key_overlap(new_keys, ref_missing)

    # WORSE: new F1 dropped meaningfully AND not a key-naming issue
    if new_f1 < old_f1 - 0.15:
        if new_overlap < old_overlap - 0.2:
            return "WORSE"
        if new_overlap >= old_overlap and new_f1 < old_f1:
            return "WORSE"  # right ideas but still worse score — catalog noise

    # CLOSER: new has better key overlap but F1 didn't improve (parser/key mismatch)
    if new_overlap > old_overlap + 0.15 and new_f1 <= old_f1 + 0.05:
        return "CLOSER"
    if new_keys and ref_missing:
        ref_n = _norm_keys(ref_missing)
        pred_n = _norm_keys(new_keys)
        for r in ref_n:
            for p in pred_n:
                if (r in p or p in r) and r != p and new_f1 < 0.8:
                    return "CLOSER"

    # WORSE: unparseable or empty when old worked
    if old_sr.match_type != "unparseable" and new_sr.match_type == "unparseable":
        return "WORSE"
    if new_sr.match_type == "unparseable" and old_sr.match_type != "unparseable":
        return "WORSE"

    # WORSE: nested format scorer can't find steps
    if not new_keys and new_raw.strip() and ("step_" in new_raw or "evaluation" in new_raw.lower()):
        if old_keys or old_f1 > 0.3:
            return "WORSE"

    if abs(new_f1 - old_f1) < 0.1:
        return "SAME"

    if new_f1 > old_f1 + 0.1:
        return "SAME"  # improved counts as same bucket for diagnosis

    if new_f1 < old_f1 - 0.05:
        return "WORSE"

    return "SAME"


def main() -> None:
    gt = {s["sample_id"]: s for s in json.loads(GT_PATH.read_text(encoding="utf-8"))["process_adherence"]}
    new_rows = {
        r["sample_id"]: r
        for r in json.loads(VALIDATE.read_text(encoding="utf-8"))["results"]
        if r["model"] == "kimi-k2.6:cloud"
    }
    old_rows = {
        r["sample_id"]: r
        for r in json.loads(OLD_GT.read_text(encoding="utf-8"))["results"]
        if r["model"] == "kimi-k2.6:cloud"
    }

    categories: dict[str, list[dict]] = {"CLOSER": [], "SAME": [], "WORSE": []}
    lines = [
        "# Process Adherence Validation Diagnosis (n=20, kimi-k2.6:cloud)",
        "",
        "Compares new prompt (`_validate_process_adherence.json`) vs v5.1 full run (`process_adherence_groundtruth.json`).",
        "",
    ]

    for sid in sorted(new_rows.keys()):
        new_row = new_rows[sid]
        old_row = old_rows.get(sid)
        ref = gt.get(sid, {})
        ref_missing = _ref_missing(ref)

        new_raw = new_row.get("raw_response", "")
        old_raw = old_row.get("raw_response", "") if old_row else ""
        new_data = parse_json_object(new_raw)
        old_data = parse_json_object(old_raw) if old_row else None

        new_sr = score_process_adherence(new_raw, ref)
        old_sr = score_process_adherence(old_raw, ref) if old_row else ScoreResult(0, "unparseable", f1=0)

        new_keys = _extract_pred_keys(new_raw, new_data)
        old_keys = _extract_pred_keys(old_raw, old_data) if old_row else []

        cat = classify_sample(ref_missing, old_sr, new_sr, old_keys, new_keys, old_raw, new_raw)
        entry = {
            "sample_id": sid,
            "ref_missing": ref_missing,
            "old_keys": old_keys,
            "new_keys": new_keys,
            "old_f1": old_sr.f1,
            "new_f1": new_sr.f1,
            "old_match": old_sr.match_type,
            "new_match": new_sr.match_type,
            "new_raw_preview": new_raw[:400],
        }
        categories[cat].append(entry)

    counts = {k: len(v) for k, v in categories.items()}
    dominant = max(counts, key=counts.get)

    lines.extend(
        [
            "## Summary",
            "",
            f"| CLOSER | SAME | WORSE |",
            f"|---:|---:|---:|",
            f"| {counts['CLOSER']} | {counts['SAME']} | {counts['WORSE']} |",
            "",
            f"**Dominant category:** {dominant}",
            "",
        ]
    )

    if dominant == "CLOSER":
        root = "Parser/scorer needs fuzzy step_key matching against STEP_KEY_TO_LABEL — models use near-correct keys but exact key match fails."
        fix = "Add Levenshtein/substring matching in `ground_truth_scorer.py` `_resolve_step_token` / `_canonicalize_steps` (not another prompt change)."
    elif dominant == "WORSE":
        root = "Catalog length or format drift — models return nested evaluation JSON or over-flag steps from the full catalog."
        fix = "Shorten prompt to topic-specific steps only, or teach scorer to walk nested `evaluation`/`steps` arrays."
    else:
        root = "Prompt change had no measurable effect on these 20 samples — ceiling is reasoning/content, not vocabulary."
        fix = "Focus on topic-scoped step list injection at runtime (production already passes `expected_resolution_graph`)."

    lines.extend([f"**Root cause:** {root}", "", f"**Recommended next fix:** {fix}", "", "## Examples", ""])

    for ex in categories[dominant][:3]:
        lines.extend(
            [
                f"### {ex['sample_id']} ({dominant})",
                f"- Reference missing: `{ex['ref_missing']}`",
                f"- Old keys: `{ex['old_keys']}` → F1={ex['old_f1']}",
                f"- New keys: `{ex['new_keys']}` → F1={ex['new_f1']}",
                f"- New response preview: `{ex['new_raw_preview'][:300]}...`",
                "",
            ]
        )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    print(f"CLOSER={counts['CLOSER']} SAME={counts['SAME']} WORSE={counts['WORSE']} dominant={dominant}")


if __name__ == "__main__":
    main()
