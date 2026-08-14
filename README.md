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

Если команда ниже отвечает JSON, Ollama уже запущена:

```bash
curl http://127.0.0.1:11434/v1/models
```

Если `ollama serve` пишет `bind: address already in use`, это обычно значит,
что Ollama уже запущена как сервис. Запускать второй server не нужно.

Проверить скачанные модели:

```bash
ollama list
```

Проверить модели, загруженные в память:

```bash
ollama ps
```

Для Linux-разработки backend-контейнер запускается с host network, поэтому
в `.env` можно оставить:

```text
LLM_BASE_URL=http://127.0.0.1:11434/v1
```

## Environment Variables

Создайте локальный `.env` из шаблона и меняйте runtime-настройки только там:

```bash
cp .env.example .env
```

Пример для Linux + Docker host network + Ollama на той же машине:

```text
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=local-dev-key
LLM_MODEL=qwen2.5:1.5b
LLM_TIMEOUT_SECONDS=20
LLM_VALIDATE_RESPONSES=true
SESSION_TTL_SECONDS=600
REVERSAL_PROBABILITY=0.35
```

Настоящие credentials нужно передавать только через environment variables.
Не добавляйте реальные ключи в Docker image или repository.

`LLM_VALIDATE_RESPONSES=true` включает проверку качества LLM-ответа. Если модель
отвечает слишком коротко, не упоминает выпавшие карты или нарушает формат,
backend вернёт fallback. Для отладки маленьких локальных моделей можно временно
поставить:

```text
LLM_VALIDATE_RESPONSES=false
```

После изменения `.env` backend/container нужно перезапустить.

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

Запуск через Docker. Все runtime-параметры берутся из `.env`:

```bash
docker run --rm \
  --name taro-night-arcana \
  --network host \
  --env-file .env \
  taro-night-arcana:integration
```

Запуск через Compose. Compose тоже читает `.env` и использует host network:

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
  | python3 -c "import sys,json; print(json.load(sys.stdin)['sessionId'])")
echo $SESSION_ID

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
