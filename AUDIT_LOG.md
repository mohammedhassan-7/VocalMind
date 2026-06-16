## 2026-06-16 — Phase 1: Multi-tenant data isolation

- Findings addressed (approved):
  - Fixed unauthenticated interaction trigger execution path and enforced org scoping for interaction/transcript/utterance loads in trigger flow.
  - Fixed RAG query route to require authenticated user and derive org filter server-side (removed client-settable org filter).
  - Added assistant SQL tenant guard to reject non-org-scoped generated SQL before execution.
  - Fixed agent profile aggregates/trends/recent queries to include `Interaction.organization_id` scoping.
  - Fixed interaction emotion-comparison utterance query to join `Interaction` and apply scoped filters.
  - Removed client org override in interaction detail trigger path and derive org filter from interaction ownership.

- Regression tests added:
  - `backend/tests/test_llm_trigger_isolation.py`
  - `backend/tests/test_rag_route_isolation.py`
  - `backend/tests/test_assistant_tenant_guard.py`
  - `backend/tests/test_agents_isolation.py`
  - `backend/tests/test_interactions_emotion_comparison_isolation.py`
  - `backend/tests/test_interactions_llm_org_filter_isolation.py`

- Verification:
  - Rebuilt/restarted backend container after each fix cycle via `docker compose up -d --build backend`.
  - Ran focused test modules for each fix and final combined run:
    - `python -m pytest tests/test_llm_trigger_isolation.py tests/test_rag_route_isolation.py tests/test_assistant_tenant_guard.py tests/test_agents_isolation.py tests/test_interactions_emotion_comparison_isolation.py tests/test_interactions_llm_org_filter_isolation.py -q`
    - Result: `6 passed`.

- Deliberately deferred from Phase 1 findings:
  - Dashboard violation subquery scoping item: deferred as **non-issue for tenant isolation** (primary query remains org-scoped; subquery concern is performance/consistency).
  - JWT `org_id` claim item: deferred as **defense-in-depth** (current source of truth remains DB-backed `current_user.organization_id` from token subject lookup).

## 2026-06-16 — Phase 2: Secrets & environment hygiene

- Findings addressed (approved):
  - Implemented explicit fail-fast startup validation matrix in `backend/app/core/config.py` via `validate_startup_settings(...)`.
  - Enforced unconditional hard-fail when `SECRET_KEY` remains default placeholder in all environments (including local dev).
  - Enforced provider-specific hard-fail when `LLM_PROVIDER=groq` and `GROQ_API_KEY` is empty.
  - Enforced provider-specific hard-fail when `LLM_PROVIDER=ollama_cloud` and neither `OLLAMA_CLOUD_API_KEY` nor alias `OLLAMA_API_KEY` is set.
  - Kept `HF_TOKEN` optional but changed warning to explicit impact statement: diarization is disabled when missing.
  - Wired validation into app startup lifecycle (`backend/app/main.py` lifespan) before DB/worker startup.

- Regression test added:
  - `backend/tests/test_config_startup_validation.py`
    - asserts fail-fast for default `SECRET_KEY` even with local-dev style config
    - asserts fail-fast for missing provider key under `groq`
    - asserts fail-fast for missing provider key under `ollama_cloud`
    - asserts explicit HF-token missing warning (no hard fail)
    - asserts pass when required settings are present

- Verification:
  - Rebuilt/restarted backend container via `docker compose up -d --build backend`.
  - Test command:
    - `python -m pytest tests/test_config_startup_validation.py tests/test_security.py -q`
    - Result: `8 passed`.

- Investigated and left unchanged (clean / no fix needed):
  - `.env` commit history hygiene: no committed non-example `.env` files found in git history.
  - `BACKEND_SPEAKER_RELABEL_ENABLED`: confirmed actively gates relabel path in runtime code.
  - `AUDIO_FOLDER_WATCHER_ENABLED`: confirmed actively gates watcher startup in runtime code.

- Deliberately deferred:
  - Benchmark artifact files containing key-like strings (`infra/benchmarks/...`) deferred to **Phase 12** because no live credentials were found; this is tracked-artifact/repo-hygiene policy, not an active secret leak.

## 2026-06-16 — Phase 3 Item 1: Assistant DB least-privilege role

- Root cause addressed:
  - Assistant NL->SQL execution was using the same privileged app DB role, so DB-layer safety depended on app-layer guards only.

- Implemented:
  - Added `infra/db/04_assistant_readonly_role.sql` to create `vocalmind_readonly` and grant **column-level** `SELECT` only (no table-level `SELECT`, no DML/DDL grants).
  - Added `ASSISTANT_DATABASE_URL` to `.env.example`, `backend/.env.example`, and `docker-compose.yml`.
  - Added `ASSISTANT_DATABASE_URL` setting in `backend/app/core/config.py`.
  - Added dedicated assistant SQL execution engine in `backend/app/api/routes/assistant.py` and switched only LLM-generated SQL execution to that engine.
  - Kept assistant bookkeeping queries (`assistant_queries` reads/writes) on the regular app `engine` as required.

- Corrected approved grant matrix (implemented exactly):
  - `users`: `id`, `organization_id`, `name`, `email`, `role`, `agent_type`, `is_active`
  - `organizations`: `id`, `name`
  - `interactions`: `id`, `organization_id`, `agent_id`, `duration_seconds`, `interaction_date`, `processing_status`, `language_detected`, `has_overlap`
  - `interaction_scores`: `id`, `interaction_id`, `overall_score`, `empathy_score`, `policy_score`, `resolution_score`, `was_resolved`, `total_silence_seconds`, `avg_response_time_seconds`
  - `policy_compliance`: `id`, `interaction_id`, `policy_id`, `is_compliant`, `compliance_score`, `llm_reasoning`
  - `company_policies`: `id`, `organization_id`, `policy_category`, `policy_title`, `policy_text`, `is_active`
  - `utterances`: `id`, `interaction_id`, `speaker_role`, `emotion`, `start_time_seconds`, `end_time_seconds`

