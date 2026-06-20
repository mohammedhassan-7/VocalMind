# VocalMind — Repository Context

> AI agent & contributor onboarding. Read fully before working on the codebase.

---

## Code Quality Rules

1. Ensure the code you write is concise and clear.
2. Ensure your changes are minimal and don't miss any component inside the codebase.
3. After finishing a task, verify the changes are correct and the task is completed successfully (e.g., run relevant tests, lint, or type checks).

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
  Frontend (:3000) ──/api/v1──▶ Backend (:8000) ──▶ PostgreSQL (host :5434 → container :5432)
       │  Vite proxy              │
       │  (same-origin)           ├──────────┬──────────┬──────────┐
       │                          ▼          ▼          ▼          ▼
       │                     VAD (:8002) WhisperX Emotion (:8001) Ingestion
       │                     Silero   (:8003)  FunASR      Docling watch
       │                              ASR+Diarize emotion2vec   mode
       │                                   │
       └───────────────────────────────────┼──────────────────────┐
                                           ▼                      ▼
                                       Qdrant (:6333)         Ollama (:11434)
                                       vocalmind_* cols       snowflake-arctic-embed2
                                                                │
                                           LLM triggers ◀───────┴── Ollama Cloud API
                                           (kimi-k2.6 / ministral-3)   (default in compose)
                                           or Groq (LLM_PROVIDER=groq)
