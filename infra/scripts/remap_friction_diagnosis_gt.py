#!/usr/bin/env python3
"""Enforce FR-5 interpretation-style emotion_shift dataset for friction diagnosis."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GT_PATH = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.json"
BACKUP_PATH = ROOT / "infra/benchmarks/ollama_cloud_ground_truth_v2.pre_force_interpretation_backup.json"

FRICTION_LABELS = ("interruption", "dismissive_tone", "missing_acknowledgment", "none")

REF_TEMPLATES = {
    "interruption": "Agent friction root cause: Interruption. Customer emotion shift linked to agent talking over or overlapping the customer.",
    "dismissive_tone": "Agent friction root cause: Dismissive tone. Curt, blaming, or impatient agent delivery contributed to the shift.",
    "missing_acknowledgment": "Agent friction root cause: Missing acknowledgment. Agent jumped to procedure without acknowledging customer concern.",
    "none": "No agent behavioral friction cause. Emotion shift (if any) is not attributable to agent interruption or dismissive behavior.",
}

SCORING_TEMPLATES = {
    "interruption": (
        "Must return friction_root_cause=interruption with an agent-overlap or interruption quote. "
        "Do NOT classify sarcasm/passive-aggression/cross_modal — emotion is pre-detected."
    ),
    "dismissive_tone": (
        "Must return friction_root_cause=dismissive_tone with curt/blaming/impatient agent quote. "
        "Do NOT classify sarcasm/passive-aggression/cross_modal — emotion is pre-detected."
    ),
    "missing_acknowledgment": (
        "Must return friction_root_cause=missing_acknowledgment showing procedural jump without acknowledgment. "
        "Do NOT classify sarcasm/passive-aggression/cross_modal — emotion is pre-detected."
    ),
    "none": (
        "Must return friction_root_cause=none when no clear agent interruption/dismissive behavior is present. "
        "Do NOT classify sarcasm/passive-aggression/cross_modal — emotion is pre-detected."
    ),
}


def _old_label(sample: dict) -> str:
    if sample.get("_friction_label"):
        return str(sample["_friction_label"])
    if sample.get("_label"):
        return str(sample["_label"])
    ref = sample.get("reference_answer", "").lower()
    if "no cross-modal" in ref or "true negative" in ref or "align" in ref[:60]:
        return "none"
    if "sarcasm" in ref:
        return "sarcasm"
    if "passive" in ref:
        return "passive_aggression"
    if "cross-modal" in ref or "tone mismatch" in ref:
        return "cross_modal"
    return "none"


def infer_friction(sample: dict) -> str:
    raw_input = str(sample.get("input", ""))
    # Keep only the conversational evidence block, not duplicated task instructions.
    core = re.split(r"\n\s*task:\s*", raw_input, maxsplit=1, flags=re.I)[0]
    blob = core.lower()

    lines = [ln.strip().lower() for ln in core.splitlines() if ln.strip()]
    agent_lines = [ln for ln in lines if re.match(r"^(?:\d+\.\s*)?agent", ln, re.I)]
    customer_lines = [ln for ln in lines if re.match(r"^(?:\d+\.\s*)?customer", ln, re.I)]
    note_lines = [ln for ln in lines if "acoustic note:" in ln]
    agent_blob = " ".join(agent_lines)
    customer_blob = " ".join(customer_lines)
    notes_blob = " ".join(note_lines)

    overlap_cues = (
        "overlapping speech",
        "talk over",
        "talking over",
        "interrupted",
        "interruption",
        "cut off",
        "cut the customer",
        "speaks over customer",
    )
    has_overlap = any(k in blob for k in overlap_cues)
    explicit_interrupt = any(k in blob for k in ("interrupted", "talk over", "talking over", "cut off", "speaks over"))
    if has_overlap and (explicit_interrupt or ("agent:" in blob and "customer:" in blob)):
        return "interruption"

    dismissive_cues = (
        "dismissive",
        "impatient",
        "curt",
        "blaming",
        "rude",
        "rudeness",
        "hostile",
        "condescending",
        "well, if you'd listened",
    )
    if any(k in agent_blob or k in notes_blob for k in dismissive_cues):
        return "dismissive_tone"

    concern_cues = (
        "worried",
        "worry",
        "concern",
        "upset",
        "frustrat",
        "angry",
        "unauthorized",
        "did not make",
        "didn't make",
        "charge",
        "overcharge",
    )
    procedural_jump_cues = (
        "verification",
        "verify",
        "policy",
        "ticket",
        "account number",
        "case",
        "review",
        "let me check",
        "pull up account",
    )
    ack_cues = ("sorry", "i understand", "i hear you", "that sounds", "i can see why")
    customer_has_concern = any(k in customer_blob for k in concern_cues)
    agent_is_procedural = any(k in agent_blob for k in procedural_jump_cues)
    agent_acknowledged = any(k in agent_blob for k in ack_cues)
    if customer_has_concern and agent_is_procedural and not agent_acknowledged:
        return "missing_acknowledgment"

    # No clear agent behavioral friction evidence.
    return "none"


def _detect_emotion(inp: str, label: str) -> str:
    low = inp.lower()
    m = re.search(r"acoustic emotion:\s*(\S+)", inp, re.I)
    if m:
        return m.group(1)
    if "anger" in low:
        return "anger"
    if "frustrat" in low:
        return "frustration"
    if "disgust" in low:
        return "disgust"
    if "fear" in low:
        return "fear"
    if label != "none":
        return "frustration"
    return "neutral"


def _parse_context(inp: str) -> tuple[str, str, str]:
    agent = ""
    customer = ""
    acoustic = ""
    m = re.search(r"Agent context:\s*(.+?)(?:\nCustomer text:|\Z)", inp, re.S)
    if m:
        agent = m.group(1).strip()
    m = re.search(r"Customer text:\s*(.+?)(?:\nAcoustic emotion:|\Z)", inp, re.S)
    if m:
        customer = m.group(1).strip()
    m = re.search(r"Acoustic emotion:\s*(.+)", inp)
    if m:
        acoustic = m.group(1).strip()

    if not customer:
        # transcript fallback
        lines = [ln.strip() for ln in inp.splitlines() if ln.strip()]
        cust_lines = [ln.split(":", 1)[1].strip() for ln in lines if re.match(r"^(?:\d+\.\s*)?Customer", ln, re.I)]
        agent_lines = [ln.split(":", 1)[1].strip() for ln in lines if re.match(r"^(?:\d+\.\s*)?Agent", ln, re.I)]
        customer = cust_lines[-1] if cust_lines else "See transcript evidence."
        agent = " ".join(agent_lines[-2:]) if agent_lines else "See transcript evidence."
    if not acoustic:
        acoustic = "neutral"
    return agent, customer, acoustic


def _force_interruption_cue(text: str) -> str:
    if "overlapping speech" in text.lower():
        return text
    return text.rstrip() + "\nAcoustic note: overlapping speech; agent speaks over customer during concern statement."


def _remove_overlap_cue(text: str) -> str:
    """Remove injected overlap note from non-interruption samples."""
    lines = []
    for line in text.splitlines():
        low = line.strip().lower()
        if "overlapping speech" in low and "speaks over customer" in low:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _extract_clean_evidence(raw: str) -> str:
    """Collapse recursively wrapped prompt bodies back to one transcript/evidence block."""
    text = (raw or "").strip()
    if not text:
        return text

    # Repeated remaps can wrap the same payload many times. Unwrap deterministically.
    wrapper_re = re.compile(
        r"^\s*Detected emotion \(pipeline\):.*?\n"
        r"Agent context:.*?\n"
        r"Customer text:.*?\n"
        r"Acoustic emotion:.*?\n\n"
        r"Transcript evidence:\n(?P<body>.*)$",
        re.I | re.S,
    )
    for _ in range(8):
        m = wrapper_re.match(text)
        if not m:
            break
        text = m.group("body").strip()

    # Keep only conversational evidence; strip appended task blocks.
    text = re.split(r"\n\s*Task:\s*", text, maxsplit=1, flags=re.I)[0].strip()
    return text


def _render_strict_input(sample: dict, label: str, detected_emotion: str) -> str:
    raw = sample.get("input", "").strip()
    raw = _extract_clean_evidence(raw)
    if label != "interruption":
        raw = _remove_overlap_cue(raw)
    agent, customer, acoustic = _parse_context(raw)
    transcript = raw
    if label == "interruption":
        transcript = _force_interruption_cue(transcript)
    task_block = (
        "Task: Interpret AGENT behavioral friction root cause ONLY.\n"
        "- Return one label: interruption | dismissive_tone | missing_acknowledgment | none.\n"
        "- Do NOT classify sarcasm/passive_aggression/cross_modal (emotion already detected upstream).\n"
        "- Ground the decision in agent evidence."
    )
    return (
        f"Detected emotion (pipeline): {detected_emotion}\n"
        f"Agent context: {agent}\n"
        f"Customer text: {customer}\n"
        f"Acoustic emotion: {acoustic}\n\n"
        f"Transcript evidence:\n{transcript}\n\n"
        f"{task_block}"
    )


def remap_sample(sample: dict, forced_label: str | None = None) -> dict:
    label = forced_label or infer_friction(sample)
    out = dict(sample)
    out["_friction_label"] = label
    out["_label"] = label
    out["reference_answer"] = REF_TEMPLATES[label]
    out["scoring_criteria"] = SCORING_TEMPLATES[label]
    out["input"] = _render_strict_input(out, label, _detect_emotion(out.get("input", ""), label))
    out["_friction_forced_interpretation"] = True
    return out


def _rebalance_labels(samples: list[dict]) -> dict[str, str]:
    """Return forced label map by sample_id using deterministic promotion rules."""
    return {s["sample_id"]: infer_friction(s) for s in samples}


def main() -> None:
    raw = GT_PATH.read_text(encoding="utf-8")
    BACKUP_PATH.write_text(raw, encoding="utf-8")
    data = json.loads(raw)
    forced_labels = _rebalance_labels(data["emotion_shift"])
    counts: dict[str, int] = {}
    for sample in data["emotion_shift"]:
        remapped = remap_sample(sample, forced_label=forced_labels.get(sample["sample_id"]))
        sample.clear()
        sample.update(remapped)
        lb = sample["_friction_label"]
        counts[lb] = counts.get(lb, 0) + 1
    GT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Updated {GT_PATH}")
    print(f"Backup: {BACKUP_PATH}")
    for k in FRICTION_LABELS:
        print(f"  {k}: {counts.get(k, 0)}")


if __name__ == "__main__":
    main()
