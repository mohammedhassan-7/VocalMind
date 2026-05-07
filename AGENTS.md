# VocalMind — Repository Context

> AI agent & contributor onboarding. Read fully before working on the codebase.

---

## What VocalMind Does

Call-center AI platform: **upload audio → transcribe → diarize → emotion-analyze → LLM-reason → score → dashboard**. Multi-tenant — every `Organization` has manager and agent `User`s; all data is org-scoped.

Key capabilities:

- **Evidence-anchored explainability** — every LLM trigger verdict traces back to transcript spans + retrieved policy/SOP evidence (no hallucinated claims)
- **Dual-emotion fusion** — acoustic (speech) + text emotion signals combined per-utterance
- **RAG-grounded compliance** — policy/SOP docs ingested into Qdrant, retrieved during trigger evaluation
- **AI Manager Assistant** — natural-language → SQL → answer (Gemini → Groq → Ollama fallback)
- **Emotion dispute workflow** — agents flag emotion events; managers review

---

## Architecture

```
  Frontend (:3000) ──REST──▶ Backend (:8000) ──▶ PostgreSQL (5432)
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
          VAD (:8002)    WhisperX (:8003)   Emotion (:8001)
          Silero          ASR+Diarize       FunASR emotion2vec
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
           Qdrant          Ollama           Groq
         (6333/6334)     (:11434)         Cloud API
         Vector DB      Embeddings       LLM chains
```

**`IS_LOCAL` switch** — `true` = inference hits Docker containers; `false` = hits remote Kaggle server via `BaseKaggleClient`. Docker Compose sets `IS_LOCAL=true`; local dev with `make support-up` also uses `true`.

---

## Directory Structure

