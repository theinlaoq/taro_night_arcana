"""Tests for server-side tarot sessions and card drawing."""

import asyncio
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
async def test_api_draw_is_idempotent_for_same_session_and_slot() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        created = await client.post(
            "/api/tarot/sessions",
            json={"spreadId": "three", "reversals": True},
        )
        session_id = created.json()["sessionId"]

        first = await client.post(f"/api/tarot/sessions/{session_id}/draw", json={"slot": 17})
        second = await client.post(f"/api/tarot/sessions/{session_id}/draw", json={"slot": 17})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


@pytest.mark.asyncio
async def test_parallel_draws_do_not_reuse_positions_or_cards() -> None:
    service = _service(reversal_probability=0)
    session = await service.create_session(spread_id="three", reversals=False)

    results = await asyncio.gather(
        service.draw_card(session.session_id, slot=1),
        service.draw_card(session.session_id, slot=2),
        service.draw_card(session.session_id, slot=3),
    )

    assert sorted(result.position.index for result in results) == [0, 1, 2]
    assert len({result.card.id for result in results}) == 3


@pytest.mark.asyncio
async def test_parallel_draws_cannot_exceed_spread_size() -> None:
    service = _service()
    session = await service.create_session(spread_id="day", reversals=True)

    results = await asyncio.gather(
        service.draw_card(session.session_id, slot=1),
        service.draw_card(session.session_id, slot=2),
        return_exceptions=True,
    )

    successes = [result for result in results if not isinstance(result, Exception)]
    errors = [result for result in results if isinstance(result, TarotError)]

    assert len(successes) == 1
    assert len(errors) == 1
    assert errors[0].code == ErrorCode.SPREAD_COMPLETE


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
async def test_expired_session_is_removed_but_still_reported_as_expired() -> None:
    now = datetime(2026, 8, 13, tzinfo=UTC)

    def clock() -> datetime:
        return now

    manager = SessionManager(ttl_seconds=600, clock=clock)
    service = TarotService(session_manager=manager, rng=Random(1))
    session = await service.create_session(spread_id="day", reversals=False)

    now += timedelta(seconds=601)
    await service.create_session(spread_id="day", reversals=False)

    with pytest.raises(TarotError) as exc_info:
        await service.draw_card(session.session_id, slot=0)

    assert exc_info.value.code == ErrorCode.SESSION_EXPIRED


@pytest.mark.asyncio
async def test_delete_session_is_idempotent() -> None:
    service = _service()
    session = await service.create_session(spread_id="day", reversals=False)

    await service.delete_session(session.session_id)
    await service.delete_session(session.session_id)

    with pytest.raises(TarotError) as exc_info:
        await service.draw_card(session.session_id, slot=0)

    assert exc_info.value.code == ErrorCode.SESSION_NOT_FOUND


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


@pytest.mark.asyncio
async def test_api_delete_session_is_idempotent() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        created = await client.post(
            "/api/tarot/sessions",
            json={"spreadId": "day", "reversals": False},
        )
        session_id = created.json()["sessionId"]

        first = await client.delete(f"/api/tarot/sessions/{session_id}")
        second = await client.delete(f"/api/tarot/sessions/{session_id}")

    assert first.status_code == 200
    assert first.json() == {"ok": True}
    assert second.status_code == 200
    assert second.json() == {"ok": True}


@pytest.mark.asyncio
async def test_api_errors_use_uniform_contract() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        unknown_spread = await client.post(
            "/api/tarot/sessions",
            json={"spreadId": "missing", "reversals": False},
        )
        missing_session = await client.post(
            "/api/tarot/sessions/missing-session/draw",
            json={"slot": 0},
        )
        invalid_slot = await client.post(
            "/api/tarot/sessions/missing-session/draw",
            json={"slot": 78},
        )
        validation_error = await client.post(
            "/api/tarot/sessions",
            json={"reversals": False},
        )

    assert unknown_spread.status_code == 404
    assert unknown_spread.json()["code"] == ErrorCode.SPREAD_NOT_FOUND

    assert missing_session.status_code == 404
    assert missing_session.json()["code"] == ErrorCode.SESSION_NOT_FOUND

    assert invalid_slot.status_code == 400
    assert invalid_slot.json() == {"code": ErrorCode.SLOT_OUT_OF_RANGE, "message": "Slot out of range"}

    assert validation_error.status_code == 422
    assert validation_error.json()["code"] == ErrorCode.VALIDATION_ERROR
