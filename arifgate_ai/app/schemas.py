from enum import Enum
from pydantic import BaseModel


class Role(str, Enum):
    student = "Student"
    instructor = "Instructor"
    freelancer = "Freelancer"
    client = "Client"
    admin = "Admin"
    guest = "Guest"


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class Recommendation(BaseModel):
    title: str
    description: str
    link: str = ""


class Match(BaseModel):
    name: str
    skills: str
    match_score: str
    link: str = ""


class ChatRequest(BaseModel):
    role: Role
    message: str
    session_id: str | None = None
    context_data: list[str] | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    role: Role
    recommendations: list[Recommendation] = []
    matches: list[Match] = []


# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------

class CourseDescriptionRequest(BaseModel):
    title: str
    topics: list[str]
    target_audience: str
    level: str = "Beginner"  # Beginner / Intermediate / Advanced


class CourseDescriptionResponse(BaseModel):
    title: str
    description: str
    highlights: list[str]


class JobDescriptionRequest(BaseModel):
    project_title: str
    requirements: str
    budget: str = ""
    duration: str = ""


class JobDescriptionResponse(BaseModel):
    title: str
    description: str
    required_skills: list[str]
    suggested_budget: str
    suggested_duration: str


class ProposalRequest(BaseModel):
    job_description: str
    freelancer_skills: list[str]
    experience_years: int
    hourly_rate: str = ""


class ProposalResponse(BaseModel):
    proposal: str
    key_selling_points: list[str]


class SkillTagRequest(BaseModel):
    text: str  # profile bio or job description


class SkillTagResponse(BaseModel):
    skills: list[str]
    keywords: list[str]


# ---------------------------------------------------------------------------
# Recommendations & Matching
# ---------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    role: Role
    query: str
    items: list[str]  # list of course/job/profile descriptions to rank
    top_k: int = 3


class RecommendResponse(BaseModel):
    recommendations: list[Recommendation]


class MatchRequest(BaseModel):
    job_description: str
    freelancer_profiles: list[str]  # list of freelancer profile descriptions
    top_k: int = 3


class MatchResponse(BaseModel):
    matches: list[Match]
