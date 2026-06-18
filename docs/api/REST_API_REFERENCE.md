# VocalMind Backend API Reference

This document provides a detailed reference for all endpoints exposed by the VocalMind central API gateway. The API is built using FastAPI and conforms to REST conventions, using JSON payloads for data exchange and Bearer token headers or HttpOnly cookies for session management.

All API routes are prefixed by `/api/v1`.

---

## 1. Authentication (`/auth`)

Handles user login, callback processing, token generation, and logout.

### `POST /auth/login/access-token`
*   **Description**: Authenticates users using OAuth2 password flow (form parameters). Returns a JWT token and sets an HttpOnly session cookie `vocalmind_token` on the response.
*   **Content-Type**: `application/x-www-form-urlencoded`
*   **Request Body**:
    *   `username` (string, required): User's email address.
    *   `password` (string, required): User's password.
*   **Response**:
    ```json
    {
      "access_token": "mock_access_token_jwt_string",
      "token_type": "bearer"
    }
    ```

### `POST /auth/google`
*   **Description**: Authenticates users via Google OAuth ID Token. Sets the HttpOnly session cookie `vocalmind_token` on the response.
*   **Query Parameters**:
    *   `token` (string, required): The Google OAuth credential token.
*   **Response**: Same as `/auth/login/access-token`.

### `GET /auth/google/login`
*   **Description**: Generates and redirects to the Google OAuth authorization URL.

### `GET /auth/google/callback`
*   **Description**: Callback endpoint for Google OAuth authorization redirect.
*   **Query Parameters**:
    *   `code` (string, required): Authorization code from Google.
    *   `state` (string, required): State parameter to prevent CSRF.
*   **Response**: Sets `vocalmind_token` cookie and redirects to `${FRONTEND_URL}/login/success`.

### `POST /auth/logout`
*   **Description**: Logs out the current user, clearing authentication cookies.
*   **Response**: Returns `200 OK` with:
    ```json
    {
      "message": "Logged out successfully"
    }
    ```

---

## 2. Users (`/users`)

Provides user profile retrieval and configuration.

### `GET /users/me`
*   **Description**: Retrieves the profile details of the currently authenticated user. Sensitive field `password_hash` is excluded from the response payload.
*   **Headers**: `Authorization: Bearer <token>`
*   **Response**:
    ```json
    {
      "id": "b0000000-0000-0000-0000-000000000001",
      "email": "manager@nexalink.com",
      "name": "Galal Manager",
      "avatar_url": null,
      "role": "manager",
      "organization_id": "a0000000-0000-0000-0000-000000000001",
      "is_active": true,
      "last_login_at": "2026-04-17T15:00:00Z",
      "agent_type": null
    }
    ```

### `PATCH /users/me`
*   **Description**: Updates the current user's display name and/or avatar URL.
*   **Headers**: `Authorization: Bearer <token>`
*   **Request Body**:
    ```json
    {
      "name": "New Name",
      "avatar_url": "https://example.com/avatar.png"
    }
    ```
    Both fields are optional. Set `avatar_url` to `""` to clear the avatar.
*   **Response**: Full updated User object (same shape as `GET /users/me`).

### `POST /users/me/change-password`
*   **Description**: Changes the current user's password. Google-OAuth accounts that have no password set can skip `current_password`.
*   **Headers**: `Authorization: Bearer <token>`
*   **Request Body**:
    ```json
    {
      "current_password": "old-password",
      "new_password": "new-password-min-8-chars"
    }
    ```
    `current_password` is optional for accounts without an existing password.
*   **Response**: `{ "status": "ok" }`

---

## 3. Interactions (`/interactions`)

The core endpoints for uploading, listing, detailing, and reprocessing customer-agent calls.

### `POST /interactions`
*   **Description**: Uploads a raw audio recording file and creates a new pending interaction.
*   **Content-Type**: `multipart/form-data`
*   **Request Body**:
    *   `file` (binary, required): The audio recording file.
    *   `agent_id` (UUID, optional): Assign the interaction to a specific agent (snake_case).
*   **Response**:
    ```json
    {
      "interactionId": "d0000000-0000-0000-0000-000000000001",
      "status": "pending",
      "audioFilePath": "storage/audio/nexalink/call.wav",
      "agentId": "agent-uuid",
      "uploadedBy": "uploader-uuid",
      "processingJobs": [
        {
          "id": "job-uuid",
          "stage": "stt",
          "status": "pending"
        }
      ]
    }
    ```

