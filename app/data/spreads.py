"""Supported tarot spreads transferred from the frontend mock."""

from app.schemas.tarot import SpreadDefinition


SPREADS = {
    "day": SpreadDefinition(id="day", name="Карта дня", positions=("Сегодня",)),
    "yesno": SpreadDefinition(id="yesno", name="Да / Нет", positions=("Ответ",), yesno=True),
    "three": SpreadDefinition(
        id="three",
        name="Три карты",
        positions=("Прошлое", "Настоящее", "Будущее"),
    ),
    "relationships": SpreadDefinition(
        id="relationships",
        name="Отношения",
        positions=("Вы", "Партнёр", "Что вас связывает", "Что мешает", "Куда это идёт"),
    ),
    "celtic": SpreadDefinition(
        id="celtic",
        name="Кельтский крест",
        positions=(
            "Суть",
            "Что пересекает",
            "Основа",
            "Прошлое",
            "Цель",
            "Ближайшее будущее",
            "Вы сами",
            "Окружение",
            "Надежды и страхи",
            "Итог",
        ),
    ),
}

# The current frontend mock uses these legacy IDs. Keep the production reference
# set to five spreads while allowing the service layer to normalize old IDs.
SPREAD_ALIASES = {
    "love": "relationships",
    "cross": "celtic",
}


def resolve_spread_id(spread_id: str) -> str:
    """Return the canonical production spread ID for a frontend spread ID."""
    return SPREAD_ALIASES.get(spread_id, spread_id)
