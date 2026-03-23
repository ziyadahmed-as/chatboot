# Requirements Document

## Introduction

This feature extends the existing role-based AI chatbot microservice (Python/FastAPI) with a full multi-component architecture. The current service handles role-based chat with OpenAI and optional RAG. This extension introduces a formal AI Gateway layer for security and routing, a dedicated Core AI Service for LLM/RAG/prompt management, a Vector Database component (Chroma or Pinecone), and an optional GPU Server for high-throughput inference. It also expands the role-based module system to cover two marketplace domains — Course Marketplace and Freelancing Marketplace — with domain-specific AI capabilities per role.

---

## Glossary

- **AI_Gateway**: The entry-point component responsible for API key validation, request routing, and rate limiting. Sits in front of the Core_AI_Service.
- **Core_AI_Service**: The existing FastAPI microservice, extended to handle LLM calls, RAG integration, and prompt management as a dedicated internal service.
- **Vector_Database**: A persistent vector store (ChromaDB or Pinecone) used for semantic search and document retrieval.
- **GPU_Server**: An optional inference server for high-volume or low-latency AI processing, invoked when configured.
- **Instructor_Module**: The AI module serving Instructor-role users in the Course Marketplace.
- **Student_Module**: The AI module serving Student-role users in the Course Marketplace.
- **Course_Shared_Module**: The shared AI module for platform-wide chatbot and smart course recommendations in the Course Marketplace.
- **Client_Module**: The AI module serving Client-role users in the Freelancing Marketplace.
- **Freelancer_Module**: The AI module serving Freelancer-role users in the Freelancing Marketplace.
- **Freelancing_Shared_Module**: The shared AI module for AI job–freelancer matching and platform help in the Freelancing Marketplace.
- **Role**: A user classification (Instructor, Student, Client, Freelancer) that determines which module and system prompt handles a request.
- **System_Prompt**: A role- and module-specific instruction set injected at the start of each LLM conversation.
- **RAG_Engine**: The Retrieval-Augmented Generation component that retrieves relevant documents from the Vector_Database before LLM generation.
- **Embedding**: A numerical vector representation of text used for semantic similarity search.
- **Backend**: The existing application backend that communicates with the AI_Gateway via REST/JSON.
- **Course_Marketplace**: The domain covering online course creation, enrollment, and learning.
- **Freelancing_Marketplace**: The domain covering freelance job posting, bidding, and project management.

---

## Requirements

### Requirement 1: AI Gateway — Security and Routing

**User Story:** As a backend engineer, I want all AI requests to pass through a dedicated gateway, so that security, API key management, and routing are centralized and decoupled from business logic.

#### Acceptance Criteria

1. THE AI_Gateway SHALL validate the `Authorization` header containing a pre-shared bearer token on every inbound request before forwarding to the Core_AI_Service.
2. IF the `Authorization` header is missing or the token is invalid, THEN THE AI_Gateway SHALL return an HTTP 401 response without forwarding the request.
3. THE AI_Gateway SHALL read the expected bearer token from the `AI_GATEWAY_SECRET` environment variable and SHALL NOT hardcode credentials in source code.
4. THE AI_Gateway SHALL route requests to the appropriate role-based module handler based on the `role` field in the request payload.
5. WHEN a request is received with an unrecognized `role` value, THE AI_Gateway SHALL return an HTTP 422 response with a descriptive error identifying the invalid field.
6. THE AI_Gateway SHALL enforce a per-client rate limit, returning HTTP 429 when the limit is exceeded, configurable via the `GATEWAY_RATE_LIMIT_RPM` environment variable.
7. THE AI_Gateway SHALL forward the validated `OPENAI_API_KEY` (read from environment) to the Core_AI_Service and SHALL NOT expose it to the calling Backend.

---

### Requirement 2: Core AI Service — LLM, RAG, and Prompt Management

**User Story:** As a developer, I want a dedicated internal service that manages LLM calls, RAG retrieval, and prompt construction, so that these concerns are isolated and independently testable.

#### Acceptance Criteria

1. THE Core_AI_Service SHALL accept internal requests from the AI_Gateway and return structured JSON responses.
2. THE Core_AI_Service SHALL select the System_Prompt based on the `role` and `module` fields in the internal request.
3. WHEN `use_rag` is `true` in the request, THE Core_AI_Service SHALL invoke the RAG_Engine to retrieve relevant documents from the Vector_Database before calling the LLM.
4. WHEN `use_rag` is `true` and no documents above a similarity threshold of 0.7 are found, THE Core_AI_Service SHALL proceed with the LLM call without injecting retrieved context.
5. THE Core_AI_Service SHALL call the LLM using the OpenAI Chat Completions API with the assembled message list (system prompt + history + optional RAG context + user message).
6. WHEN the LLM API returns an error, THE Core_AI_Service SHALL return an HTTP 502 response to the AI_Gateway.
7. WHEN the LLM API does not respond within 30 seconds, THE Core_AI_Service SHALL return an HTTP 504 response to the AI_Gateway.
8. WHERE a GPU_Server is configured via the `GPU_SERVER_URL` environment variable, THE Core_AI_Service SHALL route inference requests to the GPU_Server instead of the OpenAI API.

