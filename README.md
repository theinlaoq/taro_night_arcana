# Ночной аркан

Backend для интерактивного сервиса Таро.

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

## Тесты

Одна команда для локальной, Docker- и CI-проверки:

```bash
python -m pytest
```

Тесты не требуют доступной реальной LLM. Варианты LLM success, timeout,
exception и empty response проверяются через управляемые mock/stub-ответы.

## Адрес сервиса

Локальный адрес по умолчанию:

```text
http://127.0.0.1:8000
```

Документация API для dev/stage:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/openapi.json
```

## Схема запуска

Docker-образ backend не содержит Ollama, веса модели или другой LLM runtime.
Ожидаемая интеграционная схема:

```text
frontend -> Tarot backend -> локальный OpenAI-compatible LLM endpoint
```

Если Ollama запущена на той же машине без Docker, endpoint обычно такой:

```text
http://127.0.0.1:11434/v1
```

Если backend запущен в Docker, а Ollama работает на Docker host, используйте:

```text
http://host.docker.internal:11434/v1
```

Compose-файл уже добавляет `host.docker.internal:host-gateway` для Linux.
На Linux Ollama при этом должна слушать адрес, доступный из Docker, а не только
host `127.0.0.1`. Можно запустить Ollama так:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

Или запустить backend-контейнер с host network и оставить:

```text
LLM_BASE_URL=http://127.0.0.1:11434/v1
```

## Environment Variables

Создайте локальный `.env` из шаблона и меняйте runtime-настройки только там:

```bash
cp .env.example .env
```

Пример для Docker + Ollama на Docker host:

```text
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_API_KEY=local-dev-key
LLM_MODEL=qwen2.5:0.5b
LLM_TIMEOUT_SECONDS=20
SESSION_TTL_SECONDS=600
REVERSAL_PROBABILITY=0.35
```

Настоящие credentials нужно передавать только через environment variables.
Не добавляйте реальные ключи в Docker image или repository.

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker-запуск

Сборка образа:

```bash
docker build -t taro-night-arcana:integration .
```

Запуск против Ollama на Docker host. Все runtime-параметры берутся из `.env`:

```bash
docker run --rm \
  --name taro-night-arcana \
  --add-host=host.docker.internal:host-gateway \
  -p 8000:8000 \
  --env-file .env \
  taro-night-arcana:integration
```

Linux-вариант с host network, если Ollama слушает `127.0.0.1:11434`.
В `.env` при этом должно быть `LLM_BASE_URL=http://127.0.0.1:11434/v1`:

```bash
docker run --rm \
  --name taro-night-arcana \
  --network host \
  --env-file .env \
  taro-night-arcana:integration
```

Запуск через Compose. Compose тоже читает `.env`:

```bash
docker compose -f docker-compose.integration.yml up --build
```

## Smoke Checks

Health:

```bash
curl http://127.0.0.1:8000/health
```

OpenAPI:

```bash
curl http://127.0.0.1:8000/openapi.json
```

Static card:

```bash
curl -I http://127.0.0.1:8000/cards/m00.jpg
```

Create, draw, interpret, delete:

```bash
SESSION_ID=$(curl -s -X POST http://127.0.0.1:8000/api/tarot/sessions \
  -H "Content-Type: application/json" \
  -d '{"spreadId":"three","reversals":false}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['sessionId'])")

curl -s -X POST http://127.0.0.1:8000/api/tarot/sessions/$SESSION_ID/draw \
  -H "Content-Type: application/json" \
  -d '{"slot":0}'

curl -s -X POST http://127.0.0.1:8000/api/tarot/sessions/$SESSION_ID/draw \
  -H "Content-Type: application/json" \
  -d '{"slot":1}'

curl -s -X POST http://127.0.0.1:8000/api/tarot/sessions/$SESSION_ID/draw \
  -H "Content-Type: application/json" \
  -d '{"slot":2}'

curl -s -X POST http://127.0.0.1:8000/api/tarot/sessions/$SESSION_ID/interpret \
  -H "Content-Type: application/json" \
  -d '{"question":"Что важно учесть?","tone":"warm"}'

curl -s -X DELETE http://127.0.0.1:8000/api/tarot/sessions/$SESSION_ID
```

Если LLM endpoint недоступен, `interpret` возвращает успешный fallback:

```json
{"type":"basic","text":"...","reason":"LLM_UNAVAILABLE"}
```

## Замороженный API Contract

Стабильные endpoint для frontend-интеграции:

```text
POST   /api/tarot/sessions
POST   /api/tarot/sessions/{sessionId}/draw
POST   /api/tarot/sessions/{sessionId}/interpret
DELETE /api/tarot/sessions/{sessionId}
GET    /health
GET    /cards/{cardId}.jpg
GET    /docs
GET    /openapi.json
```
