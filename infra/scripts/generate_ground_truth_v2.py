#!/usr/bin/env python3
"""Expand ground truth with category balance, scenario diversity, and noisy ASR variants."""
from __future__ import annotations

import argparse
import difflib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

import generate_ground_truth as gt  # noqa: E402

V1_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth.json"
V2_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"

NOISY_STAGES = ("emotion_shift", "process_adherence", "nli_policy", "rag_judge")
NOISY_COUNT = 50

LABEL_TARGETS = {
    "nli_policy": {
        "Entailment": 30,
        "Benign Deviation": 30,
        "Contradiction": 30,
        "Policy Hallucination": 30,
    },
    "emotion_shift": {
        "sarcasm": 30,
        "passive_aggression": 30,
        "cross_modal": 30,
        "none": 30,
    },
}

FC_TOPIC_MIN = 15
FC_GIBBERISH_RATIO = 0.20
FC_AMBIGUOUS_RATIO = 0.10
PA_BUCKET_MIN = 25

EXTRA_SCENARIOS = (
    "loyalty_retention_offer",
    "supervisor_escalation",
    "multi_issue_call",
    "plan_change",
    "fraud_investigation_deep",
    "equipment_replacement",
    "payment_arrangement",
    "service_restoration",
)

HOMOPHONES = (
    ("their", "there"),
    ("to", "too"),
    ("two", "to"),
    ("your", "you're"),
    ("its", "it's"),
    ("then", "than"),
    ("accept", "except"),
)

FILLERS = ("um", "uh", "like", "you know", "so")
CROSSTALK = ("[overlapping speech]", "[inaudible]")
ACCENT_PHRASES = (
    "I am needing help with",
    "Please can you checking",
    "The bill it went up too much",
    "I no understand this charge",
)


def _label_of(sample: dict, stage: str) -> str | None:
    if "_label" in sample:
        return sample["_label"]
    if stage == "nli_policy":
        m = re.search(r"Verdict:\s*([^.]+)", sample.get("reference_answer", ""))
        return m.group(1).strip() if m else None
    if stage == "emotion_shift":
        ref = sample.get("reference_answer", "")
        if "sarcasm" in ref.lower():
            return "sarcasm"
        if "passive" in ref.lower():
            return "passive_aggression"
        if "cross-modal" in ref.lower():
            return "cross_modal"
        if "no cross-modal" in ref.lower() or "true negative" in sample.get("scoring_criteria", "").lower():
            return "none"
    if stage == "fast_classification":
        m = re.search(r"topic:\s*(\w+)", sample.get("reference_answer", ""))
        return m.group(1) if m else None
    return None


def _pa_bucket(sample: dict) -> int:
    missing = sample.get("_missing")
    if missing is not None:
        return min(len(missing), 3) if len(missing) < 3 else 3
    ref = sample.get("reference_answer", "")
    if "No missing" in ref:
        return 0
    m = re.search(r"\[(.*?)\]", ref)
    if not m:
        return 0
    items = [x.strip() for x in m.group(1).split(",") if x.strip()]
    n = len(items)
    return 3 if n >= 3 else n


def _inject_asr(text: str, rng: random.Random) -> str:
    out = text
    for a, b in rng.sample(HOMOPHONES, k=min(2, len(HOMOPHONES))):
        if a in out.lower() and rng.random() < 0.4:
            out = re.sub(rf"\b{a}\b", b, out, count=1, flags=re.IGNORECASE)
    if rng.random() < 0.35:
        filler = rng.choice(FILLERS)
        out = out.replace(": ", f": {filler}, ", 1)
    if rng.random() < 0.25:
        words = out.split()
        if len(words) > 8:
            drop = rng.choice(["the", "a", "an", "to"])
            out = " ".join(w for w in words if w.lower() != drop or rng.random() > 0.5)
    if rng.random() < 0.2:
        out = re.sub(r"\b(I|we|you)\b", r"\1 \1", out, count=1, flags=re.IGNORECASE)
    if rng.random() < 0.15:
        lines = out.split("\n")
        for i, ln in enumerate(lines):
            if ln.strip().startswith(("Customer", "Agent")) and rng.random() < 0.3:
                lines[i] = ln.rstrip(".") + " and also I wanted to mention the account thing"
                break
        out = "\n".join(lines)
    return out


