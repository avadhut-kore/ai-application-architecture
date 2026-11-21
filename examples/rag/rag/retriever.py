"""Retriever component decoupling knowledge search from language model generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Mapping, Optional

from contracts.models import EmbeddingRequest
from contracts.ports import EmbeddingPort
from contracts.telemetry import AiOperationContext
from ai_telemetry import traced

from .document import Chunk
from .vector_index import VectorIndexPort


@dataclass(frozen=True)
class RetrievalResult:
    """Represents an individual retrieved chunk with its rank and similarity score."""

    chunk: Chunk
    score: float
    rank: int

    @property
    def chunk_id(self) -> str:
        return self.chunk.chunk_id

    @property
    def document_id(self) -> str:
        return self.chunk.document_id

    @property
    def text(self) -> str:
        return self.chunk.text


class Retriever:
    """Knowledge retriever coordinating query vectorization and similarity retrieval."""

    def __init__(
        self,
        embedding_port: EmbeddingPort,
        vector_index: VectorIndexPort,
        embedding_model: str = "nomic-embed-text",
        default_top_k: int = 3,
        min_relevance_score: Optional[float] = None,
        prefer_primary_document: bool = False,
    ) -> None:
        self.embedding_port = embedding_port
        self.vector_index = vector_index
        self.embedding_model = embedding_model
        self.default_top_k = default_top_k
        self.min_relevance_score = min_relevance_score
        self.prefer_primary_document = prefer_primary_document

    @traced("rag.retrieve", "local")
    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Mapping[str, Any]] = None,
        min_score: Optional[float] = None,
        context: Optional[AiOperationContext] = None,
    ) -> List[RetrievalResult]:
        """Execute semantic retrieval for a user query.

        Does NOT invoke any text generation model or LLM.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        k = top_k if top_k is not None else self.default_top_k

        # 1. Embed query text using the configured EmbeddingPort
        request = EmbeddingRequest(
            inputs=[clean_query], model=self.embedding_model, metadata={"input_type": "query"}
        )
        response = await self.embedding_port.embed(request, context=context)

        query_vector = response.embeddings[0]

        # 2. Search the vector index
        scored_chunks = self.vector_index.search(
            query_vector=query_vector,
            top_k=k,
            filters=filters,
        )

        # 3. Format into ranked results (1-indexed)
        results: List[RetrievalResult] = []
        for rank, sc in enumerate(scored_chunks, start=1):
            results.append(
                RetrievalResult(
                    chunk=sc.chunk,
                    score=sc.score,
                    rank=rank,
                )
            )

        # 4. Apply evidence sufficiency policy if threshold is configured
        threshold = min_score if min_score is not None else self.min_relevance_score
        if threshold is not None:
            results = [r for r in results if r.score >= threshold]

        if self.prefer_primary_document and len(results) > 2:
            primary_document = results[0].document_id
            selected = results[:2] + [
                row for row in results[2:] if row.document_id == primary_document
            ]
            results = [
                RetrievalResult(row.chunk, row.score, rank) for rank, row in enumerate(selected, 1)
            ]

        return results
