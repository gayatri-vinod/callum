from fastapi import APIRouter

from app.core.config import settings
from app.services.storage import get_storage

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    storage = get_storage()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        "database": "sqlite" if settings.database_url.startswith("sqlite") else "postgres",
        "storage": storage.backend_name,
        "storage_mode": settings.storage_backend,
    }
