from pathlib import Path

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.db.store import store
from app.models.schemas import Document, DocumentModality
from app.services.ingest import detect_modality, enqueue_ingest

router = APIRouter()


@router.post("", response_model=Document)
async def upload_document(
    project_id: str = Form(...),
    file: UploadFile = File(...),
) -> Document:
    if not store.get_project(project_id):
        raise HTTPException(status_code=404, detail="project not found")

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"file exceeds {settings.max_upload_mb}mb")

    modality = detect_modality(file.filename or "upload.bin", file.content_type)
    doc = Document(
        project_id=project_id,
        filename=file.filename or "upload.bin",
        modality=modality,
        content_type=file.content_type,
        size_bytes=len(data),
        status="queued",
        title=Path(file.filename or "upload").stem.replace("_", " "),
    )

    upload_root = Path(settings.upload_dir) / project_id
    upload_root.mkdir(parents=True, exist_ok=True)
    dest = upload_root / f"{doc.id}_{doc.filename}"
    async with aiofiles.open(dest, "wb") as f:
        await f.write(data)

    store.add_document(doc)
    await enqueue_ingest(doc.id)
    return doc