```
backend/                  FastAPI API gateway
├── app/main.py            App factory, lifespan (tables → seed → worker → audio watcher)
├── app/api/
│   ├── main.py            Router aggregator — 16 domain routers
│   ├── deps.py             DI: get_db, get_current_user, get_supabase
│   └── routes/
│       ├── interactions.py Upload/list/detail/reprocess/emotion-comparison (1346 lines)
│       ├── dashboard.py    8 concurrent DB queries + 5-min TTL cache
│       ├── assistant.py    Text-to-SQL AI assistant (Gemini→Groq→Ollama, 888 lines)
│       ├── knowledge.py    Policy/FAQ/KB CRUD + PDF upload (695 lines)
│       ├── rag.py          RAG proxy (health + query)
│       ├── auth/           Login (password + Google OAuth), logout, cookie sessions
│       ├── emotion/        Analyze, fuse, dispute (router, service, pipeline, dispute_router)
│       ├── full/           Combined analysis (VAD → ASR → emotion in one call)
│       └── llm_trigger/   Endpoints: emotion-shift, process-adherence, nli-policy-check
├── app/core/
│   ├── config.py           Settings(BaseSettings) — all env config
│   ├── database.py         Async SQLAlchemy engine
│   ├── security.py         JWT create, bcrypt
│   ├── cache.py            DashboardCache (5-min TTL)
│   ├── audio_resolver.py   Resolve audio from local FS or Supabase Storage
│   ├── inference_contracts.py  Normalize all microservice responses, emotion label maps
│   ├── emotion_fusion.py  Acoustic×0.55 + text×0.45 fusion (+0.08 agree, −0.12 disagree)
│   ├── kaggle_client.py   BaseKaggleClient — HTTP POST with retry for remote inference
│   └── interaction_processing.py  Processing pipeline worker (649 lines, CORE)
├── app/llm_trigger/
│   ├── service.py          ~2000-line judging/reasoning engine (MOST COMPLEX)
│   ├── schemas.py          Evidence/Attribution/Provenance Pydantic models
│   ├── retrieval.py        Qdrant SOP/Policy/KB retrievers (552 lines)
│   ├── chains.py           LangChain ChatGroq chains with exponential backoff
│   └── prompts.py          Prompt templates with _INJECTION_GUARD
├── app/models/             18 SQLModel tables + enums.py (10 enum types)
├── app/schemas/assistant.py
├── scripts/                seed_nexalink.py, purge, migrate_parsed_docs.py
├── pyproject.toml          Python 3.12, fastapi, sqlmodel, langchain-groq, torch CPU
├── .env.example            49-line template
└── tests/                  22 pytest files (SQLite in-memory)

frontend/                 React dashboard
├── src/app/
│   ├── App.tsx             ThemeProvider → AuthProvider → RouterProvider
│   ├── routes.tsx          /login, /manager/*, /agent/*
│   ├── services/api.ts     ALL API calls, 864 lines, typed fetch wrapper
│   ├── contexts/           AuthContext (cookie+sessionStorage), ThemeContext
│   ├── components/
│   │   ├── manager/        Dashboard, SessionInspector, SessionDetail,
│   │   │                   ManagerAssistant, KnowledgeBase (954 lines),
│   │   │                   EmotionComparisonPanel, EvidenceAnchoredExplainabilityPanel
│   │   ├── agent/          AgentDashboard, AgentCalls, AgentCallDetail (coaching view)
│   │   ├── layouts/        ManagerLayout, AgentLayout, UserNav
│   │   └── ui/             48 shadcn/ui Radix wrappers
│   └── pages/Login.tsx
├── package.json            React 18.3, Vite 6.3, Tailwind 4.1, MUI 7, pnpm
├── vite.config.ts          Manual chunks, @→./src alias
└── cypress/e2e/            12 E2E spec files

services/                 Microservices
├── vad/app.py             Silero VAD, POST /split → base64 clips (port 8002)
├── emotion/app.py         FunASR emotion2vec, POST /predict, mono 16kHz 30s cap (port→8001)
├── whisperx/
│   ├── app.py             POST /transcribe: transcribe→align→diarize→speaker-role→overlap (port→8003)
│   └── speaker_role_classifier.py  3-tier: text cues → DistilBERT → diarization fallback
└── rag/
    ├── main.py            CLI: --ingest, --watch, -q, --compliance
    ├── ingest.py           Docling → clean → parent/child chunks → Qdrant (814 lines)
    ├── query_engine.py    RAGQueryEngine: dual collections (parents/children)
    ├── evaluator.py       PolicyComplianceEvaluator + AnswerCorrectnessEvaluator (Groq judge)
    └── pyproject.toml      Python 3.11, docling, qdrant-client, llama-index

infra/
├── db/                    01_schema.sql (v5.2: 17 tables, 10 enums, 14 indexes),
│                          02_seed.sql (NileTech + CairoConnect demo data)
├── scripts/               seed/, eval/ (5 component scripts + eval_all.py),
│                          e2e_local_audio.py, migrate.py, prepare_speaker_role_model.py
├── benchmarks/            thresholds.json, expected/ (gold standards), reports/
└── fixtures/audio/        Test fixtures (gitignored — wav/mp3 not committed)

storage/                  Local storage (audio files gitignored)
├── docs/nexalink/        SOP procedures (5), policy docs (3), KB (1) — PDF+DOCX
└── audio/nexalink/       5 scripted call recordings, named CALL_<NN>_<agent>_<scenario>.wav
                          Auto-ingested by audio_folder_watcher on backend startup +
                          every 15s while running (drop a file → it gets queued)

data/                     Parsed SOP markdown/JSON for fallback retrieval
research/                 Jupyter notebooks (emotion, ASR, diarization, finetuning, voice-gen)
docs/                    Technical docs (explainability, LLM trigger, RAG, design spec, frontend)
.github/workflows/       ci.yml, backend.yml, frontend.yml, rag_ci.yml, quality-benchmarks.yml
```

---

## Core Data Flow — Audio Processing Pipeline

This is the system's primary workflow. All code paths lead through here.

```
POST /api/v1/interactions              POST /.../from-storage
   │ (multipart audio)                    │ (Supabase path)
   └──────────────┬───────────────────────┘
                  ▼
   Create Interaction (status=pending) + 6 ProcessingJobs
   (stages: diarization → stt → emotion → reasoning → scoring → rag_eval)
                  │
                  ▼
   interaction_processing.py  —  _worker_loop
   ┌──────────────────────────────────────────────────┐
   │ 1. Claim interaction, release pool during I/O    │
   │ 2. fetch_audio_bytes() — local FS or Supabase    │
   │ 3. Call /full/analyze (local or Kaggle)          │
   │    → VAD splits → WhisperX transcribe+diarize     │
   │    → Emotion per segment → build_local_full_resp │
   │ 4. inference_contracts.py normalizes response     │
   │    - Label mapping (joy→happy, fear→frustrated…)  │
   │    - Text-fallback when acoustic returns neutral  │
   │ 5. Persist: Transcript → Utterances → EmotionEvents│
   │ 6. emotion_fusion.py fuses per-utterance:         │
   │    acoustic×0.55 + text×0.45                     │
   │    +0.08 agreement, −0.12 disagreement penalty    │
   │ 7. evaluate_interaction_triggers() [with timeout] │
   │ 8. Resolve policies → compute scores             │
   │ 9. Mark ProcessingJobs completed                 │
   └──────────────────────────────────────────────────┘
                  │
                  ▼
   GET /api/v1/interactions/{id}  →  Dashboard
   GET /.../{id}/emotion-comparison
```

