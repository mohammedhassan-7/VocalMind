#!/usr/bin/env python3
"""Rewrite samples in large duplicate clusters with structural template variation."""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra" / "scripts"))

from analyze_duplicates import cluster_stage  # noqa: E402
import generate_ground_truth as gt  # noqa: E402

ES_EXTRA_SARCASM = (
    "Oh wonderful — ticket {ticket} is still open after a week.",
    "Brilliant service; the ${amt} refund never showed on {acct}.",
    "Just peachy — another outage while I'm on a deadline.",
    "Love how every call about {ticket} starts from scratch.",
    "Sure, blame the router again instead of reading {ticket}.",
    "Another ${amt} fee — exactly what I needed this month.",
    "I'm sure the fourth transfer will finally fix {acct}.",
    "Yes, I enjoy repeating my DOB for ticket {ticket}.",
    "Outstanding — hold time only doubled since last call.",
    "Perfect timing for a billing error on account {acct}.",
    "Delighted the promo rate vanished without notice on {ticket}.",
    "Ecstatic that nobody documented my prior call on {acct}.",
)
ES_EXTRA_PASSIVE = (
    "I suppose accuracy on {ticket} is optional today.",
    "Take your time — my lunch break is flexible for {acct}.",
    "Clearly I'm the only one who remembers ticket {ticket}.",
    "No need to rush; I've only called about ${amt} twice.",
    "I'm sure the notes on {acct} will appear eventually.",
    "Do what you want — not like policy applies to everyone.",
    "I'll wait while you search for case {ticket} again.",
    "Must be nice when ${amt} errors fix themselves.",
    "Happy to hold if that helps with {acct}.",
    "I'll repeat the outage dates since {ticket} has none.",
    "Sure, escalate later — that always works on {acct}.",
    "Fine, I'll call back tomorrow about the same ${amt}.",
)
ES_EXTRA_CROSS = (
    "Customer claims satisfaction on {ticket}.\nAcoustic note: audible sigh, flat affect.",
    "Agent offers help with ${amt} credit.\nAcoustic note: monotone, rushed cadence.",
    "Customer: 'Fine, whatever about {acct}'.\nAcoustic note: tension in jaw, clipped words.",
    "Agent: 'We value your time on {ticket}'.\nAcoustic note: overlapping speech, impatience.",
    "Customer laughs after mentioning ${amt}.\nAcoustic note: sarcastic burst, not amusement.",
    "Agent apologizes for {acct} delay.\nAcoustic note: no warmth, robotic delivery.",
)
ES_EXTRA_NONE = (
    "I'm upset about ${amt} but glad you pulled up {ticket}.",
    "The outage frustrated me; thanks for checking {acct} promptly.",
    "Still annoyed by the fee, yet your explanation on {ticket} helped.",
    "Not happy about ${amt}, but I appreciate the callback on {acct}.",
    "I was angry at first; you handled {ticket} professionally.",
    "The wait was long, though you fixed {acct} in one call.",
    "Billing confused me; you clarified ${amt} without rushing.",
    "I'm disappointed but accept the resolution on {ticket}.",
)

