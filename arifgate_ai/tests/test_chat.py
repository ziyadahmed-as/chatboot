import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-secret"}


@pytest.fixture(autouse=True)
def mock_llm():
    with patch("app.routers.chat.llm_client.complete", new_callable=AsyncMock) as m:
        m.return_value = "mocked reply"
        yield m


def test_valid_request_returns_200(client, auth_headers):
    resp = client.post(
        "/v1/chat",
        json={"role": "Student", "message": "Hello"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["reply"] == "mocked reply"
    assert "session_id" in data
    assert data["role"] == "Student"


def test_invalid_role_returns_422(client, auth_headers):
    resp = client.post(
        "/v1/chat",
        json={"role": "InvalidRole", "message": "Hello"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_missing_auth_returns_401(client):
    resp = client.post(
        "/v1/chat",
        json={"role": "Student", "message": "Hello"},
    )
    assert resp.status_code == 401


def test_no_session_id_generates_new_session(client, auth_headers):
    resp = client.post(
        "/v1/chat",
        json={"role": "Student", "message": "Hello"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] is not None
    assert len(data["session_id"]) > 0


def test_same_session_id_reuses_history(client, auth_headers):
    # First request — creates a session
    resp1 = client.post(
        "/v1/chat",
        json={"role": "Student", "message": "First message"},
        headers=auth_headers,
    )
    assert resp1.status_code == 200
    session_id = resp1.json()["session_id"]

    # Second request — reuses the same session
    with patch("app.routers.chat.llm_client.complete", new_callable=AsyncMock) as m2:
        m2.return_value = "second reply"
        resp2 = client.post(
            "/v1/chat",
            json={"role": "Student", "message": "Second message", "session_id": session_id},
            headers=auth_headers,
        )
    assert resp2.status_code == 200
    assert resp2.json()["session_id"] == session_id

    # Verify history grew: session should have 4 messages (2 per turn)
    from app.routers.chat import session_store
    session = session_store.get(session_id)
    assert session is not None
    assert len(session.history) == 4
