from enum import Enum
from pydantic import BaseModel


class Role(str, Enum):
    student = "Student"
    instructor = "Instructor"
    freelancer = "Freelancer"
    client = "Client"
    admin = "Admin"
    guest = "Guest"


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
