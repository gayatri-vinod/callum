from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


def _id() -> str:
    return str(uuid4())


# JSON works on Postgres (JSONB via dialect) and SQLite
JsonType = JSON().with_variant(SQLiteJSON(), "sqlite")


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    documents: Mapped[list[DocumentRow]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    graph_nodes: Mapped[list[GraphNodeRow]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    graph_edges: Mapped[list[GraphEdgeRow]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    modality: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    authors: Mapped[list[Any]] = mapped_column(JsonType, default=list)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped[ProjectRow] = relationship(back_populates="documents")


class GraphNodeRow(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)

    project: Mapped[ProjectRow] = relationship(back_populates="graph_nodes")


class GraphEdgeRow(Base):
    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    project: Mapped[ProjectRow] = relationship(back_populates="graph_edges")
