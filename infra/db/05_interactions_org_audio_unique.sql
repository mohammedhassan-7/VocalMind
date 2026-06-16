-- Enforce watcher dedup at schema level.
-- PostgreSQL UNIQUE constraints treat NULL values as distinct, so nullable
-- audio_file_path rows (if introduced by other ingestion paths) do not
-- conflict with each other under this constraint.
ALTER TABLE interactions
ADD CONSTRAINT uq_interaction_org_audio_path
UNIQUE (organization_id, audio_file_path);
