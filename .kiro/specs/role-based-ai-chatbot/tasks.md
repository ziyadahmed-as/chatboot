# Implementation Plan: Role-Based AI Chatbot

## Overview

Implement a standalone Python/FastAPI microservice that provides role-based AI chat responses, multi-turn session management, optional RAG support, bearer token auth, and structured logging. All endpoints are versioned under `/v1`.

## Tasks

- [x] 1. Set up project structure, dependencies, and core data models
  - Create the FastAPI project layout: `app/main.py`, `app/schemas.py`, `app/models.py`, `app/routers/`, `app/services/`, `app/middleware/`
  - Define `Role` enum and Pydantic schemas: `ChatRequest`, `ChatResponse`, `IngestRequest`, `IngestResponse` in `app/schemas.py`
  - Define `Message` and `Session` dataclasses in `app/models.py`
  - Create `requirements.txt` with: `fastapi`, `uvicorn`, `openai`, `pydantic`, `chromadb`, `faiss-cpu`, `python-dotenv`
  - _Requirements: 1.1, 1.5, 8.1, 8.3, 8.4_

- [x] 2. Implement bearer token auth middleware
  - [x] 2.1 Create `app/middleware/auth.py` that reads `AI_SERVICE_SECRET` from env and validates `Authorization: Bearer <token>` on `/v1/chat` and `/v1/ingest` requests
    - Return HTTP 401 if header is missing or token does not match
    - _Requirements: 6.1, 6.2, 6.3_
  - [x] 2.2 Write unit tests for auth middleware
    - Test missing header → 401
    - Test invalid token → 401
    - Test valid token → passes through
    - _Requirements: 6.1, 6.2_

- [x] 3. Implement role-specific system prompts
  - [x] 3.1 Create `app/services/prompt_builder.py` with a dict mapping each `Role` enum value to its system prompt string
    - Student: course discovery, learning progress, study guidance
    - Instructor: course creation, student engagement, content recommendations
    - Buyer: course recommendations and purchase guidance
    - Seller: listing optimization and sales performance
    - Freelancer: proposal writing, skill positioning, job matching
    - Client: job posting, freelancer evaluation, project scoping
    - Admin: platform oversight, moderation, analytics across both marketplaces
    - Raise `ValueError` for unknown roles
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_
  - [x] 3.2 Write unit tests for prompt builder
    - Assert each role returns a non-empty string prompt
    - Assert unknown role raises `ValueError`
    - _Requirements: 2.1_

- [x] 4. Implement in-memory session store
  - [x] 4.1 Create `app/services/session_store.py` with `SessionStore` class
    - `get(session_id)` → returns `Session` or `None`
    - `create()` → generates UUID, returns new `Session`
    - `save(session)` → persists to in-memory dict with updated `last_active`
    - `expire_stale()` → evicts sessions inactive for ≥ 60 minutes
    - Limit history to the most recent 20 message turns when building context
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - [x] 4.2 Write property test for session store TTL expiry
    - **Property: Any session last active more than 60 minutes ago is evicted after `expire_stale()` is called**
    - **Validates: Requirements 3.5**
  - [x] 4.3 Write unit tests for session store
    - New session_id → session created and returned
    - Existing session_id → history appended
    - History capped at 20 turns
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 5. Implement LLM client
  - [x] 5.1 Create `app/services/llm_client.py` wrapping `AsyncOpenAI`
    - Read `OPENAI_API_KEY` and `OPENAI_MODEL` (default `gpt-4o`) from env
    - Enforce 30-second timeout
    - Map OpenAI API errors → HTTP 502
    - Map timeout errors → HTTP 504
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [x] 5.2 Write unit tests for LLM client error handling
    - Mock OpenAI error → assert 502 raised
    - Mock timeout → assert 504 raised
    - _Requirements: 4.3, 4.4_

