import asyncio

import pytest

from app.workers import document_summary_task as summary_task


@pytest.mark.asyncio
async def test_summary_tasks_execute_sequentially(monkeypatch):
    active_jobs = 0
    max_active_jobs = 0
    execution_order = []

    async def mock_generate_summary(
            document_id_str: str,
            generation_id_str: str,
    ):
        nonlocal active_jobs, max_active_jobs

        active_jobs += 1
        max_active_jobs = max(
            max_active_jobs,
            active_jobs,
        )

        execution_order.append(
            f"{document_id_str}_started"
        )

        try:
            await asyncio.sleep(0.1)
        finally:
            active_jobs -= 1

        execution_order.append(
            f"{document_id_str}_completed"
        )

    monkeypatch.setattr(
        summary_task,
        "_generate_document_summary",
        mock_generate_summary,
    )

    await asyncio.gather(
        summary_task._run_summary_with_semaphore(
            "document-1",
            "generation-1",
        ),
        summary_task._run_summary_with_semaphore(
            "document-2",
            "generation-2",
        ),
    )

    assert max_active_jobs == 1

    assert execution_order == [
        "document-1_started",
        "document-1_completed",
        "document-2_started",
        "document-2_completed",
    ]
