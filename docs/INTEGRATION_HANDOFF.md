# Night Arcana Backend Integration Handoff

## Service Address

Default local address:

```text
http://127.0.0.1:8000
```

Dev API documentation:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/openapi.json
```

## Runtime Topology

The backend image does not contain Ollama, model weights, or any other LLM
runtime. The expected integration topology is:

```text
frontend -> Tarot backend -> local OpenAI-compatible LLM endpoint
```

For Ollama on the same host, the LLM endpoint is usually:

```text
http://127.0.0.1:11434/v1
```

When the backend runs inside Docker and Ollama runs on the Docker host, use:

```text
http://host.docker.internal:11434/v1
```

The Compose file already adds `host.docker.internal:host-gateway` for Linux.
On Linux, this requires Ollama to listen on an address reachable from Docker,
not only on host `127.0.0.1`. Either start Ollama with a wider bind address:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

or run the backend container with host networking and keep
`LLM_BASE_URL=http://127.0.0.1:11434/v1`.

## Environment Variables

```text
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_API_KEY=local-dev-key
LLM_MODEL=qwen2.5:0.5b
LLM_TIMEOUT_SECONDS=20
SESSION_TTL_SECONDS=600
REVERSAL_PROBABILITY=0.35
```

Credentials must be provided through environment variables. Do not bake real
keys into the image or commit them to the repository.

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Docker Run

Build:

```bash
docker build -t taro-night-arcana:integration .
```

Run against Ollama on the Docker host:

```bash
docker run --rm \
  --name taro-night-arcana \
  --add-host=host.docker.internal:host-gateway \
  -p 8000:8000 \
  -e LLM_BASE_URL=http://host.docker.internal:11434/v1 \
  -e LLM_API_KEY=local-dev-key \
  -e LLM_MODEL=qwen2.5:0.5b \
  taro-night-arcana:integration
```

Linux host-network variant against Ollama on `127.0.0.1:11434`:

```bash
docker run --rm \
  --name taro-night-arcana \
  --network host \
  -e LLM_BASE_URL=http://127.0.0.1:11434/v1 \
  -e LLM_API_KEY=local-dev-key \
  -e LLM_MODEL=qwen2.5:0.5b \
  taro-night-arcana:integration
```

Or with Compose:

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

If the LLM endpoint is unavailable, `interpret` returns a successful fallback:

```json
{"type":"basic","text":"...","reason":"LLM_UNAVAILABLE"}
```

## Frozen API Contract

Stable endpoints for frontend integration:

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

After handoff, API contract changes should be coordinated with the frontend
developer.

## Known Limits

- Sessions are stored in memory of one backend process.
- No user accounts, history, PostgreSQL, Redis, analytics, sound, or sharing.
- LLM quality depends on the model configured behind the OpenAI-compatible
  endpoint. Fallback keeps the user flow working if the model is unavailable.
