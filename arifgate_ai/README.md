# Arifgate AI Service

An AI microservice for the **Arifgate platform**, delivering intelligent features across both the
**Course Marketplace** and the **Freelancing Marketplace**.

Built with **FastAPI** and **OpenAI GPT-4o**, the service covers four capability areas:
role-aware conversational chat, structured content generation, smart recommendations,
and AI-driven job–freelancer matching.

---

## Architecture

```
Client / Frontend
       │
       ▼
┌──────────────────────────────────────────┐
│            Arifgate AI Service           │
│              FastAPI  ·  Python 3.12     │
│                                          │
│  /v1/chat/*        Role-aware chat       │
│  /v1/generate/*    Content generation    │
│  /v1/ai/*          Recommend & Match     │
│  /v1/health        Liveness probe        │
└──────────────────┬───────────────────────┘
                   │  OpenAI Python SDK (async)
                   ▼
            OpenAI GPT-4o API
```

---

## Capabilities

### Phase 1 — Conversational Chat
Role-specific multi-turn chat powered by GPT-4o. Each role has a tailored system prompt.
Sessions are stored in memory with a 60-minute TTL and a 20-message context window.

| Role | Focus |
|---|---|
| Student | Course discovery, study guidance, learning path advice |
| Instructor | Course creation, curriculum design, student engagement |
| Client | Job posting help, candidate evaluation, project scoping |
| Freelancer | Proposal writing, skill positioning, job matching advice |
| Admin | Platform moderation, analytics, policy enforcement |
| Guest | General platform info, sign-up guidance, marketplace overview |

### Phase 2 — Content Generation, Recommendations & Matching
Structured AI tasks that return clean JSON — no free-form chat, just actionable output.

| Endpoint | Purpose |
|---|---|
| `POST /v1/generate/course-description` | Generate course title, description, and highlights |
| `POST /v1/generate/job-description` | Generate job posting with required skills and budget estimate |
| `POST /v1/generate/proposal` | Generate a freelancer proposal with key selling points |
| `POST /v1/generate/skill-tags` | Extract skills and keywords from any text |
| `POST /v1/ai/recommend` | Rank a list of courses, jobs, or profiles by relevance |
| `POST /v1/ai/match` | Match freelancer profiles to a job description with scores |

---

## Project Structure

```
arifgate_ai/
├── app/
│   ├── main.py                   # FastAPI app, middleware, router registration
│   ├── schemas.py                # All Pydantic request/response models
│   ├── models.py                 # Session and Message dataclasses
│   ├── middleware/
│   │   ├── auth.py               # Bearer token authentication (disabled for dev)
│   │   └── logging.py            # Structured JSON request logging
│   ├── routers/
│   │   ├── chat.py               # /v1/chat/* — role-specific chat endpoints
│   │   ├── generate.py           # /v1/generate/* — content generation endpoints
│   │   ├── recommend.py          # /v1/ai/* — recommendation & matching endpoints
│   │   └── health.py             # /v1/health
│   └── services/
│       ├── llm_client.py         # Lazy-initialized async OpenAI client
│       ├── ai_service.py         # Structured AI tasks (generation, matching)
│       ├── prompt_builder.py     # Role → system prompt mapping
│       └── session_store.py      # In-memory session store with TTL
├── tests/                        # Unit and property-based tests (37 passing)
├── test_data/                    # Sample JSON payloads per role
├── .env                          # Environment variables — never commit
├── requirements.txt
└── pytest.ini
```

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv envchat
envchat\Scripts\activate        # Windows
source envchat/bin/activate     # macOS / Linux
```

### 2. Install dependencies

```bash
pip install -r arifgate_ai/requirements.txt
```

### 3. Configure environment variables

Create or edit `arifgate_ai/.env`:

```env
OPENAI_API_KEY=sk-...
AI_SERVICE_SECRET=your-secret-token
OPENAI_MODEL=gpt-4o
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | Your OpenAI API key |
| `AI_SERVICE_SECRET` | Yes | — | Bearer token for API authentication |
| `OPENAI_MODEL` | No | `gpt-4o` | OpenAI model to use |

### 4. Start the server

Run from inside the `arifgate_ai/` directory:

```bash
# Windows
..\envchat\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8001 --reload

# macOS / Linux
../envchat/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

> Port 8000 is reserved for the Django backend. Use 8001.

The service is available at:
- API base: `http://localhost:8001`
- Interactive docs: `http://localhost:8001/docs`
- Health check: `http://localhost:8001/v1/health`

---

## API Reference

