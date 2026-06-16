# VocalMind / NexaLink — Defense Slide Findings (Evidence-Backed)

> Generated from repo investigation. Every bullet cites a source. Items marked `⚠️ NOT FOUND` need manual input.

---

## Repo Inventory (Investigation Step 1)

**Top-level layout** (`d:\University\Grad\VocalMind`): `backend/`, `frontend/`, `services/` (vad, whisperx, emotion, rag), `infra/` (db, benchmarks, scripts, fixtures), `storage/` (docs, audio, uploads), `docs/`, `research/`, `tools/`, `docker-compose.yml`, `docker-compose.gpu.yml`, `Makefile`, `README.md`, `AGENTS.md`, `AUDIT_LOG.md`, `.github/workflows/` (source: directory listing via repo root).

**README** describes VocalMind as a modular AI ecosystem for call-center/telecom: speech (ASR, diarization, synthesis) + RAG + context-aware conversational agents (source: `README.md:3`).

**Docs index** (`docs/README.md`): explainability layer, LLM trigger guide, RAG overview, RAG ingestion pipeline, design spec (`docs/design/vocalmind-design-spec.md`), pipeline eval findings (`docs/eval/PIPELINE_FINDINGS.md`).

**Benchmark reports read:** `infra/benchmarks/reports/overnight_20260614/FULL_REPORT_v6.md` (primary for slides 7/10/11), also `FULL_REPORT.md`, `FULL_REPORT_v7.md`, `PHASE_CONFIG_PA_SCORER.md`.

**Architecture diagrams:** Mermaid flowchart in `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md:71-80`; ASCII architecture in `AGENTS.md:29-42` and pipeline flow `AGENTS.md:146-177`. No `.drawio`, `.png`, or `.excalidraw` architecture files found in repo.

**Formal graduation proposal / problem-statement document:** ⚠️ NOT FOUND — needs manual input (no `proposal*` files in repo).

---

## Slide 2 — Problem Statement

- Call-center evaluation systems often return opaque verdicts (e.g. “Contradiction Trigger fired”, “Correctness Score: 62”) without showing which utterance or policy clause drove the decision (source: `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md:7-10`).
- Before the evidence-anchored explainability layer, LLM trigger evaluation could flag behavioral issues without anchoring them to a specific transcript span; RAG compliance could score claims without surfacing the retrieved policy chunk used (source: `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md:26-29`).
- NexaLink is the seeded demo tenant: scripted call audio, policies, SOPs, and evaluation manifests live under `storage/audio/nexalink/` and `storage/docs/` (source: `README.md:285-287`, `README.md:194-197`).
- Pipeline evaluation on 6 real scripted calls found baseline **topic_match 33.3%** — topic detection misclassified most calls because keyword buckets were incomplete (source: `docs/eval/PIPELINE_FINDINGS.md:8`, `docs/eval/PIPELINE_FINDINGS.md:20-21`).
- ⚠️ NOT FOUND — explicit written “problem statement” from a formal project proposal or early commit message describing NexaLink’s *prior* setup before VocalMind. Closest repo evidence is the explainability gap and pipeline misclassification findings above.

---

## Slide 3 — Motivation and Objectives

**Stated in repo (quoted):**

- Design goal: “AI-powered call centre evaluation SaaS platform” that transcribes calls, detects emotions, evaluates policy compliance, and generates performance scores — with separate manager and agent dashboards (source: `docs/design/vocalmind-design-spec.md:11`).
- README positions the system for **call center and telecom use cases**, integrating speech processing with RAG for context-aware agents (source: `README.md:3`).
- AGENTS.md states the core flow: **upload audio → transcribe → diarize → emotion-analyze → LLM-reason → score → dashboard** (source: `AGENTS.md:15`).
- Key capability objectives listed in AGENTS.md: evidence-anchored explainability, dual-emotion fusion, RAG-grounded compliance, AI manager assistant (NL→SQL), emotion dispute workflow (source: `AGENTS.md:17-23`).

**Inferred from what is built** *(flagged as inference, not quoted objectives):*

- Multi-tenant org isolation (manager/agent roles, org-scoped data) — inferred from `AGENTS.md:15` and schema enums `UserRole`, `OrgStatus` (source: `backend/app/models/enums.py:4-14`).
- Systematic LLM provider selection via benchmarks (Ollama Cloud vs Groq) — inferred from `infra/benchmarks/reports/FULL_REPORT.md` and `FULL_REPORT_v6.md` presence.
- ⚠️ NOT FOUND — numbered list of academic project objectives (e.g. from a CSAI proposal document).

---

## Slide 4 — Literature Review / Existing Solutions