### LLM Trigger Evaluation (step 7 above, `llm_trigger/service.py`)

The ~2000-line reasoning engine. For each interaction:

1. **Detect topic** — keyword classification (refund/billing/tech/account_access)
2. **Chunk transcript** — rolling 8-turn windows, stride 4
3. **Run 3 LangChain chains** via ChatGroq (with exponential backoff on rate limits):
   - **Emotion shift** — sarcasm, passive-aggression, cross-modal contradictions
   - **Process adherence** — compare transcript vs `RESOLUTION_GRAPHS` (expected SOP steps per topic)
   - **NLI policy** — classify as Entailment / Benign Deviation / Contradiction / Policy Hallucination
4. **Cross-modal dissonance** — text vs acoustic polarity mismatch
5. **Trajectory analysis** — `_trajectory_missing_steps()` tracks SOP step coverage
6. **Resolution heuristic** — positive/negative ending markers
7. **Resolve policy context** — 3-tier fallback: ground truth overrides → manual org files → Qdrant retrieval
8. **Build explainability** — assemble `EvidenceAnchoredExplainability` with `TriggerAttribution` (links triggers to evidence + verdict) and `ClaimProvenance` (traces retrieval source → document → chunk)
9. **Persist** to `interaction_llm_trigger_cache`

All prompts include `_INJECTION_GUARD` — treats every piece of user data as untrusted. **Never remove this.**

---

## RAG System — Dual Collections

| Collection | Granularity | Used for |
|---|---|---|
| `policy_parents` (`QDRANT_COLLECTION_PARENTS`) | H1/H2/H3 header splits of policy docs | Policy compliance evaluator, NLI policy check (LLM trigger) |
| `policy_children` (`collection_children`) | 400-char recursive, 80 overlap | Manager-assistant answer synthesis (Q&A only) |
| `sop_parents` (`QDRANT_COLLECTION_SOP_PARENTS`) | H1/H2/H3 header splits of SOP + KB docs | Process adherence (SOP) and KB claim-validation lookups |

> Policy documents are indexed at both parent and child granularity. SOP and KB documents are indexed at parent granularity only (no separate children collection).
>
> Selection rule: **parents = compliance / SOP / KB** (the consumer needs the whole rule, with all conditions and exceptions), **children = Q&A answer synthesis** (the consumer needs a precise span to quote). See `docs/rag/RAG_OVERVIEW.md` for the full matrix.

**Ingestion flow**: `storage/docs/{org}/` PDFs → Docling parse → ftfy clean → extract org/doc_type/category metadata → parent+child chunks → validate → Ollama embed (snowflake-arctic-embed2) → Qdrant upload with deterministic content-hash UUIDs (re-ingesting same doc = same points)

**Retrieval adapters** (`llm_trigger/retrieval.py`): `SOPRetriever`, `PolicyRetriever`, `KBRetriever` — all subclass `QdrantRetriever` which embeds via Ollama and queries with org+doc_type payload filters.

---

## Manager Assistant — Text-to-SQL

`assistant.py` `IntentResolver` chain: natural language → SQL → read-only execution → answer synthesis.

- Fallback: **Gemini → Groq → Ollama qwen2.5:7b** (controlled by `ASSISTANT_LLM_PROVIDER`)
- Supports ordinal follow-ups ("show me the second one"), SQL repair on parse failure
- All SQL execution is **read-only** (no INSERT/UPDATE/DELETE)
- Conversation history carried per session

---

## Frontend Architecture

**SPA**, React 18 + react-router v7. Two role-based route trees:

