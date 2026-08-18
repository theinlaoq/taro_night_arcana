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
frontend/       статическая HTML-сборка frontend
deploy/         reverse proxy конфигурация
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

Локальный адрес backend по умолчанию:

```text
http://127.0.0.1:8000
```

Полный frontend + backend stack при запуске через production compose:

```text
http://127.0.0.1:8080
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
HTTP_PORT=8080
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8080,http://localhost:8080
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=local-dev-key
LLM_MODEL=qwen2.5:1.5b
LLM_TIMEOUT_SECONDS=20
SESSION_TTL_SECONDS=600
REVERSAL_PROBABILITY=0.35
```

Для полного `docker-compose.prod.yml`, где backend работает внутри Docker
network, локальная Ollama на хост-машине должна указываться так:

```text
LLM_BASE_URL=http://host.docker.internal:11434/v1
```

Настоящие credentials нужно передавать только через environment variables.
Не добавляйте реальные ключи в Docker image или repository.

После изменения `.env` backend/container нужно перезапустить.

`CORS_ORIGINS` должен содержать origin frontend-разработчика. Для локальной
статической проверки из папки `frontend` обычно достаточно:

```text
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

Для сервера `dev.tarot.g-309.ru` production-настройки будут такими:

```text
HTTP_PORT=80
CORS_ORIGINS=http://dev.tarot.g-309.ru
LLM_BASE_URL=https://llm-server.example/v1
LLM_API_KEY=...
LLM_MODEL=...
```

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

## Полный Stack Через Compose

Этот вариант поднимает frontend, backend и nginx reverse proxy одной командой.
Локально nginx отдаёт сайт на `http://127.0.0.1:8080`.

Если LLM/Ollama запущена на этой же машине, в `.env` для этого режима укажите:

```text
LLM_BASE_URL=http://host.docker.internal:11434/v1
```

```bash
docker compose -f docker-compose.prod.yml up --build
```

Для фонового запуска на сервере:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

На сервере с доменом `dev.tarot.g-309.ru` nginx будет принимать обычный HTTP
и проксировать:

```text
/              -> frontend
/api/tarot/... -> backend
/cards/...     -> backend
/health        -> backend
/docs          -> backend
/openapi.json  -> backend
```

Frontend использует относительные запросы к `/api/tarot/...`, поэтому на домене
ему не нужен адрес `127.0.0.1:8000`.

Frontend runtime-зависимости, которые раньше могли грузиться с CDN, лежат
локально в `frontend/vendor/`. Поэтому штатный пользовательский сценарий не
требует внешних CDN.

## Локальная проверка frontend без Docker

В папке `frontend` лежит статическая HTML-сборка. После запуска backend можно
поднять простой static server:

```bash
cd frontend
python3 -m http.server 5173
```

Откройте:

```text
http://127.0.0.1:5173/Ночной%20Аркан.dc.html
```

Файл `tarot-backend-connector.js` по умолчанию обращается к тому же origin:

```text
/api/tarot/...
```

Для удобства локальной разработки есть исключение: если frontend открыт на
`http://127.0.0.1:5173` или `http://localhost:5173`, connector автоматически
ходит в backend на `http://127.0.0.1:8000`.

Если frontend запускается отдельно от backend на другом адресе и без
nginx/reverse proxy, до загрузки connector можно задать:

```html
<script>window.TAROT_BACKEND_URL = "http://backend-host:8000";</script>
```

## Smoke Checks

Health:

```bash
curl http://127.0.0.1:8000/health
```

Ответ:

```json
{"status":"ok","llm":"available"}
```

или, если LLM endpoint недоступен:

```json
{"status":"ok","llm":"unavailable"}
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

## Известные ограничения

- Сессии хранятся в памяти одного backend-процесса. При рестарте контейнера
  активные расклады сбрасываются.
- Full-stack compose собирает отдельные образы backend и frontend. Локальная
  LLM запускается отдельно и подключается через `LLM_BASE_URL`.
- Качество `type=ai` зависит от выбранной локальной модели. Если endpoint
  недоступен, отвечает с ошибкой, timeout или пустым ответом, backend возвращает
  deterministic fallback `type=basic`.
- После заморозки API contract изменения endpoint, полей request/response и
  кодов ошибок нужно согласовывать с frontend-разработчиком.
