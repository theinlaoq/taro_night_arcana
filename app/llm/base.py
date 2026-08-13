"""Abstract interface for tarot interpretation providers."""

from dataclasses import dataclass
from typing import Protocol

from app.schemas.tarot import Tone


@dataclass(frozen=True)
class InterpretationRequest:
    """Domain-level request passed from TarotService to an LLM adapter."""

    question: str
    tone: Tone
    spread_id: str
    cards: tuple[str, ...]


class TarotInterpreter(Protocol):
    """Replaceable boundary between TarotService and any LLM gateway."""

    async def interpret(self, request: InterpretationRequest) -> str | None:
        """Return an interpretation text, or None when the adapter cannot answer."""