def _inject_crosstalk(text: str, rng: random.Random) -> str:
    lines = text.split("\n")
    turn_idxs = [i for i, ln in enumerate(lines) if re.match(r"^\d+\.", ln.strip()) or "Turn" in ln[:20]]
    if not turn_idxs:
        turn_idxs = list(range(min(3, len(lines))))
    for idx in rng.sample(turn_idxs, k=min(2, len(turn_idxs))):
        tag = rng.choice(CROSSTALK)
        lines[idx] = lines[idx] + f" {tag}"
    return "\n".join(lines)


def _inject_truncation(text: str, rng: random.Random) -> str:
    lines = text.split("\n")
    candidates = [i for i, ln in enumerate(lines) if "Customer" in ln or "Agent" in ln]
    if not candidates:
        return text
    idx = rng.choice(candidates)
    words = lines[idx].split()
    if len(words) > 6:
        lines[idx] = " ".join(words[: rng.randint(4, 7)]) + "—"
    return "\n".join(lines)


def _inject_accent(text: str, rng: random.Random) -> str:
    phrase = rng.choice(ACCENT_PHRASES)
    return text.replace("I need help", phrase, 1) if "I need help" in text else text + f"\nCustomer note: {phrase}."


def _extend_transcript(text: str, rng: random.Random) -> str:
    if "Transcript" not in text and "turns" not in text.lower():
        return text
    extra = []
    for t in range(9, 9 + rng.randint(4, 8)):
        extra.append(
            f"{t}. Agent: Following up on ticket NX-{rng.randint(100000,999999)} — "
            f"step {t - 8} documented."
        )
        extra.append(
            f"{t + 1}. Customer: {'Okay' if rng.random() > 0.5 else 'Right'} — "
            f"what about the ${rng.choice(gt.AMOUNTS)} part?"
        )
        t += 1
    return text + "\n" + "\n".join(extra)


def apply_noise(sample: dict, stage: str, rng: random.Random) -> dict:
    inp = sample["input"]
    inp = _inject_asr(inp, rng)
    if rng.random() < 0.20:
        inp = _inject_crosstalk(inp, rng)
    if rng.random() < 0.10:
        inp = _inject_truncation(inp, rng)
    if rng.random() < 0.25:
        inp = _inject_accent(inp, rng)
    if rng.random() < 0.30:
        inp = _extend_transcript(inp, rng)
    noisy = dict(sample)
    noisy["input"] = inp + "\n\n[noise_tier: asr_simulated]"
    noisy["tier"] = "noisy"
    noisy["source_sample_id"] = sample.get("sample_id")
    noisy["_noise_profile"] = "asr_crosstalk_truncation_accent_longform"
    return noisy


def _count_labels(samples: list[dict], stage: str) -> Counter:
    c: Counter = Counter()
    for s in samples:
        lbl = _label_of(s, stage)
        if lbl:
            c[lbl] += 1
    return c


def _expand_labeled(stage: str, samples: list[dict], rng: random.Random) -> list[dict]:
    targets = LABEL_TARGETS[stage]
    existing = list(samples)
    counts = _count_labels(existing, stage)
    prefix = {"emotion_shift": "es", "nli_policy": "nli"}[stage]
    added: list[dict] = []
    for label, target in targets.items():
        need = max(0, target - counts.get(label, 0))
        if need <= 0:
            continue
        gen_fn = gt.gen_emotion_shift if stage == "emotion_shift" else gt.gen_nli_policy
        batch = gen_fn(existing + added, rng, need)
        for s in batch:
            s["_label"] = label
            if stage == "nli_policy":
                s["reference_answer"] = f"Verdict: {label}."
        added.extend(batch)
    return added


