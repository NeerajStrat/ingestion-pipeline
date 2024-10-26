from typing import Dict

from fastapi import APIRouter, Depends
# from app.api import deps

router = APIRouter()


@router.get("/")
async def health() -> Dict[str, str]:
    """
    Health check endpoint.
    """
    # await db.execute(text("SELECT 1"))
    return {"status": "alive"}