- [x] 6. Implement vector store adapter and RAG engine
  - [x] 6.1 Create `app/services/vector_store.py` with abstract `VectorStoreAdapter` and ChromaDB + FAISS implementations
    - `add(texts, domain)` → embed and store documents
    - `query(query_text, top_k, threshold)` → return docs with similarity ≥ threshold
    - Select backend via `RAG_BACKEND` env var (default `chromadb`)
    - _Requirements: 5.5, 5.6_
  - [x] 6.2 Create `app/services/rag_engine.py` with `retrieve(query, domain, top_k=5)` async function
    - Query vector store with threshold 0.7
    - Return empty list if no documents meet threshold
    - _Requirements: 5.1, 5.4_
  - [x] 6.3 Write property test for RAG round-trip integrity
    - **Property: For all ingested documents, retrieving with the original text as query returns content matching the ingested content**
    - **Validates: Requirements 5.7**
  - [x] 6.4 Write unit tests for RAG engine
    - No results above threshold → empty list returned
    - Results above threshold → returned and prepended to context
    - _Requirements: 5.1, 5.4_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement ingest router
  - [x] 8.1 Create `app/routers/ingest.py` handling `POST /v1/ingest`
    - Accept `IngestRequest` (list of documents + optional domain)
    - Call embedder → vector store for each document
    - Return `IngestResponse` with count of ingested documents
    - _Requirements: 5.5, 5.6, 8.1, 8.4_
  - [x] 8.2 Write unit tests for ingest endpoint
    - Valid payload → 200 with correct ingested count
    - Missing auth → 401
    - _Requirements: 5.5, 6.1_

- [x] 9. Implement chat router
  - [x] 9.1 Create `app/routers/chat.py` handling `POST /v1/chat`
    - Validate role via Pydantic (invalid role → 422)
    - Load or create session via `SessionStore`
    - If `use_rag=true`, call `RAGEngine.retrieve` and prepend results to context
    - Build messages list: system prompt + trimmed history + new user message
    - Call `LLMClient.complete`
    - Save assistant reply to session
    - Return `ChatResponse` with `reply`, `session_id`, `role`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 5.1, 5.2, 5.3_
  - [x] 9.2 Write unit tests for chat router
    - Valid request → 200 with reply, session_id, role
    - Invalid role → 422
    - Missing auth → 401
    - New session_id generated when absent
    - Existing session_id reuses history
    - _Requirements: 1.2, 1.3, 1.5, 3.2, 3.3_

- [x] 10. Implement health router and structured logging middleware
  - [x] 10.1 Create `app/routers/health.py` handling `GET /v1/health`
    - Return `{"status": "ok"}` with HTTP 200
    - _Requirements: 7.1_
  - [x] 10.2 Create `app/middleware/logging.py` that emits a structured JSON log after each response
    - Include `timestamp`, `role`, `session_id`, `latency_ms`, `status_code`
    - Log unhandled exceptions at ERROR level without exposing stack traces to caller
    - Return HTTP 500 with generic message on unhandled exceptions
    - _Requirements: 7.2, 7.3_
  - [x] 10.3 Write unit tests for health endpoint and logging middleware
    - `GET /v1/health` → 200 `{"status": "ok"}`
    - Unhandled exception → 500 with generic message, no stack trace in body
    - _Requirements: 7.1, 7.3_

- [x] 11. Wire everything together in `app/main.py`
  - Register auth middleware, logging middleware, and global exception handler
  - Mount `chat`, `ingest`, and `health` routers under `/v1`
  - Configure OpenAPI docs at `/docs` (FastAPI default)
  - Load env vars via `python-dotenv` on startup
  - _Requirements: 8.2, 8.4, 7.3_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- All endpoints are versioned under `/v1` per requirement 8.4
- `AI_SERVICE_SECRET` and `OPENAI_API_KEY` must never be hardcoded
- Session store is in-memory; swap `SessionStore` implementation for Redis in future
- RAG is disabled by default (`use_rag: false`) to keep the hot path fast
