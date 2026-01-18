"""
RAG Retriever Service - Orchestrates the complete RAG pipeline

This ties everything together:
1. Embedder: Convert query to vector
2. VectorStore: Search for similar chunks
3. Agent: Generate answer with context (uses shared LLM config)
"""

from .embedder import embedder_service
from .vector_store import VectorStoreService, get_vector_store_service
from typing import Dict, Any, List, Optional
import logging
import os
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from django.conf import settings

logger = logging.getLogger(__name__)


# =============================================================================
# OUTPUT MODELS
# =============================================================================

class Citation(BaseModel):
    """A single source citation."""
    source: str = Field(description="Document source (filename or title)")
    page: Optional[int] = Field(None, description="Page number if available")
    section: Optional[str] = Field(None, description="Section or heading")


class RAGAnswer(BaseModel):
    """Structured output from RAG query."""
    answer: str = Field(description="The answer to the user's question", min_length=10)
    citations: List[Citation] = Field(default_factory=list, description="Sources used")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")
    follow_up_questions: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Suggested follow-up questions"
    )


# =============================================================================
# RAG RETRIEVER
# =============================================================================

class RAGRetriever:
    """Complete RAG retrieval pipeline."""

    def __init__(
        self,
        vector_store: Optional[VectorStoreService] = None,
        top_k: int = 5,
        score_threshold: float = 0.7
    ):
        self.embedder = embedder_service
        self._vector_store = vector_store
        self.top_k = top_k
        self.score_threshold = score_threshold
        self._agent = None

        logger.info(f"RAGRetriever initialized (top_k={top_k}, threshold={score_threshold})")

    @property
    def vector_store(self) -> VectorStoreService:
        """Lazy-load vector store to avoid connection at import time."""
        if self._vector_store is None:
            self._vector_store = get_vector_store_service(
                embedder_dim=self.embedder.get_embedding_dimension()
            )
        return self._vector_store

    @property
    def agent(self) -> Agent:
        """Lazy-load agent with shared LLM config from agents/base.py."""
        if self._agent is None:
            # Import the shared LLM configuration
            try:
                from agents.base import get_llm_model
                model = get_llm_model()
            except ImportError:
                # Fallback if agents module not available
                model = os.getenv("AGENT_MODEL", "anthropic:claude-sonnet-4-20250514")
                logger.warning(f"Could not import agents.base, using fallback model: {model}")

            self._agent = Agent(
                model=model,
                output_type=RAGAnswer,
                system_prompt=self._get_system_prompt()
            )
        return self._agent

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the RAG agent."""
        return """
You are Professor Shield's Knowledge Assistant, a cybersecurity expert for small and medium businesses.

Your role:
- Answer questions about cybersecurity using ONLY the provided context
- Explain technical concepts in simple, accessible language
- Always cite your sources accurately
- If information isn't in the context, say "I don't have information about that in my knowledge base"
- Focus on actionable advice for non-technical business owners

Communication style:
- Friendly but professional
- Use analogies to explain complex topics
- Break down information into bullet points when helpful
- Provide 1-3 follow-up questions to deepen learning

