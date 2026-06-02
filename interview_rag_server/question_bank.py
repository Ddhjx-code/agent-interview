"""Question bank for interview question retrieval."""

import json
import random
from pathlib import Path
from typing import Optional


_DATA_DIR = Path(__file__).parent / "data"


class QuestionBank:
    def __init__(self, data_path: Optional[Path] = None):
        path = data_path or (_DATA_DIR / "questions.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._questions = data["questions"]

    def get_questions(self, topic: str, difficulty: str = "medium", count: int = 3) -> list[dict]:
        matches = [
            q for q in self._questions
            if q["topic"] == topic and q["difficulty"] == difficulty
        ]
        if len(matches) <= count:
            return matches
        return random.sample(matches, count)

    def get_topics(self) -> list[str]:
        return sorted(set(q["topic"] for q in self._questions))

    def get_question_by_id(self, question_id: str) -> Optional[dict]:
        for q in self._questions:
            if q["id"] == question_id:
                return q
        return None
