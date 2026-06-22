"""Unit tests for the consolidated interaction QA scorer.

Covers the two scoring fixes:
* policy severity gradation — a minor slip must not score like a critical breach;
* empathy now discriminates on the diagnosed agent-friction type.
"""
from uuid import uuid4

from app.llm_trigger.schemas import (
    EmotionShiftAnalysis,
    InteractionLLMTriggerReport,
    NLIEvaluation,
    ProcessAdherenceReport,
)
from app.llm_trigger.scoring import (
    compute_empathy_score,
    compute_policy_score,
    compute_scores,
)


def _report(
    *,
    nli_category="Entailment",
    severity="none",
    policy_alignment_score=0.9,
    dissonance_type="none",
    is_dissonance_detected=False,
    confidence_score=0.9,
    is_resolved=True,
    efficiency_score=9,
    missing_sop_steps=None,
) -> InteractionLLMTriggerReport:
    return InteractionLLMTriggerReport(
        interaction_id=uuid4(),
        emotion_shift=EmotionShiftAnalysis(
            is_dissonance_detected=is_dissonance_detected,
            dissonance_type=dissonance_type,
            root_cause="root cause",
            counterfactual_correction="If the agent had done better, things improve.",
            confidence_score=confidence_score,
        ),
        process_adherence=ProcessAdherenceReport(
            detected_topic="billing_issue",
            is_resolved=is_resolved,
            efficiency_score=efficiency_score,
            justification="justification",
            missing_sop_steps=missing_sop_steps or [],
            confidence_score=0.95,
        ),
        nli_policy=NLIEvaluation(
            nli_category=nli_category,
            severity=severity,
            justification="justification",
            policy_alignment_score=policy_alignment_score,
            confidence_score=0.95,
        ),
        derived_customer_text="customer",
        derived_acoustic_emotion="neutral",
        derived_fused_emotion="neutral",
        derived_agent_statement="agent",
    )


def test_policy_severity_gradation_minor_beats_critical():
    minor = compute_policy_score(_report(nli_category="Contradiction", severity="minor", policy_alignment_score=0.2))
    major = compute_policy_score(_report(nli_category="Contradiction", severity="major", policy_alignment_score=0.2))
    critical = compute_policy_score(_report(nli_category="Contradiction", severity="critical", policy_alignment_score=0.1))

    # A minor recording-notice-style slip must outscore a critical breach.
    assert minor > major > critical
    # And the minor slip must no longer be floored near zero.
    assert minor >= 0.5
    assert critical <= 0.35


def test_policy_entailment_scores_high():
    score = compute_policy_score(_report(nli_category="Entailment", policy_alignment_score=0.95))
    assert score >= 0.85


def test_policy_violation_without_severity_defaults_to_major():
    # Model omitted severity -> defaults to the middle tier, not the floor.
    defaulted = compute_policy_score(_report(nli_category="Contradiction", severity="none", policy_alignment_score=0.2))
    explicit_major = compute_policy_score(_report(nli_category="Contradiction", severity="major", policy_alignment_score=0.2))
    assert defaulted == explicit_major


def test_empathy_discriminates_on_friction_type():
    clean = compute_empathy_score(_report(dissonance_type="none"))
    missing = compute_empathy_score(_report(dissonance_type="missing_acknowledgment", is_dissonance_detected=True))
    interrupt = compute_empathy_score(_report(dissonance_type="interruption", is_dissonance_detected=True))
    dismissive = compute_empathy_score(_report(dissonance_type="dismissive_tone", is_dissonance_detected=True))

    assert clean == 1.0
    assert clean > missing > interrupt > dismissive


def test_empathy_penalty_scales_with_confidence():
    high_conf = compute_empathy_score(
        _report(dissonance_type="dismissive_tone", is_dissonance_detected=True, confidence_score=0.9)
    )
    mid_conf = compute_empathy_score(
        _report(dissonance_type="dismissive_tone", is_dissonance_detected=True, confidence_score=0.6)
    )
    # Lower (but above-floor) confidence -> smaller penalty -> higher empathy.
    assert mid_conf > high_conf


def test_empathy_below_confidence_floor_is_not_penalized():
    # A too-uncertain friction diagnosis must not drag a good agent down.
    score = compute_empathy_score(
        _report(dissonance_type="dismissive_tone", is_dissonance_detected=True, confidence_score=0.2)
    )
    assert score == 1.0


def test_compute_scores_overall_blend_and_resolved_flag():
    scores = compute_scores(_report(nli_category="Entailment", is_resolved=True, efficiency_score=10))
    assert scores.was_resolved is True
    assert 0.0 <= scores.overall <= 1.0
    assert scores.policy >= 0.85
    assert scores.empathy == 1.0
