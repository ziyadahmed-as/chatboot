# Implementation Plan: AI Architecture Modules

## Overview

Extend `arifgate_ai` with an AI Gateway, Core AI Service enhancements, Vector DB adapter, six role-based modules, structured output parsers, and full observability. Tasks are ordered: foundations → gateway → core extensions → modules → integration → tests.

## Tasks

- [ ] 1. Extend schemas and data models
  - Add `Module` enum, `RetrievedDoc`, `InternalChatRequest`, `CourseDescription`, `JobDescription`, `FreelancerProposal`, `MatchResult`, `DocumentMetadata`, `GatewayLogEntry`, `CoreLogEntry` to `arifgate_ai/app/schemas.py`
  - _Requirements: 2.2, 3.6, 5.4, 8.6, 9.5, 11.1, 11.3, 12.3, 12.4_

- [ ] 2. Implement Vector Database adapter
  - [ ] 2.1 Create `arifgate_ai/app/services/vector_db.py` with abstract `VectorDBAdapter`, `ChromaDBAdapter`, `PineconeAdapter`, and `get_vector_db()` factory
    - `VectorDBAdapter` defines `ingest(documents, domain) -> int` and `search(query, top_k, threshold) -> list[RetrievedDoc]`
    - Factory reads `VECTOR_DB_BACKEND` env var; raises `ValueError` on unsupported value
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 2.2 Write property test for RAG threshold filter (Property 6)
    - **Property 6: RAG results always meet the similarity threshold**
    - **Validates: Requirements 3.3, 10.2, 10.4**
    - Use `st.lists(st.builds(RetrievedDoc, similarity=st.floats(0.0, 1.0)))` and assert all returned docs have `similarity >= threshold`

  - [ ]* 2.3 Write property test for ingest round-trip integrity (Property 7)
    - **Property 7: Ingest round-trip integrity**
    - **Validates: Requirements 3.5**
    - Use `st.text(min_size=1)` for document content; ingest then search with same text; assert content matches

  - [ ]* 2.4 Write unit tests for Vector DB factory
    - Test `VECTOR_DB_BACKEND=chromadb` returns `ChromaDBAdapter`
    - Test `VECTOR_DB_BACKEND=pinecone` returns `PineconeAdapter`
    - Test unsupported backend raises `ValueError` at startup
    - _Requirements: 3.1_

- [ ] 3. Implement Inference Router
  - Create `arifgate_ai/app/services/inference_router.py` with `InferenceRouter` class
  - `call(messages, api_key)` checks `GPU_SERVER_URL`; routes to GPU or OpenAI with 30s timeout
  - Raises mapped exceptions for 502 (API error) and 504 (timeout)
  - _Requirements: 2.5, 2.6, 2.7, 2.8, 4.1, 4.2, 4.3, 4.4_

