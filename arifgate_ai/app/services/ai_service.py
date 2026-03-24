"""
Structured AI tasks: content generation, recommendations, and matching.
All calls go through llm_client.complete() → OpenAI chat completions.
"""
import json
import re

from app.schemas import (
    CourseDescriptionRequest, CourseDescriptionResponse,
    JobDescriptionRequest, JobDescriptionResponse,
    ProposalRequest, ProposalResponse,
    SkillTagRequest, SkillTagResponse,
    RecommendRequest, RecommendResponse, Recommendation,
    MatchRequest, MatchResponse, Match,
)
from app.services import llm_client


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from a string (handles markdown code fences)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in LLM response: {text[:200]}")
    return json.loads(match.group())


# ---------------------------------------------------------------------------
# Course description generator
# ---------------------------------------------------------------------------

async def generate_course_description(req: CourseDescriptionRequest) -> CourseDescriptionResponse:
    prompt = f"""Generate a course description for the following course.
Return ONLY a JSON object with keys: "description" (string), "highlights" (list of 3-5 strings).

Course title: {req.title}
Topics covered: {", ".join(req.topics)}
Target audience: {req.target_audience}
Level: {req.level}"""

    messages = [
        {"role": "system", "content": "You are an expert course content writer for an online learning platform."},
        {"role": "user", "content": prompt},
    ]
    raw = await llm_client.complete(messages)
    data = _extract_json(raw)
    return CourseDescriptionResponse(
        title=req.title,
        description=data.get("description", ""),
        highlights=data.get("highlights", []),
    )


# ---------------------------------------------------------------------------
# Job description generator
# ---------------------------------------------------------------------------

async def generate_job_description(req: JobDescriptionRequest) -> JobDescriptionResponse:
    prompt = f"""Generate a professional job posting for a freelancing platform.
Return ONLY a JSON object with keys:
- "description" (string)
- "required_skills" (list of strings)
- "suggested_budget" (string, e.g. "$1500 - $3000")
- "suggested_duration" (string, e.g. "4-6 weeks")

Project title: {req.project_title}
Requirements: {req.requirements}
Client budget hint: {req.budget or "not specified"}
Duration hint: {req.duration or "not specified"}"""

    messages = [
        {"role": "system", "content": "You are an expert at writing clear, attractive job postings for freelancing platforms."},
        {"role": "user", "content": prompt},
    ]
    raw = await llm_client.complete(messages)
    data = _extract_json(raw)
    return JobDescriptionResponse(
        title=req.project_title,
        description=data.get("description", ""),
        required_skills=data.get("required_skills", []),
        suggested_budget=data.get("suggested_budget", req.budget),
        suggested_duration=data.get("suggested_duration", req.duration),
    )


# ---------------------------------------------------------------------------
# Proposal generator
# ---------------------------------------------------------------------------

async def generate_proposal(req: ProposalRequest) -> ProposalResponse:
    prompt = f"""Write a compelling freelancer proposal for the following job.
Return ONLY a JSON object with keys:
- "proposal" (string, the full proposal text)
- "key_selling_points" (list of 3-5 short strings)

Job description: {req.job_description}
Freelancer skills: {", ".join(req.freelancer_skills)}
Years of experience: {req.experience_years}
Hourly rate: {req.hourly_rate or "not specified"}"""

    messages = [
        {"role": "system", "content": "You are an expert freelance proposal writer who helps freelancers win jobs."},
        {"role": "user", "content": prompt},
    ]
    raw = await llm_client.complete(messages)
    data = _extract_json(raw)
    return ProposalResponse(
        proposal=data.get("proposal", ""),
        key_selling_points=data.get("key_selling_points", []),
    )


# ---------------------------------------------------------------------------
# Skill & keyword tagger
# ---------------------------------------------------------------------------

async def extract_skill_tags(req: SkillTagRequest) -> SkillTagResponse:
    prompt = f"""Extract skills and keywords from the following text.
Return ONLY a JSON object with keys:
- "skills" (list of specific technical/professional skills)
- "keywords" (list of general keywords useful for search/matching)

Text: {req.text}"""

    messages = [
        {"role": "system", "content": "You are an expert at extracting skills and keywords from professional profiles and job descriptions."},
        {"role": "user", "content": prompt},
    ]
    raw = await llm_client.complete(messages)
    data = _extract_json(raw)
    return SkillTagResponse(
        skills=data.get("skills", []),
        keywords=data.get("keywords", []),
    )


# ---------------------------------------------------------------------------
# Smart recommendations
# ---------------------------------------------------------------------------

async def get_recommendations(req: RecommendRequest) -> RecommendResponse:
    items_text = "\n".join(f"{i+1}. {item}" for i, item in enumerate(req.items))
    prompt = f"""A {req.role.value} is looking for: "{req.query}"

Here are the available items:
{items_text}

Return ONLY a JSON object with key "recommendations" — a list of up to {req.top_k} objects, each with:
- "title" (string)
- "description" (string, 1-2 sentences explaining why it matches)
- "link" (empty string)

Rank by relevance to the user's query."""

    messages = [
        {"role": "system", "content": "You are a smart recommendation engine for an online platform."},
        {"role": "user", "content": prompt},
    ]
    raw = await llm_client.complete(messages)
    data = _extract_json(raw)
    recs = [
        Recommendation(
            title=r.get("title", ""),
            description=r.get("description", ""),
            link=r.get("link", ""),
        )
        for r in data.get("recommendations", [])
    ]
    return RecommendResponse(recommendations=recs)


# ---------------------------------------------------------------------------
# Job–Freelancer matching
# ---------------------------------------------------------------------------

async def match_freelancers(req: MatchRequest) -> MatchResponse:
    profiles_text = "\n".join(f"{i+1}. {p}" for i, p in enumerate(req.freelancer_profiles))
    prompt = f"""Match the following job with the best freelancer profiles.

Job description: {req.job_description}

Freelancer profiles:
{profiles_text}

Return ONLY a JSON object with key "matches" — a list of up to {req.top_k} objects, each with:
- "name" (string, freelancer name or identifier from the profile)
- "skills" (string, comma-separated relevant skills)
- "match_score" (string, e.g. "92%")
- "link" (empty string)

Rank by best fit for the job."""

    messages = [
        {"role": "system", "content": "You are an AI matching engine that pairs freelancers with jobs based on skills and experience."},
        {"role": "user", "content": prompt},
    ]
    raw = await llm_client.complete(messages)
    data = _extract_json(raw)
    matches = [
        Match(
            name=m.get("name", ""),
            skills=m.get("skills", ""),
            match_score=m.get("match_score", ""),
            link=m.get("link", ""),
        )
        for m in data.get("matches", [])
    ]
    return MatchResponse(matches=matches)
