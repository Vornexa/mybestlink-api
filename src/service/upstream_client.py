"""Managed outbound HTTP client for BSI upstream services."""

from __future__ import annotations

import json
import logging
from asyncio import Lock, to_thread
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from http.cookies import SimpleCookie
from pathlib import Path

import aiohttp
from yarl import URL

from src.config import Settings
from src.exceptions import UpstreamError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class UpstreamResponse:
    status: int
    headers: Mapping[str, str]
    text: str
    url: str


class SessionManager:
    """Own one outbound session and persist its cookies as safe JSON."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._session: aiohttp.ClientSession | None = None
        self._lock = Lock()

    async def get(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            async with self._lock:
                if self._session is None or self._session.closed:
                    timeout = aiohttp.ClientTimeout(
                        total=self.settings.request_timeout_seconds
                    )
                    self._session = aiohttp.ClientSession(
                        cookie_jar=aiohttp.CookieJar(), timeout=timeout
                    )
                    await self._load_cookies()
        return self._session

    def clear_cookies(self) -> None:
        if self._session and not self._session.closed:
            self._session.cookie_jar.clear()

    def cookies(self) -> dict[str, str]:
        if not self._session or self._session.closed:
            return {}
        return {
            cookie.key: cookie.value for cookie in self._session.cookie_jar
        }

    def cookies_for(self, url: str) -> dict[str, str]:
        if not self._session or self._session.closed:
            return {}
        cookies = self._session.cookie_jar.filter_cookies(URL(url))
        return {name: morsel.value for name, morsel in cookies.items()}

    async def _load_cookies(self) -> None:
        cookie_file = self.settings.cookie_file
        if not cookie_file.exists() or self._session is None:
            return
        try:
            contents = await to_thread(cookie_file.read_text, encoding="utf-8")
            payload = json.loads(contents)
            cookies = payload.get("cookies", [])
            if not isinstance(cookies, list):
                raise ValueError("cookies must be an array")
            for cookie in cookies:
                self._restore_cookie(cookie)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            logger.warning("Ignoring unreadable cookie file: %s", cookie_file)

    def _restore_cookie(self, data: object) -> None:
        if not isinstance(data, dict) or self._session is None:
            raise ValueError("cookie must be an object")
        name = data.get("name")
        value = data.get("value")
        domain = data.get("domain")
        if not all(isinstance(item, str) and item for item in (name, domain)):
            raise ValueError("cookie name and domain must be strings")
        if not isinstance(value, str):
            raise ValueError("cookie value must be a string")

        cookie = SimpleCookie()
        cookie[name] = value
        morsel = cookie[name]
        path = data.get("path", "/")
        morsel["path"] = path if isinstance(path, str) and path else "/"
        if not data.get("host_only", False):
            morsel["domain"] = domain
        for attribute in ("expires", "max-age", "httponly", "samesite"):
            attribute_value = data.get(attribute)
            if isinstance(attribute_value, str) and attribute_value:
                morsel[attribute] = attribute_value
        if data.get("secure", False):
            morsel["secure"] = True

        scheme = "https" if data.get("secure", False) else "http"
        response_url = URL.build(
            scheme=scheme,
            host=domain.lstrip("."),
            path=morsel["path"],
        )
        self._session.cookie_jar.update_cookies(cookie, response_url)

    def _serialize_cookies(self) -> list[dict[str, object]]:
        if not self._session or self._session.closed:
            return []
        jar = self._session.cookie_jar
        # aiohttp has no public host-only-cookie accessor. Persisting this bit
        # prevents a restored host-only cookie from being sent to subdomains.
        host_only_cookies = getattr(jar, "_host_only_cookies", set())
        return [
            {
                "name": cookie.key,
                "value": cookie.value,
                "domain": cookie["domain"],
                "path": cookie["path"] or "/",
                "expires": cookie["expires"],
                "max-age": cookie["max-age"],
                "secure": bool(cookie["secure"]),
                "httponly": cookie["httponly"],
                "samesite": cookie["samesite"],
                "host_only": (cookie["domain"], cookie.key)
                in host_only_cookies,
            }
            for cookie in jar
            if cookie["domain"]
        ]

    async def save(self) -> None:
        if not self._session or self._session.closed:
            return
        async with self._lock:
            cookie_file = self.settings.cookie_file
            temporary_file = cookie_file.with_suffix(cookie_file.suffix + ".tmp")
            payload = {"version": 1, "cookies": self._serialize_cookies()}
            await to_thread(
                self._write_cookie_file,
                cookie_file,
                temporary_file,
                payload,
            )

    @staticmethod
    def _write_cookie_file(
        cookie_file: Path,
        temporary_file: Path,
        payload: dict[str, object],
    ) -> None:
        cookie_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_file.write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )
        temporary_file.replace(cookie_file)

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self.save()
            await self._session.close()


class UpstreamClient:
    """Centralize timeouts, TLS policy, cookie persistence, and HTTP errors."""

    def __init__(self, settings: Settings, sessions: SessionManager) -> None:
        self.settings = settings
        self.sessions = sessions

    async def request_text(
        self,
        method: str,
        url: str,
        *,
        expected_statuses: Collection[int] | None = None,
        **kwargs: object,
    ) -> UpstreamResponse:
        session = await self.sessions.get()
        try:
            async with session.request(
                method,
                url,
                ssl=self.settings.verify_ssl,
                **kwargs,
            ) as response:
                text = await response.text()
                result = UpstreamResponse(
                    status=response.status,
                    headers=dict(response.headers),
                    text=text,
                    url=str(response.url),
                )
        except (aiohttp.ClientError, TimeoutError) as error:
            message = f"Upstream request failed: {type(error).__name__}"
            raise UpstreamError(message) from error

        await self.sessions.save()
        if expected_statuses is not None and result.status not in expected_statuses:
            raise UpstreamError(f"Upstream returned HTTP {result.status}")
        return result

    async def elearning(
        self, method: str, path: str, **kwargs: object
    ) -> UpstreamResponse:
        return await self.request_text(
            method,
            f"{self.settings.elearning_base_url}/{path.lstrip('/')}",
            **kwargs,
        )

    async def exam(
        self, method: str, path: str, **kwargs: object
    ) -> UpstreamResponse:
        return await self.request_text(
            method,
            f"{self.settings.exam_base_url}/{path.lstrip('/')}",
            **kwargs,
        )