- **Groq** is the default `LLM_PROVIDER=groq` for LLM trigger chains; requires `GROQ_API_KEY` at startup (source: `backend/app/core/config.py:88-90`, `backend/app/core/config.py:137-141`, `README.md:32-33`).
- **Ollama Cloud** is an alternative provider (`LLM_PROVIDER=ollama_cloud`) using OpenAI-compatible endpoint `https://ollama.com/v1` (source: `backend/app/core/config.py:72`, `backend/app/llm_trigger/chains.py:48-49`).
- Migration benchmark rationale: **`kimi-k2.6:cloud` is not available on Groq**, so Ollama Cloud Pro is “the correct choice for model access + predictable billing” despite per-token equivalents sometimes favoring Groq on paper (source: `infra/benchmarks/reports/FULL_REPORT.md:486-493`).
- Ollama Cloud bills **flat-rate subscription** (Pro $20/mo, Max $100/mo), not per-token; benchmark reports include Groq-equivalent and OpenAI-equivalent cost columns for comparison (source: `infra/benchmarks/reports/FULL_REPORT.md:89`, `infra/benchmarks/reports/overnight_20260614/final_run_laneA_kimi_v19.md:4-10`).
- **Five Ollama Cloud candidate models** benchmarked: `kimi-k2.6:cloud`, `kimi-k2.5:cloud`, `ministral-3:8b`, `ministral-3:14b`, `qwen3.5:cloud` (source: `infra/benchmarks/reports/FULL_REPORT.md:25`, `infra/benchmarks/reports/benchmark_summary_v2.md:56`).
- Neutral judge model **`gemma3:12b`** via Ollama Cloud — explicitly “not a candidate model” (source: `infra/benchmarks/reports/benchmark_summary_v3.md:7`).
- Manager assistant provider chain in `auto` mode: **Gemini → Groq → Ollama Cloud → local Ollama** (source: `backend/app/api/routes/assistant.py:763-777`, `AGENTS.md:22`).
- Docker Compose comments show **local Ollama service disabled** with note “Ollama Cloud migration: local Ollama service disabled” (source: `docker-compose.yml:127-128`).
- Vector DB: **Qdrant** with dual collections for policy parents/children and SOP parents (source: `docs/rag/RAG_OVERVIEW.md:21-46`, `docker-compose.yml:145-161`).
- Embeddings: **Ollama** `snowflake-arctic-embed2` (source: `README.md:97`, `docker-compose.yml:66`).
- ⚠️ NOT FOUND — formal literature review or comparison to commercial call-center AI platforms (e.g. Observe.AI, Cresta) in repo docs.

---

## Slide 5 — Proposed Solution

- VocalMind is a **modular AI ecosystem** integrating speech processing (ASR, diarization, synthesis) with retrieval-augmented generation to create **context-aware conversational agents**, designed for **call center and telecom use cases** (source: `README.md:3`).
- AGENTS.md one-line summary: **Call-center AI platform** — upload audio, transcribe, diarize, emotion-analyze, LLM-reason, score, dashboard; multi-tenant with org-scoped manager and agent users (source: `AGENTS.md:15`).
- Components per README architecture table: Backend (FastAPI gateway), Frontend (React dashboards), VAD, WhisperX, Emotion, RAG, Ingestion, Explainability layer, Research notebooks (source: `README.md:9-19`).
- LLM trigger feature evaluates interactions via three analysis dimensions: **emotion shift**, **process adherence** (SOP), **NLI policy** — with RAG retrieval for grounding (source: `docs/llm_trigger/LLM_TRIGGER_FEATURE_GUIDE.md:11-15`).
- Evidence-anchored explainability standardizes: `claim or trigger → evidence → verdict` for manager-facing review (source: `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md:31-33`).

---

## Slide 6 — System Architecture

### Services and connections

| Component | Port / location | Role |
|---|---|---|
| Frontend (React/Vite) | `:3000` | Manager & agent dashboards (source: `README.md:107`, `docker-compose.yml:108-125`) |
| Backend (FastAPI) | `:8000` | API gateway, auth, pipeline worker, LLM trigger (source: `README.md:108`, `docker-compose.yml:28-105`) |
| PostgreSQL | host `5434` → container `5432` | Primary DB + readonly assistant role (source: `docker-compose.yml:8-14`, `docker-compose.yml:44-45`) |
| Qdrant | `:6333`, `:6334` | Vector store for RAG (source: `docker-compose.yml:145-161`) |
| VAD (Silero) | `:8002` | Voice activity detection (source: `README.md:13`, `docker-compose.yml:203-217`) |
| Emotion (Transformers) | host `:8001` → container `:8000` | Speech emotion recognition (source: `README.md:15`, `docker-compose.yml:219-237`) |
| WhisperX | host `:8003` → container `:8000` | ASR + diarization + speaker-role (source: `README.md:14`, `docker-compose.yml:239-277`) |
| RAG Ingestion | (no host port) | Document ingest → Qdrant (source: `docker-compose.yml:163-201`) |
| LLM providers | Groq (default) or Ollama Cloud API | Chains in `backend/app/llm_trigger/` (source: `backend/app/llm_trigger/chains.py:47-50`) |
| Local Ollama | commented out in compose | Embeddings/assistant fallback when enabled (source: `docker-compose.yml:127-143`) |

