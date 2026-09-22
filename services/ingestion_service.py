from ingestion.loader import DocumentLoader


class IngestionService:

    def __init__(self,
                 loader: DocumentLoader,
                 chunker,
                 embedder,
                 repository):
        self.loader = loader
        self.chunker = chunker
        self.embedder = embedder
        self.repository = repository

    def ingest(self, source: str):
        documents = self.loader.load(source)

        chunks = self.chunker.chunk(documents)

        embeddings = self.embedder.embed_documents(chunks)

        return self.repository.save(
            chunks,
            embeddings
        )
