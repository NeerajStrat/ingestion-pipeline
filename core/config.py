import os
from constants import DB_NAME

import nest_asyncio
nest_asyncio.apply()

class Settings:
    DATABASE_URL = os.environ["MONGO_URI"]+"/"+DB_NAME
    MONGO_URI = os.environ["MONGO_URI"]


settings = Settings()