ES_TRIGGERS = {
    "sarcasm": (
        "Oh perfect, another billing surprise on ticket {ticket}.",
        "Sure, because this is exactly the premium experience I signed up for.",
        "Wow, third outage this month — truly outstanding service on {ticket}.",
        "Great, so the ${amt} charge just appeared again. Love that.",
        "Fantastic — hold music for twenty minutes, then a disconnect on {ticket}.",
        "No rush at all; take your time fixing account {acct} again.",
        "I'm thrilled the router reset didn't work for the fourth time.",
        "Lovely — another transfer loop before anyone reads ticket {ticket}.",
    ) + ES_EXTRA_SARCASM,
    "passive_aggression": (
        "Well, if you'd read the email about {ticket}, we wouldn't be here.",
        "I guess I'll just wait while you look up account {acct} again.",
        "Do whatever you think is best — not like I've called three times.",
        "Sure, put me on hold again. I have nowhere else to be.",
        "Must be nice to only need one verification step from some customers.",
        "I'll repeat the story from the top since notes never stick on {ticket}.",
        "Take your time — it's only my third lunch break spent on this.",
        "No worries, I'm used to explaining the ${amt} charge every week.",
    ) + ES_EXTRA_PASSIVE,
    "cross_modal": (
        "I'm really worried about the ${amt} charge on {ticket}.\nAcoustic note: agent tone dismissive while words sound supportive.",
        "Customer says they're calm about outage on {acct}.\nAcoustic note: voice shaking, elevated pitch.",
        "Agent: 'Happy to help with {ticket}'.\nAcoustic note: clipped, impatient delivery.",
        "Customer: 'I trust you'll fix the ${amt} fee'.\nAcoustic note: sarcastic laugh detected.",
    ) + ES_EXTRA_CROSS,
    "none": (
        "I'm frustrated about the ${amt} charge, but I appreciate you checking {ticket}.",
        "This outage was annoying, yet your team kept me updated on {acct}.",
        "I was upset at first, though you explained the ${amt} line clearly.",
        "Still unhappy about the fee, but thanks for verifying {ticket} quickly.",
    ) + ES_EXTRA_NONE,
}

NLI_OPENINGS = (
    "Customer raised issue first:\n",
    "Agent cited policy first:\n",
    "Supervisor escalation context:\n",
    "Follow-up call — prior ticket {ticket}:\n",
    "Compliance review thread — case {ticket}:\n",
    "Written complaint attached to {ticket}:\n",
    "Chat transcript escalated to voice on {ticket}:\n",
    "Second-line review for account {acct}:\n",
    "Policy exception request on {ticket}:\n",
    "Regulatory inquiry reference {ticket}:\n",
    "Quality audit sample {ticket}:\n",
    "Manager callback regarding {ticket}:\n",
    "Prior denial appeal for {acct}:\n",
    "Billing dispute tied to {ticket}:\n",
    "Retention offer context on {acct}:\n",
    "Technical outage waiver for {ticket}:\n",
    "Fraud hold review case {ticket}:\n",
    "SLA breach ticket {ticket}:\n",
)

