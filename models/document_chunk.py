from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import UUID, Text, Integer, Enum as SQLEnum, DateTime, Computed
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey, Index
from db.database import Base
from ingestion.embedding_status import EmbeddingStatus


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Semantic search
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),
        nullable=True,
    )

    # Keyword/full-text search
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple', content)",
            persisted=True,
        )
    )

    Index(
        "ix_document_chunks_search_vector",
        search_vector,
        postgresql_using="gin",
    )

    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        SQLEnum(EmbeddingStatus, native_enum=False),
        default=EmbeddingStatus.PENDING,
        nullable=False,
    )

    metadata_chunk: Mapped[dict] = mapped_column(
        # PostgreSQL JSONB
        JSONB,
        nullable=False,
        default=dict,
    )

    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
