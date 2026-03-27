"""
Endpoint smoke tests — dummy data.
Tests routing, request validation, and response structure.
OpenAI calls that hit rate limits are reported separately (not a routing failure).

Run from inside arifgate_ai/:
    python test_endpoints.py
"""
import json
import sys
import httpx

BASE = "http://localhost:8001"

PASS    = "\033[92m PASS\033[0m"
FAIL    = "\033[91m FAIL\033[0m"
WARN    = "\033[93m WARN\033[0m"
SECTION = "\033[96m"
RESET   = "\033[0m"

results = {"pass": 0, "fail": 0, "warn": 0}


def check(name: str, resp: httpx.Response, expected_status: int = 200):
    if resp.status_code == expected_status:
        tag = PASS
        results["pass"] += 1
        try:
            body = json.dumps(resp.json(), indent=2)
            preview = body[:300] + ("..." if len(body) > 300 else "")
        except Exception:
            preview = resp.text[:300]
        print(f"{tag}  [{resp.status_code}]  {name}")
        print(f"       {preview}\n")
    elif resp.status_code == 429:
        # Rate limit — routing worked, OpenAI quota exhausted
        tag = WARN
        results["warn"] += 1
        print(f"{tag}  [{resp.status_code}]  {name}  (OpenAI rate limit — routing OK)\n")
    else:
        tag = FAIL
        results["fail"] += 1
        print(f"{tag}  [{resp.status_code}]  {name}")
        print(f"       {resp.text[:400]}\n")
    return resp


client = httpx.Client(timeout=60)

print(f"\n{SECTION}{'='*62}{RESET}")
print(f"{SECTION}  Arifgate AI — Endpoint Smoke Tests{RESET}")
print(f"{SECTION}{'='*62}{RESET}\n")

# ── Infrastructure ────────────────────────────────────────────
print(f"{SECTION}── Infrastructure ──────────────────────────────────────{RESET}")

check("GET  /v1/health", client.get(f"{BASE}/v1/health"))

# ── Knowledge Base ────────────────────────────────────────────
print(f"{SECTION}── Knowledge Base ──────────────────────────────────────{RESET}")

check("POST /v1/ingest", client.post(f"{BASE}/v1/ingest", json={
    "documents": [
        "Arifgate Course Marketplace offers Python, React, Django, and Data Science courses.",
        "Arifgate Freelancing Marketplace connects clients with skilled freelancers.",
        "Students can enroll in courses, track progress, and earn certificates.",
        "Freelancers can build profiles, showcase portfolios, and apply for jobs.",
        "Clients post job listings, review proposals, and hire the best candidate.",
        "Instructors publish courses and earn revenue from student enrollments.",
        "Platform rule: All payments must go through Arifgate. No off-platform transactions.",
    ],
    "domain": "platform"
}))

# ── Public Chat ───────────────────────────────────────────────
print(f"{SECTION}── Public Chat ─────────────────────────────────────────{RESET}")

r = check("POST /v1/ask", client.post(f"{BASE}/v1/ask", json={
    "message": "What is Arifgate and what can I do here?"
}))
session_id = r.json().get("session_id") if r.status_code == 200 else None

if session_id:
    check("POST /v1/ask  (multi-turn follow-up)", client.post(f"{BASE}/v1/ask", json={
        "message": "How do I sign up as a student?",
        "session_id": session_id
    }))

# ── Role Chat ─────────────────────────────────────────────────
print(f"{SECTION}── Role-Specific Chat ──────────────────────────────────{RESET}")

check("POST /v1/chat/student", client.post(f"{BASE}/v1/chat/student", json={
    "message": "I know basic Python. What should I learn next to become a full-stack developer?"
}))

check("POST /v1/chat/instructor", client.post(f"{BASE}/v1/chat/instructor", json={
    "message": "How should I structure a 10-hour React course for beginners?"
}))

check("POST /v1/chat/client", client.post(f"{BASE}/v1/chat/client", json={
    "message": "I need a developer to build an e-commerce store. What skills should I look for?"
}))

check("POST /v1/chat/freelancer", client.post(f"{BASE}/v1/chat/freelancer", json={
    "message": "How do I write a winning proposal for a Django REST API job?"
}))

