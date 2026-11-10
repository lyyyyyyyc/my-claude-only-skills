# Diangong Cup Style Map

This skill is based on `menu-math-modeling-paper-styler` and uses a copied general mathematical-modeling DOCX template.

## Layout Model

1. The paper begins with:
   - page 1: title, abstract, keywords
   - page 2: table of contents
   - main body after the TOC
2. Page numbers start from the first page of the main body, use Arabic numerals, and are centered in the footer.
3. No cover page by default.
4. No page header by default.
5. Do not include personal identity, school, team, or contact information unless the official 电工杯 template explicitly requires it.
6. References should be cited in the正文 and listed in citation order.
7. The appendix should preserve software names, commands, parameter settings, source-code notes, and simulation/result file notes that support the solution.

## Bundled Template Layout

- Page size: A4
- Margins:
  - top: `1134` twips, about 2.0 cm
  - bottom: `1134` twips, about 2.0 cm
  - left: `1418` twips, about 2.5 cm
  - right: `1418` twips, about 2.5 cm
- Footer distance: `992` twips
- Header distance: `851` twips

## Section Model Implemented By The Renderer

### Section 1: Abstract Page

- Contains only:
  - paper title
  - `摘要`
  - abstract body
  - `关键词：...`
- Uses the blank footer from the bundled template
- Has no page numbering

### Section 2: TOC Page

- Inserted automatically by the renderer
- Contains:
  - centered `目录`
  - a live TOC field
- Uses the blank footer from the bundled template
- Has no page numbering

### Section 3: Main Body

- Starts immediately after the TOC
- Uses the numbered footer from the bundled template
- Sets `pgNumType start=1`
- Carries the正文, references, and appendix

## Enforced Typography

- Paper title:
  - centered
  - `黑体`
  - `三号` (`32` half-points)
  - not bold
- `摘要` heading:
  - centered
  - `黑体`
  - `四号` (`28` half-points)
  - not bold
- Abstract body:
  - same as the main body text
- Main body:
  - Chinese `宋体`
  - Western text `Times New Roman`
  - `小四` (`24` half-points)
  - justified
  - first-line indent of 2 characters
- Level-1 heading:
  - centered
  - `黑体`
  - `四号`
  - not bold
  - paragraph spacing before/after `0.5` line
- Level-2 heading:
  - left aligned
  - `黑体`
  - `小四`
  - not bold
  - paragraph spacing before/after `0.5` line
- Level-3 heading:
  - left aligned
  - `黑体`
  - `小四`
  - not bold
  - paragraph spacing before/after `0.5` line
- Table text:
  - same fonts and size as the main body
  - centered in cells
- Figure caption:
  - centered
  - `五号` (`21` half-points)
  - `宋体` or `Times New Roman`
  - bold
  - spacing before `0`, after `0.5` line
- Table caption:
  - centered
  - `五号` (`21` half-points)
  - `宋体` or `Times New Roman`
  - bold
  - spacing before `0.5` line, after `0`
- References:
  - left aligned
  - `宋体`
  - `小四`
  - not bold

## Visible Quick Styles

The skill only keeps these styles in the quick-style gallery:

- `正文`
- `标题 1`
- `标题 2`
- `标题 3`
- `参考文献`
- `图注`
- `表注`
- `图`
- `表格`

Any other style that appears in the template is demoted out of the gallery unless required as the active representative of one of the groups above.

## Table Policy

- Default: `three-line`
  - Standard three-line table
  - Top/bottom rules: `1.5 pt`
  - Header separator rule: `1.0 pt`
  - No left/right borders
  - No internal vertical rules
  - No body-row horizontal rules
- Optional: `full-grid`
- Optional: `light-grid`

## TOC Policy

- The renderer inserts a field-based TOC and marks the DOCX to update fields on open.
- If Word/WPS still shows the placeholder line, update the TOC once manually after opening.

## Markdown Mapping

| Markdown pattern | Output behavior |
| --- | --- |
| first standalone line / first `#` before `摘要` | paper title |
| `摘要` line or `# 摘要` | abstract heading trigger |
| `关键词：...` | first-page keyword line |
| `# / ## / ###` after keywords |正文 hierarchy |
| `图1 ...` / `表1 ...` | caption-like paragraph formatting |
| `# 参考文献` |正文尾部 reference section |
| `# 附录` | appendix after正文 |

## Diangong Cup Writing Notes

- For circuit, power-system, control, signal-processing, optimization, or simulation tasks, keep assumptions and parameter units close to the model definition.
- Put reproducible commands, software names, solver settings, and source-code notes in the appendix.
- Use figures for circuit topology, flowcharts, signal curves, power curves, residual/error curves, and sensitivity analysis only when they directly support the result.
- Keep tables focused on parameters, evaluation indicators, experiment comparisons, or final decision schemes.

## Non-Goals

- The renderer does not invent missing references.
- The renderer does not infer official 电工杯 formatting rules that are not present in the bundled template.
- The renderer does not add team metadata, cover pages, or school information.