### Six audio-processing pipeline stages (`JobStage`)

Defined in `STAGE_ORDER` (source: `backend/app/core/interaction_processing.py:46-53`, `backend/app/models/enums.py:28-34`):

| # | Stage | What it does (from code/docs) |
|---|---|---|
| 1 | **diarization** | Speaker separation via WhisperX `/full/analyze` path (pyannote or channel-mode for stereo telephony) (source: `AGENTS.md:159-160`, `docker-compose.yml:255-257`) |
| 2 | **stt** | Speech-to-text transcription (WhisperX ASR) (source: `AGENTS.md:159-160`, `services/whisperx/app.py` per `AGENTS.md:111`) |
| 3 | **emotion** | Per-segment acoustic (+ text) emotion; fused acoustic×0.55 + text×0.45 (source: `AGENTS.md:161-168`, `backend/app/core/emotion_fusion.py` per `AGENTS.md:73`) |
| 4 | **reasoning** | `evaluate_interaction_triggers()` — emotion shift, process adherence, NLI policy LangChain chains + explainability (source: `AGENTS.md:169`, `backend/app/core/interaction_processing.py:736-743`) |
| 5 | **scoring** | Computes `InteractionScore` (empathy, policy, resolution, overall) from LLM trigger report (source: `backend/app/core/interaction_processing.py:761-816`) |
| 6 | **rag_eval** | RAG-grounded policy/SOP context resolution during trigger evaluation (Qdrant retrieval + compliance paths) (source: `AGENTS.md:152`, `docs/llm_trigger/LLM_TRIGGER_FEATURE_GUIDE.md:43-49`) |

*Note:* Upload creates 6 `ProcessingJobs` in this order (source: `AGENTS.md:151-152`). Jobs for diarization/stt/emotion are marked running together at pipeline start; all six marked completed at end (source: `backend/app/core/interaction_processing.py:624-626`, `840-841`).

### Six LLM benchmark stages (separate from `JobStage`)

Used in Ollama Cloud quality benchmarks: `emotion_shift`, `process_adherence`, `nli_policy`, `rag_judge`, `text_to_sql`, `fast_classification` (source: `infra/benchmarks/reports/overnight_20260614/FULL_REPORT_v6.md:13`, `backend/app/llm_trigger/chains.py:33-40`).

---

## Slide 7 — Methodology

### End-to-end data flow

1. Audio uploaded (`POST /api/v1/interactions`) or auto-ingested from `storage/audio/<org_slug>/` (source: `README.md:267-277`, `AGENTS.md:147-152`).
2. Worker fetches audio → `/full/analyze` (VAD → WhisperX → emotion) → normalize → persist transcript/utterances/emotion events (source: `AGENTS.md:157-165`).
3. LLM trigger evaluation → policy resolution → scores → `processing_status=completed` (source: `AGENTS.md:169-171`, `backend/app/core/interaction_processing.py:834`).
4. Manager views via `GET /api/v1/interactions/{id}` with optional `include_llm_triggers=true` (source: `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md:47`).

### Benchmark methodology (from `FULL_REPORT_v6.md`)

- **Scope:** “six Ollama Cloud pipeline stages on **synthetic ground-truth data**” (source: `FULL_REPORT_v6.md:13`).
- **Scale:** “**3,219 model calls**, zero errors” from retry-v2 run `overnight_20260614/` (source: `FULL_REPORT_v6.md:5`, `FULL_REPORT_v6.md:13`).
- **Scoring pivot:** Replaced LLM judge with **exact match / F1 against reference labels** on saved `raw_response` JSON — “no new model calls” (source: `FULL_REPORT_v6.md:47`).
- **Emotion_shift validation sub-run:** `emotion_shift_v2.json` at **n=170** with fixed prompt (source: `FULL_REPORT_v6.md:5`, `FULL_REPORT_v6.md:53-55`).
- **PA re-score:** Fuzzy scorer re-scored **765 existing observations** (source: `FULL_REPORT_v6.md:5`, `FULL_REPORT_v6.md:59`).
- **Earlier migration benchmark** (context): five models, **135-sample stratified subset** from **550-sample** ground-truth pool; parallel 5-model execution; neutral `gemma3:12b` judge (source: `infra/benchmarks/reports/FULL_REPORT.md:25`).
- **Metrics per stage:** exact match (all), mean F1 (PA), execution match (text_to_sql), plus parseable % for emotion_shift (source: `FULL_REPORT_v6.md:21-28`, `FULL_REPORT_v6.md:49-51`).
- **Limitations acknowledged:** synthetic data only; ~3,328 near-duplicate pairs in pool; no real call-center transcripts in benchmark pool (source: `FULL_REPORT_v6.md:93-94`).

