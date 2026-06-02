"""Interview RAG MCP Server.

Exposes tools for knowledge search, question retrieval, and learning path
generation via the Model Context Protocol.
"""

import json
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from interview_rag_server.knowledge_base.embedder import embed_query
from interview_rag_server.learning_path import get_learning_path as _get_lp
from interview_rag_server.question_bank import QuestionBank
from interview_rag_server.vector_store import VectorStore


DATA_DIR = Path(__file__).parent / "data"

mcp = FastMCP("interview-rag")

_store: Optional[VectorStore] = None
_question_bank: Optional[QuestionBank] = None


def _get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore.load(DATA_DIR)
    return _store


def _get_question_bank() -> QuestionBank:
    global _question_bank
    if _question_bank is None:
        _question_bank = QuestionBank()
    return _question_bank


def _search_knowledge_impl(
    query: str, topic: Optional[str] = None, top_k: int = 5
) -> list[dict]:
    store = _get_store()
    query_vec = embed_query(query)
    results = store.search(query_vec, top_k=top_k, topic_filter=topic)
    return [
        {
            "text": r["text"],
            "topic": r["topic"],
            "source": r["source"],
            "content_type": r["content_type"],
            "score": r["score"],
        }
        for r in results
    ]


def _get_interview_questions_impl(
    topic: str, difficulty: str = "medium", count: int = 3
) -> list[dict]:
    bank = _get_question_bank()
    return bank.get_questions(topic=topic, difficulty=difficulty, count=count)


def _get_learning_path_impl(weak_topics: list[str]) -> dict:
    return _get_lp(weak_topics)


@mcp.tool()
def search_knowledge(query: str, topic: str = "", top_k: int = 5) -> str:
    """Semantic search over the AI Agent knowledge base.

    Searches through content from hello-agents tutorial and Photo-agents
    framework to find relevant knowledge chunks.

    Args:
        query: Natural language search query (Chinese or English)
        topic: Optional topic filter. One of: llm, agent, rag, memory,
               multi-agent, rlhf, vlm, evaluation, engineering.
               Leave empty for all topics.
        top_k: Number of results to return (default 5)
    """
    topic_filter = topic if topic else None
    results = _search_knowledge_impl(query, topic=topic_filter, top_k=top_k)
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def get_interview_questions(topic: str, difficulty: str = "medium", count: int = 3) -> str:
    """Get interview questions for a specific topic and difficulty level.

    Args:
        topic: Knowledge domain. One of: llm, agent, rag, memory,
               multi-agent, rlhf, vlm, evaluation, engineering
        difficulty: Question difficulty. One of: easy, medium, hard
        count: Number of questions to retrieve (default 3)
    """
    results = _get_interview_questions_impl(topic, difficulty, count)
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def get_learning_path(weak_topics: str) -> str:
    """Generate learning recommendations based on identified weak areas.

    Args:
        weak_topics: Comma-separated list of weak topic slugs.
                     Options: llm, agent, rag, memory, multi-agent,
                     rlhf, vlm, evaluation, engineering
    """
    topics = [t.strip() for t in weak_topics.split(",") if t.strip()]
    result = _get_learning_path_impl(topics)
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
