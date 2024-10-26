from typing import Dict, List, Tuple
from fastapi import APIRouter, Depends
from pipeline import pipeline
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from api.deps import get_db
from logger import logger

router = APIRouter()


# Define the Pydantic model for the request body
class IngestionPayload(BaseModel):
    tickers: List[str]  # A list of strings

@router.post("/")
async def ingestion(
    payload: IngestionPayload, 
    db_session: Tuple[AsyncIOMotorDatabase, object] = Depends(get_db)):
    # Access the list of strings from the payload
    tickers = payload.tickers
    """
    Health check endpoint.
    """
    try:
        await pipeline(tickers=tickers, db_session=db_session)
    except Exception as e:
        logger.debug("error {}".format(e))
        return {"status": "Failed"}
    return {"status": "Successful"}