# Interview RAG Server

MCP server providing RAG-powered knowledge retrieval for AI Agent interview simulation.

## Setup

```bash
pip install -r requirements.txt
python -m interview_rag_server.knowledge_base.build_index
```

## Usage

Configured as MCP server in `.claude/settings.json`. Starts automatically when Claude Code loads the project.

Use the `/agent-interview` skill in Claude Code with a resume path:
```
/agent-interview path/to/resume.pdf
```

## Tools

- `search_knowledge(query, topic, top_k)` — Semantic search over knowledge base
- `get_interview_questions(topic, difficulty, count)` — Get interview questions
- `get_learning_path(weak_topics)` — Get learning recommendations

## Rebuild Index

If source materials change:
```bash
python -m interview_rag_server.knowledge_base.build_index
```