### `POST /interactions/from-storage`
*   **Description**: Creates an interaction using an audio file path that already exists in Supabase/S3 Storage.
*   **Request Body (JSON)**:
    ```json
    {
      "storage_path": "recordings/nexalink/2026/04/call-001.wav",
      "agent_id": "optional-agent-uuid",
      "file_size_bytes": 4321000,
      "duration_seconds": 245,
      "interaction_date": "2026-04-17T15:00:00Z",
      "verify_exists": false
    }
    ```
*   **Response**: Same as `POST /interactions`.

### `GET /interactions`
*   **Description**: Returns a list of interactions belonging to the user's organization. This endpoint accepts **no query parameters** and returns the full organization list.
*   **Response keys (camelCase)**:
    ```json
    [
      {
        "id": "d0000000-0000-0000-0000-000000000001",
        "agentName": "Priya",
        "overallScore": 8.5,
        "hasViolation": false,
        "responseTime": 1.2,
        "processingFailures": [],
        "processingStatus": "completed"
      }
    ]
    ```

### `GET /interactions/{interaction_id}`
*   **Description**: Retrieves the complete details of a single interaction, including transcription metadata, utterances list, compliance checks, and explainability payloads.
*   **Query Parameters**:
    *   `include_llm_triggers` (boolean, default `false`): When true, includes the full 3-chain LLM trigger evaluation payload in the response.
    *   `llm_force_rerun` (boolean, default `false`): Forces a fresh trigger evaluation even if a cached result exists.
*   **Response**: Renders a comprehensive structure containing:
    *   `interaction`: Core interaction fields.
    *   `utterances`: Array of segment transcriptions.
    *   `emotionEvents`: Acoustic emotion shift markers.
    *   `policyViolations`: Array of compliance violations.
    *   `emotionComparison`: Comparison payload between acoustic and text emotion.
    *   `ragCompliance`: Compliance evaluations retrieved from vector store.
    *   `emotionTriggers`: Shift triggers.
    *   `llmTriggers`: Full 3-chain LLM trigger evaluation payload (present when `include_llm_triggers=true`).
    *   `processingFailures`: Logged errors.

### `GET /interactions/{interaction_id}/processing-status`
*   **Description**: Retrieves status of the 6 stages of processing jobs for this call.
*   **Response**: Wrapper object:
    ```json
    {
      "interactionId": "uuid",
      "status": "completed",
      "jobs": [
        {
          "stage": "stt",
          "status": "completed",
          "retryCount": 0,
          "errorMessage": null,
          "startedAt": "2026-06-18T12:00:00Z",
          "completedAt": "2026-06-18T12:01:00Z"
        }
      ]
    }
    ```

### `GET /interactions/{interaction_id}/emotion-comparison`
*   **Description**: Retrieves segment-level comparison data between acoustic emotion predictions and text-based emotion predictions.
*   **Response**: Distribution statistics and comparison segments.

### `GET /interactions/{interaction_id}/audio`
*   **Description**: Resolves and streams/downloads the raw audio file.

### `POST /interactions/{interaction_id}/reprocess`
*   **Description**: Triggers reprocessing of the call, optionally forcing a full re-evaluation.
*   **Query Parameters**:
    *   `force` (boolean, default false): Force overwrite.
*   **Response**:
    ```json
    {
      "interactionId": "d0000000-0000-0000-0000-000000000001",
      "status": "pending",
      "processingJobs": [...],
      "queued": true,
      "forced": false
    }
    ```

### `DELETE /interactions/{interaction_id}`
*   **Description**: Deletes an interaction and all its cascades (transcript, utterances, scores).
*   **Response**: `204 No Content`.

---

## 4. Emotion Events & Disputes

Agent-dispute endpoints are under `/interactions` (emotion) and `/policy-compliance` (compliance). Auth uses standard JWT/cookie — no `token` query parameter is needed.

### `POST /interactions/emotion-events/{event_id}/dispute`
*   **Description**: Agent disputes an AI-generated emotion verdict on one of their own calls.
*   **Request Body**:
    ```json
    { "agent_flag_note": "Acoustic was loud due to static, not sarcasm." }
    ```
*   **Response**: `{ "event_id", "is_flagged": true, "agent_flagged_at", "message" }`

### `DELETE /interactions/emotion-events/{event_id}/dispute`
*   **Description**: Agent (or manager) retracts a previously submitted emotion dispute.
*   **Response**: `{ "event_id", "message": "Dispute retracted." }`

### `POST /policy-compliance/{compliance_id}/dispute`
*   **Description**: Agent disputes a policy compliance verdict on one of their own calls. (Agent-only)
*   **Request Body**:
    ```json
    { "agent_flag_note": "This policy does not apply to this call type." }
    ```
*   **Response**: `{ "compliance_id", "is_flagged": true, "agent_flagged_at", "message" }`

### `DELETE /policy-compliance/{compliance_id}/dispute`
*   **Description**: Agent or manager retracts a compliance dispute.
*   **Response**: `{ "compliance_id", "message": "Dispute retracted." }`

---

## 5. Dashboard (`/dashboard`)

### `GET /dashboard/stats`
*   **Description**: Returns high-level KPIs and metrics for the organization dashboard, including empathy scores, compliance averages, resolution rates, and the agent leaderboard.
*   **Caching**: Employs a 5-minute TTL server-side cache.

---

## 6. AI Assistant (`/assistant`)

### `POST /assistant/query`
*   **Description**: Submits a natural language query to the AI Manager Assistant, executing a read-only query and returning synthesized insights.
*   **Request Body**:
    ```json
    {
      "query_text": "Show me Sara's average empathy score this week",
      "mode": "chat"
    }
    ```
*   **Response**:
    ```json
    {
      "id": "msg-1234",
      "type": "ai",
      "content": "Sara Agent's average empathy score is 84.5% across 6 calls.",
      "sql": "SELECT AVG(empathy_score) FROM interaction_scores WHERE ...",
      "execution_time": "180ms",
      "executionTime": "180ms",
      "data": [ { "avg": 0.845 } ],
      "success": true
    }
    ```

### `GET /assistant/history`
*   **Description**: Retrieves conversation history for the current session.
*   **Response**: Returns list of conversation messages.

---

## 7. Knowledge Base & Policies (`/knowledge`)

Manages the ingestion, modification, and toggling of documents and rules.

### `GET /knowledge/policies` | `GET /knowledge/faqs` | `GET /knowledge/kb`
*   **Description**: Lists policy records, FAQs, or KB references.

### `POST /knowledge/policies` | `POST /knowledge/faqs`
*   **Description**: Manual creation of a single text-based policy or FAQ entry. (No equivalent for KB — KB articles are created exclusively via file upload.)

### `POST /knowledge/policies/upload` | `POST /knowledge/faqs/upload` | `POST /knowledge/kb/upload`
*   **Description**: Uploads a PDF file (DOCX is not supported by these endpoints) to be processed by direct PDF reading and ingested into Qdrant vector databases.
*   **Content-Type**: `multipart/form-data`
*   **Form Parameters**:
    *   `file` (binary, required): The PDF document file.
    *   `title` (string, optional): Title.
    *   `category` (string, optional): Category.

### `PATCH /knowledge/policies/{policy_id}` | `PATCH /knowledge/faqs/{faq_id}`
*   **Description**: Updates title, category, or text details.

### `PATCH /knowledge/policies/{policy_id}/upload` | `PATCH /knowledge/faqs/{faq_id}/upload` | `PATCH /knowledge/kb/{kb_id}/upload`
*   **Description**: Re-uploads and replaces the binary source document for an existing policy, FAQ, or KB entry.

### `POST /knowledge/policies/{policy_id}/toggle` | `POST /knowledge/faqs/{faq_id}/toggle` | `POST /knowledge/kb/{kb_id}/toggle`
*   **Description**: Enables or disables a document's active status. Disabled documents are ignored during retrieval.

### `DELETE /knowledge/policies/{policy_id}` | `DELETE /knowledge/faqs/{faq_id}` | `DELETE /knowledge/kb/{kb_id}`
*   **Description**: Permanently deletes a document and removes its corresponding vectors from Qdrant.

---

## 8. RAG Retrieval (`/rag`)

### `POST /rag/query`
*   **Description**: Standalone entry point to execute search queries against Qdrant collections. The org filter is automatically derived from the authenticated user's organization.
*   **Request Body**:
    ```json
    {
      "query": "What is the policy on late fees?",
      "mode": "answer"
    }
    ```
*   **Response**: Returns synthesized response and a `retrieval_provenance` list.

### `GET /rag/health`
*   **Description**: Health status checking for the RAG query engine and Qdrant integration.

---

