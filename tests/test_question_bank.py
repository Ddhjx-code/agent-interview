from interview_rag_server.question_bank import QuestionBank


def test_get_questions_by_topic():
    bank = QuestionBank()
    questions = bank.get_questions(topic="agent", difficulty="medium", count=3)
    assert len(questions) <= 3
    assert all(q["topic"] == "agent" for q in questions)
    assert all("question" in q for q in questions)


def test_get_questions_by_difficulty():
    bank = QuestionBank()
    easy = bank.get_questions(topic="llm", difficulty="easy", count=5)
    hard = bank.get_questions(topic="llm", difficulty="hard", count=5)
    assert all(q["difficulty"] == "easy" for q in easy)
    assert all(q["difficulty"] == "hard" for q in hard)


def test_get_questions_returns_metadata():
    bank = QuestionBank()
    questions = bank.get_questions(topic="rag", difficulty="medium", count=1)
    if questions:
        q = questions[0]
        assert "key_points" in q
        assert "source" in q


def test_get_all_topics():
    bank = QuestionBank()
    topics = bank.get_topics()
    assert "llm" in topics
    assert "agent" in topics
    assert "rag" in topics
