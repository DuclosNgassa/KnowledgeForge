from pathlib import Path

from ingestion.models import LoadedDocument


class TextLoader:

    def load(self, file_path: str) -> list[LoadedDocument]:
        path = Path(file_path)
        content = path.read_text(
            encoding="utf-8",
        )

        return [
            LoadedDocument(
                content=content,
                source=str(path),
                metadata={
                    "file_type": "txt",
                }
            )
        ]