---

## Slide 8 — Main Features

**Implemented and wired (API / entrypoints confirmed):**

- **Auth:** password login, Google OAuth, logout (`/api/v1/auth/*`) (source: `backend/app/api/routes/auth/router.py:69-190`, `README.md:11`).
- **Interaction upload & management:** create, list, detail, reprocess, delete, processing-status, emotion-comparison, audio stream (source: `backend/app/api/routes/interactions.py:355-1372`).
- **Audio folder auto-ingest:** watches `storage/audio/<org_slug>/` every 15s (source: `README.md:267-277`).
- **Dashboard stats:** `GET /api/v1/dashboard/stats` (source: `backend/app/api/routes/dashboard.py:45`).
- **LLM trigger probes:** emotion-shift, process-adherence, nli-policy-check endpoints (source: `backend/app/api/routes/llm_trigger/router.py:71-143`).
- **Manager AI assistant:** `POST /api/v1/assistant/query` (chat + text-to-SQL modes) (source: `backend/app/api/routes/assistant.py:994`).
- **Knowledge base CRUD:** policies, FAQs, KB upload/toggle/delete (source: `backend/app/api/routes/knowledge.py:115-700`).
- **RAG query proxy:** `POST /api/v1/rag/query` (source: `backend/app/api/routes/rag.py:163`).
- **Emotion dispute workflow:** agent dispute + manager review endpoints (source: `backend/app/api/routes/emotion/dispute_router.py:4-14`).
- **Inference microservice proxies:** VAD, transcription, diarization, full analyze, emotion analyze/fuse/process (source: `backend/app/api/routes/vad/router.py`, `transcription/router.py`, `diarization/router.py`, `full/router.py`, `emotion/router.py`).
- **Evidence-anchored explainability UI:** `EvidenceAnchoredExplainabilityPanel` on manager session detail (source: `docs/llm_trigger/LLM_TRIGGER_FEATURE_GUIDE.md:86-93`).
- **GPU compose overlay:** `make up-gpu` / `docker-compose.gpu.yml` (source: `README.md:167-176`).
- **Demo mode for frontend clients** (recent): commit `78c51b5` “enable fe demo mode for potential clients” (source: `git log`).

**Documented but limited / not production-wired:**

- `fast_classification` benchmark stage has “**no production call site** wired in backend/service runtime flows” (source: `backend/app/llm_trigger/chains.py:31-32`).
- Speech **synthesis** listed in README tagline; no dedicated synthesis microservice in architecture table implementation rows (source: `README.md:3` vs `README.md:9-19`).

---

## Slide 9 — Technical Implementation

### Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLModel, asyncpg, LangChain (source: `README.md:11`, `README.md:28`, `AGENTS.md:85`) |
| Frontend | React 18, Vite, Tailwind v4, MUI, Radix/shadcn, pnpm (source: `README.md:12`, `AGENTS.md:103`) |
| VAD | Silero, FastAPI (source: `README.md:13`) |
| ASR/Diarization | WhisperX, pyannote, DistilBERT speaker-role classifier (source: `README.md:14`, `README.md:56-66`) |
| Emotion | Transformers / FunASR emotion2vec (source: `README.md:15`, `AGENTS.md:109`) |
| RAG | LlamaIndex, Docling, Qdrant, Groq/Ollama LLMs (source: `README.md:16-17`, `docs/rag/RAG_OVERVIEW.md:12-15`) |
| DB | PostgreSQL 17 (source: `docker-compose.yml:9`) |
| CI | GitHub Actions: security (Gitleaks), backend, frontend, RAG, quality benchmarks (source: `.github/workflows/ci.yml:1-34`, `README.md:202`) |

### `build_llm(stage=...)` routing — current state

- **Implemented:** `build_llm(fast=False, stage=...)` with `get_model_for_stage(stage)` resolving per-stage env overrides, then class fallback to `OLLAMA_CLOUD_HEAVY_MODEL` or `OLLAMA_CLOUD_FAST_MODEL` (source: `backend/app/llm_trigger/chains.py:44-88`, `91-126`).
- **Stage → model class map:** heavy = `emotion_shift`, `process_adherence`, `text_to_sql`; fast = `nli_policy`, `rag_judge`, `fast_classification`, `rag_synthesis` (source: `backend/app/llm_trigger/chains.py:33-40`).
- **Production chain wiring:** `_resolve_chain_model` calls `build_llm(fast=False, stage=stage)` when `LLM_PROVIDER=ollama_cloud`; when `groq`, uses shared `ChatGroq` via `_get_shared_model()` — **per-stage routing does not apply on Groq path** (source: `backend/app/llm_trigger/chains.py:134-139`, `142-150`).
- **JSON object mode** bound on emotion_shift, process_adherence, nli_policy chains for Ollama Cloud (source: `backend/app/llm_trigger/chains.py:153-158`, `186-216`; also `FULL_REPORT_v7.md:11`).

