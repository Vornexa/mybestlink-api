"""Dashboard endpoint."""

from aiohttp import web

from src.app_keys import UPSTREAM_CLIENT_KEY
from src.parser.mybestlink_parser import parse_dashboard


async def get_dashboard(request: web.Request) -> web.Response:
    response = await request.app[UPSTREAM_CLIENT_KEY].elearning(
        "GET", "/dashboard", expected_statuses={200}
    )
    return web.json_response(parse_dashboard(response.text))
