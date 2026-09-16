from enum import Enum


class DocumentType(str, Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    TXT = "TXT"
    MARKDOWN = "MARKDOWN"
    WEB = "WEB"
