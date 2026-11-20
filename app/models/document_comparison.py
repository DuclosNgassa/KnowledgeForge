from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.database import Base
from app.models.enums import ComparisonStatus


class DocumentComparison(Base):
    __tablename__ = "document_comparisons"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    criteria: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )

    status: Mapped[ComparisonStatus] = mapped_column(
        SQLEnum(ComparisonStatus, native_enum=False),
        default=ComparisonStatus.WAITING_FOR_PREREQUISITES,
        nullable=False,
    )

    overview: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    conclusion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    result: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    generation_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
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

    items: Mapped[list["DocumentComparisonItem"]] = relationship(
        back_populates="comparison",
        cascade="all, delete-orphan",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="document_comparisons",
    )


class DocumentComparisonItem(Base):
    __tablename__ = "document_comparison_items"

    __table_args__ = (
        UniqueConstraint(
            "comparison_id",
            "document_id",
            name="uq_document_comparison_items_comparison_document",
        ),
        UniqueConstraint(
            "comparison_id",
            "position",
            name="uq_document_comparison_items_comparison_position",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    comparison_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_comparisons.id", ondelete="CASCADE"),
        nullable=False,
    )

    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    comparison: Mapped["DocumentComparison"] = relationship(
        back_populates="items",
    )

    document: Mapped["Document"] = relationship(
        back_populates="comparison_items",
    )
