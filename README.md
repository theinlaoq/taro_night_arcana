# Ночной аркан

Backend для интерактивного сервиса «Таро» в шоу-руме.

Сейчас в репозитории сформирован только каркас проекта. Реализацию будем добавлять постепенно по слоям:

1. данные карт и раскладов;
2. серверные сессии;
3. REST API;
4. LLM-адаптер;
5. fallback-интерпретация;
6. static-раздача карт;
7. Docker и тесты.

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

## Тесты

Одна команда для локальной, Docker- и CI-проверки:

```bash
python -m pytest
```

Тесты не требуют доступной реальной LLM. Варианты LLM success, timeout,
exception и empty response проверяются через управляемые mock/stub-ответы.