> Authentication is currently disabled for development.
> To re-enable, update `app/middleware/auth.py` and pass `Authorization: Bearer <AI_SERVICE_SECRET>` on all `/v1/` requests.

---

### Chat Endpoints

All chat endpoints accept the same request body. `session_id` is optional on the first turn —
copy it from the response and pass it on subsequent turns to maintain conversation history.

**Request body**
```json
{
  "message": "Your message here",
  "session_id": null,
  "context_data": ["optional document 1", "optional document 2"]
}
```

**Response body**
```json
{
  "reply": "AI response text",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "Student",
  "recommendations": [],
  "matches": []
}
```

| Method | Endpoint | Role |
|---|---|---|
| POST | `/v1/chat/student` | Student |
| POST | `/v1/chat/instructor` | Instructor |
| POST | `/v1/chat/client` | Client |
| POST | `/v1/chat/freelancer` | Freelancer |
| POST | `/v1/chat/admin` | Admin |
| POST | `/v1/chat/guest` | Guest (no account needed) |
| POST | `/v1/chat` | Any — pass `role` field in body |

---

### Content Generation Endpoints

#### `POST /v1/generate/course-description`
Generate a course description with highlights.

```json
// Request
{
  "title": "Python for Data Science",
  "topics": ["pandas", "numpy", "matplotlib", "scikit-learn"],
  "target_audience": "Developers with basic Python knowledge",
  "level": "Beginner"
}

// Response
{
  "title": "Python for Data Science",
  "description": "Master the essential Python libraries...",
  "highlights": ["Hands-on projects with real datasets", "..."]
}
```

#### `POST /v1/generate/job-description`
Generate a professional job posting with skill and budget suggestions.

```json
// Request
{
  "project_title": "E-commerce Backend API",
  "requirements": "Build a REST API for an online store with Stripe payments and order tracking",
  "budget": "$3000",
  "duration": "6 weeks"
}

// Response
{
  "title": "E-commerce Backend API",
  "description": "We are looking for an experienced backend developer...",
  "required_skills": ["Django", "PostgreSQL", "Stripe API", "Docker"],
  "suggested_budget": "$2500 - $3500",
  "suggested_duration": "5-7 weeks"
}
```

#### `POST /v1/generate/proposal`
Generate a tailored freelancer proposal for a job posting.

```json
// Request
{
  "job_description": "Build a REST API for a healthcare appointment booking system...",
  "freelancer_skills": ["Django", "FastAPI", "PostgreSQL", "Docker"],
  "experience_years": 5,
  "hourly_rate": "$45"
}

// Response
{
  "proposal": "Dear Hiring Manager, I am excited to apply for...",
  "key_selling_points": ["5 years Django experience", "Healthcare API background", "..."]
}
```

#### `POST /v1/generate/skill-tags`
Extract structured skill tags and search keywords from any text.

```json
// Request
{
  "text": "Backend developer with 5 years experience in Python, Django, FastAPI, PostgreSQL, Docker, and AWS deployment."
}

// Response
{
  "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Docker", "AWS"],
  "keywords": ["backend", "REST API", "cloud deployment", "microservices"]
}
```

---

### Recommendation & Matching Endpoints

#### `POST /v1/ai/recommend`
Rank a list of courses, jobs, or profiles by relevance to a user query.

```json
// Request
{
  "role": "Student",
  "query": "I want to learn web development from scratch",
  "items": [
    "Course: JavaScript for Beginners. Level: Beginner. Rating: 4.7",
    "Course: React Fundamentals. Level: Intermediate. Prerequisites: JavaScript",
    "Course: HTML & CSS Basics. Level: Beginner. Rating: 4.8"
  ],
  "top_k": 2
}

// Response
{
  "recommendations": [
    {
      "title": "HTML & CSS Basics",
      "description": "Best starting point for web development with no prior experience.",
      "link": ""
    },
    {
      "title": "JavaScript for Beginners",
      "description": "Natural next step after learning HTML and CSS.",
      "link": ""
    }
  ]
}
```

#### `POST /v1/ai/match`
Match freelancer profiles to a job description with relevance scores.

```json
// Request
{
  "job_description": "Build a Django REST API for a fintech startup. Required: Django, PostgreSQL, Celery, Redis.",
  "freelancer_profiles": [
    "Tariq S. Skills: Django, FastAPI, PostgreSQL, Docker. 5 years experience. Rate: $45/hr.",
    "Mia T. Skills: Vue.js, Laravel, MySQL. 4 years experience. Rate: $40/hr.",
    "Ahmed K. Skills: Django, Celery, Redis, PostgreSQL. 6 years experience. Rate: $55/hr."
  ],
  "top_k": 2
}

// Response
{
  "matches": [
    {
      "name": "Ahmed K.",
      "skills": "Django, Celery, Redis, PostgreSQL",
      "match_score": "96%",
      "link": ""
    },
    {
      "name": "Tariq S.",
      "skills": "Django, FastAPI, PostgreSQL, Docker",
      "match_score": "82%",
      "link": ""
    }
  ]
}
```

