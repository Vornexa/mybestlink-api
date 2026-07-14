"""Application factory and development entry point."""

from __future__ import annotations

import logging
import socket

from aiohttp import web

from src.app_keys import SESSION_MANAGER_KEY, SETTINGS_KEY, UPSTREAM_CLIENT_KEY
from src.config import Settings
from src.middleware.base_middleware import base_middleware
from src.router.route import setup_routes
from src.service.upstream_client import SessionManager, UpstreamClient


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.connect(("8.8.8.8", 80))
            return connection.getsockname()[0]
    except OSError:
        return "localhost"


async def _close_resources(app: web.Application) -> None:
    await app[SESSION_MANAGER_KEY].close()


def create_app(settings: Settings | None = None) -> web.Application:
    settings = settings or Settings.from_env()
    sessions = SessionManager(settings)

    app = web.Application(middlewares=[base_middleware])
    app[SETTINGS_KEY] = settings
    app[SESSION_MANAGER_KEY] = sessions
    app[UPSTREAM_CLIENT_KEY] = UpstreamClient(settings, sessions)
    app.on_cleanup.append(_close_resources)
    setup_routes(app)
    return app


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    runtime_settings = Settings.from_env()
    local_ip = get_local_ip()
    print("\nAPI running")
    print(f"Local:   http://127.0.0.1:{runtime_settings.port}/")
    print(f"Network: http://{local_ip}:{runtime_settings.port}/\n")
    web.run_app(
        create_app(runtime_settings),
        host=runtime_settings.host,
        port=runtime_settings.port,
    )