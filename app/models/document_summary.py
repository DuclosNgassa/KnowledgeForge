import uuid

from sqlalchemy import UUID, ForeignKey, Text, Enum as SQLEnum, UniqueConstraint, DateTime

from app.core.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from app.models.enums import SummaryStatus


class DocumentSummary(Base):
    __tablename__ = "document_summaries"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            name="uq_document_summaries_document_id",
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

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[SummaryStatus] = mapped_column(
        SQLEnum(SummaryStatus, native_enum=False),
        default=SummaryStatus.PENDING,
        nullable=False,
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
        back_populates="summary",
    )
