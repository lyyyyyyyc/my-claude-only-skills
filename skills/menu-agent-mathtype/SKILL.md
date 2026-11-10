---
name: menu-agent-mathtype
description: |-
  将可编辑的 Word 公式转换为可双击编辑的 MathType Equation.DSMT4 OLE 对象，保留 Word 批注与修订记录，默认采用 Times New Roman 和与正文匹配的 字号；独立公式默认居中，公式编号默认置于右侧；转换后强制审核乱码、字号 和版式并自动修正，将正文或表格中的混排参数转换为普通 Word 文本。适用于必须保持 MathType 可编辑性而不能使用图片或 OMML 的 DOC/DOCX 稿件。
metadata: {}
---

# Agent Mathtype：MathType 公式处理技能

## 用途

当 Word 稿件中的公式需要保持 MathType 可编辑性，并且版式需要接近参考
PDF 时使用本技能。默认目标是 Windows Word 中的 MathType OLE 对象
`Equation.DSMT4`。拉丁字母、函数、变量和数字默认使用 Times New Roman。
希腊字母、积分号、求和号及其他专用数学符号在必要时保留 MathType 的符号
字体，以避免字形损坏和间距异常。

本流程采用失败即停止的策略。禁止覆盖源文件，禁止用公式截图代替可编辑
对象，也不能只依据 Word 结构统计就宣布完成。交付前必须完成结构检查和
PDF 视觉检查。

## 默认行为（除非用户明确指定例外）

1. **独立显示公式居中。** 公式所在段落使用居中对齐；行内公式继续跟随正文，
   不强行改变正文段落的对齐方式。表格单元格中的独立公式也默认居中，但不得
   改变表格整体布局。
2. **公式编号置于右侧。** 为每个独立显示公式按文档出现顺序生成连续编号
   `(1)`、`(2)`、`(3)`……，使用居中制表位放置公式、右对齐制表位放置编号。
   编号必须与右页边界保持一致，不得使用空格模拟右对齐。已有编号只有在能够
   可靠解析且无重复、无缺失时才保留；否则重新连续编号。行内公式、变量定义
   中的短参数和普通文本不自动编号。
3. **转换后强制审核并修正。** MathType 转换完成后，必须执行“结构审核、文本
   乱码审核、字号审核、PDF 视觉审核”四项检查。任何一项失败，都必须先修正
   后再交付；无法修正时停止并报告具体公式序号和失败原因。
4. **大括号以源 Markdown 为准。** 用户提供源 `.md` 文档或对应公式片段时，
   多行公式、分段函数和约束组是否显示分组大括号，必须遵循源公式：原文没有
   就不自动添加，原文有就保留。居中、对齐、分行和拆分不能改变这一规则；
   用户明确要求改变括号时例外。具体见第 10.0 节。

默认交付文件名应明确区分源文件，例如在源文件名后追加
`_MathType_optimized` 或 `_MathType_优化版`，不得覆盖源文件。

## 输入与输出

必需输入：

- `Source`：源 `.docx` 文件。
- `Output`：与源文件不同的 `.docx` 输出路径，默认新建副本。

可选输入：

- `TexManifest`：制表符分隔的
  `formula_ordinal<TAB>base64(UTF-8 TeX)` 清单。
- `BodyFontSizePt`：正文或所在段落的字号。优先从段落或样式中检测；无法
  可靠检测时使用 10 pt。
- `ReferencePdf`：用于版式对照的 PDF。
- `SourceMarkdown`：用户提供的源 `.md` 文档或对应公式片段，用于核对原始公式
  的可见大括号；该依据优先于本技能的带大括号示例。
- `Report`：JSON 结构验证报告路径。

输出文件必须保留可编辑的 MathType 对象、修订记录、导师批注、表格、图片
以及未在任务范围内的正文内容。只有用户明确要求时，才修改其他内容。

## 工作流程决策

1. **先盘点。** 通过 Word COM 只读打开副本，统计 `InlineShapes`、
   `Equation.DSMT4` 和 `OMaths`，同时记录批注、修订数以及
   `TrackRevisions` 状态。
