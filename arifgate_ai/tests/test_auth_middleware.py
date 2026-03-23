import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app, raise_server_exceptions=False)


# --- /v1/chat protection ---

def test_chat_missing_auth_returns_401(client):
    response = client.post("/v1/chat", json={})
    assert response.status_code == 401


def test_chat_wrong_token_returns_401(client):
    response = client.post("/v1/chat", json={}, headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401


def test_chat_valid_token_passes_auth(client):
    # Route doesn't exist yet, but auth should pass (not 401)
    response = client.post("/v1/chat", json={}, headers={"Authorization": "Bearer test-secret"})
    assert response.status_code != 401


# --- /v1/ingest protection ---

def test_ingest_missing_auth_returns_401(client):
    response = client.post("/v1/ingest", json={})
    assert response.status_code == 401


def test_ingest_wrong_token_returns_401(client):
    response = client.post("/v1/ingest", json={}, headers={"Authorization": "Bearer bad-token"})
    assert response.status_code == 401


def test_ingest_valid_token_passes_auth(client):
    response = client.post("/v1/ingest", json={}, headers={"Authorization": "Bearer test-secret"})
    assert response.status_code != 401


# --- Unprotected paths ---

def test_health_no_auth_required(client):
    response = client.get("/v1/health")
    assert response.status_code != 401


def test_root_no_auth_required(client):
    response = client.get("/")
    assert response.status_code == 200
