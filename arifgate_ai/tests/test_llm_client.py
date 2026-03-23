import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
import openai


def _make_mock_client(side_effect):
    """Build a mock AsyncOpenAI client whose completions.create raises side_effect."""
    mock_create = AsyncMock(side_effect=side_effect)
    mock_client = MagicMock()
    mock_client.chat.completions.create = mock_create
    return mock_client


@pytest.mark.asyncio
async def test_complete_raises_502_on_api_error():
    mock_client = _make_mock_client(
        openai.APIError("API error", request=None, body=None)
    )
    with patch("app.services.llm_client._get_client", return_value=mock_client):
        from app.services.llm_client import complete
        with pytest.raises(HTTPException) as exc_info:
            await complete([{"role": "user", "content": "hello"}])
        assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_complete_raises_504_on_timeout():
    mock_client = _make_mock_client(openai.APITimeoutError(request=None))
    with patch("app.services.llm_client._get_client", return_value=mock_client):
        from app.services.llm_client import complete
        with pytest.raises(HTTPException) as exc_info:
            await complete([{"role": "user", "content": "hello"}])
        assert exc_info.value.status_code == 504


@pytest.mark.asyncio
async def test_complete_raises_429_on_rate_limit():
    mock_client = _make_mock_client(
        openai.RateLimitError("rate limit", response=MagicMock(status_code=429), body=None)
    )
    with patch("app.services.llm_client._get_client", return_value=mock_client):
        from app.services.llm_client import complete
        with pytest.raises(HTTPException) as exc_info:
            await complete([{"role": "user", "content": "hello"}])
        assert exc_info.value.status_code == 429
