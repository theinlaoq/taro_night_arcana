"""Shared API error codes and exception helpers."""

from enum import StrEnum

from fastapi import status


class ErrorCode(StrEnum):
    """Error codes required by the frontend/backend contract."""

    SPREAD_NOT_FOUND = "SPREAD_NOT_FOUND"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SLOT_OUT_OF_RANGE = "SLOT_OUT_OF_RANGE"
    SPREAD_COMPLETE = "SPREAD_COMPLETE"
    SPREAD_INCOMPLETE = "SPREAD_INCOMPLETE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class TarotError(Exception):
    """Domain error that should be serialized with the frontend error contract."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        http_status: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


def spread_not_found(spread_id: str) -> TarotError:
    """Build an error for an unknown spread."""
    return TarotError(
        ErrorCode.SPREAD_NOT_FOUND,
        f"Spread not found: {spread_id}",
        status.HTTP_404_NOT_FOUND,
    )


def session_not_found(session_id: str) -> TarotError:
    """Build an error for an unknown session."""
    return TarotError(
        ErrorCode.SESSION_NOT_FOUND,
        f"Session not found: {session_id}",
        status.HTTP_404_NOT_FOUND,
    )


def session_expired(session_id: str) -> TarotError:
    """Build an error for an expired session."""
    return TarotError(
        ErrorCode.SESSION_EXPIRED,
        f"Session expired: {session_id}",
        status.HTTP_410_GONE,
    )
