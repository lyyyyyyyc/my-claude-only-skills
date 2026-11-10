# 一站式流水线 SOP

## 概述

本 skill 执行一条固定的四步流水线。用户输入论文 .docx 文件路径后，自动完成所有处理。

---

## Step 0: 读取与诊断

### 0.1 提取文本
```bash
pandoc "输入文件.docx" -o /tmp/paper_content.md --wrap=none
```
如果 pandoc 不可用，使用 python markitdown 作为备选。

### 0.2 识别论文结构和类型

读取提取出的 markdown，识别：

**论文类型**（四选一）：
- `experiment` — 实验研究（有实验方法、实验结果）
- `simulation` — 数值模拟（有模型建立、参数标定、模拟结果）
- `review` — 综述（有大量文献综述，无独立实验/模拟）
- `theory` — 理论研究（有公式推导、理论分析）

**论文结构**（识别各章节边界）：
- Title / 标题
- Abstract / 摘要
- Introduction / 引言
- Related Work / Literature Review / 文献综述
- Methods / Experiments / 方法 / 实验
- Results / 结果
- Discussion / 讨论
- Conclusion / 结论
- References / 参考文献

如果论文使用中文标题，同样能识别。

### 0.3 确定目标期刊

- 如果用户指定了期刊名或出版社，从 `references/journal-formats/` 加载对应格式
- 如果用户未指定，使用 `references/journal-formats/default.md`（通用SCI期刊标准）

### 0.4 输出诊断清单

输出一份简短的诊断清单，格式：

```
## 论文诊断
- 类型: [experiment/simulation/review/theory]
- 语言: [中文/英文/中英混合]
- 章节: [识别的章节列表]
- 目标期刊: [期刊名或"通用SCI标准"]

### 当前状态评估
- 面子工程: ⭐⭐ (问题: ...)
- 创新点表达: ⭐⭐ (问题: ...)
- 工作量呈现: ⭐⭐ (问题: ...)
```

这份诊断清单在后续处理中作为输入参考。

---

## Step 1-3: 三大支柱并行处理

三个支柱各由一个 Agent 独立处理。它们同时启动，各自读取自己的 reference 文件。

### Agent 1: 面子工程包装
```
读取: references/pillar-1-face.md, references/academic-phrasebank.md
输入: 论文全文 markdown + 诊断清单 + 目标期刊格式
任务:
  1. 全文语言润色（重点 Abstract/Introduction/Conclusion）
  2. 对标期刊模板给出排版建议
  3. 建议新增的图表（核心创新示意图 + 逻辑框架图）
输出:
  - polished_sections: {abstract, intro, conclusion, ...} 润色后文本
  - formatting_suggestions: 排版修改建议列表
  - figure_suggestions: 建议新增的图表描述
```

### Agent 2: 创新点包装
```
读取: references/pillar-2-innovation.md
输入: 论文全文 markdown + 诊断清单
任务:
  1. 提取1-2个核心创新点
  2. 重写标题建议
  3. 重写 Abstract/Introduction/Conclusion 关键段落
  4. 生成创新点示意图描述
输出:
  - innovation_points: 提取的创新点
  - new_title_suggestions: 新标题建议（2-3个）
  - rewritten_sections: 改造后的关键章节
  - innovation_figure_description: 创新点示意图的文字描述
```

### Agent 3: 工作量包装
```
读取: references/pillar-3-workload.md
输入: 论文全文 markdown + 诊断清单
任务:
  1. 对 Results 部分增加深层分析
  2. 对 Methods 部分补充细节描述
  3. 审查文献综述覆盖度
  4. 生成验证/可靠性论证建议
输出:
  - enhanced_results: 增强后的结果分析
  - enhanced_methods: 补充后的方法描述
  - literature_audit: 文献综述审查结果
  - validation_suggestions: 验证/可靠性建议
```

### 并行执行方式

使用 Agent 工具同时启动三个 agent，用 `run_in_background: false` 确保三个都完成后进入 Step 4。

---

## Step 4: 合成与输出

### 4.1 合并三个 Agent 的输出

将三份输出合并，去重冲突。如果不同 Agent 对同一段落有不同修改，优先采用顺序：**创新点包装 > 面子工程 > 工作量包装**。

具体合并规则：
- 标题：采用 Agent 2（创新点）的建议
- Abstract：Agent 2（创新点）的结构 + Agent 1（面子工程）的语言润色
- Introduction：Agent 2（创新点）的逻辑重构 + Agent 1 的语言 + Agent 3 的文献审查
- Methods：Agent 3（工作量）的补充 + Agent 1 的语言润色
- Results：Agent 3（工作量）的深层分析 + Agent 1 的语言润色
- Discussion：Agent 3（工作量）的机制阐述 + Agent 1 的语言润色
- Conclusion：Agent 2（创新点）的重新表述 + Agent 1 的语言润色

### 4.2 生成包装版 .docx

用 docx-js 创建新的 .docx 文件：

1. 设置页面格式（参照目标期刊模板：A4/Letter、页边距、字体、字号、行距）
2. 写入新标题
3. 按原论文章节顺序写入各章节，但使用改造后的内容
4. 在 Introduction 附近插入创新点示意图（如果 Agent 2 生成了）
5. 在文档开头插入一页"包装说明"（列出主要改动摘要，供导师/合作者查阅）

**关键规则**：
- 保留原论文的核心数据（数值、表格、公式）不变
- 所有新增分析不修改原始数据结论
- 排版使用 docx-js 的 `styles` 配置统一控制

### 4.3 生成诊断报告 .docx

按照 `assets/diagnostic-report-template.md` 的内容结构，用 docx-js 生成 Word 格式的诊断报告：

- 使用与包装版相同的排版规范（字体、行距、页边距）
- 中文撰写，包含总体评估表、三大支柱改动详情、投稿前待办清单
- 表格使用 docx-js 的 Table 组件，评分用 ★ 符号

### 4.4 输出文件

两个 .docx 文件放在原论文相同目录：
- `{原文件名}_包装版.docx`
- `{原文件名}_诊断报告.docx`

向用户报告简要摘要，并提醒：
> 💡 **提示**：建议用 Word 的「比较文档」功能对比原稿和包装版，可直观看到所有改动。正式投稿前请逐条审阅确认。