Never:
- Make up information not in the context
- Cite sources not provided
- Be condescending
"""

    def search(
        self,
        question: str,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant chunks.

        Args:
            question: The search query
            filter_conditions: Optional metadata filters

        Returns:
            List of context chunks with scores
        """
        logger.info(f"Searching for: {question[:100]}...")

        # Embed the question
        query_embedding = self.embedder.encode_query(question)

        # Search vector store
        search_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=self.top_k,
            score_threshold=self.score_threshold,
            filter_conditions=filter_conditions
        )

        # Convert to context chunks
        context_chunks = [
            {
                "text": result.payload.get('text', ''),
                "source": result.payload.get('source', 'Unknown'),
                "page": result.payload.get('page'),
                "section": result.payload.get('section'),
                "score": result.score
            }
            for result in search_results
        ]

        return context_chunks

    async def search_async(
        self,
        question: str,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Async version of search (wraps sync for now)."""
        return self.search(question, filter_conditions)

    def query(
        self,
        question: str,
        user_id: Optional[str] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete RAG query: embed -> search -> generate answer.

        Args:
            question: User's question
            user_id: Optional user ID
            filter_conditions: Optional metadata filters

        Returns:
            Dict with answer, citations, confidence, etc.
        """
        logger.info(f"Processing query: {question[:100]}...")

        # Search for context
        context_chunks = self.search(question, filter_conditions)

        if not context_chunks:
            logger.warning("No relevant context found")
            return {
                "answer": "I couldn't find relevant information to answer your question in my knowledge base.",
                "citations": [],
                "confidence": 0.0,
                "follow_up_questions": [],
                "search_results_count": 0
            }

        # Format context for prompt
        context_text = self._format_context(context_chunks)

        # Build prompt
        prompt = f"""Context from knowledge base:
{context_text}

User question: {question}

Provide a helpful answer based on the context above. Remember to:
1. Cite your sources
2. Assess your confidence based on context quality
3. Suggest follow-up questions
4. Use simple language for non-technical users
"""

        try:
            # Generate answer using the agent
            result = self.agent.run_sync(prompt)
            answer = result.output

            return {
                "answer": answer.answer,
                "citations": [
                    {"source": c.source, "page": c.page, "section": c.section}
                    for c in answer.citations
                ],
                "confidence": answer.confidence,
                "follow_up_questions": answer.follow_up_questions,
                "search_results_count": len(context_chunks)
            }

        except Exception as e:
            logger.error(f"Agent failed to generate answer: {str(e)}")
            return {
                "answer": "I encountered an error generating a response. Please try again.",
                "citations": [],
                "confidence": 0.0,
                "follow_up_questions": [],
                "search_results_count": len(context_chunks),
                "error": str(e)
            }

    async def query_async(
        self,
        question: str,
        user_id: Optional[str] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async version of query."""
        logger.info(f"Processing async query: {question[:100]}...")

        context_chunks = self.search(question, filter_conditions)

        if not context_chunks:
            return {
                "answer": "I couldn't find relevant information in my knowledge base.",
                "citations": [],
                "confidence": 0.0,
                "follow_up_questions": [],
                "search_results_count": 0
            }

        context_text = self._format_context(context_chunks)

        prompt = f"""Context from knowledge base:
{context_text}

User question: {question}
"""

        try:
            result = await self.agent.run(prompt)
            answer = result.output

            return {
                "answer": answer.answer,
                "citations": [
                    {"source": c.source, "page": c.page, "section": c.section}
                    for c in answer.citations
                ],
                "confidence": answer.confidence,
                "follow_up_questions": answer.follow_up_questions,
                "search_results_count": len(context_chunks)
            }

        except Exception as e:
            logger.error(f"Agent failed (async): {str(e)}")
            return {
                "answer": "Error generating response.",
                "citations": [],
                "confidence": 0.0,
                "follow_up_questions": [],
                "search_results_count": len(context_chunks),
                "error": str(e)
            }

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into a readable context string."""
        if not chunks:
            return "No relevant context found."

        formatted_parts = []

        for i, chunk in enumerate(chunks, 1):
            text = chunk.get('text', '')
            source = chunk.get('source', 'Unknown')
            page = chunk.get('page')
            section = chunk.get('section')

            source_ref = f"Source: {source}"
            if page:
                source_ref += f", Page {page}"
            if section:
                source_ref += f", Section: {section}"

            chunk_text = f"""
--- Context {i} ---
{source_ref}

{text}
"""
            formatted_parts.append(chunk_text)

        return "\n".join(formatted_parts)


# Global instance (lazy-loaded)
def get_rag_retriever() -> RAGRetriever:
    """Get the RAG retriever instance."""
    rag_config = getattr(settings, 'RAG_CONFIG', {})

    return RAGRetriever(
        top_k=rag_config.get('TOP_K', 5),
        score_threshold=rag_config.get('SCORE_THRESHOLD', 0.7)
    )


# Singleton instance for easy import
rag_retriever = RAGRetriever()
