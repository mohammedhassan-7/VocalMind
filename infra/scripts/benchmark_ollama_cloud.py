#!/usr/bin/env python3
"""
Benchmark candidate Ollama Cloud models for each VocalMind pipeline stage.

Usage:
    python infra/scripts/benchmark_ollama_cloud.py \
        --ground-truth infra/benchmarks/ollama_cloud_ground_truth.json \
        --output infra/benchmarks/reports/ollama_cloud_benchmark_<timestamp>.json \
        --ollama-cloud-key $OLLAMA_API_KEY \
        --judge-model gpt-4o-mini
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import sys
import time
import threading
import math
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "infra" / "benchmarks" / "reports"
ASSISTANT_PY = ROOT / "backend" / "app" / "api" / "routes" / "assistant.py"
TRIAGE_PATH = ROOT / "infra" / "benchmarks" / "model_triage_v1.json"

# Runtime rate-limit / retry config (set in run_benchmark from CLI).
_ACTIVE_RATE_LIMITER: "RateLimiter | None" = None
_ACTIVE_MAX_RETRIES: int = 5


class RateLimiter:
    """Simple global token bucket: max N requests per 60s wall clock."""

    def __init__(self, max_per_minute: float) -> None:
        self.max_per_minute = max(0.0, max_per_minute)
        self.lock = threading.Lock()
        self.timestamps: list[float] = []

    def acquire(self) -> None:
        if self.max_per_minute <= 0:
            return
        while True:
            with self.lock:
                now = time.perf_counter()
                cutoff = now - 60.0
                self.timestamps = [t for t in self.timestamps if t > cutoff]
                if len(self.timestamps) < self.max_per_minute:
                    self.timestamps.append(now)
                    return
                wait = self.timestamps[0] + 60.0 - now
            time.sleep(max(0.05, wait))


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _retryable_status(code: int) -> bool:
    return code in (429, 500, 502, 503, 504)


def _call_with_retry(fn: Any) -> Any:
    """Execute fn(); retry on 429/5xx with exponential backoff."""
    last_exc: Exception | None = None
    max_retries = _ACTIVE_MAX_RETRIES
    for attempt in range(max_retries):
        if _ACTIVE_RATE_LIMITER:
            _ACTIVE_RATE_LIMITER.acquire()
        try:
            return fn()
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            code = exc.response.status_code
            if not _retryable_status(code) or attempt >= max_retries - 1:
                raise
            retry_after = _parse_retry_after(exc.response.headers.get("Retry-After"))
            delay = retry_after if retry_after is not None else min(60.0, 2.0 * (2**attempt))
            print(
                f"  retry {attempt + 1}/{max_retries - 1} after HTTP {code}, sleep {delay:.1f}s",
                flush=True,
            )
            time.sleep(delay)
        except httpx.TransportError as exc:
            last_exc = exc
            if attempt >= max_retries - 1:
                raise
            delay = min(60.0, 2.0 * (2**attempt))
            print(f"  retry {attempt + 1}/{max_retries - 1} after transport error, sleep {delay:.1f}s", flush=True)
            time.sleep(delay)
    raise last_exc or RuntimeError("retry exhausted")

sys.path.insert(0, str(ROOT / "infra" / "scripts"))
from benchmark_input import normalize_emotion_shift_input, normalize_nli_input  # noqa: E402
from text_to_sql_execution import score_sql_execution  # noqa: E402


def _load_prompt_constants():
    path = ROOT / "backend/app/llm_trigger/prompt_constants.py"
    spec = importlib.util.spec_from_file_location("prompt_constants", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_pc = _load_prompt_constants()
EMOTION_SHIFT_FEW_SHOT = _pc.EMOTION_SHIFT_FEW_SHOT
EMOTION_SHIFT_SYSTEM_CORE = _pc.EMOTION_SHIFT_SYSTEM_CORE
INJECTION_GUARD = _pc.INJECTION_GUARD
NLI_FEW_SHOT = _pc.NLI_FEW_SHOT
NLI_POLICY_SYSTEM_CORE = _pc.NLI_POLICY_SYSTEM_CORE
PROCESS_ADHERENCE_FEW_SHOT = _pc.PROCESS_ADHERENCE_FEW_SHOT
PROCESS_ADHERENCE_SYSTEM_CORE = _pc.PROCESS_ADHERENCE_SYSTEM_CORE
TEXT_TO_SQL_FEW_SHOT = _pc.TEXT_TO_SQL_FEW_SHOT

# Original-run samples whose model outputs are reused (re-judge only) for nli/pa.
REUSE_RESPONSE_SAMPLES: dict[str, frozenset[str]] = {
    "nli_policy": frozenset({f"nli_{i:03d}" for i in range(1, 11)}),
    "process_adherence": frozenset({f"pa_{i:03d}" for i in range(1, 11)}),
}


def _load_assistant_schema() -> str:
    """Extract production _SCHEMA from assistant.py (no FastAPI import)."""
    tree = ast.parse(ASSISTANT_PY.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_SCHEMA":
                    return ast.literal_eval(node.value)
    raise RuntimeError(f"_SCHEMA not found in {ASSISTANT_PY}")


def _strip_code_fences(text: str) -> str:
    """Remove markdown ```sql / ```json fences from model output."""
    stripped = text.strip()
    if "```" not in stripped:
        return stripped
    for part in stripped.split("```"):
        cleaned = part.strip()
        lower = cleaned.lower()
        if lower.startswith("sql"):
            cleaned = cleaned[3:].strip()
        elif lower.startswith("json"):
            cleaned = cleaned[4:].strip()
        if cleaned.upper().startswith("SELECT") or cleaned.upper().startswith("WITH"):
            return cleaned
        if cleaned.startswith("{"):
            return cleaned
    return stripped


def _build_text_to_sql_system() -> str:
    schema = _load_assistant_schema()
    return (
        "You are a PostgreSQL expert for a call-center analytics platform.\n"
        "Convert the manager's question into a single valid PostgreSQL SELECT query.\n\n"
        f"Schema:\n{schema}\n\n"
        "Rules:\n"
        "1. Always restrict to the organization using organization_id on users OR interactions.\n"
        "2. Return ONLY raw SQL - no markdown, no explanation.\n"
        "3. Read-only: a single SELECT or WITH ... SELECT — never DELETE/UPDATE/DROP/INSERT/ALTER/CREATE/TRUNCATE.\n"
        "4. Add LIMIT 50 unless the user asks for more or uses aggregates.\n"
        "5. Float casting: PostgreSQL ROUND() requires NUMERIC type. Always write ROUND(expr::NUMERIC, 1).\n"
        "6. Scores in db are 0.0-1.0. To show as 0-10: multiply by 10.\n"
        "7. Join interaction_scores on: interaction_scores.interaction_id = interactions.id\n"
        "8. For ranked lists, add deterministic tie-breaking with a stable secondary key.\n\n"
        "Few-shot examples:\n"
        f"{TEXT_TO_SQL_FEW_SHOT}"
    )


TEXT_TO_SQL_SYSTEM = _build_text_to_sql_system()

EMOTION_SHIFT_SYSTEM = (
    EMOTION_SHIFT_SYSTEM_CORE + "\n\nFew-shot examples:\n" + EMOTION_SHIFT_FEW_SHOT + INJECTION_GUARD
)

PROCESS_ADHERENCE_SYSTEM = (
    PROCESS_ADHERENCE_SYSTEM_CORE
    + "\n\nFew-shot example:\n"
    + PROCESS_ADHERENCE_FEW_SHOT
    + INJECTION_GUARD
)

NLI_POLICY_SYSTEM = (
    NLI_POLICY_SYSTEM_CORE + "\n\nFew-shot examples:\n" + NLI_FEW_SHOT + INJECTION_GUARD
)

JSON_OUTPUT_STAGES = frozenset({"emotion_shift", "process_adherence", "nli_policy", "rag_judge", "fast_classification"})

RAG_JUDGE_SYSTEM = (
    "You are a compliance auditor for a customer-service organization.\n\n"
    "Evaluate whether the agent's actions and statements comply with the company policies.\n"
    "Respond with ONLY valid JSON — no markdown, no explanation outside JSON:\n"
    "{\n"
    '    "compliance_score": <float 0.0 to 1.0>,\n'
    '    "violations": ["violation 1", "violation 2", ...],\n'
    '    "policy_references": ["Policy Section X: Title", ...],\n'
    '    "reasoning": "Brief explanation of your assessment"\n'
    "}"
)

# ── Stage definitions ─────────────────────────────────────────────────────────

FAST_CLASSIFICATION_SYSTEM = (
    "You are a fast call-center query classifier for VocalMind.\n"
    "Given a short customer utterance or manager query fragment, return ONLY valid JSON:\n"
    '{"topic": "<one of: refund_request, billing_issue, technical_support, account_access, '
    'retention, fraud_dispute, fee_adjustment, unknown>", '
    '"is_gibberish": <boolean>}\n\n'
    "Topic hints:\n"
    "- refund_request: refund, credit, chargeback, outage credit\n"
    "- billing_issue: invoice, bill, charge, overcharge\n"
    "- technical_support: internet, router, speed, connectivity\n"
    "- account_access: login, password, PIN, 2FA\n"
    "- retention: cancel, downgrade, leave provider\n"
    "- fraud_dispute: unauthorized charge, fraud\n"
    "- fee_adjustment: waive fee, late fee\n"
    "- unknown: cannot classify\n"
    "- is_gibberish: true when text is random characters or meaningless noise"
)

STAGES: dict[str, dict[str, Any]] = {
    "emotion_shift": {
        "description": "Detect sarcasm, passive-aggression, cross-modal emotion contradictions in a call transcript chunk",
        "system_prompt": EMOTION_SHIFT_SYSTEM,
        "typical_input_tokens": 800,
        "typical_output_tokens": 300,
        "pass_threshold": 7,
    },
    "process_adherence": {
        "description": "Compare transcript chunk against SOP resolution graph steps",
        "system_prompt": PROCESS_ADHERENCE_SYSTEM,
        "typical_input_tokens": 1200,
        "typical_output_tokens": 400,
        "pass_threshold": 7,
    },
    "nli_policy": {
        "description": "Classify transcript claim as Entailment / Benign Deviation / Contradiction / Policy Hallucination",
        "system_prompt": NLI_POLICY_SYSTEM,
        "typical_input_tokens": 1000,
        "typical_output_tokens": 200,
        "pass_threshold": 7,
    },
    "rag_judge": {
        "description": "PolicyComplianceEvaluator and AnswerCorrectnessEvaluator judge",
        "system_prompt": RAG_JUDGE_SYSTEM,
        "typical_input_tokens": 600,
        "typical_output_tokens": 150,
        "pass_threshold": 7,
    },
    "text_to_sql": {
        "description": "Convert natural-language manager query into read-only SQL",
        "system_prompt": TEXT_TO_SQL_SYSTEM,
        "typical_input_tokens": 500,
        "typical_output_tokens": 200,
        "pass_threshold": 7,
    },
    "fast_classification": {
        "description": "Topic classification, gibberish detection, query pruning (latency-critical)",
        "system_prompt": FAST_CLASSIFICATION_SYSTEM,
        "typical_input_tokens": 300,
        "typical_output_tokens": 80,
        "pass_threshold": 7,
    },
}

CANDIDATE_MODELS = [
    "ministral-3:8b",
    "ministral-3:14b",
    "gpt-oss:20b",
    "gemma3:12b",
    "kimi-k2.5:cloud",
    "kimi-k2.6:cloud",
    "qwen3.5:cloud",
    "deepseek-v3.1:671b",
]

REFERENCE_PRICES = {
    "groq": {
        "llama-3.1-8b": {"input": 0.05, "output": 0.08},
        "llama-3.3-70b": {"input": 0.59, "output": 0.79},
        "kimi-k2": {"input": 1.00, "output": 3.00},
        "mixtral-8x7b": {"input": 0.24, "output": 0.24},
    },
    "openai": {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    },
    "ollama_cloud_plans": {
        "pro": {"monthly_usd": 20, "concurrent_models": 3},
        "max": {"monthly_usd": 100, "concurrent_models": 10},
    },
}

COST_EXPLANATION = """Ollama Cloud does not publish per-token prices — it bills on GPU time consumed,
which depends on model size (usage level 1–4) and request duration.
We therefore show two cost columns:
  - groq_equivalent_usd: what the same token volume would cost on Groq for the
    nearest equivalent model family. Use this to sanity-check token efficiency.
  - openai_equivalent_usd: same calculation against gpt-4o-mini as a market anchor.
