"""Validation helpers for deck and spread reference data."""

from dataclasses import dataclass

from app.data.deck import DECK
from app.data.spreads import SPREADS
from app.schemas.tarot import CardDefinition, SpreadDefinition, YesNoAnswer


EXPECTED_CARD_IDS = (
    *(f"m{index:02}" for index in range(22)),
    *(f"w{index:02}" for index in range(1, 15)),
    *(f"c{index:02}" for index in range(1, 15)),
    *(f"s{index:02}" for index in range(1, 15)),
    *(f"p{index:02}" for index in range(1, 15)),
)
EXPECTED_SPREAD_IDS = {"day", "yesno", "three", "relationships", "celtic"}


@dataclass(frozen=True)
class ReferenceValidationResult:
    """Summary returned by reference-data validation."""

    cards_count: int
    spreads_count: int


def validate_reference_data(
    deck: tuple[CardDefinition, ...] = DECK,
    spreads: dict[str, SpreadDefinition] = SPREADS,
) -> ReferenceValidationResult:
    """Validate production tarot reference data and raise ValueError on mismatch."""
    _validate_deck(deck)
    _validate_spreads(spreads)
    return ReferenceValidationResult(cards_count=len(deck), spreads_count=len(spreads))


def _validate_deck(deck: tuple[CardDefinition, ...]) -> None:
    if len(deck) != 78:
        raise ValueError(f"Expected 78 cards, got {len(deck)}")

    card_ids = tuple(card.id for card in deck)
    if card_ids != EXPECTED_CARD_IDS:
        raise ValueError("Deck card IDs do not match the required production order")

    if len(set(card_ids)) != len(card_ids):
        raise ValueError("Deck card IDs must be unique")

    yes_no_up_values = set()
    for card in deck:
        required_strings = (
            card.id,
            card.name,
            card.arcana,
            card.meaning_up,
            card.meaning_reversed,
            card.image_url,
        )
        if any(not value for value in required_strings):
            raise ValueError(f"Card {card.id} has an empty required field")

        if card.image_url != f"/cards/{card.id}.jpg":
            raise ValueError(f"Card {card.id} has invalid imageUrl: {card.image_url}")

        if card.yes_no_up not in (YesNoAnswer.YES, YesNoAnswer.NO):
            raise ValueError(f"Card {card.id} has invalid yesNoUp")

        if card.yes_no_reversed not in (YesNoAnswer.YES, YesNoAnswer.NO):
            raise ValueError(f"Card {card.id} has invalid yesNoReversed")

        yes_no_up_values.add(card.yes_no_up)

    if yes_no_up_values != {YesNoAnswer.YES, YesNoAnswer.NO}:
        raise ValueError("yesNoUp must contain both yes and no answers")


def _validate_spreads(spreads: dict[str, SpreadDefinition]) -> None:
    if set(spreads) != EXPECTED_SPREAD_IDS:
        raise ValueError(f"Spread IDs must be exactly {sorted(EXPECTED_SPREAD_IDS)}")

    expected_cards_required = {
        "day": 1,
        "yesno": 1,
        "three": 3,
        "relationships": 5,
        "celtic": 10,
    }

    for spread_id, cards_required in expected_cards_required.items():
        spread = spreads[spread_id]
        if not spread.name:
            raise ValueError(f"Spread {spread_id} has empty name")
        if spread.cards_required != cards_required:
            raise ValueError(
                f"Spread {spread_id} must require {cards_required} cards, "
                f"got {spread.cards_required}"
            )
        if any(not position for position in spread.positions):
            raise ValueError(f"Spread {spread_id} has an empty position name")
