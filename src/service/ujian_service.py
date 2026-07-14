"""Exam schedule and location validation endpoints."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import UTC, datetime
from urllib.parse import unquote, urljoin, urlparse

from aiohttp import web
from bs4 import BeautifulSoup

from src.app_keys import UPSTREAM_CLIENT_KEY
from src.exceptions import UpstreamError
from src.parser.mybestlink_parser import parse_exam_schedule
from src.service.upstream_client import UpstreamClient
from src.validation import validate_coordinates

_REDIRECT_STATUSES = {200, 301, 302, 303, 307, 308}
_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml",
}


def extract_redirect(headers: Mapping[str, str], html: str) -> str:
    """Extract a redirect URL from Location or a meta-refresh document."""

    for name, value in headers.items():
        if name.lower() == "location" and value:
            return value.strip()

    soup = BeautifulSoup(html, "html.parser")
    meta_refresh = soup.find(
        "meta", attrs={"http-equiv": re.compile(r"^refresh$", re.IGNORECASE)}
    )
    content = meta_refresh.get("content", "") if meta_refresh else ""
    match = re.search(r"url\s*=\s*(.+)$", str(content), re.IGNORECASE)
    if not match:
        raise UpstreamError("Upstream exam redirect was not found")
    return match.group(1).strip().strip("'\"")


def resolve_trusted_url(base_url: str, candidate: str) -> str:
    """Resolve a URL while preventing redirects to an unexpected host."""

    resolved = urljoin(f"{base_url.rstrip('/')}/", candidate)
    base = urlparse(base_url)
    target = urlparse(resolved)
    if (
        target.scheme != base.scheme
        or target.hostname != base.hostname
        or target.port != base.port
    ):
        raise UpstreamError("Upstream redirect uses an untrusted host")
    return resolved


async def fetch_ujian_dashboard(client: UpstreamClient) -> str:
    """Follow the elearning-to-exam authentication hand-off."""

    headers = {
        **_BROWSER_HEADERS,
        "Referer": f"{client.settings.elearning_base_url}/halaman-ujian",
    }
    first = await client.elearning(
        "GET",
        "/halaman-ujian",
        headers=headers,
        allow_redirects=False,
        expected_statuses=_REDIRECT_STATUSES,
    )
    exam_redirect = resolve_trusted_url(
        client.settings.exam_base_url,
        extract_redirect(first.headers, first.text),
    )

    second = await client.request_text(
        "GET",
        exam_redirect,
        headers=headers,
        allow_redirects=False,
        expected_statuses=_REDIRECT_STATUSES,
    )
    dashboard_url = resolve_trusted_url(
        client.settings.exam_base_url,
        extract_redirect(second.headers, second.text),
    )

    dashboard = await client.request_text(
        "GET",
        dashboard_url,
        headers=headers,
        allow_redirects=True,
        expected_statuses={200},
    )
    return dashboard.text


async def get_jadwal_ujian(request: web.Request) -> web.Response:
    exam_type = request.query.get("type", "uts").lower()
    if exam_type not in {"uts", "uas"}:
        raise web.HTTPBadRequest(reason="type must be either 'uts' or 'uas'")

    client = request.app[UPSTREAM_CLIENT_KEY]
    dashboard_html = await fetch_ujian_dashboard(client)
    soup = BeautifulSoup(dashboard_html, "html.parser")

    target_link = None
    for link in soup.find_all("a", href=True):
        text = link.get_text(strip=True).lower()
        if exam_type in text and "jadwal" in text:
            target_link = str(link["href"])
            break
    if not target_link:
        raise UpstreamError(
            f"Jadwal {exam_type.upper()} link was not found on the exam dashboard"
        )

    schedule_url = resolve_trusted_url(client.settings.exam_base_url, target_link)
    schedule_page = await client.request_text(
        "GET",
        schedule_url,
        headers={
            **_BROWSER_HEADERS,
            "Referer": f"{client.settings.exam_base_url}/dashboard",
        },
        allow_redirects=True,
        expected_statuses={200},
    )
    schedule = parse_exam_schedule(schedule_page.text)
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return web.json_response(
        {
            "status": "success",
            "data": {"jadwal": schedule},
            "meta": {
                "total": len(schedule),
                "type": exam_type.upper(),
                "timestamp": timestamp,
            },
        }
    )


async def post_cek_lokasi_service(
    client: UpstreamClient, latitude: float, longitude: float
) -> dict[str, object]:
    await fetch_ujian_dashboard(client)
    xsrf_cookie = client.sessions.cookies_for(
        client.settings.exam_base_url
    ).get("XSRF-TOKEN")
    if not xsrf_cookie:
        raise UpstreamError("XSRF token was not found in the exam session")

    response = await client.exam(
        "POST",
        "/api/save-location",
        json={"latitude": latitude, "longitude": longitude},
        headers={
            "Content-Type": "application/json",
            "Referer": f"{client.settings.exam_base_url}/dashboard",
            "Origin": client.settings.exam_base_url,
            "X-XSRF-TOKEN": unquote(xsrf_cookie),
            "User-Agent": "Mozilla/5.0",
        },
    )
    if response.status == 200:
        return {"success": True, "message": "Lokasi berhasil divalidasi"}
    return {
        "success": False,
        "error": f"Gagal validasi lokasi: upstream HTTP {response.status}",
    }


async def post_cek_lokasi(request: web.Request) -> web.Response:
    data = await request.json()
    if not isinstance(data, Mapping):
        raise web.HTTPBadRequest(reason="Request body must be an object")
    if "latitude" not in data or "longitude" not in data:
        raise web.HTTPBadRequest(reason="latitude and longitude are required")
    try:
        latitude, longitude = validate_coordinates(
            data["latitude"], data["longitude"]
        )
    except ValueError as error:
        raise web.HTTPBadRequest(reason=str(error)) from error

    result = await post_cek_lokasi_service(
        request.app[UPSTREAM_CLIENT_KEY], latitude, longitude
    )
    return web.json_response(result)
