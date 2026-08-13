"""Shared API error codes and exception helpers."""

from enum import StrEnum


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