### Per-stage env var design

Defined in `backend/app/core/config.py:73-84` and passed through `docker-compose.yml:77-88`:

- Global: `OLLAMA_CLOUD_HEAVY_MODEL` (default `kimi-k2.6:cloud`), `OLLAMA_CLOUD_FAST_MODEL` (default `ministral-3:8b`)
- Per-stage (new names): `OLLAMA_MODEL_EMOTION_SHIFT`, `OLLAMA_MODEL_PROCESS_ADHERENCE`, `OLLAMA_MODEL_NLI_POLICY`, `OLLAMA_MODEL_RAG_JUDGE`, `OLLAMA_MODEL_TEXT_TO_SQL`, `OLLAMA_MODEL_FAST_CLASSIFICATION`, `OLLAMA_MODEL_RAG_SYNTHESIS`
- Legacy aliases: `OLLAMA_EMOTION_SHIFT_MODEL`, `OLLAMA_PROCESS_ADHERENCE_MODEL`, `OLLAMA_NLI_MODEL`
- Provider switch: `LLM_PROVIDER` = `groq` (default) | `ollama_cloud` (source: `backend/app/core/config.py:87-90`)

*`FULL_REPORT_v6.md` (2026-06-15) stated “There are no per-stage env vars today” — superseded in code and `FULL_REPORT_v7.md:13` which documents wiring added in Prompt 18.*

### `OLLAMA_CLOUD_HEAVY_MODEL` global setup

- Default **`kimi-k2.6:cloud`** in config, `.env.example`, and docker-compose (source: `backend/app/core/config.py:73`, `docker-compose.yml:77`, `backend/.env.example:68`).
- v6 finding: single heavy model is best compromise but sacrifices **~0.070 cumulative points (~7.0 pp)** vs per-stage winners (source: `FULL_REPORT_v6.md:80-86`).

### `utterances.speaker` → `speaker_role` schema fix

- Production PostgreSQL schema column is **`speaker_role`** (`speaker_role_enum`) (source: `infra/db/01_schema.sql:31`, `infra/db/01_schema.sql:151`).
- Text-to-SQL assistant schema documents `utterances.speaker_role` (source: `backend/app/api/routes/assistant.py:106`, `backend/app/api/routes/assistant.py:430`).
- Migration audit identified and fixed bug: assistant had used `utterances.speaker` → corrected to `speaker_role` (source: `infra/benchmarks/reports/FULL_REPORT.md:25`).
- Regression test: `test_assistant_schema_uses_speaker_role_not_speaker` (source: `backend/tests/test_assistant.py:58-63`).

### Groq fallback handling

- **LLM trigger:** `LLM_PROVIDER=groq` uses `ChatGroq` with `GROQ_API_KEY`; startup **hard-fails** if key missing (source: `backend/app/llm_trigger/chains.py:80-87`, `backend/app/core/config.py:137-141`).
- **Manager assistant:** `_groq_chat_complete` returns `None` if no key; in `auto` mode tries Gemini then Groq then Ollama Cloud then local Ollama (source: `backend/app/api/routes/assistant.py:635-639`, `763-777`).
- **README:** `GROQ_API_KEY` required when `LLM_PROVIDER=groq`; **optional when using Ollama Cloud** (source: `README.md:32-33`).
- **Chains retry:** `_invoke_chain_with_retry` — up to 3 attempts on rate-limit/timeout/transient errors (source: `backend/app/llm_trigger/chains.py:161-183`).

### DB port config

- **Docker Compose:** host port **`5434`** mapped to container `5432` (source: `docker-compose.yml:13-14`).
- **`backend/.env.example`:** documents host port **`5433`** “to avoid conflicts with a native PostgreSQL service … bound to 5432 on Windows” (source: `backend/.env.example:24-27`).
- **Eval repro doc:** “db on 5433 to avoid native Postgres conflict” (source: `docs/eval/PIPELINE_FINDINGS.md:141`).
- *Port mismatch between compose (5434) and `.env.example` (5433) is present in repo — verify which is active in your deployment.*

---

## Slide 10 — Testing and Evaluation

### Test suite

**Backend (`backend/tests/`):** 36 test files; **~183** `def test_*` functions counted via repo grep (source: `backend/tests/` file list; grep count).