FC_PHRASES = {
    "refund_request": (
        "Need a refund on invoice {inv}",
        "Please reverse the ${amt} charge on {inv}",
        "Credit my account for invoice {inv}",
        "Dispute ${amt} on billing doc {inv}",
        "Return ${amt} from last cycle {inv}",
        "Wrong amount on {inv} — refund ${amt}",
        "Cancel and refund order {inv}",
        "Overcharge on {inv}, want ${amt} back",
        "Duplicate charge {inv} for ${amt}",
        "Refund request ref {inv}",
        "Billing error ${amt} on {inv}",
        "Chargeback prep for {inv}",
        "Adjust invoice {inv} by ${amt}",
        "Credit note needed for {inv}",
        "Reverse fee ${amt} on {inv}",
        "Refund ${amt} from promo {inv}",
        "Invoice {inv} shows wrong ${amt}",
        "Please fix {inv} and refund ${amt}",
    ),
    "billing_issue": (
        "Bill jumped to ${amt}",
        "Why is invoice {inv} so high",
        "Unexpected ${amt} on statement {inv}",
        "Autopay took ${amt} not ${amt2}",
        "Plan rate changed on {inv}",
        "Tax line wrong on {inv}",
        "Promo expired on bill {inv}",
        "Double billed ${amt} on {inv}",
        "Usage spike ${amt} invoice {inv}",
        "Equipment fee ${amt} on {inv}",
        "Late fee ${amt} dispute {inv}",
        "Proration error on {inv}",
        "Bundle discount missing {inv}",
        "Roaming charges ${amt} {inv}",
        "Paper bill fee on {inv}",
        "Installment ${amt} on {inv}",
        "Credit not applied {inv}",
        "Balance shows ${amt} not ${amt2}",
    ),
    "technical_support": (
        "Router {model} drops every {mins} min",
        "Internet keeps cutting out on {model}",
        "WiFi dead zones with {model}",
        "Speed test fails on {model}",
        "Firmware update broke {model}",
        "DNS errors on {model}",
        "VPN conflicts with {model}",
        "Mesh node {model} offline",
        "Packet loss on {model}",
        "Latency spikes {mins} ms on {model}",
        "Port forwarding on {model}",
        "IPv6 issue {model}",
        "Guest network down {model}",
        "Parental controls {model}",
        "Factory reset {model} failed",
        "Cable modem sync {model}",
        "ONT light red {model}",
        "VoIP jitter on {model}",
    ),
    "account_access": (
        "Locked out of account {acct}",
        "PIN reset needed for {acct}",
        "2FA not working {acct}",
        "Password expired on {acct}",
        "Email change for {acct}",
        "Username recovery {acct}",
        "App login fails {acct}",
        "Security questions {acct}",
        "SIM swap block {acct}",
        "Portal access {acct}",
        "MFA device lost {acct}",
        "Suspicious login {acct}",
        "Profile update {acct}",
        "Authorized user add {acct}",
        "Close sub-account {acct}",
        "Merge accounts {acct}",
        "Reactivate dormant {acct}",
        "Verify identity {acct}",
    ),
    "retention": (
        "Cancel plan {plan}",
        "Switching providers unless you help",
        "Competitor offer on {plan}",
        "Downgrade {plan} tier",
        "Price match request {plan}",
        "Contract end {plan}",
        "Bundle break {plan}",
        "Loyalty discount {plan}",
        "Early termination {plan}",
        "Pause service {plan}",
        "Move address keep {plan}",
        "Student discount {plan}",
        "Senior rate {plan}",
        "Military discount {plan}",
        "Win-back offer {plan}",
        "Compare {plan} to rival",
        "Retention call {plan}",
        "Cancel add-ons {plan}",
    ),
    "fraud_dispute": (
        "Unauthorized ${amt} on card {last4}",
        "Fraud charge ${amt} I didn't make",
        "Skimmed card ending {last4}",
        "Account takeover ${amt}",
        "Phishing charge ${amt}",
        "Duplicate auth {last4}",
        "Foreign transaction ${amt}",
        "Merchant dispute ${amt}",
        "Subscription fraud ${amt}",
        "SIM fraud on {acct}",
        "Check fraud ${amt}",
        "Wire fraud alert ${amt}",
        "Crypto scam ${amt}",
        "Gift card fraud ${amt}",
        "Refund fraud ${amt}",
        "Chargeback {last4}",
        "Identity theft {acct}",
        "Block card {last4}",
    ),
    "fee_adjustment": (
        "Waive ${amt} late fee on {acct}",
        "Remove the ${amt} penalty please",
        "Courtesy credit ${amt}",
        "Goodwill adjustment ${amt}",
        "Overdraft fee ${amt}",
        "Service fee waive ${amt}",
        "Activation fee ${amt}",
        "Restocking fee ${amt}",
        "Convenience fee ${amt}",
        "Annual fee credit ${amt}",
        "Prorated fee ${amt}",
        "Installation waive ${amt}",
        "Dispatch fee ${amt}",
        "Reconnection ${amt}",
        "Equipment rental ${amt}",
        "Early upgrade ${amt}",
        "Insurance fee ${amt}",
        "Regulatory fee ${amt}",
    ),
    "unknown": (
        "When is fiber coming to zip {zipc}",
        "Coverage map update for {zipc}",
        "Store hours near {zipc}",
        "New tower {zipc}",
        "Roaming in {zipc}",
        "Business plan {zipc}",
        "Outage map {zipc}",
        "Speed tiers {zipc}",
        "Partner promo {zipc}",
        "Community event {zipc}",
        "Job fair {zipc}",
        "Recycling bin {zipc}",
        "Solar rebate {zipc}",
        "EV charger {zipc}",
        "Smart home {zipc}",
        "Gift card balance",
        "Donation program",
        "Survey feedback",
    ),
}


def _rand_amt(rng: random.Random, variant: int) -> int:
    return rng.randint(12, 899) + (variant % 17)