def _expand_process_adherence(samples: list[dict], rng: random.Random) -> list[dict]:
    graphs = gt._load_dict_constant(gt.SERVICE_PY, "RESOLUTION_GRAPHS")
    existing = list(samples)
    buckets: dict[int, list] = defaultdict(list)
    for s in existing:
        buckets[_pa_bucket(s)].append(s)
    added: list[dict] = []
    for bucket in (0, 1, 2, 3):
        need = max(0, PA_BUCKET_MIN - len(buckets[bucket]))
        if need <= 0:
            continue
        start = max((gt._sample_num(s.get("sample_id", ""), "pa") or 0 for s in existing + added), default=0)
        for i in range(need):
            seq = start + i + 1 + bucket * 100
            topic = list(graphs.keys())[(seq + bucket) % len(graphs)]
            steps = graphs[topic]
            missing_count = bucket if bucket < 3 else min(len(steps), 3 + seq % 2)
            missing = [steps[j] for j in range(missing_count) if j < len(steps)]
            present = [s for s in steps if s not in missing]
            ticket = f"NX-{seq:06d}"
            scenario = EXTRA_SCENARIOS[seq % len(EXTRA_SCENARIOS)]
            lines = [
                f"Topic hint: {topic} | Scenario: {scenario.replace('_', ' ')}",
                f"Call reference: {ticket} | Amount: ${gt.AMOUNTS[seq % len(gt.AMOUNTS)]}",
                "Transcript (8 turns):",
                f"Customer: Calling about {scenario.replace('_', ' ')} on account {1000+seq}-{2000+seq}.",
                f"Agent ({gt.AGENT_NAMES[seq % len(gt.AGENT_NAMES)]}): I'll help with {ticket}.",
            ]
            for idx, step in enumerate(present[:4]):
                lines.append(f"Turn {idx + 3} Agent: [completed: {step}]")
            lines.append(f"Customer: Clarifying {scenario} detail {seq}.")
            lines.append(f"Agent: Acknowledged — continuing.")
            lines.append("\nExpected resolution graph steps:")
            lines.extend(f"- {s}" for s in steps)
            ref = (
                f"Missing SOP steps: [{', '.join(missing)}]."
                if missing
                else "No missing SOP steps. Complete adherence."
            )
            sid = gt._next_id("pa", existing + added)
            added.append(
                {
                    "sample_id": sid,
                    "input": "\n".join(lines),
                    "reference_answer": ref,
                    "scoring_criteria": "Must list exact RESOLUTION_GRAPH missing step names",
                    "_topic": topic,
                    "_missing": missing,
                    "_scenario": scenario,
                }
            )
    return added


def _expand_fast_classification(samples: list[dict], rng: random.Random) -> list[dict]:
    existing = list(samples)
    topic_counts = _count_labels(existing, "fast_classification")
    added: list[dict] = []
    for topic in gt.FAST_TOPICS:
        need = max(0, FC_TOPIC_MIN - topic_counts.get(topic, 0))
        if need <= 0:
            continue
        batch = gt.gen_fast_classification(existing + added, rng, need)
        for s in batch:
            s["reference_answer"] = f"topic: {topic}, is_gibberish: false"
        added.extend(batch)
    total = len(existing) + len(added)
    gib_target = int((total + len(added)) * FC_GIBBERISH_RATIO)
    amb_target = int((total + len(added)) * FC_AMBIGUOUS_RATIO)
    gib_have = sum(1 for s in existing + added if "is_gibberish: true" in s.get("reference_answer", ""))
    amb_have = sum(1 for s in existing + added if s.get("_note"))
    for _ in range(max(0, gib_target - gib_have)):
        seq = len(existing) + len(added) + 1
        added.append(
            {
                "sample_id": gt._next_id("fc", existing + added),
                "input": f"asdf qwerty mxnx blah #{seq} zzz",
                "reference_answer": "topic: unknown, is_gibberish: true",
                "scoring_criteria": "topic from reference; is_gibberish flag",
            }
        )
    for _ in range(max(0, amb_target - amb_have)):
        seq = len(existing) + len(added) + 1
        amt = gt.AMOUNTS[seq % len(gt.AMOUNTS)]
        added.append(
            {
                "sample_id": gt._next_id("fc", existing + added),
                "input": f"There's a ${amt} charge on invoice NX-{seq:06d} I don't recognize",
                "reference_answer": "topic: fraud_dispute, is_gibberish: false",
                "scoring_criteria": "topic from reference; is_gibberish flag",
                "_note": "ambiguous, multiple valid labels: billing_issue|fraud_dispute",
            }
        )
    return added