| Manager routes | Agent routes |
|---|---|
| `/manager` → Dashboard (KPIs, charts, leaderboard) | `/agent` → Dashboard (personal KPIs, trend) |
| `/manager/sessions` → SessionInspector (search/sort/paginate) | `/agent/calls` → personal call list |
| `/manager/sessions/:id` → SessionDetail (audio, transcript, triggers, explainability) | `/agent/calls/:id` → coaching view |
| `/manager/assistant` → AI chat | `/agent/settings` |
| `/manager/knowledge` → KnowledgeBase CRUD | |
| `/manager/settings` | |

**API client** (`api.ts`): single 864-line typed fetch wrapper. Token in `sessionStorage` + `localStorage` hint for reload; actual auth via HttpOnly cookie. 15s cache on `getInteractionDetail`.

**Styling**: MUI ThemeProvider + Tailwind v4 CSS. 48 shadcn/ui Radix wrapper components in `components/ui/`.

---

## Database Schema (v5.2)

17 DDL tables + 1 runtime table (interaction_llm_trigger_cache), 10 enum types, 14 indexes. Full DDL in `infra/db/01_schema.sql`.

**Core data chain**: `Organization` → `User` → `Interaction` → `ProcessingJob` (6 stages) → `Transcript` ↔ `Utterance` → `EmotionEvent` → `InteractionScore` + `InteractionLLMTriggerCache`

**Policy chain**: `CompanyPolicy` → `OrganizationPolicy` (org-scoped toggle) → `PolicyCompliance` (per-interaction)

**Feedback (RLHF)**: `EmotionFeedback`, `ComplianceFeedback` — agents dispute, managers review

**Key types**: `processing_status` (pending/processing/completed/failed), `job_stage` (diarization/stt/emotion/reasoning/scoring/rag_eval), `speaker_role` (agent/customer), `user_role` (manager/agent)

---

## Setup

```bash
cp .env.example .env && cp backend/.env.example backend/.env   # fill GROQ_API_KEY, HF_TOKEN
make up                    # Full Docker stack (db+backend+frontend+ollama+qdrant+vad+emotion+whisperx+ingestion)
# OR local dev:
make support-up            # db, ollama, qdrant, vad, emotion, whisperx
make be-install && make be-dev   # Backend :8000 (set IS_LOCAL=true in backend/.env)
make fe-install && make fe-dev   # Frontend :3000
make prepare-speaker-model       # One-time: extract DistilBERT for WhisperX speaker-role
make seed                        # Seed SQL demo data
```

---

## Testing & Linting

| Suite | Command | Framework | Details |
|---|---|---|---|
| Backend | `make be-test` | pytest + SQLite in-memory | 22 test files covering auth, fusion, pipeline, inference routes, dashboard, triggers, assistant, SOP retrieval |
| Backend lint | `make be-lint` | Ruff | |
| Frontend unit | `cd frontend && pnpm run test` | Vitest + jsdom | 11 test files (core components + utils) |
| Frontend lint | `make fe-lint` | `tsc --noEmit` | |
| Frontend E2E | `make fe-test` | Cypress | 12 specs; runs against `pnpm build` + preview, not dev server |
| RAG | `make rag-test` | pytest | config, ingest, query, evaluator |
| RAG lint | `make rag-lint` | Ruff | |
| Quality eval | `make quality-eval-all` | eval scripts | Compares outputs vs gold standards in `infra/benchmarks/expected/`; fails on regression |
| Full LLM trigger | `make llm-trigger-test` | pytest+vitest | Backend trigger tests + RAG ingest + frontend AgentCallDetail |

---

## CI/CD (GitHub Actions)

| Workflow | Paths | Runs |
|---|---|---|
| `ci.yml` | main | Gitleaks security audit |
| `backend.yml` | `backend/**` | ruff → pytest → quality benchmarks → pip-licenses |
| `frontend.yml` | `frontend/**` | tsc --noEmit → build → Cypress E2E |
| `rag_ci.yml` | `services/rag/**` | ruff → pytest |
| `quality-benchmarks.yml` | manual | eval_all.py → upload reports |

---

## Critical Gotchas

