"""
Document ingestion endpoint.
Feeds text documents into the ChromaDB vector store for RAG retrieval.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.services import rag_service

router = APIRouter(tags=["Knowledge Base"])


class IngestRequest(BaseModel):
    documents: list[str]
    domain: str | None = None  # e.g. "courses", "freelancing", "platform"


class IngestResponse(BaseModel):
    ingested: int
    domain: str


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest documents into the RAG vector store",
)
async def ingest(req: IngestRequest) -> IngestResponse:
    """
    Add documents to the ChromaDB vector store.
    These will be automatically retrieved and injected as context
    in all subsequent chat requests.

    Use this to load:
    - Course catalog entries
    - Freelancer profiles
    - Job listings
    - Platform rules and FAQs
    """
    count = rag_service.ingest(req.documents, req.domain)
    return IngestResponse(ingested=count, domain=req.domain or "general")
