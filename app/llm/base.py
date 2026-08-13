"""Abstract interface for tarot interpretation providers."""

from dataclasses import dataclass
from typing import Protocol

from app.schemas.tarot import Tone, YesNoAnswer


@dataclass(frozen=True)
class InterpretationCard:
    """One drawn card in the interpretation context."""

    position_index: int
    position_name: str
    card_id: str
    card_name: str
    reversed: bool
    meaning: str
    arcana: str
    element: str | None
    verdict: YesNoAnswer | None = None
    verdict_text: str | None = None


@dataclass(frozen=True)
class InterpretationRequest:
    """Domain-level request passed from TarotService to an LLM adapter."""

    question: str
    tone: Tone
    spread_id: str
    spread_name: str
    cards: tuple[InterpretationCard, ...]


class TarotInterpreter(Protocol):
    """Replaceable boundary between TarotService and any LLM gateway."""

    async def interpret(self, request: InterpretationRequest) -> str | None:
        """Return an interpretation text, or None when the adapter cannot answer."""
