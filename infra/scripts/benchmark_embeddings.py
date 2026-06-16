#!/usr/bin/env python3
"""
Benchmark Ollama Cloud / local embedding models for VocalMind RAG.

Usage:
    python infra/scripts/benchmark_embeddings.py \
        --pairs infra/benchmarks/expected/embedding_pairs.json \
        --output infra/benchmarks/reports/embedding_benchmark_<timestamp>.json \
        --ollama-cloud-key $OLLAMA_API_KEY
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "infra" / "benchmarks" / "reports"
DEFAULT_PAIRS = ROOT / "infra" / "benchmarks" / "expected" / "embedding_pairs.json"

CANDIDATE_EMBED_MODELS = [
    {"model": "snowflake-arctic-embed2", "base_url": "https://ollama.com", "cloud": True},
    {"model": "snowflake-arctic-embed2", "base_url": "http://localhost:11434", "cloud": False},
    {"model": "nomic-embed-text", "base_url": "https://ollama.com", "cloud": True},
    {"model": "nomic-embed-text", "base_url": "http://localhost:11434", "cloud": False},
]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _embed_text(
    text: str,
    *,
    model: str,
    base_url: str,
    api_key: str | None = None,
    timeout: float = 60.0,
) -> tuple[list[float], float]:
    """Return (vector, latency_ms)."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payloads = (
        ("/api/embed", {"model": model, "input": text}),
        ("/api/embeddings", {"model": model, "prompt": text}),
    )
    t0 = time.perf_counter()
    last_error: Exception | None = None
    with httpx.Client(timeout=timeout) as client:
        for path, payload in payloads:
            try:
                resp = client.post(f"{base_url.rstrip('/')}{path}", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                vector = data.get("embedding")
                if vector:
                    return vector, (time.perf_counter() - t0) * 1000
            except Exception as exc:
                last_error = exc
    raise ConnectionError(f"Embedding failed for {model} @ {base_url}: {last_error}")


def _discover_doc_chunks(docs_root: Path, max_chunks: int = 40) -> list[dict[str, str]]:
    """Collect text chunks from parsed markdown under storage/docs."""
    chunks: list[dict[str, str]] = []
    if not docs_root.exists():
        return chunks

    for md_path in sorted(docs_root.rglob("*.md")):
        if "_raw" in md_path.name or "_chunks" in md_path.name:
            continue
        try:
            text = md_path.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            continue
        if len(text) < 80:
            continue
        for block in text.split("\n\n"):
            block = block.strip()
            if len(block) < 80:
                continue
            chunks.append(
                {
                    "source_file": str(md_path.relative_to(docs_root)),
                    "text": block[:1200],
                }
            )
            if len(chunks) >= max_chunks:
                return chunks
    return chunks


def _top_k_hit_rate(
    query_vec: list[float],
    corpus: list[dict[str, str]],
    expected_fragments: list[str],
    *,
    model: str,
    base_url: str,
    api_key: str | None,
    k: int = 5,
) -> dict[str, Any]:
    if not corpus:
        return {"hit": False, "top_k_sources": [], "note": "empty corpus"}

    scored: list[tuple[float, dict[str, str]]] = []
    for doc in corpus:
        doc_vec, _ = _embed_text(
            doc["text"], model=model, base_url=base_url, api_key=api_key
        )
        scored.append((_cosine_similarity(query_vec, doc_vec), doc))
    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:k]
    top_sources = [item[1]["source_file"] for _, item in top]
    joined = " ".join(top_sources).lower()
    hit = any(frag.lower() in joined for frag in expected_fragments)
    return {
        "hit": hit,
        "top_k_sources": top_sources,
        "top_score": top[0][0] if top else 0.0,
    }


