# Arifgate AI — Role-Based AI Chatbot Service

A standalone Python/FastAPI microservice that provides intelligent, role-aware AI chat responses for the **Arifgate platform** — covering both the Course Marketplace and the Freelancing Marketplace.

---

## Features

- Role-specific AI endpoints for Student, Instructor, Client, Freelancer, and Admin
- Multi-turn conversation sessions with 60-minute TTL and 20-turn history cap
- Optional RAG (Retrieval-Augmented Generation) with ChromaDB or FAISS backends
- Bearer token authentication on all protected endpoints
- Structured JSON logging per request
- OpenAI GPT integration with 30s timeout and error mapping (502/504)
- Auto-generated OpenAPI docs at `/docs`

---

## Project Structure

```
arifgate_ai/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── schemas.py               # Pydantic models (Role, ChatRequest, ChatResponse, ...)
│   ├── models.py                # Dataclasses (Message, Session)
│   ├── middleware/
│   │   ├── auth.py              # Bearer token auth middleware
│   │   └── logging.py           # Structured JSON logging middleware
│   ├── routers/
│   │   ├── chat.py              # All chat endpoints (generic + role-specific)
│   │   ├── ingest.py            # Document ingestion endpoint
│   │   └── health.py            # Health check endpoint
│   └── services/
│       ├── prompt_builder.py    # Role → system prompt mapping
│       ├── session_store.py     # In-memory session management
│       ├── llm_client.py        # OpenAI AsyncOpenAI wrapper
│       ├── vector_store.py      # ChromaDB / FAISS adapter
│       └── rag_engine.py        # RAG retrieval logic
├── tests/                       # Unit + property-based tests
├── env                          # Environment variables (never commit secrets)
├── requirements.txt
└── pytest.ini
```

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv envchat
envchat\Scripts\activate        # Windows
# source envchat/bin/activate   # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r arifgate_ai/requirements.txt
```

### 3. Configure environment variables

Edit `arifgate_ai/env`:

```env
OPENAI_API_KEY=sk-...
AI_SERVICE_SECRET=your-secret-token
OPENAI_MODEL=gpt-4o
RAG_BACKEND=chromadb
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | Your OpenAI API key |
| `AI_SERVICE_SECRET` | Yes | — | Bearer token for API auth |
| `OPENAI_MODEL` | No | `gpt-4o` | LLM model name |
| `RAG_BACKEND` | No | `chromadb` | `chromadb` or `faiss` |
| `CHROMA_PERSIST_DIR` | No | in-memory | ChromaDB persistence path |

---

## Running the Server

```bash
# From the project root
envchat\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8001
```

> Port 8000 may be occupied by another service (e.g. Django). Use 8001 or any free port.

The server will be available at `http://localhost:8001`.
Interactive API docs: `http://localhost:8001/docs`

---

## API Endpoints

All chat and ingest endpoints require:
```
Authorization: Bearer <AI_SERVICE_SECRET>
Content-Type: application/json
```

### Role-Specific Chat Endpoints

| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/v1/chat/student` | Student | Course help, guidance, recommendations |
| POST | `/v1/chat/instructor` | Instructor | Course creation, content generation |
| POST | `/v1/chat/client` | Client | Job descriptions, candidate recommendations |
| POST | `/v1/chat/freelancer` | Freelancer | Proposals, skill tags, job recommendations |
| POST | `/v1/chat/admin` | Admin | Platform oversight and moderation |
| POST | `/v1/chat/guest` | Guest | General platform info, sign-up guidance |
| POST | `/v1/chat` | Any | Generic endpoint — pass `role` in body |

### Other Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/v1/ingest` | Yes | Ingest documents into the vector store |
| GET | `/v1/health` | No | Liveness check |
| GET | `/docs` | No | Swagger UI |

---

## Request / Response Format

### Chat request (role-specific endpoints)

```json
{
  "message": "What Python courses do you recommend for beginners?",
  "session_id": null,
  "context_data": ["optional document 1", "optional document 2"],
  "use_rag": false
}
```

### Chat response

```json
{
  "reply": "Here are some great Python courses for beginners...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "Student",
  "recommendations": [
    {"title": "Python Basics", "description": "...", "link": ""}
  ],
  "matches": []
}
```

### Ingest request

```json
{
  "documents": ["Course: Python for Beginners. Topics: variables, loops..."],
  "domain": "courses"
}
```

---

## Testing the Endpoints

> All test payloads are in `test_data/`. Set your `AI_SERVICE_SECRET` in `arifgate_ai/env` first.
> Replace `your-secret-token` with the value of `AI_SERVICE_SECRET`.

---

### Health Check

```bash
curl http://localhost:8001/v1/health
```

