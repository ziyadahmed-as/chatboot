from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-secret"}


def test_ingest_valid_payload_returns_200_with_count(client, auth_headers):
    mock_store = MagicMock()
    with patch("app.routers.ingest.get_vector_store", return_value=mock_store):
        response = client.post(
            "/v1/ingest",
            json={"documents": ["doc one", "doc two", "doc three"], "domain": "education"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert response.json()["ingested"] == 3
    mock_store.add.assert_called_once_with(["doc one", "doc two", "doc three"], "education")


def test_ingest_no_domain_returns_correct_count(client, auth_headers):
    mock_store = MagicMock()
    with patch("app.routers.ingest.get_vector_store", return_value=mock_store):
        response = client.post(
            "/v1/ingest",
            json={"documents": ["only doc"]},
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert response.json()["ingested"] == 1
    mock_store.add.assert_called_once_with(["only doc"], None)


def test_ingest_missing_auth_returns_401(client):
    response = client.post(
        "/v1/ingest",
        json={"documents": ["doc"]},
    )
    assert response.status_code == 401
