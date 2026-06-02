"""One-time script to build the FAISS vector index from source projects.

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

    print(f"\nTotal chunks: {chunk_id}")
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

    print("\n[1/4] Extracting and chunking source files...")
    chunks = build_chunks()

    if not chunks:
        print("ERROR: No chunks produced. Check file paths.")
        sys.exit(1)

    print(f"\n[2/4] Generating embeddings for {len(chunks)} chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts, batch_size=32)
    print(f"  Embedding shape: {embeddings.shape}")

    print("\n[3/4] Building FAISS index...")
    store = VectorStore(dim=embeddings.shape[1])
    store.add(embeddings, chunks)

    output_dir = DATA_DIR
    print(f"\n[4/4] Saving to {output_dir}...")
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
