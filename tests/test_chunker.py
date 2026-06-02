from interview_rag_server.knowledge_base.chunker import chunk_text, chunk_markdown_file


def test_chunk_text_basic():
    text = "word " * 600
    chunks = chunk_text(text, max_tokens=512, overlap_tokens=64)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk["text"].split()) <= 520


def test_chunk_text_preserves_content():
    text = "Hello world. This is a test document with some content."
    chunks = chunk_text(text, max_tokens=512, overlap_tokens=64)
    assert len(chunks) == 1
    assert chunks[0]["text"].strip() == text.strip()


def test_chunk_text_overlap():
    words = [f"w{i}" for i in range(1000)]
    text = " ".join(words)
    chunks = chunk_text(text, max_tokens=100, overlap_tokens=20)
    assert len(chunks) >= 2
    chunk0_words = chunks[0]["text"].split()
    chunk1_words = chunks[1]["text"].split()
    overlap_words = chunk0_words[-20:]
    assert chunk1_words[:20] == overlap_words


def test_chunk_markdown_file_preserves_headers():
    content = """# Main Title

## Section One

This is the first section with some content about agents.

## Section Two

This is the second section about RAG technology.
"""
    chunks = chunk_markdown_file(content, max_tokens=512, overlap_tokens=64)
    assert len(chunks) >= 1
    assert "Main Title" in chunks[0]["text"] or "Section" in chunks[0]["text"]


def test_chunk_markdown_file_metadata():
    content = """# Chapter Title

## Sub Section

Content here.
"""
    chunks = chunk_markdown_file(content, max_tokens=512, overlap_tokens=64)
    assert all("section_header" in c for c in chunks)
