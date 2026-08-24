from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.repository import Repository
from app.db.session import get_db
from app.models.schemas import Document
from app.services.ingest import detect_modality, enqueue_ingest
from app.services.storage import StorageError, content_disposition, get_storage

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

    doc = await repo.add_document(
        project_id=project_id,
        filename=filename,
        modality=modality,
        content_type=file.content_type,
        size_bytes=len(data),
        status="queued",
        title=title,
    )

    storage = get_storage()
    try:
        stored = await storage.put_bytes(
            project_id=project_id,
            document_id=doc.id,
            filename=filename,
            data=data,
            content_type=file.content_type,
        )
    except Exception as exc:
        await repo.update_document(doc.id, status="failed")
        raise HTTPException(status_code=502, detail=f"storage upload failed: {exc}") from exc

    meta = dict(doc.meta or {})
    meta["storage_backend"] = stored.backend
    meta["storage_key"] = stored.key

    await repo.update_document(
        doc.id,
        storage_path=stored.uri,
        meta=meta,
    )
    await enqueue_ingest(db, doc.id)
    updated = await repo.get_document(doc.id)
    return updated or doc


@router.get("/{document_id}/content")
async def download_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    repo = Repository(db)
    doc = await repo.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")

    # storage_path lives on the ORM row; re-fetch via repository internals
    from app.db.models import DocumentRow

    row = await db.get(DocumentRow, document_id)
    if not row or not row.storage_path:
        raise HTTPException(status_code=404, detail="file not stored yet")

    storage = get_storage()
    try:
        data, content_type = await storage.get_bytes(row.storage_path)
    except StorageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    media = content_type or row.content_type or "application/octet-stream"
    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": content_disposition(row.filename)},
    )


@router.get("/assets/{asset_id}/content")
async def download_extracted_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    from app.db.models import DocumentAssetRow

    asset = await db.get(DocumentAssetRow, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="asset not found")
    try:
        data, content_type = await get_storage().get_bytes(asset.storage_path)
    except StorageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=data,
        media_type=content_type or asset.content_type,
        headers={"Content-Disposition": content_disposition(asset.filename)},
    )
