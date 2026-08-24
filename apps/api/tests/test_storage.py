"""Storage service tests (local backend — no MinIO required)."""

from __future__ import annotations

import importlib

import fitz
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))

    import app.core.config as config

    config.get_settings.cache_clear()
    config.settings = config.get_settings()

    import app.db.session as db_session
    import app.db.seed as seed_mod
    import app.services.storage as storage_mod
    import app.main as main_mod

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
async def test_health_reports_local_storage(client):
    res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["storage"] == "local"
    assert body["storage_mode"] == "local"


@pytest.mark.asyncio
async def test_upload_and_download_roundtrip(client):
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Callum storage integration test")
    payload = pdf.tobytes()
    pdf.close()
    files = {"file": ("medsam_notes.pdf", payload, "application/pdf")}
    data = {"project_id": "proj_sam_medical"}

    up = await client.post("/api/upload", data=data, files=files)
    assert up.status_code == 200, up.text
    doc = up.json()
    assert doc["filename"] == "medsam_notes.pdf"
    assert doc["status"] == "ready"
    assert doc["meta"]["storage_backend"] == "local"
    assert "storage_key" in doc["meta"]

    down = await client.get(f"/api/upload/{doc['id']}/content")
    assert down.status_code == 200
    assert down.content == payload
    assert "medsam_notes.pdf" in down.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_storage_unit_put_get(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))

    import app.core.config as config
    import app.services.storage as storage_mod

    config.get_settings.cache_clear()
    config.settings = config.get_settings()
    storage_mod.get_storage.cache_clear()
    importlib.reload(storage_mod)

    storage = storage_mod.get_storage()
    await storage.ensure_ready()
    stored = await storage.put_bytes(
        project_id="p1",
        document_id="d1",
        filename="paper.pdf",
        data=b"hello-callum",
        content_type="application/pdf",
    )
    assert stored.backend == "local"
    assert stored.uri.startswith("file://")
    assert await storage.exists(stored.uri)
    data, _ = await storage.get_bytes(stored.uri)
    assert data == b"hello-callum"
