---
name: math-modeling-skill-creator
description: |-
  用于创建、修改、扩展或优化数学建模相关 skill。当用户提出“创建数模 skill / 为某类数模任务做专门 skill / 修改已有数模 skill / 优化触发词 / 设计 references、agents、assets / 做数模 skill 模板”等需求时使用。它负责把数模需求沉淀成可触发、可维护、可安装的 skill 结构，而不是直接替代数模求解本身。
when_to_use: when the user wants to create, modify, expand, or optimize a mathematical modeling skill, especially when they
  mention 创建数模skill、修改数模skill、做数模技能模板、优化触发词、设计references、设计agents、做专门skill、把这套流程沉淀成skill等表达
metadata:
  codex-original-fields: '{"languages": "zh-CN", "version": "1.0.0"}'
---

# 数学建模技能创建器

## 概述
- 把数模需求转化为可落地的 `SKILL.md`，并保证触发条件清晰、结构可维护、可安装到 Codex。
- 优先调用 `math-modeling-brainstorm` 做需求拆解；参考并吸收外部 `skill-creator` 与 `writing-skills` 的方法，但不整包照搬其完整工作流。
- 目标不是写出“一次性大 prompt”，而是做出可复用、可扩展、后续还能继续维护的数模 skill。

## 什么时候优先用本 skill
- 用户明确说“帮我创建一个数模 skill”“给某类数模任务做专门 skill”“把这套流程沉淀成 skill”。
- 用户已经有某个数模 skill，但想继续改触发词、调结构、拆 references、加 agents 或做模板化整理。
- 用户不是要直接解数模题，而是要建设、优化或维护数模 skill 本身。
- 用户想把某个数模解题套路从一次性对话变成长期可复用的 Codex skill。

## 第一优先动作
当本 skill 被触发时，始终先做以下四件事：

1. 判断用户是在“创建新 skill”还是“修改已有 skill”。
2. 若当前任务是创建新 skill，必须先强制询问用户：是否要在新 skill 的开头强制调用 `math-modeling-brainstorm`。
3. 明确这个 skill 的目标任务、触发场景、输出形式和边界。
4. 判断它应该是一个独立数模 skill，还是应并入现有数模 skill。
5. 先设计触发与结构，再开始写 `SKILL.md`，不要一上来就堆正文规则。

## 目标与意图捕获
创建或修改数模 skill 时，至少先确认以下问题：
- 这个 skill 应该帮助 Codex 做什么。
- 用户会怎么说，Codex 才应该触发这个 skill。
- 输出应以什么形式交付：流程、模板、参考文档、代码规范，还是综合型 skill。
- 它是通用型数模 skill，还是只服务于某一类任务。
- 是否需要拆分 `references/`、`agents/`、`assets/`。
- 若当前是在创建新 skill，必须先问用户：是否要在新 skill 的开头强制调用 `math-modeling-brainstorm`；未问清前，不得直接替用户决定。

若用户表述含糊，优先调用 `math-modeling-brainstorm` 把需求拆成“任务目标、输入类型、输出类型、边界、下游衔接”五个部分，再继续设计。

## 触发设计（description / when_to_use）
- `description` 不只写“做什么”，还要写“用户通常会怎么说”。
- 触发描述要略微“推触发”，减少 undertrigger，但不能突破 skill 的真实边界。
- `when_to_use` 要像真实用户话术，不要只写抽象概念。
- 如果 skill 有严格边界，例如必须显式 `$skill-name` 才触发，就在 `description`、`when_to_use` 和正文第一节三处同时强调。
- 如果 skill 是路由型或总入口型，应明确写“先判断范围 / 先选分类 / 先做分流”，避免 Codex 一触发就直接执行下游任务。

## 结构设计（主文 / references / agents）
- 主 `SKILL.md` 放高频规则、触发边界、默认流程、常见错误和维护入口。
- 低频长说明、维护说明、清单、扩展规则优先放到 `references/`。
- 只有当某类工作需要稳定的角色分工时，再加 `agents/`。
- 如果某个 skill 支持多个数模子领域，优先用“主入口 + references 路由”而不是把所有知识塞进一个超长主文。
- 如果只是一次性的说明或某次任务特例，不要写进主 `SKILL.md`。

## 数模 skill 分工判断
新增 skill 之前，先判断是否真的需要独立 skill：
- 若这是数模总入口、思路拆解、任务分流：更适合 `math-modeling-brainstorm`。
- 若这是约束提取：更适合 `math-modeling-constraints`。
- 若这是目标函数设计：更适合 `math-modeling-objective-function-builder`。
- 若这是论文写作：更适合 `math-modeling-paper-writing`。
- 若这是评委审核：更适合 `math-modeling-judge-review`。
- 若这是某个新领域里高频、可复用、稳定独立的一套流程，才适合新建独立数模 skill。

如果新需求和现有 skill 高度重叠，优先判断是“扩展已有 skill”还是“拆成 references 文档”，不要默认新建目录。

## 轻量测试提示词设计
数模 skill 不必整包引入外部 `skill-creator` 的 benchmark / eval-viewer 流程，但至少应为每个新 skill 设计 2–3 条真实测试提示词，用于人工回归检查：
- 一条“明确触发”的标准提示词。
- 一条“口语化触发”的真实用户表达。
- 一条“容易混淆但不该误触发”的边界提示词。

测试提示词应尽量像用户真实会说的话，而不是只写抽象命令。

## 修改已有 skill 的维护原则
- 先看当前 skill 的 `description`、`when_to_use`、正文结构和 `references/` 分层，再决定改哪里。
- 优先最小改动，不因新增一点内容就推倒重写。
- 能补到现有区块里，就不要新开大区块。
- 如果新增内容是低频长说明，优先下沉到 `references/`。
- 修改后要检查：触发边界有没有变、结构有没有更乱、是否引入重复表达。

## 安装闭环与验证
如果用户要求真正创建或修改 skill 文件，完成后至少要确认：
- `SKILL.md` frontmatter 是否完整。
- 目录结构是否合理。
- 如有 `agents/openai.yaml`，命名和展示字段是否一致。
- 新 skill 是否已经安装到 `C:\\Users\\LX\\.codex\\skills\\local`。
- 主路径、安装路径、调用名是否都能明确交付给用户。

## Common Mistakes
- 一上来就写正文规则，不先设计触发边界和结构。
- 把一次性对话经验直接写成永久规则。
- `description` 只写“做什么”，不写“用户会怎么说”，导致不易触发。
- 把低频长说明塞进主 `SKILL.md`，导致主文越来越重。
- 不先判断是否应该扩展已有 skill，就盲目新建一个数模 skill。
- 把外部 `skill-creator` 的 benchmark、viewer、run_loop、打包工作流整包复制进来，导致数模 skill 创建器过重。
- 仍然默认依赖通用 `brainstorming`，而不是优先使用 `math-modeling-brainstorm`。

## 维护说明（供 Codex 按需读取）
- 若后续需要继续为本 skill 新增触发词、结构规则、维护流程、参考清单或安装校验要求，请先读取 `references/add-content-guide.md` 和 `references/skill-creation-checklist.md` 再修改。

