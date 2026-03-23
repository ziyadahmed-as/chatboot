from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str


@dataclass
class Session:
    session_id: str
    role: str
    history: list[Message] = field(default_factory=list)
    last_active: datetime = field(default_factory=datetime.utcnow)
