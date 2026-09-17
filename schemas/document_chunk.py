from dataclasses import dataclass
from typing import Any


@dataclass
class DocumentChunkData:
    content: str
    source: str
    chunk_index: int
    metadata: dict[str, Any]
