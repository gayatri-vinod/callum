from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.repository import Repository
from app.db.session import get_db
from app.models.schemas import Document
from app.services.ingest import detect_modality, enqueue_ingest

router = APIRouter()


@router.post("", response_model=Document)
async def upload_document(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> Document:
    repo = Repository(db)
    if not await repo.get_project(project_id):
        raise HTTPException(status_code=404, detail="project not found")

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"file exceeds {settings.max_upload_mb}mb")

    modality = detect_modality(file.filename or "upload.bin", file.content_type)
    filename = file.filename or "upload.bin"
    title = Path(filename).stem.replace("_", " ")

    # Persist row first to get id, then write file with that id
    doc = await repo.add_document(
        project_id=project_id,
        filename=filename,
        modality=modality,
        content_type=file.content_type,
        size_bytes=len(data),
        status="queued",
        title=title,
    )

    upload_root = Path(settings.upload_dir) / project_id
    upload_root.mkdir(parents=True, exist_ok=True)
    dest = upload_root / f"{doc.id}_{doc.filename}"
    async with aiofiles.open(dest, "wb") as f:
        await f.write(data)

    await repo.update_document(doc.id, storage_path=str(dest))
    await enqueue_ingest(db, doc.id)
    updated = await repo.get_document(doc.id)
    return updated or doc
