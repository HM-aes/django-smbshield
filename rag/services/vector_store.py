"""
Vector Store Service - Interface to Qdrant vector database

Handles:
- Creating and managing Qdrant collections
- Inserting embeddings with metadata
- Searching for similar vectors
- Deleting and updating vectors
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from qdrant_client.http import models
import numpy as np
from typing import List, Dict, Any, Optional, Union
import logging
import os
from dataclasses import dataclass
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result from Qdrant."""
    id: Union[str, int]
    score: float
    payload: Dict[str, Any]
    vector: Optional[List[float]] = None

    def __repr__(self) -> str:
        source = self.payload.get('source', 'unknown')
        text_preview = str(self.payload.get('text', ''))[:50]
        return f"SearchResult(id={self.id}, score={self.score:.3f}, source={source}, text='{text_preview}...')"


class VectorStoreService:
    """
    Service for interacting with Qdrant vector database.

    Provides a clean interface for:
    - Storing embeddings + metadata
    - Searching by similarity
    - Managing collections
    - Filtering results
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        collection_name: str = "smbshield_knowledge",
        vector_size: int = 384,
        distance: Distance = Distance.COSINE
    ):
        """
        Initialize connection to Qdrant.

        Args:
            host: Qdrant server hostname
            port: Qdrant port (default 6333)
            api_key: API key for Qdrant Cloud (None for local)
            collection_name: Name of the collection to use
            vector_size: Dimension of embeddings (must match embedding model)
            distance: How to measure similarity (COSINE recommended)
        """
        self.host = host
        self.port = port
        self.api_key = api_key
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance

        logger.info(f"Connecting to Qdrant at {host}:{port}")

        if api_key:
            self.client = QdrantClient(
                url=f"https://{host}",
                api_key=api_key,
                port=port
            )
            logger.info("Using Qdrant Cloud with API key")
        else:
            self.client = QdrantClient(
                host=host,
                port=port
            )
            logger.info("Using local Qdrant instance")

        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name in collection_names:
                logger.info(f"Collection '{self.collection_name}' already exists")
                return

            logger.info(f"Creating new collection: {self.collection_name}")

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=self.distance
                )
            )

            logger.info(
                f"Collection created successfully: {self.collection_name} "
                f"(size={self.vector_size}, distance={self.distance})"
            )

        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {str(e)}")
            raise RuntimeError(f"Could not create/access collection: {str(e)}")

    def insert(
        self,
        embeddings: Union[np.ndarray, List[np.ndarray]],
        payloads: Union[Dict[str, Any], List[Dict[str, Any]]],
        ids: Optional[Union[str, int, List[Union[str, int]]]] = None
    ) -> List[Union[str, int]]:
        """
        Insert embeddings with metadata into Qdrant.

        Args:
            embeddings: Single embedding or list of embeddings
            payloads: Metadata dict(s) to store with embedding(s)
            ids: Optional IDs for the points

        Returns:
            List of IDs where data was inserted
        """
        is_single = False

        if isinstance(embeddings, np.ndarray):
            if embeddings.ndim == 1:
                embeddings = [embeddings]
                payloads = [payloads]
                ids = [ids] if ids is not None else None
                is_single = True
            else:
                embeddings = list(embeddings)

        if not isinstance(payloads, list):
            payloads = [payloads]

        if ids is not None and not isinstance(ids, list):
            ids = [ids]

        if len(embeddings) != len(payloads):
            raise ValueError(
                f"Number of embeddings ({len(embeddings)}) must match "
                f"number of payloads ({len(payloads)})"
            )

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]

        logger.debug(f"Inserting {len(embeddings)} vectors into {self.collection_name}")

        try:
            points = []
            for embedding, payload, point_id in zip(embeddings, payloads, ids):
                if isinstance(embedding, np.ndarray):
                    embedding = embedding.tolist()

                if len(embedding) != self.vector_size:
                    raise ValueError(
                        f"Embedding size mismatch: expected {self.vector_size}, "
                        f"got {len(embedding)}"
                    )

                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"Successfully inserted {len(points)} vectors")

            return ids if not is_single else ids[0]

        except Exception as e:
            logger.error(f"Failed to insert vectors: {str(e)}")
            raise RuntimeError(f"Insertion failed: {str(e)}")

    def search(
        self,
        query_embedding: Union[np.ndarray, List[float]],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar vectors in Qdrant.

        Args:
            query_embedding: The query vector to search for
            top_k: How many results to return
            score_threshold: Only return results above this score
            filter_conditions: Metadata filters to apply

        Returns:
            List[SearchResult]: Sorted by similarity (highest first)
        """
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()

        if len(query_embedding) != self.vector_size:
            raise ValueError(
                f"Query embedding size mismatch: expected {self.vector_size}, "
                f"got {len(query_embedding)}"
            )

        logger.debug(
            f"Searching {self.collection_name} with top_k={top_k}, "
            f"threshold={score_threshold}, filters={filter_conditions}"
        )

        try:
            query_filter = None
            if filter_conditions:
                query_filter = self._build_filter(filter_conditions)

            # Use query_points (new Qdrant client API)
            search_response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False
            )

            results = []
            for hit in search_response.points:
                result = SearchResult(
                    id=hit.id,
                    score=hit.score,
                    payload=hit.payload or {}
                )
                results.append(result)

            logger.info(f"Search returned {len(results)} results")

            if results:
                top_result = results[0]
                logger.debug(
                    f"Top result: score={top_result.score:.3f}, "
                    f"source={top_result.payload.get('source', 'N/A')}"
                )

            return results

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise RuntimeError(f"Search operation failed: {str(e)}")

    def _build_filter(
        self,
        conditions: Dict[str, Any]
    ) -> Filter:
        """Build a Qdrant filter from simple conditions dict."""
        field_conditions = []

        for key, value in conditions.items():
            condition = FieldCondition(
                key=key,
                match=MatchValue(value=value)
            )
            field_conditions.append(condition)

        if not field_conditions:
            return None

        return Filter(must=field_conditions)

    def delete(
        self,
        ids: Union[str, int, List[Union[str, int]]]
    ) -> None:
        """Delete vectors by ID."""
        if not isinstance(ids, list):
            ids = [ids]

        logger.info(f"Deleting {len(ids)} vectors from {self.collection_name}")

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=ids)
            )
            logger.info(f"Successfully deleted {len(ids)} vectors")

        except Exception as e:
            logger.error(f"Delete failed: {str(e)}")
            raise RuntimeError(f"Delete operation failed: {str(e)}")

    def count(self) -> int:
        """Get total number of vectors in collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            count = info.points_count
            logger.debug(f"Collection {self.collection_name} contains {count} vectors")
            return count
        except Exception as e:
            logger.error(f"Failed to count vectors: {str(e)}")
            return 0

    def clear_collection(self) -> None:
        """Delete all vectors in the collection. USE WITH CAUTION!"""
        logger.warning(f"Clearing all data from collection: {self.collection_name}")

        try:
            self.client.delete_collection(collection_name=self.collection_name)
            self._ensure_collection_exists()
            logger.info(f"Collection {self.collection_name} cleared successfully")

        except Exception as e:
            logger.error(f"Failed to clear collection: {str(e)}")
            raise RuntimeError(f"Clear operation failed: {str(e)}")

    def __repr__(self) -> str:
        return (
            f"VectorStoreService(collection={self.collection_name}, "
            f"host={self.host}, size={self.vector_size})"
        )


def get_vector_store_service(embedder_dim: int = 384) -> VectorStoreService:
    """Get a configured VectorStoreService from Django settings."""
    rag_config = getattr(settings, 'RAG_CONFIG', {})

    return VectorStoreService(
        host=rag_config.get('QDRANT_HOST', os.getenv('QDRANT_HOST', 'localhost')),
        port=rag_config.get('QDRANT_PORT', int(os.getenv('QDRANT_PORT', 6333))),
        api_key=rag_config.get('QDRANT_API_KEY', os.getenv('QDRANT_API_KEY')),
        collection_name=rag_config.get(
            'COLLECTION_NAME',
            os.getenv('QDRANT_COLLECTION_NAME', 'smbshield_knowledge')
        ),
        vector_size=embedder_dim,
        distance=Distance.COSINE
    )
