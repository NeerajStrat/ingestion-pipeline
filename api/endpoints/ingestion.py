from typing import Dict, List, Tuple
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from api.deps import get_db
from sse_starlette.sse import EventSourceResponse
import constants
from logger import logger
import download_sec_docs
from api.crud import async_upsert_documents_from_filings
from pymongo import ASCENDING

router = APIRouter()


# Define the Pydantic model for the request body
class IngestionPayload(BaseModel):
    tickers: List[str]  # A list of strings

@router.post("/")
async def ingestion(
    payload: IngestionPayload, 
    db_session: Tuple[AsyncIOMotorDatabase, object] = Depends(get_db)):
    tickers = payload.tickers

    async def event_publisher():
        async with db_session as (db, session):
            
            download_sec_docs.sec_download(ciks = tickers)

            collection = db.get_collection(constants.COLLECTION_NAME)
            await collection.create_index([("url", ASCENDING)], unique=True)
            async for event in async_upsert_documents_from_filings(tickers, collection):
                yield event

    return EventSourceResponse(event_publisher())