def _make_noisy_variants(stage: str, clean: list[dict], rng: random.Random) -> list[dict]:
    prefix = gt.PREFIX[stage]
    pool = [s for s in clean if s.get("tier") != "noisy"]
    rng.shuffle(pool)
    sources = pool[:NOISY_COUNT]
    noisy: list[dict] = []
    for i, src in enumerate(sources, start=1):
        n = apply_noise(src, stage, rng)
        n["sample_id"] = f"{prefix}_n{i:03d}"
        noisy.append(n)
    return noisy


def build_v2(seed: int = 42) -> dict[str, Any]:
    rng = random.Random(seed)
    base = json.loads(V1_PATH.read_text(encoding="utf-8"))
    out: dict[str, list] = {k: list(v) for k, v in base.items() if isinstance(v, list)}

    for stage in ("emotion_shift", "nli_policy"):
        out[stage].extend(_expand_labeled(stage, out[stage], rng))

    out["process_adherence"].extend(_expand_process_adherence(out["process_adherence"], rng))
    out["fast_classification"].extend(_expand_fast_classification(out["fast_classification"], rng))

    for stage in NOISY_STAGES:
        out[stage].extend(_make_noisy_variants(stage, out[stage], rng))

    # Mark clean tier on originals
    for stage, samples in out.items():
        for s in samples:
            if "tier" not in s:
                s["tier"] = "clean"

    return out


def report_pool(data: dict[str, list]) -> dict[str, Any]:
    rep: dict[str, Any] = {}
    dupes_total = 0
    for stage, samples in data.items():
        clean = [s for s in samples if s.get("tier", "clean") == "clean"]
        noisy = [s for s in samples if s.get("tier") == "noisy"]
        dupes = gt._dedup_check(samples)
        dupes_total += len(dupes)
        entry: dict[str, Any] = {
            "total": len(samples),
            "clean": len(clean),
            "noisy": len(noisy),
            "near_dup_pairs": len(dupes),
        }
        if stage in LABEL_TARGETS:
            entry["per_label"] = dict(_count_labels(clean, stage))
        if stage == "process_adherence":
            buckets = Counter(_pa_bucket(s) for s in clean)
            entry["per_bucket"] = {str(k): buckets[k] for k in sorted(buckets)}
        if stage == "fast_classification":
            topics = _count_labels(clean, stage)
            n = len(clean) or 1
            entry["per_topic"] = dict(topics)
            entry["gibberish_pct"] = round(
                100 * sum(1 for s in clean if "is_gibberish: true" in s.get("reference_answer", "")) / n,
                1,
            )
            entry["ambiguous_pct"] = round(100 * sum(1 for s in clean if s.get("_note")) / n, 1)
        rep[stage] = entry
    rep["grand_total"] = sum(len(v) for v in data.values())
    rep["near_dup_pairs_total"] = dupes_total
    return rep


def main() -> None:
    parser = argparse.ArgumentParser(description="Build industry-grade ground truth v2 pool.")
    parser.add_argument("--output", default=str(V2_PATH))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    if args.report_only and Path(args.output).exists():
        data = json.loads(Path(args.output).read_text(encoding="utf-8"))
    else:
        data = build_v2(seed=args.seed)
        payload = {
            "version": "v2",
            "base": str(V1_PATH.name),
            "generated_by": "generate_ground_truth_v2.py",
            **data,
        }
        Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {args.output}")

    rep = report_pool({k: v for k, v in data.items() if isinstance(v, list)})
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
