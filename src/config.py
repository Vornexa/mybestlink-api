"""Application configuration loaded from environment variables."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}
logger = logging.getLogger(__name__)


def _environment_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    value = raw_value.strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    raise ValueError(
        f"{name} must be one of: {', '.join(sorted(_TRUE_VALUES | _FALSE_VALUES))}"
    )


def normalize_base_url(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty URL")
    normalized = value.strip().rstrip("/")
    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{name} must use http or https")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(f"{name} must be a base URL without credentials or query")
    return normalized


@dataclass(slots=True)
class Settings:
    """Runtime settings for the API and its upstream services."""

    host: str = "0.0.0.0"
    port: int = 8000
    elearning_base_url: str = "https://elearning.bsi.ac.id"
    exam_base_url: str = "https://ujiankampusa.bsi.ac.id"
    cookie_file: Path = Path("cookies.json")
    control_config_file: Path = Path("control-panel.json")
    request_timeout_seconds: float = 30.0
    verify_ssl: bool = True

    def control_values(self) -> dict[str, object]:
        return {
            "elearning_base_url": self.elearning_base_url,
            "exam_base_url": self.exam_base_url,
            "request_timeout_seconds": self.request_timeout_seconds,
            "verify_ssl": self.verify_ssl,
        }

    def validate_control_values(self, payload: object) -> dict[str, object]:
        if not isinstance(payload, dict):
            raise ValueError("Request body must be an object")
        required = set(self.control_values())
        if set(payload) != required:
            raise ValueError(
                "config must include elearning_base_url, exam_base_url, "
                "request_timeout_seconds, and verify_ssl"
            )
        timeout = payload["request_timeout_seconds"]
        if isinstance(timeout, bool) or not isinstance(timeout, int | float):
            raise ValueError("request_timeout_seconds must be a number")
        if not 1 <= float(timeout) <= 120:
            raise ValueError("request_timeout_seconds must be between 1 and 120")
        verify_ssl = payload["verify_ssl"]
        if not isinstance(verify_ssl, bool):
            raise ValueError("verify_ssl must be a boolean")
        return {
            "elearning_base_url": normalize_base_url(
                "elearning_base_url", payload["elearning_base_url"]
            ),
            "exam_base_url": normalize_base_url(
                "exam_base_url", payload["exam_base_url"]
            ),
            "request_timeout_seconds": float(timeout),
            "verify_ssl": verify_ssl,
        }

    def apply_control_values(self, values: dict[str, object]) -> None:
        self.elearning_base_url = str(values["elearning_base_url"])
        self.exam_base_url = str(values["exam_base_url"])
        self.request_timeout_seconds = float(values["request_timeout_seconds"])
        self.verify_ssl = bool(values["verify_ssl"])

    def load_control_overrides(self) -> Settings:
        if not self.control_config_file.exists():
            return self
        try:
            payload = json.loads(
                self.control_config_file.read_text(encoding="utf-8")
            )
            self.apply_control_values(self.validate_control_values(payload))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            logger.warning(
                "Ignoring unreadable control panel config: %s",
                self.control_config_file,
            )
        return self

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from ``MYBESTLINK_*`` environment variables."""

        defaults = cls()
        try:
            port = int(os.getenv("MYBESTLINK_PORT", str(defaults.port)))
        except ValueError as error:
            raise ValueError("MYBESTLINK_PORT must be an integer") from error
        if not 1 <= port <= 65535:
            raise ValueError("MYBESTLINK_PORT must be between 1 and 65535")

        try:
            timeout = float(
                os.getenv(
                    "MYBESTLINK_REQUEST_TIMEOUT",
                    str(defaults.request_timeout_seconds),
                )
            )
        except ValueError as error:
            raise ValueError(
                "MYBESTLINK_REQUEST_TIMEOUT must be a number"
            ) from error
        if timeout <= 0:
            raise ValueError("MYBESTLINK_REQUEST_TIMEOUT must be greater than 0")

        return cls(
            host=os.getenv("MYBESTLINK_HOST", defaults.host),
            port=port,
            elearning_base_url=os.getenv(
                "MYBESTLINK_ELEARNING_BASE_URL", defaults.elearning_base_url
            ).rstrip("/"),
            exam_base_url=os.getenv(
                "MYBESTLINK_EXAM_BASE_URL", defaults.exam_base_url
            ).rstrip("/"),
            cookie_file=Path(
                os.getenv("MYBESTLINK_COOKIE_FILE", str(defaults.cookie_file))
            ),
            control_config_file=Path(
                os.getenv(
                    "MYBESTLINK_CONTROL_CONFIG_FILE",
                    str(defaults.control_config_file),
                )
            ),
            request_timeout_seconds=timeout,
            verify_ssl=_environment_bool(
                "MYBESTLINK_VERIFY_SSL", defaults.verify_ssl
            ),
        )
