#!/usr/bin/env python3
"""Build stratified benchmark subset from ollama_cloud_ground_truth.json."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GT_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth.json"
OUT_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_subset_v1.json"

TARGETS = {
    "emotion_shift": 25,
    "process_adherence": 25,
    "nli_policy": 25,
    "rag_judge": 20,
    "text_to_sql": 20,
    "fast_classification": 20,
}

CURATED_MAX = {
    "emotion_shift": 5,
    "process_adherence": 10,
    "nli_policy": 10,
    "rag_judge": 5,
    "text_to_sql": 5,
    "fast_classification": 7,
}

PREFIX = {
    "emotion_shift": "es",
    "process_adherence": "pa",
    "nli_policy": "nli",
    "rag_judge": "rj",
    "text_to_sql": "sql",
    "fast_classification": "fc",
}


def _num(sid: str, prefix: str) -> int:
    m = re.match(rf"{prefix}_(\d+)", sid)
    return int(m.group(1)) if m else 9999


def _curated(stage: str, samples: list[dict]) -> list[dict]:
    p = PREFIX[stage]
    mx = CURATED_MAX[stage]
    return sorted(
        [s for s in samples if _num(s["sample_id"], p) <= mx],
        key=lambda s: s["sample_id"],
    )


def _es_label(s: dict) -> str:
    if s.get("_label"):
        return s["_label"]
    ref = s.get("reference_answer", "")
    if "No cross-modal" in ref or "true negative" in ref.lower():
        return "none"
    if "Sarcasm" in ref or "sarcasm" in ref.lower():
        return "sarcasm"
    if "passive" in ref.lower():
        return "passive_aggression"
    if "Cross-modal" in ref or "cross-modal" in ref:
        return "cross_modal"
    return "unknown"


def _pick_stratified(
    pool: list[dict],
    target: int,
    bucket_fn,
    bucket_targets: dict[str, int] | None = None,
) -> list[dict]:
    if len(pool) <= target:
        return pool
    by_bucket: dict[str, list[dict]] = defaultdict(list)
    for s in pool:
        by_bucket[bucket_fn(s)].append(s)
    for k in by_bucket:
        by_bucket[k].sort(key=lambda s: s["sample_id"])

    chosen: list[dict] = []
    chosen_ids: set[str] = set()
    if bucket_targets:
        for bucket, n in bucket_targets.items():
            for s in by_bucket.get(bucket, [])[:n]:
                if s["sample_id"] not in chosen_ids:
                    chosen.append(s)
                    chosen_ids.add(s["sample_id"])
    # fill remaining evenly
    remaining = [s for s in pool if s["sample_id"] not in chosen_ids]
    remaining.sort(key=lambda s: s["sample_id"])
    per = max(1, (target - len(chosen)) // max(1, len(by_bucket)))
    while len(chosen) < target and remaining:
        for bucket in sorted(by_bucket):
            if len(chosen) >= target:
                break
            cands = [s for s in by_bucket[bucket] if s["sample_id"] not in chosen_ids]
            take = min(per, len(cands), target - len(chosen))
            for s in cands[:take]:
                chosen.append(s)
                chosen_ids.add(s["sample_id"])
        remaining = [s for s in pool if s["sample_id"] not in chosen_ids]
        if not remaining:
            break
        if len(chosen) < target:
            for s in remaining:
                if len(chosen) >= target:
                    break
                chosen.append(s)
                chosen_ids.add(s["sample_id"])
            break
        per = 1
    return sorted(chosen[:target], key=lambda s: s["sample_id"])


def _pa_missing_count(s: dict) -> str:
    missing = s.get("_missing")
    if missing is None:
        ref = s.get("reference_answer", "")
        if "No missing" in ref:
            return "0"
        return "1+"
    return str(len(missing))


def _nli_label(s: dict) -> str:
    if s.get("_label"):
        return s["_label"]
    ref = s.get("reference_answer", "")
    for lbl in ("Entailment", "Benign Deviation", "Contradiction", "Policy Hallucination"):
        if lbl in ref:
            return lbl
    return "unknown"


def _rj_doc(s: dict) -> str:
    m = re.search(r"(FIN-RULE-\d+|CS-RULE-\d+|SEC-RULE-\d+)", s.get("input", ""))
    return m.group(1) if m else "unknown"


def _sql_kind(s: dict) -> str:
    q = s.get("input", "").lower()
    sql = s.get("reference_answer", "").lower()
    if "count(*)" in sql and "group by" not in sql:
        return "count"
    if "group by" in sql and "order by" in sql and "limit" in sql:
        return "top_n"
    if "group by" in sql:
        return "aggregation"
    if "date_trunc" in sql or "interval" in sql or "current_date" in sql:
        return "date_filter"
    if " join " in sql:
        return "join"
    return "other"


def build_subset(data: dict[str, list[dict]]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}

    # emotion_shift
    es = data["emotion_shift"]
    es_cur = _curated("emotion_shift", es)
    es_pool = [s for s in es if s not in es_cur]
    es_extra = _pick_stratified(
        es_pool,
        TARGETS["emotion_shift"] - len(es_cur),
        _es_label,
        {"none": 6, "sarcasm": 5, "passive_aggression": 5, "cross_modal": 4},
    )
    out["emotion_shift"] = sorted(es_cur + es_extra, key=lambda s: s["sample_id"])

    # process_adherence
    pa = data["process_adherence"]
    pa_cur = _curated("process_adherence", pa)
    pa_pool = [s for s in pa if s not in pa_cur]
    pa_extra = _pick_stratified(
        pa_pool,
        TARGETS["process_adherence"] - len(pa_cur),
        _pa_missing_count,
        {"0": 6, "1": 6, "2": 6, "3": 3},
    )
    out["process_adherence"] = sorted(pa_cur + pa_extra, key=lambda s: s["sample_id"])

    # nli_policy
    nli = data["nli_policy"]
    nli_cur = _curated("nli_policy", nli)
    nli_pool = [s for s in nli if s not in nli_cur]
    nli_extra = _pick_stratified(
        nli_pool,
        TARGETS["nli_policy"] - len(nli_cur),
        _nli_label,
        {
            "Entailment": 4,
            "Benign Deviation": 4,
            "Contradiction": 4,
            "Policy Hallucination": 3,
        },
    )
    out["nli_policy"] = sorted(nli_cur + nli_extra, key=lambda s: s["sample_id"])

    # rag_judge
    rj = data["rag_judge"]
    rj_cur = _curated("rag_judge", rj)
    rj_pool = [s for s in rj if s not in rj_cur]
    rj_extra = _pick_stratified(rj_pool, TARGETS["rag_judge"] - len(rj_cur), _rj_doc)
    out["rag_judge"] = sorted(rj_cur + rj_extra, key=lambda s: s["sample_id"])

    # text_to_sql — exclude invalid u.team if any remain
    sql = [s for s in data["text_to_sql"] if "u.team" not in s.get("reference_answer", "")]
    sql_cur = _curated("text_to_sql", sql)
    sql_pool = [s for s in sql if s not in sql_cur]
    sql_extra = _pick_stratified(
        sql_pool,
        TARGETS["text_to_sql"] - len(sql_cur),
        _sql_kind,
    )
    out["text_to_sql"] = sorted(sql_cur + sql_extra, key=lambda s: s["sample_id"])

    # fast_classification
    fc = data["fast_classification"]
    fc_cur = _curated("fast_classification", fc)
    fc_pool = [s for s in fc if s not in fc_cur]
    fc_extra = _pick_stratified(fc_pool, TARGETS["fast_classification"] - len(fc_cur), lambda s: "gibberish" if "is_gibberish: true" in s.get("reference_answer", "") else ("ambiguous" if s.get("_note") else "normal"))
    out["fast_classification"] = sorted(fc_cur + fc_extra, key=lambda s: s["sample_id"])

    return out


def stats(subset: dict[str, list[dict]]) -> dict[str, Any]:
    rep: dict[str, Any] = {}
    es_labels = Counter(_es_label(s) for s in subset["emotion_shift"])
    rep["emotion_shift"] = {
        "count": len(subset["emotion_shift"]),
        "labels": dict(es_labels),
        "true_negative_pct": round(100 * es_labels.get("none", 0) / len(subset["emotion_shift"]), 1),
    }
    pa_miss = Counter(_pa_missing_count(s) for s in subset["process_adherence"])
    rep["process_adherence"] = {"count": len(subset["process_adherence"]), "missing_steps": dict(pa_miss)}
    nli = Counter(_nli_label(s) for s in subset["nli_policy"])
    rep["nli_policy"] = {"count": len(subset["nli_policy"]), "labels": dict(nli)}
    rep["rag_judge"] = {"count": len(subset["rag_judge"]), "docs": dict(Counter(_rj_doc(s) for s in subset["rag_judge"]))}
    rep["text_to_sql"] = {"count": len(subset["text_to_sql"]), "kinds": dict(Counter(_sql_kind(s) for s in subset["text_to_sql"]))}
    fc_gib = sum(1 for s in subset["fast_classification"] if "is_gibberish: true" in s.get("reference_answer", ""))
    fc_amb = sum(1 for s in subset["fast_classification"] if s.get("_note"))
    rep["fast_classification"] = {
        "count": len(subset["fast_classification"]),
        "gibberish_pct": round(100 * fc_gib / len(subset["fast_classification"]), 1),
        "ambiguous": fc_amb,
    }
    return rep


def main() -> None:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    subset = build_subset(data)
    OUT_PATH.write_text(json.dumps(subset, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats(subset), indent=2))
    print(f"Wrote {OUT_PATH} ({sum(len(v) for v in subset.values())} samples)")


if __name__ == "__main__":
    main()
