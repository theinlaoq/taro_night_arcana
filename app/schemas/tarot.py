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
