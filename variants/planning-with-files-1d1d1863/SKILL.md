---
name: planning-with-files-1d1d1863
description: |-
  使用 Manus 风格的持久化 Markdown 文件进行规划、进度跟踪和知识存储。当开始复杂任务、多步骤项目、研究任务时使用。触发词：plan、规划、设计方案、实现计划。
metadata:
  codex-original-fields: '{"original-name": "planning-with-files"}'
---

# Planning With Files Skill

这是一个模拟 Claude Code Plan Mode 的完整 Skill，提供结构化的规划工作流。

## 核心原则

1. **先规划后执行**：在执行任何代码修改之前，必须先完成完整的规划流程
2. **持久化计划**：所有计划都写入 Markdown 文件，便于追踪和回顾
3. **用户审批**：重大变更需要用户明确批准
4. **增量更新**：计划可以随时更新和迭代

## 工作流程（5 阶段）

### Phase 1: 初始理解 (Understanding)

**目标**：全面理解用户的需求和相关代码

**步骤**：
1. 仔细阅读用户的请求，识别核心需求
2. 使用 Explore agents 探索代码库（Task 工具，subagent_type: Explore）
3. 使用只读工具收集上下文：Read, Glob, Grep, WebSearch, WebFetch
4. 使用 AskUserQuestion 澄清任何歧义

**输出**：对需求和代码库的清晰理解

### Phase 2: 设计方案 (Design)

**目标**：设计详细的实现方案

**步骤**：
1. 使用 Plan agent 设计实现方案（Task 工具，subagent_type: Plan）
2. 考虑多种可能的实现方式
3. 评估每种方案的优缺点
4. 识别关键文件和修改点

**输出**：详细的技术设计方案

### Phase 3: 审查验证 (Review)

**目标**：确保计划与用户意图一致

**步骤**：
1. 读取所有关键文件，深入理解
2. 验证方案的可行性
3. 检查潜在风险和副作用
4. 使用 AskUserQuestion 确认关键决策

**输出**：经过验证的最终方案

### Phase 4: 写入计划 (Document)

**目标**：将计划写入持久化文件

**步骤**：
1. 创建计划文件：位置 .plans/ 文件夹，命名 {描述性名称}-{日期}.md
2. 使用标准模板格式
3. 包含：任务概述、实现步骤、关键文件列表、预期结果

**输出**：完整的计划文件

### Phase 5: 用户批准 (Approval)

**目标**：获得用户批准后再执行

**步骤**：
1. 向用户展示计划摘要
2. 询问用户是否批准
3. 如果用户要求修改，返回相应阶段
4. 批准后，开始执行计划

**输出**：用户明确的批准或修改请求

## TodoWrite 集成

在规划过程中，使用 TodoWrite 工具跟踪进度。每个阶段开始时标记为 in_progress，完成后立即标记为 completed。

## 只读模式限制

在 Phase 1-4 期间，只能使用以下工具：
- Read, Glob, Grep, WebSearch, WebFetch
- Task (Explore/Plan), AskUserQuestion, TodoWrite
- Write (仅限 .plans/ 目录)

禁止使用：Edit, Write（计划文件除外）, Bash（修改性命令）, NotebookEdit

## 何时使用此 Skill

应该使用：复杂的多文件重构、新功能实现（3+ 步骤）、架构设计和决策、大型代码库探索

不应该使用：简单的 typo 修复、单行代码修改、用户已明确指定具体操作

## 计划文件存储位置

默认位置：{项目根目录}/.plans/

## 版本历史

- v1.0.0 - 初始版本，实现完整的 5 阶段工作流