2. **判断处理类型。**
   - 独立显示公式：重建为 MathType OLE。
   - 混入正文或表格单元格的参数：使用普通 Word 文本，并用 Word 的上下标
     格式，不创建 MathType 对象。
   - 现有 MathType 对象只有排版问题：只替换该对象，保留原位置、宽度和高度。
3. **创建独立输出副本。** 源路径和输出路径解析后相同就立即停止；缺少目标
   对象也立即停止。
4. **重建公式。** 批量转换优先使用 MathType 官方 Word 命令；单公式修复
   或受控 TeX 替换使用选择性 OLE 重建。
5. **修正字体与版式。** 先与参考 PDF 对照，默认将独立公式居中并将编号右对齐。
6. **转换后审核。** 按第 6 节的审核门执行；发现乱码、字号异常、编号漂移或
   对齐错误时，回到第 2 至第 5 步进行选择性修复，审核通过前不得交付。

## 1. 对象盘点与安全门

使用 Word COM 遍历每个 `InlineShape`，只将以下对象认定为 MathType：

```powershell
if ($shape.OLEFormat.ProgID -eq 'Equation.DSMT4') { ... }
```

不能把图片、普通形状或 OMML 对象误判为 MathType。至少记录以下信息：

- 源文件和输出文件的绝对路径；
- 每个公式的序号、Range、宽度和高度；
- MathType OLE 数量与 OMML 数量；
- 批注数、修订数以及是否开启修订追踪。

正式批量转换前，关闭其他 Word 窗口。先复制源文件，再以可写方式打开副本。
任意一个公式转换失败，都不得保存不完整的批处理结果。

## 2. 提取与重建 MathType 公式

### TeX 公式清单

如果 OLE 数据对象提供 `TeX Input Language`，就读取每个公式的 TeX，并保存
为确定性的清单：

```text
公式序号<TAB>Base64 编码的 UTF-8 TeX
```

重建前保存 TeX 哈希，重建后读取并比较。用户明确要求替换时，哈希变化不一定
是错误，但公式缺失、TeX 无法解码或回读为空都必须判定为失败。

### MathType 官方转换

已验证的本地脚本为：

```text
E:\大创\MATHTYPE\scripts\rebuild_all_with_official_mathtype.ps1
E:\大创\MATHTYPE\scripts\send_enter_to_process.ps1
```

官方流程从文档末尾向前处理公式，避免删除前一个对象后使后续序号失效。它在
原位置写入 `$...$` TeX，调用 `MTCommand_TeXToggle`，等待新的 OLE 注册完成，
最后恢复原 Word 外部宽度和高度。

在已验证的电脑上，转换确认窗口的类名是 `ThunderDFrame`，标题是
`转换以显示样式？`，不是常见的 `#32770`。自动化脚本必须先将该窗口切到前台
再发送 Enter。复杂公式最多等待 60 秒，并且只有在 OLE 数量达到目标值且保持
稳定后，才能继续处理下一个公式。

### 单公式选择性重建

单个公式或受控替换使用：

```text
E:\大创\MATHTYPE\scripts\MathTypeOleSelectiveRebuilder.exe
```

替换表仍使用“公式序号 + Base64 TeX”的格式。安全顺序如下：

1. 读取并保存旧公式的 Range、尺寸和 TeX；
2. 删除旧 OLE，但保留原插入位置；
3. 在原位置创建空白 `Equation.DSMT4`；
4. 通过 OLE `IDataObject` 写入以空字符结尾的 UTF-16 TeX；
5. 从新对象回读 TeX 并比较；
6. 恢复原宽度、高度以及 Word 外层字体。

不能直接向已有 OLE 写入 TeX。MathType 可能把新 TeX 插入当前编辑光标，造成
旧公式与新公式重叠。也不要为每个公式都调用 `DoVerb` 打开编辑器，批量处理时
会累积界面会话并导致后续公式挂起。应优先直接访问 OLE；只有 Word 延迟初始化
当前对象时，才对该单个对象回退激活。批处理期间不要使用系统剪贴板传输公式。

