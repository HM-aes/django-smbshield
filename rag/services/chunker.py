"""
Chunker Service - Split documents into smaller pieces

Handles:
- Splitting long documents into chunks (sized for LLM context)
- Maintaining overlap between chunks (preserves context)
- Splitting on natural boundaries (paragraphs, sentences)
"""

from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a single chunk of text with its metadata."""
    text: str
    metadata: Dict[str, Any]
    chunk_id: Optional[int] = None

    def __repr__(self) -> str:
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"Chunk(id={self.chunk_id}, text='{text_preview}', metadata={self.metadata})"


class ChunkerService:
    """
    Service for splitting documents into overlapping chunks.

    Strategy:
    1. Try to split on paragraph boundaries (double newline)
    2. If paragraphs too long, split on sentence boundaries
    3. If sentences too long, split on any whitespace
    4. Always maintain overlap between consecutive chunks
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize the chunker service.

        Args:
            chunk_size: Target size of each chunk (in tokens, ~4 chars per token)
            chunk_overlap: How much chunks should overlap
            separators: List of strings to split on, in order of preference
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.separators = separators or [
            "\n\n",    # Paragraph break
            "\n",      # Single newline
            ". ",      # Sentence end
            "! ",      # Exclamation
            "? ",      # Question
            "; ",      # Semicolon
            ", ",      # Comma
            " ",       # Space (last resort)
        ]

        logger.info(
            f"ChunkerService initialized: chunk_size={chunk_size}, "
            f"overlap={chunk_overlap}"
        )

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Split a single text into overlapping chunks.

        Args:
            text: The document text to split
            metadata: Information about the source document

        Returns:
            List[Chunk]: List of text chunks with metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []

        if metadata is None:
            metadata = {}

        # Convert chunk_size from tokens to approximate characters
        char_chunk_size = self.chunk_size * 4
        char_overlap = self.chunk_overlap * 4

        logger.debug(
            f"Chunking text of length {len(text)} chars into "
            f"~{char_chunk_size} char chunks with {char_overlap} overlap"
        )

        chunk_texts = self._split_text_recursive(
            text,
            chunk_size=char_chunk_size,
            overlap=char_overlap
        )

        chunks = []
        for idx, chunk_text in enumerate(chunk_texts):
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = idx
            chunk_metadata['total_chunks'] = len(chunk_texts)

            chunk = Chunk(
                text=chunk_text.strip(),
                metadata=chunk_metadata,
                chunk_id=idx
            )
            chunks.append(chunk)

        logger.info(f"Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks

    def _split_text_recursive(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
        separator_idx: int = 0
    ) -> List[str]:
        """Recursively split text using the best available separator."""
        if len(text) <= chunk_size:
            return [text]

        if separator_idx >= len(self.separators):
            return self._split_by_characters(text, chunk_size, overlap)

        separator = self.separators[separator_idx]
        splits = text.split(separator)

        if len(splits) == 1:
            return self._split_text_recursive(
                text, chunk_size, overlap, separator_idx + 1
            )

        chunks = []
        current_chunk = []
        current_length = 0

        for split in splits:
            split_with_sep = split + separator if split != splits[-1] else split
            split_length = len(split_with_sep)

            if current_length + split_length > chunk_size and current_chunk:
                chunk_text = "".join(current_chunk)
                chunks.append(chunk_text)

                if overlap > 0 and len(chunk_text) >= overlap:
                    overlap_text = chunk_text[-overlap:]
                    current_chunk = [overlap_text, split_with_sep]
                    current_length = len(overlap_text) + split_length
                else:
                    current_chunk = [split_with_sep]
                    current_length = split_length
            else:
                current_chunk.append(split_with_sep)
                current_length += split_length

        if current_chunk:
            chunks.append("".join(current_chunk))

        # Check if any chunk is still too large
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > chunk_size * 1.5:
                sub_chunks = self._split_text_recursive(
                    chunk, chunk_size, overlap, separator_idx + 1
                )
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)

        return final_chunks

    def _split_by_characters(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """Last resort: split by character count."""
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            start += (chunk_size - overlap)

        return chunks

    def chunk_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Chunk]:
        """
        Chunk multiple documents at once.

        Args:
            documents: List of documents to chunk
                      Each document: {"text": "...", "metadata": {...}}

        Returns:
            List[Chunk]: All chunks from all documents
        """
        all_chunks = []

        for doc in documents:
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            doc_chunks = self.chunk_text(text, metadata)
            all_chunks.extend(doc_chunks)

        logger.info(
            f"Chunked {len(documents)} documents into {len(all_chunks)} chunks"
        )

        return all_chunks