To convert to Ollama Cloud subscription cost: divide your Pro/Max plan monthly fee
by your estimated monthly call count. VocalMind's 3-chain trigger runs ~24 LLM
calls per interaction (3 chains × ~8 windows). At 500 interactions/month that is
~12,000 calls/month → $0.0017/call on Pro, $0.0083/call on Max."""

JUDGE_PROMPTS = {
    "emotion_shift": """
You are evaluating an LLM response for a call-center emotion analysis task.
Score from 0–10 using this rubric:
  10 — Correctly identifies ALL emotion shifts listed in the reference; provides
       a specific transcript quote as evidence; correctly classifies the type
       (sarcasm / passive-aggression / cross-modal contradiction).
   7 — Identifies the main shift; evidence quote present; minor classification error.
   4 — Identifies the shift but provides no evidence quote or wrong type.
   1 — Misses the shift entirely or fabricates one not in the transcript.
   0 — Refusal, empty response, or incoherent output.

Reference answer: {reference_answer}
Criteria: {scoring_criteria}
Model response to evaluate: {response}

Return JSON: {{"score": <int>, "pass": <bool>, "reasoning": "<one sentence>"}}
""",
    "process_adherence": """
Score 0–10:
  10 — Correctly lists ALL missing SOP steps from the reference; steps named
       exactly match RESOLUTION_GRAPH labels; no hallucinated steps added.
   7 — Lists most missing steps; one hallucination or missing step.
   4 — Partially correct; more than one error.
   0 — Completely wrong or empty.

Reference answer: {reference_answer}
Model response: {response}
Return JSON: {{"score": <int>, "pass": <bool>, "reasoning": "<one sentence>"}}
""",
    "nli_policy": """
Score 0–10:
  10 — Correct verdict label (Entailment/Benign Deviation/Contradiction/Policy Hallucination)
       AND a supporting evidence span quoted from the transcript.
   7 — Correct label; no span quoted.
   3 — Wrong label but reasoning is coherent.
   0 — Wrong label and incoherent reasoning or empty.

Reference answer: {reference_answer}
Model response: {response}
Return JSON: {{"score": <int>, "pass": <bool>, "reasoning": "<one sentence>"}}
""",
    "rag_judge": """
Score 0–10:
  10 — Compliance verdict matches reference; cited policy document matches reference.
   7 — Verdict correct; wrong document cited OR reference lists extra violation detail not in model output.
   3 — Verdict wrong but reasoning references correct policy domain.
   0 — Verdict wrong and reasoning is hallucinated or empty.

IMPORTANT — model output format:
The candidate returns JSON with compliance_score (0.0–1.0), violations[], policy_references[], reasoning.
It does NOT return a text verdict string. Derive the verdict from compliance_score:
  >= 0.8  → Compliant
  0.4–0.79 → Partially compliant (treat as Non-compliant if reference says Non-compliant)
  < 0.4   → Non-compliant
If a "Derived verdict" line is present below, use it as the model's verdict.

Policy document match: same rule ID (e.g. FIN-RULE-001, CS-RULE-008) in policy_references
counts as a match even if formatting differs (with/without section title).

Reference answer: {reference_answer}
Model response to evaluate: {response}
Return JSON: {{"score": <int>, "pass": <bool>, "reasoning": "<one sentence>"}}
""",
    "text_to_sql": """
Score 0–10:
  10 — SQL is syntactically valid, read-only, targets correct tables/columns per reference.
   7 — Correct tables and columns; minor syntax issue or unnecessary JOIN.
   3 — Wrong table or column but correct query structure.
   0 — INSERT/UPDATE/DELETE present, empty, or completely wrong tables.

IMPORTANT: A `WITH ... SELECT` CTE is read-only SELECT, NOT a write operation.
Example valid CTE:
  WITH ranked AS (SELECT u.name, AVG(s.overall_score) AS avg FROM users u JOIN interaction_scores s ON s.interaction_id = i.id GROUP BY u.name)
  SELECT * FROM ranked ORDER BY avg DESC LIMIT 5;
Do NOT penalize WITH ... SELECT as INSERT/UPDATE/DELETE.

Reference answer: {reference_answer}
Model response: {response}
Return JSON: {{"score": <int>, "pass": <bool>, "reasoning": "<one sentence>"}}
""",
    "fast_classification": """
Score 0–10 based ONLY on label correctness (ignore latency completely):
  10 — Correct topic label AND correct is_gibberish flag.
   5 — Exactly one of topic or is_gibberish is correct.
   0 — Both wrong, empty, or refusal.

Reference answer: {reference_answer}
Model response: {response}
Return JSON: {{"score": <int>, "pass": <bool>, "reasoning": "<one sentence>"}}
""",
}


def _groq_price_key(model: str) -> str:
    fast_markers = ("ministral", "gemma", "gpt-oss", "8b", "12b", "20b")
    if any(m in model.lower() for m in fast_markers):
        return "llama-3.1-8b"
    if "kimi" in model.lower():
        return "kimi-k2"
    return "llama-3.3-70b"


def _estimate_costs(
    prompt_tokens: int,
    completion_tokens: int,
    model: str,
) -> tuple[float, float]:
    groq_key = _groq_price_key(model)
    groq_prices = REFERENCE_PRICES["groq"][groq_key]
    openai_prices = REFERENCE_PRICES["openai"]["gpt-4o-mini"]
    groq_cost = (prompt_tokens / 1_000_000 * groq_prices["input"]) + (
        completion_tokens / 1_000_000 * groq_prices["output"]
    )
    openai_cost = (prompt_tokens / 1_000_000 * openai_prices["input"]) + (
        completion_tokens / 1_000_000 * openai_prices["output"]
    )
    return groq_cost, openai_cost


def _derive_compliance_verdict(score: float) -> str:
    if score >= 0.8:
        return "Compliant"
    if score >= 0.4:
        return "Partially compliant"
    return "Non-compliant"


def _normalize_rag_response_for_judge(response: str) -> str:
    """Map compliance_score JSON to an explicit verdict for the judge rubric."""
    stripped = _strip_code_fences(response)
    start = stripped.find("{")
    end = stripped.rfind("}") + 1
    if start < 0 or end <= start:
        return stripped
    try:
        data = json.loads(stripped[start:end])
    except json.JSONDecodeError:
        return stripped
    try:
        score = float(data.get("compliance_score", -1))
    except (TypeError, ValueError):
        return stripped
    if score < 0:
        return stripped
    refs = data.get("policy_references") or []
    violations = data.get("violations") or []
    verdict = _derive_compliance_verdict(score)
    return (
        f"Derived verdict: {verdict} (compliance_score={score}). "
        f"policy_references={refs}. violations={violations}.\n\n"
        f"Original model JSON:\n{stripped}"
    )


def _parse_judge_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if "```" in text:
        for part in text.split("```"):
            cleaned = part.strip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
            if cleaned.startswith("{"):
                text = cleaned
                break
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        raise ValueError(f"Judge returned non-JSON: {content[:200]}")
    blob = text[start:end]
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        fixed = re.sub(r"\bTrue\b", "true", blob)
        fixed = re.sub(r"\bFalse\b", "false", fixed)
        fixed = re.sub(r"\bNone\b", "null", fixed)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Judge JSON parse failed: {exc}; raw={content[:200]}") from exc


def call_ollama_cloud(
    *,
    model: str,
    system: str,
    user: str,
    api_key: str,
    base_url: str = "https://ollama.com/v1",
    stream: bool = True,
    timeout: float = 120.0,
    json_mode: bool = False,
) -> dict[str, Any]:
    """Call Ollama Cloud OpenAI-compatible chat completions API."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "stream": stream,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    t0 = time.perf_counter()
    ttft_ms: float | None = None
    chunks: list[str] = []
    prompt_tokens = 0
    completion_tokens = 0

    with httpx.Client(timeout=timeout) as client:
        if stream:
            def _do_stream() -> dict[str, Any]:
                nonlocal ttft_ms, prompt_tokens, completion_tokens
                local_chunks: list[str] = []
                with client.stream("POST", url, headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
                        usage = data.get("usage")
                        if usage:
                            prompt_tokens = int(usage.get("prompt_tokens") or prompt_tokens)
                            completion_tokens = int(usage.get("completion_tokens") or completion_tokens)
                        delta = (data.get("choices") or [{}])[0].get("delta") or {}
                        piece = delta.get("content") or ""
                        if piece:
                            if ttft_ms is None:
                                ttft_ms = (time.perf_counter() - t0) * 1000
                            local_chunks.append(piece)
                return {"chunks": local_chunks}

            out = _call_with_retry(_do_stream)
            chunks = out["chunks"]
        else:
            def _do_post() -> dict[str, Any]:
                resp = client.post(url, headers=headers, json={**payload, "stream": False})
                resp.raise_for_status()
                return resp.json()

            data = _call_with_retry(_do_post)
            usage = data.get("usage") or {}
            prompt_tokens = int(usage.get("prompt_tokens") or 0)
            completion_tokens = int(usage.get("completion_tokens") or 0)
            message = (data.get("choices") or [{}])[0].get("message") or {}
            chunks.append(message.get("content") or "")
            ttft_ms = (time.perf_counter() - t0) * 1000

    total_ms = (time.perf_counter() - t0) * 1000
    raw = "".join(chunks).strip()

    if prompt_tokens == 0 and completion_tokens == 0:
        prompt_tokens = max(1, len(system.split()) + len(user.split()))
        completion_tokens = max(1, len(raw.split()))

    return {
        "raw_response": raw,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "time_to_first_token_ms": ttft_ms or total_ms,
        "total_latency_ms": total_ms,
    }


def _load_model_triage() -> dict[str, list[str]]:
    data = json.loads(TRIAGE_PATH.read_text(encoding="utf-8"))
    return data["stage_models"]


def _obs_key(row: dict[str, Any]) -> tuple[str, str, str, int]:
    return (row["stage"], row["model"], row["sample_id"], int(row.get("repeat", 0)))


def _load_stage_results(path: str) -> list[dict[str, Any]]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    # Support checkpoint JSONL files in addition to JSON outputs.
    if p.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return data
    return data.get("results", data.get("rows", []))


def _load_retry_error_keys(path: str) -> set[tuple[str, str, str, int]]:
    return {_obs_key(r) for r in _load_stage_results(path) if r.get("error")}


def _merge_retry_results(prior_path: str, new_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {_obs_key(r): r for r in _load_stage_results(prior_path)}
    for row in new_rows:
        merged[_obs_key(row)] = row
    return list(merged.values())


def _error_label(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429:
        return "rate_limited_exhausted"
    msg = str(exc)
    if "429 Too Many Requests" in msg or ("429" in msg and "Too Many Requests" in msg):
        return "rate_limited_exhausted"
    return msg


def _load_reuse_responses(path: str) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Index prior benchmark rows by (stage, model, sample_id)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in data.get("results", []):
        key = (row["stage"], row["model"], row["sample_id"])
        index[key] = row
    return index


def judge_response(
    *,
    stage: str,
    response: str,
    reference: str,
    criteria: str,
    latency_ms: float,
    judge_model: str,
    judge_api_key: str,
    judge_base_url: str,
    pass_threshold: int,
) -> dict[str, Any]:
    normalized = _strip_code_fences(response)
    if stage == "rag_judge":
        normalized = _normalize_rag_response_for_judge(response)
    if stage == "text_to_sql" and not normalized.strip():
        return {
            "judge_score_0_to_10": 0.0,
            "judge_pass": False,
            "judge_reasoning": "Empty SQL response (skipped judge).",
        }

    template = JUDGE_PROMPTS[stage]
    format_kwargs: dict[str, str] = {
        "reference_answer": reference,
        "scoring_criteria": criteria,
        "response": normalized,
    }
    if "{latency_ms}" in template:
        format_kwargs["latency_ms"] = f"{latency_ms:.1f}"
    prompt = template.format(**format_kwargs)
    url = f"{judge_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {judge_api_key}",
        "Content-Type": "application/json",
    }
    strict_suffix = (
        "\n\nReturn ONLY a single JSON object with keys score, pass, reasoning. "
        "Use JSON literals true/false (not Python True/False)."
    )
    last_error = ""
    last_content = ""
    for attempt in range(2):
        user_prompt = prompt if attempt == 0 else prompt + strict_suffix
        payload = {
            "model": judge_model,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        with httpx.Client(timeout=60.0) as client:
            def _judge_post() -> dict[str, Any]:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()

            data = _call_with_retry(_judge_post)
        last_content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        try:
            parsed = _parse_judge_json(last_content)
            score = float(parsed.get("score", 0))
            passed = bool(parsed.get("pass", score >= pass_threshold))
            return {
                "judge_score_0_to_10": score,
                "judge_pass": passed,
                "judge_reasoning": str(parsed.get("reasoning", "")),
            }
        except ValueError as exc:
            last_error = str(exc)
            print(f"  judge parse retry {attempt + 1}: {last_error[:120]}", flush=True)

    return {
        "judge_score_0_to_10": None,
        "judge_pass": False,
        "judge_reasoning": f"judge_parse_failed: {last_error}",
        "judge_raw_response": last_content[:500],
        "error": "judge_parse_failed",
    }


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (p / 100.0)
    f = int(math.floor(k))
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def _checkpoint_path(output: Path) -> Path:
    return output.with_suffix(".checkpoint.jsonl")


def _load_checkpoint(path: Path) -> tuple[set[tuple[str, str, str, int]], list[dict[str, Any]]]:
    done: set[tuple[str, str, str, int]] = set()
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return done, rows
    skipped = 0
    by_key: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        key = (row["stage"], row["model"], row["sample_id"], int(row.get("repeat", 0)))
        by_key[key] = row  # last write wins for duplicate keys
    if skipped:
        print(f"Checkpoint {path.name}: skipped {skipped} corrupt line(s)", flush=True)
    rows = list(by_key.values())
    done = set(by_key.keys())
    return done, rows


def _append_checkpoint(path: Path, row: dict[str, Any], lock: threading.Lock) -> None:
    with lock:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _aggregate_results(results: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, float]]]:
    buckets: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in results:
        buckets[row["stage"]][row["model"]].append(row)

    summary: dict[str, dict[str, dict[str, float]]] = {}
    for stage, models in buckets.items():
        summary[stage] = {}
        for model, rows in models.items():
            n = len(rows)
            n_scored = sum(1 for r in rows if r.get("judge_score_0_to_10") is not None)
            score_sum = sum(r.get("judge_score_0_to_10", 0.0) for r in rows if r.get("judge_score_0_to_10") is not None)
            latencies = [float(r.get("total_latency_ms", 0.0)) for r in rows]
            scores = [float(r["judge_score_0_to_10"]) for r in rows if r.get("judge_score_0_to_10") is not None]
            # across-repeat stdev: group by sample_id when repeats>1
            repeat_groups: dict[str, list[float]] = defaultdict(list)
            for r in rows:
                if r.get("judge_score_0_to_10") is not None:
                    repeat_groups[r["sample_id"]].append(float(r["judge_score_0_to_10"]))
            repeat_stdevs = []
            for vals in repeat_groups.values():
                if len(vals) > 1:
                    mean = sum(vals) / len(vals)
                    repeat_stdevs.append(math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals)))
            score_stdev = sum(repeat_stdevs) / len(repeat_stdevs) if repeat_stdevs else 0.0
            summary[stage][model] = {
                "avg_score": score_sum / n_scored if n_scored else 0.0,
                "score_mean": score_sum / n_scored if n_scored else 0.0,
                "score_stdev": score_stdev,
                "pass_rate": sum(1 for r in rows if r.get("judge_pass")) / n if n else 0.0,
                "avg_ttft_ms": sum(r.get("time_to_first_token_ms", 0.0) for r in rows) / n if n else 0.0,
                "avg_total_ms": sum(r.get("total_latency_ms", 0.0) for r in rows) / n if n else 0.0,
                "p50_total_latency_ms": _percentile(latencies, 50),
                "p95_total_latency_ms": _percentile(latencies, 95),
                "p99_total_latency_ms": _percentile(latencies, 99),
                "groq_cost_per_1k": sum(r.get("groq_equivalent_cost_usd", 0.0) for r in rows) / n * 1000 if n else 0.0,
                "openai_cost_per_1k": sum(r.get("openai_equivalent_cost_usd", 0.0) for r in rows) / n * 1000 if n else 0.0,
                "error_count": sum(1 for r in rows if r.get("error")),
                "judge_parse_fail_count": sum(1 for r in rows if r.get("error") == "judge_parse_failed"),
                "observation_count": n,
            }
            if stage == "fast_classification":
                summary[stage][model]["latency_sla_200ms_pass_rate"] = sum(
                    1 for r in rows if r.get("total_latency_ms", 9999) <= 200
                ) / n
    return summary