---

### Requirement 3: Vector Database Integration

**User Story:** As a developer, I want the system to store and retrieve document embeddings from a persistent vector database, so that RAG-based responses are grounded in domain-specific knowledge.

#### Acceptance Criteria

1. THE Vector_Database SHALL support both ChromaDB and Pinecone as backends, selectable via the `VECTOR_DB_BACKEND` environment variable (`chromadb` or `pinecone`).
2. WHEN a document is ingested via `POST /v1/ingest`, THE Core_AI_Service SHALL generate an Embedding for the document and store it in the Vector_Database with an optional `domain` tag.
3. WHEN a semantic search query is issued, THE Vector_Database SHALL return the top-K documents with cosine similarity above the configured threshold.
4. THE Core_AI_Service SHALL expose a `POST /v1/ingest` endpoint that accepts a list of text documents and an optional `domain` tag, returning the count of successfully ingested documents.
5. FOR ALL documents ingested and then retrieved using the original text as the query, the retrieved document content SHALL match the originally ingested content (round-trip integrity property).
6. THE Core_AI_Service SHALL support a Pretty_Printer that serializes ingested document metadata back to a structured format, and FOR ALL valid document metadata objects, serializing then deserializing SHALL produce an equivalent object (round-trip property).

---

### Requirement 4: Optional GPU Server

**User Story:** As a platform operator, I want the system to optionally route inference to a dedicated GPU server, so that high-volume or latency-sensitive workloads can be handled without relying solely on the OpenAI API.

#### Acceptance Criteria

1. WHERE `GPU_SERVER_URL` is set, THE Core_AI_Service SHALL send inference requests to the GPU_Server endpoint instead of the OpenAI API.
2. WHERE `GPU_SERVER_URL` is not set, THE Core_AI_Service SHALL fall back to the OpenAI API for all inference requests.
3. WHEN the GPU_Server does not respond within 30 seconds, THE Core_AI_Service SHALL return an HTTP 504 response.
4. IF the GPU_Server returns an error response, THEN THE Core_AI_Service SHALL return an HTTP 502 response.

---

### Requirement 5: Course Marketplace — Instructor Module

**User Story:** As an Instructor, I want AI assistance for generating course descriptions, so that I can create compelling, well-structured course listings efficiently.

#### Acceptance Criteria

1. WHEN a request is received with `role=Instructor`, THE Instructor_Module SHALL use a System_Prompt focused on course creation, content structuring, and student engagement within the Course_Marketplace.
2. WHEN an Instructor provides a course topic and key learning objectives, THE Instructor_Module SHALL generate a structured course description including title, summary, target audience, and learning outcomes.
3. IF the provided course topic is fewer than 5 characters, THEN THE Instructor_Module SHALL return a validation error requesting more detail.
4. THE Instructor_Module SHALL format generated course descriptions as structured JSON with fields: `title`, `summary`, `target_audience`, and `learning_outcomes`.

---

### Requirement 6: Course Marketplace — Student Module

**User Story:** As a Student, I want a chatbot that helps me navigate courses and guides my learning, so that I can find the right content and stay on track.

#### Acceptance Criteria

1. WHEN a request is received with `role=Student`, THE Student_Module SHALL use a System_Prompt focused on course discovery, learning progress tracking, and study guidance within the Course_Marketplace.
2. WHEN a Student asks for course recommendations, THE Student_Module SHALL use the RAG_Engine to retrieve relevant course documents from the Vector_Database before generating a response.
3. WHEN a Student asks a question about a specific course topic, THE Student_Module SHALL provide a contextually relevant answer grounded in available course knowledge.
4. THE Student_Module SHALL maintain multi-turn conversation history per session to support coherent follow-up questions.

---

### Requirement 7: Course Marketplace — Shared Module

**User Story:** As any Course Marketplace user, I want access to a platform-wide AI chatbot and smart course recommendations, so that I can get general help and discover relevant courses regardless of my role.

#### Acceptance Criteria

1. THE Course_Shared_Module SHALL provide a platform-wide help chatbot accessible to all Course_Marketplace roles (Student, Instructor, Buyer, Seller).
2. WHEN a user requests course recommendations, THE Course_Shared_Module SHALL use the RAG_Engine to retrieve semantically relevant courses from the Vector_Database and return a ranked list.
3. THE Course_Shared_Module SHALL accept an optional `context` field in the request payload to personalize recommendations based on user history or preferences.

