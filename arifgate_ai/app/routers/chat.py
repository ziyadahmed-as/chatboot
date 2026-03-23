from fastapi import APIRouter
from app.schemas import ChatRequest, ChatResponse, Role
from app.services.session_store import SessionStore
from app.services.prompt_builder import get_system_prompt
from app.services import rag_engine, llm_client
from app.models import Message
from pydantic import BaseModel

router = APIRouter()
session_store = SessionStore()


# ---------------------------------------------------------------------------
# Role-specific request schemas (role is implicit — no need to pass it)
# ---------------------------------------------------------------------------

class RoleMessageRequest(BaseModel):
    message: str
    session_id: str | None = None
    context_data: list[str] | None = None
    context: dict | None = None
    use_rag: bool = False


# ---------------------------------------------------------------------------
# Shared handler
# ---------------------------------------------------------------------------

async def _handle_chat(role: Role, req: RoleMessageRequest) -> ChatResponse:
    session_store.expire_stale()

    session = None
    if req.session_id:
        session = session_store.get(req.session_id)
    if session is None:
        session = session_store.create(role=role.value)

    system_prompt = get_system_prompt(role)
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages.extend(session_store.get_context(session))

    if req.context_data:
        messages.append({
            "role": "system",
            "content": f"Relevant context:\n{chr(10).join(req.context_data)}",
        })
    elif req.use_rag:
        docs = await rag_engine.retrieve(req.message)
        if docs:
            messages.append({
                "role": "system",
                "content": f"Relevant context:\n{chr(10).join(docs)}",
            })

    messages.append({"role": "user", "content": req.message})

    reply = await llm_client.complete(messages)

    session.history.append(Message(role="user", content=req.message))
    session.history.append(Message(role="assistant", content=reply))
    session_store.save(session)

    return ChatResponse(
        reply=reply,
        session_id=session.session_id,
        role=role,
        recommendations=[],
        matches=[],
    )


# ---------------------------------------------------------------------------
# Generic endpoint (role passed in body — kept for backward compatibility)
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse, summary="Generic chat (role in body)")
async def chat(request: ChatRequest) -> ChatResponse:
    return await _handle_chat(request.role, RoleMessageRequest(
        message=request.message,
        session_id=request.session_id,
        context_data=request.context_data,
        context=request.context,
        use_rag=request.use_rag,
    ))


# ---------------------------------------------------------------------------
# Role-specific endpoints
# ---------------------------------------------------------------------------

@router.post("/chat/student", response_model=ChatResponse, summary="Student — course help & guidance")
async def chat_student(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.student, req)


@router.post("/chat/instructor", response_model=ChatResponse, summary="Instructor — course creation & content")
async def chat_instructor(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.instructor, req)


@router.post("/chat/client", response_model=ChatResponse, summary="Client — job descriptions & candidate recommendations")
async def chat_client(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.client, req)


@router.post("/chat/freelancer", response_model=ChatResponse, summary="Freelancer — proposals, skill tags & job recommendations")
async def chat_freelancer(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.freelancer, req)


@router.post("/chat/admin", response_model=ChatResponse, summary="Admin — platform oversight & moderation")
async def chat_admin(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.admin, req)


@router.post("/chat/guest", response_model=ChatResponse, summary="Guest — general platform info & sign-up guidance")
async def chat_guest(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.guest, req)
