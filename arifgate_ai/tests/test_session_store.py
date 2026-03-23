import time
from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.models import Message, Session
from app.services.session_store import SessionStore, _store


@pytest.fixture(autouse=True)
def clear_store():
    _store.clear()
    yield
    _store.clear()


@pytest.fixture
def store():
    return SessionStore()


def test_create_returns_session_with_uuid(store):
    session = store.create("Student")
    assert session.session_id
    assert len(session.session_id) == 36  # UUID format
    assert session.role == "Student"
    assert session.history == []


def test_create_stores_session(store):
    session = store.create("Instructor")
    assert store.get(session.session_id) is session


def test_get_returns_none_for_unknown_id(store):
    assert store.get("nonexistent-id") is None


def test_get_returns_existing_session(store):
    session = store.create("Freelancer")
    result = store.get(session.session_id)
    assert result is session


def test_save_updates_last_active(store):
    session = store.create("Student")
    old_time = session.last_active
    time.sleep(0.01)
    store.save(session)
    assert session.last_active > old_time


def test_save_persists_session(store):
    session = store.create("Student")
    session.history.append(Message(role="user", content="hello"))
    store.save(session)
    retrieved = store.get(session.session_id)
    assert len(retrieved.history) == 1


def test_expire_stale_removes_old_sessions(store):
    session = store.create("Student")
    session.last_active = datetime.utcnow() - timedelta(minutes=61)
    _store[session.session_id] = session
    store.expire_stale()
    assert store.get(session.session_id) is None


def test_expire_stale_keeps_recent_sessions(store):
    session = store.create("Student")
    store.expire_stale()
    assert store.get(session.session_id) is not None


def test_expire_stale_boundary_exactly_60_minutes(store):
    session = store.create("Student")
    session.last_active = datetime.utcnow() - timedelta(minutes=60)
    _store[session.session_id] = session
    store.expire_stale()
    # exactly 60 min ago should be evicted (last_active <= cutoff)
    assert store.get(session.session_id) is None


def test_get_context_returns_openai_format(store):
    session = store.create("Student")
    session.history.append(Message(role="user", content="hi"))
    session.history.append(Message(role="assistant", content="hello"))
    ctx = store.get_context(session)
    assert ctx == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


def test_get_context_returns_last_20_messages(store):
    session = store.create("Student")
    for i in range(25):
        session.history.append(Message(role="user", content=str(i)))
    ctx = store.get_context(session)
    assert len(ctx) == 20
    assert ctx[0]["content"] == "5"
    assert ctx[-1]["content"] == "24"


def test_get_context_empty_history(store):
    session = store.create("Student")
    assert store.get_context(session) == []


# Property: Any session last active more than 60 minutes ago is evicted after expire_stale() is called
# Validates: Requirements 3.5
@given(st.integers(min_value=61, max_value=10000))
@settings(max_examples=100)
def test_property_expire_stale_evicts_sessions_older_than_60_minutes(minutes_ago):
    _store.clear()
    store = SessionStore()
    session = store.create("Student")
    session.last_active = datetime.utcnow() - timedelta(minutes=minutes_ago)
    _store[session.session_id] = session
    store.expire_stale()
    assert store.get(session.session_id) is None
    _store.clear()
