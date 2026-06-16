-- Dedicated least-privilege role for assistant NL->SQL execution.
-- This script is idempotent for existing databases and safe for fresh init.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vocalmind_readonly') THEN
        CREATE ROLE vocalmind_readonly LOGIN PASSWORD 'vocalmind_readonly_dev';
    ELSE
        ALTER ROLE vocalmind_readonly WITH LOGIN PASSWORD 'vocalmind_readonly_dev';
    END IF;
END $$;

REVOKE ALL ON SCHEMA public FROM vocalmind_readonly;
GRANT USAGE ON SCHEMA public TO vocalmind_readonly;

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM vocalmind_readonly;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM vocalmind_readonly;
REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM vocalmind_readonly;

-- users: id, organization_id, name, email, role, agent_type, is_active
GRANT SELECT (id, organization_id, name, email, role, agent_type, is_active)
ON TABLE users TO vocalmind_readonly;

-- organizations: id, name
GRANT SELECT (id, name)
ON TABLE organizations TO vocalmind_readonly;

-- interactions: id, organization_id, agent_id, duration_seconds, interaction_date,
-- processing_status, language_detected, has_overlap
GRANT SELECT (
    id,
    organization_id,
    agent_id,
    duration_seconds,
    interaction_date,
    processing_status,
    language_detected,
    has_overlap
)
ON TABLE interactions TO vocalmind_readonly;

-- interaction_scores: id, interaction_id, overall_score, empathy_score, policy_score,
-- resolution_score, was_resolved, total_silence_seconds, avg_response_time_seconds
GRANT SELECT (
    id,
    interaction_id,
    overall_score,
    empathy_score,
    policy_score,
    resolution_score,
    was_resolved,
    total_silence_seconds,
    avg_response_time_seconds
)
ON TABLE interaction_scores TO vocalmind_readonly;

-- policy_compliance: id, interaction_id, policy_id, is_compliant, compliance_score, llm_reasoning
GRANT SELECT (
    id,
    interaction_id,
    policy_id,
    is_compliant,
    compliance_score,
    llm_reasoning
)
ON TABLE policy_compliance TO vocalmind_readonly;

-- company_policies: id, organization_id, policy_category, policy_title, policy_text, is_active
GRANT SELECT (
    id,
    organization_id,
    policy_category,
    policy_title,
    policy_text,
    is_active
)
ON TABLE company_policies TO vocalmind_readonly;

-- utterances: id, interaction_id, speaker_role, emotion, start_time_seconds, end_time_seconds
GRANT SELECT (
    id,
    interaction_id,
    speaker_role,
    emotion,
    start_time_seconds,
    end_time_seconds
)
ON TABLE utterances TO vocalmind_readonly;