## 3. MathType 字体与字号

判断结果前，先确认 MathType 内部偏好：

```text
Text         = Times New Roman
Function     = Times New Roman
Variable     = Times New Roman, italic
Number       = Times New Roman
Full         = 与正文一致，无法确定时为 10 pt
Script       = 58%
ScriptScript = 42%
```

希腊字母、运算符和特殊符号继续使用 Symbol、MT Extra 或其他专用数学字体。
不能把每个字符粗暴地全部改成 Times New Roman，否则积分号、求和号、希腊字母
和部分间距可能损坏。

Word 外层字体只控制 OLE 占位框、基线和所在段落，不能可靠修改 MathType 内部
字符样式。因此先设置或重建 MathType 内部样式，再设置 Word 外层字体并恢复
尺寸。行内公式跟随所在正文的字号；独立显示公式遵循稿件的显示公式规范，
未指定时使用 10 pt。

## 4. 正文参数与独立公式的处理策略

正文或表格中的参数是否使用 MathType，不是本技能的通用硬性规则，必须先
依据当前项目的排版规范和用户要求选择模式：

- **全 MathType 模式**：独立公式、正文行内参数和表格参数都保留为可编辑的
  MathType OLE；
- **独立公式 MathType 模式**：独立公式使用 MathType，正文或表格中的短参数
  使用普通 Word 文本；
- **保留原格式模式**：不主动转换正文或表格中的参数，只修复用户明确指出的
  公式或版式问题。

如果用户没有指定模式，默认保留原有对象类型，不擅自把正文参数转换为普通
文本，也不擅自把普通文本转换为 MathType。模式确定后，整个文档应保持一致，
除非用户明确指定某个表格、段落或公式使用例外格式。

当当前项目选择“独立公式 MathType 模式”时，普通 Word 文本使用 Times New
Roman 和所在正文的字号。变量（例如 `B`）可使用斜体，数字、乘号、括号和
运算符保持正体，下标和上标使用 Word 自带格式，表格要求居中时同步居中。
该模式适合将 `B × 1 × 56,000`、`(2, 4)` 等短参数与表格正文统一。

当当前项目选择“全 MathType 模式”时，正文参数也必须按 MathType 内部偏好
重建，并通过 PDF 检查行内基线、字号、上下标和表格单元格间距。不能仅设置
Word 外层字体后就宣称 MathType 内部样式已经改变。

## 5. 公式专项排版修复

### 三列对齐

当二行假设公式需要分别对齐 `H₀/H₁`、两行 `x(t)` 起点以及 `y=0/y=1` 时，
已验证的 MathType 导入器可使用三列左对齐数组：

以下示例仅在源公式本来有可见左大括号时使用。源 Markdown 无分组大括号时，
保留数组对齐结构，但不添加外层 `\left\{` 和与其配对的 `\right.`。

```tex
\left\{\begin{array}{lll}
H_0 & :x(t)=n(t), & y=0,\\
H_1 & :x(t)=\alpha [s*h](t-\tau)+n(t), & y=1,
\end{array}\right.
```

每次修改后都必须导出 PDF 检查。已验证环境中，`{rcl}` 会使中间列按内容居中，
导致两行 `x(t)` 起点不一致；`{rlr}` 也没有稳定改变导入器行为。若
`\phantom`、`aligned` 或 `&&` 被导入成红色普通文本，应立即回退，不得交付。

### 函数间距

如果 `\text{GELU}` 导入后函数名与括号之间过紧，可使用标准数学算子形式：

```tex
\operatorname{GELU}\left(\cdots\right)
```

替换后必须导出 PDF，确认 `GELU` 与括号之间的间距自然，不能只依据 TeX 字符串
判断。

### 居中与编号

