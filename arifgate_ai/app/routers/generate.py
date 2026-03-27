
from fastapi import APIRouter

from app.schemas import (
    CourseDescriptionRequest, CourseDescriptionResponse,
    JobDescriptionRequest, JobDescriptionResponse,
    ProposalRequest, ProposalResponse,
    SkillTagRequest, SkillTagResponse,
)
from app.services import ai_service

router = APIRouter(prefix="/generate", tags=["Content Generation"])


@router.post("/course-description", response_model=CourseDescriptionResponse,
             summary="Generate a course description (Instructor)")
async def course_description(req: CourseDescriptionRequest) -> CourseDescriptionResponse:
    return await ai_service.generate_course_description(req)


@router.post("/job-description", response_model=JobDescriptionResponse,
             summary="Generate a job posting (Client)")
async def job_description(req: JobDescriptionRequest) -> JobDescriptionResponse:
    return await ai_service.generate_job_description(req)


@router.post("/proposal", response_model=ProposalResponse,
             summary="Generate a freelancer proposal (Freelancer)")
async def proposal(req: ProposalRequest) -> ProposalResponse:
    return await ai_service.generate_proposal(req)


@router.post("/skill-tags", response_model=SkillTagResponse,
             summary="Extract skill tags and keywords from text")
async def skill_tags(req: SkillTagRequest) -> SkillTagResponse:
    return await ai_service.extract_skill_tags(req)
