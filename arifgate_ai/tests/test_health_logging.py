import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("AI_SERVICE_SECRET", "test-secret")
os.environ.setdefault("OPENAI_MODEL", "gpt-4o")


@pytest.fixture
def app_with_error_route():
    """Return a TestClient for an app that includes the error test route."""
    from app.main import app
    from app.middleware.logging import LoggingMiddleware
    from fastapi.routing import APIRouter

    # Add a test-only error route
    test_router = APIRouter()

    @test_router.get("/test-error")
    async def trigger_error():
        raise RuntimeError("boom")

    app.include_router(test_router, prefix="/v1")
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_health_returns_200_ok(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unhandled_exception_returns_500_no_stack_trace(app_with_error_route):
    response = app_with_error_route.get("/v1/test-error")
    assert response.status_code == 500
    body = response.json()
    assert body == {"detail": "Internal server error"}
    # Ensure no stack trace leaks into the response body
    assert "Traceback" not in response.text
    assert "RuntimeError" not in response.text
