"""Pydantic models shared by the Tarot API and domain services."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class YesNoAnswer(StrEnum):
    """Allowed backend verdict values for the yes/no spread."""

    YES = "yes"
    NO = "no"


class Tone(StrEnum):
    """Allowed interpretation tones from the frontend contract."""

    IRONIC = "ironic"
    WARM = "warm"
    DRY = "dry"


class CardDefinition(BaseModel):
    """Production reference data for one tarot card."""

    id: str
    name: str
    arcana: str
    element: str | None
    meaning_up: str = Field(alias="meaningUp")
    meaning_reversed: str = Field(alias="meaningReversed")
    yes_no_up: YesNoAnswer = Field(alias="yesNoUp")
    yes_no_reversed: YesNoAnswer = Field(alias="yesNoReversed")
    image_url: str = Field(alias="imageUrl")

    model_config = ConfigDict(frozen=True, populate_by_name=True)


class SpreadPosition(BaseModel):
    """One named position inside a spread."""

    index: int
    name: str

    model_config = ConfigDict(frozen=True)


class SpreadDefinition(BaseModel):
    """Production reference data for one tarot spread."""

    id: str
    name: str
    positions: tuple[str, ...]
    yesno: bool = False

    model_config = ConfigDict(frozen=True)

    @property
    def cards_required(self) -> int:
        """Number of cards the visitor must draw for this spread."""
        return len(self.positions)


class CreateSessionRequest(BaseModel):
    """Request body for POST /api/tarot/sessions."""

    spread_id: str = Field(alias="spreadId")
    reversals: bool = True

    model_config = ConfigDict(populate_by_name=True)


class DrawCardRequest(BaseModel):
    """Request body for POST /api/tarot/sessions/{sessionId}/draw."""

    slot: int


class SpreadPublic(BaseModel):
    """Spread description returned to the frontend."""

    id: str
    name: str
    cards_required: int = Field(alias="cardsRequired")
    positions: list[SpreadPosition]

    model_config = ConfigDict(populate_by_name=True)


class DeckPublic(BaseModel):
    """Public deck metadata."""

    size: int


class CreateSessionResponse(BaseModel):
    """Response body for session creation."""

    session_id: str = Field(alias="sessionId")
    spread: SpreadPublic
    deck: DeckPublic

    model_config = ConfigDict(populate_by_name=True)


class DrawnCardPublic(BaseModel):
    """Drawn card returned to the frontend."""

    id: str
    name: str
    reversed: bool
    image_url: str = Field(alias="imageUrl")
    meaning: str
    arcana: str
    element: str | None

    model_config = ConfigDict(populate_by_name=True)


class DrawCardResponse(BaseModel):
    """Response body for drawing one card."""

    position: SpreadPosition
    card: DrawnCardPublic
    verdict: YesNoAnswer | None = None
    verdict_text: str | None = Field(default=None, alias="verdictText")

    model_config = ConfigDict(populate_by_name=True)


class OkResponse(BaseModel):
    """Generic successful response for idempotent commands."""

    ok: bool = True
