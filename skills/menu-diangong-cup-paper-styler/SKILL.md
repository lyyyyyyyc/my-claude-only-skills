---
name: menu-diangong-cup-paper-styler
description: |-
  Render 电工杯数学建模 papers into a styled DOCX using the bundled math-modeling paper template and strict section typography. Use when generating 电工杯/电工杯数学建模/电工杯论文 sections, converting markdown drafts into Word, or automatically assembling 首页摘要、第二页目录、正文页码、三线表、参考文献 and 附录.
metadata: {}
---

# Diangong Cup Paper Styler

## Overview

Use this skill when the output should be a formal 电工杯数学建模 paper rather than plain markdown.

This skill is based on `menu-math-modeling-paper-styler`. It reuses the verified DOCX renderer, table handling, page-number handling, and strict typography rules, but changes the trigger context and starter materials to 电工杯. The bundled template is copied from the existing math-modeling paper styler.

The renderer is template-driven:
- page 1: `论文题目 + 摘要 + 关键词`
- page 2: `目录`
- page 3 onward: 正文
- page numbers start from the first page of 正文, centered in the footer, Arabic numerals
- no cover page by default
- no page header by default

This skill enforces the paper typography strictly as:
- paper title: centered, 黑体, 三号, not bold
- abstract heading: centered, 黑体, 四号, not bold
- abstract body: same as main body
- main body: 中文宋体小四, English Times New Roman 小四, 首行缩进两字符
- level-1 heading: centered, 黑体四号, not bold
- level-2 heading: left aligned, 黑体小四, not bold
- level-3 heading: left aligned, 黑体小四, not bold
- table text: same as main body, centered
- figure/table captions: 五号宋体或 Times New Roman, bold
- references: 宋体小四, left aligned, not bold
- spacing: headings use 0.5 line before and after; figure captions use before `0` after `0.5` line; table captions use before `0.5` line after `0`

The visible quick-style set is intentionally minimized to only:
- `正文`
- `标题 1`
- `标题 2`
- `标题 3`
- `参考文献`
- `图注`
- `表注`
- `图`
- `表格`

Other styles may still exist internally for DOCX compatibility, but the skill demotes them out of the quick-style gallery.

## Workflow

1. Draft the 电工杯 paper in markdown.
- Put the paper title on the first standalone line or as the first `#` heading before `摘要`.
- Write `摘要` as a standalone line or `# 摘要`.
- Write the keyword line as `关键词：关键词1 关键词2 ...`.
- Start the body after the keyword line. Do not write a markdown `目录` section; the renderer creates page 2 automatically.
- Keep canonical section names when possible:
  `问题重述`、`问题分析`、`模型假设与符号说明`、`数据预处理`、`模型建立与求解`、`模型分析检验`、`模型评价与推广`、`参考文献`、`附录`。
- Use `# / ## / ###` for the body hierarchy.
- Keep the abstract as plain prose paragraphs. Avoid complex markdown constructs inside the abstract page.
- Under `# 参考文献`, keep one entry per paragraph or one numbered item per entry.
- In `# 附录`, keep software names, commands, parameter settings, source-code descriptions, and generated result file notes when they support the 电工杯 solution.
- Do not include personal identity, school, team, or contact information unless the specific competition template explicitly requires it.

2. Render the markdown into DOCX.

```bash
python scripts/render_docx.py input.md output.docx
```

By default, markdown tables render as standard three-line tables:
- top rule: `1.5 pt`
- header separator rule: `1.0 pt`
- bottom rule: `1.5 pt`
- no left/right outer borders
- no internal vertical lines
- no body-row horizontal grid lines

If the user wants full-grid table borders, use:

```bash
python scripts/render_docx.py --table-style full-grid input.md output.docx
```

If the user wants a lighter spreadsheet-like grid, use:

```bash
python scripts/render_docx.py --table-style light-grid input.md output.docx
```

3. Check the output.
- Confirm page 1 contains only title, abstract, and keywords.
- Confirm page 2 is the table of contents.
- Confirm the main body starts after the TOC.
- Confirm the footer is blank before the正文 and page numbering starts from the first正文 page.
- Confirm there is no header.
- Confirm references and appendix content support the 电工杯 solution and do not expose team identity.
- If the TOC still shows the placeholder text, update the table of contents once in Word/WPS after opening the file.
- If the user asks for surgical edits to an existing `.docx`, switch to the `docx` skill instead of re-rendering the whole file.

## Renderer Behavior

- The script extracts the title, abstract, and keywords from the markdown front matter.
- The script renders the body with `pandoc --reference-doc`.
- The script then post-processes the DOCX to add:
  - first-page abstract layout
  - a dedicated TOC page
  - a numbered正文 section starting at page 1
  - field updates for the TOC
  - no header references
- `Heading2` and `Heading3` fallback paragraph styles are injected automatically when the bundled template does not expose usable named styles for those markdown levels.
- The post-processor rewrites body, references, table text, and caption formatting to the strict specification above instead of trusting template defaults.

## Authoring Rules

- Prefer semantic markdown over manual formatting.
- Do not write a cover page unless the 电工杯 official template requires one.
- Do not hardcode font names or spacing in markdown unless the user explicitly wants manual override.
- Keep the abstract page concise and prose-first.
- Keep正文 primarily in Chinese.
- Use bracketed numeric citations in the正文, such as `[1]` or `[1][3]`, and list references in citation order.
- Keep appendix source-code material separated from the main正文 narrative.
- For 电工杯 problems involving circuits, power systems, control, signal processing, optimization, or simulation, keep model assumptions, parameter definitions, and validation results visible in the正文 instead of burying them only in code.

## Resources

- `assets/diangong-cup-reference-template.docx`: bundled DOCX reference template copied from the existing math-modeling paper styler.
- `assets/diangong-cup-paper-skeleton.md`: starter markdown skeleton for 电工杯-style mathematical modeling papers.
- `references/style-map.md`: layout and style behavior notes for this skill.
- `scripts/render_docx.py`: markdown-to-DOCX renderer that builds the首页/目录/正文 sections after `pandoc` conversion.

## Dependency

- `pandoc` must be available on the machine.
- The script uses only Python's standard library plus `pandoc`, so no extra Python package install is required.

## Example

```bash
python scripts/render_docx.py assets/diangong-cup-paper-skeleton.md paper.docx
```

```bash
python scripts/render_docx.py --table-style three-line assets/diangong-cup-paper-skeleton.md paper-three-line.docx
```

```bash
python scripts/render_docx.py --table-style light-grid assets/diangong-cup-paper-skeleton.md paper-light-grid.docx
```