Expected response:
```json
{"status": "ok"}
```

---

### Student — `POST /v1/chat/student`

**1. Course recommendations**
```bash
curl -X POST http://localhost:8001/v1/chat/student \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to learn web development from scratch. What courses should I start with?"
  }'
```

**2. Topic explanation**
```bash
curl -X POST http://localhost:8001/v1/chat/student \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you explain the difference between supervised and unsupervised machine learning?"
  }'
```

**3. With RAG context (course catalog)**
```bash
curl -X POST http://localhost:8001/v1/chat/student \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which course is best for me if I already know basic HTML?",
    "use_rag": true,
    "context_data": [
      "Course: Advanced CSS & Flexbox. Level: Intermediate. Topics: layouts, animations, responsive design. Rating: 4.8",
      "Course: JavaScript for Beginners. Level: Beginner. Topics: variables, DOM, events. Rating: 4.7",
      "Course: React Fundamentals. Level: Intermediate. Prerequisites: JavaScript basics. Rating: 4.9"
    ]
  }'
```

**4. Multi-turn session (copy `session_id` from a previous response)**
```bash
curl -X POST http://localhost:8001/v1/chat/student \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which of those courses has the best reviews for complete beginners?",
    "session_id": "PASTE_SESSION_ID_HERE"
  }'
```

---

### Instructor — `POST /v1/chat/instructor`

**1. Generate a course description**
```bash
curl -X POST http://localhost:8001/v1/chat/instructor \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Generate a course description for: Python for Data Science — covering pandas, numpy, matplotlib, and scikit-learn for beginners with basic Python knowledge."
  }'
```

**2. Course improvement advice**
```bash
curl -X POST http://localhost:8001/v1/chat/instructor \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My JavaScript course has a 3.9 rating and students say the exercises are too easy. How can I improve engagement and difficulty progression?"
  }'
```

**3. Course structure advice**
```bash
curl -X POST http://localhost:8001/v1/chat/instructor \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am building a 10-hour course on React. How should I structure the modules and what should each section cover?"
  }'
```

---

### Client — `POST /v1/chat/client`

**1. Generate a job description**
```bash
curl -X POST http://localhost:8001/v1/chat/client \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need a full-stack developer for a 3-month e-commerce project. The store sells handmade jewelry. I need product listings, a shopping cart, Stripe payments, and an admin dashboard."
  }'
```

**2. Skill and budget suggestions**
```bash
curl -X POST http://localhost:8001/v1/chat/client \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to build a mobile app for food delivery similar to Uber Eats but for a local city. What skills should I look for and what is a realistic budget?"
  }'
```

**3. Extract keyword tags from a job post**
```bash
curl -X POST http://localhost:8001/v1/chat/client \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Extract keyword tags from this job post: Looking for an experienced backend engineer to build REST APIs using Django and PostgreSQL. Must have experience with Docker, AWS deployment, and writing unit tests."
  }'
```

**4. Candidate recommendations with RAG context**
```bash
curl -X POST http://localhost:8001/v1/chat/client \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which of these freelancers is the best fit for my React dashboard project?",
    "use_rag": true,
    "context_data": [
      "Freelancer: Ahmed K. Skills: React, TypeScript, Node.js, REST APIs. Experience: 5 years. Rate: $45/hr. Rating: 4.9",
      "Freelancer: Sara M. Skills: Vue.js, JavaScript, CSS, Figma. Experience: 3 years. Rate: $35/hr. Rating: 4.7",
      "Freelancer: Omar T. Skills: React, Redux, GraphQL, AWS. Experience: 7 years. Rate: $65/hr. Rating: 5.0"
    ]
  }'
```

**5. Hiring process question**
```bash
curl -X POST http://localhost:8001/v1/chat/client \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the safest way to pay a freelancer? Can I do milestone-based payments and what happens if they do not deliver?"
  }'
```

---

### Freelancer — `POST /v1/chat/freelancer`

**1. Generate a proposal**
```bash
curl -X POST http://localhost:8001/v1/chat/freelancer \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a proposal for this job: Looking for a React developer to build a real-time chat app with WebSockets and a clean UI. Budget: $2000. Duration: 4 weeks. My skills: React, TypeScript, Socket.io, Tailwind CSS, 4 years experience."
  }'
```

**2. Extract skill tags from a profile**
```bash
curl -X POST http://localhost:8001/v1/chat/freelancer \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Extract skill tags from my profile: I am a backend developer with 6 years of experience building scalable APIs using Python, Django, and FastAPI. I have worked with PostgreSQL, Redis, Docker, and deployed on AWS and GCP."
  }'
```