**Coverage areas (representative):**
- Auth, security headers, P0 security, unauthorized access (source: `test_auth.py`, `test_p0_security.py`, `test_security.py`)
- Interaction ingestion, processing quality, LLM triggers, emotion comparison (source: `test_interaction_ingestion.py`, `test_interaction_processing_quality.py`, `test_llm_trigger_service.py`)
- Assistant SQL guards, tenant isolation, readonly DB permissions (source: `test_assistant_sql_structure_guard.py`, `test_assistant_tenant_guard.py`, `test_assistant_readonly_db_permissions.py`)
- Org isolation across agents, RAG, LLM trigger cache (source: `test_*_isolation.py` files)
- Config startup validation (Groq/Ollama key fail-fast) (source: `test_config_startup_validation.py`)
- Inference routes/services, pipeline, dashboard, emotion fusion (source: matching `test_*.py` files)
- Tests use **SQLite in-memory** per AGENTS.md (source: `AGENTS.md:87`)

**Services tests:** whisperx (channel diarization, speaker role, transcribe) + rag config — **~18** tests (source: `services/whisperx/tests/`, `services/rag/tests/` grep counts).

**Frontend Vitest:** 11 test files under `frontend/src/tests/` (e.g. SessionDetail, ManagerAssistant, LLMTriggerSections) (source: glob `frontend/src/tests/*.test.*`).

**Frontend Cypress E2E:** **14** spec files (`auth`, `manager-dashboard`, `session-detail`, `knowledge-base`, `agent-calls`, etc.) (source: `frontend/cypress/e2e/*.cy.ts`).

**Containerized / CI:** `.github/workflows/ci.yml` runs security audit (Gitleaks); separate `backend.yml`, `frontend.yml`, `rag_ci.yml`, `quality-benchmarks.yml` referenced in README (source: `README.md:202`, `.github/workflows/ci.yml`).

### Benchmark evaluation (from `FULL_REPORT_v6.md`)

| Item | Value | Source |
|---|---|---|
| Observations | 3,219 model calls, 0 API errors | `FULL_REPORT_v6.md:5`, `:13` |
| Stages benchmarked | 6 (emotion_shift, process_adherence, nli_policy, rag_judge, text_to_sql, fast_classification) | `FULL_REPORT_v6.md:13` |
| Candidate models (migration report) | 5 Ollama Cloud models + neutral judge | `FULL_REPORT.md:25` |
| Primary metrics | exact match (all), mean F1 (PA), execution match (SQL), parseable % | `FULL_REPORT_v6.md:21-28`, `:47` |
| ES prompt validation | n=170 full re-run | `FULL_REPORT_v6.md:5`, `:53-55` |
| Judge calibration set | 48 samples, **0/49 scored** in v6 limitations | `FULL_REPORT_v6.md:92` |

**Pipeline eval (non-benchmark):** `tools/evaluate_pipeline.py` scores real scripted calls on agent_match, topic_match, resolution_match, SOP retrieval, turn ratio, emotion cosine (source: `docs/eval/PIPELINE_FINDINGS.md:62-74`).

---

## Slide 11 — Results

### Final winner configuration (latest ground-truth rescoring)

**Winner stack (highlighted for defense):**
- `emotion_shift` -> **`kimi-k2.5:cloud`**
- `nli_policy` -> **`kimi-k2.5:cloud`**
- `process_adherence` -> **`ministral-3:8b`**
- `fast_classification` -> **`ministral-3:8b`**
- `rag_judge` -> **`qwen3.5:cloud`**
- `text_to_sql` -> **`qwen3.5:cloud`**

**Final exact accuracy (latest merged checkpoints with targeted retry rescoring):**

| Stage | Final exact |
|---|---:|
| emotion_shift | **76.5%** |
| nli_policy | **87.2%** |
| process_adherence | **84.3%** |
| fast_classification | **90.3%** |
| rag_judge | **98.0%** |
| text_to_sql | **74.0%** |

### Previous attempts (to show iteration path)

| Stage | Earlier baseline (v6) | Mid attempt (v20) | Final winner run |
|---|---:|---:|---:|
| emotion_shift | 53% | 69.4% | **76.5%** |
| nli_policy | 52% | 74.4% | **87.2%** |
| process_adherence | F1=0.539 (scorer in v6) | 57.5% exact | **84.3% exact** |
| fast_classification | 69% | 67.5% | **90.3%** |
| rag_judge | 95% | 96.0% | **98.0%** |
| text_to_sql | 54% | 74.0% | **74.0%** |

**Interpretation for slide narration:**
- We did not jump to a single run; we iterated through baseline -> targeted retries -> scorer hardening -> final stack selection.
- The largest gains came from fixing scoring and extraction edge-cases for `process_adherence`, `nli_policy`, and `fast_classification`.
- Remaining hard area is `text_to_sql` (execution-based ceiling), while quality-critical policy/compliance stages are now strong.