check("POST /v1/chat/admin", client.post(f"{BASE}/v1/chat/admin", json={
    "message": "What metrics should I monitor weekly to track platform health?"
}))

check("POST /v1/chat/guest", client.post(f"{BASE}/v1/chat/guest", json={
    "message": "What is the difference between the Course and Freelancing marketplaces?"
}))

check("POST /v1/chat  (generic, role in body)", client.post(f"{BASE}/v1/chat", json={
    "role": "Student",
    "message": "Recommend a beginner course for web development."
}))

# Validation — bad role should return 422
check("POST /v1/chat  (invalid role → 422)", client.post(f"{BASE}/v1/chat", json={
    "role": "Hacker",
    "message": "test"
}), expected_status=422)

# ── Content Generation ────────────────────────────────────────
print(f"{SECTION}── Content Generation ──────────────────────────────────{RESET}")

check("POST /v1/generate/course-description", client.post(f"{BASE}/v1/generate/course-description", json={
    "title": "Python for Data Science",
    "topics": ["pandas", "numpy", "matplotlib", "scikit-learn"],
    "target_audience": "Developers with basic Python knowledge",
    "level": "Beginner"
}))

check("POST /v1/generate/job-description", client.post(f"{BASE}/v1/generate/job-description", json={
    "project_title": "Fashion E-commerce Store",
    "requirements": "Product listings, shopping cart, Stripe payments, admin panel",
    "budget": "$3000",
    "duration": "8 weeks"
}))

check("POST /v1/generate/proposal", client.post(f"{BASE}/v1/generate/proposal", json={
    "job_description": "Build a REST API for a healthcare booking system using Django and PostgreSQL.",
    "freelancer_skills": ["Django", "FastAPI", "PostgreSQL", "Docker"],
    "experience_years": 5,
    "hourly_rate": "$45"
}))

check("POST /v1/generate/skill-tags", client.post(f"{BASE}/v1/generate/skill-tags", json={
    "text": "Backend developer with 5 years in Python, Django, FastAPI, PostgreSQL, Redis, Docker, AWS."
}))

# ── Recommendations & Matching ────────────────────────────────
print(f"{SECTION}── Recommendations & Matching ──────────────────────────{RESET}")

check("POST /v1/ai/recommend", client.post(f"{BASE}/v1/ai/recommend", json={
    "role": "Student",
    "query": "I want to learn web development from scratch",
    "items": [
        "Course: React Fundamentals. Level: Intermediate. Prerequisites: JavaScript.",
        "Course: HTML & CSS Basics. Level: Beginner. Rating: 4.8.",
        "Course: JavaScript for Beginners. Level: Beginner. Rating: 4.7.",
        "Course: Advanced Node.js. Level: Advanced."
    ],
    "top_k": 2
}))

check("POST /v1/ai/match", client.post(f"{BASE}/v1/ai/match", json={
    "job_description": "Build a Django REST API for a fintech startup. Required: Django, PostgreSQL, Celery, Redis.",
    "freelancer_profiles": [
        "Ahmed K. Skills: Django, Celery, Redis, PostgreSQL. 6 years. $55/hr. Rating: 4.9.",
        "Mia T. Skills: Vue.js, Laravel, MySQL. 4 years. $40/hr. Rating: 4.7.",
        "Tariq S. Skills: Django, FastAPI, PostgreSQL, Docker. 5 years. $45/hr. Rating: 4.8."
    ],
    "top_k": 2
}))

# ── Summary ───────────────────────────────────────────────────
client.close()
total = results["pass"] + results["fail"] + results["warn"]
print(f"{SECTION}{'='*62}{RESET}")
print(f"\033[92m  PASS: {results['pass']}/{total}\033[0m")
if results["warn"]:
    print(f"\033[93m  WARN: {results['warn']}/{total}  (OpenAI rate limit — routing is fine)\033[0m")
if results["fail"]:
    print(f"\033[91m  FAIL: {results['fail']}/{total}\033[0m")
print(f"{SECTION}{'='*62}{RESET}\n")

sys.exit(0 if results["fail"] == 0 else 1)
