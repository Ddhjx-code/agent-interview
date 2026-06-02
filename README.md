# Agent Interview

AI Agent 岗位模拟面试系统 —— 基于 Claude Code Skill + MCP Server + RAG 知识库，为求职者提供沉浸式的 AI Agent 技术面试模拟与评估。

## 功能

- **简历解析**：读取候选人简历（PDF/MD/TXT），分析技术背景和目标岗位
- **多轮面试**：覆盖 LLM、Agent、RAG、记忆系统、多智能体、RLHF、VLM、工程实践等方向
- **自适应难度**：根据候选人回答质量动态调整问题深度
- **RAG 知识库**：基于 hello-agents（16章系统教程）、Agent-Learning-Hub（学习路线图 + 90+ 外部资源）构建
- **评估报告**：生成包含知识评分、学习方向、改进建议和简历修改建议的完整报告

## 架构

```
┌─────────────────────────────────────────────┐
│  Claude Code                                │
│                                             │
│  /interview [resume_path]                   │
│       ↓                                     │
│  ┌─────────────────────────────────────┐    │
│  │  agent-interview Skill              │    │
│  │  面试流程编排 + 评估 + 报告生成      │    │
│  └──────────────┬──────────────────────┘    │
│                 │ MCP tool calls             │
│  ┌──────────────▼──────────────────────┐    │
│  │  interview-rag MCP Server           │    │
│  │                                     │    │
│  │  search_knowledge    语义检索知识库   │    │
│  │  get_interview_questions 获取面试题  │    │
│  │  get_learning_path   生成学习路径    │    │
│  │                                     │    │
│  │  FAISS + bge-base-zh-v1.5           │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r interview_rag_server/requirements.txt
```

需要的核心依赖：
- `fastmcp` >= 2.0.0
- `faiss-cpu` >= 1.7.4
- `sentence-transformers` >= 2.2.0

### 2. 构建知识库索引

首次使用需要从源项目构建向量索引：

```bash
# 克隆知识源项目（构建完成后可删除）
git clone https://github.com/datawhalechina/hello-agents.git
git clone https://github.com/datawhalechina/Agent-Learning-Hub.git

# 抓取 Agent-Learning-Hub 中引用的外部资源（官方文档、论文、开源项目 README）
python -m interview_rag_server.knowledge_base.fetch_web_sources

# 构建 FAISS 索引
python -m interview_rag_server.knowledge_base.build_index
```

构建完成后会在 `interview_rag_server/data/` 下生成：
- `faiss_index.bin` — 向量索引（1086 vectors, 768-dim）
- `metadata.json` — 文本块元数据

源项目目录在索引构建完成后可以安全删除。

### 3. 配置 Claude Code

确保 `.claude/settings.json` 中已配置 MCP Server：

```json
{
  "mcpServers": {
    "interview-rag": {
      "command": "python",
      "args": ["-m", "interview_rag_server.server"],
      "cwd": "/path/to/agent_study",
      "env": {
        "EMBEDDING_MODEL": "BAAI/bge-base-zh-v1.5",
        "HF_HUB_OFFLINE": "1"
      }
    }
  }
}
```

### 4. 开始面试

在 Claude Code 中使用 `/interview` 技能：

```
/interview path/to/resume.pdf
```

## 面试流程

1. **简历分析** — 解析候选人背景，确定面试重点
2. **热身问题** — 1 轮宽泛问题，评估基线水平
3. **知识面试** — 3-5 轮，覆盖 Agent 技术全栈
4. **项目深挖** — 1-2 轮，针对简历中的项目追问
5. **评估报告** — 生成结构化评估，含学习路径和简历建议

## 知识覆盖

| 主题 | 来源 |
|------|------|
| LLM 基础 | hello-agents Ch.3, Extra01 |
| Agent 架构 | hello-agents Ch.1/4/6/7, Agent-Learning-Hub Stage 0-1, Anthropic/OpenAI 官方指南 |
| RAG 技术 | hello-agents Ch.8, Agent-Learning-Hub Stage 2, GPT Researcher/RAGFlow 等项目 |
| 记忆系统 | hello-agents Ch.8, Agent-Learning-Hub Stage 2, mem0/Letta 等项目 |
| 多智能体 | hello-agents Ch.15, Agent-Learning-Hub Stage 4, A2A/ACP 协议文档 |
| RLHF/对齐 | hello-agents Ch.11 |
| VLM | hello-agents Extra01, Agent-Learning-Hub Stage 6 |
| 评估方法 | hello-agents Ch.12, Agent-Learning-Hub Stage 7, AgentBench/SWE-bench 论文 |
| 工程实践 | hello-agents Ch.9/10, Agent-Learning-Hub Stage 3/5/8, Claude Code Docs, learn-claude-code |
| Agent Harness | Agent-Learning-Hub Stage 3, Dive into Claude Code 论文, AI Harness Engineering 论文 |
| Skills/协议 | Agent-Learning-Hub Stage 5, MCP/A2A/ACP 协议文档 |

## MCP Server Tools

| Tool | 用途 | 参数 |
|------|------|------|
| `search_knowledge` | 语义检索知识库 | query, topic?, top_k? |
| `get_interview_questions` | 获取分级面试题 | topic, difficulty?, count? |
| `get_learning_path` | 生成学习路径 | weak_topics |

## 测试

```bash
pytest tests/ -v
```

## 项目结构

```
.
├── .claude/
│   ├── skills/agent-interview.md   # Claude Code 技能文件
│   └── settings.json               # MCP Server 配置
├── interview_rag_server/
│   ├── server.py                   # MCP Server 入口
│   ├── vector_store.py             # FAISS 向量存储
│   ├── question_bank.py            # 面试题库
│   ├── learning_path.py            # 学习路径生成
│   ├── knowledge_base/
│   │   ├── build_index.py          # 索引构建脚本
│   │   ├── chunker.py              # 文本分块
│   │   └── embedder.py             # Embedding 封装
│   └── data/
│       ├── questions.json          # 面试题库数据
│       ├── learning_paths.json     # 学习路径数据
│       ├── topic_file_mapping.json # 主题-文件映射
│       ├── topic_index.json        # 主题-向量映射
│       ├── faiss_index.bin         # FAISS 索引（gitignored）
│       └── metadata.json           # 块元数据（gitignored）
├── tests/                          # 单元测试
└── docs/                           # 设计文档和实施计划
```

## 技术选型

- **Embedding**: BAAI/bge-base-zh-v1.5 — 中文语义表示 SOTA，开源本地运行
- **向量存储**: FAISS (CPU) — 零基础设施，单文件持久化，<100K 向量高效
- **MCP 框架**: FastMCP — 官方 Python MCP SDK
- **分块策略**: 512 token / 64 overlap，保留 markdown 标题上下文
- **知识源**: hello-agents 本地教程 + Agent-Learning-Hub 外部资源（自动抓取 90+ 链接）

## License

MIT
