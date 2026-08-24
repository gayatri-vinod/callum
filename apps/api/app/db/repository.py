from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    DocumentAssetRow,
    DocumentChunkRow,
    DocumentPageRow,
    DocumentReferenceRow,
    DocumentRow,
    GraphEdgeRow,
    GraphNodeRow,
    ProjectRow,
)
from app.models.schemas import (
    Document,
    DocumentAsset,
    DocumentChunk,
    DocumentExtraction,
    DocumentModality,
    DocumentPage,
    DocumentReference,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    Project,
    SearchHit,
)


def _dt(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def project_to_schema(row: ProjectRow, document_count: int = 0) -> Project:
    return Project(
        id=row.id,
        name=row.name,
        description=row.description or "",
        created_at=_dt(row.created_at),
        updated_at=_dt(row.updated_at),
        document_count=document_count,
        status=row.status,
    )


def document_to_schema(row: DocumentRow) -> Document:
    modality = row.modality
    try:
        modality_enum = DocumentModality(modality)
    except ValueError:
        modality_enum = DocumentModality.unknown
    return Document(
        id=row.id,
        project_id=row.project_id,
        filename=row.filename,
        modality=modality_enum,
        content_type=row.content_type,
        size_bytes=row.size_bytes or 0,
        status=row.status,
        title=row.title,
        authors=list(row.authors or []),
        abstract=row.abstract,
        created_at=_dt(row.created_at),
        meta=dict(row.meta or {}),
    )


class Repository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_projects(self) -> list[Project]:
        result = await self.session.execute(
            select(ProjectRow).order_by(ProjectRow.updated_at.desc())
        )
        rows = result.scalars().all()
        projects: list[Project] = []
        for row in rows:
            count = await self._document_count(row.id)
            projects.append(project_to_schema(row, count))
        return projects

    async def get_project(self, project_id: str) -> Project | None:
        row = await self.session.get(ProjectRow, project_id)
        if not row:
            return None
        count = await self._document_count(row.id)
        return project_to_schema(row, count)

    async def create_project(self, name: str, description: str = "") -> Project:
        row = ProjectRow(
            name=name.lower().strip(),
            description=description.strip(),
            status="active",
        )
        self.session.add(row)
        await self.session.flush()
        return project_to_schema(row, 0)

    async def list_documents(self, project_id: str) -> list[Document]:
        result = await self.session.execute(
            select(DocumentRow)
            .where(DocumentRow.project_id == project_id)
            .order_by(DocumentRow.created_at.desc())
        )
        return [document_to_schema(row) for row in result.scalars().all()]

    async def get_document(self, document_id: str) -> Document | None:
        row = await self.session.get(DocumentRow, document_id)
        return document_to_schema(row) if row else None

    async def get_document_storage_path(self, document_id: str) -> str | None:
        row = await self.session.get(DocumentRow, document_id)
        return row.storage_path if row else None

    async def add_document(
        self,
        *,
        project_id: str,
        filename: str,
        modality: DocumentModality | str,
        content_type: str | None = None,
        size_bytes: int = 0,
        status: str = "queued",
        title: str | None = None,
        authors: list[str] | None = None,
        abstract: str | None = None,
        storage_path: str | None = None,
        meta: dict | None = None,
        document_id: str | None = None,
    ) -> Document:
        payload = {
            "project_id": project_id,
            "filename": filename,
            "modality": modality.value if isinstance(modality, DocumentModality) else modality,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "status": status,
            "title": title,
            "authors": authors or [],
            "abstract": abstract,
            "storage_path": storage_path,
            "meta": meta or {},
        }
        if document_id:
            payload["id"] = document_id
        row = DocumentRow(**payload)
        self.session.add(row)

        project = await self.session.get(ProjectRow, project_id)
        if project:
            project.updated_at = datetime.now(UTC)

        await self.session.flush()
        return document_to_schema(row)

    async def replace_extraction(
        self,
        document_id: str,
        *,
        pages: list[dict],
        chunks: list[dict],
        references: list[dict],
        assets: list[dict],
    ) -> None:
        """Atomically replace all deterministic extraction output for a document."""
        for model in (
            DocumentPageRow,
            DocumentChunkRow,
            DocumentReferenceRow,
            DocumentAssetRow,
        ):
            await self.session.execute(delete(model).where(model.document_id == document_id))

        self.session.add_all([DocumentPageRow(document_id=document_id, **page) for page in pages])
        self.session.add_all(
            [DocumentChunkRow(document_id=document_id, **chunk) for chunk in chunks]
        )
        self.session.add_all(
            [DocumentReferenceRow(document_id=document_id, **reference) for reference in references]
        )
        self.session.add_all(
            [DocumentAssetRow(document_id=document_id, **asset) for asset in assets]
        )
        await self.session.flush()

    async def get_extraction(self, document_id: str) -> DocumentExtraction | None:
        document = await self.get_document(document_id)
        if not document:
            return None
        page_result = await self.session.execute(
            select(DocumentPageRow)
            .where(DocumentPageRow.document_id == document_id)
            .order_by(DocumentPageRow.page_number)
        )
        chunk_result = await self.session.execute(
            select(DocumentChunkRow)
            .where(DocumentChunkRow.document_id == document_id)
            .order_by(DocumentChunkRow.ordinal)
        )
        reference_result = await self.session.execute(
            select(DocumentReferenceRow)
            .where(DocumentReferenceRow.document_id == document_id)
            .order_by(DocumentReferenceRow.ordinal)
        )
        asset_result = await self.session.execute(
            select(DocumentAssetRow)
            .where(DocumentAssetRow.document_id == document_id)
            .order_by(DocumentAssetRow.page_number, DocumentAssetRow.id)
        )
        return DocumentExtraction(
            document=document,
            pages=[
                DocumentPage(
                    id=row.id,
                    document_id=row.document_id,
                    page_number=row.page_number,
                    text=row.text,
                    width=row.width,
                    height=row.height,
                    image_count=row.image_count,
                    meta=dict(row.meta or {}),
                )
                for row in page_result.scalars().all()
            ],
            chunks=[
                DocumentChunk(
                    id=row.id,
                    document_id=row.document_id,
                    ordinal=row.ordinal,
                    page_start=row.page_start,
                    page_end=row.page_end,
                    section=row.section,
                    text=row.text,
                    char_count=row.char_count,
                    token_estimate=row.token_estimate,
                    meta=dict(row.meta or {}),
                )
                for row in chunk_result.scalars().all()
            ],
            references=[
                DocumentReference(
                    id=row.id,
                    document_id=row.document_id,
                    ordinal=row.ordinal,
                    raw_text=row.raw_text,
                    title=row.title,
                    doi=row.doi,
                    url=row.url,
                    meta=dict(row.meta or {}),
                )
                for row in reference_result.scalars().all()
            ],
            assets=[
                DocumentAsset(
                    id=row.id,
                    document_id=row.document_id,
                    page_number=row.page_number,
                    kind=row.kind,
                    filename=row.filename,
                    content_type=row.content_type,
                    width=row.width,
                    height=row.height,
                    meta=dict(row.meta or {}),
                )
                for row in asset_result.scalars().all()
            ],
        )

    async def update_document(
        self,
        document_id: str,
        *,
        status: str | None = None,
        abstract: str | None = None,
        title: str | None = None,
        authors: list[str] | None = None,
        meta: dict | None = None,
        storage_path: str | None = None,
    ) -> Document | None:
        row = await self.session.get(DocumentRow, document_id)
        if not row:
            return None
        if status is not None:
            row.status = status
        if abstract is not None:
            row.abstract = abstract
        if title is not None:
            row.title = title
        if authors is not None:
            row.authors = authors
        if meta is not None:
            row.meta = meta
        if storage_path is not None:
            row.storage_path = storage_path
        row.updated_at = datetime.now(UTC)
        await self.session.flush()
        return document_to_schema(row)

    async def search(
        self,
        query: str,
        project_id: str | None = None,
        limit: int = 12,
    ) -> list[SearchHit]:
        q = query.lower().strip()
        stmt = select(DocumentRow)
        if project_id:
            stmt = stmt.where(DocumentRow.project_id == project_id)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    func.lower(DocumentRow.title).like(like),
                    func.lower(DocumentRow.filename).like(like),
                    func.lower(DocumentRow.abstract).like(like),
                )
            )
        stmt = stmt.order_by(DocumentRow.updated_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        hits: list[SearchHit] = []
        for row in result.scalars().all():
            title = row.title or row.filename
            score = 0.92 if q and q in (title or "").lower() else 0.71
            meta = dict(row.meta or {})
            try:
                modality = DocumentModality(row.modality)
            except ValueError:
                modality = DocumentModality.unknown
            hits.append(
                SearchHit(
                    id=row.id,
                    title=title,
                    snippet=(row.abstract or "no abstract extracted yet.")[:220],
                    score=score,
                    modality=modality,
                    year=meta.get("year"),
                    citations=meta.get("citations"),
                    source="postgres",
                )
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit]

    async def knowledge_graph(self, project_id: str) -> KnowledgeGraph:
        nodes_result = await self.session.execute(
            select(GraphNodeRow).where(GraphNodeRow.project_id == project_id)
        )
        edges_result = await self.session.execute(
            select(GraphEdgeRow).where(GraphEdgeRow.project_id == project_id)
        )
        nodes = [
            GraphNode(
                id=n.id,
                label=n.label,
                type=n.type,
                meta=dict(n.meta or {}),
            )
            for n in nodes_result.scalars().all()
        ]
        edges = [
            GraphEdge(
                id=e.id,
                source=e.source,
                target=e.target,
                relation=e.relation,
                weight=e.weight,
            )
            for e in edges_result.scalars().all()
        ]
        return KnowledgeGraph(project_id=project_id, nodes=nodes, edges=edges)

    async def replace_knowledge_graph(
        self,
        project_id: str,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
    ) -> KnowledgeGraph:
        existing_nodes = await self.session.execute(
            select(GraphNodeRow).where(GraphNodeRow.project_id == project_id)
        )
        for row in existing_nodes.scalars().all():
            await self.session.delete(row)
        existing_edges = await self.session.execute(
            select(GraphEdgeRow).where(GraphEdgeRow.project_id == project_id)
        )
        for row in existing_edges.scalars().all():
            await self.session.delete(row)

        for node in nodes:
            self.session.add(
                GraphNodeRow(
                    id=node.id,
                    project_id=project_id,
                    label=node.label,
                    type=node.type,
                    meta=node.meta,
                )
            )
        for edge in edges:
            self.session.add(
                GraphEdgeRow(
                    id=edge.id,
                    project_id=project_id,
                    source=edge.source,
                    target=edge.target,
                    relation=edge.relation,
                    weight=edge.weight,
                )
            )
        await self.session.flush()
        return await self.knowledge_graph(project_id)

    async def _document_count(self, project_id: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(DocumentRow)
            .where(DocumentRow.project_id == project_id)
        )
        return int(result.scalar_one())
