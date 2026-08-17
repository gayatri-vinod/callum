from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import Repository
from app.db.session import get_db
from app.models.schemas import KnowledgeGraph

router = APIRouter()


@router.get("/{project_id}", response_model=KnowledgeGraph)
async def get_graph(
    project_id: str, db: AsyncSession = Depends(get_db)
) -> KnowledgeGraph:
    repo = Repository(db)
    if not await repo.get_project(project_id):
        raise HTTPException(status_code=404, detail="project not found")
    return await repo.knowledge_graph(project_id)