1. **`BACKEND_SPEAKER_RELABEL_ENABLED=false`** — WhisperX already labels speaker roles; enabling backend relabeling causes double-labeling. Do NOT enable both.
2. **`IS_LOCAL` routing** — single boolean routes all inference. `true` = Docker containers, `false` = Kaggle remote. Mismatch = all inference calls fail.
3. **Emotion fusion weights** — acoustic 0.55 / text 0.45 are tuned; changing them requires re-running `make quality-eval-emotion` against gold standards.
4. **`_INJECTION_GUARD`** — appended to every LLM prompt; treats user data as untrusted. Never remove.
5. **3-tier SOP fallback** — Qdrant down degrades to manual org files in `storage/docs/`, not a hard failure.
6. **Deterministic RAG UUIDs** — content-hash-based; re-ingesting = same Qdrant points (idempotent).
7. **SQLite ≠ PostgreSQL** — tests use SQLite in-memory; JSONB, specific indexes are Postgres-only.
8. **Dashboard cache** — 5-min TTL; stale data after seeding/reprocessing is expected.
9. **Audio normalization** — Emotion service caps at mono 16kHz / 30s; longer clips truncated.
10. **Groq rate limits** — 3-chain trigger evaluation uses exponential backoff; sustained rate-limiting = minutes per interaction.
11. **Cypress requires build** — E2E runs against `pnpm run build` + `vite preview`, never the dev server.
12. **Docker on Windows** — use `make build-retry` or `docker_compose_retry.ps1` for transient daemon errors.
13. **`uv.lock` gitignored** — run `uv sync` locally; lock file is not committed.
14. **Model artifacts gitignored** — `*.pt`, `*.safetensors`, `*.bin`, `speaker_classifier_export.zip`; run `make prepare-speaker-model` to extract DistilBERT.
15. **WhisperX alignment** — corrupted checkpoint auto-re-downloads; first attempt may fail.
16. **Assistant SQL is read-only** — no INSERT/UPDATE/DELETE allowed in generated SQL execution.

---

## Coding Conventions

**Python** (backend: 3.12, services: 3.11): Ruff linter, uv package manager, FastAPI async handlers, SQLModel ORM, Pydantic for all schemas, `Depends()` DI via `deps.py`, `Settings(BaseSettings)` from env vars, snake_case/PascalCase naming.

**TypeScript** (frontend): `tsc --noEmit` lint, pnpm, React 18 + Vite 6, Tailwind v4 + MUI, shadcn/ui Radix wrappers, react-router v7, React Context state, `@/` import alias, PascalCase components / camelCase functions.

**Docker**: multi-stage backend build, health checks on all services, named volumes (postgres, ollama, qdrant), bind mounts for dev hot-reload.

---

## Key Env Variables

| Variable | Purpose | Default |
|---|---|---|
| `IS_LOCAL` | Docker or Kaggle inference | `false` |
| `GROQ_API_KEY` | LLM chains (required) | — |
| `HF_TOKEN` | pyannote diarization (required for WhisperX) | — |
| `DATABASE_URL` | Postgres connection | `postgresql+asyncpg://vocalmind:vocalmind_dev@db:5432/vocalmind` |
| `ASSISTANT_LLM_PROVIDER` | gemini/ollama/auto | `ollama` (in Docker) |
| `BACKEND_SPEAKER_RELABEL_ENABLED` | Never enable with WhisperX running | `false` |
| `EMOTION/VAD/WHISPERX_API_URL` | Microservice endpoints | Docker service names |
| `OLLAMA_BASE_URL` | Embeddings | `http://ollama:11434` |
| `QDRANT_URL` | Vector DB | `http://qdrant:6333` |

Full templates: `.env.example` (root, 80 lines), `backend/.env.example` (49 lines). Local dev: change service URLs to `http://localhost:{port}`.

---

## Key Documentation

| Path | What it covers |
|---|---|
| `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md` | Claim→evidence→verdict architecture, API fields, UI cards |
| `docs/llm_trigger/LLM_TRIGGER_FEATURE_GUIDE.md` | 3-chain pipeline, retrieval priority, payload behavior, testing |
| `docs/rag/RAG_OVERVIEW.md` | Dual collections, provenance flow, runtime components |
| `docs/rag/INGESTION_PIPELINE.md` | 8-stage ingestion, Qdrant routing |
| `docs/design/vocalmind-design-spec.md` | Complete Figma spec (932 lines) |
| `infra/db/01_schema.sql` | v5.2 PostgreSQL DDL |

---

## Code Quality Rules

1. Ensure the code you write is concise and clear.
2. Ensure your changes are minimal and don't miss any component inside the codebase.
3. After finishing a task, verify the changes are correct and the task is completed successfully (e.g., run relevant tests, lint, or type checks).