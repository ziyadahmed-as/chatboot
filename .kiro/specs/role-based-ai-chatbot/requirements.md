# Requirements Document

## Introduction

A role-based AI chatbot microservice that provides intelligent, context-aware, and role-specific guidance across two marketplace domains: a Course Marketplace and a Freelancing Marketplace. The service is implemented as a standalone AI microservice (Python/FastAPI) that communicates with the existing backend via REST/JSON. It integrates with OpenAI LLMs and optionally supports Retrieval-Augmented Generation (RAG) for grounding responses in domain-specific knowledge. Each user role receives tailored responses, recommendations, and automation assistance relevant to their context.

---

## Glossary

- **AI_Service**: The standalone AI microservice responsible for processing chat requests and returning responses.
- **LLM**: Large Language Model (OpenAI GPT) used to generate natural language responses.
- **RAG_Engine**: The optional Retrieval-Augmented Generation component that retrieves relevant documents before generating a response.
- **Vector_Store**: A vector database (e.g., ChromaDB or FAISS) used by the RAG_Engine to store and retrieve embedded documents.
- **Role**: A user classification that determines the system prompt, context, and capabilities available in a chat session. Roles include: Student, Instructor, Buyer, Seller, Freelancer, Client, and Admin.
- **Session**: A stateful conversation context tied to a user and role, maintaining message history for multi-turn dialogue.
- **System_Prompt**: A role-specific instruction set injected at the start of each LLM conversation to constrain and guide the model's behavior.
- **Backend**: The existing application backend that communicates with the AI_Service via REST/JSON.
- **Course_Marketplace**: The domain covering online course creation, enrollment, and learning.
- **Freelancing_Marketplace**: The domain covering freelance job posting, bidding, and project management.
- **Embedding**: A numerical vector representation of text used for semantic similarity search in the RAG_Engine.
- **Knowledge_Base**: A collection of domain-specific documents ingested into the Vector_Store for RAG retrieval.

---

## Requirements

### Requirement 1: Role-Based Chat Endpoint

**User Story:** As a backend service, I want to send a chat message along with a user role, so that the AI_Service returns a response tailored to that role's context and responsibilities.

#### Acceptance Criteria

1. THE AI_Service SHALL expose a REST endpoint `POST /chat` that accepts a JSON payload containing `role`, `message`, `session_id`, and optional `context` fields.
2. WHEN a request is received at `POST /chat`, THE AI_Service SHALL validate that the `role` field is one of the supported roles: Student, Instructor, Buyer, Seller, Freelancer, Client, or Admin.
3. IF the `role` field is missing or invalid, THEN THE AI_Service SHALL return an HTTP 422 response with a descriptive error message identifying the invalid field.
4. WHEN a valid request is received, THE AI_Service SHALL select and inject the role-specific System_Prompt before forwarding the conversation to the LLM.
5. THE AI_Service SHALL return the LLM response as a JSON object containing `reply`, `session_id`, and `role` fields.

---

### Requirement 2: Role-Specific System Prompts

**User Story:** As a product owner, I want each user role to receive contextually appropriate AI guidance, so that responses are relevant to the user's goals and domain.

#### Acceptance Criteria

1. THE AI_Service SHALL maintain a distinct System_Prompt for each supported role.
2. WHEN the role is Student, THE AI_Service SHALL use a System_Prompt that focuses on course discovery, learning progress, and study guidance within the Course_Marketplace.
3. WHEN the role is Instructor, THE AI_Service SHALL use a System_Prompt that focuses on course creation, student engagement, and content recommendations within the Course_Marketplace.
4. WHEN the role is Freelancer, THE AI_Service SHALL use a System_Prompt that focuses on proposal writing, skill positioning, and job matching within the Freelancing_Marketplace.
5. WHEN the role is Client, THE AI_Service SHALL use a System_Prompt that focuses on job posting, freelancer evaluation, and project scoping within the Freelancing_Marketplace.
6. WHEN the role is Admin, THE AI_Service SHALL use a System_Prompt that focuses on platform oversight, moderation assistance, and analytics interpretation across both marketplaces.
7. WHEN the role is Buyer, THE AI_Service SHALL use a System_Prompt that focuses on course recommendations and purchase guidance within the Course_Marketplace.
8. WHEN the role is Seller, THE AI_Service SHALL use a System_Prompt that focuses on listing optimization and sales performance within the Course_Marketplace.

---

### Requirement 3: Multi-Turn Conversation Session Management

**User Story:** As a user, I want the chatbot to remember the context of my previous messages within a session, so that I can have coherent multi-turn conversations.

#### Acceptance Criteria

