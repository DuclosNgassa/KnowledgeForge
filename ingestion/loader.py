from pathlib import Path

from ingestion.loaders.markdown import MarkdownLoader
from ingestion.loaders.pdf import PdfLoader
from ingestion.loaders.text import TextLoader
from ingestion.loaders.web import WebLoader
from ingestion.loaders.word import WordLoader
from ingestion.models import LoadedDocument


class DocumentLoader:

    def __init__(self):
        self.pdf_loader = PdfLoader()
        self.text_loader = TextLoader()
        self.markdown_loader = MarkdownLoader()
        self.word_loader = WordLoader()
        self.web_loader = WebLoader()

    def load(self, source: str) -> list[LoadedDocument]:
        if source.startswith(("http://", "https://")):
            return self.web_loader.load(source)

        extension = Path(source).suffix.lower()

        match extension:
            case ".pdf":
                return self.pdf_loader.load(source)
            case ".txt":
                return self.text_loader.load(source)
            case ".md":
                return self.markdown_loader.load(source)
            case ".docx":
                return self.word_loader.load(source)
            case _:
                raise ValueError(
                    f"Unsupported document type: {extension}"
                )
