from fastapi import APIRouter

from api.endpoints import ingestion, health

api_router = APIRouter()
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
api_router.include_router(health.router, prefix="/health", tags=["health"])