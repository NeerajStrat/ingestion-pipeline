import os
from constants import DB_NAME

import nest_asyncio
nest_asyncio.apply()

class Settings:
    DATABASE_URL = os.environ["MONGODB_URI"]+"/"+DB_NAME
    MONGODB_URI = os.environ["MONGODB_URI"]


settings = Settings()