独立公式默认居中。先检查所在段落的制表位，使用居中制表位放置公式，使用右
对齐制表位放置公式编号；不得用连续空格或手工空格模拟居中/右对齐。公式编号
发生移动时，必须同步更新后续编号和正文中的引用，禁止产生重复编号、缺失编号
或 `(49)` 到 `(1)` 这类逆序编号。编号写入后必须重新扫描文档 XML 或 Word
段落文本，确认编号顺序为 `(1)` 到 `(N)`。

## 6. 转换后审核与自动修正

本节是强制步骤，不能用“转换命令成功”替代。审核应在所有 OLE 重建完成后、
最终保存前执行；修正后必须再次审核。

### 6.1 结构审核

- 统计 `Equation.DSMT4`、`InlineShapes`、`OMaths`、表格、批注、修订和
  `TrackRevisions`，并与转换前盘点对照。
- 默认要求独立公式全部是 `Equation.DSMT4`，OMML 为 0；公式数量不得无故
  减少。复杂公式拆成多行 OLE 时，记录拆分映射，不把拆分误判为公式丢失。
- 统计独立显示公式段落数和编号数，二者必须相等；编号必须从 `(1)` 连续到
  `(N)`，不得重复、缺失或逆序。
- 每个独立公式段落的对齐属性必须为居中；编号所在制表位必须为右对齐。行内
  公式和表格正文的对齐不得被误改。

### 6.2 乱码与 TeX 残留审核

同时检查 Word 段落文本、文档 XML 和可读取的 MathType TeX。以下内容视为失败：

- 公式正文中出现原始控制命令，例如 `\begin`、`\end`、`\aligned`、
  `\mspace`、孤立 `&`、未闭合的 `$`；
- 出现 Unicode 替换字符 `U+FFFD`、明显的问号方框、乱码 TeX 片段或中文
  `\text{...}` 被当作红色普通文本；
- OLE 无法双击打开、TeX 回读为空或回读与预期公式不一致。

发现问题时，按以下顺序修正：

1. 保留原公式 TeX、Range、宽度和高度，定位具体公式序号；
2. 将不兼容命令改写为 MathType 已验证的 TeX（例如用 `array` 三列对齐替代
   `aligned`，用 `\operatorname{...}` 替代不稳定的 `\text{...}`）；
3. 通过选择性 OLE 重建替换原对象，禁止用截图或 OMML 覆盖；
4. 回读 TeX 并再次扫描残留命令，确认乱码消失。

### 6.3 字号与字体审核

- MathType 内部偏好必须为 `Text/Function/Number = Times New Roman`、变量可
  斜体、专用数学符号保留 Symbol/MT Extra；`Full` 与正文匹配，无法确定时
  使用 10 pt，`Script=58%`、`ScriptScript=42%`。
- 记录每个 OLE 的内部 Full 字号（可读取时）、Word 外层字号、宽度和高度。
  默认正文/独立公式外层字号统一为 `BodyFontSizePt`；未提供时使用 10 pt。
- 发现外层字号不一致、内部 Full 字号偏离、公式高度异常偏小或脚本比例异常
  时，必须重新设置 MathType 内部样式或选择性重建该公式，再统一设置 Word
  外层字体和字号。不能只修改 OLE 外框后宣称内部字号已修复。
- 复杂公式因分式、上下标而高度不同不自动判为错误；但同一类相邻公式若出现
  明显缩小、基线漂移或字符不可读，必须按异常公式处理。

### 6.4 PDF 视觉审核

导出 PDF 后至少检查所有被重建公式所在页，以及包含长公式、分段公式、编号和表格
的页面。确认：

- 公式视觉中心与正文版心一致，编号贴近右边界且不换行、不漂移；
- 无红色 TeX 命令、乱码、裁切、重叠、基线跳动或明显小于同级公式的对象；
- 分段/数组各列起点一致，长约束公式不会被压缩成不可读的一行；
- 表格、图片、批注和正文未因公式重建而错位。

审核报告至少增加以下字段：

