from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import Repository
from app.db.session import get_db
from app.models.schemas import SearchHit, SearchRequest

router = APIRouter()


@router.post("", response_model=list[SearchHit])
async def search(
    body: SearchRequest, db: AsyncSession = Depends(get_db)
) -> list[SearchHit]:
    return await Repository(db).search(
        body.query, project_id=body.project_id, limit=body.limit
    )
