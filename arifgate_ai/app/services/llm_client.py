import asyncio
import os

import httpx
import openai
from fastapi import HTTPException
from openai import AsyncOpenAI

_api_key = os.environ.get("OPENAI_API_KEY")
if not _api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is required")

_model = os.environ.get("OPENAI_MODEL", "gpt-4o")

_client = AsyncOpenAI(
    api_key=_api_key,
    timeout=httpx.Timeout(30.0),
)


async def complete(messages: list[dict]) -> str:
    try:
        response = await asyncio.wait_for(
            _client.chat.completions.create(
                model=_model,
                messages=messages,
            ),
            timeout=30.0,
        )
        return response.choices[0].message.content
    except (asyncio.TimeoutError, httpx.TimeoutException):
        raise HTTPException(status_code=504, detail="LLM timeout")
    except openai.APIError:
        raise HTTPException(status_code=502, detail="LLM error")