- Evidence and corrections captured before migration:
  - `company_policies.organization_id` was verified as real tenant key in both `backend/app/models/policy.py` and `infra/db/01_schema.sql`; it was restored to grants.
  - `_is_org_scoped_sql` guard behavior was rechecked to ensure DB permissions do not break valid scoped queries.
  - `interaction_scores.total_silence_seconds` and `avg_response_time_seconds` were included after re-evaluation as legitimate analytics fields.
  - `users.agent_type` and `users.is_active` were included based on assistant evaluation artifacts showing real use-cases for these filters.
  - `policy_compliance.evidence_text` and `retrieved_policy_text` remained excluded due to direct quote/raw policy-text exposure.

- Accepted tradeoff (documented):
  - `policy_compliance.llm_reasoning` remains grantable to preserve explainability functionality.
  - Residual risk accepted for now: `llm_reasoning` may paraphrase policy/call content.
  - Revisit in a future phase if real examples show raw transcript/policy quote leakage in practice.

- Regression tests added:
  - `backend/tests/test_assistant_readonly_db_permissions.py`
    - positive scoped SELECT across granted columns succeeds.
    - restricted `users.password_hash` read fails at DB permission layer.
    - restricted `policy_compliance.evidence_text` read fails at DB permission layer.
    - mutating/DDL statements (`INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `CREATE TABLE`) fail at DB permission layer.

- Verification:
  - Rebuilt/restarted backend container: `docker compose up -d --build backend`
  - Applied role migration to existing DB volume: `docker compose exec -T db psql -U vocalmind -d vocalmind -f /docker-entrypoint-initdb.d/04_assistant_readonly_role.sql`
  - Before/after test evidence:
    - Before fix run (`tests/test_assistant.py tests/test_assistant_tenant_guard.py tests/test_assistant_readonly_db_permissions.py`): initial run failed (test path/config issue when tests were not mounted / async plugin missing in container context).
    - After fix + corrected test invocation: `25 passed`.

## 2026-06-16 — Phase 3 Item 2: AST-based SQL structural validator + allowlist

- Root cause addressed:
  - Assistant SQL safety checks were lexical (`startswith` + keyword blocklist), which can miss structurally unsafe SQL and did not enforce explicit projections, table/column allowlists, or strict LIMIT controls.

- Implemented:
  - Added parser-based SQL validation in `backend/app/api/routes/assistant.py` using `sqlparse`.
  - Added `sqlparse` dependency to backend project manifests.
  - Introduced allowlist-based validation against approved assistant schema:
    - Allowed tables: `users`, `organizations`, `interactions`, `interaction_scores`, `policy_compliance`, `company_policies`, `utterances`.
    - Allowed columns per table match the approved Phase 3 Item 1 readonly matrix.
  - Enforced structural rules before execution:
    - exactly one SQL statement;
    - statement type must be `SELECT` or `WITH ... SELECT`;
    - no wildcard projections (`SELECT *` or `table.*`);
    - referenced tables must be a subset of allowlisted tables;
    - referenced columns must be in allowlisted columns;
    - explicit `LIMIT` is required and capped at `200`.
  - Kept `_is_org_scoped_sql(...)` as an independent additional guard.
  - Replaced silent lexical rejection behavior with explicit user-facing rejection message:
    - `"I can only run safe analytics queries. <specific reason>"`
  - Updated ordinal follow-up helper query to avoid wildcard selection.
  - Updated assistant `_SCHEMA` prompt block to align with enforced allowlist column names.

- Regression tests added/updated:
  - Updated `backend/tests/test_assistant.py`:
    - unit test: rejects `SELECT *` exfiltration shape.
    - unit test: rejects multi-statement injection (`SELECT ...; DROP TABLE ...`).
    - updated markdown-fence parse test to a valid allowlisted+limited query.
  - Added `backend/tests/test_assistant_sql_structure_guard.py`:
    - route-level rejection for `SELECT *` with clear error message.
    - route-level rejection for multi-statement injection with clear error message.

- Verification:
  - Rebuilt/restarted backend container after changes.
  - Test command:
    - `python -m pytest tests/test_assistant.py tests/test_assistant_tenant_guard.py tests/test_assistant_readonly_db_permissions.py tests/test_assistant_sql_structure_guard.py -q`
    - Result: `29 passed`.

- Deferred note re conversation-history prompt-injection framing:
  - This batch did **not** modify `_fetch_conversation_block`.
  - The structural validator blocks unsafe SQL forms even if malicious prompt context influences generation, substantially reducing execution-path risk.
  - Context-inclusion quality/prompt-hygiene remains a separate defense-in-depth concern for a future phase (non-blocking for this item’s execution safety objective).

- API-level smoke check against live backend (post-implementation):
  - Executed authenticated end-to-end checks through `POST /api/v1/assistant/query` and captured request/response payloads.
  - Verified runtime execution-path evidence for successful SQL case via backend logs:
    - `ASSISTANT_SQL_ENGINE_EXEC readonly role path`
    - confirms generated SQL execution used `assistant_sql_engine`.
  - Observed behavior:
    - Safe case (`second one` with previously seeded allowlisted scoped SQL): `200`, `success=true`, returned row data.
    - `SELECT *` case: `200`, explicit rejection message
      - `"I can only run safe analytics queries. Wildcard projection (SELECT *) is not allowed."`
    - Multi-statement case: `200`, explicit rejection message
      - `"I can only run safe analytics queries. Assistant SQL must be exactly one statement."`
    - `users.password_hash` case: `200`, explicit rejection message
      - `"I can only run safe analytics queries. Column 'password_hash' is not in the assistant allowlist."`
  - Catch-layer note for defense-in-depth:
    - In live API flow, the `password_hash` probe is caught by **item 2 structural allowlist** before DB execution.
    - DB-permission denial layer from **item 1** remains independently verified by dedicated regression tests (`test_assistant_readonly_db_permissions.py`) and still serves as a fallback safety layer.

- Phase 3 status: closed.

## 2026-06-16 — Phase 4: LLM provider/model routing by stage

- Design decisions implemented:
  - Kept **two synchronized implementations** (no cross-container shared import module):
    - backend LangChain routing in `backend/app/llm_trigger/chains.py`
    - services/rag SDK/LlamaIndex routing in `services/rag/config.py`
  - Added a concrete cross-service drift guard test:
    - `backend/tests/test_llm_trigger_service.py::test_stage_name_contract_matches_rag_implementation`
    - asserts backend + rag expose the exact same stage-name set.

- Stage contract implemented (shared across backend and rag):
  - `emotion_shift`
  - `process_adherence`
  - `nli_policy`
  - `rag_judge`
  - `text_to_sql`
  - `fast_classification` *(declared only; no live runtime call site yet)*
  - `rag_synthesis`
  - Notes:
    - Both implementations include explicit in-code comments that `fast_classification` is benchmarked/configurable but currently unwired in production runtime flows.

- Fallback class mapping implemented:
  - heavy class: `emotion_shift`, `process_adherence`, `text_to_sql`
  - fast class: `nli_policy`, `rag_judge`, `fast_classification`
  - `rag_synthesis` decision resolution (explicit):
    - No benchmark evidence in `FULL_REPORT_v6.md` supports classifying synthesis as fast/heavy.
    - Chosen path: preserve current behavior exactly when unset.
    - `rag_synthesis` fallback now skips fast/heavy globals and defaults directly to `settings.groq.model` unless `OLLAMA_MODEL_RAG_SYNTHESIS` is explicitly set.
  - fallback chain:
    1) per-stage var (new naming)
    2) legacy stage var (where historically present)
    3) class default (`OLLAMA_CLOUD_HEAVY_MODEL` or `OLLAMA_CLOUD_FAST_MODEL` when `LLM_PROVIDER=ollama_cloud`) for benchmarked classes
    4) service legacy default (`settings.groq.model`) for non-ollama-cloud provider paths and for unset `rag_synthesis`.

- Backend call-site wiring (pass 1 + pass 2):
  - `backend/app/llm_trigger/chains.py`
    - added stage contract + class-based fallback resolver
    - added new stage vars support:
      - `OLLAMA_MODEL_EMOTION_SHIFT`
      - `OLLAMA_MODEL_PROCESS_ADHERENCE`
      - `OLLAMA_MODEL_NLI_POLICY`
      - `OLLAMA_MODEL_RAG_JUDGE`
      - `OLLAMA_MODEL_TEXT_TO_SQL`
      - `OLLAMA_MODEL_FAST_CLASSIFICATION`
      - `OLLAMA_MODEL_RAG_SYNTHESIS`
    - preserved legacy vars:
      - `OLLAMA_EMOTION_SHIFT_MODEL`
      - `OLLAMA_PROCESS_ADHERENCE_MODEL`
      - `OLLAMA_NLI_MODEL`
    - exposed `recognized_stage_names()` for sync tests.
  - `backend/app/api/routes/assistant.py`
    - text-to-SQL generation/repair path now routes Ollama Cloud model selection through stage `text_to_sql` (`get_model_for_stage("text_to_sql")`), leaving SQL safety guards unchanged.

- services/rag wiring (pass 3):
  - `services/rag/config.py`
    - added matching stage contract + `recognized_stage_names()` + `resolve_model_for_stage(stage)`
    - `rag_judge_model()` now stage-routed (`rag_judge`)
    - added `rag_synthesis_model()` stage-routed (`rag_synthesis`) with legacy-preserving fallback (`settings.groq.model`) when unset
  - `services/rag/query_engine.py`
    - `_setup_llm()` now uses `rag_synthesis_model()` instead of direct `settings.groq.model`
    - query log model field now reports `rag_synthesis_model()` consistently.

- Env/config updates (legacy vars preserved):
  - Updated:
    - `.env.example` (root)
    - `backend/.env.example`
    - `services/rag/.env.example`
    - `docker-compose.yml` env pass-through for backend + ingestion
    - `backend/app/core/config.py` settings fields
    - `services/rag/config.py` settings fields
  - Legacy variables remain supported and are not removed.

- Regression tests added/updated:
  - backend:
    - `backend/tests/test_llm_trigger_service.py`
      - stage override precedence
      - legacy override fallback
      - heavy/fast class fallback behavior
      - unknown stage rejection
      - stage set contract
      - cross-service stage sync assertion
    - `backend/tests/test_assistant.py`
      - verifies assistant Ollama Cloud `text_to_sql` path uses stage-routed model selection.
  - rag:
    - `services/rag/tests/test_config.py`
      - stage resolver precedence + fallback + unknown-stage rejection + contract set.
      - explicit regression for `rag_synthesis` legacy-preserving fallback when per-stage var is unset.

- Verification (one call site family at a time, then combined):
  - pass 1 backend llm_trigger:
    - `python -m pytest tests/test_llm_trigger_service.py -q`
    - result: `19 passed`
  - pass 2 assistant + structural guards:
    - `python -m pytest tests/test_assistant.py tests/test_assistant_sql_structure_guard.py -q`
    - result: `21 passed`
    - confirms model routing changes did not alter SQL allowlist/guard behavior.
  - pass 1+2 combined backend:
    - `python -m pytest tests/test_llm_trigger_service.py tests/test_assistant.py tests/test_assistant_sql_structure_guard.py -q`
    - result: `41 passed`
  - pass 3 rag tests:
    - `python -m pytest tests/test_config.py tests/test_evaluator.py tests/test_query_engine.py -q` (executed in container context with `/app/rag` mounted)
    - result: `37 passed`
  - container verification:
    - backend rebuilt/restarted: `docker compose up -d --build backend`
    - startup logs show successful app boot and health-check `200`.

## 2026-06-16 — Phase 5: Speaker-role double-labeling conflict check

- What was found:
  - Caller path exists: backend pipeline calls `relabel_segments_with_speaker_model(...)` in `backend/app/core/interaction_processing.py` before utterance persistence.
  - Hard gate confirmed: relabel path is controlled by `BACKEND_SPEAKER_RELABEL_ENABLED`; disabled path returns segments unchanged.
  - When enabled, behavior is last-write-wins for non-empty-text segments: backend relabeler can overwrite WhisperX-assigned role labels, with no merge/conflict arbitration.
  - `SpeakerRole` enum and normalization coverage are consistent (`agent`/`customer`) across WhisperX outputs, backend relabeler normalization, and persistence mapping.

- What was fixed:
  - Added explicit reconciliation-policy comment at `backend/app/core/speaker_role_infer.py` entry point (`relabel_segments_with_speaker_model`), documenting intentional last-write-wins behavior and lack of confidence-based conflict arbitration.
  - Added observability warning for enabled-but-unavailable model path:
    - `"BACKEND_SPEAKER_RELABEL_ENABLED=true but model unavailable; WhisperX labels preserved unchanged."`
  - Added regression test:
    - `backend/tests/test_speaker_role_infer.py::test_relabel_enabled_model_unavailable_preserves_labels_and_warns`
    - asserts unchanged segments + warning emission.

- What was found clean and needed no fix:
  - Enum consistency (`SpeakerRole.agent` / `SpeakerRole.customer`) across both classifiers and persistence.
  - Normalization/mapping path for known role-label variants remains valid.

- What was explicitly deferred (intentional behavior, not a bug):
  - Reconciliation policy redesign (e.g., merge/arbitration/confidence blending or pipeline reorder) is deferred.
  - Reason: current last-write-wins behavior is intentional and opt-in; changing it requires explicit product/stakeholder decision, not a silent audit-pass refactor.

- Verification:
  - Rebuilt/restarted backend container: `docker compose up -d --build backend`
  - Test command:
    - `python -m pytest tests/test_speaker_role_infer.py -q`
    - result: `1 passed`.

## 2026-06-16 — Phase 6: Audio folder watcher and file-handling surface

- What was fixed:
  - Added intake-time path confinement guard in `backend/app/core/audio_folder_watcher.py` before processing each discovered file:
    - out-of-bounds paths (including symlink escapes resolving outside `org_dir`) are now skipped.
    - warning includes both `org.slug` and attempted path context for operations visibility.
  - Added DB-level dedup constraint on watcher identity key:
    - model: `backend/app/models/interaction.py` now defines `UniqueConstraint("organization_id", "audio_file_path", name="uq_interaction_org_audio_path")`.
    - migration SQL: `infra/db/05_interactions_org_audio_unique.sql`.
    - migration note documents PostgreSQL NULL semantics: UNIQUE treats NULL as distinct, so nullable `audio_file_path` rows do not conflict with each other.
  - Added watcher-focused regression coverage:
    - `backend/tests/test_audio_folder_watcher.py`
      - rejects out-of-bounds symlink-resolved path and asserts warning emission.
      - accepts valid in-bounds file path.

- What was found clean and needed no fix:
  - Org scoping: watcher-triggered inserts derive and persist `organization_id` from iterated `Organization` rows (no null/default cross-tenant write path found).
  - Single-instance dedup behavior: existing pre-insert lookup in watcher loop remains correct for one process.
  - Crash-safe retention profile: watcher leaves original files in place, avoiding delete-before-persist data-loss window.

- What was deferred and why:
  - File retention policy (move/delete/archive after processing): deferred as intentional product/ops tradeoff; current keep-in-place behavior is safer for crash recovery.
  - Magic-byte/content validation beyond extension filtering: deferred to Phase 12; current behavior degrades gracefully via processing failure paths (`mark_interaction_failed`), making this a quality-hardening decision requiring product guidance (reject-at-intake vs process-and-fail).

- Verification:
  - Rebuilt/restarted backend: `docker compose up -d --build backend`
  - Applied DB migration: `docker compose exec -T db psql -U vocalmind -d vocalmind -f /docker-entrypoint-initdb.d/05_interactions_org_audio_unique.sql`
  - Test command:
    - `python -m pytest tests/test_audio_folder_watcher.py tests/test_interaction_ingestion.py tests/test_interaction_processing_quality.py -q`
    - result: `17 passed`.

## 2026-06-16 — Phase 7: LLM output trust boundaries

- What was fixed:
  - `rag_judge` prompt sanitization added in RAG layer:
    - Introduced `services/rag/prompt_safety.py` with role-prefix neutralization, backtick defang, and truncation helpers.
    - Applied sanitization to all user-controlled/interpolated fields in `services/rag/evaluator.py` prompt construction (`transcript`, `question`, `agent_answer`, and retrieved chunk text blocks).
  - Declarative shape/range validation added after JSON parse in `services/rag/evaluator.py`:
    - Required key checks for expected judge payload fields.
    - Explicit numeric handling for score fields with 0..1 clamp.
    - Invalid parseable shape now falls back to neutral score (`0.5`) with explicit reasoning, rather than propagating malformed values.
  - `rag_synthesis` prompt-input sanitization added:
    - Sanitized retrieved chunk text before node synthesis.
    - Sanitized question and appended instruction-safety guard before passing to LlamaIndex synthesizer.
    - Keeps current synthesis architecture; applies trust-boundary preprocessing at inputs.

- What was found clean and needed no fix:
  - Trigger-chain paths (`emotion_shift`, `process_adherence`, `nli_policy`) already had structured parser boundaries and established fallback behavior.
  - Assistant SQL execution path remains intentionally guarded at the output boundary (SQL structural/org-scope validation + readonly engine), so no additional prompt-input sanitizer was added to `assistant.py`.

- What was acknowledged-and-documented but not fixed:
  - Benchmark infra SQL execution surface (`infra/scripts/text_to_sql_execution.py`) remains broader by design in dev tooling.
  - Added explicit security comment documenting this is benchmark/dev-only and must not be wired to live tenant-facing DB paths.
  - No production-guard retrofit was applied to the benchmark script in this phase.

- What was found clean with no action needed:
  - No production call sites were found where LLM output is used as file paths, shell arguments, or subprocess path/command selectors.

- Verification:
  - Rebuilt/restarted backend container: `docker compose up -d --build backend`
  - Combined gate command:
    - `python -m pytest services/rag/tests/test_evaluator.py services/rag/tests/test_query_engine.py -q`
    - result: `22 passed`.

## 2026-06-16 — Phase 8: Error handling, logging, and observability

- Fixed:
  - Added a global FastAPI exception sanitizer in `backend/app/main.py`:
    - catches unhandled exceptions,
    - logs full server-side error with traceback and generated `error_id`,
    - returns sanitized `500` body with generic detail + `error_id`.
  - Removed client-facing internal exception passthrough from high-risk `500` paths:
    - `backend/app/api/routes/rag.py` now logs full detail server-side and returns sanitized internal-error message with reference ID.
    - health dependency checks in `rag.py` / `llm_trigger/router.py` no longer echo raw exception text in response payloads.
  - Sensitive log demotion/guarding:
    - `services/rag/query_engine.py`: added `RAG_QUERY_LOG_ENABLED` gate (default `false`) to make file-based query content persistence opt-in.
      - when disabled, emits DEBUG-only metric log (`question_len`, `chunk_count`, `response_len`) with no content.
      - `services/rag/.env.example` updated with privacy note for this flag.
    - `backend/app/api/routes/assistant.py`:
      - SQL parse preview log moved to DEBUG and reduced to safe 100-char preview.
      - SQL execution failure SQL-content log moved to DEBUG and reduced to safe 100-char preview.
    - `backend/app/core/kaggle_client.py` and `backend/app/api/routes/emotion/pipeline.py`:
      - removed upstream `response.text` logging from error lines; now logs status/body length only.
  - Retrieval failure observability (distinguishable from empty results):
    - `backend/app/llm_trigger/retrieval.py` `ResolvedRetrievalContext` now includes `retrieval_failed: bool`.
    - on SOP retrieval exceptions, function now logs warning with context and returns `source="retrieval_error"` + `retrieval_failed=True`.
    - `backend/app/llm_trigger/service.py` now logs retrieval-failure warnings in policy/SOP catch paths and carries `retrieval_failed` signal in `ResolvedPolicyContext`.

- Deferred to Phase 12:
  - Cross-service `print(...)` → unified structured logger migration across backend/whisperx/rag (requires shared logging contract).
  - Correlation-ID propagation across service boundaries (requires explicit cross-service header/context contract).
  - Frontend `.catch(() => {})` observability patterns (frontend pass, out of current backend/infra scope).

- Acknowledged/documented:
  - `backend/scripts/seed_nexalink.py` credential output remains a local-dev bootstrap behavior; added explicit code comment that printed defaults must not be used in non-local environments.
  - Auth exception detail logging in backend remains server-side and is accepted for this phase pending broader structured logging review.

- Verification:
  - Rebuilt backend container: `docker compose up -d --build backend`
  - Backend-focused test gate:
    - `python -m pytest tests/test_llm_trigger_service.py tests/test_assistant.py tests/test_error_sanitization.py tests/test_sop_retrieval.py -q`
    - result: `48 passed`.
  - RAG query-engine gate:
    - `python -m pytest services/rag/tests/test_query_engine.py -q`
    - result: `8 passed`.

## 2026-06-16 — Phase 9: Dependency and supply-chain hygiene

- Fixed:
  - Upgraded high-reach backend CVE packages in `backend/pyproject.toml` and regenerated lockfile:
    - `aiohttp>=3.14.0` (resolved to `3.14.1`)
    - `pyjwt[crypto]>=2.12.0` (resolved to `2.13.0`)
    - `python-multipart>=0.0.26` (resolved to `0.0.32`)
    - `starlette>=1.1.0` (resolved to `1.3.1`)
  - Moved `pytest` out of backend runtime dependency set (removed from `[project].dependencies`; retained under `[dependency-groups].dev`).
  - Hardened WhisperX image dependency sync intent:
    - `services/whisperx/Dockerfile` now uses `uv sync --no-dev`.
  - Added explicit security-risk acknowledgment comments (no behavior change):
    - `services/emotion/app.py` above `AutoModel(..., trust_remote_code=True)`
    - `services/vad/app.py` above `torch.hub.load(...)`
  - Added reusable supply-chain scan targets to `Makefile`:
    - `audit` / `audit-backend-rag` for backend + ingestion `pip-audit`
    - `audit-cuda-services` with manual instructions and CUDA image caveat.

- Deferred to Phase 12:
  - Base image digest pinning across services (defer to automated digest update workflow, e.g. Dependabot/Renovate).
  - Removing build tooling (`gcc`) from RAG production image via multi-stage Docker restructure.
  - `transformers` upgrade in backend (tracked CVE path; deferred pending dedicated compatibility verification).
  - Torch-family CVE tracking (known gap where `pip-audit` coverage is incomplete for `+cpu` variants; requires manual tracking process).
  - Model commit pinning for Emotion/VAD remote model sources (requires service-owner coordination; security-note comments added as interim acknowledgment).

- Scan gaps noted:
  - CUDA service image audit (`whisperx`, `emotion`) not completed in this pass due to image pull/build weight and runtime constraints.
  - Torch `+cpu` variant CVE coverage is not fully represented by standard `pip-audit` output.

- Verification:
  - Lock refresh:
    - containerized command: `docker compose run --rm -v ./backend:/app backend sh -c "python -m ensurepip --upgrade && python -m pip install uv && cd /app && python -m uv lock"`
    - lock update output confirms upgraded versions for `aiohttp`, `pyjwt`, `python-multipart`, `starlette`.
  - Runtime dependency exclusion check:
    - containerized command: `python -m uv sync --no-dev` then `.venv/bin/python -m pip show pytest`
    - result: `WARNING: Package(s) not found: pytest`.
  - Backend rebuild/restart:
    - `docker compose up -d --build backend`
    - result: backend image rebuilt and container started successfully.
  - Full backend test gate:
    - `python -m pytest tests/ -q`
    - result: `178 passed` (warnings only).

## 2026-06-16 — Phase 10: Error handling, observability, and silent failure surface

- Fixed:
  - `print()` → logger migration in service runtimes:
    - `services/whisperx/app.py`
    - `services/emotion/app.py`
    - `services/vad/app.py`
    - Added module-level `logger = logging.getLogger(__name__)` and replaced operational `print(...)` emissions with appropriate logger levels.
  - Removed internal exception leakage in WhisperX 500 path:
    - `services/whisperx/app.py` now logs with `logger.exception("Internal transcription error")` and returns `HTTPException(status_code=500, detail="Internal transcription error")`.
  - Added degraded-path flag to evaluator result contract:
    - `services/rag/evaluator.py` `ComplianceResult` now includes `degraded: bool = False`.
    - Fallback/neutral return paths now set `degraded=True` (no-policy context, parse failure, malformed response shape).
  - Guarded startup fire-and-forget prewarm task:
    - `backend/app/main.py` now wraps prewarm in `_prewarm_with_log()` and logs startup prewarm failures via `logger.exception(...)`.
  - Assistant provider-exhaustion visibility:
    - `backend/app/api/routes/assistant.py` retains per-provider `warning` logs for individual misses.
    - Added explicit `error` logs on provider exhaustion return paths (no response after all attempts).
  - Root readiness improvement:
    - `backend/app/main.py` `/health` now performs a fast DB connectivity check (`asyncpg` + `SELECT 1`).
    - Returns `200 {"status":"ok","db":"ok"}` when reachable.
    - Returns `503 {"status":"degraded","db":"unreachable"}` on DB failure.

- Deferred to Phase 11:
  - Circuit-breaker pattern across all LLM call paths (no open/half-open/closed state yet).
  - RAG evaluator single-shot retry gap on judge calls (`chat.completions.create` path).

- Deferred to Phase 12:
  - Cross-service correlation/request ID propagation.
  - Stage-status multi-commit partial write risk:
    - a failure between stage N and stage N+1 status writes leaves mixed stage states in the DB, detectable only by querying `job_status` rows directly.
  - Assistant degraded-path response tagging contract changes.
  - `ComplianceResult.degraded` persistence to DB/reporting schema (field now available in service contract; DB propagation deferred).

- Known gap:
  - Backend and RAG service logs remain mostly free-form text (not fully structured JSON).
  - Queryability in centralized log aggregation is still limited until structured logging format standardization lands.

- Verification:
  - RAG evaluator gate:
    - `python -m pytest services/rag/tests/test_evaluator.py -q`
    - result: `15 passed`.
  - Backend readiness behavior:
    - healthy DB check:
      - command: backend `/health`
      - response: `200 {"status":"ok","db":"ok"}`
    - broken DB URL simulation:
      - command: one-off backend run with invalid `DATABASE_URL`
      - response: `503 {"status":"degraded","db":"unreachable"}`
  - Backend rebuild:
    - `docker compose up -d --build backend` completed successfully.
  - Full backend test gate:
    - `python -m pytest tests/ -q`
    - result: `178 passed` (warnings only).

## 2026-06-16 — Phase 11: Retry hardening and circuit-breaker pattern across LLM call paths

- Fixed:
  - Closed RAG evaluator single-shot retry gap in `services/rag/evaluator.py`:
    - added `_invoke_judge_with_retry(...)` application on judge calls with bounded retries (`max 3`), exponential backoff from `0.5s` (+ jitter), transient-only retry guard.
    - on retry exhaustion, existing neutral/degraded fallback remains the terminal path (`degraded=True` for compliance fallback).
  - Hardened assistant provider calls with per-provider bounded retries in `backend/app/api/routes/assistant.py`:
    - `Ollama local`, `Ollama Cloud`, and `Groq` provider attempts now each retry transient failures up to `2` attempts before provider fallthrough.
  - Added in-process circuit-breaker singleton registry:
    - `backend/app/core/llm_circuit_breaker.py`
    - endpoint keys: `ollama_local`, `ollama_cloud`, `groq`
    - behavior: opens after `5` consecutive transient failures within `60s`, open window `30s`, half-open single-probe semantics (success closes, transient failure reopens).
    - only transient failures count toward trip threshold; non-transient failures do not trip.
  - Wired breaker usage to call sites:
    - `backend/app/api/routes/assistant.py`
      - wraps single provider attempts (inside retry loops) via endpoint-scoped breakers.
      - `CircuitOpenError` is handled as immediate provider skip/fallthrough (no retry while open).
    - `services/rag/evaluator.py`
      - wraps Groq judge single attempts through the shared `groq` breaker before retry wrapper.
      - open circuit short-circuits to existing degraded fallback path (no retry while open).
  - Added diagnostic endpoint:
    - `backend/app/main.py` → `GET /health/circuit-breakers`
    - returns state snapshot for registered breakers (`state`, `failure_count`, and open-window timestamps when applicable).
    - code comment notes this endpoint is diagnostic-only and should be restricted to internal/admin exposure before public deployment.
  - Added isolated breaker unit coverage:
    - `backend/tests/test_llm_circuit_breaker.py`
      1) starts closed; 4 transient failures do not open
      2) 5th transient failure opens
      3) open state rejects without invoking callable
      4) half-open probe success closes
      5) half-open probe transient failure reopens
      6) non-transient failure does not increment failure counter

- Retry primitive decision (documented):
  - Chosen path: minimal-delta per-call-site integration (assistant + evaluator) instead of refactoring a single shared retry utility this phase.
  - Rationale: existing backend `_invoke_chain_with_retry` is LangChain chain-interface-specific (`chain.ainvoke(inputs)`); generalizing to a shared coroutine utility was deferred to avoid broad refactor risk in a hardening pass.

- Deferred to Phase 12:
  - Redis-backed shared breaker state if deployment moves to multi-worker or multi-replica topology.
  - Embedding-path circuit breaker (`services/rag/query_engine.py::_embed_query`) — bounded retry exists; breaker intentionally not applied in this phase due to separate failure domain.
  - `ComplianceResult.degraded` DB-column/reporting persistence.
  - Assistant degraded-path response tagging in API contract.

- Known limitation:
  - In-process breaker state is per-worker. If backend scales to multiple Uvicorn workers or multiple container replicas, breaker state is not shared and open signals do not propagate across workers.
  - Groq breaker state is also split between backend and RAG service processes; cross-process threshold accumulation requires the Redis-backed shared state deferred to Phase 12.

- Verification:
  - Full backend gate:
    - `python -m pytest tests/ -q`
    - result: `185 passed` (warnings only).
  - Full RAG gate:
    - `python -m pytest services/rag/tests/ -q`
    - result: `83 passed`.

## 2026-06-16 — Phase 12: Consolidation, deferred items, and production-readiness

- Block A — deferred fixes completed:
  - A1 (`ComplianceResult.degraded` persistence + API):
    - Added `degraded` column to `policy_compliance` model/table:
      - `backend/app/models/policy.py`
      - `infra/db/01_schema.sql`
      - migration: `infra/db/06_policy_compliance_degraded.sql`
    - Wired degraded propagation from transcript-level evaluator result into persisted `PolicyCompliance` rows:
      - `backend/app/core/interaction_processing.py` now sets `degraded` from `transcript_policy_report.degraded`.
    - Included degraded signal in interaction policy-violation API payload:
      - `backend/app/api/routes/interactions.py` now selects/returns `degraded` per violation.
    - Migration execution:
      - `docker compose exec -T db psql -U vocalmind -d vocalmind -f /docker-entrypoint-initdb.d/06_policy_compliance_degraded.sql`
      - result: `ALTER TABLE`.
  - A2 (assistant degraded-path response tagging):
    - Added explicit assistant response schema with `degraded: bool`:
      - `backend/app/schemas/assistant.py` (`AssistantQueryResponse`)
    - Updated assistant query route to return typed response and set degraded semantics:
      - success/help paths => `degraded=False`
      - provider exhaustion/error fallback paths => `degraded=True`
      - file: `backend/app/api/routes/assistant.py`
    - Added regression test:
      - `backend/tests/test_assistant.py::test_process_assistant_query_sets_degraded_on_total_provider_failure`
  - A3 (`_embed_query` circuit breaker):
    - Wrapped embedding HTTP call with `get_breaker("embedding").call_sync(...)`:
      - `services/rag/query_engine.py`
    - Added breaker regression test:
      - `services/rag/tests/test_query_engine.py::TestEmbeddingCircuitBreaker::test_embed_query_raises_when_embedding_circuit_open`
    - Added breaker reset helper for deterministic tests:
      - `services/rag/llm_circuit_breaker.py::reset_breakers()`
  - A4 (stage-status partial-write transaction safety):
    - Removed per-status autocommits from `_set_job_status` and `_set_interaction_status`.
    - Wrapped stage status loops and failure-path writes in explicit transactional try/commit/rollback blocks:
      - `process_interaction(...)`: running/completed stage batches are atomic.
      - `mark_interaction_failed(...)`: interaction failure + per-stage failed statuses are atomic.
      - file: `backend/app/core/interaction_processing.py`
    - Added regression test for mid-loop failure rollback:
      - `backend/tests/test_interaction_processing_quality.py::test_mark_interaction_failed_stage_status_transaction_rolls_back_on_mid_loop_failure`
  - A5 (base image digest pinning):
    - Digest-pinned base images with tag/date comments in:
      - `backend/Dockerfile`
      - `services/rag/Dockerfile`
      - `services/emotion/Dockerfile`
      - `services/vad/Dockerfile`
      - `services/whisperx/Dockerfile`
      - `frontend/Dockerfile`
      - `frontend/Dockerfile.dev`
    - Added human-readable `# pinned: <tag> (<date>)` comments near each `FROM`.
  - A6 (RAG build-tooling runtime surface):
    - Converted `services/rag/Dockerfile` to builder + runtime multi-stage layout.
    - Build tooling (`gcc`) remains in builder only; runtime image excludes compiler toolchain.
    - Runtime dependency copy switched to virtualenv copy pattern (`/opt/venv` + PATH export).
    - Outcome:
      - ingestion image build remains long-running due to heavy model dependencies; final measured local image size snapshot remained `vocalmind-ingestion:latest 9.96GB` during this phase window.
      - runtime startup regression (`No module named 'groq'`) was fixed in-phase.
      - root cause category: **(2) dependency declaration gap** (the direct `groq` module was imported at runtime but was not declared in `services/rag/pyproject.toml` main dependencies).
      - fix:
        - added `groq>=0.30.0` to `services/rag/pyproject.toml` main `dependencies`.
        - hardened runtime interpreter selection in `services/rag/Dockerfile` by setting `VIRTUAL_ENV`, prepending venv to `PATH`, and using venv python in `CMD`.
      - post-fix verification:
        - `docker compose run --rm ingestion /opt/venv/bin/python -c "import sys, groq; print(sys.executable); print(groq.__version__)"`
        - output showed `/opt/venv/bin/python` and `groq` version `1.4.0` with no import error.

- Block B — production-readiness:
  - B1 (correlation ID propagation):
    - Added backend request context utility with ContextVar + outbound header helper + logging filter:
      - `backend/app/core/request_context.py`
    - Added middleware-level request ID handling in backend:
      - generates/propagates `X-Request-ID`
      - injects into response headers
      - installs request-id logging filter at app boot
      - file: `backend/app/main.py`
    - Wired outbound `X-Request-ID` forwarding for backend sidecar calls:
      - central Kaggle/sidecar HTTP client headers (`backend/app/core/kaggle_client.py`)
      - local VAD pipeline call (`backend/app/api/routes/emotion/pipeline.py`)
      - health-check probe calls (`backend/app/api/routes/rag.py`, `backend/app/api/routes/llm_trigger/router.py`)
    - Added sidecar request-id middleware/log propagation:
      - `services/emotion/app.py`
      - `services/vad/app.py`
      - `services/whisperx/app.py`
  - B2 (Redis-backed shared circuit breaker):
    - Not implemented this phase.
    - Trigger conditions not met: no Redis service in compose and no confirmed multi-worker rollout.
    - Remains deferred until either Redis is introduced or deployment topology requires cross-process breaker state.
  - B3 (`transformers` compatibility check):
    - Isolated compatibility gate run with `transformers==4.48.3` in backend test container.
    - Full backend test gate result under upgraded transformers: `188 passed`.
    - Initial unconstrained test run attempt surfaced an invalid major-version selection (`5.x`) and wrong test-path invocation; corrected by pinning to `4.48.3` and rerunning full gate.
    - Follow-up dependency pin landing is pending separate dependency-file update/lock refresh decision (see known limitations/open follow-ups below).

- Block C — final audit sweep findings (run before additional fixes):
  - TODO/FIXME/HACK scan:
    - no active security/data-correctness TODO/FIXME/HACK debt found in production code paths.
    - matched instances were test strings, transcript content, or notebook payloads, not live risk markers.
  - Route/org-scoping sweep:
    - reviewed route surfaces under `backend/app/api/routes`.
    - no newly introduced unscoped tenant-sensitive route found in this phase’s additions.
    - scoped routes (e.g., `knowledge.py`, interaction/assistant/rag surfaces) continue to use `CurrentUser` + org filters.
  - New dependency sweep:
    - reviewed dependency manifests:
      - `backend/pyproject.toml`
      - `services/rag/pyproject.toml`
      - `services/whisperx/pyproject.toml`
      - `services/vad/requirements.txt`
      - `services/emotion/requirements.txt`
    - no untracked/deferred dependency security gap was introduced by Phase 12 code changes themselves.

- Verification:
  - Backend full gate:
    - `python -m pytest tests/ -q`
    - result: `188 passed` (warnings only).
  - RAG full gate:
    - `python -m pytest services/rag/tests/ -q`
    - result: `84 passed`.
  - Transformers compatibility gate:
    - isolated backend run with `transformers==4.48.3`
    - result: `188 passed`.

- Known limitations / remaining accepted gaps after Phase 12:
  - In-process breaker state remains local to process boundaries:
    - per-worker within backend; and split between backend vs RAG service processes.
    - shared cross-process accumulation still requires deferred Redis-backed state.
  - `transformers` CVE closure workflow:
    - compatibility was validated in isolated test run, but dependency file/lock update to permanently move production pin forward remains pending formal dependency update step.
  - Existing prior-phase deferrals that were not in-scope for direct closure this phase remain as documented in their phase sections.

## 2026-06-16 — Audit Closing Summary (Phases 1–12)

- Phase 1: Closed major multi-tenant isolation gaps across trigger, RAG, assistant SQL execution path, and interaction/agent surfaces; added org-isolation regression tests.
- Phase 2: Implemented startup fail-fast configuration hygiene for secrets/provider keys; clarified optional HF token behavior.
- Phase 3: Enforced assistant DB least privilege (readonly role + column grants) and AST-level SQL structural allowlist/limit safeguards.
- Phase 4: Added stage-based LLM routing contract across backend and RAG with drift guard tests.
- Phase 5: Audited and documented speaker-role relabel reconciliation behavior; added observability + regression for unavailable relabel model path.
- Phase 6: Hardened watcher path confinement and DB dedup constraints for ingestion safety.
- Phase 7: Strengthened LLM trust boundaries for evaluator/synthesis prompt inputs and response-shape validation.
- Phase 8: Applied supply-chain/runtime hardening updates identified in dependency/image review.
- Phase 9: Addressed image/dependency hygiene set and documented deferred infrastructure-sensitive items.
- Phase 10: Improved silent-failure handling/observability and documented deferred degraded-propagation and transactionality items.
- Phase 11: Standardized retry posture and added in-process circuit breakers for key LLM endpoints, including diagnostic state endpoint and isolated breaker tests.
- Phase 12: Consolidated deferred items (degraded persistence/tagging, embedding breaker, transaction atomicity, digest pinning, correlation IDs), ran compatibility/sweep passes, and documented residual accepted limitations.

- Final accepted limitations at handoff:
  - Circuit-breaker state is not globally shared across workers/services without Redis-backed state.
  - Permanent `transformers` pin/lock uplift after successful compatibility gate remains to be landed explicitly.
