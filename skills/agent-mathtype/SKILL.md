---
name: agent-mathtype
description: |-
  将可编辑的 Word 公式转换为可双击编辑的 MathType Equation.DSMT4 OLE 对象，保留 Word 批注与修订记录，默认采用 Times New Roman 和与正文匹配的 字号，修复公式对齐与编号，并将正文或表格中的混排参数转换为普通 Word 文本。适用于必须保持 MathType 可编辑性而不能使用图片或 OMML 的 DOC/DOCX 稿件。
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
5. **修正字体与版式。** 先与参考 PDF 对照，再做结构检查和 PDF 检查。

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

独立公式左对齐时，先检查所在段落的制表位。使用居中制表位放置公式，使用右
对齐制表位放置公式编号。公式编号发生移动时，必须同步更新后续编号和正文中
的引用，禁止产生重复编号或缺失编号。

## 6. 验证门

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

## 7. 失败处理

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

## 8. 交付清单

交付修改后的文档时，必须同时提供：

1. 输出 `.docx` 文件链接；
2. 结构验证 JSON 路径；
3. PDF 检查文件或截图路径；
4. MathType、OMML、批注、修订和修订追踪状态的数量；
5. 已修改内容和明确未修改内容的简短说明。

源 Word 必须保留，以便回滚。如果用户要求覆盖正式文件，先明确说明源路径
和目标路径，再执行复制或替换。

