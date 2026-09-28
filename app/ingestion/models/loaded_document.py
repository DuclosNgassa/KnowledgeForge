from dataclasses import dataclass, field

"""
LoadedDocument(
    content="Large Language Models are...",
    source="research.pdf",
    metadata={
        "file_type": "pdf",
        "page": 3,
    },
)
"""


@dataclass
class LoadedDocument:
    content: str
    source: str
    metadata: dict = field(default_factory=dict)
