#!/usr/bin/env python3
"""Cluster near-duplicate ground-truth samples via union-find."""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra" / "scripts"))
import generate_ground_truth as gt  # noqa: E402

STAGES = (
    "emotion_shift",
    "process_adherence",
    "nli_policy",
    "rag_judge",
    "text_to_sql",
    "fast_classification",
)


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _skeleton(text: str) -> str:
    import re

    t = text.lower()
    t = re.sub(r"NX-\d+", "NX-XXXXXX", t)
    t = re.sub(r"\$\d+", "$AMT", t)
    t = re.sub(r"\d{4,}", "NUM", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def cluster_stage(samples: list[dict], threshold: float) -> tuple[list[tuple[str, str, float]], dict[str, list[str]]]:
    ids = [s.get("sample_id", "?") for s in samples]
    texts = [_skeleton(s.get("input", "")) for s in samples]
    uf = UnionFind()
    pairs: list[tuple[str, str, float]] = []
    for i in range(len(samples)):
        for j in range(i + 1, len(samples)):
            ratio = difflib.SequenceMatcher(None, texts[i], texts[j]).ratio()
            if ratio >= threshold:
                pairs.append((ids[i], ids[j], ratio))
                uf.union(ids[i], ids[j])
    clusters: dict[str, list[str]] = defaultdict(list)
    for sid in ids:
        clusters[uf.find(sid)].append(sid)
    return pairs, {k: v for k, v in clusters.items() if len(v) > 1}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground-truth", default=str(ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"))
    parser.add_argument("--threshold", type=float, default=0.8)
    parser.add_argument("--min-cluster", type=int, default=8)
    parser.add_argument("--export-clusters", default="")
    args = parser.parse_args()

    data = json.loads(Path(args.ground_truth).read_text(encoding="utf-8"))
    total_pairs = 0
    large_clusters: list[tuple[str, int, str, list[str]]] = []

    for stage in STAGES:
        samples = data.get(stage, [])
        if not isinstance(samples, list):
            continue
        pairs, clusters = cluster_stage(samples, args.threshold)
        total_pairs += len(pairs)
        for root, members in sorted(clusters.items(), key=lambda x: -len(x[1])):
            if len(members) >= args.min_cluster:
                rep = next(s for s in samples if s.get("sample_id") == members[0])
                inp = rep.get("input", "")[:150].replace("\n", " ")
                large_clusters.append((stage, len(members), inp, members))

    large_clusters.sort(key=lambda x: -x[1])
    print(f"Total near-dup pairs (>={args.threshold}): {total_pairs}")
    print(f"Largest cluster size: {large_clusters[0][1] if large_clusters else 1}")
    print("\nTop 15 clusters:")
    for stage, size, inp, members in large_clusters[:15]:
        print(f"  [{stage}] size={size} ids={members[0]}..{members[-1]} ({len(members)} total)")
        print(f"    {inp}...")

    if args.export_clusters:
        payload = {
            "total_pairs": total_pairs,
            "large_clusters": [
                {"stage": s, "size": n, "sample_ids": m, "representative_input": inp}
                for s, n, inp, m in large_clusters
            ],
        }
        Path(args.export_clusters).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nExported cluster manifest to {args.export_clusters}")


if __name__ == "__main__":
    main()
