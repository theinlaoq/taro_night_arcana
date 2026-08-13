"""Main tarot use-case service.

This layer coordinates deck data, spreads, sessions, draw rules, and interpretation.
Routes should call this service instead of owning business logic directly.
"""

from app.data.deck import DECK
from app.data.spreads import SPREADS, resolve_spread_id
from app.llm.base import TarotInterpreter


class TarotService:
    """Application service for tarot use cases."""

    def __init__(self, interpreter: TarotInterpreter | None = None) -> None:
        self._interpreter = interpreter
        self._deck = DECK
        self._spreads = SPREADS

    def get_spread(self, spread_id: str):
        """Return a spread definition by canonical or legacy frontend ID."""
        return self._spreads.get(resolve_spread_id(spread_id))

    @property
    def deck_size(self) -> int:
        """Total number of production cards."""
        return len(self._deck)
