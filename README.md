# Ночной аркан

Backend для интерактивного сервиса «Таро» в шоу-руме.

## Структура

```text
app/
  api/          FastAPI endpoints
  core/         настройки и общие ошибки
  data/         колода, расклады, проверка справочников
  llm/          адаптер к OpenAI-compatible API
  schemas/      Pydantic-модели request/response
  services/     бизнес-логика Таро
cards/          локальные изображения карт
tests/          автотесты
```

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Документация API после запуска:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/openapi.json
```

Интеграционная инструкция для frontend-разработчика:
[docs/INTEGRATION_HANDOFF.md](/home/alexey/Projects/taro_night_arcana/docs/INTEGRATION_HANDOFF.md)

## Тесты

Одна команда для локальной, Docker- и CI-проверки:

```bash
python -m pytest
```

Тесты не требуют доступной реальной LLM. Варианты LLM success, timeout,
exception и empty response проверяются через управляемые mock/stub-ответы.
