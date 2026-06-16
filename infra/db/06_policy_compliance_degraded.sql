-- Phase 12 A1: persist evaluator degraded-path signal.
-- Default false preserves legacy behavior for existing rows.
ALTER TABLE policy_compliance
    ADD COLUMN IF NOT EXISTS degraded BOOLEAN NOT NULL DEFAULT FALSE;

