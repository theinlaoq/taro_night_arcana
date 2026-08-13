"""OpenAI-compatible chat completions adapter for the local LLM."""

from app.core.config import Settings
from app.llm.base import InterpretationRequest


class OpenAICompatibleTarotInterpreter:
    """Future adapter for a local OpenAI-compatible chat completions endpoint."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def interpret(self, request: InterpretationRequest) -> str | None:
        """Call the configured LLM gateway.

        The real HTTP implementation belongs to the LLM task. For the first
        task we only establish the replaceable boundary required by the spec.
        """
        _ = (self._settings, request)
        return None