---

### Requirement 8: Freelancing Marketplace — Client Module

**User Story:** As a Client, I want AI assistance for creating job postings and evaluating candidates, so that I can attract the right freelancers and scope projects effectively.

#### Acceptance Criteria

1. WHEN a request is received with `role=Client`, THE Client_Module SHALL use a System_Prompt focused on job posting, freelancer evaluation, and project scoping within the Freelancing_Marketplace.
2. WHEN a Client provides a project description, THE Client_Module SHALL generate a structured job description including title, required skills, estimated budget range, and project scope.
3. WHEN a Client provides a project description, THE Client_Module SHALL suggest relevant skill tags and a budget range based on the project type and complexity.
4. THE Client_Module SHALL automatically extract and return keyword tags from a provided job description for use in search indexing.
5. WHEN a Client requests candidate recommendations, THE Client_Module SHALL use the RAG_Engine to retrieve and rank relevant freelancer profiles from the Vector_Database.
6. THE Client_Module SHALL format generated job descriptions as structured JSON with fields: `title`, `description`, `required_skills`, `budget_range`, and `keywords`.

---

### Requirement 9: Freelancing Marketplace — Freelancer Module

**User Story:** As a Freelancer, I want AI assistance for writing proposals and positioning my profile, so that I can win more jobs and present my skills effectively.

#### Acceptance Criteria

1. WHEN a request is received with `role=Freelancer`, THE Freelancer_Module SHALL use a System_Prompt focused on proposal writing, skill positioning, and job matching within the Freelancing_Marketplace.
2. WHEN a Freelancer provides a job description and their skill summary, THE Freelancer_Module SHALL generate a tailored proposal highlighting relevant experience and fit.
3. WHEN a Freelancer provides a profile description, THE Freelancer_Module SHALL extract and return a list of skill tags for profile indexing.
4. WHEN a Freelancer requests job recommendations, THE Freelancer_Module SHALL use the RAG_Engine to retrieve and rank relevant job postings from the Vector_Database.
5. THE Freelancer_Module SHALL format generated proposals as structured text with sections: introduction, relevant experience, proposed approach, and call to action.

---

### Requirement 10: Freelancing Marketplace — Shared Module

**User Story:** As any Freelancing Marketplace user, I want access to AI-powered job–freelancer matching and a platform help chatbot, so that the right people find the right opportunities.

#### Acceptance Criteria

1. THE Freelancing_Shared_Module SHALL provide a platform-wide help chatbot accessible to all Freelancing_Marketplace roles (Client, Freelancer).
2. WHEN a matching request is received, THE Freelancing_Shared_Module SHALL use the RAG_Engine to compute semantic similarity between job postings and freelancer profiles and return a ranked match list.
3. THE Freelancing_Shared_Module SHALL accept a `top_k` parameter (default 5) to control the number of matches returned.
4. WHEN no matches above a similarity threshold of 0.7 are found, THE Freelancing_Shared_Module SHALL return an empty match list rather than low-confidence results.

---

### Requirement 11: Structured Output and Parsers

**User Story:** As a developer, I want all AI-generated structured outputs (job descriptions, course descriptions, proposals) to be parseable and round-trip safe, so that downstream systems can reliably consume them.

#### Acceptance Criteria

1. THE Core_AI_Service SHALL parse LLM-generated structured outputs (course descriptions, job descriptions, proposals) into typed Python objects before returning them to the AI_Gateway.
2. IF the LLM returns a response that cannot be parsed into the expected schema, THEN THE Core_AI_Service SHALL return an HTTP 422 response with a descriptive parsing error.
3. THE Core_AI_Service SHALL include a Pretty_Printer that serializes typed output objects back to JSON strings.
4. FOR ALL valid structured output objects, parsing then printing then parsing SHALL produce an equivalent object (round-trip property).

---

### Requirement 12: Observability and Health

**User Story:** As a DevOps engineer, I want both the AI_Gateway and Core_AI_Service to expose health checks and structured logs, so that I can monitor the full pipeline.

#### Acceptance Criteria

1. THE AI_Gateway SHALL expose a `GET /health` endpoint returning HTTP 200 with `{"status": "ok"}` when operational.
2. THE Core_AI_Service SHALL expose a `GET /v1/health` endpoint returning HTTP 200 with `{"status": "ok"}` when operational.
3. THE AI_Gateway SHALL emit structured JSON logs for every proxied request, including `timestamp`, `role`, `module`, `latency_ms`, and `status_code`.
4. THE Core_AI_Service SHALL emit structured JSON logs for every processed request, including `timestamp`, `role`, `session_id`, `latency_ms`, and `status_code`.
5. IF an unhandled exception occurs in either component, THEN the component SHALL log the exception at ERROR level and return HTTP 500 with a generic error message, without exposing internal stack traces to the caller.
