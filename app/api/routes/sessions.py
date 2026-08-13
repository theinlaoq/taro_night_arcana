"""Tarot session endpoints.

This file will hold the four REST endpoints from the technical specification:
- POST /api/tarot/sessions
- POST /api/tarot/sessions/{session_id}/draw
- POST /api/tarot/sessions/{session_id}/interpret
- DELETE /api/tarot/sessions/{session_id}
"""

from fastapi import APIRouter

from app.schemas.tarot import (
    CreateSessionRequest,
    CreateSessionResponse,
    DrawCardRequest,
    DrawCardResponse,
    OkResponse,
)
from app.services.tarot_service import TarotService


router = APIRouter()
tarot_service = TarotService()


@router.post("/sessions", response_model=CreateSessionResponse, response_model_by_alias=True)
async def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
    """Create a server-side tarot session."""
    return await tarot_service.create_session(
        spread_id=request.spread_id,
        reversals=request.reversals,
    )


@router.post(
    "/sessions/{session_id}/draw",
    response_model=DrawCardResponse,
    response_model_by_alias=True,
    response_model_exclude_none=True,
)
async def draw_card(session_id: str, request: DrawCardRequest) -> DrawCardResponse:
    """Draw one card from an existing tarot session."""
    return await tarot_service.draw_card(session_id=session_id, slot=request.slot)


@router.delete("/sessions/{session_id}", response_model=OkResponse)
async def delete_session(session_id: str) -> OkResponse:
    """Delete a tarot session idempotently."""
    await tarot_service.delete_session(session_id)
    return OkResponse(ok=True)
