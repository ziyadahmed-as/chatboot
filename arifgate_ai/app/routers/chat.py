from fastapi import APIRouter
from pydantic import BaseModel

from app.models import Message
from app.schemas import ChatRequest, ChatResponse, Role
from app.services import llm_client
from app.services.prompt_builder import get_system_prompt
from app.services.session_store import SessionStore

router = APIRouter()
session_store = SessionStore()


class RoleMessageRequest(BaseModel):
    message: str
    session_id: str | None = None
    context_data: list[str] | None = None


async def _handle_chat(role: Role, req: RoleMessageRequest) -> ChatResponse:
    session_store.expire_stale()

    session = session_store.get(req.session_id) if req.session_id else None
    if session is None:
        session = session_store.create(role=role.value)

    messages: list[dict] = [
        {"role": "system", "content": get_system_prompt(role)},
        *session_store.get_context(session),
    ]

    if req.context_data:
        messages.append({
            "role": "system",
            "content": "Relevant context:\n" + "\n".join(req.context_data),
        })

    messages.append({"role": "user", "content": req.message})

    reply = await llm_client.complete(messages)

    session.history.append(Message(role="user", content=req.message))
    session.history.append(Message(role="assistant", content=reply))
    session_store.save(session)

    return ChatResponse(reply=reply, session_id=session.session_id, role=role)


# Generic endpoint — role passed in body
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await _handle_chat(
        request.role,
        RoleMessageRequest(
            message=request.message,
            session_id=request.session_id,
            context_data=request.context_data,
        ),
    )


# Role-specific endpoints
@router.post("/chat/student", response_model=ChatResponse)
async def chat_student(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.student, req)


@router.post("/chat/instructor", response_model=ChatResponse)
async def chat_instructor(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.instructor, req)


@router.post("/chat/client", response_model=ChatResponse)
async def chat_client(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.client, req)


@router.post("/chat/freelancer", response_model=ChatResponse)
async def chat_freelancer(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.freelancer, req)


@router.post("/chat/admin", response_model=ChatResponse)
async def chat_admin(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.admin, req)


@router.post("/chat/guest", response_model=ChatResponse)
async def chat_guest(req: RoleMessageRequest) -> ChatResponse:
    return await _handle_chat(Role.guest, req)
