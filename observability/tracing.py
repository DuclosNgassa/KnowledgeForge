from contextlib import asynccontextmanager
import time

from observability.logging import logger


@asynccontextmanager
async def trace_operation(
        operation: str,
        request_id: str | None = None,
        **metadata,
):
    start_time = time.perf_counter()

    try:
        yield

    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.error(
            f"operation_failed | "
            f"operation={operation} | "
            f"request_id={request_id} | "
            f"duration_ms={duration_ms:.2f} | "
            f"metadata={metadata}"
        )

        raise

    else:
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"operation_completed | "
            f"operation={operation} | "
            f"request_id={request_id} | "
            f"duration_ms={duration_ms:.2f} | "
            f"metadata={metadata}"
        )
