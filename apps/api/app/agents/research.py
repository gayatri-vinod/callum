from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from app.models.schemas import Citation, Claim


RESEARCH_MODES = {
    "research": "autonomous research collaborator",
    "review": "literature review synthesizer",
    "gaps": "research gap detector",
    "experiment": "experiment planner",
    "novelty": "novelty analyzer",
}


def _demo_claims(message: str) -> list[Claim]:
    return [
        Claim(
            text=(
                "MedSAM adapts Segment Anything to medical imagery with domain-specific "
                "prompting and fine-tuning, improving clinical segmentation robustness."
            ),
            confidence=0.86,
            evidence_strength="strong",
            citations=[
                Citation(
                    paper_id="doc_3",
                    title="MedSAM",
                    authors=["Ma et al."],
                    year=2024,
                    page=4,
                    paragraph="§3.2 Domain adaptation",
                    confidence=0.91,
                )
            ],
        ),
        Claim(
            text=(
                "A weak baseline risk remains: many medical SAM variants report gains "
                "without matched compute or annotation protocol controls."
            ),
            confidence=0.62,
            evidence_strength="moderate",
            citations=[
                Citation(
                    paper_id="doc_2",
                    title="Segment Anything",
                    authors=["Kirillov et al."],
                    year=2023,
                    page=12,
                    paragraph="Limitations",
                    confidence=0.74,
                )
            ],
        ),
    ]


async def stream_research_response(
    *,
    project_id: str,
    message: str,
    mode: str = "research",
) -> AsyncIterator[dict[str, Any]]:
    """Stream a structured research response.

    Production path: LangGraph multi-agent workflow with retrieval, citation
    verification, and hallucination checks. Local MVP streams a grounded demo
    payload so the UI can be developed end-to-end without GPU services.
    """
    mode_label = RESEARCH_MODES.get(mode, RESEARCH_MODES["research"])
    yield {"event": "status", "data": {"stage": "planning", "detail": f"starting {mode_label}"}}
    await asyncio.sleep(0.25)

    yield {
        "event": "status",
        "data": {"stage": "retrieval", "detail": "hybrid search + citation-aware rerank"},
    }
    await asyncio.sleep(0.35)

    yield {
        "event": "status",
        "data": {"stage": "reading", "detail": "cross-referencing MedSAM, SAM, U-Net clusters"},
    }
    await asyncio.sleep(0.35)

    claims = _demo_claims(message)
    chunks = [
        f"## objective\n{message.strip() or 'improve sam for medical imaging'}\n\n",
        "## reading set\n",
        "- **Segment Anything** (Kirillov et al., 2023) — foundation promptable segmentation\n",
        "- **MedSAM** (Ma et al., 2024) — medical adaptation of SAM\n",
        "- **U-Net** (Ronneberger et al., 2015) — classic medical baseline\n\n",
        "## synthesis\n",
        "The strongest path is not another generic SAM fine-tune. Focus on ",
        "**annotation-efficient prompts**, **modality-specific encoders** (CT/MRI), ",
        "and **protocol-matched baselines**. Evidence for clinical gains is solid in MedSAM, ",
        "but reproducibility gaps remain around compute and label quality.\n\n",
        "## open problems\n",
        "1. weak baseline controls across medical SAM papers\n",
        "2. limited evaluation on rare pathologies\n",
        "3. missing cost / latency reporting for clinical deployment\n\n",
        "## next experiments\n",
        "- fine-tune SAM mask decoder on KiTS19 + BraTS with frozen image encoder\n",
        "- ablate point vs box vs text prompts under fixed annotation budget\n",
        "- report dice, hausdorff, gpu-hours, and vram as first-class metrics\n",
    ]

    for chunk in chunks:
        yield {"event": "token", "data": {"text": chunk}}
        await asyncio.sleep(0.05)

    yield {
        "event": "claims",
        "data": {"claims": [c.model_dump() for c in claims]},
    }

    yield {
        "event": "citations",
        "data": {
            "citations": [
                cit.model_dump() for claim in claims for cit in claim.citations
            ]
        },
    }

    if mode == "gaps":
        yield {
            "event": "gaps",
            "data": {
                "gaps": [
                    {
                        "title": "protocol-matched baselines missing",
                        "description": "Many medical SAM papers compare against unmatched U-Net setups.",
                        "confidence": 0.78,
                        "opportunity": "Publish a controlled baseline suite with fixed labels and compute.",
                    },
                    {
                        "title": "rare pathology under-evaluated",
                        "description": "Public benchmarks skew toward common organs and tumor types.",
                        "confidence": 0.71,
                        "opportunity": "Curate a long-tail medical segmentation challenge set.",
                    },
                ]
            },
        }

    if mode == "experiment":
        yield {
            "event": "experiment",
            "data": {
                "hypothesis": "A modality-aware SAM decoder improves Dice on CT organ segmentation under a fixed annotation budget.",
                "datasets": ["KiTS19", "BraTS 2021", "TotalSegmentator subset"],
                "training_pipeline": "freeze ViT encoder → train mask decoder + prompt encoder → light LoRA on encoder",
                "loss_functions": ["dice + ce", "focal tversky"],
                "evaluation_metrics": ["dice", "hd95", "surface dice", "gpu-hours"],
                "hardware": "1× 24GB GPU, ~18–30 gpu-hours",
                "challenges": ["domain shift across scanners", "prompt ambiguity"],
                "contribution": "annotation-efficient medical SAM recipe with matched baselines",
                "related_papers": ["Segment Anything", "MedSAM", "U-Net"],
                "risks": ["overfitting to public CT distributions", "weak clinical generalization"],
            },
        }

    yield {
        "event": "done",
        "data": {
            "project_id": project_id,
            "mode": mode,
            "disclaimer": "evidence strength shown per claim — weak evidence is labeled, never fabricated",
        },
    }


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
