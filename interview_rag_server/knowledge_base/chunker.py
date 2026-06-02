"""Text chunking for knowledge base indexing.

Splits text into segments of ~max_tokens with overlap, preserving markdown
section headers as context prefixes.
"""

import re


def _split_into_words(text: str) -> list[str]:
    return text.split()


def chunk_text(text: str, max_tokens: int = 512, overlap_tokens: int = 64) -> list[dict]:
    """Split plain text into overlapping chunks.

    Returns list of dicts with 'text' and 'char_start' keys.
    Uses word-level splitting as token approximation.
    """
    words = _split_into_words(text)
    if len(words) <= max_tokens:
        return [{"text": text.strip(), "char_start": 0}]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunk_words = words[start:end]
        chunk_text_str = " ".join(chunk_words)
        chunks.append({"text": chunk_text_str, "char_start": start})
        if end >= len(words):
            break
        start = end - overlap_tokens

    return chunks


def chunk_markdown_file(
    content: str, max_tokens: int = 512, overlap_tokens: int = 64
) -> list[dict]:
    """Split markdown content into chunks, preserving section header context.

    Each chunk gets a 'section_header' field with the most recent heading.
    """
    lines = content.split("\n")
    sections: list[tuple[str, str]] = []
    current_header = ""
    current_lines: list[str] = []

    for line in lines:
        if re.match(r"^#{1,4}\s+", line):
            if current_lines:
                sections.append((current_header, "\n".join(current_lines)))
            current_header = line.strip().lstrip("#").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_header, "\n".join(current_lines)))

    chunks = []
    for header, section_text in sections:
        section_text_stripped = section_text.strip()
        if not section_text_stripped:
            continue
        raw_chunks = chunk_text(section_text_stripped, max_tokens, overlap_tokens)
        for chunk in raw_chunks:
            chunk["section_header"] = header
            if header and not chunk["text"].startswith("#"):
                chunk["text"] = f"[{header}] {chunk['text']}"
            chunks.append(chunk)

    return chunks