def run_embedding_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    pairs_path = Path(args.pairs)
    pairs_data = json.loads(pairs_path.read_text(encoding="utf-8"))
    pair_rows = pairs_data.get("pairs", [])
    retrieval_rows = pairs_data.get("retrieval_queries", [])

    api_key = args.ollama_cloud_key or os.environ.get("OLLAMA_API_KEY", "")
    docs_root = Path(args.docs_root)
    corpus = _discover_doc_chunks(docs_root)

    models = CANDIDATE_EMBED_MODELS
    if args.models:
        models = []
        for token in args.models.split(","):
            token = token.strip()
            if not token:
                continue
            models.append(
                {
                    "model": token,
                    "base_url": args.ollama_base_url,
                    "cloud": True,
                }
            )

    results: list[dict[str, Any]] = []
    for cfg in models:
        model = cfg["model"]
        base_url = cfg["base_url"]
        cloud = cfg.get("cloud", False)
        key = api_key if cloud else None
        label = f"{model}@{base_url}"

        print(f"Benchmarking {label}")
        pair_metrics: list[dict[str, Any]] = []
        latencies: list[float] = []

        for pair in pair_rows:
            try:
                q_vec, q_lat = _embed_text(
                    pair["query"], model=model, base_url=base_url, api_key=key
                )
                p_vec, p_lat = _embed_text(
                    pair["passage"], model=model, base_url=base_url, api_key=key
                )
                sim = _cosine_similarity(q_vec, p_vec)
                latencies.extend([q_lat, p_lat])
                pair_metrics.append(
                    {
                        "pair_id": pair["id"],
                        "cosine_similarity": round(sim, 4),
                        "query_latency_ms": round(q_lat, 2),
                        "passage_latency_ms": round(p_lat, 2),
                    }
                )
            except Exception as exc:
                pair_metrics.append({"pair_id": pair["id"], "error": str(exc)})

        retrieval_metrics: list[dict[str, Any]] = []
        hits = 0
        for row in retrieval_rows:
            try:
                q_vec, _ = _embed_text(
                    row["query"], model=model, base_url=base_url, api_key=key
                )
                hit_info = _top_k_hit_rate(
                    q_vec,
                    corpus,
                    row.get("expected_source_fragments", []),
                    model=model,
                    base_url=base_url,
                    api_key=key,
                    k=args.top_k,
                )
                if hit_info.get("hit"):
                    hits += 1
                retrieval_metrics.append({"query_id": row["id"], **hit_info})
            except Exception as exc:
                retrieval_metrics.append({"query_id": row["id"], "error": str(exc)})

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        avg_sim = (
            sum(m["cosine_similarity"] for m in pair_metrics if "cosine_similarity" in m)
            / max(1, sum(1 for m in pair_metrics if "cosine_similarity" in m))
        )
        hit_rate = hits / len(retrieval_rows) if retrieval_rows else 0.0

        results.append(
            {
                "model": model,
                "base_url": base_url,
                "cloud": cloud,
                "avg_pair_cosine_similarity": round(avg_sim, 4),
                "avg_embedding_latency_ms": round(avg_latency, 2),
                "top_k_hit_rate": round(hit_rate, 4),
                "corpus_size": len(corpus),
                "pair_metrics": pair_metrics,
                "retrieval_metrics": retrieval_metrics,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pairs_file": str(pairs_path),
        "docs_root": str(docs_root),
        "top_k": args.top_k,
        "results": results,
    }


def write_markdown_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"## VocalMind Embedding Benchmark — {payload['generated_at']}",
        "",
        f"Docs root: `{payload['docs_root']}` (corpus chunks vary by ingest state)",
        "",
        "| Model | Base URL | Avg Cosine Sim | Avg Latency (ms) | Top-k Hit Rate |",
        "|---|---|---|---|---|",
    ]
    for row in payload["results"]:
        lines.append(
            f"| {row['model']} | {row['base_url']} | {row['avg_pair_cosine_similarity']:.4f} | "
            f"{row['avg_embedding_latency_ms']:.1f} | {row['top_k_hit_rate']:.0%} |"
        )
    lines.extend(
        [
            "",
            "### Recommendation",
            "- Embeddings: use ___________",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark embedding models for VocalMind RAG.")
    parser.add_argument("--pairs", default=str(DEFAULT_PAIRS))
    parser.add_argument("--output", default="")
    parser.add_argument("--docs-root", default=str(ROOT / "storage" / "docs" / "nexalink"))
    parser.add_argument("--ollama-cloud-key", default="")
    parser.add_argument("--ollama-base-url", default="https://ollama.com")
    parser.add_argument("--models", default="", help="Comma-separated model names (cloud URL)")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        data = json.loads(Path(args.pairs).read_text(encoding="utf-8"))
        print(f"Pairs: {len(data.get('pairs', []))}")
        print(f"Retrieval queries: {len(data.get('retrieval_queries', []))}")
        print(f"Docs root exists: {Path(args.docs_root).exists()}")
        return

    payload = run_embedding_benchmark(args)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = Path(args.output) if args.output else REPORTS_DIR / f"embedding_benchmark_{ts}.json"
    md_path = json_path.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown_report(md_path, payload)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
