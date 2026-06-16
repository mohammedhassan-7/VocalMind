#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

from ground_truth_scorer import extract_emotion_prediction, parse_emotion_ref, parse_json_object, score_observation  # noqa: E402


def _load_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("results", [])
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python infra/scripts/score_trigger_kpis.py <result_path>")

    result_path = Path(sys.argv[1])
    rows = _load_rows(result_path)

    gt = json.loads((ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json").read_text(encoding="utf-8"))
    es_idx = {s["sample_id"]: s for s in gt.get("emotion_shift", [])}

    by_model = defaultdict(lambda: defaultdict(int))
    friction_labels = {"interruption", "dismissive_tone", "missing_acknowledgment"}

    for row in rows:
        stage = row.get("stage")
        model = row.get("model")
        if stage == "emotion_shift":
            ref_sample = es_idx.get(row.get("sample_id"))
            if not ref_sample:
                continue

            sr = score_observation("emotion_shift", row.get("raw_response", ""), ref_sample, row)
            by_model[model]["es_total"] += 1
            if sr.match_type != "unparseable":
                by_model[model]["es_parseable"] += 1
            if sr.match_type == "exact":
                by_model[model]["es_exact"] += 1

            ref_label, _ = parse_emotion_ref(ref_sample)
            ref_bin = "none" if ref_label == "none" else "friction"
            data = parse_json_object(row.get("raw_response", ""))
            pred_label = None
            if data is not None:
                pred_label = (extract_emotion_prediction(data)[0] or "").strip()
            pred_bin = "none" if pred_label == "none" else ("friction" if pred_label in friction_labels else "unknown")
            if pred_bin == ref_bin:
                by_model[model]["es_trigger_acc"] += 1
        elif stage == "nli_policy":
            by_model[model]["nli_total"] += 1

    for model in sorted(by_model):
        m = by_model[model]
        es_total = m.get("es_total", 0)
        nli_total = m.get("nli_total", 0)
        if es_total:
            print(
                f"{model} | es_exact={m.get('es_exact', 0) / es_total:.1%} | "
                f"es_parseable={m.get('es_parseable', 0) / es_total:.1%} | "
                f"es_trigger_acc={m.get('es_trigger_acc', 0) / es_total:.1%} | "
                f"es_n={es_total} | nli_n={nli_total}"
            )
        else:
            print(f"{model} | es_n=0 | nli_n={nli_total}")


if __name__ == "__main__":
    main()
