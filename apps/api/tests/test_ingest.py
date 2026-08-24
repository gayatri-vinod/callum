"""PDF parsing and citation-ready ingestion tests."""

from __future__ import annotations

import base64
import importlib

import fitz
import pytest
from httpx import ASGITransport, AsyncClient

from app.services.parsers import ParseError, parse_pdf

_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def research_pdf() -> bytes:
    pdf = fitz.open()
    page1 = pdf.new_page()
    page1.insert_text((72, 72), "A Reliable Medical Segmentation Study", fontsize=18)
    page1.insert_text(
        (72, 110),
        "Abstract\n"
        "We evaluate a robust segmentation method across three clinical datasets.\n"
        "Keywords: segmentation, medicine\n"
        "1 Introduction\n"
        "Medical image segmentation requires reproducible evaluation and strong baselines.",
        fontsize=11,
    )
    page1.insert_image(fitz.Rect(72, 250, 140, 318), stream=_PNG_1X1)

    page2 = pdf.new_page()
    page2.insert_text(
        (72, 72),
        "2 Methods\n"
        "Our method uses a prompt encoder and a frozen visual backbone.\n\n"
        "3 Results\n"
        "The model improves Dice while using less annotation time.\n\n"
        "References\n"
        "[1] A. Author. Segment Anything. https://doi.org/10.1000/sam.2023\n"
        "[2] B. Author. U-Net. https://example.org/unet",
        fontsize=11,
    )
    pdf.set_metadata(
        {
            "title": "Reliable Medical Segmentation",
            "author": "Ada Researcher; Ben Scientist",
            "subject": "medical imaging",
        }
    )
    data = pdf.tobytes()
    pdf.close()
    return data


def test_parse_pdf_extracts_grounded_structure():
    parsed = parse_pdf(research_pdf(), "paper.pdf")
    assert parsed.title == "Reliable Medical Segmentation"
    assert parsed.authors == ["Ada Researcher", "Ben Scientist"]
    assert parsed.abstract and "three clinical datasets" in parsed.abstract
    assert len(parsed.pages) == 2
    assert parsed.pages[0].page_number == 1
    assert parsed.pages[0].image_count >= 1
    assert parsed.chunks
    assert all(chunk.page_start >= 1 for chunk in parsed.chunks)
    assert any(chunk.section == "methods" for chunk in parsed.chunks)
    assert len(parsed.references) == 2
    assert parsed.references[0].doi == "10.1000/sam.2023"
    assert parsed.assets
    assert parsed.meta["parser"] == "pymupdf"


def test_parse_pdf_rejects_invalid_bytes():
    with pytest.raises(ParseError, match="invalid or unreadable PDF"):
        parse_pdf(b"not a pdf", "broken.pdf")


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))

    from app.core import config

    config.get_settings.cache_clear()
    config.settings = config.get_settings()

    import app.db.seed as seed_mod
    import app.db.session as db_session
    import app.main as main_mod
    import app.services.storage as storage_mod

    storage_mod.get_storage.cache_clear()
    importlib.reload(db_session)
    importlib.reload(seed_mod)
    importlib.reload(storage_mod)
    importlib.reload(main_mod)

    await db_session.init_db()
    async with db_session.SessionLocal() as session:
        await seed_mod.seed_if_empty(session)
    await storage_mod.get_storage().ensure_ready()

    transport = ASGITransport(app=main_mod.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await db_session.engine.dispose()
    storage_mod.get_storage.cache_clear()


@pytest.mark.asyncio
async def test_pdf_upload_persists_extraction(client):
    upload = await client.post(
        "/api/upload",
        data={"project_id": "proj_sam_medical"},
        files={"file": ("study.pdf", research_pdf(), "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    document = upload.json()
    assert document["status"] == "ready"
    assert document["title"] == "Reliable Medical Segmentation"
    assert document["meta"]["page_count"] == 2
    assert document["meta"]["reference_count"] == 2

    response = await client.get(
        f"/api/projects/proj_sam_medical/documents/{document['id']}/extraction"
    )
    assert response.status_code == 200, response.text
    extraction = response.json()
    assert len(extraction["pages"]) == 2
    assert extraction["chunks"]
    assert extraction["references"][0]["doi"] == "10.1000/sam.2023"
    assert extraction["assets"]

    asset_id = extraction["assets"][0]["id"]
    asset = await client.get(f"/api/upload/assets/{asset_id}/content")
    assert asset.status_code == 200
    assert asset.headers["content-type"].startswith("image/")


@pytest.mark.asyncio
async def test_invalid_pdf_is_marked_failed(client):
    upload = await client.post(
        "/api/upload",
        data={"project_id": "proj_sam_medical"},
        files={"file": ("broken.pdf", b"not a pdf", "application/pdf")},
    )
    assert upload.status_code == 200
    document = upload.json()
    assert document["status"] == "failed"
    assert "invalid or unreadable PDF" in document["meta"]["ingest_error"]
