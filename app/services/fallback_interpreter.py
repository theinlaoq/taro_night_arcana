"""Deterministic local interpretation used when the LLM is unavailable."""

from app.llm.base import InterpretationRequest


class FallbackInterpreter:
    """Deterministic interpreter based on local card meanings."""

    def interpret(self, request: InterpretationRequest) -> str:
        """Build a stable local reading without calling an LLM."""
        question = request.question.strip()
        if question:
            intro = f"Вы спросили: «{question}». Рассмотрим карты как метафору ситуации."
        else:
            intro = "Вопрос не задан, поэтому расклад можно читать как общий повод для самопроверки."

        card_sentences = []
        for card in request.cards:
            orientation = "перевёрнутая" if card.reversed else "прямая"
            sentence = (
                f"{card.position_name} — {card.card_name} ({orientation}): "
                f"{card.meaning}."
            )
            if card.verdict_text:
                sentence += f" Для формата да/нет это звучит как: {card.verdict_text.lower()}."
            card_sentences.append(sentence)

        middle = " ".join(card_sentences)
        closing = (
            "Это не прогноз, а способ увидеть собственные акценты чуть со стороны. "
            "Какой один маленький шаг вы готовы проверить на практике?"
        )
        return f"{intro}\n\n{middle}\n\n{closing}"