```

**Docker Compose services (9):** `db`, `backend`, `frontend`, `ollama`, `qdrant`, `ingestion`, `vad`, `emotion`, `whisperx`. GPU overlay: `docker-compose.gpu.yml` (`make up-gpu`).

**`IS_LOCAL` switch** — `true` = inference hits Docker containers; `false` = hits remote Kaggle server via `BaseKaggleClient`. Docker Compose sets `IS_LOCAL=true`; local dev with `make support-up` also uses `true`.

---

## Directory Structure

```
VocalMind/
├── docker-compose.yml         9-service stack (CPU defaults)
├── docker-compose.gpu.yml     GPU overlay for whisperx + emotion (+ optional ollama GPU)
├── Makefile                   up, up-gpu, support-up, ollama-pull-embed, be-*, fe-*, rag-*, seed, migrate
├── .env.example               Root secrets passed into compose (GROQ, HF, Ollama Cloud, etc.)
├── start-gpu.ps1              Windows helper to launch GPU stack
│
├── backend/                   FastAPI API gateway
│   ├── app/main.py            Lifespan: tables → Nexalink/Meridian seed → worker → audio watcher
│   ├── app/api/
│   │   ├── main.py            Router aggregator — 18+ domain routers
│   │   ├── deps.py            DI: get_db, get_current_user, get_supabase
│   │   └── routes/
│   │       ├── interactions.py  Upload/list/detail/reprocess/scores/emotion-comparison
│   │       ├── dashboard.py     8 concurrent DB queries + 5-min TTL cache
│   │       ├── assistant.py     Text-to-SQL (Gemini → Groq → Ollama fallback)
│   │       ├── knowledge.py       Policy/FAQ/KB CRUD + PDF upload
│   │       ├── rag.py           RAG proxy (health + query)
│   │       ├── auth/            Password + Google OAuth, HttpOnly cookie sessions
│   │       ├── emotion/         Analyze, fuse, dispute
│   │       ├── full/            Combined VAD → ASR → emotion pipeline
│   │       ├── llm_trigger/     emotion-shift, process-adherence, nli-policy-check
│   │       ├── agents.py, users.py, notifications.py, reviews.py, feedback.py
│   │       ├── compliance_disputes.py, internal.py, diarization.py, transcription.py, vad.py
│   ├── app/core/
│   │   ├── config.py            Settings(BaseSettings) — all env config + startup validation
│   │   ├── interaction_processing.py  Pipeline worker + priority reprocess queue (CORE)
│   │   ├── model.pkl, vectorizer.pkl  Retrained LR+TF-IDF speaker-role classifier
│   │   ├── audio_folder_watcher.py    Auto-ingest storage/audio/<org_slug>/
│   │   ├── audio_resolver.py          Local FS / Supabase Storage resolution
│   │   ├── inference_contracts.py     Normalize microservice responses
│   │   ├── emotion_fusion.py          Acoustic×0.55 + text×0.45 fusion
│   │   ├── kaggle_client.py           Remote inference when IS_LOCAL=false
│   │   ├── llm_circuit_breaker.py, notification_service.py, score_utils.py, …
│   ├── app/llm_trigger/
│   │   ├── service.py           Judging/reasoning engine (MOST COMPLEX)
│   │   ├── retrieval.py         Qdrant SOP/Policy/KB retrievers
│   │   ├── chains.py            Groq or Ollama Cloud LangChain chains
│   │   ├── prompts.py           Templates with _INJECTION_GUARD
│   │   └── schemas.py           Evidence/Attribution/Provenance models
│   ├── app/models/              SQLModel tables + enums
│   ├── alembic/versions/        Schema migrations (baseline + notifications/disputes/avatar)
│   ├── scripts/
│   │   ├── seed_nexalink.py     NexaLink org + 5 agents (Priya, Daniel, Marcus, Aisha, Hannah)
│   │   └── seed_meridian.py     Meridian org + 5 agents (Sarah, Tyler, Andre, Jasmine, Karen)
│   ├── pyproject.toml           Python 3.12, FastAPI, SQLModel, langchain-groq
│   ├── .env.example             ~150-line template (Ollama Cloud stage models, RAG, Supabase)
│   └── tests/                   35 pytest files (SQLite in-memory)
│
├── frontend/                  React dashboard
│   ├── src/app/
│   │   ├── App.tsx, routes.tsx  /login, /manager/*, /agent/*
│   │   ├── services/api.ts      Typed fetch wrapper; empty VITE_API_URL → same-origin /api/v1
│   │   ├── contexts/            AuthContext, ThemeContext
│   │   ├── components/manager/  ManagerDashboard, SessionInspector, SessionDetail,
│   │   │                        ManagerAssistant, KnowledgeBase, ReviewQueue,
│   │   │                        EmotionComparisonPanel, EvidenceAnchoredExplainabilityPanel, …
│   │   ├── components/agent/    AgentDashboard, AgentCalls, AgentCallDetail
│   │   ├── components/layouts/  ManagerLayout, AgentLayout, UserNav
│   │   └── components/ui/       shadcn/ui Radix wrappers
│   ├── vite.config.ts           Dev proxy /api → backend; allowedHosts for ngrok
│   ├── package.json             React 18, Vite 6, Tailwind 4, MUI 7, pnpm
│   └── cypress/e2e/             14 E2E spec files
│
├── services/
│   ├── vad/app.py               Silero VAD (host :8002)
│   ├── emotion/app.py           FunASR emotion2vec (host :8001 → container :8000)
│   ├── whisperx/
│   │   ├── app.py                 POST /transcribe: transcribe → align → diarize → speaker-role
│   │   ├── speaker_role_classifier.py  Text cues + DistilBERT (models/speaker_role/distilbert/)
│   │   └── models/speaker_role/   Extracted from speaker_classifier_export.zip (gitignored)
│   └── rag/                     Ingestion container (vocalmind-ingestion)
│       ├── main.py              CLI: --ingest, --watch, -q, --compliance
│       ├── ingest.py            Docling → parent/child chunks → Ollama embed → Qdrant
│       ├── query_engine.py      Dual-collection RAG retrieval
│       ├── evaluator.py         Policy compliance + answer correctness judges
│       └── config.py            QDRANT + OLLAMA settings (mounted read-only in compose)
│
├── storage/                   Bind-mounted into backend + ingestion (large files gitignored)
│   ├── audio/nexalink/        CALL_<NN>_<agent>_<scenario>.wav — auto-ingested
│   ├── audio/meridian/        Meridian batch recordings + evaluation/manifest.json
│   ├── docs/nexalink/         Policy/SOP/KB PDFs for RAG
│   ├── docs/meridian/
│   └── uploads/               Manual upload staging
│
├── infra/
│   ├── db/                    01_schema.sql + migrations 04–06; 02_seed.sql (legacy NileTech/CairoConnect)
│   ├── scripts/               migrate.py, e2e_local_audio.py, ingest_audio_folder.py,
│   │                          prepare_speaker_role_model.py, benchmark/eval harness (many)
│   ├── benchmarks/            thresholds.json, expected/, overnight reports/
│   └── fixtures/audio/        Test fixtures (gitignored)
│
├── research/                  Notebooks + training/ (speaker LR export, batch_ids.csv)
├── tools/                     reprocess_and_compare.py, evaluate_pipeline.py, …
├── docs/                      explainability, LLM trigger, RAG, design spec, eval findings
└── .github/workflows/         ci.yml, backend.yml, frontend.yml, rag_ci.yml, quality-benchmarks.yml
```

### Demo orgs & UI login

Backend startup seeds **NexaLink** and **Meridian** when `SEED_DEMO_DATA=true` (compose default). Password for all seeded accounts: **`password123`**.

| Org | Manager login | Agents (sample) |
|-----|---------------|-----------------|
| NexaLink | `manager@nexalink.com` | `agent.aisha@nexalink.com`, `agent.priya@nexalink.com`, … |
| Meridian | `manager@meridian.com` | `agent.jasmine@meridian.com`, `agent.andre@meridian.com`, … |

Legacy SQL init (`infra/db/02_seed.sql`) also creates **NileTech** / **CairoConnect** users (`manager@niletech.com`, etc.) — separate from the NexaLink/Meridian eval batch.

**UI:** http://localhost:3000 · **API docs:** http://localhost:8000/docs

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
   │    → VAD splits → WhisperX transcribe+diarize   │
   │    → WhisperX DistilBERT + text cues (1st pass) │
   │    → Emotion per segment → build_local_full_resp │
   │ 4. inference_contracts.py normalizes response     │
   │ 5. Speaker roles (backend interaction_processing):│
   │    - Multi-cluster: LR+TF-IDF (model.pkl) on     │
   │      cluster text + rebalanced text-cue priors   │
   │    - Single-cluster diarization collapse: per-   │
   │      segment classify_segment_speaker_role()     │
   │ 6. Persist: Transcript → Utterances → EmotionEvents│
   │ 7. emotion_fusion.py fuses per-utterance:         │
   │    acoustic×0.55 + text×0.45                     │
   │    +0.08 agreement, −0.12 disagreement penalty    │
   │ 8. evaluate_interaction_triggers() [with timeout] │
   │ 9. Resolve policies → compute scores             │
   │ 10. Mark ProcessingJobs completed                │
   └──────────────────────────────────────────────────┘
                  │
                  ▼
   GET /api/v1/interactions/{id}  →  Dashboard
        (includes top-level `scores` wrapper + legacy overallScore fields)
   POST /api/v1/interactions/{id}/reprocess?priority=true  →  priority queue
   GET /.../{id}/emotion-comparison
```

### LLM Trigger Evaluation (step 7 above, `llm_trigger/service.py`)

The ~2000-line reasoning engine. For each interaction:

1. **Detect topic** — keyword classification (refund/billing/tech/account_access)
2. **Chunk transcript** — rolling 8-turn windows, stride 4
3. **Run 3 LangChain chains** (provider from `LLM_PROVIDER` — **`ollama_cloud` default in compose**, or `groq`):
   - Heavy stages → `OLLAMA_CLOUD_HEAVY_MODEL` (default `kimi-k2.6:cloud`)
   - Fast stages → `OLLAMA_CLOUD_FAST_MODEL` (default `ministral-3:8b`)
   - Per-stage overrides: `OLLAMA_EMOTION_SHIFT_MODEL`, `OLLAMA_PROCESS_ADHERENCE_MODEL`, `OLLAMA_NLI_MODEL`, …
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

| Collection | Env var | Granularity | Used for |
|---|---|---|---|
| `vocalmind_parents` | `QDRANT_COLLECTION_PARENTS` | H1/H2/H3 header splits of policy docs | NLI policy check, policy compliance |
| `vocalmind_children` | `QDRANT_COLLECTION_CHILDREN` | 400-char recursive, 80 overlap | Manager-assistant answer synthesis (Q&A) |
| `vocalmind_sop_parents` | `QDRANT_COLLECTION_SOP_PARENTS` | H1/H2/H3 splits of SOP + KB docs | Process adherence, KB claim validation |

> Policy documents are indexed at both parent and child granularity. SOP and KB documents are indexed at parent granularity only (no separate children collection).
>
> Selection rule: **parents = compliance / SOP / KB** (the consumer needs the whole rule, with all conditions and exceptions), **children = Q&A answer synthesis** (the consumer needs a precise span to quote). See `docs/rag/RAG_OVERVIEW.md` for the full matrix.

**Ingestion flow**: `storage/docs/{org}/` PDFs → Docling parse → ftfy clean → parent+child chunks → **compose Ollama** embed (`snowflake-arctic-embed2`, 1024-dim) → Qdrant upload with deterministic content-hash UUIDs. **`vocalmind-ingestion`** runs `main.py --watch` and depends on `ollama` + `qdrant` being healthy.

**Embeddings:** local Ollama in compose (`OLLAMA_BASE_URL=http://ollama:11434`). Set `OLLAMA_CLOUD_EMBED_ENABLED=true` to use Ollama Cloud embeddings instead. Pull model once: `make ollama-pull-embed`.

**Retrieval adapters** (`llm_trigger/retrieval.py`): `SOPRetriever`, `PolicyRetriever`, `KBRetriever` — all subclass `QdrantRetriever` which embeds via Ollama and queries with org+doc_type payload filters.

---

## Manager Assistant — Text-to-SQL

`assistant.py` `IntentResolver` chain: natural language → SQL → read-only execution → answer synthesis.

- Fallback: **Gemini → Groq → Ollama qwen2.5:7b** (controlled by `ASSISTANT_LLM_PROVIDER`; compose default **`ollama_cloud`**)
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

**API client** (`api.ts`): typed fetch wrapper. In Docker compose, `VITE_API_URL=""` → same-origin `/api/v1` via **Vite dev proxy** (`VITE_DEV_PROXY_TARGET=http://backend:8000`). This also works with **ngrok** on port 3000 (tunnel the frontend, not the backend). Token in `sessionStorage` + HttpOnly cookie. Detail responses include a top-level `scores` object.

**Styling**: MUI ThemeProvider + Tailwind v4 CSS. shadcn/ui Radix wrappers in `components/ui/`.

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
cp .env.example .env && cp backend/.env.example backend/.env   # fill OLLAMA_API_KEY, HF_TOKEN, SECRET_KEY
make build                  # Build all Docker images (use make build-retry on Windows)
make up                     # Full stack: db+backend+frontend+ollama+qdrant+ingestion+vad+emotion+whisperx
make ollama-pull-embed      # Pull snowflake-arctic-embed2 into compose Ollama
make prepare-speaker-model  # Extract DistilBERT for WhisperX (needs speaker_classifier_export.zip at repo root)
# Backend auto-seeds Nexalink + Meridian on first startup (SEED_DEMO_DATA=true)
# OR Supabase remote seed:
make seed                   # Requires SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in backend/.env
# GPU (Windows/Linux with NVIDIA Container Toolkit):
make up-gpu                 # docker-compose.yml + docker-compose.gpu.yml
# Local dev (backend/frontend on host):
make support-up             # db, ollama, qdrant, vad, emotion, whisperx only
make ollama-pull-embed
make be-install && make be-dev   # Backend :8000 (IS_LOCAL=true in backend/.env)
make fe-install && make fe-dev   # Frontend :3000
make migrate                # Alembic migrations via infra/scripts/migrate.py
```

---

## Testing & Linting

| Suite | Command | Framework | Details |
|---|---|---|---|
| Backend | `make be-test` | pytest + SQLite in-memory | 35 test files |
| Backend lint | `make be-lint` | Ruff | |
| Frontend unit | `cd frontend && pnpm run test` | Vitest + jsdom | 11 test files (core components + utils) |
| Frontend lint | `make fe-lint` | `tsc --noEmit` | |
| Frontend E2E | `make fe-test` | Cypress | 14 specs; runs against `pnpm build` + preview, not dev server |
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

1. **`BACKEND_SPEAKER_RELABEL_ENABLED=false`** — WhisperX already labels speaker roles; enabling backend relabeling causes double-labeling. Backend uses LR+TF-IDF (`model.pkl`) for cluster assignment and single-cluster per-segment fallback — separate from WhisperX DistilBERT.
2. **`IS_LOCAL` routing** — single boolean routes all inference. `true` = Docker containers, `false` = Kaggle remote. Mismatch = all inference calls fail.
3. **Single-cluster diarization** — PyAnnote sometimes returns one speaker cluster; backend falls back to per-segment LR labeling. Reprocess with `?priority=true` after model/heuristic changes.
4. **Emotion fusion weights** — acoustic 0.55 / text 0.45 are tuned; changing them requires re-running `make quality-eval-emotion` against gold standards.
5. **`_INJECTION_GUARD`** — appended to every LLM prompt; treats user data as untrusted. Never remove.
6. **3-tier SOP fallback** — Qdrant down degrades to manual org files in `storage/docs/`, not a hard failure.
7. **Deterministic RAG UUIDs** — content-hash-based; re-ingesting = same Qdrant points (idempotent).
8. **SQLite ≠ PostgreSQL** — tests use SQLite in-memory; JSONB, specific indexes are Postgres-only.
9. **Dashboard cache** — 5-min TTL; stale data after seeding/reprocessing is expected.
10. **Audio normalization** — Emotion service caps at mono 16kHz / 30s; longer clips truncated.
11. **LLM rate limits** — 3-chain trigger evaluation uses backoff; sustained rate-limiting = minutes per interaction (Groq or Ollama Cloud).
12. **Cypress requires build** — E2E runs against `pnpm run build` + `vite preview`, never the dev server.
13. **Docker on Windows** — use `make build-retry` or `docker_compose_retry.ps1` for transient daemon errors.
14. **`uv.lock` gitignored** — run `uv sync` locally; lock file is not committed.
15. **Model artifacts gitignored** — `*.pt`, `*.safetensors`, `speaker_classifier_export.zip`; run `make prepare-speaker-model`. LR speaker model (`model.pkl`, `vectorizer.pkl`) lives in `backend/app/core/` after retraining.
16. **WhisperX alignment** — corrupted checkpoint auto-re-downloads; first attempt may fail.
17. **Assistant SQL is read-only** — no INSERT/UPDATE/DELETE allowed in generated SQL execution.
18. **ngrok / public demos** — tunnel **port 3000** (frontend), not 8000. Compose uses Vite proxy so API calls stay same-origin. Avoid running host Ollama and compose Ollama both on `:11434`.
19. **Postgres host port** — Docker maps **`5434:5432`**; use `localhost:5434` from the host, `db:5432` inside containers.
20. **Ollama in compose** — `vocalmind-ollama` must be healthy before backend/ingestion start; run `make ollama-pull-embed` on fresh installs.

---

## Coding Conventions

**Python** (backend: 3.12, services: 3.11): Ruff linter, uv package manager, FastAPI async handlers, SQLModel ORM, Pydantic for all schemas, `Depends()` DI via `deps.py`, `Settings(BaseSettings)` from env vars, snake_case/PascalCase naming.

**TypeScript** (frontend): `tsc --noEmit` lint, pnpm, React 18 + Vite 6, Tailwind v4 + MUI, shadcn/ui Radix wrappers, react-router v7, React Context state, `@/` import alias, PascalCase components / camelCase functions.

**Docker**: multi-stage backend build, health checks on all services, named volumes (postgres, ollama, qdrant), bind mounts for dev hot-reload.

---

## Key Env Variables

| Variable | Purpose | Default (compose) |
|---|---|---|
| `IS_LOCAL` | Docker or Kaggle inference | `true` |
| `LLM_PROVIDER` | Trigger chains: `groq` or `ollama_cloud` | `ollama_cloud` |
| `OLLAMA_API_KEY` / `OLLAMA_CLOUD_API_KEY` | Ollama Cloud LLM (+ optional cloud embed) | — |
| `GROQ_API_KEY` | LLM chains when `LLM_PROVIDER=groq` | — |
| `HF_TOKEN` | pyannote diarization (required for WhisperX) | — |
| `SECRET_KEY` | JWT signing | dev placeholder in compose |
| `DATABASE_URL` | Postgres (in container) | `postgresql+asyncpg://vocalmind:vocalmind_dev@db:5432/vocalmind` |
| `ASSISTANT_LLM_PROVIDER` | gemini / groq / ollama_cloud / ollama / auto | `ollama_cloud` |
| `BACKEND_SPEAKER_RELABEL_ENABLED` | Never enable with WhisperX running | `false` |
| `SEED_DEMO_DATA` | Auto-seed Nexalink + Meridian on backend startup | `true` |
| `EMOTION/VAD/WHISPERX_API_URL` | Microservice endpoints | Docker service names |
| `OLLAMA_BASE_URL` | Local embeddings | `http://ollama:11434` (compose); `http://localhost:11434` (host dev) |
| `EMBEDDING_MODEL` | RAG embedding model | `snowflake-arctic-embed2` |
| `QDRANT_URL` | Vector DB | `http://qdrant:6333` |
| `QDRANT_COLLECTION_PARENTS` | Policy parent chunks | `vocalmind_parents` |
| `QDRANT_COLLECTION_CHILDREN` | Policy child chunks | `vocalmind_children` |
| `QDRANT_COLLECTION_SOP_PARENTS` | SOP + KB parent chunks | `vocalmind_sop_parents` |
| `EXTRA_AUDIO_ROOTS` | Extra allow-listed audio search roots (`;`-separated) | `/app/storage/audio_import` |
| `AUDIO_FOLDER_WATCHER_ENABLED` | Auto-ingest from `storage/audio/<org>/` | `true` |
| `VITE_API_URL` | Frontend API base; empty = same-origin proxy | `""` in compose |
| `VITE_DEV_PROXY_TARGET` | Vite proxy target for `/api` | `http://backend:8000` |

Full templates: `.env.example` (root), `backend/.env.example` (~150 lines). Local native dev: service URLs → `http://localhost:{port}`; Postgres host port **5434**.

### Running natively with GPU (CUDA) instead of Docker

For local CUDA inference, keep only **postgres + qdrant + ollama + frontend** in Docker (the infra layer) and run the GPU-needy services + backend on the host with a conda env that has `torch + cu*`, `whisperx`, `pyannote`, `funasr`, `silero_vad`, and the backend deps. See `docs/eval/PIPELINE_FINDINGS.md` (`Reproducing` section) for the exact start commands. Throughput improves ~15× (e.g. CALL_15 takes ~2 min on a 4060 vs 30+ min in the Docker CPU image).

---

## Key Documentation

| Path | What it covers |
|---|---|
| `docs/explainability/EVIDENCE_ANCHORED_EXPLAINABILITY_LAYER.md` | Claim→evidence→verdict architecture, API fields, UI cards |
| `docs/llm_trigger/LLM_TRIGGER_FEATURE_GUIDE.md` | 3-chain pipeline, retrieval priority, payload behavior, testing |
| `docs/rag/RAG_OVERVIEW.md` | Dual collections, provenance flow, runtime components |
| `docs/rag/INGESTION_PIPELINE.md` | 8-stage ingestion, Qdrant routing |
| `docs/design/vocalmind-design-spec.md` | Complete Figma spec (932 lines) |
| `docs/eval/PIPELINE_FINDINGS.md` | Pipeline-vs-GT evaluation, per-axis baseline → final scores, what was fixed and what remains |
| `tools/README.md` | Reproducible evaluation harness (`reprocess_and_compare.py`, `evaluate_pipeline.py`, `compare_summary.py`) |
| `infra/db/01_schema.sql` | v5.2 PostgreSQL DDL |

---
