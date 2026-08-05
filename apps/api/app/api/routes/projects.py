from fastapi import APIRouter, HTTPException

from app.db.store import store
from app.models.schemas import Document, Project, ProjectCreate

router = APIRouter()


@router.get("", response_model=list[Project])
async def list_projects() -> list[Project]:
    return store.list_projects()


@router.post("", response_model=Project)
async def create_project(body: ProjectCreate) -> Project:
    return store.create_project(body.name, body.description)


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    return project


@router.get("/{project_id}/documents", response_model=list[Document])
async def list_documents(project_id: str) -> list[Document]:
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="project not found")
    return store.list_documents(project_id)