*(v6 baseline source: `infra/benchmarks/reports/overnight_20260614/FULL_REPORT_v6.md`; v20 delta source: `infra/benchmarks/reports/overnight_20260614/targeted_retry_delta_v20.csv`; final exact values from latest merged checkpoint rescoring in this session.)*

### Pipeline eval on scripted calls (separate from Ollama benchmark)

| Axis | Baseline → Final |
|---|---|
| topic_match | 33.3% → **100.0%** |
| resolution_match | 33.3% → **83.3%** |
| sop_retrieval_match | 33.3% → **100.0%** |
| avg_turn_ratio | 2.17 → **0.94** |
| avg_emotion_cosine_fused | 0.894 → **0.948** |

(source: `docs/eval/PIPELINE_FINDINGS.md:7-14`)

### Cost note (migration benchmark)

At N=100 interactions/month, Groq-equiv ~$5.46 but **kimi-k2.6 not on Groq** — Ollama Cloud Pro ($20/mo) recommended for model access (source: `infra/benchmarks/reports/FULL_REPORT.md:468-493`).

---

## Slide 12 — Challenges and Lessons Learned

| Challenge | Resolution | Source |
|---|---|---|
| **Opaque LLM/RAG verdicts** — triggers and compliance scores without utterance/policy evidence | Evidence-anchored explainability layer: `triggerAttributions` + `claimProvenance` on interaction detail | `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md:26-33`; merge `6a3fc47` |
| **Topic misclassification (33% topic_match)** — incomplete keyword buckets, LLM defaulting money mentions to billing | Added topic buckets, resolution graphs, full-transcript detection, strong-signal override of LLM topic | `docs/eval/PIPELINE_FINDINGS.md:20-26`; commit `5bd6766` |
| **Production schema bug** — text-to-SQL assistant used `utterances.speaker` instead of `speaker_role` | Fixed assistant schema to `speaker_role`; added regression test | `FULL_REPORT.md:25`; `backend/app/api/routes/assistant.py:106`; `backend/tests/test_assistant.py:58-63` |
| **LLM judge wrong on model rankings** — especially emotion_shift (parse vs accuracy conflated) | Pivoted benchmark primary metric to ground-truth exact match / F1 | `FULL_REPORT_v6.md:45-47`, `:49-51` |
| **PA benchmark scores understated** — scorer regex `,(?=[A-Z])` vs `", Confirm..."` ground truth | Fixed `ground_truth_scorer.py` reference parse + fuzzy step_key matching; kimi-k2.6 F1 0.508→0.539 | `FULL_REPORT_v6.md:57-59`; `PHASE_CONFIG_PA_SCORER.md:36-37` |
| **kimi-k2.5 emotion_shift unparseable JSON (54%)** | Closed four-label schema + JSON mode in benchmark; 53% exact at 100% parseable on n=170 | `FULL_REPORT_v6.md:53-55` |
| **Cross-org policy/FAQ mutation** — security/data isolation breach | Critical fix in commit `4f5016e` / `fa90781` “prevent cross-org policy/FAQ mutation” | `git log` |
| **Speaker role diarization errors** — agent closings tagged as customer | Removed “thank you” from customer cues; cluster-level role assignment; DistilBERT classifier | `docs/eval/PIPELINE_FINDINGS.md:55-58`; commit `a8aaa8e` |
| **WhisperX model re-download on every container recreate** | Persist HF/torch caches via Docker volume `whisperx_cache` | commit `6e29472`; `docker-compose.yml:267-270` |
| **Groq quota exhaustion during eval** — deterministic fallback path needed | Pipeline-side resolution heuristic aligned with GT wording; documented Groq TPD limit | `docs/eval/PIPELINE_FINDINGS.md:136` |
| **Dev DB port conflict with native PostgreSQL** | Non-default host ports documented (5433 in `.env.example`, 5434 in compose) | `backend/.env.example:24-27`; `docker-compose.yml:14`; `PIPELINE_FINDINGS.md:141` |
| **One heavy model vs three stage winners** | Quantified 7.0 pp gap; per-stage env vars + `build_llm(stage=...)` recommended | `FULL_REPORT_v6.md:63-86`; implemented in `chains.py` per `FULL_REPORT_v7.md:13` |
| **Over-segmented transcripts (turn_ratio 2.17)** | `merge_short_same_speaker_segments()` in WhisperX | `docs/eval/PIPELINE_FINDINGS.md:51-53` |

---

## Slide 13 — Conclusion

*(Synthesis only — derived from findings in slides 2–12, not new investigation.)*

