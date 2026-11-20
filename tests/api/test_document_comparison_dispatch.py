from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.routes import document as router_module
from app.services.document_comparison_orchestration_service import (
    PrerequisiteDispatch,
)


@pytest.mark.asyncio
async def test_dispatch_comparison_prerequisites_dispatches_both_jobs():
    document_id = uuid4()
    summary_generation_id = uuid4()
    extraction_generation_id = uuid4()
    comparison_id = uuid4()
    generation_id = uuid4()

    dispatches = [
        PrerequisiteDispatch(
            document_id=document_id,
            summary_generation_id=summary_generation_id,
            extraction_generation_id=extraction_generation_id,
        )
    ]

    summary_kiq = AsyncMock()
    extraction_kiq = AsyncMock()

    service = SimpleNamespace(
        summary_service=SimpleNamespace(set_dispatch_failed=AsyncMock()),
        extraction_service=SimpleNamespace(set_dispatch_failed=AsyncMock()),
        set_dispatch_failed=AsyncMock(),
    )
    db = AsyncMock()

    with (
        patch.object(
            router_module,
            "generate_document_summary",
            SimpleNamespace(kiq=summary_kiq),
        ),
        patch.object(
            router_module,
            "extract_document",
            SimpleNamespace(kiq=extraction_kiq),
        ),
    ):
        await router_module.dispatch_comparison_prerequisites(
            dispatches=dispatches,
            service=service,
            db=db,
            comparison_id=comparison_id,
            generation_id=generation_id,
        )

    summary_kiq.assert_awaited_once_with(
        str(document_id),
        str(summary_generation_id),
    )
    extraction_kiq.assert_awaited_once_with(
        str(document_id),
        str(extraction_generation_id),
    )

    service.summary_service.set_dispatch_failed.assert_not_awaited()
    service.extraction_service.set_dispatch_failed.assert_not_awaited()
    service.set_dispatch_failed.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_dispatch_comparison_prerequisites_handles_summary_dispatch_failure():
    document_id = uuid4()
    summary_generation_id = uuid4()
    extraction_generation_id = uuid4()
    comparison_id = uuid4()
    generation_id = uuid4()

    dispatches = [
        PrerequisiteDispatch(
            document_id=document_id,
            summary_generation_id=summary_generation_id,
            extraction_generation_id=extraction_generation_id,
        )
    ]

    summary_kiq = AsyncMock(side_effect=RuntimeError("Redis unavailable"))
    extraction_kiq = AsyncMock()

    service = SimpleNamespace(
        summary_service=SimpleNamespace(set_dispatch_failed=AsyncMock()),
        extraction_service=SimpleNamespace(set_dispatch_failed=AsyncMock()),
        set_dispatch_failed=AsyncMock(),
    )
    service.set_dispatch_failed = AsyncMock()

    db = AsyncMock()

    with (
        patch.object(
            router_module,
            "generate_document_summary",
            SimpleNamespace(kiq=summary_kiq),
        ),
        patch.object(
            router_module,
            "extract_document",
            SimpleNamespace(kiq=extraction_kiq),
        ),
    ):
        await router_module.dispatch_comparison_prerequisites(
            dispatches=dispatches,
            service=service,
            db=db,
            comparison_id=comparison_id,
            generation_id=generation_id,
        )

    service.summary_service.set_dispatch_failed.assert_awaited_once_with(
        document_id=document_id,
        generation_id=summary_generation_id,
        error_message=f"Failed to enqueue document summary | document_id={document_id}.",
    )

    extraction_kiq.assert_awaited_once_with(
        str(document_id),
        str(extraction_generation_id),
    )

    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_dispatch_comparison_prerequisites_handles_extraction_dispatch_failure():
    document_id = uuid4()
    extraction_generation_id = uuid4()
    comparison_id = uuid4()
    generation_id = uuid4()

    dispatches = [
        PrerequisiteDispatch(
            document_id=document_id,
            extraction_generation_id=extraction_generation_id,
        )
    ]

    summary_kiq = AsyncMock()
    extraction_kiq = AsyncMock(side_effect=RuntimeError("Redis unavailable"))

    service = SimpleNamespace(
        summary_service=SimpleNamespace(set_dispatch_failed=AsyncMock()),
        extraction_service=SimpleNamespace(set_dispatch_failed=AsyncMock()),
        set_dispatch_failed=AsyncMock(),
    )
    service.set_dispatch_failed = AsyncMock()
    db = AsyncMock()

    with (
        patch.object(
            router_module,
            "generate_document_summary",
            SimpleNamespace(kiq=summary_kiq),
        ),
        patch.object(
            router_module,
            "extract_document",
            SimpleNamespace(kiq=extraction_kiq),
        ),
    ):
        await router_module.dispatch_comparison_prerequisites(
            dispatches=dispatches,
            service=service,
            db=db,
            comparison_id=comparison_id,
            generation_id=generation_id,
        )

    service.extraction_service.set_dispatch_failed.assert_awaited_once_with(
        document_id=document_id,
        generation_id=extraction_generation_id,
        error_message=f"Failed to enqueue document extraction | document_id={document_id}.",
    )

    db.commit.assert_awaited_once()
    summary_kiq.assert_not_awaited()