```json
{
  "alignment": {"standalone_centered": true, "numbering_right_aligned": true},
  "numbering": {"count": 0, "ascending": true, "duplicates": 0, "missing": 0},
  "audit": {
    "residual_tex_tokens": [],
    "replacement_characters": 0,
    "font_size_outliers": 0,
    "visual_pages_checked": []
  }
}
```

只有 `alignment.standalone_centered=true`、`alignment.numbering_right_aligned=true`、
`numbering.ascending=true` 且 `audit` 中无乱码和字号异常时，才允许进入交付阶段。

## 7. 验证门

如果本地脚本存在，运行：

```text
E:\大创\MATHTYPE\scripts\verify_formula_layout_final_20260819.ps1
```

最终 JSON 报告至少记录：

- `Equation.DSMT4` 数量；
- OMML 数量，通常应为 0；
- 批注数、修订数和 `TrackRevisions` 状态；
- 每个表格中的 MathType 数量；
- 输出路径和检查时间。

随后用 Word 导出 PDF，检查所有被修改公式、表格和编号所在页面。重点检查：
字形是否被裁切，基线是否改变，函数间距是否异常，数组三列是否对齐，编号
是否重复或缺失，以及表格是否溢出。只做结构统计而不检查 PDF，不能视为通过。

2026 年 8 月 19 日已验证稿件的参考结果是：MathType OLE 25 个、OMML 0 个、
批注 7 条、修订追踪开启。这个数字仅用于对照，不能替代当前输入文件的实际盘点。

## 8. 失败处理

出现以下任一情况时，停止处理并报告具体阶段：

- 源路径和输出路径相同；
- Word 或 MathType 不可用；
- 无法识别转换确认窗口；
- 预期 OLE 数量没有出现或没有稳定；
- TeX 回读结果异常；
- 公式无法重新打开为 `Equation.DSMT4`；
- PDF 出现裁切、重叠或编号漂移。

不能用截图或 OMML 公式掩盖转换失败。除非确实读取并执行了 MathType EF/MTEF
内部重排，否则不能声称完成了 MTEF 内部重排。必须明确说明实际使用的是官方
TeX 切换、OLE 重建还是其他路径。

通过 COM 关闭 Word 时，使用兼容 ByRef 的 Variant 参数：

```powershell
[object]$doNotSave = 0
$doc.Close([ref]$doNotSave)
[object]$doNotSaveWord = 0
$word.Quit([ref]$doNotSaveWord)
```

## 9. 交付清单

交付修改后的文档时，必须同时提供：

1. 输出 `.docx` 文件链接；
2. 结构验证 JSON 路径；
3. PDF 检查文件或截图路径；
4. MathType、OMML、批注、修订和修订追踪状态的数量；
5. 已修改内容和明确未修改内容的简短说明。

源 Word 必须保留，以便回滚。如果用户要求覆盖正式文件，先明确说明源路径
和目标路径，再执行复制或替换。

## 10. Complex piecewise functions and constraint groups

When a display equation contains a piecewise function, a population recursion, a multi-row constraint group, or more than one formula object in the same display paragraph, treat it as one logical formula group. Do not leave several independent MathType OLE objects separated by manual spaces or soft line breaks when their rows are expected to align.

### 10.0 源 Markdown 的大括号优先规则

- 先核对用户提供的 `.md` 中对应的数学公式块，区分可见分组大括号与 TeX 语法
  使用的花括号。例如 `x_{ij}`、`\frac{a}{b}`、`\begin{array}{ll}` 中的 `{}`
  不代表公式外侧有可见大括号；`cases` 环境通常代表可见左大括号。
- 源公式没有可见分组大括号时，多条公式仍按源文档排列，不得仅因为多行、
  多约束、分段函数或选用了 `array` 就增加 `\left\{...\right.` 或 `cases`。
  MathType 不兼容 `aligned` 时，可以改用无外层大括号的 `array`，但保持公式
  内容、行序和原有分组关系。
- 源公式有可见大括号时，保留其方向及包围范围。若长公式必须拆成多个 OLE，
  各部分也遵循源文档的有括号/无括号状态，不因拆分给无括号公式补上大括号。
