from fastapi import FastAPI
from api.api import api_router
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from logger import logger

app = FastAPI(
    title="FinAILLM",
    swagger_ui_parameters={"syntaxHighlight": False}
    # openapi_url=f"{settings.API_PREFIX}/openapi.json",
    # lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)
app.include_router(api_router, prefix="/api")

def start():
    print("Running in AppEnvironment: " + "Dev")
    # __setup_logging(settings.LOG_LEVEL)
    
    """Launched with `poetry run start` at root level"""
    # if settings.RENDER:
    #     # on render.com deployments, run migrations
    #     logger.debug("Running migrations")
    #     alembic_args = ["--raiseerr", "upgrade", "head"]
    #     alembic.config.main(argv=alembic_args)
    #     logger.debug("Migrations complete")
    # else:
    #     logger.debug("Skipping migrations")
    # live_reload = not settings.RENDER
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,
    )

if __name__ == "__main__":
    start()
