"""Typed keys used by the aiohttp application container."""

from aiohttp import web

from src.config import Settings
from src.service.upstream_client import SessionManager, UpstreamClient

SETTINGS_KEY = web.AppKey("settings", Settings)
SESSION_MANAGER_KEY = web.AppKey("session_manager", SessionManager)
UPSTREAM_CLIENT_KEY = web.AppKey("upstream_client", UpstreamClient)