- Built **VocalMind**: a multi-tenant call-center AI platform integrating WhisperX ASR/diarization, emotion analysis, RAG-grounded LLM trigger evaluation, and manager/agent dashboards (source: synthesis of `README.md:3`, `AGENTS.md:15-23`).
- Shipped **evidence-anchored explainability** so compliance and coaching verdicts trace to transcript spans and retrieved policy/SOP/KB chunks (source: `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md:31-33`).
- Ran **large-scale Ollama Cloud benchmarks** (3,219 calls, six LLM stages) and ground-truth re-scoring; identified per-stage model winners and quantified single-vs-multi-model tradeoff (source: `FULL_REPORT_v6.md:5-13`, `:63-86`).
- Improved **pipeline accuracy on NexaLink/Meridian scripted calls** — topic_match 33%→100%, resolution_match 33%→83% (source: `docs/eval/PIPELINE_FINDINGS.md:7-14`).
- Hardened production: schema fix (`speaker_role`), cross-org mutation fix, provider fail-fast validation, JSON mode on LLM chains (source: slides 9–12 citations).
- Strongest benchmark stages: **rag_judge 95%**, **fast_classification 69%**; weakest: **process_adherence F1≈0.54** (source: `FULL_REPORT_v6.md:21-28`).

---

## Slide 14 — Future Work

### From repo docs / code markers

- **Deploy emotion_shift prompt fix to production end-to-end** — validated at n=170 in benchmark path; v6 action item #2 (source: `FULL_REPORT_v6.md:105`).
- **Set per-stage model env vars to benchmark winners** — e.g. ES→kimi-k2.5, PA→kimi-k2.6, NLI→ministral-3:8b; recovers ~7.0 pp vs single kimi-k2.6 heavy (source: `FULL_REPORT_v6.md:104`; env vars exist in `config.py:75-84` but default empty).
- **Judge calibration** — 48-sample set remains largely unscored; low priority for selection but unvalidated as monitoring signal (source: `FULL_REPORT_v6.md:92`, `:108`).
- **Ground-truth dedup cleanup** — ~3,328 near-duplicate pairs may inflate metrics (source: `FULL_REPORT_v6.md:93`).
- **Real-transcript benchmark extension** — current pool is synthetic only (source: `FULL_REPORT_v6.md:94`).
- **NLI / text_to_sql prompt tweaks** — +13 pp / +6 pp at n=20, not full-scale confirmed (source: `FULL_REPORT_v6.md:95`, `:107`).
- **Human evaluation automation** — “not yet automated in the repo” (source: `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md:403`).
- **Multi-party calls / warm transfers / IVR** — broader support future work (source: `docs/eval/PIPELINE_FINDINGS.md:135`).
- **Telephony-quality eval** — need 8 kHz μ-law eval split (source: `docs/eval/PIPELINE_FINDINGS.md:133`).
- **PII redaction** before transcript persistence — out of scope so far (source: `docs/eval/PIPELINE_FINDINGS.md:134`).
- **Trained speaker-role classifier** — deferred until real labeled call data (source: `docs/eval/PIPELINE_FINDINGS.md:132`).
- **Wire `fast_classification` in production** — benchmarked but no runtime call site (source: `backend/app/llm_trigger/chains.py:31-32`).
- **Switch default `LLM_PROVIDER` to `ollama_cloud`** in production deployments once keys and per-stage models configured — currently defaults to `groq` (source: `backend/app/core/config.py:90`, `docker-compose.yml:90`).

### `build_llm(stage=...)` — current state (code verification)

| Aspect | State | Source |
|---|---|---|
| Function exists with `stage` parameter | **Implemented** | `backend/app/llm_trigger/chains.py:44-88` |
| `get_model_for_stage()` + env overrides | **Implemented** | `backend/app/llm_trigger/chains.py:91-126`, `config.py:75-84` |
| Chain builders pass stage to resolver | **Implemented** (ollama_cloud path) | `chains.py:134-138`, `186-216` |
| Per-stage overrides in docker-compose | **Present** (empty defaults) | `docker-compose.yml:79-88` |
| Groq production path uses per-stage routing | **No** — shared `ChatGroq` model | `chains.py:137-139`, `80-87` |
| v6 report “env vars not wired” | **Superseded** by v7/code — wiring exists; overrides must be set explicitly | `FULL_REPORT_v6.md:65`; `FULL_REPORT_v7.md:13` |

### TODO/FIXME scan

- AUDIT_LOG states no active security/data-correctness TODO/FIXME in production paths (source: `AUDIT_LOG.md:651-652`).
- ⚠️ NOT FOUND — GitHub open issues list (not fetched; use `gh issue list` if needed).

---

*End of findings document. Row-level benchmark data: `infra/benchmarks/reports/overnight_20260614/*_groundtruth.json`, `emotion_shift_v2_groundtruth.json` (per `FULL_REPORT_v6.md:118`).*