- [ ] 4. Implement Module Router and Role Modules
  - [ ] 4.1 Create `arifgate_ai/app/modules/base.py` with abstract `RoleModule` (system_prompt, `build_messages`, `parse_output`)
    - _Requirements: 2.2_

  - [ ] 4.2 Implement `InstructorModule` in `arifgate_ai/app/modules/instructor.py`
    - System prompt focused on course creation and student engagement
    - `parse_output` returns `CourseDescription`; validates course topic >= 5 chars (raises 422 otherwise)
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]* 4.3 Write property test for CourseDescription output fields (Property 15)
    - **Property 15: CourseDescription output contains all required fields**
    - **Validates: Requirements 5.2, 5.4**
    - Use `st.text(min_size=5)` for topic; assert `title`, `summary`, `target_audience`, `learning_outcomes` are non-empty

  - [ ] 4.4 Implement `StudentModule` in `arifgate_ai/app/modules/student.py`
    - System prompt focused on course discovery and study guidance
    - Supports multi-turn history via session; uses RAG for course recommendations
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 4.5 Write property test for session history order (Property 10)
    - **Property 10: Session history preserves message order and completeness**
    - **Validates: Requirements 6.4**
    - Use `st.lists(st.builds(Message), min_size=1)`; append N messages; assert history matches in order

  - [ ] 4.6 Implement `CourseSharedModule` in `arifgate_ai/app/modules/course_shared.py`
    - Platform-wide help chatbot for all Course Marketplace roles; uses RAG for recommendations
    - Accepts optional `context` field for personalization
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ] 4.7 Implement `ClientModule` in `arifgate_ai/app/modules/client.py`
    - System prompt focused on job posting and freelancer evaluation
    - `parse_output` returns `JobDescription`; extracts keyword tags; uses RAG for candidate recommendations
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 4.8 Write property test for JobDescription output fields (Property 16)
    - **Property 16: JobDescription output contains all required fields**
    - **Validates: Requirements 8.2, 8.6**
    - Use `st.text(min_size=10)` for project description; assert `title`, `description`, `required_skills`, `budget_range`, `keywords` are non-empty

  - [ ] 4.9 Implement `FreelancerModule` in `arifgate_ai/app/modules/freelancer.py`
    - System prompt focused on proposal writing and skill positioning
    - `parse_output` returns `FreelancerProposal`; extracts skill tags; uses RAG for job recommendations
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 4.10 Write property test for FreelancerProposal output fields (Property 17)
    - **Property 17: FreelancerProposal output contains all required sections**
    - **Validates: Requirements 9.2, 9.5**
    - Use `st.text(min_size=10)` for job description + skills; assert `introduction`, `relevant_experience`, `proposed_approach`, `call_to_action` are non-empty

  - [ ]* 4.11 Write property test for skill tag monotonicity (Property 18)
    - **Property 18: Skill tag extraction is monotone with respect to skill content**
    - **Validates: Requirements 9.3**
    - Use `st.text()` for base description + `st.lists(st.text())` for added skills; assert tag count does not decrease

  - [ ] 4.12 Implement `FreelancingSharedModule` in `arifgate_ai/app/modules/freelancing_shared.py`
    - Platform-wide help chatbot for Client and Freelancer roles; semantic job–freelancer matching via RAG
    - Accepts `top_k` (default 5); returns empty list when no matches above 0.7 threshold
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ]* 4.13 Write property test for match results bounded by top_k (Property 12)
    - **Property 12: Match results are bounded by top_k**
    - **Validates: Requirements 10.3, 10.4**
    - Use `st.integers(min_value=1, max_value=20)` for top_k; assert `len(results) <= top_k` and all `similarity >= 0.7`

  - [ ] 4.14 Create `arifgate_ai/app/modules/router.py` with `ModuleRouter` mapping `(role, module_key)` → module class instance
    - _Requirements: 2.2_

  - [ ]* 4.15 Write property test for system prompt selection (Property 5)
    - **Property 5: System prompt selection is correct for every (role, module) pair**
    - **Validates: Requirements 2.2, 5.1, 6.1, 8.1, 9.1**
    - Use `st.sampled_from(list(MODULE_REGISTRY.keys()))`; assert first message is system message matching registered prompt

  - [ ]* 4.16 Write property test for shared module role access (Property 11)
    - **Property 11: Shared modules accept all valid marketplace roles**
    - **Validates: Requirements 7.1, 10.1**
    - Use `st.sampled_from([Role.student, Role.instructor])` for `CourseSharedModule` and `st.sampled_from([Role.client, Role.freelancer])` for `FreelancingSharedModule`; assert no role-rejection error

- [ ] 5. Implement structured output parsers and Pretty Printer
  - Create `arifgate_ai/app/services/output_parser.py` with `OutputParser.parse(role, raw) -> BaseModel` and `OutputSerializer.to_response(obj) -> ChatResponse`
  - Create `arifgate_ai/app/services/pretty_printer.py` with `pretty_print(obj: BaseModel) -> str`
  - Return HTTP 422 with descriptive message when LLM output fails schema parsing
  - _Requirements: 11.1, 11.2, 11.3_

  - [ ]* 5.1 Write property test for document metadata serialization round-trip (Property 8)
    - **Property 8: Document metadata serialization round-trip**
    - **Validates: Requirements 3.6, 11.3**
    - Use `st.builds(DocumentMetadata)`; assert `DocumentMetadata.model_validate_json(pretty_print(obj)) == obj`

  - [ ]* 5.2 Write property test for structured output round-trip (Property 9)
    - **Property 9: Structured output round-trip (parse → print → parse)**
    - **Validates: Requirements 11.4**
    - Use `st.one_of(st.builds(CourseDescription), st.builds(JobDescription), st.builds(FreelancerProposal))`; assert parse(print(parse(json))) == first parsed object

- [ ] 6. Extend Core AI Service routers and ingest endpoint
  - Create `arifgate_ai/app/routers/chat.py` — `POST /v1/chat` wiring `ModuleRouter → build_messages → RAGEngine → InferenceRouter → OutputParser → ChatResponse`
  - Create `arifgate_ai/app/routers/ingest.py` — `POST /v1/ingest` calling `VectorDBAdapter.ingest`
  - Add `GET /v1/health` returning `{"status": "ok"}`
  - Register routers in `arifgate_ai/app/main.py`; update `AuthMiddleware` protected prefixes if needed
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.2, 3.4, 12.2_

