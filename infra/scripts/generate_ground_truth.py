#!/usr/bin/env python3
"""Append template-based NexaLink ground-truth samples to ollama_cloud_ground_truth.json."""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import random
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
GT_PATH = ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth.json"
SERVICE_PY = ROOT / "backend" / "app" / "llm_trigger" / "service.py"
ORG_ID = "00000000-0000-0000-0000-000000000001"

TARGETS = {
    "emotion_shift": 100,
    "process_adherence": 100,
    "nli_policy": 100,
    "rag_judge": 100,
    "text_to_sql": 50,
    "fast_classification": 100,
}

# Hand-curated samples from re-audit fixes (preserve these on --reset).
CURATED_MAX_NUM = {
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

FAST_TOPICS = (
    "refund_request",
    "billing_issue",
    "technical_support",
    "account_access",
    "retention",
    "fraud_dispute",
    "fee_adjustment",
    "unknown",
)

AGENT_NAMES = ("Priya", "Daniel", "Marcus", "Aisha", "Jordan", "Elena", "Sam")
CUSTOMER_NAMES = ("Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie")
AMOUNTS = (15, 23, 47, 87, 120, 199, 250)

RAG_POLICY_DOCS = (
    ("FIN-RULE-001", "Refund Policy > Outage Credits", "Outages of 24+ hours qualify for pro-rated credits on the next bill."),
    ("FIN-RULE-010", "Refund Timeline Script", "Credits appear on the next PDF bill within 5 business days."),
    ("CS-RULE-001", "Greeting", "Agents must use the approved NexaLink greeting verbatim."),
    ("CS-RULE-002", "Recording Notice", "Agents must state the call may be recorded."),
    ("CS-RULE-008", "Communication Standards", "Agents must not talk over the customer or use dismissive tone."),
    ("SEC-RULE-008", "Account Security", "After suspected fraud, advise password change and monitor activity."),
)

SCENARIO_TOPICS = (
    "refund_request",
    "billing_dispute",
    "tech_outage",
    "account_access",
    "fraud_investigation",
    "plan_upgrade",
    "cancellation",
    "positive_no_issue",
)


def _load_dict_constant(path: Path, name: str) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            if isinstance(target, ast.Name) and target.id == name:
                return ast.literal_eval(node.value)
    raise RuntimeError(f"{name} not found in {path}")


def _sample_num(sample_id: str, prefix: str) -> int | None:
    m = re.match(rf"{prefix}_(\d+)", sample_id)
    return int(m.group(1)) if m else None


def _next_id(prefix: str, existing: list[dict]) -> str:
    nums = [_sample_num(s.get("sample_id", ""), prefix) or 0 for s in existing]
    return f"{prefix}_{max(nums, default=0) + 1:03d}"


def _too_similar(candidate: str, existing: list[dict], threshold: float = 0.8) -> bool:
    for s in existing:
        if difflib.SequenceMatcher(None, candidate, s.get("input", "")).ratio() >= threshold:
            return True
    return False


def _dedup_check(samples: list[dict], threshold: float = 0.8) -> list[tuple[str, str, float]]:
    dupes: list[tuple[str, str, float]] = []
    for i, a in enumerate(samples):
        ta = a.get("input", "")
        for b in samples[i + 1 :]:
            ratio = difflib.SequenceMatcher(None, ta, b.get("input", "")).ratio()
            if ratio >= threshold:
                dupes.append((a.get("sample_id", "?"), b.get("sample_id", "?"), ratio))
    return dupes


def _generate_batch(
    existing: list[dict],
    prefix: str,
    factory: Callable[[int], dict[str, Any]],
    n: int,
) -> list[dict]:
    start = max((_sample_num(s.get("sample_id", ""), prefix) or 0 for s in existing), default=0)
    out: list[dict] = []
    for i in range(n):
        sample = factory(start + i + 1)
        sample["sample_id"] = f"{prefix}_{start + i + 1:03d}"
        out.append(sample)
    return out


def _ticket(rng: random.Random) -> str:
    return f"NX-{rng.randint(100000, 999999)}"


def _account(rng: random.Random) -> str:
    return f"{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}-{rng.randint(10, 99)}"


def _eight_turn(
    seq: int,
    scenario: str,
    agent: str,
    customer: str,
    shift_turn: int | None,
    shift_type: str | None,
) -> str:
    amount = AMOUNTS[seq % len(AMOUNTS)]
    ticket = f"NX-{seq:06d}"
    acct = f"{1000 + seq % 8999}-{2000 + seq % 8999}-{10 + seq % 89}"
    lines = [
        f"Agent ({agent}): Thank you for calling NexaLink, this is {agent}. How can I help?",
        f"Customer ({customer}): I'm calling about {scenario.replace('_', ' ')} — ticket {ticket}.",
        f"Agent: I understand. Can I verify account {acct}?",
        f"Customer: Sure, that's the account on file since {2018 + seq % 7}.",
        f"Agent: Thanks. I see a ${amount} line item from {(seq % 28) + 1} days ago.",
        f"Customer: That's the part I need help with on case {seq}.",
        f"Agent: Let me walk through our policy for {scenario.replace('_', ' ')}.",
        f"Customer: What can you do for me today on ref {seq * 13}?",
    ]
    if shift_turn and shift_type == "sarcasm":
        lines[shift_turn - 1] = (
            f"Customer: Oh wonderful — another ${amount} surprise on ticket {ticket}. Best service ever."
        )
    elif shift_turn and shift_type == "passive_aggression":
        lines[shift_turn - 1] = (
            f"Agent: Well, if you'd read the email about {ticket}, we wouldn't be repeating this."
        )
    elif shift_turn and shift_type == "cross_modal":
        lines[shift_turn - 1] = (
            f"Customer: I'm really worried about the ${amount} charge on {ticket}.\n"
            f"Acoustic note: agent tone dismissive while words sound supportive."
        )
    elif shift_type == "none":
        lines[shift_turn - 1] if shift_turn else None
        if shift_turn:
            lines[shift_turn - 1] = (
                f"Customer: I'm frustrated about the ${amount} charge, but I appreciate you checking {ticket}."
            )
    return "Transcript chunk (8 turns):\n" + "\n".join(f"{i + 1}. {t}" for i, t in enumerate(lines))


def gen_emotion_shift(existing: list[dict], rng: random.Random, n: int) -> list[dict]:
    agents = ("Priya", "Daniel", "Marcus", "Aisha", "Jordan", "Elena", "Sam")
    customers = ("Alex", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Quinn")
    types = ("sarcasm", "passive_aggression", "cross_modal", "none")

    def factory(seq: int) -> dict[str, Any]:
        stype = types[seq % len(types)]
        if stype == "none":
            shift_turn = 4 + (seq % 3)
        else:
            shift_turn = 3 + (seq % 5)
        scenario = SCENARIO_TOPICS[seq % len(SCENARIO_TOPICS)]
        agent = agents[seq % len(agents)]
        customer = customers[(seq * 3) % len(customers)]
        inp = _eight_turn(seq, scenario, agent, customer, shift_turn, stype)
        if stype == "none":
            ref = "No cross-modal contradiction. Text and acoustic emotions align."
            crit = "True negative — no sarcasm/passive-aggression"
        elif stype == "sarcasm":
            ref = f"Sarcasm at turn {shift_turn}. Cross-modal contradiction flagged."
            crit = "Must identify sarcasm with quote evidence"
        elif stype == "passive_aggression":
            ref = f"Passive-aggression at turn {shift_turn}. Cross-modal or tone mismatch flagged."
            crit = "Must identify passive-aggression with quote"
        else:
            ref = f"Cross-modal contradiction at turn {shift_turn}. Tone mismatch flagged."
            crit = "Must flag cross-modal mismatch with evidence"
        return {
            "input": inp + f"\n\nSample ref: ES-{seq:04d}\nTask: Detect emotion shift / cross-modal signals.",
            "reference_answer": ref,
            "scoring_criteria": crit,
            "_label": stype,
        }

    return _generate_batch(existing, "es", factory, n)


def gen_process_adherence(
    resolution_graphs: dict[str, list[str]], existing: list[dict], rng: random.Random, n: int
) -> list[dict]:
    topics = list(resolution_graphs.keys())
    agents = ("Priya", "Daniel", "Marcus", "Aisha")

    def factory(seq: int) -> dict[str, Any]:
        topic = topics[seq % len(topics)]
        steps = resolution_graphs[topic]
        missing_count = seq % 4
        missing = [steps[i] for i in range(missing_count) if i < len(steps)]
        present = [s for s in steps if s not in missing]
        ticket = f"NX-{seq:06d}"
        customer = ("Alex", "Taylor", "Morgan", "Casey", "Riley")[seq % 5]
        amount = AMOUNTS[seq % len(AMOUNTS)]
        lines = [
            f"Topic hint: {topic}",
            f"Call reference: {ticket} | Customer: {customer} | Amount: ${amount}",
            "Transcript (8 turns):",
            f"Customer: I need help with my {topic.replace('_', ' ')} on account {1000+seq}-{2000+seq}-{10+seq%89}.",
            f"Agent ({agents[seq % len(agents)]}): I can help with ticket {ticket} today.",
        ]
        for idx, step in enumerate(present[:4]):
            lines.append(f"Turn {idx + 3} Agent: [completed: {step}] — ref {seq * 17 + idx}")
        lines.append(f"Customer: Clarifying detail {seq} for {ticket}.")
        lines.append(f"Agent: Acknowledged — continuing {topic.replace('_', ' ')}.")
        lines.append("\nExpected resolution graph steps:")
        lines.extend(f"- {s}" for s in steps)
        ref = (
            f"Missing SOP steps: [{', '.join(missing)}]."
            if missing
            else "No missing SOP steps. Complete adherence."
        )
        return {
            "input": "\n".join(lines),
            "reference_answer": ref,
            "scoring_criteria": "Must list exact RESOLUTION_GRAPH missing step names",
            "_topic": topic,
            "_missing": missing,
        }

    return _generate_batch(existing, "pa", factory, n)


def gen_nli_policy(existing: list[dict], rng: random.Random, n: int) -> list[dict]:
    labels = ["Entailment", "Benign Deviation", "Contradiction", "Policy Hallucination"]
    variants = {
        "Entailment": [
            (
                "Outages under 24 hours are not eligible for automatic credits.",
                "Your outage was {hours} hours, so no automatic credit applies per policy.",
            ),
            (
                "Refund requests require order ID and purchase within 30 days.",
                "I have order {order_id} from {days} days ago — you're within the 30-day window.",
            ),
        ],
        "Benign Deviation": [
            (
                "Agents must verify identity before account changes.",
                "This is urgent — I'll verify PIN and email first. We skip the security-question step "
                "only because you called from the number on file ({phone}).",
            ),
            (
                "Escalations require supervisor approval before promising credits over $50.",
                "I'll note a ${amount} goodwill credit pending — skipping the hold script because "
                "you're a 5-year customer and I documented the reason in ticket {ticket}.",
            ),
        ],
        "Contradiction": [
            (
                "Bill credits post within 5-7 business days, not card refunds.",
                "I'll refund ${amount} to your card within 48 hours.",
            ),
            (
                "Agents may not promise same-day technician visits on weekends.",
                "A technician will arrive today before 5 PM to fix your line.",
            ),
        ],
        "Policy Hallucination": [
            (
                "Goodwill credits up to $200 without manager approval.",
                "Policy requires a $25 processing fee and director sign-off for any credit.",
            ),
            (
                "NexaLink does not offer lifetime price locks on promotional plans.",
                "Your plan is locked at $29 forever with no renewal increase.",
            ),
        ],
    }

    def factory(seq: int) -> dict[str, Any]:
        label = labels[seq % len(labels)]
        policy_tpl, agent_tpl = variants[label][(seq // len(labels)) % len(variants[label])]
        ctx = {
            "hours": 2 + (seq % 18),
            "order_id": f"ORD-{10000 + seq}",
            "days": 3 + (seq % 22),
            "phone": f"555-{100 + seq % 899}-{1000 + seq % 8999}",
            "amount": (25, 50, 75, 120)[seq % 4],
            "ticket": f"NX-{seq:06d}",
        }
        policy = policy_tpl.format(**ctx)
        agent = agent_tpl.format(**ctx)
        return {
            "input": f"Ground truth policy:\n{policy}\n\nAgent statement:\n{agent}\n\nRef: NLI-{seq:04d}",
            "reference_answer": f"Verdict: {label}.",
            "scoring_criteria": f"Must return {label}",
            "_label": label,
        }

    return _generate_batch(existing, "nli", factory, n)


def gen_rag_judge(existing: list[dict], rng: random.Random, n: int) -> list[dict]:
    def factory(seq: int) -> dict[str, Any]:
        rule_id, title, policy_text = RAG_POLICY_DOCS[seq % len(RAG_POLICY_DOCS)]
        ticket = f"NX-{seq:06d}"
        compliant = seq % 3 != 0
        if compliant:
            transcript = (
                f"Agent on call {ticket}: followed {rule_id} — stated required script and cited "
                f"{title} correctly before proceeding."
            )
            ref = f"Compliant. Source: {rule_id}."
        else:
            transcript = (
                f"Agent on call {ticket}: skipped a required {rule_id} step and proceeded without "
                f"citing {title}."
            )
            ref = f"Non-compliant. Violation of {rule_id}."
        return {
            "input": (
                f"--- COMPANY POLICIES ---\n[{rule_id} | {title}]\n{policy_text}\n\n"
                f"--- AGENT TRANSCRIPT ---\n{transcript}"
            ),
            "reference_answer": ref,
            "scoring_criteria": f"Must cite {rule_id}",
            "_compliant": compliant,
        }

    return _generate_batch(existing, "rj", factory, n)


def gen_text_to_sql(existing: list[dict], rng: random.Random, n: int) -> list[dict]:
    def factory(seq: int) -> dict[str, Any]:
        kind = seq % 10
        days = 7 + (seq % 83)
        limit_n = 3 + (seq % 8)
        team = ("Support", "Billing", "Retention")[seq % 3]
        if kind == 0:
            q = f"Top {limit_n} agents by overall score in the last {days} days"
            sql = (
                f"SELECT u.name, ROUND(AVG(s.overall_score)::NUMERIC * 10, 1) AS avg_score "
                f"FROM users u JOIN interactions i ON i.agent_id = u.id AND i.organization_id = '{ORG_ID}' "
                f"JOIN interaction_scores s ON s.interaction_id = i.id WHERE u.role = 'agent' "
                f"AND i.interaction_date >= NOW() - INTERVAL '{days} days' "
                f"GROUP BY u.id, u.name ORDER BY avg_score DESC LIMIT {limit_n}"
            )
        elif kind == 1:
            q = f"How many unresolved calls in the last {days} days?"
            sql = (
                f"SELECT COUNT(*) AS unresolved_count FROM interactions i "
                f"JOIN interaction_scores s ON s.interaction_id = i.id "
                f"WHERE i.organization_id = '{ORG_ID}' AND s.was_resolved = false "
                f"AND i.interaction_date >= NOW() - INTERVAL '{days} days'"
            )
        elif kind == 2:
            q = "Most common customer emotions this month"
            sql = (
                f"SELECT u2.emotion, COUNT(*) AS count FROM utterances u2 "
                f"JOIN interactions i ON u2.interaction_id = i.id "
                f"WHERE u2.speaker_role = 'customer' AND i.organization_id = '{ORG_ID}' "
                f"AND i.interaction_date >= date_trunc('month', now()) "
                f"GROUP BY u2.emotion ORDER BY count DESC LIMIT 10"
            )
        elif kind == 3:
            q = f"Average handle time for {'human' if seq % 2 == 0 else 'AI'} agents"
            agent_type = "human" if seq % 2 == 0 else "ai"
            sql = (
                f"SELECT ROUND(AVG(i.duration_seconds)::NUMERIC, 1) AS avg_aht "
                f"FROM interactions i JOIN users u ON u.id = i.agent_id "
                f"WHERE i.organization_id = '{ORG_ID}' AND u.role = 'agent' AND u.agent_type = '{agent_type}'"
            )
        elif kind == 4:
            q = "Interactions with empathy score below 0.5 this week"
            sql = (
                f"SELECT i.id, s.empathy_score FROM interactions i "
                f"JOIN interaction_scores s ON s.interaction_id = i.id "
                f"WHERE i.organization_id = '{ORG_ID}' AND s.empathy_score < 0.5 "
                f"AND i.interaction_date >= date_trunc('week', now())"
            )
        elif kind == 5:
            q = f"Count of {'active human' if seq % 2 == 0 else 'AI'} agent calls today"
            if seq % 2 == 0:
                filt = "u.role = 'agent' AND u.agent_type = 'human' AND u.is_active = true"
            else:
                filt = "u.role = 'agent' AND u.agent_type = 'ai'"
            sql = (
                f"SELECT COUNT(*) FROM interactions i JOIN users u ON u.id = i.agent_id "
                f"WHERE i.organization_id = '{ORG_ID}' AND {filt} "
                f"AND i.interaction_date >= CURRENT_DATE"
            )
        elif kind == 6:
            q = "Agents with most frustrated customer utterances"
            sql = (
                f"SELECT u.name, COUNT(*) AS frustrated_count FROM users u "
                f"JOIN interactions i ON i.agent_id = u.id "
                f"JOIN utterances ut ON ut.interaction_id = i.id "
                f"WHERE i.organization_id = '{ORG_ID}' AND ut.speaker_role = 'customer' "
                f"AND ut.emotion = 'frustrated' GROUP BY u.id, u.name "
                f"ORDER BY frustrated_count DESC LIMIT {limit_n}"
            )
        elif kind == 7:
            q = "Daily call volume last 14 days"
            sql = (
                f"SELECT DATE(i.interaction_date) AS day, COUNT(*) AS calls "
                f"FROM interactions i WHERE i.organization_id = '{ORG_ID}' "
                f"AND i.interaction_date >= NOW() - INTERVAL '14 days' "
                f"GROUP BY day ORDER BY day"
            )
        elif kind == 8:
            q = "Resolved rate by agent this month"
            sql = (
                f"SELECT u.name, ROUND(100.0 * AVG(CASE WHEN s.was_resolved THEN 1 ELSE 0 END), 1) AS pct "
                f"FROM users u JOIN interactions i ON i.agent_id = u.id "
                f"JOIN interaction_scores s ON s.interaction_id = i.id "
                f"WHERE i.organization_id = '{ORG_ID}' AND u.role = 'agent' "
                f"AND i.interaction_date >= date_trunc('month', now()) "
                f"GROUP BY u.id, u.name ORDER BY pct DESC"
            )
        else:
            secs = 300 + (seq % 600)
            q = f"Longest calls over {secs} seconds this month"
            sql = (
                f"SELECT i.id, i.duration_seconds, u.name FROM interactions i "
                f"JOIN users u ON u.id = i.agent_id "
                f"WHERE i.organization_id = '{ORG_ID}' AND i.duration_seconds > {secs} "
                f"AND i.interaction_date >= date_trunc('month', now()) "
                f"ORDER BY i.duration_seconds DESC LIMIT {limit_n}"
            )
        return {
            "input": f"Organization ID: {ORG_ID}\nQuestion: {q} (SQL-{seq:03d})",
            "reference_answer": sql,
            "scoring_criteria": "SELECT only; valid schema columns",
        }

    return _generate_batch(existing, "sql", factory, n)


def gen_fast_classification(existing: list[dict], rng: random.Random, n: int) -> list[dict]:
    stems = {
        "refund_request": "Please refund invoice {inv} for ${amt}",
        "billing_issue": "My bill jumped to ${amt} on invoice {inv}",
        "technical_support": "Router {model} drops connection every {mins} minutes",
        "account_access": "Locked out — PIN reset for account {acct}",
        "retention": "Cancel plan {plan} — switching to competitor",
        "fraud_dispute": "Unauthorized ${amt} charge on card ending {last4}",
        "fee_adjustment": "Waive the ${amt} late fee on account {acct}",
        "unknown": "When will fiber expand to zip {zipc}",
    }
    gibberish_parts = ("asdfgh", "qwerty", "zzxx", "blah", "mxnx", "!!!")

    def factory(seq: int) -> dict[str, Any]:
        if seq % 7 == 0:
            text = f"{' '.join(gibberish_parts[i % len(gibberish_parts)] for i in range(3 + seq % 4))} #{seq}"
            ref = "topic: unknown, is_gibberish: true"
            note = None
        elif seq % 11 == 0:
            text = f"There's a ${AMOUNTS[seq % len(AMOUNTS)]} charge on invoice NX-{seq:06d} I don't recognize"
            ref = "topic: fraud_dispute, is_gibberish: false"
            note = "ambiguous, multiple valid labels: billing_issue|fraud_dispute"
        else:
            topic = FAST_TOPICS[seq % len(FAST_TOPICS)]
            ctx = {
                "inv": f"NX-{seq:06d}",
                "amt": AMOUNTS[seq % len(AMOUNTS)],
                "model": ("XR-200", "NB-5", "FH-900")[seq % 3],
                "mins": 5 + (seq % 40),
                "acct": f"{1000+seq}-{2000+seq}-{10+seq%89}",
                "plan": ("Basic", "Plus", "Pro")[seq % 3],
                "last4": 1000 + seq % 8999,
                "zipc": 10000 + seq % 89999,
            }
            text = stems[topic].format(**ctx)
            ref = f"topic: {topic}, is_gibberish: false"
            note = None
        sample: dict[str, Any] = {
            "input": text,
            "reference_answer": ref,
            "scoring_criteria": "topic from reference; is_gibberish flag",
        }
        if note:
            sample["_note"] = note
        return sample

    return _generate_batch(existing, "fc", factory, n)


def validate_sql(sql: str) -> bool:
    try:
        proc = subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "db",
                "psql",
                "-U",
                "vocalmind",
                "-d",
                "vocalmind",
                "-c",
                f"EXPLAIN {sql}",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _keep_curated(stage: str, samples: list[dict]) -> list[dict]:
    prefix = PREFIX[stage]
    max_num = CURATED_MAX_NUM[stage]
    kept = []
    for s in samples:
        num = _sample_num(s.get("sample_id", ""), prefix)
        if num is not None and num <= max_num:
            kept.append(s)
    return kept


def _label_stats(stage: str, samples: list[dict]) -> dict[str, Any]:
    if stage == "emotion_shift":
        labels = Counter(s.get("_label", "unknown") for s in samples)
        eight_turn = sum(1 for s in samples if "8 turns" in s.get("input", ""))
        none_pct = 100.0 * labels.get("none", 0) / max(len(samples), 1)
        return {"labels": dict(labels), "eight_turn": eight_turn, "true_negative_pct": round(none_pct, 1)}
    if stage == "nli_policy":
        labels = Counter(s.get("_label", "unknown") for s in samples)
        return {"labels": dict(labels)}
    if stage == "fast_classification":
        gib = sum(1 for s in samples if "is_gibberish: true" in s.get("reference_answer", ""))
        amb = sum(1 for s in samples if s.get("_note"))
        return {"gibberish_pct": round(100.0 * gib / max(len(samples), 1), 1), "ambiguous": amb}
    return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate-sql", action="store_true")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop auto-generated samples; keep curated only, then fill to targets",
    )
    args = parser.parse_args()
    rng = random.Random(args.seed)

    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    resolution_graphs = _load_dict_constant(SERVICE_PY, "RESOLUTION_GRAPHS")

    generators: dict[str, Callable[[list[dict], int], list[dict]]] = {
        "emotion_shift": lambda e, n: gen_emotion_shift(e, rng, n),
        "process_adherence": lambda e, n: gen_process_adherence(resolution_graphs, e, rng, n),
        "nli_policy": lambda e, n: gen_nli_policy(e, rng, n),
        "rag_judge": lambda e, n: gen_rag_judge(e, rng, n),
        "text_to_sql": lambda e, n: gen_text_to_sql(e, rng, n),
        "fast_classification": lambda e, n: gen_fast_classification(e, rng, n),
    }

    stats: dict[str, Any] = {}
    for stage, target in TARGETS.items():
        existing = data.get(stage, [])
        if args.reset:
            existing = _keep_curated(stage, existing)
        need = max(0, target - len(existing))
        if need:
            existing.extend(generators[stage](existing, need))
        data[stage] = existing
        dupes = _dedup_check(existing)
        stats[stage] = {
            "count": len(existing),
            "added": need,
            "dupes": len(dupes),
            **(_label_stats(stage, existing)),
        }

    if args.validate_sql:
        results = [validate_sql(s["reference_answer"]) for s in data["text_to_sql"]]
        stats["text_to_sql"]["sql_validated"] = sum(results)
        stats["text_to_sql"]["sql_total"] = len(results)

    # Flag label imbalance (<10%)
    for stage in ("nli_policy", "emotion_shift"):
        labels = stats[stage].get("labels", {})
        if labels:
            low = [k for k, v in labels.items() if v / stats[stage]["count"] < 0.10]
            if low:
                stats[stage]["label_imbalance"] = low

    print(json.dumps(stats, indent=2))
    if args.dry_run:
        return
    GT_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {GT_PATH}")


if __name__ == "__main__":
    main()
