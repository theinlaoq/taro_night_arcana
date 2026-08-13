"""In-memory session storage with TTL and per-session locking.

The MVP stores active sessions in one backend process. Persistence can be added
later without changing the HTTP contract.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.core.errors import session_expired, session_not_found


@dataclass
class DrawRecord:
    """A card draw stored in a session."""

    slot: int
    position_index: int
    card_id: str
    reversed: bool


@dataclass
class TarotSession:
    """Mutable in-memory state for one active spread."""

    session_id: str
    spread_id: str
    created_at: datetime
    last_activity_at: datetime
    reversals: bool
    shuffled_deck: tuple[str, ...]
    draws_by_slot: dict[int, DrawRecord] = field(default_factory=dict)
    draws_in_order: list[DrawRecord] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class SessionManager:
    """In-memory session repository with TTL cleanup."""

    def __init__(
        self,
        ttl_seconds: int,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sessions: dict[str, TarotSession] = {}
        self._expired_session_ids: set[str] = set()
        self._registry_lock = asyncio.Lock()

    async def create(
        self,
        session_id: str,
        spread_id: str,
        reversals: bool,
        shuffled_deck: tuple[str, ...],
    ) -> TarotSession:
        """Store and return a new session."""
        now = self._clock()
        session = TarotSession(
            session_id=session_id,
            spread_id=spread_id,
            created_at=now,
            last_activity_at=now,
            reversals=reversals,
            shuffled_deck=shuffled_deck,
        )
        async with self._registry_lock:
            self._cleanup_expired(now)
            self._sessions[session_id] = session
        return session

    async def get_active(self, session_id: str) -> TarotSession:
        """Return an active session and update its last activity timestamp."""
        async with self._registry_lock:
            session = self._sessions.get(session_id)
            if session is None:
                if session_id in self._expired_session_ids:
                    raise session_expired(session_id)
                raise session_not_found(session_id)

            now = self._clock()
            if self._is_expired(session, now):
                del self._sessions[session_id]
                self._expired_session_ids.add(session_id)
                raise session_expired(session_id)

            session.last_activity_at = now
            return session

    async def delete(self, session_id: str) -> None:
        """Delete a session if it exists. Used by future reset endpoint."""
        async with self._registry_lock:
            self._sessions.pop(session_id, None)
            self._expired_session_ids.discard(session_id)

    def _cleanup_expired(self, now: datetime) -> None:
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if self._is_expired(session, now)
        ]
        for session_id in expired_ids:
            del self._sessions[session_id]
            self._expired_session_ids.add(session_id)

    def _is_expired(self, session: TarotSession, now: datetime) -> bool:
        return now - session.last_activity_at > self._ttl