---

## curl Examples

### Health check
```bash
curl http://localhost:8001/v1/health
```

### Student chat
```bash
curl -X POST http://localhost:8001/v1/chat/student \
  -H "Content-Type: application/json" \
  -d '{"message": "I know basic Python. What should I learn next to become a full-stack developer?"}'
```

### Multi-turn session
```bash
# Turn 1 — start a session
curl -X POST http://localhost:8001/v1/chat/student \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the best way to learn React?"}'

# Turn 2 — continue the session (paste session_id from turn 1 response)
curl -X POST http://localhost:8001/v1/chat/student \
  -H "Content-Type: application/json" \
  -d '{"message": "How long will it take if I study 2 hours a day?", "session_id": "PASTE_SESSION_ID"}'
```

### Generate a course description
```bash
curl -X POST http://localhost:8001/v1/generate/course-description \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Machine Learning with Python",
    "topics": ["linear regression", "decision trees", "neural networks"],
    "target_audience": "Developers with basic Python knowledge",
    "level": "Intermediate"
  }'
```

### Generate a job description
```bash
curl -X POST http://localhost:8001/v1/generate/job-description \
  -H "Content-Type: application/json" \
  -d '{
    "project_title": "Fashion E-commerce Store",
    "requirements": "Product listings, shopping cart, Stripe payments, admin panel",
    "budget": "$3000",
    "duration": "8 weeks"
  }'
```

### Generate a proposal
```bash
curl -X POST http://localhost:8001/v1/generate/proposal \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Build a REST API for a healthcare booking system using Django and PostgreSQL.",
    "freelancer_skills": ["Django", "FastAPI", "PostgreSQL", "Docker"],
    "experience_years": 5,
    "hourly_rate": "$45"
  }'
```

### Extract skill tags
```bash
curl -X POST http://localhost:8001/v1/generate/skill-tags \
  -H "Content-Type: application/json" \
  -d '{"text": "Backend developer specializing in Python, Django, FastAPI, PostgreSQL, Redis, Docker, and AWS."}'
```

### Smart recommendations
```bash
curl -X POST http://localhost:8001/v1/ai/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Freelancer",
    "query": "I specialize in Python and Django REST APIs",
    "items": [
      "Job: Django API for fintech startup. Budget: $4000. Required: Django, PostgreSQL, Celery.",
      "Job: React Native mobile app. Budget: $2500. Required: React Native, Firebase.",
      "Job: FastAPI microservice for AI platform. Budget: $3000. Required: FastAPI, Docker, AWS."
    ],
    "top_k": 2
  }'
```

### Freelancer matching
```bash
curl -X POST http://localhost:8001/v1/ai/match \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Build a Django REST API for a fintech startup. Required: Django, PostgreSQL, Celery, Redis.",
    "freelancer_profiles": [
      "Tariq S. Skills: Django, FastAPI, PostgreSQL, Docker. 5 years. Rate: $45/hr.",
      "Ahmed K. Skills: Django, Celery, Redis, PostgreSQL. 6 years. Rate: $55/hr."
    ],
    "top_k": 2
  }'
```

---

## Running Tests

```bash
# From the project root
envchat\Scripts\python.exe -m pytest arifgate_ai/tests/ -v
```

All 37 tests pass. No external services required — OpenAI calls are mocked.

| Test File | Coverage |
|---|---|
| `test_auth_middleware.py` | Bearer token validation |
| `test_chat.py` | Chat router — all roles, session reuse |
| `test_prompt_builder.py` | Role → system prompt mapping |
| `test_session_store.py` | Session CRUD, TTL expiry, property tests |
| `test_llm_client.py` | OpenAI error mapping (502, 504, 429) |
| `test_health_logging.py` | Health check, unhandled exception handling |

---

## Notes

- **Authentication** is currently disabled for development. Re-enable it in `app/middleware/auth.py` before deploying to production.
- **Sessions** are stored in memory and reset on server restart. Replace `SessionStore` with a Redis-backed implementation for production.
- **Test data** for all roles is available in `test_data/` — use with Postman or any HTTP client.
- `OPENAI_API_KEY` must never be committed to version control. It is covered by `.gitignore`.
