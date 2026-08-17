from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import Repository
from app.db.session import get_db
from app.models.schemas import Document, Project, ProjectCreate

router = APIRouter()


@router.get("", response_model=list[Project])
async def list_projects(db: AsyncSession = Depends(get_db)) -> list[Project]:
    return await Repository(db).list_projects()


@router.post("", response_model=Project)
async def create_project(
    body: ProjectCreate, db: AsyncSession = Depends(get_db)
) -> Project:
    return await Repository(db).create_project(body.name, body.description)


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)) -> Project:
    project = await Repository(db).get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    return project


@router.get("/{project_id}/documents", response_model=list[Document])
async def list_documents(
    project_id: str, db: AsyncSession = Depends(get_db)
) -> list[Document]:
    repo = Repository(db)
    if not await repo.get_project(project_id):
        raise HTTPException(status_code=404, detail="project not found")
    return await repo.list_documents(project_id)
