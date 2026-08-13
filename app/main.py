"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.errors import ErrorCode, TarotError


app = FastAPI(title="Night Arcana Tarot API")
app.include_router(api_router)
app.mount("/cards", StaticFiles(directory="cards"), name="cards")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health endpoint required by the showroom integration"""
    return {"status": "ok"}


@app.exception_handler(TarotError)
async def tarot_error_handler(_: object, exc: TarotError) -> JSONResponse:
    """Serialize domain errors with the frontend/backend error contract"""
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "message": exc.message},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: object, exc: RequestValidationError) -> JSONResponse:
    """Return FastAPI validation errors with the agreed top-level shape"""
    return JSONResponse(
        status_code=422,
        content={"code": ErrorCode.VALIDATION_ERROR, "message": str(exc)},
    )


@app.exception_handler(Exception)
async def unknown_error_handler(_: object, exc: Exception) -> JSONResponse:
    """Keep unexpected errors inside the same top-level error envelope"""
    return JSONResponse(
        status_code=500,
        content={"code": ErrorCode.UNKNOWN_ERROR, "message": str(exc) or "Unknown error"},
    )
