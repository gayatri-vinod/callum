from fastapi import APIRouter, HTTPException

from app.db.store import store
from app.models.schemas import KnowledgeGraph

router = APIRouter()


@router.get("/{project_id}", response_model=KnowledgeGraph)
async def get_graph(project_id: str) -> KnowledgeGraph:
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="project not found")
    return store.knowledge_graph(project_id)
