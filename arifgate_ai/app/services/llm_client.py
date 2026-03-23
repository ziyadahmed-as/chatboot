import os

import httpx
import openai
from fastapi import HTTPException
from openai import AsyncOpenAI

# Client is initialised lazily so that load_dotenv() in main.py runs first.
_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        _client = AsyncOpenAI(
            api_key=api_key,
            timeout=httpx.Timeout(30.0),
        )
    return _client


async def complete(messages: list[dict]) -> str:
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    try:
        response = await _get_client().chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content
    except openai.APITimeoutError:
        raise HTTPException(status_code=504, detail="LLM timeout")
    except openai.APIConnectionError:
        raise HTTPException(status_code=502, detail="LLM connection error")
    except openai.AuthenticationError:
        raise HTTPException(status_code=502, detail="LLM authentication failed — check OPENAI_API_KEY")
    except openai.RateLimitError:
        raise HTTPException(status_code=429, detail="OpenAI rate limit exceeded")
    except openai.APIError as exc:
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}")