1. THE AI_Service SHALL maintain conversation history per `session_id` for the duration of a session.
2. WHEN a message is received with an existing `session_id`, THE AI_Service SHALL include the prior message history in the LLM context window.
3. WHEN a message is received with a new or absent `session_id`, THE AI_Service SHALL create a new Session and return a generated `session_id` in the response.
4. THE AI_Service SHALL limit the conversation history included in the LLM context to the most recent 20 message turns to stay within token limits.
5. WHEN a session has been inactive for 60 minutes, THE AI_Service SHALL expire the session and discard its history.

---

### Requirement 4: OpenAI LLM Integration

**User Story:** As a developer, I want the AI_Service to use OpenAI's API for language generation, so that responses are high quality and configurable.

#### Acceptance Criteria

1. THE AI_Service SHALL use the OpenAI Chat Completions API to generate all responses.
2. THE AI_Service SHALL read the OpenAI API key from the `OPENAI_API_KEY` environment variable and SHALL NOT hardcode credentials in source code.
3. WHEN the OpenAI API returns an error response, THE AI_Service SHALL return an HTTP 502 response with a message indicating upstream LLM failure.
4. WHEN the OpenAI API does not respond within 30 seconds, THE AI_Service SHALL return an HTTP 504 response with a timeout error message.
5. THE AI_Service SHALL support configuration of the LLM model name (e.g., `gpt-4o`, `gpt-3.5-turbo`) via an environment variable `OPENAI_MODEL`, defaulting to `gpt-4o`.

---

### Requirement 5: Optional RAG Support

**User Story:** As a product owner, I want the chatbot to optionally retrieve relevant domain documents before generating a response, so that answers are grounded in platform-specific knowledge.

#### Acceptance Criteria

1. WHERE RAG is enabled, THE AI_Service SHALL retrieve the top-K semantically relevant documents from the Vector_Store before calling the LLM.
2. WHERE RAG is enabled, THE AI_Service SHALL prepend the retrieved document excerpts to the LLM context as additional grounding information.
3. THE AI_Service SHALL enable or disable RAG per-request via an optional boolean `use_rag` field in the request payload, defaulting to `false`.
4. WHEN `use_rag` is `true` and the Vector_Store contains no relevant documents above a similarity threshold of 0.7, THE AI_Service SHALL proceed with the LLM call without injecting retrieved context.
5. THE AI_Service SHALL support ingestion of documents into the Knowledge_Base via a `POST /ingest` endpoint that accepts a list of text documents and an optional `domain` tag (e.g., `courses`, `freelancing`).
6. WHEN a document is ingested, THE AI_Service SHALL generate an Embedding for the document and store it in the Vector_Store.
7. FOR ALL documents ingested and then retrieved, the retrieved document content SHALL match the originally ingested content (round-trip integrity property).

---

### Requirement 6: Request Authentication and Authorization

**User Story:** As a backend engineer, I want the AI_Service to verify that requests come from the authorized backend, so that the service is not publicly exploitable.

#### Acceptance Criteria

1. THE AI_Service SHALL require an `Authorization` header containing a pre-shared bearer token on all requests to `/chat` and `/ingest`.
2. IF the `Authorization` header is missing or the token is invalid, THEN THE AI_Service SHALL return an HTTP 401 response.
3. THE AI_Service SHALL read the expected bearer token from the `AI_SERVICE_SECRET` environment variable and SHALL NOT hardcode it in source code.

---

### Requirement 7: Health and Observability

**User Story:** As a DevOps engineer, I want the AI_Service to expose a health check endpoint and structured logs, so that I can monitor service availability and debug issues.

#### Acceptance Criteria

1. THE AI_Service SHALL expose a `GET /health` endpoint that returns HTTP 200 with a JSON body `{"status": "ok"}` when the service is running.
2. THE AI_Service SHALL emit structured JSON logs for every request, including `timestamp`, `role`, `session_id`, `latency_ms`, and `status_code`.
3. IF an unhandled exception occurs, THEN THE AI_Service SHALL log the exception details at ERROR level and return an HTTP 500 response with a generic error message, without exposing internal stack traces to the caller.

---

### Requirement 8: REST/JSON Contract with Backend

**User Story:** As a backend developer, I want a well-defined REST/JSON contract for the AI_Service, so that integration is straightforward and predictable.

#### Acceptance Criteria

1. THE AI_Service SHALL accept and return `Content-Type: application/json` on all endpoints.
2. THE AI_Service SHALL document all endpoints via an auto-generated OpenAPI schema accessible at `GET /docs`.
3. WHEN the request body does not conform to the expected JSON schema, THE AI_Service SHALL return an HTTP 422 response with field-level validation error details.
4. THE AI_Service SHALL version the API under a `/v1` path prefix (e.g., `POST /v1/chat`, `POST /v1/ingest`, `GET /v1/health`).
