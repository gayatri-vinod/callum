from pathlib import Path

from app.db.store import store
from app.models.schemas import DocumentModality

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


async def enqueue_ingest(document_id: str) -> None:
    """Mark document processing. Celery workers will own the real pipeline."""
    doc = store.documents.get(document_id)
    if not doc:
        return
    doc.status = "processing"
    # Local MVP: instant ready. Production: parse → extract → embed → graph.
    doc.status = "ready"
    if not doc.abstract:
        doc.abstract = "queued for multimodal parse, figure/table/equation extraction, and indexing."
