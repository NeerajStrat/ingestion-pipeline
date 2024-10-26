# from db.session import mongodb
from typing import AsyncGenerator, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.client_session import ClientSession
from core.config import settings
from constants import DB_NAME
import logging
import nest_asyncio

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

import nest_asyncio
nest_asyncio.apply()

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[DB_NAME]

@asynccontextmanager
async def get_db() -> Tuple[AsyncIOMotorDatabase, object]:
# -> AsyncGenerator[Tuple[AsyncIOMotorDatabase, object], None]:
    session =  await client.start_session()
    # try:
    logging.info("Starting Session ......................")
    yield db, session
    # finally:
    #     logging.info("Ending Session.........................")
    #     await session.end_session()

if __name__ == "__main__":
    import asyncio
    asyncio.run(get_db)
