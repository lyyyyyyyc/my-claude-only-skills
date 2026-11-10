# Planning With Files Skill

一个模拟 Claude Code Plan Mode 的完整 Skill，提供结构化的规划工作流。

## 功能特性

- **5 阶段工作流**：初始理解 → 设计方案 → 审查验证 → 写入计划 → 用户批准
- **持久化计划文件**：所有计划保存在 .plans/ 目录
- **TodoWrite 集成**：实时跟踪任务进度
- **只读安全模式**：规划阶段不会修改任何代码

## 安装位置

```
~/.claude/skills/planning-with-files/
├── SKILL.md              # 主 Skill 文件
├── templates/
│   └── plan-template.md  # 计划文件模板
├── examples.md           # 使用示例
├── reference.md          # 参考资料
└── README.md             # 本文件
```

## 使用方法

### 自动触发

当你的消息包含以下关键词时，此 Skill 会自动激活：
- "规划"、"plan"
- "设计方案"
- "实现计划"
- "帮我分析"

### 手动调用

```
/planning-with-files
```

## 工作流程

1. **Phase 1: 初始理解**
   - 探索代码库（使用 Explore agents）
   - 收集上下文（Read, Glob, Grep）
   - 澄清需求（AskUserQuestion）

2. **Phase 2: 设计方案**
   - 使用 Plan agent
   - 评估多种方案
   - 选择最佳实现

3. **Phase 3: 审查验证**
   - 验证可行性
   - 确认关键决策

4. **Phase 4: 写入计划**
   - 创建计划文件到 .plans/ 目录
   - 使用标准模板

5. **Phase 5: 用户批准**
   - 展示计划摘要
   - 获得用户确认
   - 开始执行

## 计划文件位置

默认：`{项目根目录}/.plans/`

文件命名格式：`{描述性名称}-{日期}.md`

## 适用场景

✅ **应该使用**：
- 复杂的多文件重构
- 新功能实现（3+ 步骤）
- 架构设计和决策
- 大型代码库探索
- 需要用户确认的重要变更

❌ **不应该使用**：
- 简单的 typo 修复
- 单行代码修改
- 用户已明确指定具体操作
- 纯信息查询

## 与原生 Plan Mode 的区别

| 特性 | 原生 Plan Mode | 此 Skill |
|------|---------------|----------|
| 触发方式 | Shift+Tab 切换 | 关键词自动触发或 /planning-with-files |
| 计划存储 | 临时计划文件 | 持久化 .plans/ 目录 |
| 任务跟踪 | 无 | 集成 TodoWrite |
| 模板支持 | 无 | 标准化模板 |

## 版本历史

- v1.0.0 - 初始版本，实现完整的 5 阶段工作流
