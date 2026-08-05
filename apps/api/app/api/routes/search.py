from fastapi import APIRouter

from app.db.store import store
from app.models.schemas import SearchHit, SearchRequest

router = APIRouter()


@router.post("", response_model=list[SearchHit])
async def search(body: SearchRequest) -> list[SearchHit]:
    return store.search(body.query, project_id=body.project_id, limit=body.limit)
