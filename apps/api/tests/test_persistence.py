"""Persistence smoke tests.

Uses a dedicated sqlite file and reloads DB modules so engine binds correctly.
"""

from __future__ import annotations

import importlib

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path.as_posix()}")

    import app.core.config as config

    config.get_settings.cache_clear()
    config.settings = config.get_settings()

    import app.db.session as db_session
    import app.db.seed as seed_mod
    import app.main as main_mod

    importlib.reload(db_session)
    importlib.reload(seed_mod)
    importlib.reload(main_mod)

    await db_session.init_db()
    async with db_session.SessionLocal() as session:
        await seed_mod.seed_if_empty(session)

    transport = ASGITransport(app=main_mod.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await db_session.engine.dispose()


@pytest.mark.asyncio
async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_projects_persisted(client):
    res = await client.get("/api/projects")
    assert res.status_code == 200
    projects = res.json()
    assert any(p["id"] == "proj_sam_medical" for p in projects)

    created = await client.post(
        "/api/projects",
        json={"name": "Vision Transformers", "description": "survey"},
    )
    assert created.status_code == 200
    assert created.json()["name"] == "vision transformers"

    again = await client.get("/api/projects")
    names = [p["name"] for p in again.json()]
    assert "vision transformers" in names


@pytest.mark.asyncio
async def test_documents_and_search(client):
    docs = await client.get("/api/projects/proj_sam_medical/documents")
    assert docs.status_code == 200
    assert len(docs.json()) >= 6

    search = await client.post(
        "/api/search",
        json={"query": "medsam", "project_id": "proj_sam_medical"},
    )
    assert search.status_code == 200
    hits = search.json()
    assert hits
    assert any("MedSAM" in h["title"] for h in hits)


@pytest.mark.asyncio
async def test_graph_persisted(client):
    res = await client.get("/api/graph/proj_sam_medical")
    assert res.status_code == 200
    body = res.json()
    assert len(body["nodes"]) >= 5
    assert len(body["edges"]) >= 5