## 9. Microservices Proxy (`/diarization`, `/transcription`, `/vad`, `/full`)

These endpoints act as a gateway routing to the underlying ML pipeline services:
*   `POST /diarization/analyze`: Proxy to /split and WhisperX diarize.
*   `POST /diarization/analyze-local`: Local file execution proxy with payload `{ "file_path": "..." }`.
*   `POST /transcription/analyze`: Proxy to WhisperX transcription.
*   `POST /transcription/analyze-local`: Local file execution proxy with payload `{ "file_path": "..." }`.
*   `POST /vad/analyze`: Proxy to Silero VAD segment boundaries detector.
*   `POST /vad/analyze-local`: Local file execution proxy with payload `{ "file_path": "..." }`.
*   `POST /full/analyze`: Performs VAD split -> transcribe + diarize -> emotion detection in a single combined call.
*   `POST /full/analyze-local`: Local file execution proxy with payload `{ "file_path": "..." }`.

---

## 10. Agents (`/agents`)

Provides profile and performance overview endpoints.

### `GET /agents`
*   **Description**: Lists all active agent users belonging to the manager's organization.

### `GET /agents/{agent_id}`
*   **Description**: Retrieves detailed performance statistics, call count, and aggregate KPIs for a specific agent.

---

## 11. LLM Triggers (`/llm-trigger`)

Run evaluations directly or verify model settings.

### `GET /llm-trigger/health`
*   **Description**: Verification route for Groq connection status.

### `POST /llm-trigger/emotion-shift`
*   **Description**: Runs emotion shifts analysis on transcript.

### `POST /llm-trigger/process-adherence`
*   **Description**: Evaluates transcript against SOP resolution graphs.

### `POST /llm-trigger/nli-policy-check`
*   **Description**: Evaluates alignment of claims with SOP/policy.

### `POST /llm-trigger/interaction/{interaction_id}/run`
*   **Description**: Triggers evaluation of all three LLM chains for a specific interaction.

---

## 12. Internal Routing (`/internal`)

### `POST /internal/set-kaggle-url`
*   **Description**: Dynamically overrides backend configuration for Kaggle remote tunnels.

---

## 13. Notifications (`/notifications`)

In-app notification delivery via polling. Phase 1 is pull-based; Phase 2 will add Server-Sent Events.

### `GET /notifications`
*   **Description**: Returns notifications for the authenticated user, ordered by `created_at DESC`.
*   **Query Parameters**:
    *   `unread` (boolean, default `false`): If `true`, returns only unread notifications.
    *   `limit` (integer, default `50`, max `200`): Page size.
    *   `offset` (integer, default `0`): Pagination offset.
*   **Response**:
    ```json
    [
      {
        "id": "uuid",
        "type": "evaluation_complete",
        "title": "Call evaluation ready",
        "body": "Interaction CALL_15 has finished processing.",
        "link_url": "/manager/sessions/uuid",
        "payload": { "interaction_id": "uuid" },
        "is_read": false,
        "read_at": null,
        "created_at": "2026-06-18T15:00:00Z"
      }
    ]
    ```

### `GET /notifications/unread-count`
*   **Description**: Lightweight badge-count endpoint. Returns the number of unread notifications for the current user.
*   **Response**: `{ "unread": 5 }`

### `POST /notifications/{notification_id}/read`
*   **Description**: Marks a single notification as read.
*   **Response**: `{ "id": "uuid", "is_read": true }`

### `POST /notifications/read-all`
*   **Description**: Marks all unread notifications for the current user as read.
*   **Response**: `{ "updated": 5 }`

**Notification `type` values:**

| Value | Triggered when |
|---|---|
| `evaluation_complete` | A call finishes the full processing pipeline |
| `agent_flag_pending` | An agent submits an emotion or compliance dispute |
| `flag_approved` | A manager approves an agent's dispute |
| `flag_rejected` | A manager rejects an agent's dispute |
| `manager_correction` | A manager directly corrects a call verdict |
| `feedback_applied` | A feedback row is exported to the training dataset |

---

## 14. Manager Review Queue (`/reviews`)

Single endpoint group for manager decisions on agent-disputed AI evaluations (both emotion and compliance).

