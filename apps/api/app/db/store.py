from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.schemas import (
    Document,
    DocumentModality,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    Project,
    SearchHit,
)

# In-memory store for MVP local development. Swap for Postgres + MinIO + Qdrant in production.


class Store:
    def __init__(self) -> None:
        self.projects: dict[str, Project] = {}
        self.documents: dict[str, Document] = {}
        self._seed()

    def _seed(self) -> None:
        demo = Project(
            id="proj_sam_medical",
            name="sam for medical imaging",
            description="improve segment anything for clinical ct / mri workflows",
            document_count=6,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.projects[demo.id] = demo

        samples = [
            ("Attention Is All You Need", "pdf", ["Vaswani et al."], 2017),
            ("Segment Anything", "pdf", ["Kirillov et al."], 2023),
            ("MedSAM", "pdf", ["Ma et al."], 2024),
            ("U-Net", "pdf", ["Ronneberger et al."], 2015),
            ("whiteboard notes — annotation protocol", "image", [], None),
            ("lab meeting recording", "audio", [], None),
        ]
        for i, (title, modality, authors, year) in enumerate(samples):
            doc = Document(
                id=f"doc_{i+1}",
                project_id=demo.id,
                filename=f"{title.lower().replace(' ', '_')}.{'pdf' if modality=='pdf' else 'bin'}",
                modality=DocumentModality(modality),
                title=title,
                authors=authors,
                status="ready",
                size_bytes=1_200_000 + i * 50_000,
                abstract="seeded literature for local development.",
                meta={"year": year} if year else {},
            )
            self.documents[doc.id] = doc

        self.projects[demo.id].document_count = len(
            [d for d in self.documents.values() if d.project_id == demo.id]
        )

    def list_projects(self) -> list[Project]:
        return sorted(self.projects.values(), key=lambda p: p.updated_at, reverse=True)

    def get_project(self, project_id: str) -> Project | None:
        return self.projects.get(project_id)

    def create_project(self, name: str, description: str = "") -> Project:
        project = Project(name=name.lower().strip(), description=description.strip())
        self.projects[project.id] = project
        return project

    def list_documents(self, project_id: str) -> list[Document]:
        return [d for d in self.documents.values() if d.project_id == project_id]

    def add_document(self, doc: Document) -> Document:
        self.documents[doc.id] = doc
        project = self.projects.get(doc.project_id)
        if project:
            project.document_count = len(self.list_documents(project.id))
            project.updated_at = datetime.utcnow()
        return doc

    def search(self, query: str, project_id: str | None = None, limit: int = 12) -> list[SearchHit]:
        q = query.lower().strip()
        hits: list[SearchHit] = []
        for doc in self.documents.values():
            if project_id and doc.project_id != project_id:
                continue
            hay = f"{doc.title or ''} {' '.join(doc.authors)} {doc.abstract or ''}".lower()
            if not q or q in hay:
                score = 0.92 if q and q in (doc.title or "").lower() else 0.71
                hits.append(
                    SearchHit(
                        id=doc.id,
                        title=doc.title or doc.filename,
                        snippet=(doc.abstract or "no abstract extracted yet.")[:220],
                        score=score,
                        modality=doc.modality,
                        year=doc.meta.get("year"),
                        citations=doc.meta.get("citations"),
                    )
                )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit]

    def knowledge_graph(self, project_id: str) -> KnowledgeGraph:
        nodes = [
            GraphNode(id="p_sam", label="Segment Anything", type="paper", meta={"year": 2023}),
            GraphNode(id="p_medsam", label="MedSAM", type="paper", meta={"year": 2024}),
            GraphNode(id="p_unet", label="U-Net", type="paper", meta={"year": 2015}),
            GraphNode(id="m_sam", label="SAM", type="model"),
            GraphNode(id="m_vit", label="ViT", type="model"),
            GraphNode(id="d_kits", label="KiTS19", type="dataset"),
            GraphNode(id="d_brats", label="BraTS", type="dataset"),
            GraphNode(id="t_seg", label="medical segmentation", type="task"),
            GraphNode(id="a_kirillov", label="Kirillov", type="author"),
            GraphNode(id="a_ma", label="Ma", type="author"),
        ]
        edges = [
            GraphEdge(id="e1", source="p_medsam", target="p_sam", relation="extends"),
            GraphEdge(id="e2", source="p_sam", target="m_sam", relation="introduced"),
            GraphEdge(id="e3", source="p_sam", target="m_vit", relation="uses"),
            GraphEdge(id="e4", source="p_medsam", target="d_kits", relation="evaluated_on"),
            GraphEdge(id="e5", source="p_medsam", target="t_seg", relation="improves"),
            GraphEdge(id="e6", source="p_unet", target="t_seg", relation="introduced"),
            GraphEdge(id="e7", source="p_medsam", target="p_unet", relation="inspired_by"),
            GraphEdge(id="e8", source="a_kirillov", target="p_sam", relation="authored"),
            GraphEdge(id="e9", source="a_ma", target="p_medsam", relation="authored"),
            GraphEdge(id="e10", source="p_medsam", target="d_brats", relation="evaluated_on"),
        ]
        return KnowledgeGraph(project_id=project_id, nodes=nodes, edges=edges)


store = Store()
