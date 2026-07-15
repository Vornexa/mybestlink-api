"""Small web control panel for runtime API configuration."""

from __future__ import annotations

import json
from asyncio import to_thread
from collections.abc import Mapping
from pathlib import Path
from time import perf_counter

import aiohttp
from aiohttp import web

from src.app_keys import SESSION_MANAGER_KEY, SETTINGS_KEY
from src.config import Settings, normalize_base_url

VIEW_DIR = Path(__file__).resolve().parents[2] / "view"
UI_METADATA_FILE = VIEW_DIR / "ui.json"


def _ui_metadata() -> dict[str, list[dict[str, str]]]:
    return json.loads(UI_METADATA_FILE.read_text(encoding="utf-8"))


def _connector_base_url(settings: Settings, settings_key: str) -> str:
    if settings_key == "elearning_base_url":
        return settings.elearning_base_url
    if settings_key == "exam_base_url":
        return settings.exam_base_url
    raise ValueError(f"Unknown connector settings key: {settings_key}")


def _snapshot(settings: Settings, cookie_count: int) -> dict[str, object]:
    metadata = _ui_metadata()
    connectors = [
        {
            "id": connector["id"],
            "name": connector["name"],
            "base_url": _connector_base_url(settings, connector["settings_key"]),
            "purpose": connector["purpose"],
        }
        for connector in metadata["connectors"]
    ]
    endpoints = metadata["endpoints"]
    return {
        "status": "ok",
        "config": settings.control_values(),
        "connectors": connectors,
        "runtime": {
            "host": settings.host,
            "port": settings.port,
            "cookie_count": cookie_count,
            "endpoint_count": len(endpoints),
        },
        "endpoints": endpoints,
    }


def _write_config(path: Path, values: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = path.with_suffix(path.suffix + ".tmp")
    temporary_file.write_text(
        json.dumps(values, indent=2, sort_keys=True), encoding="utf-8"
    )
    temporary_file.replace(path)


async def _json_object(request: web.Request) -> Mapping[str, object]:
    if request.content_type != "application/json":
        raise web.HTTPUnsupportedMediaType(
            reason="Content-Type must be application/json"
        )
    body = await request.json()
    if not isinstance(body, Mapping):
        raise web.HTTPBadRequest(reason="Request body must be an object")
    return body


async def get_control_panel(_: web.Request) -> web.FileResponse:
    return web.FileResponse(VIEW_DIR / "index.html")


async def get_data_console(_: web.Request) -> web.FileResponse:
    return web.FileResponse(VIEW_DIR / "data.html")


async def get_control_config(request: web.Request) -> web.Response:
    settings = request.app[SETTINGS_KEY]
    sessions = request.app[SESSION_MANAGER_KEY]
    return web.json_response(_snapshot(settings, len(sessions.cookies())))


async def put_control_config(request: web.Request) -> web.Response:
    settings = request.app[SETTINGS_KEY]
    try:
        values = settings.validate_control_values(dict(await _json_object(request)))
    except ValueError as error:
        raise web.HTTPBadRequest(reason=str(error)) from error

    await to_thread(_write_config, settings.control_config_file, values)
    await request.app[SESSION_MANAGER_KEY].close()
    settings.apply_control_values(values)
    return web.json_response(_snapshot(settings, 0))


async def post_connector_test(request: web.Request) -> web.Response:
    settings = request.app[SETTINGS_KEY]
    body = await _json_object(request)
    connector = body.get("connector")
    connector_settings = {
        item["id"]: item["settings_key"] for item in _ui_metadata()["connectors"]
    }
    if connector not in connector_settings:
        valid_connectors = ", ".join(sorted(connector_settings))
        raise web.HTTPBadRequest(reason=f"connector must be one of: {valid_connectors}")

    configured_url = _connector_base_url(
        settings, connector_settings[str(connector)]
    )
    try:
        url = normalize_base_url("url", body.get("url", configured_url))
    except ValueError as error:
        raise web.HTTPBadRequest(reason=str(error)) from error

    started_at = perf_counter()
    timeout = aiohttp.ClientTimeout(total=min(settings.request_timeout_seconds, 10))
    try:
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.get(
                url,
                allow_redirects=False,
                ssl=settings.verify_ssl,
            ) as response,
        ):
            http_status = response.status
        reachable = http_status < 500
        message = "Connector reachable" if reachable else "Upstream server error"
    except (aiohttp.ClientError, TimeoutError) as error:
        reachable = False
        http_status = None
        message = f"Connection failed: {type(error).__name__}"

    return web.json_response(
        {
            "status": "ok",
            "connector": connector,
            "reachable": reachable,
            "http_status": http_status,
            "latency_ms": round((perf_counter() - started_at) * 1000),
            "message": message,
        }
    )
