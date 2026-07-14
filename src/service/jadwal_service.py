"""Lecture schedule endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from aiohttp import web

from src.app_keys import UPSTREAM_CLIENT_KEY
from src.parser.mybestlink_parser import (
    parse_class_schedule,
    parse_replacement_schedule,
)


def _schedule_response(schedule: list[dict[str, object]]) -> web.Response:
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return web.json_response(
        {
            "status": "success",
            "data": {"jadwal": schedule},
            "meta": {"total": len(schedule), "timestamp": timestamp},
        }
    )


async def get_jadwal_kuliah(request: web.Request) -> web.Response:
    response = await request.app[UPSTREAM_CLIENT_KEY].elearning(
        "GET", "/sch", expected_statuses={200}
    )
    return _schedule_response(parse_class_schedule(response.text))


async def get_jadwal_pengganti(request: web.Request) -> web.Response:
    response = await request.app[UPSTREAM_CLIENT_KEY].elearning(
        "GET", "/kuliah-pengganti", expected_statuses={200}
    )
    return _schedule_response(parse_replacement_schedule(response.text))
