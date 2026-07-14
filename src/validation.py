"""Validation helpers shared by HTTP handlers."""

from __future__ import annotations


def _coordinate(value: object, name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    try:
        coordinate = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a number") from error
    if not minimum <= coordinate <= maximum:
        raise ValueError(f"{name} must be between {minimum:g} and {maximum:g}")
    return coordinate


def validate_coordinates(latitude: object, longitude: object) -> tuple[float, float]:
    """Validate and normalize WGS84 latitude/longitude values."""

    return (
        _coordinate(latitude, "latitude", -90, 90),
        _coordinate(longitude, "longitude", -180, 180),
    )
