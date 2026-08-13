"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.routes import router as api_router


app = FastAPI(title="Night Arcana Tarot API")
app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health endpoint required by the showroom integration."""
    return {"status": "ok"}
