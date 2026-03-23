import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
import openai


@pytest.mark.asyncio
async def test_complete_raises_502_on_api_error():
    """Validates: Requirements 4.3 - openai.APIError maps to 502 Bad Gateway"""
    with patch("app.services.llm_client._client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = openai.APIError("API error", request=None, body=None)

        from app.services.llm_client import complete

        with pytest.raises(HTTPException) as exc_info:
            await complete([{"role": "user", "content": "hello"}])

        assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_complete_raises_504_on_timeout():
    """Validates: Requirements 4.4 - asyncio.TimeoutError maps to 504 Gateway Timeout"""
    import asyncio

    with patch("app.services.llm_client._client.chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = asyncio.TimeoutError()

        from app.services.llm_client import complete

        with pytest.raises(HTTPException) as exc_info:
            await complete([{"role": "user", "content": "hello"}])

        assert exc_info.value.status_code == 504