def write_markdown_report(
    path: Path,
    results: list[dict[str, Any]],
    summary: dict[str, dict[str, dict[str, float]]],
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"## VocalMind Ollama Cloud Model Benchmark — {now}",
        "",
        "### Cost methodology",
        COST_EXPLANATION,
        "",
    ]
    for stage in STAGES:
        lines.append(f"### Stage: {stage}")
        lines.append(
            "| Model | Avg Score | Pass Rate | Avg TTFT (ms) | Avg Total (ms) | "
            "Groq Equiv Cost/1k calls | OpenAI Equiv Cost/1k calls |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        stage_rows = summary.get(stage, {})
        for model in sorted(stage_rows, key=lambda m: stage_rows[m]["avg_score"], reverse=True):
            s = stage_rows[model]
            lines.append(
                f"| {model} | {s['avg_score']:.1f} | {s['pass_rate']:.0%} | "
                f"{s['avg_ttft_ms']:.0f}ms | {s['avg_total_ms']:.0f}ms | "
                f"${s['groq_cost_per_1k']:.2f} | ${s['openai_cost_per_1k']:.2f} |"
            )
        lines.append("")

    lines.extend(
        [
            "### Recommendation",
            "Paste this section manually after reviewing results:",
            "- Heavy stages (emotion_shift, process_adherence, nli_policy): use ___________",
            "- Fast stages (fast_classification): use ___________",
            "- RAG judge: use ___________",
            "- Embeddings: use ___________",
            "",
            f"Total benchmark rows: {len(results)}",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _process_model_sample(
    *,
    model: str,
    stage_name: str,
    stage_cfg: dict[str, Any],
    sample: dict[str, Any],
    sample_id: str,
    reuse_row: dict[str, Any] | None,
    ollama_key: str,
    ollama_base_url: str,
    judge_model: str,
    judge_key: str,
    judge_base_url: str,
    text_to_sql_use_judge: bool = False,
    skip_judge: bool = False,
    repeat: int = 0,
) -> dict[str, Any]:
    mode = "rejudge" if reuse_row else "run"
    rep_tag = f" r{repeat + 1}" if repeat else ""
    print(f"{mode} {stage_name} / {model} / {sample_id}{rep_tag}", flush=True)
    try:
        if reuse_row:
            call = {
                "raw_response": reuse_row.get("raw_response", ""),
                "prompt_tokens": int(reuse_row.get("prompt_tokens") or 0),
                "completion_tokens": int(reuse_row.get("completion_tokens") or 0),
                "time_to_first_token_ms": float(reuse_row.get("time_to_first_token_ms") or 0),
                "total_latency_ms": float(reuse_row.get("total_latency_ms") or 0),
            }
            groq_cost = float(reuse_row.get("groq_equivalent_cost_usd") or 0)
            openai_cost = float(reuse_row.get("openai_equivalent_cost_usd") or 0)
        else:
            user_text = sample["input"]
            if stage_name == "emotion_shift":
                user_text = normalize_emotion_shift_input(user_text)
            elif stage_name == "nli_policy":
                user_text = normalize_nli_input(user_text)
            call = call_ollama_cloud(
                model=model,
                system=stage_cfg["system_prompt"],
                user=user_text,
                api_key=ollama_key,
                base_url=ollama_base_url,
                json_mode=stage_name in JSON_OUTPUT_STAGES,
            )
            groq_cost, openai_cost = _estimate_costs(
                call["prompt_tokens"], call["completion_tokens"], model
            )
        if skip_judge and stage_name != "text_to_sql":
            judged = {
                "judge_score_0_to_10": None,
                "judge_pass": False,
                "judge_reasoning": "judge skipped (--skip-judge)",
            }
        elif stage_name == "text_to_sql" and not text_to_sql_use_judge:
            judged = score_sql_execution(call["raw_response"], sample["reference_answer"])
        else:
            judged = judge_response(
                stage=stage_name,
                response=call["raw_response"],
                reference=sample["reference_answer"],
                criteria=sample.get("scoring_criteria", ""),
                latency_ms=call["total_latency_ms"],
                judge_model=judge_model,
                judge_api_key=judge_key,
                judge_base_url=judge_base_url,
                pass_threshold=stage_cfg["pass_threshold"],
            )
        return {
            "model": model,
            "stage": stage_name,
            "sample_id": sample_id,
            "repeat": repeat,
            "prompt_tokens": call["prompt_tokens"],
            "completion_tokens": call["completion_tokens"],
            "time_to_first_token_ms": call["time_to_first_token_ms"],
            "total_latency_ms": call["total_latency_ms"],
            "raw_response": call["raw_response"],
            "groq_equivalent_cost_usd": groq_cost,
            "openai_equivalent_cost_usd": openai_cost,
            "reused_response": bool(reuse_row),
            **judged,
        }
    except Exception as exc:
        err = _error_label(exc)
        print(f"  ERROR {stage_name}/{model}/{sample_id}: {exc}", flush=True)
        return {
            "model": model,
            "stage": stage_name,
            "sample_id": sample_id,
            "repeat": repeat,
            "error": err,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "time_to_first_token_ms": 0.0,
            "total_latency_ms": 0.0,
            "groq_equivalent_cost_usd": 0.0,
            "openai_equivalent_cost_usd": 0.0,
            "judge_score_0_to_10": 0.0,
            "judge_pass": False,
            "judge_reasoning": str(exc),
        }


def run_benchmark(args: argparse.Namespace, output_path: Path | None = None) -> list[dict[str, Any]]:
    global _ACTIVE_RATE_LIMITER, _ACTIVE_MAX_RETRIES
    rpm = float(getattr(args, "max_requests_per_minute", 20))
    _ACTIVE_MAX_RETRIES = max(1, int(getattr(args, "max_retries", 5)))
    _ACTIVE_RATE_LIMITER = RateLimiter(rpm) if rpm > 0 else None
    if _ACTIVE_RATE_LIMITER:
        print(f"Rate limit: {rpm:.0f} requests/min, max retries={_ACTIVE_MAX_RETRIES}", flush=True)

    ground_truth = json.loads(Path(args.ground_truth).read_text(encoding="utf-8"))
    judge_key = (
        args.judge_api_key
        or os.environ.get("OPENAI_API_KEY", "")
        or os.environ.get("OLLAMA_CLOUD_API_KEY", "")
        or os.environ.get("OLLAMA_API_KEY", "")
    )
    ollama_key = (
        args.ollama_cloud_key
        or os.environ.get("OLLAMA_CLOUD_API_KEY", "")
        or os.environ.get("OLLAMA_API_KEY", "")
    )

    stage_filter = {s.strip() for s in args.stages.split(",") if s.strip()} if args.stages else None
    max_samples = int(getattr(args, "max_samples", 0) or 0)
    retry_from = getattr(args, "retry_errors_from", "") or ""
    retry_keys: set[tuple[str, str, str, int]] | None = None
    if retry_from:
        retry_keys = _load_retry_error_keys(retry_from)
        print(f"Retry-errors-from {retry_from}: {len(retry_keys)} error observation(s)", flush=True)

    reuse_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    if args.reuse_responses_from:
        reuse_index = _load_reuse_responses(args.reuse_responses_from)

    if args.dry_run:
        print("Dry run: validating ground truth structure only.")
        for stage in STAGES:
            if stage_filter and stage not in stage_filter:
                continue
            samples = ground_truth.get(stage, [])
            print(f"  {stage}: {len(samples)} samples")
        return []

    if not ollama_key:
        raise SystemExit("OLLAMA_API_KEY is required (pass --ollama-cloud-key or set env var).")
    if not judge_key and not getattr(args, "skip_judge", False):
        raise SystemExit("Judge API key required (--judge-api-key or OPENAI_API_KEY/OLLAMA_API_KEY).")

    default_models = [m.strip() for m in args.models.split(",") if m.strip()] if args.models else CANDIDATE_MODELS
    stage_triage = _load_model_triage() if getattr(args, "use_model_triage", False) else None
    parallel_models = not getattr(args, "serial_models", False)
    text_to_sql_use_judge = getattr(args, "text_to_sql_use_judge", False)
    skip_judge = getattr(args, "skip_judge", False)
    repeats = max(1, int(getattr(args, "repeats", 1)))
    checkpoint_lock = threading.Lock()
    done_keys: set[tuple[str, str, str, int]] = set()
    results: list[dict[str, Any]] = []
    ckpt_path: Path | None = None
    if output_path:
        ckpt_path = _checkpoint_path(output_path)
        done_keys, results = _load_checkpoint(ckpt_path)
        if retry_keys:
            done_keys -= retry_keys
            results = [r for r in results if _obs_key(r) not in retry_keys]
            print(f"Cleared {len(retry_keys)} error key(s) from checkpoint for retry", flush=True)
        if done_keys:
            print(f"Resuming from checkpoint: {len(done_keys)} observations already done", flush=True)

    total_tasks = 0
    pending_tasks = 0
    for stage_name in STAGES:
        if stage_filter and stage_name not in stage_filter:
            continue
        samples = ground_truth.get(stage_name, [])
        if max_samples > 0:
            samples = samples[:max_samples]
        models_n = len(stage_triage.get(stage_name, default_models) if stage_triage else default_models)
        if retry_keys:
            stage_retry = {k for k in retry_keys if k[0] == stage_name}
            total_tasks += len(stage_retry)
        else:
            total_tasks += len(samples) * models_n * repeats
    pending_tasks = total_tasks - len(done_keys)
    if ckpt_path and pending_tasks < total_tasks:
        print(f"Checkpoint progress: {len(done_keys)}/{total_tasks} observations", flush=True)

    for stage_name, stage_cfg in STAGES.items():
        if stage_filter and stage_name not in stage_filter:
            continue
        samples = ground_truth.get(stage_name, [])
        if max_samples > 0:
            samples = samples[:max_samples]
        if not samples:
            print(f"Warning: no ground-truth samples for stage {stage_name}")
            continue
        if stage_triage:
            models_sorted = sorted(stage_triage.get(stage_name, default_models))
        else:
            models_sorted = sorted(default_models)
        max_workers = min(5, len(models_sorted)) if parallel_models else 1
        reuse_ids = REUSE_RESPONSE_SAMPLES.get(stage_name, frozenset())

        for sample in samples:
            sample_id = sample.get("sample_id", "")

            for repeat_idx in range(repeats):
                def _task(model: str, _repeat: int = repeat_idx) -> dict[str, Any] | None:
                    key = (stage_name, model, sample_id, _repeat)
                    if retry_keys is not None and key not in retry_keys:
                        return None
                    if key in done_keys:
                        return None
                    reuse_key = (stage_name, model, sample_id)
                    reuse_row = reuse_index.get(reuse_key) if sample_id in reuse_ids and _repeat == 0 else None
                    row = _process_model_sample(
                        model=model,
                        stage_name=stage_name,
                        stage_cfg=stage_cfg,
                        sample=sample,
                        sample_id=sample_id,
                        reuse_row=reuse_row,
                        ollama_key=ollama_key,
                        ollama_base_url=args.ollama_base_url,
                        judge_model=args.judge_model,
                        judge_key=judge_key,
                        judge_base_url=args.judge_base_url,
                        text_to_sql_use_judge=text_to_sql_use_judge,
                        skip_judge=skip_judge,
                        repeat=_repeat,
                    )
                    if ckpt_path:
                        _append_checkpoint(ckpt_path, row, checkpoint_lock)
                    return row

                if parallel_models and len(models_sorted) > 1:
                    rows_by_model: dict[str, dict[str, Any] | None] = {}
                    with ThreadPoolExecutor(max_workers=max_workers) as pool:
                        futures = {pool.submit(_task, model): model for model in models_sorted}
                        for fut in as_completed(futures):
                            model = futures[fut]
                            rows_by_model[model] = fut.result()
                    for model in models_sorted:
                        row = rows_by_model[model]
                        if row is not None:
                            results.append(row)
                            done_keys.add((stage_name, model, sample_id, repeat_idx))
                else:
                    for model in models_sorted:
                        row = _task(model)
                        if row is not None:
                            results.append(row)
                            done_keys.add((stage_name, model, sample_id, repeat_idx))

    # Re-load full checkpoint for consistent ordering on resume
    if ckpt_path and ckpt_path.exists():
        _, results = _load_checkpoint(ckpt_path)
    if retry_from:
        results = _merge_retry_results(retry_from, results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Ollama Cloud models for VocalMind stages.")
    parser.add_argument(
        "--ground-truth",
        default=str(ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth.json"),
    )
    parser.add_argument("--output", default="")
    parser.add_argument("--ollama-cloud-key", default="")
    parser.add_argument("--ollama-base-url", default="https://ollama.com/v1")
    parser.add_argument("--judge-model", default="gpt-4o-mini")
    parser.add_argument("--judge-api-key", default="")
    parser.add_argument("--judge-base-url", default="https://api.openai.com/v1")
    parser.add_argument("--models", default="", help="Comma-separated model list override")
    parser.add_argument("--stages", default="", help="Comma-separated stage filter")
    parser.add_argument(
        "--reuse-responses-from",
        default="",
        help="Prior benchmark JSON; reuse raw_response for REUSE_RESPONSE_SAMPLES (re-judge only)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without API calls")
    parser.add_argument(
        "--serial-models",
        action="store_true",
        help="Call models sequentially per sample (default: parallel ThreadPoolExecutor)",
    )
    parser.add_argument(
        "--use-model-triage",
        action="store_true",
        help="Use per-stage model lists from infra/benchmarks/model_triage_v1.json",
    )
    parser.add_argument(
        "--text-to-sql-use-judge",
        action="store_true",
        help="Use LLM judge for text_to_sql instead of DB execution comparison (debug fallback)",
    )
    parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Skip LLM judge calls (use with ground-truth re-scoring only)",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of repeat runs per (sample, model) for latency/score variance (default 1)",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=0,
        help="Cap samples per stage (0 = all). Useful for probe runs.",
    )
    parser.add_argument(
        "--max-requests-per-minute",
        type=float,
        default=20.0,
        help="Global rate limit for model+judge API calls (default 20/min, 0=off)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=5,
        help="Max retries on 429/5xx with exponential backoff (default 5)",
    )
    parser.add_argument(
        "--retry-errors-from",
        default="",
        help="Prior stage JSON; re-run only rows with error set, merge back in",
    )
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = Path(args.output) if args.output else REPORTS_DIR / f"ollama_cloud_benchmark_{ts}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)

    results = run_benchmark(args, output_path=json_path)
    if args.dry_run:
        return

    models = args.models.split(",") if args.models else CANDIDATE_MODELS
    stage_list = [s.strip() for s in args.stages.split(",") if s.strip()] if args.stages else list(STAGES.keys())
    md_path = json_path.with_suffix(".md")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stages": stage_list,
        "candidate_models": models,
        "judge_model": args.judge_model,
        "judge_base_url": args.judge_base_url,
        "repeats": args.repeats,
        "reuse_responses_from": args.reuse_responses_from or None,
        "reference_prices": REFERENCE_PRICES,
        "cost_explanation": COST_EXPLANATION,
        "results": results,
        "summary": _aggregate_results(results),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown_report(md_path, results, payload["summary"])
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
