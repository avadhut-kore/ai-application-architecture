"""Heading-aware deterministic chunking strategy for markdown documents."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .document import Chunk, Document, make_chunk_id

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


class HeadingAwareChunker:
    """Chunks structured markdown documents while preserving section headings and metadata.

    Ensures that chunks respect logical topic boundaries defined by markdown headings
    rather than splitting arbitrarily across sentences.
    """

    def __init__(
        self,
        max_chunk_chars: int = 800,
        min_chunk_chars: int = 50,
        overlap_chars: int = 0,
    ) -> None:
        if max_chunk_chars <= min_chunk_chars:
            raise ValueError(
                f"max_chunk_chars ({max_chunk_chars}) must be greater than min_chunk_chars ({min_chunk_chars})"
            )
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars
        self.overlap_chars = overlap_chars

    def chunk_document(self, document: Document) -> List[Chunk]:
        """Split a document into deterministic chunks preserving section context."""
        content = document.content.strip()
        if not content:
            return []

        # Find all heading positions
        matches = list(HEADING_PATTERN.finditer(content))
        if not matches:
            # No headings: chunk purely by paragraphs
            return self._chunk_paragraphs(
                document=document,
                section_title=document.title,
                text=content,
                start_index=0,
            )

        chunks: List[Chunk] = []
        chunk_idx = 0

        # Process preamble before first heading if substantial
        first_match = matches[0]
        if first_match.start() > 0:
            preamble = content[: first_match.start()].strip()
            if len(preamble) >= self.min_chunk_chars:
                preamble_chunks = self._chunk_paragraphs(
                    document=document,
                    section_title=f"{document.title} (Overview)",
                    text=preamble,
                    start_index=chunk_idx,
                )
                chunks.extend(preamble_chunks)
                chunk_idx += len(preamble_chunks)

        # Process each heading section
        for i, match in enumerate(matches):
            heading_level = len(match.group(1))
            heading_title = match.group(2).strip()

            # Skip main document H1 heading if identical to title
            section_start = match.end()
            section_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_body = content[section_start:section_end].strip()

            if not section_body and heading_level == 1:
                # Top level header with no immediate text before subheadings
                continue

            full_section_text = f"## {heading_title}\n\n{section_body}".strip() if section_body else f"## {heading_title}"

            if len(full_section_text) <= self.max_chunk_chars:
                chunk = Chunk(
                    chunk_id=make_chunk_id(document.document_id, chunk_idx),
                    document_id=document.document_id,
                    chunk_index=chunk_idx,
                    text=full_section_text,
                    section_title=heading_title,
                    metadata=dict(document.metadata),
                )
                chunks.append(chunk)
                chunk_idx += 1
            else:
                # Section is oversized: split paragraphs within this section
                sub_chunks = self._chunk_paragraphs(
                    document=document,
                    section_title=heading_title,
                    text=section_body,
                    start_index=chunk_idx,
                    section_prefix=f"## {heading_title}\n\n",
                )
                chunks.extend(sub_chunks)
                chunk_idx += len(sub_chunks)

        return chunks

    def _chunk_paragraphs(
        self,
        document: Document,
        section_title: str,
        text: str,
        start_index: int,
        section_prefix: str = "",
    ) -> List[Chunk]:
        """Split a long text block into bounded chunks preserving paragraph boundaries."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return []

        chunks: List[Chunk] = []
        current_idx = start_index
        current_buffer: List[str] = []
        current_len = len(section_prefix)

        for para in paragraphs:
            para_len = len(para) + 2  # plus \n\n
            if current_buffer and (current_len + para_len > self.max_chunk_chars):
                chunk_text = section_prefix + "\n\n".join(current_buffer)
                chunks.append(
                    Chunk(
                        chunk_id=make_chunk_id(document.document_id, current_idx),
                        document_id=document.document_id,
                        chunk_index=current_idx,
                        text=chunk_text,
                        section_title=section_title,
                        metadata=dict(document.metadata),
                    )
                )
                current_idx += 1
                current_buffer = [para]
                current_len = len(section_prefix) + para_len
            else:
                current_buffer.append(para)
                current_len += para_len

        if current_buffer:
            chunk_text = section_prefix + "\n\n".join(current_buffer)
            chunks.append(
                Chunk(
                    chunk_id=make_chunk_id(document.document_id, current_idx),
                    document_id=document.document_id,
                    chunk_index=current_idx,
                    text=chunk_text,
                    section_title=section_title,
                    metadata=dict(document.metadata),
                )
            )

        return chunks