- 例如源 Markdown 的两行等式没有外层大括号，可使用如下无括号数组；居中和
  右侧编号仍按本技能原有规则处理：

```tex
\begin{array}{ll}
x+y & =1,\\
x-y & =0.
\end{array}
```

### 10.1 Preferred MathType construction

- Rebuild a normal piecewise function as one `Equation.DSMT4` OLE using an `array`. Add the outer `\left\{ ... \right.` only when the source formula has that visible grouping brace or the user explicitly requests it; follow section 10.0 for Markdown sources.
- Use `array{ll}` for value/condition pairs and `array{lll}` for variable/equality/expression rows. Keep the expression column and condition column aligned with `&`.
- Use `\operatorname{...}` or `\mathrm{...}` for function names and fixed labels. Avoid unstable `\text{...}` in converted TeX; use `\mathrm{ER}` for fixed abbreviations such as emergency relief.
- Prefer `\dfrac` only when the equation remains compact; otherwise use `\frac` to reduce height and prevent clipping.
- Keep the formula body in MathType. Do not replace a failed conversion with an image, screenshot, or OMML object.

### 10.2 Long constraint groups

- First try one multi-row MathType OLE with an `array` and aligned expression/condition columns.
- If MathType rejects the TeX because the group is too long, split the logical group into two or more shorter `array` OLEs vertically. The split must occur between complete constraint rows, never in the middle of a row.
- Insert real paragraph breaks between the OLEs. Do not use spaces, tabs, or a soft line break to simulate vertical stacking; these can place the arrays side by side or make row starts drift.
- Center each array paragraph independently. Put the equation number only on the final paragraph of the group, using the right-aligned tab stop.
- If the stacked group would cross a page boundary, set a page break before the first array so the entire logical group starts on the next page. Never leave the first half at the bottom of one page and the second half at the top of the next page.
- After splitting, verify that the array layout and row order preserve the source grouping, that visible braces remain present or absent as in the source, and that all rows share the intended column starts.

### 10.3 Numbering and typography for complex groups

- A multi-OLE logical group still receives exactly one equation number.
- Equation numbers remain sequential `(1)` through `(N)`, right aligned by a tab stop; never use repeated spaces to imitate right alignment.
- Set every rebuilt OLE outer frame to the body font size, normally 12 pt in this project, and use Times New Roman for the outer frame. Do not fix a visibly tiny formula by changing only surrounding paragraph text.
- Check that neighboring rows have consistent baseline and readable script sizes. A tall formula is acceptable; a clipped or unexpectedly tiny formula is not.

### 10.4 Mandatory review loop

After rebuilding complex groups, run all of these checks before delivery:

1. Structural: every intended group contains the expected number of `Equation.DSMT4` objects; OMML is 0 unless explicitly requested; no source paragraph, table, comment, or image content was lost.
2. TeX/encoding: no visible `\begin`, `\end`, `\aligned`, `\mspace`, replacement character `U+FFFD`, red TeX text, or unreadable glyphs remain.
3. Layout: complex arrays are centered, columns start consistently, the final paragraph carries the right-aligned number, and no group is split across pages.
4. Typography: outer OLE sizes are uniform and no target formula is a font-size outlier.
5. PDF: export the result and visually inspect every page containing a rebuilt piecewise function, long constraint group, or equation number. If any check fails, repair the specific formula group and repeat the full review.
6. Source braces: when source Markdown is provided, compare every rebuilt group's visible braces with the corresponding source math block. A brace added to a source group without one is an audit failure: remove only the added grouping brace, preserve TeX syntax braces, rebuild, and repeat the PDF check. Verify existing braces retain their original scope.

The audit report should record the rebuilt formula numbers, whether any long group was vertically split, the pages visually checked, residual TeX tokens, replacement-character count, numbering continuity, and font-size outliers. When source Markdown is provided, also record the source file or formula fragment and whether visible grouping braces match it.
