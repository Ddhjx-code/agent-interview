from interview_rag_server.learning_path import get_learning_path


def test_get_learning_path_single_topic():
    result = get_learning_path(["rag"])
    assert "recommendations" in result
    assert len(result["recommendations"]) >= 1
    rec = result["recommendations"][0]
    assert "topic" in rec
    assert "resources" in rec
    assert "priority" in rec


def test_get_learning_path_multiple_topics():
    result = get_learning_path(["llm", "agent", "rag"])
    assert len(result["recommendations"]) == 3
    priorities = [r["priority"] for r in result["recommendations"]]
    assert priorities == sorted(priorities)


def test_get_learning_path_unknown_topic():
    result = get_learning_path(["nonexistent_topic"])
    assert len(result["recommendations"]) == 1
    assert "generic" in result["recommendations"][0].get("resources", [{}])[0].get("type", "generic")
