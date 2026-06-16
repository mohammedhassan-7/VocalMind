-- Benchmark seed data for text_to_sql execution scoring.
-- Org 00000000-0000-0000-0000-000000000001 matches ground-truth SQL filters.
-- Tagged BENCHMARK_ORG — safe to delete via infra/scripts/seed_benchmark_db.sh cleanup section.

BEGIN;

-- Password hash for synthetic benchmark users.
-- Use pgcrypto to generate valid bcrypt hashes at seed time.

DELETE FROM policy_compliance
WHERE interaction_id IN (
  SELECT id FROM interactions WHERE organization_id = '00000000-0000-0000-0000-000000000001'
);
DELETE FROM interaction_scores
WHERE interaction_id IN (
  SELECT id FROM interactions WHERE organization_id = '00000000-0000-0000-0000-000000000001'
);
DELETE FROM utterances
WHERE interaction_id IN (
  SELECT id FROM interactions WHERE organization_id = '00000000-0000-0000-0000-000000000001'
);
DELETE FROM transcripts
WHERE interaction_id IN (
  SELECT id FROM interactions WHERE organization_id = '00000000-0000-0000-0000-000000000001'
);
DELETE FROM interactions
WHERE organization_id = '00000000-0000-0000-0000-000000000001';
DELETE FROM organization_policies
WHERE organization_id = '00000000-0000-0000-0000-000000000001';
DELETE FROM company_policies
WHERE organization_id = '00000000-0000-0000-0000-000000000001';
DELETE FROM users
WHERE organization_id = '00000000-0000-0000-0000-000000000001';
DELETE FROM organizations
WHERE id = '00000000-0000-0000-0000-000000000001';

INSERT INTO organizations (id, name, slug, status)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'BENCHMARK_ORG', 'benchmark-org', 'active'),
  ('00000000-0000-0000-0000-000000000002', 'BENCHMARK_ORG_CTRL', 'benchmark-org-ctrl', 'active');

INSERT INTO users (id, organization_id, email, password_hash, name, role, agent_type, is_active)
VALUES
  ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000001', 'mgr@benchmark.org', crypt('password123', gen_salt('bf')), 'Bench Manager', 'manager', NULL, true),
  ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', 'priya@benchmark.org', crypt('password123', gen_salt('bf')), 'Priya Bench', 'agent', 'human', true),
  ('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000001', 'daniel@benchmark.org', crypt('password123', gen_salt('bf')), 'Daniel Bench', 'agent', 'human', true),
  ('00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000001', 'marcus@benchmark.org', crypt('password123', gen_salt('bf')), 'Marcus Bench', 'agent', 'ai', true),
  ('00000000-0000-0000-0000-000000000014', '00000000-0000-0000-0000-000000000001', 'aisha@benchmark.org', crypt('password123', gen_salt('bf')), 'Aisha Bench', 'agent', 'human', true),
  ('00000000-0000-0000-0000-000000000015', '00000000-0000-0000-0000-000000000001', 'jordan@benchmark.org', crypt('password123', gen_salt('bf')), 'Jordan Bench', 'agent', 'human', false),
  ('00000000-0000-0000-0000-000000000016', '00000000-0000-0000-0000-000000000001', 'elena@benchmark.org', crypt('password123', gen_salt('bf')), 'Elena Bench', 'agent', 'ai', true),
  ('00000000-0000-0000-0000-000000000017', '00000000-0000-0000-0000-000000000001', 'sam@benchmark.org', crypt('password123', gen_salt('bf')), 'Sam Bench', 'agent', 'human', true),
  ('00000000-0000-0000-0000-000000000018', '00000000-0000-0000-0000-000000000001', 'quinn@benchmark.org', crypt('password123', gen_salt('bf')), 'Quinn Bench', 'agent', 'ai', false),
  ('00000000-0000-0000-0000-000000000020', '00000000-0000-0000-0000-000000000002', 'ctrl@benchmark.org', crypt('password123', gen_salt('bf')), 'Ctrl Agent', 'agent', 'human', true);

INSERT INTO company_policies (id, organization_id, policy_title, policy_category, policy_text, is_active)
VALUES
  ('00000000-0000-0000-0000-000000000030', '00000000-0000-0000-0000-000000000001', 'Recording Notice', 'CS', 'Agents must state calls may be recorded.', true),
  ('00000000-0000-0000-0000-000000000031', '00000000-0000-0000-0000-000000000001', 'Refund Timeline', 'FIN', 'Credits post within 5-7 business days.', true),
  ('00000000-0000-0000-0000-000000000032', '00000000-0000-0000-0000-000000000001', 'Identity Verification', 'SEC', 'Verify identity before account changes.', true);

