import uuid
from datetime import datetime, timedelta

from app.models import Message, Session

_store: dict[str, Session] = {}
_SESSION_TTL_MINUTES = 60
_CONTEXT_WINDOW = 20


class SessionStore:
    def get(self, session_id: str) -> Session | None:
        return _store.get(session_id)

    def create(self, role: str) -> Session:
        session = Session(session_id=str(uuid.uuid4()), role=role)
        _store[session.session_id] = session
        return session

    def save(self, session: Session) -> None:
        session.last_active = datetime.utcnow()
        _store[session.session_id] = session

    def expire_stale(self) -> None:
        cutoff = datetime.utcnow() - timedelta(minutes=_SESSION_TTL_MINUTES)
        stale = [sid for sid, s in _store.items() if s.last_active <= cutoff]
        for sid in stale:
            del _store[sid]

    def get_context(self, session: Session) -> list[dict]:
        recent = session.history[-_CONTEXT_WINDOW:]
        return [{"role": m.role, "content": m.content} for m in recent]
