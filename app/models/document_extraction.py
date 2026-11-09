import uuid
from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint, ForeignKey, DateTime, Enum as SQLEnum, Text, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.database import Base
from app.models.enums import ExtractionStatus


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            name="uq_document_extractions_document_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    extraction_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None
    )

    status: Mapped[ExtractionStatus] = mapped_column(
        SQLEnum(ExtractionStatus, native_enum=False),
        default=ExtractionStatus.PENDING,
        nullable=False,
    )

    generation_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    document: Mapped["Document"] = relationship(
        back_populates="extraction",
    )