INSERT INTO organization_policies (id, organization_id, policy_id, is_active)
SELECT gen_random_uuid(), '00000000-0000-0000-0000-000000000001', id, true
FROM company_policies
WHERE organization_id = '00000000-0000-0000-0000-000000000001';

-- 18 interactions across date ranges (this week/month, last 30d, prior months)
INSERT INTO interactions (id, organization_id, agent_id, uploaded_by, audio_file_path, file_size_bytes, duration_seconds, file_format, interaction_date, processing_status)
VALUES
  ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000010', '/benchmark/call101.wav', 100000, 420, 'wav', date_trunc('week', now()) + interval '1 day', 'completed'),
  ('00000000-0000-0000-0000-000000000102', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000010', '/benchmark/call102.wav', 100000, 350, 'wav', date_trunc('week', now()) + interval '2 days', 'completed'),
  ('00000000-0000-0000-0000-000000000103', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000010', '/benchmark/call103.wav', 100000, 510, 'wav', date_trunc('month', now()) + interval '1 day', 'completed'),
  ('00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000014', '00000000-0000-0000-0000-000000000010', '/benchmark/call104.wav', 100000, 280, 'wav', date_trunc('month', now()) + interval '3 days', 'completed'),
  ('00000000-0000-0000-0000-000000000105', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000016', '00000000-0000-0000-0000-000000000010', '/benchmark/call105.wav', 100000, 330, 'wav', date_trunc('month', now()) + interval '5 days', 'completed'),
  ('00000000-0000-0000-0000-000000000106', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000017', '00000000-0000-0000-0000-000000000010', '/benchmark/call106.wav', 100000, 400, 'wav', now() - interval '5 days', 'completed'),
  ('00000000-0000-0000-0000-000000000107', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000010', '/benchmark/call107.wav', 100000, 290, 'wav', now() - interval '12 days', 'completed'),
  ('00000000-0000-0000-0000-000000000108', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000010', '/benchmark/call108.wav', 100000, 360, 'wav', now() - interval '20 days', 'completed'),
  ('00000000-0000-0000-0000-000000000109', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000010', '/benchmark/call109.wav', 100000, 320, 'wav', now() - interval '25 days', 'completed'),
  ('00000000-0000-0000-0000-000000000110', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000014', '00000000-0000-0000-0000-000000000010', '/benchmark/call110.wav', 100000, 450, 'wav', now() - interval '35 days', 'completed'),
  ('00000000-0000-0000-0000-000000000111', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000016', '00000000-0000-0000-0000-000000000010', '/benchmark/call111.wav', 100000, 380, 'wav', now() - interval '45 days', 'completed'),
  ('00000000-0000-0000-0000-000000000112', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000017', '00000000-0000-0000-0000-000000000010', '/benchmark/call112.wav', 100000, 310, 'wav', now() - interval '60 days', 'completed'),
  ('00000000-0000-0000-0000-000000000113', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000010', '/benchmark/call113.wav', 100000, 340, 'wav', now() - interval '75 days', 'completed'),
  ('00000000-0000-0000-0000-000000000114', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000010', '/benchmark/call114.wav', 100000, 295, 'wav', now() - interval '90 days', 'completed'),
  ('00000000-0000-0000-0000-000000000115', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000010', '/benchmark/call115.wav', 100000, 520, 'wav', now() - interval '10 days', 'completed'),
  ('00000000-0000-0000-0000-000000000116', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000014', '00000000-0000-0000-0000-000000000010', '/benchmark/call116.wav', 100000, 480, 'wav', now() - interval '3 days', 'completed'),
  ('00000000-0000-0000-0000-000000000117', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000016', '00000000-0000-0000-0000-000000000010', '/benchmark/call117.wav', 100000, 600, 'wav', date_trunc('month', now()) + interval '7 days', 'completed'),
  ('00000000-0000-0000-0000-000000000118', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000017', '00000000-0000-0000-0000-000000000010', '/benchmark/call118.wav', 100000, 315, 'wav', CURRENT_DATE, 'completed');

INSERT INTO transcripts (id, interaction_id, full_text, overall_confidence)
SELECT gen_random_uuid(), id, 'Benchmark transcript text', 0.92
FROM interactions
WHERE organization_id = '00000000-0000-0000-0000-000000000001';

INSERT INTO utterances (id, interaction_id, transcript_id, speaker_role, user_id, sequence_index, start_time_seconds, end_time_seconds, text, emotion, emotion_confidence)
SELECT
  gen_random_uuid(),
  i.id,
  t.id,
  CASE WHEN gs % 2 = 0 THEN 'agent'::speaker_role_enum ELSE 'customer'::speaker_role_enum END,
  CASE WHEN gs % 2 = 0 THEN i.agent_id ELSE NULL END,
  gs,
  (gs - 1) * 5.0,
  gs * 5.0,
  CASE WHEN gs % 2 = 0 THEN 'Agent benchmark utterance' ELSE 'Customer benchmark utterance' END,
  CASE
    WHEN gs % 5 = 0 THEN 'frustrated'
    WHEN gs % 5 = 1 THEN 'neutral'
    WHEN gs % 5 = 2 THEN 'happy'
    WHEN gs % 5 = 3 THEN 'frustrated'
    ELSE 'concerned'
  END,
  0.85
FROM interactions i
JOIN transcripts t ON t.interaction_id = i.id
CROSS JOIN generate_series(1, 4) gs
WHERE i.organization_id = '00000000-0000-0000-0000-000000000001';

INSERT INTO interaction_scores (id, interaction_id, overall_score, empathy_score, policy_score, resolution_score, was_resolved, total_silence_seconds, avg_response_time_seconds)
VALUES
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000101', 0.42, 0.35, 0.40, 0.38, false, 12.0, 3.2),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000102', 0.55, 0.48, 0.52, 0.50, false, 8.0, 2.8),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000103', 0.88, 0.82, 0.85, 0.90, true, 5.0, 2.1),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000104', 0.91, 0.87, 0.89, 0.92, true, 4.0, 1.9),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000105', 0.76, 0.70, 0.72, 0.74, true, 6.0, 2.4),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000106', 0.63, 0.58, 0.60, 0.62, false, 7.0, 2.6),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000107', 0.72, 0.68, 0.70, 0.71, true, 5.5, 2.2),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000108', 0.81, 0.77, 0.79, 0.80, true, 4.5, 2.0),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000109', 0.48, 0.42, 0.45, 0.47, false, 9.0, 3.0),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000110', 0.67, 0.62, 0.65, 0.66, true, 6.5, 2.5),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000111', 0.58, 0.52, 0.55, 0.57, false, 8.5, 2.9),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000112', 0.85, 0.80, 0.83, 0.84, true, 4.2, 1.8),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000113', 0.79, 0.74, 0.76, 0.78, true, 5.2, 2.3),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000114', 0.44, 0.38, 0.41, 0.43, false, 10.0, 3.1),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000115', 0.93, 0.90, 0.91, 0.94, true, 3.5, 1.7),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000116', 0.38, 0.32, 0.35, 0.36, false, 11.0, 3.4),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000117', 0.86, 0.81, 0.84, 0.85, true, 4.8, 1.9),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000118', 0.69, 0.64, 0.66, 0.68, true, 6.0, 2.4);

INSERT INTO policy_compliance (id, interaction_id, policy_id, is_compliant, compliance_score, llm_reasoning, evidence_text)
VALUES
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000030', false, 0.35, 'Missed recording notice', 'No recording disclosure'),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000102', '00000000-0000-0000-0000-000000000031', false, 0.42, 'Wrong refund timeline stated', 'Promised 48h refund'),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000103', '00000000-0000-0000-0000-000000000030', true, 0.88, 'Recording notice given', 'Stated call may be recorded'),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000032', true, 0.91, 'Identity verified', 'Asked security questions'),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000105', '00000000-0000-0000-0000-000000000031', true, 0.79, 'Correct timeline', '5-7 business days'),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000106', '00000000-0000-0000-0000-000000000030', false, 0.48, 'Partial compliance', 'Late recording notice'),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000107', '00000000-0000-0000-0000-000000000032', true, 0.82, 'Verified PIN', 'PIN and email confirmed'),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000108', '00000000-0000-0000-0000-000000000031', true, 0.85, 'Timeline correct', 'Credit on next bill'),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000116', '00000000-0000-0000-0000-000000000030', false, 0.28, 'No recording notice', 'Skipped disclosure'),
  (gen_random_uuid(), '00000000-0000-0000-0000-000000000117', '00000000-0000-0000-0000-000000000032', false, 0.33, 'Skipped verification', 'Changed account without verify');

COMMIT;
