class PermissionDeniedError(PermissionError):
    """Raised when the actor lacks a Finance capability permission."""


class InvalidIdempotencyKeyError(ValueError):
    """Raised when a client retry key is absent or unsafe."""


class IdempotencyConflictError(RuntimeError):
    """Raised when a retry key is reused with different command input."""

