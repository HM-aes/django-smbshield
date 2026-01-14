"""
Embedder Service - Converts text into numerical vectors (embeddings)

Uses Sentence Transformers for fast, local embedding generation.
No API calls required - runs entirely on CPU/GPU.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Union, List
import os
from functools import lru_cache
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class EmbedderService:
    """
    Service for generating text embeddings using sentence-transformers.

    Handles:
    - Loading the embedding model (once, then cached)
    - Encoding single texts or batches
    - Managing device (CPU vs GPU)
    - Normalizing vectors for better similarity comparison
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        normalize_embeddings: bool = True
    ):
        """
        Initialize the embedder service.

        Args:
            model_name: Which sentence-transformer model to use
                       - "all-MiniLM-L6-v2" (default): Fast, 384 dimensions, 80MB
                       - "all-mpnet-base-v2": Better quality, 768 dimensions, 420MB
            device: Where to run the model ("cpu", "cuda", "mps")
            normalize_embeddings: Whether to normalize vectors to unit length
        """
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self._model = None

        logger.info(
            f"EmbedderService initialized with model={model_name}, "
            f"device={device}, normalize={normalize_embeddings}"
        )

    @property
    def model(self) -> SentenceTransformer:
        """Load the model on first access (lazy loading)."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")

            try:
                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device
                )
                logger.info(
                    f"Model loaded successfully. "
                    f"Embedding dimension: {self._model.get_sentence_embedding_dimension()}"
                )
            except Exception as e:
                logger.error(f"Failed to load model: {str(e)}")
                raise RuntimeError(
                    f"Could not load embedding model '{self.model_name}'. Error: {str(e)}"
                )

        return self._model

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Convert text(s) into embedding vector(s).

        Args:
            texts: Single text or list of texts to encode
            batch_size: How many texts to process at once
            show_progress: Show a progress bar for large batches

        Returns:
            np.ndarray: Embedding vector(s)
        """
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]

        logger.debug(f"Encoding {len(texts)} text(s)")

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=self.normalize_embeddings,
            )

            if is_single:
                return embeddings[0]

            return embeddings

        except Exception as e:
            logger.error(f"Encoding failed: {str(e)}")
            raise RuntimeError(f"Failed to encode texts: {str(e)}")

    def encode_query(self, query: str) -> np.ndarray:
        """Convenience method for encoding a search query."""
        logger.debug(f"Encoding query: {query[:50]}...")
        return self.encode(query)

    def encode_documents(
        self,
        documents: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """Convenience method for encoding multiple documents."""
        logger.info(f"Encoding {len(documents)} documents")
        return self.encode(
            documents,
            batch_size=batch_size,
            show_progress=show_progress
        )

    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        embedding1 = embedding1 / norm1
        embedding2 = embedding2 / norm2

        return float(np.dot(embedding1, embedding2))

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        return self.model.get_sentence_embedding_dimension()

    def __repr__(self) -> str:
        return (
            f"EmbedderService(model={self.model_name}, "
            f"device={self.device}, "
            f"dim={self.get_embedding_dimension()})"
        )


@lru_cache(maxsize=1)
def get_embedder_service() -> EmbedderService:
    """Get or create the global embedder service instance (singleton)."""
    # Get configuration from Django settings or environment
    rag_config = getattr(settings, 'RAG_CONFIG', {})

    model_name = rag_config.get(
        'EMBEDDING_MODEL',
        os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    )
    device = rag_config.get(
        'EMBEDDING_DEVICE',
        os.getenv("EMBEDDING_DEVICE", "cpu")
    )

    logger.info(f"Creating EmbedderService with model={model_name}, device={device}")

    return EmbedderService(
        model_name=model_name,
        device=device,
        normalize_embeddings=True
    )


# Global singleton instance
embedder_service = get_embedder_service()
