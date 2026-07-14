"""HTTP logging and JSON error handling middleware."""

from __future__ import annotations

import json
import logging
from time import perf_counter

from aiohttp import web

from src.exceptions import UpstreamError

logger = logging.getLogger(__name__)


@web.middleware
async def base_middleware(
    request: web.Request, handler: web.RequestHandler
) -> web.StreamResponse:
    started_at = perf_counter()
    try:
        response = await handler(request)
    except web.HTTPException as error:
        response = web.json_response(
            {"status": "error", "message": error.reason},
            status=error.status,
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        response = web.json_response(
            {"status": "error", "message": "Request body must be valid JSON"},
            status=400,
        )
    except UpstreamError as error:
        logger.warning("Upstream failure for %s: %s", request.path, error)
        response = web.json_response(
            {"status": "error", "message": str(error)}, status=502
        )
    except Exception:
        logger.exception("Unhandled error for %s", request.path)
        response = web.json_response(
            {"status": "error", "message": "Internal server error"},
            status=500,
        )

    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.path,
        response.status,
        (perf_counter() - started_at) * 1000,
    )
    return response