---
name: dashixiong-baozhuang
description: |-
  大师兄论文包装工具。输入Word论文草稿（.docx），自动诊断并完成三大支柱改造—— 面子工程（排版规范+语言润色+图片优化）、创新点包装（显式表达+学术故事+对比现有研究）、 工作量包装（深挖数据+补充细节+验证话术），输出包装后的.docx及诊断报告。 触发词：论文包装、SCI包装、提升论文、4区包装2区、论文润色升级、包装论文、提升期刊层次、 论文改造、SCI升级、论文拔高、帮我包装、润色包装、paper packaging、SCI upgrade、 大师兄、大师兄包装、dashixiong、找大师兄、师兄帮我、师兄包装。 当用户提到"提升论文档次"、"论文投2区"、"把论文包装一下"、"让大师兄帮我"时也触发。
metadata: {}
---

# 大师兄论文包装 Skill

**输入**: 一篇 Word 论文草稿（.docx） → **输出**: 包装后的 .docx + 诊断报告 .docx

## 核心原则

**不造假、不加实验、不改数据。** 所有改动只在"学术表达"层面——优化呈现方式，让同样的研究看起来像二区水平的论文。

---

## 执行流程

按照 `static/core/pipeline.md` 的详细 SOP 执行以下四步流水线：

### Step 0: 读取与诊断

1. 用 `pandoc` 提取论文全文（如果不可用则用 python markitdown）：
   ```bash
   pandoc "{用户提供的.docx路径}" -o /tmp/paper_content.md --wrap=none
   ```

2. 读取 `static/core/stance.md` 理解三大支柱核心理念

3. 识别论文类型（实验/模拟/综述/理论）和结构（标题、摘要、引言、方法、结果、讨论、结论）

4. 确定目标期刊：如果用户指定了期刊名/出版社，加载对应的 `references/journal-formats/` 模板；否则使用 `references/journal-formats/default.md`

5. 向用户输出一份简短的诊断清单

### Step 1-3: 三大支柱并行处理

**同时启动三个 Agent**（各读取各自的 reference 文件，互不干扰）：

**Agent A — 面子工程**（读取 `references/pillar-1-face.md` + `references/academic-phrasebank.md`）：
- 全文语言润色（重点 Abstract/Introduction/Conclusion）
- 对标目标期刊的排版建议
- 建议新增图表（核心创新示意图 + 逻辑框架图）

**Agent B — 创新点包装**（读取 `references/pillar-2-innovation.md`）：
- 提取 1-2 个核心创新点
- 提供新标题建议（2-3个选项）
- 重写 Abstract/Introduction/Conclusion 关键段落
- 提供创新点示意图的文字描述

**Agent C — 工作量包装**（读取 `references/pillar-3-workload.md`）：
- 对 Results 增加深层分析（规律、影响因素、机制）
- 对 Methods 补充细节描述（参数含义、取值依据、干扰排除）
- 文献综述覆盖度审查
- 验证/可靠性论证建议

每个 Agent 产出结构化结果（润色后文本 + 改动说明列表）。

### Step 4: 合成与输出

1. **合并三个 Agent 的输出**（冲突时优先级：创新点包装 > 面子工程 > 工作量包装）

2. **生成包装版 .docx**（使用 docx-js）：
   - 设置页面格式（参照目标期刊模板）
   - 写入新标题 + 改造后的各章节
   - 嵌入新增示意图
   - 在文档开头插入"包装说明"页
   - 输出到 `{原文件名}_包装版.docx`

3. **生成诊断报告 .docx**（参照 `assets/diagnostic-report-template.md`，用 docx-js 生成）：
   - 输出到 `{原文件名}_诊断报告.docx`

4. **向用户报告**：简要摘要 + 两个输出文件路径 + 审阅提示

---

## 输出规范

详见 `static/core/output-format.md`。

简要版：
- **包装版 .docx**：用 docx-js 创建，保留原结构，应用所有改动，排版对齐目标期刊，嵌入示意图
- **诊断报告 .docx**：总体评估表 + 三大支柱改动详情 + 投稿前待办清单，Word 格式方便打印和分享

核心约束：不改数据、不加实验、不虚构引用、不改变结论实质。

---

## 文件索引

| 文件 | 何时加载 |
|------|----------|
| `static/core/stance.md` | Step 0 — 理解三大支柱理念 |
| `static/core/pipeline.md` | Step 0 — 流水线 SOP 细节 |
| `static/core/output-format.md` | Step 4 — 输出规范 |
| `references/pillar-1-face.md` | Agent A — 面子工程操作 |
| `references/pillar-2-innovation.md` | Agent B — 创新点包装操作 |
| `references/pillar-3-workload.md` | Agent C — 工作量包装操作 |
| `references/academic-phrasebank.md` | Agent A — 润色时参考句式 |
| `references/journal-formats/*.md` | Step 0 — 按目标期刊加载 |
| `assets/diagnostic-report-template.md` | Step 4 — 诊断报告格式 |

---

## 依赖

- `pandoc` 或 `python -m markitdown`：提取 docx 文本
- `docx` npm package (docx-js)：创建输出 .docx
- （可选）现有 docx skill 的 scripts：unpack.py, pack.py, validate.py
