"""Build the FAISS vector index from local source projects and web sources.

Usage:
    python -m interview_rag_server.knowledge_base.build_index
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from interview_rag_server.knowledge_base.chunker import chunk_markdown_file, chunk_text
from interview_rag_server.knowledge_base.embedder import embed_texts
from interview_rag_server.vector_store import VectorStore


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAPPING_FILE = DATA_DIR / "topic_file_mapping.json"
WEB_MAPPING_FILE = DATA_DIR / "web_source_mapping.json"
WEB_SOURCES_DIR = DATA_DIR / "web_sources"


def load_file_content(filepath: Path) -> str:
    try:
        return filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return filepath.read_text(encoding="utf-8", errors="ignore")


def build_chunks() -> list[dict]:
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    all_chunks = []
    chunk_id = 0

    for entry in mapping["mappings"]:
        topic = entry["topic"]
        content_type = entry["content_type"]

        for rel_path in entry["files"]:
            filepath = WORKSPACE_ROOT / rel_path
            if not filepath.exists():
                print(f"  [SKIP] {rel_path} (not found)")
                continue

            print(f"  [READ] {rel_path} ({topic})")
            content = load_file_content(filepath)

            if not content.strip():
                continue

            if filepath.suffix == ".md":
                chunks = chunk_markdown_file(content, max_tokens=512, overlap_tokens=64)
            else:
                chunks = chunk_text(content, max_tokens=512, overlap_tokens=64)

            for chunk in chunks:
                all_chunks.append({
                    "id": chunk_id,
                    "text": chunk["text"],
                    "topic": topic,
                    "source": rel_path,
                    "content_type": content_type,
                    "section_header": chunk.get("section_header", ""),
                })
                chunk_id += 1

    print(f"\n  Local file chunks: {chunk_id}")
    return all_chunks, chunk_id


def build_web_chunks(start_id: int = 0) -> list[dict]:
    if not WEB_MAPPING_FILE.exists():
        print("  [SKIP] No web_source_mapping.json found")
        return []

    with open(WEB_MAPPING_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    all_chunks = []
    chunk_id = start_id

    for entry in mapping["sources"]:
        filepath = DATA_DIR / entry["file"]
        if not filepath.exists():
            continue

        content = load_file_content(filepath)
        if not content.strip():
            continue

        # Strip frontmatter
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                content = content[end + 3:].strip()

        title = entry.get("title", "")
        url = entry.get("url", "")
        topic = entry.get("topic", "agent")
        source_type = entry.get("source_type", "web")

        print(f"  [WEB] {title or url[:60]} ({topic})")

        chunks = chunk_markdown_file(content, max_tokens=512, overlap_tokens=64)

        for chunk in chunks:
            all_chunks.append({
                "id": chunk_id,
                "text": chunk["text"],
                "topic": topic,
                "source": url,
                "content_type": source_type,
                "section_header": chunk.get("section_header", ""),
            })
            chunk_id += 1

    print(f"  Web source chunks: {chunk_id - start_id}")
    return all_chunks


def build_topic_index(chunks: list[dict]) -> dict:
    topic_index: dict[str, list[int]] = {}
    for chunk in chunks:
        topic = chunk["topic"]
        if topic not in topic_index:
            topic_index[topic] = []
        topic_index[topic].append(chunk["id"])
    return topic_index


def main():
    print("=" * 60)
    print("Building knowledge base index...")
    print("=" * 60)

    print("\n[1/5] Extracting and chunking local source files...")
    local_chunks, next_id = build_chunks()

    print("\n[2/5] Extracting and chunking web sources...")
    web_chunks = build_web_chunks(start_id=next_id)

    chunks = local_chunks + web_chunks
    print(f"\nTotal chunks: {len(chunks)}")

    if not chunks:
        print("ERROR: No chunks produced. Check file paths.")
        sys.exit(1)

    print(f"\n[3/5] Generating embeddings for {len(chunks)} chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts, batch_size=32)
    print(f"  Embedding shape: {embeddings.shape}")

    print("\n[4/5] Building FAISS index...")
    store = VectorStore(dim=embeddings.shape[1])
    store.add(embeddings, chunks)

    output_dir = DATA_DIR
    print(f"\n[5/5] Saving to {output_dir}...")
    store.save(output_dir)

    topic_index = build_topic_index(chunks)
    with open(output_dir / "topic_index.json", "w", encoding="utf-8") as f:
        json.dump(topic_index, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Index saved to {output_dir}")
    print(f"  - faiss_index.bin ({store.size} vectors)")
    print(f"  - metadata.json ({len(chunks)} entries)")
    print(f"  - topic_index.json ({len(topic_index)} topics)")


if __name__ == "__main__":
    main()
