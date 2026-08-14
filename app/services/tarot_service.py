"""Main tarot use-case service.

This layer coordinates deck data, spreads, sessions, draw rules, and interpretation.
Routes should call this service instead of owning business logic directly.
"""

import random
from uuid import uuid4

from fastapi import status

from app.core.config import settings
from app.core.errors import ErrorCode, TarotError, spread_not_found
from app.data.deck import DECK
from app.data.spreads import SPREADS, resolve_spread_id
from app.llm.base import InterpretationCard, InterpretationRequest, TarotInterpreter
from app.schemas.tarot import (
    CreateSessionResponse,
    DeckPublic,
    DrawCardResponse,
    DrawnCardPublic,
    InterpretResponse,
    SpreadPosition,
    SpreadPublic,
    Tone,
    YesNoAnswer,
)
from app.services.fallback_interpreter import FallbackInterpreter
from app.services.session_manager import DrawRecord, SessionManager, TarotSession


class TarotService:
    """Application service for tarot use cases."""

    def __init__(
        self,
        session_manager: SessionManager | None = None,
        interpreter: TarotInterpreter | None = None,
        reversal_probability: float | None = None,
        validate_llm_responses: bool | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self._interpreter = interpreter
        self._fallback_interpreter = FallbackInterpreter()
        self._deck = DECK
        self._spreads = SPREADS
        self._cards_by_id = {card.id: card for card in self._deck}
        self._session_manager = session_manager or SessionManager(settings.session_ttl_seconds)
        self._reversal_probability = (
            settings.reversal_probability
            if reversal_probability is None
            else reversal_probability
        )
        self._validate_llm_responses = (
            settings.llm_validate_responses
            if validate_llm_responses is None
            else validate_llm_responses
        )
        self._rng = rng or random.Random()

    def get_spread(self, spread_id: str):
        """Return a spread definition by canonical or legacy frontend ID."""
        return self._spreads.get(resolve_spread_id(spread_id))

    @property
    def deck_size(self) -> int:
        """Total number of production cards."""
        return len(self._deck)

    async def create_session(self, spread_id: str, reversals: bool) -> CreateSessionResponse:
        """Create a server-side spread session without exposing the hidden deck order."""
        canonical_spread_id = resolve_spread_id(spread_id)
        spread = self._spreads.get(canonical_spread_id)
        if spread is None:
            raise spread_not_found(spread_id)

        shuffled_deck = tuple(card.id for card in self._deck)
        shuffled_deck = tuple(self._rng.sample(shuffled_deck, k=len(shuffled_deck)))
        session_id = str(uuid4())

        await self._session_manager.create(
            session_id=session_id,
            spread_id=canonical_spread_id,
            reversals=reversals,
            shuffled_deck=shuffled_deck,
        )

        return CreateSessionResponse(
            sessionId=session_id,
            spread=self._to_public_spread(spread),
            deck=DeckPublic(size=len(self._deck)),
        )

    async def draw_card(self, session_id: str, slot: int) -> DrawCardResponse:
        """Draw one card by fan slot, preserving idempotency for (session, slot)."""
        if slot < 0 or slot >= len(self._deck):
            raise TarotError(
                ErrorCode.SLOT_OUT_OF_RANGE,
                "Slot out of range",
                status.HTTP_400_BAD_REQUEST,
            )

        session = await self._session_manager.get_active(session_id)
        async with session.lock:
            existing = session.draws_by_slot.get(slot)
            if existing is not None:
                return self._to_draw_response(session, existing)

            spread = self._spreads[session.spread_id]
            if len(session.draws_in_order) >= spread.cards_required:
                raise TarotError(
                    ErrorCode.SPREAD_COMPLETE,
                    "Spread already complete",
                    status.HTTP_409_CONFLICT,
                )

            record = DrawRecord(
                slot=slot,
                position_index=len(session.draws_in_order),
                card_id=session.shuffled_deck[slot],
                reversed=session.reversals and self._rng.random() < self._reversal_probability,
            )
            session.draws_by_slot[slot] = record
            session.draws_in_order.append(record)
            return self._to_draw_response(session, record)

    async def delete_session(self, session_id: str) -> None:
        """Delete a session idempotently."""
        await self._session_manager.delete(session_id)

    async def interpret(
        self,
        session_id: str,
        question: str,
        tone: Tone,
    ) -> InterpretResponse:
        """Interpret a completed spread through the LLM, falling back locally."""
        session = await self._session_manager.get_active(session_id)
        async with session.lock:
            spread = self._spreads[session.spread_id]
            if len(session.draws_in_order) < spread.cards_required:
                raise TarotError(
                    ErrorCode.SPREAD_INCOMPLETE,
                    "Spread is not complete",
                    status.HTTP_409_CONFLICT,
                )
            request = self._to_interpretation_request(session, question, tone)

        if self._interpreter is not None:
            try:
                text = await self._interpreter.interpret(request)
                if text and (
                    not self._validate_llm_responses
                    or self._is_usable_ai_response(text, request)
                ):
                    return InterpretResponse(type="ai", text=text.strip())
            except Exception:
                pass

        return InterpretResponse(
            type="basic",
            text=self._fallback_interpreter.interpret(request),
            reason="LLM_UNAVAILABLE",
        )

    def _to_public_spread(self, spread) -> SpreadPublic:
        return SpreadPublic(
            id=spread.id,
            name=spread.name,
            cardsRequired=spread.cards_required,
            positions=[
                SpreadPosition(index=index, name=name)
                for index, name in enumerate(spread.positions)
            ],
        )

    def _to_draw_response(
        self,
        session: TarotSession,
        record: DrawRecord,
    ) -> DrawCardResponse:
        spread = self._spreads[session.spread_id]
        card = self._cards_by_id[record.card_id]
        meaning = card.meaning_reversed if record.reversed else card.meaning_up
        yes_no_answer = card.yes_no_reversed if record.reversed else card.yes_no_up

        verdict = yes_no_answer if spread.yesno else None
        verdict_text = None
        if verdict == YesNoAnswer.YES:
            verdict_text = "Скорее да"
        elif verdict == YesNoAnswer.NO:
            verdict_text = "Скорее нет"

        return DrawCardResponse(
            position=SpreadPosition(
                index=record.position_index,
                name=spread.positions[record.position_index],
            ),
            card=DrawnCardPublic(
                id=card.id,
                name=card.name,
                reversed=record.reversed,
                imageUrl=card.image_url,
                meaning=meaning,
                arcana=card.arcana,
                element=card.element,
            ),
            verdict=verdict,
            verdictText=verdict_text,
        )

    def _to_interpretation_request(
        self,
        session: TarotSession,
        question: str,
        tone: Tone,
    ) -> InterpretationRequest:
        spread = self._spreads[session.spread_id]
        cards = tuple(
            self._to_interpretation_card(session, record)
            for record in session.draws_in_order
        )
        return InterpretationRequest(
            question=question,
            tone=tone,
            spread_id=spread.id,
            spread_name=spread.name,
            cards=cards,
        )

    def _to_interpretation_card(
        self,
        session: TarotSession,
        record: DrawRecord,
    ) -> InterpretationCard:
        spread = self._spreads[session.spread_id]
        card = self._cards_by_id[record.card_id]
        draw_response = self._to_draw_response(session, record)
        return InterpretationCard(
            position_index=record.position_index,
            position_name=spread.positions[record.position_index],
            card_id=card.id,
            card_name=card.name,
            reversed=record.reversed,
            meaning=draw_response.card.meaning,
            arcana=card.arcana,
            element=card.element,
            verdict=draw_response.verdict,
            verdict_text=draw_response.verdict_text,
        )

    def _is_usable_ai_response(self, text: str, request: InterpretationRequest) -> bool:
        """Reject low-quality model output so the UI can use deterministic fallback."""
        stripped = text.strip()
        if len(stripped) < 180:
            return False

        if not stripped.endswith("?"):
            return False

        if not any(card.card_name in stripped for card in request.cards):
            return False

        lines = [line.strip() for line in stripped.splitlines() if line.strip()]
        if any(line.startswith(("-", "*", "•")) for line in lines):
            return False

        paragraphs = [part.strip() for part in stripped.split("\n\n") if part.strip()]
        if len(paragraphs) < 2:
            return False

        return True
