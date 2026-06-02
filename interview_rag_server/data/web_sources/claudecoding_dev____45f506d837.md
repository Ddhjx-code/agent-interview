---
url: https://claudecoding.dev/
title: Claude Code 源码解析
topic: engineering
source_type: blog
---

[ C Claude Code 源码解析 ](/)

  * [ 首页 ](/)
  * [ 文章 ](/posts/)
  * [ 关于 ](/about/)



# Claude Code 源码解析

手把手带你探索 Claude Code 的架构设计和实现细节

### [ 第零章：如何开始探索  一步步教你如何获取 Claude Code 源码，开启属于你的探索。  920 字 2025-07-16 ](/posts/get-started/) ### [ 第一章：搜寻所有提示词  提示词是任何 Agent 的核心，也是最容易获取的。  6202 字 2025-07-25 ](/posts/prompt-list/) ### [ 第二章：Agent 架构  探索整体架构，以及最主体的 Agent Loop 实现细节。  22 字 2025-07-25 ](/posts/agent-loop/) ### [ 第四章：默认工具环境  对于足够 Agentic 的模型来说，他们需要足够基本工具来完成大部分工作，本节探索提供了哪些工具，大概运行机制如何。  26 字 2025-07-29 ](/posts/tools/) ### [ 第五章：Task 工具  Task 是最特殊最复杂的一个工具，这是独立并发的 Sub Agents。会以隔离上下文的方式单独运行，主体以单向任务分派机制指派任务。  31 字 2025-07-29 ](/posts/task-tool/) ### [ 第六章：文件存储  Claude Code 不采用数据库，仅采用 JSON 纯文本，在本地运行时几乎事无巨细都存储在主机上。本文探索这些存储数据在哪里是什么。  36 字 2025-07-29 ](/posts/storage/) ### [ 第六章：认证系统  本节探索 Claude Code 是如何与 Anthropic 完成身份认证，以及如何暴露认证机制给其他模型服务方。  24 字 2025-07-16 ](/posts/authentication/)

(C) 2025 Claude Code 源码解析. All rights reserved.

探索 Claude Code 进行源码赏析

[ ](https://github.com/kaichen/claudecoding.dev)