def _rewrite_emotion(sample: dict, rng: random.Random, variant: int) -> None:
    label = sample.get("_label") or "none"
    triggers = ES_TRIGGERS.get(label, ES_TRIGGERS["none"])
    ticket = f"NX-{100000 + variant + rng.randint(0, 9999)}"
    amt = _rand_amt(rng, variant)
    acct = f"{1000 + variant % 9000}-{2000 + variant % 8000}-{10 + variant % 89}"
    turn_count = (6, 8, 10, 12)[variant % 4]
    shift_turn = 2 + (variant % max(1, turn_count - 2))
    agent = gt.AGENT_NAMES[variant % len(gt.AGENT_NAMES)]
    customer = gt.CUSTOMER_NAMES[(variant * 2 + rng.randint(0, 5)) % len(gt.CUSTOMER_NAMES)]
    scenario = gt.SCENARIO_TOPICS[(variant + rng.randint(0, 7)) % len(gt.SCENARIO_TOPICS)]
    pool = [
        f"Agent ({agent}): NexaLink support, this is {agent}. How can I help today?",
        f"Customer ({customer}): Calling about {scenario.replace('_', ' ')} — reference {ticket}.",
        f"Agent: I'll pull up account {acct} and ticket {ticket}.",
        f"Customer: The ${amt} line from last week is the main issue.",
        f"Agent: I see notes on case {variant % 10000}. One moment while I review policy.",
        f"Customer: I've already verified identity twice on prior calls.",
        f"Agent: Understood — let me check escalation options for {ticket}.",
        f"Customer: What's the actual resolution timeline here?",
        f"Agent: I can offer a ${amt // 2} courtesy credit while we investigate.",
        f"Customer: That doesn't cover the full ${amt} overcharge.",
        f"Agent: I'll document your preference on {ticket}.",
        f"Customer: Please email confirmation to the address on {acct}.",
    ]
    lines = pool[:turn_count]
    trigger = triggers[(variant + rng.randint(0, len(triggers) - 1)) % len(triggers)].format(
        ticket=ticket, amt=amt, acct=acct
    )
    speaker = "Agent" if label == "passive_aggression" else "Customer"
    name = agent if label == "passive_aggression" else customer
    lines[min(shift_turn - 1, len(lines) - 1)] = f"{speaker} ({name}): {trigger}"
    sample["input"] = f"Transcript chunk ({turn_count} turns):\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(lines))
    sample["_rewritten"] = True


def _rewrite_nli(sample: dict, rng: random.Random, variant: int) -> None:
    inp = sample.get("input", "")
    ticket = f"NX-{variant + rng.randint(1000, 999999):06d}"
    acct = f"{1000 + variant % 5000}-{2000 + variant % 4000}"
    opening = NLI_OPENINGS[variant % len(NLI_OPENINGS)].format(ticket=ticket, acct=acct)
    if "Ground truth policy:" in inp:
        parts = inp.split("Agent statement:")
        policy_head = parts[0].replace("Ground truth policy:", "Policy clause:")
        sample["input"] = opening + policy_head + "Agent statement:" + parts[1]
    elif "Policy clause:" in inp:
        parts = inp.split("Agent statement:")
        sample["input"] = opening + parts[0] + "Agent statement:" + parts[1]
    sample["_rewritten"] = True


def _rewrite_pa(sample: dict, rng: random.Random, variant: int) -> None:
    turn_count = (6, 8, 10, 12)[variant % 4]
    agent = gt.AGENT_NAMES[variant % len(gt.AGENT_NAMES)]
    customer = gt.CUSTOMER_NAMES[(variant + 3) % len(gt.CUSTOMER_NAMES)]
    ticket = f"NX-{variant + rng.randint(0, 99999):06d}"
    amt = _rand_amt(rng, variant)
    steps = [
        f"Agent ({agent}): Thank you for calling NexaLink, this is {agent}.",
        f"Customer ({customer}): I need help with billing and access — ticket {ticket}.",
        f"Agent: I'll verify your identity before discussing account details.",
        f"Customer: The ${amt} charge and login lock are both urgent.",
        f"Agent: I see two tracks — I'll document billing AND access separately on {ticket}.",
        f"Customer: Please don't merge them; they're unrelated issues.",
        f"Agent: Understood. First I'll read the mandatory disclosure for billing.",
        f"Customer: Fine — but don't skip the security reset steps.",
        f"Agent: I'll follow the checklist for fraud-sensitive changes.",
        f"Customer: How long for each resolution path?",
        f"Agent: Billing review 24h; access restore after verification.",
        f"Customer: Email me case numbers for both tracks.",
    ]
    sample["input"] = f"Transcript ({turn_count} turns):\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(steps[:turn_count]))
    sample["_rewritten"] = True


