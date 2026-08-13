"""Tests for the initial FastAPI skeleton and production reference data."""

from pathlib import Path

from app.data.deck import DECK
from app.data.spreads import SPREADS, resolve_spread_id
from app.data.validation import validate_reference_data
from app.main import app
from app.schemas.tarot import YesNoAnswer
from app.services.tarot_service import TarotService


def test_project_skeleton_has_health_route() -> None:
    route_paths = {route.path for route in app.routes if hasattr(route, "path")}
    assert "/health" in route_paths


def test_reference_data_is_valid() -> None:
    result = validate_reference_data()
    assert result.cards_count == 78
    assert result.spreads_count == 5


def test_deck_has_78_unique_ids_and_required_fields() -> None:
    card_ids = [card.id for card in DECK]

    assert len(DECK) == 78, "Deck must contain exactly 78 cards"
    assert len(set(card_ids)) == 78, "Deck card IDs must be unique"
    for card in DECK:
        assert card.id, f"{card.id} has empty id"
        assert card.name, f"{card.id} has empty name"
        assert card.arcana, f"{card.id} has empty arcana"
        assert card.meaning_up, f"{card.id} has empty meaningUp"
        assert card.meaning_reversed, f"{card.id} has empty meaningReversed"
        assert card.yes_no_up, f"{card.id} has empty yesNoUp"
        assert card.yes_no_reversed, f"{card.id} has empty yesNoReversed"
        assert card.image_url, f"{card.id} has empty imageUrl"


def test_deck_image_urls_follow_frontend_contract() -> None:
    assert len({card.image_url for card in DECK}) == 78
    assert all(card.image_url == f"/cards/{card.id}.jpg" for card in DECK)


def test_all_card_image_files_exist() -> None:
    image_paths = [Path("cards") / f"{card.id}.jpg" for card in DECK]

    assert len(image_paths) == 78
    for path in image_paths:
        assert path.exists(), f"Missing local card image: {path}"


def test_yesno_values_are_complete_and_mixed() -> None:
    up_values = {card.yes_no_up for card in DECK}

    assert all(card.yes_no_up for card in DECK)
    assert all(card.yes_no_reversed for card in DECK)
    assert up_values == {YesNoAnswer.YES, YesNoAnswer.NO}


def test_card_static_mount_can_resolve_local_file() -> None:
    static_route = next(route for route in app.routes if getattr(route, "path", None) == "/cards")
    full_path, stat_result = static_route.app.lookup_path("m00.jpg")

    assert stat_result is not None
    assert Path(full_path).name == "m00.jpg"
    assert Path(full_path).read_bytes().startswith(b"\xff\xd8")


def test_spread_counts_match_spec() -> None:
    assert {spread_id: spread.cards_required for spread_id, spread in SPREADS.items()} == {
        "day": 1,
        "yesno": 1,
        "three": 3,
        "relationships": 5,
        "celtic": 10,
    }


def test_current_frontend_legacy_spread_ids_can_be_resolved() -> None:
    assert resolve_spread_id("love") == "relationships"
    assert resolve_spread_id("cross") == "celtic"


def test_tarot_service_does_not_depend_on_llm_config() -> None:
    service = TarotService()
    assert service.deck_size == 78
    assert service.get_spread("three") is SPREADS["three"]
