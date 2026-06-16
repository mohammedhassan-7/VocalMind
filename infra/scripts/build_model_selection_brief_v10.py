#!/usr/bin/env python3
"""Build a one-page model selection brief from final run or checkpoint rows."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

from ground_truth_scorer import score_observation  # noqa: E402

REPORT_DIR = ROOT / "infra" / "benchmarks" / "reports" / "overnight_20260614"
GT_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"
TOTAL_BY_STAGE = {"emotion_shift": 170 * 8, "nli_policy": 172 * 8}


def _load_rows() -> tuple[list[dict], str]:
    final_path = REPORT_DIR / "final_run_es_nli_8models_v10.json"
    checkpoint_path = REPORT_DIR / "final_run_es_nli_8models_v10.checkpoint.jsonl"
    if final_path.exists():
        data = json.loads(final_path.read_text(encoding="utf-8"))
        return data.get("results", []), str(final_path)
    rows = [json.loads(line) for line in checkpoint_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows, str(checkpoint_path)


def _dedupe(rows: list[dict]) -> list[dict]:
    by_key: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        by_key[(row.get("stage", ""), row.get("model", ""), row.get("sample_id", ""))] = row
    return list(by_key.values())


def _score_stage(stage: str, rows: list[dict], gt_index: dict[str, dict]) -> dict[str, dict[str, float]]:
    by_model: dict[str, list[tuple[dict, object]]] = defaultdict(list)
    for row in rows:
        if row.get("stage") != stage:
            continue
        sid = row.get("sample_id")
        ref = gt_index.get(stage, {}).get(sid)
        if not ref:
            continue
        sr = score_observation(stage, row.get("raw_response", ""), ref, row)
        by_model[row["model"]].append((row, sr))

    out: dict[str, dict[str, float]] = {}
    for model, pairs in by_model.items():
        n = len(pairs)
        exact = sum(1 for _, sr in pairs if getattr(sr, "match_type", "") == "exact")
        unparseable = sum(1 for _, sr in pairs if getattr(sr, "match_type", "") == "unparseable")
        lat = sorted(float(r.get("total_latency_ms") or 0) for r, _ in pairs)
        p50 = lat[len(lat) // 2] if lat else 0.0
        out[model] = {
            "n": n,
            "exact_rate": exact / n if n else 0.0,
            "parseable_rate": (n - unparseable) / n if n else 0.0,
            "p50_ms": p50,
        }
    return out


def _rank(stage_stats: dict[str, dict[str, float]]) -> list[tuple[str, dict[str, float]]]:
    return sorted(
        stage_stats.items(),
        key=lambda kv: (kv[1]["exact_rate"], kv[1]["parseable_rate"], -kv[1]["p50_ms"]),
        reverse=True,
    )


def main() -> None:
    rows, source = _load_rows()
    rows = _dedupe(rows)
    gt = json.loads(GT_PATH.read_text(encoding="utf-8"))
    gt_index = {
        "emotion_shift": {s["sample_id"]: s for s in gt.get("emotion_shift", [])},
        "nli_policy": {s["sample_id"]: s for s in gt.get("nli_policy", [])},
    }
    es = _score_stage("emotion_shift", rows, gt_index)
    nli = _score_stage("nli_policy", rows, gt_index)
    es_ranked = _rank(es)
    nli_ranked = _rank(nli)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows_by_stage = defaultdict(int)
    for r in rows:
        rows_by_stage[r.get("stage", "")] += 1

    lines = [
        "# Model Selection Brief v10 (One Page)",
        "",
        f"Generated: {now}",
        f"Source: `{source}`",
        "",
        "## Coverage",
        f"- emotion_shift rows: {rows_by_stage.get('emotion_shift', 0)}/{TOTAL_BY_STAGE['emotion_shift']}",
        f"- nli_policy rows: {rows_by_stage.get('nli_policy', 0)}/{TOTAL_BY_STAGE['nli_policy']}",
        "",
        "## Recommended Routing (Current Best)",
        f"- OLLAMA_EMOTION_SHIFT_MODEL: `{es_ranked[0][0]}`" if es_ranked else "- OLLAMA_EMOTION_SHIFT_MODEL: `n/a`",
        f"- OLLAMA_NLI_MODEL: `{nli_ranked[0][0]}`" if nli_ranked else "- OLLAMA_NLI_MODEL: `n/a`",
        "",
        "## Why These Models",
    ]

    if es_ranked:
        m, s = es_ranked[0]
        lines.extend(
            [
                f"- emotion_shift winner `{m}`: exact={s['exact_rate']:.1%}, parseable={s['parseable_rate']:.1%}, p50={s['p50_ms']:.0f}ms, n={int(s['n'])}.",
                "- Rationale: best GT exact on friction-root-cause interpretation while keeping parseability strong.",
            ]
        )
    if nli_ranked:
        m, s = nli_ranked[0]
        lines.extend(
            [
                f"- nli_policy winner `{m}`: exact={s['exact_rate']:.1%}, parseable={s['parseable_rate']:.1%}, p50={s['p50_ms']:.0f}ms, n={int(s['n'])}.",
                "- Rationale: best policy classification exactness under parseability and latency tie-breakers.",
            ]
        )
    else:
        lines.append("- nli_policy winner pending: stage rows have not been produced yet in current run.")

    lines.extend(["", "## Top Contenders Snapshot"])
    if es_ranked:
        lines.append("- emotion_shift top 3:")
        for m, s in es_ranked[:3]:
            lines.append(
                f"  - {m}: exact={s['exact_rate']:.1%}, parseable={s['parseable_rate']:.1%}, p50={s['p50_ms']:.0f}ms, n={int(s['n'])}"
            )
    if nli_ranked:
        lines.append("- nli_policy top 3:")
        for m, s in nli_ranked[:3]:
            lines.append(
                f"  - {m}: exact={s['exact_rate']:.1%}, parseable={s['parseable_rate']:.1%}, p50={s['p50_ms']:.0f}ms, n={int(s['n'])}"
            )

    out = REPORT_DIR / "MODEL_SELECTION_BRIEF_v10.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
