

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.client_session import ClientSession
from core.config import settings
from logger import logger
import nest_asyncio
nest_asyncio.apply()

class MongoDB:
    def __init__(self, database_url: str):
        self.client = AsyncIOMotorClient(database_url)
        self.database = self.client.get_database()

    async def get_session(self) -> ClientSession:
        logger.info("MonogDB get_session..........")
        return await self.client.start_session()
        

# Create a global MongoDB instance
mongodb = MongoDB(settings.DATABASE_URL)