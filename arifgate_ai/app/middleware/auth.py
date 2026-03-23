import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

PROTECTED_PREFIXES = ("/v1/chat", "/v1/ingest")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
            secret = os.environ.get("AI_SERVICE_SECRET", "")
            auth_header = request.headers.get("Authorization", "")

            if not auth_header.startswith("Bearer ") or auth_header[7:] != secret:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized"},
                )

        return await call_next(request)
