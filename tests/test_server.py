"""Tests for MCP server tool functions (unit-level, no MCP transport)."""

from pathlib import Path

import pytest


def test_search_knowledge_returns_results():
    from interview_rag_server.server import _search_knowledge_impl

    data_dir = Path(__file__).parent.parent / "interview_rag_server" / "data"
    if not (data_dir / "faiss_index.bin").exists():
        pytest.skip("Index not built yet")

    results = _search_knowledge_impl("什么是ReAct框架", topic=None, top_k=3)
    assert len(results) <= 3
    assert all("text" in r for r in results)
    assert all("source" in r for r in results)


def test_search_knowledge_with_topic_filter():
    from interview_rag_server.server import _search_knowledge_impl

    data_dir = Path(__file__).parent.parent / "interview_rag_server" / "data"
    if not (data_dir / "faiss_index.bin").exists():
        pytest.skip("Index not built yet")

    results = _search_knowledge_impl("Agent架构", topic="agent", top_k=3)
    assert all(r["topic"] == "agent" for r in results)


def test_get_interview_questions_returns_questions():
    from interview_rag_server.server import _get_interview_questions_impl

    questions = _get_interview_questions_impl(topic="agent", difficulty="medium", count=2)
    assert len(questions) <= 2
    assert all("question" in q for q in questions)


def test_get_learning_path_returns_recommendations():
    from interview_rag_server.server import _get_learning_path_impl

    result = _get_learning_path_impl(weak_topics=["rag", "memory"])
    assert "recommendations" in result
    assert len(result["recommendations"]) == 2
