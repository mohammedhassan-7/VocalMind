from langchain_core.prompts import ChatPromptTemplate

from app.llm_trigger.prompt_constants import (
    EMOTION_SHIFT_FEW_SHOT,
    EMOTION_SHIFT_SYSTEM_CORE,
    INJECTION_GUARD,
    NLI_FEW_SHOT,
    NLI_POLICY_SYSTEM_CORE,
    PROCESS_ADHERENCE_SYSTEM_CORE,
)

__all__ = [
    "EMOTION_SHIFT_FEW_SHOT",
    "NLI_FEW_SHOT",
    "build_emotion_shift_prompt",
    "build_process_adherence_prompt",
    "build_nli_policy_prompt",
]


def build_emotion_shift_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                EMOTION_SHIFT_SYSTEM_CORE + "\n{format_instructions}\n" + INJECTION_GUARD,
            ),
            (
                "human",
                "{few_shot}\n\n"
                "Detected emotion (pipeline): {detected_emotion}\n"
                "Agent context: {agent_context}\n"
                "Customer text: {customer_text}\n"
                "Acoustic emotion: {acoustic_emotion}\n\n"
                "Task:\n"
                "1) Diagnose agent behavioral friction_root_cause: interruption, dismissive_tone, "
                "missing_acknowledgment, or none.\n"
                "2) Do NOT output sarcasm, passive_aggression, or cross_modal.\n"
                "3) Set turn_index to the agent turn where friction occurred (or null).\n"
                "4) Set evidence to a verbatim quote of the agent friction behavior.\n"
                "5) Return ONLY the JSON object.",
            ),
        ]
    )


def build_process_adherence_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                PROCESS_ADHERENCE_SYSTEM_CORE + "\n{format_instructions}\n" + INJECTION_GUARD,
            ),
            (
                "human",
                "{few_shot}\n\n"
                "Topic hint: {topic_hint}\n\n"
                "Transcript:\n{transcript_text}\n\n"
                "Retrieved SOP:\n{retrieved_sop}\n\n"
                "Expected resolution graph steps:\n{expected_resolution_graph}\n\n"
                "Task:\n"
                "- Set missing_sop_steps to an array of step_key strings (snake_case) from the catalog "
                "that are absent or weak in the transcript (empty array if none).\n"
                "- Provide justification, evidence_quotes, and citations grounded in the transcript.\n"
                "- Return ONLY the JSON object.",
            ),
        ]
    )


def build_nli_policy_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                NLI_POLICY_SYSTEM_CORE + "\n{format_instructions}\n" + INJECTION_GUARD,
            ),
            (
                "human",
                "{few_shot}\n\n"
                "Ground truth policy:\n{ground_truth_policy}\n\n"
                "Agent statement:\n{agent_statement}\n\n"
                "Classify into exactly one category. Set both verdict and nli_category to the same label.\n"
                "Return ONLY the JSON object.",
            ),
        ]
    )
