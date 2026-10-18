"""Text chunker module for RAG ingestion.

Specification Section 8.1:
Chunks text into segments of ~800 characters with ~100 character overlap,
splitting on paragraph or sentence boundaries where possible.
"""

from typing import List


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Splits a document text into overlapping chunks respecting sentence/paragraph breaks.

    Args:
        text: Raw document string.
        chunk_size: Target character length per chunk (~800 chars).
        overlap: Overlap character length between successive chunks (~100 chars).

    Returns:
        List of text chunk strings.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # Look for natural paragraph break near end
        break_pos = text.rfind("\n\n", start + chunk_size // 2, end)
        if break_pos == -1:
            # Look for sentence boundary (. ! ?)
            for p in range(end, start + chunk_size // 2, -1):
                if text[p - 1:p + 1] in [". ", "? ", "! ", ".\n", "?\n", "!\n"]:
                    break_pos = p
                    break

        if break_pos == -1:
            # Look for space
            break_pos = text.rfind(" ", start + chunk_size // 2, end)

        if break_pos == -1 or break_pos <= start:
            break_pos = end

        chunk = text[start:break_pos].strip()
        if chunk:
            chunks.append(chunk)

        # Advance start position considering overlap
        start = break_pos - overlap if (break_pos - overlap) > start else break_pos

    return chunks
