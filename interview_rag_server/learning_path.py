"""Learning path generator based on identified weak topics."""

import json
from pathlib import Path


_DATA_DIR = Path(__file__).parent / "data"


def get_learning_path(weak_topics: list[str]) -> dict:
    """Generate prioritized learning recommendations for weak topics."""
    paths_file = _DATA_DIR / "learning_paths.json"
    with open(paths_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_paths = data["paths"]
    recommendations = []

    for topic in weak_topics:
        if topic in all_paths:
            path_info = all_paths[topic]
            recommendations.append({
                "topic": topic,
                "display_name": path_info["display_name"],
                "resources": path_info["resources"],
                "key_concepts": path_info["key_concepts"],
                "priority": path_info["priority_weight"],
            })
        else:
            recommendations.append({
                "topic": topic,
                "display_name": topic,
                "resources": [{"type": "generic", "ref": "hello-agents 全书", "title": "系统学习智能体"}],
                "key_concepts": [],
                "priority": 1,
            })

    recommendations.sort(key=lambda r: r["priority"])
    return {"recommendations": recommendations}
