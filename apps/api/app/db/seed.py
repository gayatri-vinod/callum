from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProjectRow
from app.db.repository import Repository
from app.models.schemas import DocumentModality, GraphEdge, GraphNode

DEMO_PROJECT_ID = "proj_sam_medical"


async def seed_if_empty(session: AsyncSession) -> None:
    """Seed demo project + corpus + graph when the database is empty."""
    result = await session.execute(select(ProjectRow).limit(1))
    if result.scalar_one_or_none() is not None:
        return

    repo = Repository(session)
    session.add(
        ProjectRow(
            id=DEMO_PROJECT_ID,
            name="sam for medical imaging",
            description="improve segment anything for clinical ct / mri workflows",
            status="active",
        )
    )
    await session.flush()

    samples = [
        ("doc_1", "Attention Is All You Need", "pdf", ["Vaswani et al."], 2017),
        ("doc_2", "Segment Anything", "pdf", ["Kirillov et al."], 2023),
        ("doc_3", "MedSAM", "pdf", ["Ma et al."], 2024),
        ("doc_4", "U-Net", "pdf", ["Ronneberger et al."], 2015),
        ("doc_5", "whiteboard notes — annotation protocol", "image", [], None),
        ("doc_6", "lab meeting recording", "audio", [], None),
    ]
    for doc_id, title, modality, authors, year in samples:
        await repo.add_document(
            document_id=doc_id,
            project_id=DEMO_PROJECT_ID,
            filename=f"{title.lower().replace(' ', '_')}.{'pdf' if modality == 'pdf' else 'bin'}",
            modality=DocumentModality(modality),
            title=title,
            authors=authors,
            status="ready",
            size_bytes=1_200_000,
            abstract="seeded literature for local development.",
            meta={"year": year} if year else {},
        )

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
    await repo.replace_knowledge_graph(DEMO_PROJECT_ID, nodes, edges)
    await session.commit()
