"""Normalize ground-truth sample inputs to production chain field shapes."""
from __future__ import annotations

import re


def normalize_emotion_shift_input(text: str) -> str:
    """Format GT input like production `build_emotion_shift_prompt` human message body."""
    if "Customer text:" in text or "customer_text:" in text.lower():
        return text

    agent_lines: list[str] = []
    customer_lines: list[str] = []
    acoustic_parts: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("task:"):
            continue
        if re.match(r"^(transcript chunk|sample ref)", stripped, re.I):
            continue
        if re.match(r"^acoustic note:", stripped, re.I):
            acoustic_parts.append(re.sub(r"^acoustic note:\s*", "", stripped, flags=re.I))
            continue
        if re.match(r"^acoustic emotion:", stripped, re.I):
            acoustic_parts.append(re.sub(r"^acoustic emotion:\s*", "", stripped, flags=re.I))
            continue
        if re.match(r"^text emotion:", stripped, re.I):
            continue
        agent_m = re.match(r"^(?:\d+\.\s*)?Agent(?:\s*\([^)]+\))?:\s*(.+)", stripped, re.I)
        cust_m = re.match(r"^(?:\d+\.\s*)?Customer(?:\s*\([^)]+\))?:\s*(.+)", stripped, re.I)
        if agent_m:
            agent_lines.append(agent_m.group(1).strip())
        elif cust_m:
            customer_lines.append(cust_m.group(1).strip())

    agent_context = " ".join(agent_lines[-3:]) if agent_lines else ""
    customer_text = customer_lines[-1] if customer_lines else ""
    if not customer_text:
        for line in text.splitlines():
            if line.strip().lower().startswith("customer:"):
                customer_text = line.split(":", 1)[1].strip()
                break

    acoustic_emotion = "; ".join(acoustic_parts) if acoustic_parts else "neutral"
    if not agent_context and not customer_text:
        return text

    return (
        f"Agent context: {agent_context or 'see transcript'}\n"
        f"Customer text: {customer_text or 'see transcript'}\n"
        f"Acoustic emotion: {acoustic_emotion}\n\n"
        f"Transcript (full):\n{text.strip()}"
    )


def normalize_nli_input(text: str) -> str:
    """Strip ref lines; keep policy + agent statement block."""
    lines = []
    for line in text.splitlines():
        if re.match(r"^ref:\s*", line.strip(), re.I):
            continue
        lines.append(line)
    return "\n".join(lines).strip()
