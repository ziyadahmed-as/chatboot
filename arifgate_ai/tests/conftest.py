import os
import pytest
from fastapi.testclient import TestClient

# Set required env vars before importing app
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("AI_SERVICE_SECRET", "test-secret")
os.environ.setdefault("OPENAI_MODEL", "gpt-4o")


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-secret"}