**3. Job recommendations with RAG context**
```bash
curl -X POST http://localhost:8001/v1/chat/freelancer \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Which of these jobs is the best match for my skills in Python, Django, and REST APIs?",
    "use_rag": true,
    "context_data": [
      "Job: Build a Django REST API for a healthcare app. Budget: $3000. Duration: 6 weeks. Required: Django, PostgreSQL, JWT auth.",
      "Job: React Native mobile app for a fitness tracker. Budget: $2500. Duration: 8 weeks. Required: React Native, Firebase.",
      "Job: FastAPI microservice for an e-commerce platform. Budget: $1800. Duration: 3 weeks. Required: FastAPI, Docker, PostgreSQL."
    ]
  }'
```

**4. Platform safety question**
```bash
curl -X POST http://localhost:8001/v1/chat/freelancer \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "A client is asking me to work outside the platform and pay via bank transfer. Is this safe? What are the risks?"
  }'
```

---

### Admin — `POST /v1/chat/admin`

**1. Platform analytics guidance**
```bash
curl -X POST http://localhost:8001/v1/chat/admin \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Give me a summary of what metrics I should monitor weekly to track platform health across both the Course Marketplace and Freelancing Marketplace."
  }'
```

**2. Moderation guidance**
```bash
curl -X POST http://localhost:8001/v1/chat/admin \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "A user has been reported 3 times for posting fake reviews on courses. What actions should I take and what is the standard moderation process?"
  }'
```

---

### Guest — `POST /v1/chat/guest`

No account needed. Guests can ask general questions about the platform without authentication... wait — the guest endpoint still requires the Bearer token (all `/v1/` routes are protected). Use the same header.

**1. What is Arifgate?**
```bash
curl -X POST http://localhost:8001/v1/chat/guest \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Arifgate and what can I do here?"
  }'
```

**2. Ask about courses for beginners**
```bash
curl -X POST http://localhost:8001/v1/chat/guest \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Are there courses for complete beginners? I have never coded before."
  }'
```

**3. Ask about hiring a freelancer**
```bash
curl -X POST http://localhost:8001/v1/chat/guest \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need someone to build a website for my small business. Can I find a developer here?"
  }'
```

**4. Difference between the two marketplaces**
```bash
curl -X POST http://localhost:8001/v1/chat/guest \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the difference between the Course Marketplace and the Freelancing Marketplace?"
  }'
```

**5. Multi-turn session (follow-up)**
```bash
curl -X POST http://localhost:8001/v1/chat/guest \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I create an account and start learning?",
    "session_id": "PASTE_SESSION_ID_HERE"
  }'
```

---

### Ingest Documents — `POST /v1/ingest`

```bash
# Ingest course catalog for RAG
curl -X POST http://localhost:8001/v1/ingest \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      "Course: Python for Data Science. Level: Beginner. Topics: pandas, numpy, matplotlib. Rating: 4.8",
      "Course: React Fundamentals. Level: Intermediate. Prerequisites: JavaScript basics. Rating: 4.9",
      "Course: Django REST Framework. Level: Intermediate. Topics: APIs, auth, deployment. Rating: 4.7"
    ],
    "domain": "courses"
  }'

# Ingest freelancer profiles for RAG
curl -X POST http://localhost:8001/v1/ingest \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      "Freelancer: Ahmed K. Skills: React, TypeScript, Node.js. Rate: $45/hr. Rating: 4.9",
      "Freelancer: Sara M. Skills: Vue.js, JavaScript, Figma. Rate: $35/hr. Rating: 4.7"
    ],
    "domain": "freelancing"
  }'
```

---

> All test payloads are also available as JSON files in `test_data/` for use with Postman or any HTTP client.

---

## Running Tests

```bash
# From the project root
envchat\Scripts\python.exe -m pytest arifgate_ai/tests/ -v
```

Test files:

| File | Coverage |
|---|---|
| `test_auth_middleware.py` | Bearer token validation |
| `test_prompt_builder.py` | Role → system prompt mapping |
| `test_session_store.py` | Session CRUD + TTL property test |
| `test_llm_client.py` | LLM error mapping (502/504) |
| `test_rag.py` | RAG round-trip + engine unit tests |
| `test_ingest.py` | Ingest endpoint |
| `test_chat.py` | Chat router (all roles, session reuse) |
| `test_health_logging.py` | Health check + 500 error handling |

---

## Notes

- Sessions are in-memory — they reset on server restart. Swap `SessionStore` for a Redis-backed implementation for production.
- `AI_SERVICE_SECRET` and `OPENAI_API_KEY` must never be committed to version control.
- RAG is disabled by default (`use_rag: false`) to keep the hot path fast. Pass `context_data` directly for one-off document grounding without ingestion.
