"""Single source of truth for interaction QA scoring.

Both the production pipeline (``app.core.interaction_processing``) and the
ad-hoc reprocess script consume this module so scores stay on one scale (0.0–1.0)
and ``was_resolved`` is always populated.

Design notes (why the formulas look the way they do):

* **Policy** is driven primarily by the NLI policy verdict — the model's actual
  judgment of whether the agent's statements comply with policy. SOP-step
  coverage (``efficiency_score``) only acts as a *soft* modifier (±15%), because
  a missing step in the transcript usually means "we failed to detect it", not
  "the agent failed it". Letting undetected steps dominate produced the
  false-negative policy scores (e.g. a clean full-SOP call scoring 10–44%).
* **Empathy** is derived from the agent-behaviour friction the emotion-shift
  chain diagnoses (``dissonance_type``), so it actually discriminates between a
  dismissive agent and an exemplary one instead of collapsing to a constant.
* **Resolution** keeps the established step function; its direction matched
  ground truth in evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.llm_trigger.schemas import InteractionLLMTriggerReport


# Weights for the overall blend. Policy is the heaviest QA signal.
_OVERALL_WEIGHTS = {"policy": 0.4, "empathy": 0.3, "resolution": 0.3}

# Base policy score for compliant verdicts (severity is always "none" here).
_NLI_CATEGORY_BASE: dict[str, float] = {
    "Entailment": 0.95,
    "Benign Deviation": 0.85,
    "Contradiction": 0.30,
    "Policy Hallucination": 0.20,
}

# Severity-graded base for *violation* verdicts. A minor procedural slip (e.g. a
# missing recording notice) must not score the same as a critical regulatory or
# identity-verification breach — that flatness was producing PASS calls scoring
# in the teens. The model grades severity in the NLI output; we map it here.
_NLI_SEVERITY_BASE: dict[tuple[str, str], float] = {
    ("Contradiction", "critical"): 0.25,
    ("Contradiction", "major"): 0.45,
    ("Contradiction", "minor"): 0.65,
    ("Policy Hallucination", "critical"): 0.15,
    ("Policy Hallucination", "major"): 0.35,
    ("Policy Hallucination", "minor"): 0.55,
}

# When the model flags a violation but omits severity, assume the middle tier so
# we neither floor a possible false-positive nor excuse a real breach.
_DEFAULT_VIOLATION_SEVERITY = "major"

# Empathy penalty per diagnosed agent friction type (subtracted from 1.0).
_FRICTION_PENALTY: dict[str, float] = {
    "none": 0.0,
    "missing_acknowledgment": 0.15,
    "interruption": 0.25,
    "dismissive_tone": 0.35,
}

# Below this confidence we do not penalize empathy — too uncertain to credibly
# fault the agent, so a borderline diagnosis can't drag a good call down.
_FRICTION_MIN_CONFIDENCE = 0.5


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalize_friction(dissonance_type: str | None) -> str:
    return (dissonance_type or "none").strip().lower().replace("-", "_").replace(" ", "_")


@dataclass(frozen=True)
class InteractionScores:
    """All scores normalized to 0.0–1.0."""

    overall: float
    empathy: float
    policy: float
    resolution: float
    was_resolved: bool


def _policy_base_score(nli) -> float:
    """Severity-graded base score for the NLI verdict.

    Compliant verdicts (Entailment / Benign Deviation) use the flat category
    base. Violation verdicts (Contradiction / Policy Hallucination) are graded
    by the model-supplied severity so a minor slip and a critical breach no
    longer collapse to the same floor.
    """
    category = nli.nli_category
    if category in ("Entailment", "Benign Deviation"):
        return _NLI_CATEGORY_BASE.get(category, 0.6)

    severity = (nli.severity or _DEFAULT_VIOLATION_SEVERITY).strip().lower()
    if severity not in ("critical", "major", "minor"):
        severity = _DEFAULT_VIOLATION_SEVERITY
    return _NLI_SEVERITY_BASE.get((category, severity), _NLI_CATEGORY_BASE.get(category, 0.3))


def compute_policy_score(report: InteractionLLMTriggerReport) -> float:
    """Policy compliance, anchored on the NLI verdict with soft SOP-coverage modifier."""
    nli = report.nli_policy
    base = _policy_base_score(nli)

    # Blend in the continuous alignment score as a light refinement. Kept small
    # (0.2) so the severity-graded base stays the dominant term — the model's
    # alignment for any violation tends to collapse near 0 and would otherwise
    # wipe out the severity gradation.
    if nli.policy_alignment_score is not None:
        base = (0.8 * base) + (0.2 * float(nli.policy_alignment_score))

    # SOP-step coverage scales the result within [0.85, 1.0] — a mild modifier,
    # never the dominant term, so undetected steps can't tank a compliant call.
    coverage = _clamp_unit(float(report.process_adherence.efficiency_score) / 10.0)
    base = base * (0.85 + 0.15 * coverage)

    # Degrade gracefully toward neutral when the verdict lacked grounded evidence.
    if nli.insufficient_evidence:
        base = max(base, 0.6)

    return _clamp_unit(base)


def compute_empathy_score(report: InteractionLLMTriggerReport) -> float:
    """Empathy from the diagnosed agent friction, scaled by model confidence."""
    shift = report.emotion_shift

    if shift.insufficient_evidence:
        return 0.8  # neutral: we can't credit or penalize the agent.

    friction = _normalize_friction(shift.dissonance_type)
    penalty = _FRICTION_PENALTY.get(friction, 0.25 if shift.is_dissonance_detected else 0.0)

    confidence = shift.confidence_score
    if friction != "none" and confidence is not None:
        # Too-uncertain diagnoses do not penalize a good agent at all.
        if confidence < _FRICTION_MIN_CONFIDENCE:
            return 1.0
        # Otherwise weight the penalty by confidence so weaker diagnoses bite less.
        penalty *= _clamp_unit(confidence)

    return _clamp_unit(1.0 - penalty)


def compute_resolution_score(report: InteractionLLMTriggerReport) -> float:
    """Resolution step function: resolved (full vs partial SOP) vs unresolved."""
    adherence = report.process_adherence
    if adherence.is_resolved:
        return 0.94 if not adherence.missing_sop_steps else 0.84
    return 0.42


def compute_scores(report: InteractionLLMTriggerReport) -> InteractionScores:
    """Compute all interaction QA scores (0.0–1.0) from an LLM trigger report."""
    policy = compute_policy_score(report)
    empathy = compute_empathy_score(report)
    resolution = compute_resolution_score(report)
    overall = round(
        (policy * _OVERALL_WEIGHTS["policy"])
        + (empathy * _OVERALL_WEIGHTS["empathy"])
        + (resolution * _OVERALL_WEIGHTS["resolution"]),
        4,
    )
    return InteractionScores(
        overall=overall,
        empathy=round(empathy, 4),
        policy=round(policy, 4),
        resolution=round(resolution, 4),
        was_resolved=bool(report.process_adherence.is_resolved),
    )
