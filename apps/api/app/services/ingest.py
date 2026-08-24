import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import Repository
from app.models.schemas import DocumentModality
from app.services.parsers import ParseError, parse_document
from app.services.storage import get_storage

EXT_MAP = {
    ".pdf": DocumentModality.pdf,
    ".png": DocumentModality.image,
    ".jpg": DocumentModality.image,
    ".jpeg": DocumentModality.image,
    ".webp": DocumentModality.image,
    ".gif": DocumentModality.image,
    ".mp4": DocumentModality.video,
    ".mov": DocumentModality.video,
    ".mp3": DocumentModality.audio,
    ".wav": DocumentModality.audio,
    ".m4a": DocumentModality.audio,
    ".csv": DocumentModality.dataset,
    ".xlsx": DocumentModality.dataset,
    ".xls": DocumentModality.dataset,
    ".md": DocumentModality.markdown,
    ".markdown": DocumentModality.markdown,
    ".py": DocumentModality.code,
    ".ipynb": DocumentModality.code,
    ".ppt": DocumentModality.slides,
    ".pptx": DocumentModality.slides,
}


def detect_modality(filename: str, content_type: str | None = None) -> DocumentModality:
    ext = Path(filename).suffix.lower()
    if ext in EXT_MAP:
        return EXT_MAP[ext]
    if content_type:
        if content_type.startswith("image/"):
            return DocumentModality.image
        if content_type.startswith("video/"):
            return DocumentModality.video
        if content_type.startswith("audio/"):
            return DocumentModality.audio
        if content_type == "application/pdf":
            return DocumentModality.pdf
    return DocumentModality.unknown


async def enqueue_ingest(session: AsyncSession, document_id: str) -> None:
    """Parse a stored document and persist citation-ready extraction output.

    This runs inline for now. Step 12 moves the same idempotent operation to Celery.
    """
    repo = Repository(session)
    doc = await repo.get_document(document_id)
    if not doc:
        return
    await repo.update_document(document_id, status="processing")
    storage_path = await repo.get_document_storage_path(document_id)
    if not storage_path:
        await repo.update_document(
            document_id,
            status="failed",
            meta={**doc.meta, "ingest_error": "document has no stored object"},
        )
        return

    try:
        data, _ = await get_storage().get_bytes(storage_path)
        parsed = await asyncio.to_thread(parse_document, data, doc.filename, doc.modality)

        asset_rows: list[dict] = []
        for asset in parsed.assets:
            stored = await get_storage().put_bytes(
                project_id=doc.project_id,
                document_id=doc.id,
                filename=asset.filename,
                data=asset.data,
                content_type=asset.content_type,
            )
            asset_rows.append(
                {
                    "page_number": asset.page_number,
                    "kind": asset.kind,
                    "filename": asset.filename,
                    "content_type": asset.content_type,
                    "storage_path": stored.uri,
                    "width": asset.width,
                    "height": asset.height,
                    "meta": asset.meta,
                }
            )

        await repo.replace_extraction(
            document_id,
            pages=[
                {
                    "page_number": page.page_number,
                    "text": page.text,
                    "width": page.width,
                    "height": page.height,
                    "image_count": page.image_count,
                    "meta": page.meta,
                }
                for page in parsed.pages
            ],
            chunks=[
                {
                    "ordinal": chunk.ordinal,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "section": chunk.section,
                    "text": chunk.text,
                    "char_count": len(chunk.text),
                    "token_estimate": max(1, len(chunk.text) // 4),
                    "meta": chunk.meta,
                }
                for chunk in parsed.chunks
            ],
            references=[
                {
                    "ordinal": reference.ordinal,
                    "raw_text": reference.raw_text,
                    "title": reference.title,
                    "doi": reference.doi,
                    "url": reference.url,
                    "meta": {},
                }
                for reference in parsed.references
            ],
            assets=asset_rows,
        )
        await repo.update_document(
            document_id,
            status="ready",
            title=parsed.title or doc.title,
            authors=parsed.authors or doc.authors,
            abstract=parsed.abstract or doc.abstract,
            meta={
                **doc.meta,
                **parsed.meta,
                "ingest_status": "complete",
                "ingest_error": None,
            },
        )
    except ParseError as exc:
        status = "pending_parser" if str(exc).startswith("no parser is available") else "failed"
        await repo.update_document(
            document_id,
            status=status,
            meta={
                **doc.meta,
                "ingest_status": status,
                "ingest_error": str(exc),
            },
        )
    except Exception as exc:  # noqa: BLE001 - ingestion is a failure boundary
        await repo.update_document(
            document_id,
            status="failed",
            meta={
                **doc.meta,
                "ingest_status": "failed",
                "ingest_error": f"{type(exc).__name__}: {exc}",
            },
        )
