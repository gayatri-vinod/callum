from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def new_id() -> str:
    return str(uuid4())


class DocumentModality(str, Enum):
    pdf = "pdf"
    image = "image"
    video = "video"
    audio = "audio"
    dataset = "dataset"
    markdown = "markdown"
    code = "code"
    slides = "slides"
    unknown = "unknown"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""


class Project(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    document_count: int = 0
    status: str = "active"


class Document(BaseModel):
    id: str = Field(default_factory=new_id)
    project_id: str
    filename: str
    modality: DocumentModality = DocumentModality.unknown
    content_type: str | None = None
    size_bytes: int = 0
    status: str = "queued"  # queued | processing | ready | failed
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    meta: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    paper_id: str | None = None
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    page: int | None = None
    paragraph: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    url: str | None = None


class Claim(BaseModel):
    text: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence_strength: str = "moderate"  # weak | moderate | strong


class AgentMessage(BaseModel):
    role: str  # user | assistant | system | tool
    content: str
    citations: list[Citation] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)


class AgentRequest(BaseModel):
    project_id: str
    message: str
    mode: str = "research"  # research | review | gaps | experiment | novelty
    stream: bool = True


class SearchRequest(BaseModel):
    project_id: str | None = None
    query: str
    modality: DocumentModality | None = None
    year_from: int | None = None
    year_to: int | None = None
    limit: int = Field(default=12, ge=1, le=50)


class SearchHit(BaseModel):
    id: str
    title: str
    snippet: str
    score: float
    modality: DocumentModality = DocumentModality.pdf
    year: int | None = None
    citations: int | None = None
    source: str = "hybrid"


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # paper | author | method | dataset | model | institution | task
    meta: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str  # improves | uses | inspired_by | evaluated_on | extends | competes_with
    weight: float = 1.0


class KnowledgeGraph(BaseModel):
    project_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class PaperStructure(BaseModel):
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    institution: list[str] = Field(default_factory=list)
    publication: str | None = None
    year: int | None = None
    datasets: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    architecture: str | None = None
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    training_pipeline: str | None = None
    loss: str | None = None
    evaluation_metrics: list[str] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    future_work: list[str] = Field(default_factory=list)
    github: str | None = None
    paper_url: str | None = None
    citation: str | None = None


class ResearchGap(BaseModel):
    title: str
    description: str
    evidence: list[Claim] = Field(default_factory=list)
    confidence: float = 0.5
    opportunity: str | None = None


class ExperimentPlan(BaseModel):
    hypothesis: str
    datasets: list[str] = Field(default_factory=list)
    training_pipeline: str
    loss_functions: list[str] = Field(default_factory=list)
    evaluation_metrics: list[str] = Field(default_factory=list)
    hardware: str
    challenges: list[str] = Field(default_factory=list)
    contribution: str
    related_papers: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
