"""Context construction and evidence budget management with untrusted boundary protection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from .retriever import RetrievalResult

EVIDENCE_HEADER = "=== BEGIN RETRIEVED EVIDENCE (UNTRUSTED DATA) ==="
EVIDENCE_FOOTER = "=== END RETRIEVED EVIDENCE ==="


@dataclass(frozen=True)
class ContextBuildResult:
    """Result payload produced by ContextBuilder."""

    formatted_context: str
    included_chunk_ids: List[str]
    total_chars: int
    chunks_count: int
    truncated: bool = False


class ContextBuilder:
    """Constructs bounded, delimited evidence context blocks from retrieved chunks.

    Enforces the Untrusted Evidence Principle: retrieved content is formatted with
    strict security boundaries to mitigate prompt injection risks and prevent model hijacking.
    """

    def __init__(
        self,
        max_chunks: int = 5,
        max_chars: int = 4000,
    ) -> None:
        if max_chunks <= 0:
            raise ValueError(f"max_chunks must be positive, got {max_chunks}")
        if max_chars <= 0:
            raise ValueError(f"max_chars must be positive, got {max_chars}")
        self.max_chunks = max_chunks
        self.max_chars = max_chars

    def build_context(self, retrieval_results: Sequence[RetrievalResult]) -> ContextBuildResult:
        """Format retrieved chunks into a safe, bounded evidence context string."""
        if not retrieval_results:
            return ContextBuildResult(
                formatted_context="[NO RELEVANT EVIDENCE FOUND]",
                included_chunk_ids=[],
                total_chars=0,
                chunks_count=0,
                truncated=False,
            )

        included_ids: List[str] = []
        blocks: List[str] = []
        current_len = len(EVIDENCE_HEADER) + len(EVIDENCE_FOOTER) + 4
        truncated = False

        for res in retrieval_results[: self.max_chunks]:
            chunk = res.chunk
            header = f"[Source ID: {chunk.chunk_id}] (Section: {chunk.section_title or 'General'})"
            entry = f"{header}\n{chunk.text.strip()}"
            entry_len = len(entry) + 2  # plus separator \n\n

            if (current_len + entry_len) > self.max_chars:
                truncated = True
                break

            blocks.append(entry)
            included_ids.append(chunk.chunk_id)
            current_len += entry_len

        if not blocks:
            # Even first chunk exceeded budget; take truncated first chunk
            first_res = retrieval_results[0]
            chunk = first_res.chunk
            allowed_text_len = max(50, self.max_chars - 200)
            truncated_text = chunk.text[:allowed_text_len] + "... [TRUNCATED DUE TO BUDGET]"
            entry = f"[Source ID: {chunk.chunk_id}] (Section: {chunk.section_title or 'General'})\n{truncated_text}"
            blocks.append(entry)
            included_ids.append(chunk.chunk_id)
            current_len = len(entry)
            truncated = True

        formatted = f"{EVIDENCE_HEADER}\n\n" + "\n\n".join(blocks) + f"\n\n{EVIDENCE_FOOTER}"

        return ContextBuildResult(
            formatted_context=formatted,
            included_chunk_ids=included_ids,
            total_chars=len(formatted),
            chunks_count=len(blocks),
            truncated=truncated,
        )
