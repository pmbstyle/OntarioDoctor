import logging
from typing import List
from backend.shared.models import Document, Chunk
from backend.shared.constants import CHUNK_SIZE, CHUNK_OVERLAP


logger = logging.getLogger(__name__)


class TextChunker:
    """Text chunking service"""

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: Document) -> List[Chunk]:
        """
        Chunk a document into smaller pieces

        Args:
            document: Document to chunk

        Returns:
            List of chunks with metadata
        """
        text = document.text.strip()

        # Simple word-based chunking
        words = text.split()
        chunks = []
        chunk_id = 0

        # Calculate words per chunk (approximate tokens)
        words_per_chunk = int(self.chunk_size * 0.75)  # ~0.75 words per token
        words_overlap = int(self.chunk_overlap * 0.75)

        start = 0
        while start < len(words):
            end = min(start + words_per_chunk, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            # Create chunk
            chunk = Chunk(
                text=chunk_text,
                chunk_id=chunk_id,
                metadata={
                    "title": document.title,
                    "url": document.url,
                    "source": document.source,
                    "section": document.section or "main",
                    "chunk_id": chunk_id
                }
            )
            chunks.append(chunk)

            chunk_id += 1
            start = end - words_overlap if end < len(words) else end

        logger.debug(f"Chunked document '{document.title}' into {len(chunks)} chunks")
        return chunks

    def chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        """
        Chunk multiple documents

        Args:
            documents: List of documents to chunk

        Returns:
            List of all chunks
        """
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        logger.info(f"Chunked {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks
