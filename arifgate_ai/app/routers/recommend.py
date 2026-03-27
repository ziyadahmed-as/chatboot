
from fastapi import APIRouter

from app.schemas import (
    RecommendRequest, RecommendResponse,
    MatchRequest, MatchResponse,
)
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["Recommendations & Matching"])


@router.post("/recommend", response_model=RecommendResponse,
             summary="Smart recommendations — courses, jobs, or candidates")
async def recommend(req: RecommendRequest) -> RecommendResponse:
    return await ai_service.get_recommendations(req)


@router.post("/match", response_model=MatchResponse,
             summary="Match freelancers to a job description")
async def match(req: MatchRequest) -> MatchResponse:
    return await ai_service.match_freelancers(req)
