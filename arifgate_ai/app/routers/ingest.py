from fastapi import APIRouter
from app.schemas import IngestRequest, IngestResponse
from app.services.vector_store import get_vector_store

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest) -> IngestResponse:
    store = get_vector_store()
    store.add(request.documents, request.domain)
    return IngestResponse(ingested=len(request.documents))
