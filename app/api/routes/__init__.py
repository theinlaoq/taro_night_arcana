"""API route registry."""

from fastapi import APIRouter

from app.api.routes.sessions import router as sessions_router


router = APIRouter()
router.include_router(sessions_router, prefix="/api/tarot", tags=["tarot"])
