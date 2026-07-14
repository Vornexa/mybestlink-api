"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


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


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings for the API and its upstream services."""

    host: str = "0.0.0.0"
    port: int = 8000
    elearning_base_url: str = "https://elearning.bsi.ac.id"
    exam_base_url: str = "https://ujiankampusa.bsi.ac.id"
    cookie_file: Path = Path("cookies.json")
    request_timeout_seconds: float = 30.0
    verify_ssl: bool = True

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
            request_timeout_seconds=timeout,
            verify_ssl=_environment_bool(
                "MYBESTLINK_VERIFY_SSL", defaults.verify_ssl
            ),
        )