### `GET /reviews/queue`
*   **Description**: Returns all pending emotion and compliance flags for the manager's organization. **Manager-only.**
*   **Response**:
    ```json
    {
      "emotion": [
        {
          "kind": "emotion",
          "review_id": "uuid",
          "interaction_id": "uuid",
          "agent_id": "uuid",
          "agent_name": "Sara Agent",
          "agent_flagged_at": "2026-06-18T12:00:00Z",
          "agent_flag_note": "Static noise caused false anger label",
          "previous_emotion": "neutral",
          "new_emotion": "angry",
          "llm_justification": "...",
          "confidence_score": 0.72,
          "jump_to_seconds": 45.3
        }
      ],
      "compliance": [
        {
          "kind": "compliance",
          "review_id": "uuid",
          "interaction_id": "uuid",
          "agent_id": "uuid",
          "agent_name": "Sara Agent",
          "agent_flagged_at": "2026-06-18T12:00:00Z",
          "agent_flag_note": "Policy does not apply here",
          "policy_id": "uuid",
          "policy_title": "Late Fee Policy",
          "is_compliant": false,
          "compliance_score": 0.3,
          "llm_reasoning": "...",
          "evidence_text": "..."
        }
      ]
    }
    ```

### `POST /reviews/emotion/{event_id}`
*   **Description**: Manager accepts or rejects an agent's emotion dispute. **Manager-only.**
*   **Request Body**:
    ```json
    {
      "decision": "accept",
      "corrected_emotion": "neutral",
      "corrected_justification": "Background noise caused false detection.",
      "manager_note": "Reviewed audio at 45s — clearly not anger."
    }
    ```
    `corrected_emotion` is required when `decision == "accept"`. `decision` is `"accept"` or `"reject"`.
*   **Response**: `{ "review_id": "uuid", "decision": "accept", "feedback_id": "uuid" }`

### `POST /reviews/compliance/{compliance_id}`
*   **Description**: Manager accepts or rejects an agent's compliance dispute. **Manager-only.**
*   **Request Body**:
    ```json
    {
      "decision": "accept",
      "corrected_is_compliant": true,
      "corrected_score": 0.85,
      "manager_note": "Policy does not apply to this call type."
    }
    ```
    `corrected_is_compliant` is required when `decision == "accept"`.
*   **Response**: `{ "review_id": "uuid", "decision": "accept", "feedback_id": "uuid" }`

---

## 15. Manager Direct Feedback (`/feedback`)

Manager-initiated corrections that do not require a prior agent dispute flag. Creates a feedback row immediately at `reviewed` status for training export.

### `POST /feedback/emotion`
*   **Description**: Manager directly corrects an AI emotion verdict. **Manager-only.**
*   **Request Body**:
    ```json
    {
      "emotion_event_id": "uuid",
      "corrected_emotion": "neutral",
      "corrected_justification": "Speaker was calm throughout.",
      "correction_reason": "False positive from background noise."
    }
    ```
*   **Response** (201 Created): `{ "feedback_id": "uuid" }`

### `POST /feedback/compliance`
*   **Description**: Manager directly corrects a compliance verdict. **Manager-only.**
*   **Request Body**:
    ```json
    {
      "policy_compliance_id": "uuid",
      "corrected_is_compliant": true,
      "corrected_score": 0.9,
      "correction_reason": "Policy does not apply to this call scenario."
    }
    ```
*   **Response** (201 Created): `{ "feedback_id": "uuid" }`

---

## 16. Emotion Analysis (`/emotion`)

Proxy and fusion endpoints for the emotion microservice.

### `POST /emotion/analyze`
*   **Description**: Upload an audio file, get back dominant emotion prediction from the FunASR emotion2vec model.
*   **Content-Type**: `multipart/form-data`
*   **Request**: `file` (binary, required) — audio file.
*   **Response**: `{ "emotion": "happy", "confidence": 0.87, "all_scores": { ... } }`

### `POST /emotion/analyze-local`
*   **Description**: Analyze from a local file path on the server.
*   **Request Body**: `{ "file_path": "/path/to/audio.wav" }`

### `POST /emotion/fuse`
*   **Description**: Fuse text-based and acoustic emotion signals into a single fused result using the weighted fusion algorithm (acoustic×0.55 + text×0.45).
*   **Request Body**: Text + acoustic emotion labels and confidence scores.
*   **Response**: `{ "fused_emotion": "...", "fused_confidence": 0.82, "model": "..." }`

### `POST /emotion/process`
*   **Description**: Full VAD → emotion pipeline. Returns utterance-shaped list with per-segment emotion predictions.
*   **Content-Type**: `multipart/form-data`
*   **Request**: `file` (binary, required).

