"""Tarot session endpoints.

This file will hold the four REST endpoints from the technical specification:
- POST /api/tarot/sessions
- POST /api/tarot/sessions/{session_id}/draw
- POST /api/tarot/sessions/{session_id}/interpret
- DELETE /api/tarot/sessions/{session_id}
"""

from fastapi import APIRouter


router = APIRouter()
