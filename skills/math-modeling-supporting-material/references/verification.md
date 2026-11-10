# 验收说明

## 交付目录与内部证据分离

先人工确认计算范围、论文图表顺序及能直接回答赛题的结果，再用工具检查结构。内部清单、来源映射、日志、数值比较与图面记录均放在交付包外的审核目录。

本技能脚本要求 Python 3.10+，只用标准库。它不执行模型、不更改输入，也不生成真实成功记录。返回码 0 表示它覆盖的检查通过，1 是验收失败，2 是调用或读取错误。模型运行和业务正确性仍需单独验证。

```text
python "<本技能目录>/scripts/audit_package.py" check --project "<原项目根目录>" --package "<支撑材料目录>" --audit-dir "<包外审核目录>"
```

## 包外 manifest.json

| 字段 | 含义 |
|---|---|
| schema_version | 3 |
| paper_versions | 已确认的论文版本名列表，制作差异只在内部记录 |
| required_sections | 需保留的计算功能列表，如预处理、各问、敏感性、稳健性、绘图 |
| sources | 源程序的项目相对路径 path、sha256、sections、交付脚本列表 scripts；排除项写 exclude_reason |
| helpers | 公共 PY 包内路径列表，不把未运行的计算伪装成公共函数 |
| result_groups | 实际题号结果目录名，如 problem_1_results；必须与 results 下目录一致 |
| artifacts | paper_figure、paper_table 或 result，逐项记录 id、包内 path；论文图表含 paper_version；图含 sha256；xlsx 表格含 sheet；result 另含 source_output，指向本审核目录中保留的程序原输出文件 |
| external_data | 题外数据 path、source、use、license，无则空；内部许可核对不带入无必要的私人信息 |
| private_terms | 需要从交付包排除的已知个人路径、姓名或标识，仅在本内部清单中保存 |
| verification | 相对本审核目录的运行证据文件，如 verification.json |

范围清单必须先根据实际项目建立，不能用已经找到的文件倒推应有范围。结果项同时保留内部 answer_to 字段，说明回答哪个题意要求；该字段供人工判定，不伪称机器能判断答题价值。论文表格的内部清单同时保存表号、标题、位置与行列规模。source_output 必须是真实程序输出，不得从编辑后的交付文件反向复制来伪造基准。

## 包外 verification.json

```json
{
  "clean_run": true,
  "command": ["python", "Code/run_all.py", "--input-dir", "原始附件目录"],
  "environment": {"python": "实际版本", "packages": {"包名": "实际版本"}},
  "code_sha256": {"Code/run_all.py": "实际SHA256", "Code/01_preprocess.py": "实际SHA256"},
  "steps": [{"script": "Code/01_preprocess.py", "exit_code": 0, "log": "logs/01.log"}],
  "checks": {
    "coverage": {"status": "passed", "evidence": "coverage.csv"},
    "numerical": {"status": "passed", "evidence": "comparison.csv"},
    "visual": {"status": "passed", "evidence": "visual.csv"}
  }
}
```

这只是格式说明。code_sha256 覆盖全部 PY；steps 覆盖全部功能脚本，同一脚本可按不同参数多次执行，每次保留命令、退出码和日志。公共函数和总入口无需作为重复计算步骤。实际环境、输入哈希、起止时间、耗时和随机种子可追加字段。

clean_run 指从无旧中间数据的状态启动。后续增量修正要保留对应代码版本、重验时间及下游范围，不能改写旧记录冒充全量运行。coverage 说明范围与答题结果选择，numerical 记录主键、数值容差和约束，visual 记录图面及元数据检查。确实不适用的项目在内部证据中说明依据。

## 自动与人工职责

自动检查根目录四项、Figures 三目录、连续图片编号、按题号的直接结果目录、论文表格实体、无交付来源表和日志、源码编译、源与当前代码哈希、结果表及工作表实体、运行命令结构和证据存在。结果文件与 source_output 的 SHA256 必须一致，覆盖内容和格式，不接受仅数值一致。

Code 除 `.py` 外允许必要的 `.txt`、`.json`、`.yaml`、`.yml`、`.toml`、`.ini`、`.cfg`、`.csv`、`.lock` 配置和依赖文件。不能换扩展名藏入其他源码。提交文件里的制作来源词、个人路径或元数据身份线索会判为待修正，不再把源文件出处字符串当作可交付的说明。

隐私脚本检查纯文本、PNG 文本元数据及办公文件 XML。已知个人词由 private_terms 提供；未经工具覆盖的 PDF 元数据、其他二进制内容和图面可见身份信息，必须使用适用工具及目视检查。不能用简单搜索结果为零保证任何未知隐私都不存在。

人工还需检查：

1. 全部计算和图形代码保留，结果按文件选取题目答案并原样复制；论文图片和全部表格逐项对应正文及附录。
2. 完整实跑不用旧数据；按唯一键比较记录、离散决策和浮点结果，容差事先确定；非唯一最优解比较可行性和目标值并解释。
3. 约束检查候选与最终决策；参数实验保留完整组合，固定策略重估与重新优化不混称。
4. 图像实际尺寸、DPI、字形、布局和矢量字体符合项目标准；清除元数据后像素不变。
5. 结果表保留原有数据、结构与样式，不额外加色或排版；检查私人批注、作者、链接和隐藏信息。通用生成器 openpyxl 不判为个人作者；其他非空作者属性须复核。不能为追求哈希一致而交付身份信息，也不能借脱敏改变业务内容。
6. 换工作目录运行仍可用，重跑结果发布仍为原样复制，不添加样式；论文图表齐全，日志、缓存和来源索引继续放包外。

## 维护测试

```text
python "<本技能目录>/scripts/test_audit_package.py"
```

测试使用临时夹具，覆盖结构、编号、隐私、表格、缺失步骤、旧哈希及路径越界等正反例。测试记录不是实际建模运行证据。用户禁止子代理时串行自查并测试，不调用子代理，也不声称做了独立代理审查。