- [ ] 7. Add structured JSON logging to Core AI Service
  - Create `arifgate_ai/app/services/logger.py` emitting `CoreLogEntry` as JSON after each request
  - Log `timestamp`, `role`, `session_id`, `latency_ms`, `status_code`; log unhandled exceptions at ERROR level without exposing stack traces to callers
  - _Requirements: 12.4, 12.5_

  - [ ]* 7.1 Write property test for Core AI Service log fields (Property 14)
    - **Property 14: Core AI Service structured log entries contain all required fields**
    - **Validates: Requirements 12.4**
    - Use `st.builds(InternalChatRequest)`; assert emitted log JSON contains all required fields with non-null values

- [ ] 8. Checkpoint — Core AI Service
  - Ensure all Core AI Service tests pass. Ask the user if questions arise.

- [ ] 9. Implement AI Gateway
  - [ ] 9.1 Create `gateway/main.py` as a separate FastAPI app with `GET /health`, `POST /chat`, `POST /ingest`
    - Health returns `{"status": "ok"}`
    - _Requirements: 1.1, 12.1_

  - [ ] 9.2 Implement `GatewayAuthMiddleware` in `gateway/middleware/auth.py`
    - Validates `Authorization: Bearer <AI_GATEWAY_SECRET>`; returns 401 on missing/invalid token; does not forward request
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 9.3 Write property test for auth validation (Property 1)
    - **Property 1: Auth validation rejects all invalid tokens**
    - **Validates: Requirements 1.1, 1.2**
    - Use `st.text()` for token values; assert any token != `AI_GATEWAY_SECRET` returns 401 and request is not forwarded

  - [ ] 9.4 Implement `RateLimitMiddleware` in `gateway/middleware/rate_limit.py`
    - Per-client sliding-window counter; returns 429 when `GATEWAY_RATE_LIMIT_RPM` exceeded
    - _Requirements: 1.6_

  - [ ]* 9.5 Write property test for rate limiting (Property 3)
    - **Property 3: Rate limiting enforces per-client request cap**
    - **Validates: Requirements 1.6**
    - Use `st.integers(min_value=1, max_value=200)` for request counts; assert requests beyond limit return 429

  - [ ] 9.6 Implement `RequestLoggingMiddleware` in `gateway/middleware/logging.py`
    - Emits `GatewayLogEntry` as structured JSON after each response
    - _Requirements: 12.3_

  - [ ]* 9.7 Write property test for Gateway log fields (Property 13)
    - **Property 13: Gateway structured log entries contain all required fields**
    - **Validates: Requirements 12.3**
    - Use `st.builds(GatewayChatRequest)`; assert emitted log JSON contains `timestamp`, `role`, `module`, `latency_ms`, `status_code` with non-null values

  - [ ] 9.8 Implement Gateway proxy router in `gateway/routers/proxy.py`
    - Validates `role` field (422 on unknown role); builds `InternalChatRequest`; forwards to `CORE_AI_SERVICE_URL`; strips `openai_api_key` from response
    - Returns 502 on upstream error, 504 on timeout
    - _Requirements: 1.4, 1.5, 1.7, 2.1_

  - [ ]* 9.9 Write property test for role-based routing (Property 2)
    - **Property 2: Role-based routing accepts valid roles and rejects unknown ones**
    - **Validates: Requirements 1.4, 1.5**
    - Use `st.sampled_from(Role)` for valid roles and `st.text()` filtered to non-Role values for invalid; assert valid routes succeed and invalid return 422

  - [ ]* 9.10 Write property test for API key not in response (Property 4)
    - **Property 4: OpenAI API key is never present in Gateway responses**
    - **Validates: Requirements 1.7**
    - Use `st.builds(GatewayChatRequest)`; assert response body does not contain `OPENAI_API_KEY` value

- [ ] 10. Checkpoint — AI Gateway
  - Ensure all Gateway tests pass. Ask the user if questions arise.

- [ ] 11. Wire everything together and update configuration
  - Add `gateway/requirements.txt` and ensure `arifgate_ai/requirements.txt` includes `hypothesis`, `chromadb`, `pinecone-client`, `httpx`
  - Update `arifgate_ai/app/main.py` to register all new routers and apply structured logging middleware
  - Ensure `gateway/main.py` middleware stack order: `GatewayAuthMiddleware` → `RateLimitMiddleware` → `RequestLoggingMiddleware`
  - Update `arifgate_ai/tests/conftest.py` with shared fixtures for both Gateway and Core AI Service test clients
  - _Requirements: 1.1–1.7, 2.1–2.8, 12.1–12.5_

- [ ] 12. Final checkpoint — Full test suite
  - Ensure all unit tests and property-based tests pass across both components. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Property tests use `@settings(max_examples=100)` and include a comment tag: `# Feature: ai-architecture-modules, Property N: <title>`
- Each property test is a single function per correctness property from the design document
- The Gateway and Core AI Service are separate processes; use `httpx.AsyncClient` for inter-service calls in tests
