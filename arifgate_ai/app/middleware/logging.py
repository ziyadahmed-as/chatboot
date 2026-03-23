import json
import logging
import time
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("arifgate_ai")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        role = None
        session_id = None

        # Try to extract role/session_id from request body (JSON only)
        try:
            body = await request.body()
            if body:
                import json as _json
                data = _json.loads(body)
                role = data.get("role")
                session_id = data.get("session_id")
        except Exception:
            pass

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            logger.error("Unhandled exception", exc_info=True)
            latency_ms = int((time.monotonic() - start) * 1000)
            _emit_log(request, role, session_id, latency_ms, 500)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

        latency_ms = int((time.monotonic() - start) * 1000)
        _emit_log(request, role, session_id, latency_ms, status_code)
        return response


def _emit_log(request: Request, role, session_id, latency_ms: int, status_code: int):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "session_id": session_id,
        "latency_ms": latency_ms,
        "status_code": status_code,
    }
    logger.info(json.dumps(record))
