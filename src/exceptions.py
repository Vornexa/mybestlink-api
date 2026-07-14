"""Application-specific exception types."""


class UpstreamError(RuntimeError):
    """Raised when a BSI upstream request or response is invalid."""
