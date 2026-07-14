"""Login use case and HTTP handler."""

from __future__ import annotations

import re
from collections.abc import Mapping

from aiohttp import web
from bs4 import BeautifulSoup

from src.app_keys import UPSTREAM_CLIENT_KEY
from src.exceptions import UpstreamError
from src.service.upstream_client import UpstreamClient


def solve_captcha(text: str) -> int | None:
    """Solve the addition/subtraction captcha used by the login page."""

    match = re.search(r"(\d+)\s*([+-])\s*(\d+)", text)
    if not match:
        return None
    first, operator, second = match.groups()
    left, right = int(first), int(second)
    return left + right if operator == "+" else left - right


async def get_login_page(client: UpstreamClient) -> tuple[str, int]:
    client.sessions.clear_cookies()
    response = await client.elearning(
        "GET", "/login", expected_statuses={200}
    )
    soup = BeautifulSoup(response.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    captcha_element = soup.find(id="captcha_question")
    if not token_input or not token_input.get("value") or not captcha_element:
        raise UpstreamError("Login page has an unexpected format")

    answer = solve_captcha(captcha_element.get_text(strip=True))
    if answer is None:
        raise UpstreamError("Login captcha has an unsupported format")
    return str(token_input["value"]), answer


async def login(client: UpstreamClient, username: str, password: str) -> str:
    token, captcha_answer = await get_login_page(client)
    response = await client.elearning(
        "POST",
        "/login",
        data={
            "username": username,
            "password": password,
            "_token": token,
            "captcha_answer": captcha_answer,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        expected_statuses={200},
    )
    return response.text


async def _credentials(request: web.Request) -> tuple[str | None, str | None]:
    if request.content_type == "application/json":
        body = await request.json()
    elif request.content_type in {
        "multipart/form-data",
        "application/x-www-form-urlencoded",
    }:
        body = await request.post()
    else:
        raise web.HTTPUnsupportedMediaType(
            reason="Supported content types: application/json, multipart/form-data, "
            "application/x-www-form-urlencoded"
        )

    if not isinstance(body, Mapping):
        raise web.HTTPBadRequest(reason="Request body must be an object")
    return body.get("username"), body.get("password")


async def post_login(request: web.Request) -> web.Response:
    username, password = await _credentials(request)
    if not isinstance(username, str) or not username.strip():
        raise web.HTTPBadRequest(reason="username is required")
    if not isinstance(password, str) or not password:
        raise web.HTTPBadRequest(reason="password is required")

    html = await login(request.app[UPSTREAM_CLIENT_KEY], username.strip(), password)
    if "dashboard" in html.lower():
        return web.json_response({"status": "success", "message": "Logged in"})
    return web.json_response(
        {"status": "failed", "message": "Invalid credentials"}
    )