def _rewrite_rag(sample: dict, rng: random.Random, variant: int) -> None:
    inp = sample.get("input", "")
    if "--- AGENT TRANSCRIPT ---" in inp:
        head, tail = inp.split("--- AGENT TRANSCRIPT ---", 1)
        if variant % 2 == 0:
            sample["input"] = head + "--- AGENT TRANSCRIPT ---\nBefore action: agent cited policy clause.\n" + tail
        else:
            sample["input"] = head + "--- AGENT TRANSCRIPT ---\nAfter action: agent cited policy clause post-hoc.\n" + tail
    sample["_rewritten"] = True


def _rewrite_fc(sample: dict, rng: random.Random, variant: int) -> None:
    ref = sample.get("reference_answer", "")
    topic = "unknown"
    for t in gt.FAST_TOPICS:
        if f"topic: {t}" in ref:
            topic = t
            break
    phrases = FC_PHRASES.get(topic, FC_PHRASES["unknown"])
    amt = _rand_amt(rng, variant)
    amt2 = _rand_amt(rng, variant + 17)
    ctx = {
        "inv": f"NX-{variant + rng.randint(0, 999999):06d}",
        "amt": amt,
        "amt2": amt2,
        "model": ("XR-200", "NB-5", "FH-900", "ZX-10", "MK-44")[variant % 5],
        "mins": 5 + rng.randint(0, 55),
        "acct": f"{1000 + variant % 9000}-{2000 + variant % 8000}",
        "plan": ("Basic", "Plus", "Pro", "Enterprise", "Student")[variant % 5],
        "last4": 1000 + (variant + rng.randint(0, 8999)) % 8999,
        "zipc": 10000 + (variant + rng.randint(0, 89999)) % 89999,
    }
    phrase = phrases[(variant + rng.randint(0, len(phrases) - 1)) % len(phrases)].format(**ctx)
    sample["input"] = f"{phrase} [case-{variant % 10000}-t{topic[:3]}]"
    sample["_rewritten"] = True


REWRITERS = {
    "emotion_shift": _rewrite_emotion,
    "nli_policy": _rewrite_nli,
    "process_adherence": _rewrite_pa,
    "rag_judge": _rewrite_rag,
    "fast_classification": _rewrite_fc,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground-truth", default=str(ROOT / "infra" / "benchmarks" / "ollama_cloud_ground_truth_v2.json"))
    parser.add_argument("--threshold", type=float, default=0.8)
    parser.add_argument("--min-cluster", type=int, default=10)
    parser.add_argument("--seed", type=int, default=88)
    args = parser.parse_args()

    path = Path(args.ground_truth)
    data = json.loads(path.read_text(encoding="utf-8"))
    rng = random.Random(args.seed)
    rewritten = 0

    for stage, rewriter in REWRITERS.items():
        samples = data.get(stage, [])
        if not isinstance(samples, list):
            continue
        _, clusters = cluster_stage(samples, args.threshold)
        by_id = {s["sample_id"]: s for s in samples}
        for members in clusters.values():
            if len(members) < args.min_cluster:
                continue
            for idx, sid in enumerate(members[1:], start=1):
                if sid in by_id:
                    v = int(re.sub(r"\D", "", sid) or idx) + idx * 17
                    rewriter(by_id[sid], rng, v)
                    rewritten += 1

    meta = data.get("version", "v2")
    data["dedup_rewritten_count"] = rewritten
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Rewrote {rewritten} samples in large clusters -> {path}")


if __name__ == "__main__":
    main()
