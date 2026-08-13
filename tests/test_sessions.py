"""Tests for server-side tarot sessions and card drawing."""

from datetime import UTC, datetime, timedelta
from random import Random
from uuid import UUID

import httpx
import pytest

from app.core.errors import ErrorCode, TarotError
from app.data.deck import CARDS_BY_ID
from app.data.spreads import SPREADS
from app.main import app
from app.services.session_manager import SessionManager
from app.services.tarot_service import TarotService


def _service(
    *,
    ttl_seconds: int = 600,
    reversal_probability: float = 0.35,
    rng_seed: int = 1,
) -> TarotService:
    return TarotService(
        session_manager=SessionManager(ttl_seconds=ttl_seconds),
        reversal_probability=reversal_probability,
        rng=Random(rng_seed),
    )


@pytest.mark.asyncio
async def test_create_session_returns_public_contract_without_hidden_order() -> None:
    service = _service()

    response = await service.create_session(spread_id="three", reversals=True)
    payload = response.model_dump(by_alias=True)

    UUID(payload["sessionId"])
    assert payload["spread"] == {
        "id": "three",
        "name": "Три карты",
        "cardsRequired": 3,
        "positions": [
            {"index": 0, "name": "Прошлое"},
            {"index": 1, "name": "Настоящее"},
            {"index": 2, "name": "Будущее"},
        ],
    }
    assert payload["deck"] == {"size": 78}
    assert "shuffledDeck" not in payload


@pytest.mark.asyncio
async def test_all_spreads_draw_correct_positions() -> None:
    service = _service(reversal_probability=0)

    for spread_id, spread in SPREADS.items():
        session = await service.create_session(spread_id=spread_id, reversals=False)
        for slot, position_name in enumerate(spread.positions):
            response = await service.draw_card(session.session_id, slot=slot)
            assert response.position.index == slot
            assert response.position.name == position_name
            assert response.card.reversed is False


@pytest.mark.asyncio
async def test_draw_is_idempotent_for_same_session_and_slot() -> None:
    service = _service(reversal_probability=1)
    session = await service.create_session(spread_id="three", reversals=True)

    first = await service.draw_card(session.session_id, slot=17)
    second = await service.draw_card(session.session_id, slot=17)

    assert first == second


@pytest.mark.asyncio
async def test_cannot_draw_more_cards_than_spread_requires() -> None:
    service = _service()
    session = await service.create_session(spread_id="day", reversals=True)

    await service.draw_card(session.session_id, slot=0)

    with pytest.raises(TarotError) as exc_info:
        await service.draw_card(session.session_id, slot=1)

    assert exc_info.value.code == ErrorCode.SPREAD_COMPLETE


@pytest.mark.asyncio
async def test_same_physical_card_is_not_drawn_twice() -> None:
    service = _service(reversal_probability=0)
    session = await service.create_session(spread_id="celtic", reversals=False)

    drawn_ids = [
        (await service.draw_card(session.session_id, slot=slot)).card.id
        for slot in range(SPREADS["celtic"].cards_required)
    ]

    assert len(drawn_ids) == len(set(drawn_ids))


@pytest.mark.asyncio
async def test_yesno_verdict_uses_card_answer_table() -> None:
    service = _service(reversal_probability=1)
    session = await service.create_session(spread_id="yesno", reversals=True)

    response = await service.draw_card(session.session_id, slot=0)
    card = CARDS_BY_ID[response.card.id]

    assert response.card.reversed is True
    assert response.verdict == card.yes_no_reversed
    assert response.verdict_text in {"Скорее да", "Скорее нет"}


@pytest.mark.asyncio
async def test_session_expires_after_ttl() -> None:
    now = datetime(2026, 8, 13, tzinfo=UTC)

    def clock() -> datetime:
        return now

    manager = SessionManager(ttl_seconds=600, clock=clock)
    service = TarotService(session_manager=manager, rng=Random(1))
    session = await service.create_session(spread_id="day", reversals=False)

    now += timedelta(seconds=601)

    with pytest.raises(TarotError) as exc_info:
        await service.draw_card(session.session_id, slot=0)

    assert exc_info.value.code == ErrorCode.SESSION_EXPIRED


@pytest.mark.asyncio
async def test_api_create_session_to_draw_card_flow() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        created = await client.post(
            "/api/tarot/sessions",
            json={"spreadId": "three", "reversals": False},
        )
        assert created.status_code == 200
        session_id = created.json()["sessionId"]

        drawn = await client.post(
            f"/api/tarot/sessions/{session_id}/draw",
            json={"slot": 37},
        )

    assert drawn.status_code == 200
    payload = drawn.json()
    assert payload["position"] == {"index": 0, "name": "Прошлое"}
    assert payload["card"]["reversed"] is False
    assert payload["card"]["imageUrl"] == f"/cards/{payload['card']['id']}.jpg"
