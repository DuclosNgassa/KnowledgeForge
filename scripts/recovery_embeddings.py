import asyncio

from app.workers.recovery import recover_embedding_jobs

"""
 Before running this script, make sure that the redis connection 
 is set up correctly and the broker is running.
 
Run in different PowerShell windows:
1. Start the broker:
    uv run taskiq worker app.workers.worker:broker
2. Run the task:
    uv run python -m scripts.recovery_embeddings
"""


async def main():
    await recover_embedding_jobs.kiq()


if __name__ == "__main__":
    asyncio.run(main())
