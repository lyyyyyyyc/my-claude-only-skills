# 执行合同、适用性与降级路径

在开始预处理、仅复核已有产物、没有原始数据、数据规模或字段类型受限时读取本文件。目的不是强制所有任务走相同流水线，而是让代理知道当前能做什么、不能做什么、需要留下什么证据。

## 1. `task_manifest`

开始时从用户消息、题面、数据字典和已完成的上游结果提取；只对阻止安全处理的信息补问一个关键问题。

```yaml
task_manifest:
  mode: advice_only / raw_audit / preprocessing / predictive_modeling / optimization / review_only
  objective:
  generalization_target:
  analysis_grain:
  target_variable:
  event_time:
  information_available_time:
  constraints:
  input_root:
  authoritative_source_list: []
  input_sources:
    - path_or_identifier:
      format:
      table_or_sheet:
      header_or_page:
      encoding_or_delimiter:
      access_limit:
      raw_copy_status:
  output_root:
  output_mode: files / inline_report
  model_contract:
    status: not_required / provisional / confirmed
    problem_type: classification / regression / forecasting / clustering / optimization / explanatory / none
    target_or_outcome:
    generalization_claim:
    validation_design: not_applicable / holdout / cross_validation / nested_cross_validation / time_split / external_validation
    metric_or_acceptance_criteria: []
    selection_scope: []
    test_policy:
  distribution_test_contract:
    status: not_required / provisional / confirmed
    test_object:
    inclusion_and_zero_negative_policy:
    parameter_fit_method:
    p_value_calibration: Lilliefors_if_verified / parametric_bootstrap / D_only
    bootstrap_replications:
    random_seed:
    conclusion_rule:
  runtime:
    executor:
    language_and_version:
    package_versions: {}
    unavailable_capabilities: []
  evidence_status:
    confirmed: []
    assumptions: []
    to_verify: []
  irreversible_actions_require_confirmation: true
```

任务模式的规范映射为：`advice_only=概念建议`、`raw_audit=原始数据审计或描述统计`、`preprocessing=实际执行预处理`、`predictive_modeling=需要模型验证的预测/分类/估计`、`optimization=数据校准或评估驱动的优化/仿真`、`review_only=仅复核已有产物`。对话中可使用中文名称，但写入 `task_manifest.mode` 时必须使用上述枚举值。

概念性问题进入 `advice_only`：不读取或写入文件，不创建处理日志，不假装存在数据结论，只说明适用条件、风险、可执行步骤和真实执行所需输入。用户请求执行预处理而 `input_sources` 未提供时，第一问只请求已确认的 `input_root` 或 `authoritative_source_list`；确定输入后、且准备写文件时，下一问才确认 `output_root` 和写入权限。用户明确表示输入不可得、不可访问或只提供已有产物时，有产物才设为 `review_only`；没有可复核产物时保留 `advice_only` 并报告输入阻塞，不重复追问同一信息。不得假装已读取原始文件。`input_root` 必须是用户指定或已确认的目录，`authoritative_source_list` 必须列出允许读取的文件/表；默认不得递归扫描工作区、临时目录、审计目录、浏览器配置、压缩包或历史生成物。原始副本默认只读保留，不因“备份”而覆盖、移动或重新编码唯一原始文件。`review_only` 的每一项检查都以当前产物直接可观察的证据为限；要求原始数据、转换历史、训练范围或字段语义的规则在证据缺失时必须标为“不可观察”，并写明限制。

`generated_at`、`accessed_on`、运行时间戳和文件生成时间统一使用 ISO 8601 完整时间与 UTC 偏移；原始来源只给出日期或未说明时区时，原样记录其日期并将时区记为 `unknown`，不得猜测或伪造转换后的时间。

仅当预处理需要以模型分数选择变换、特征、降维、重采样或阈值，或需要声明未见样本表现时，才建立 `model_contract`。`not_required` 表示任务不使用模型验证指标；相应输出应写明语义、边界、结构或资源证据。`provisional` 表示关键的目标、泛化声明、验证设计或指标尚未齐全，在补全前不能使用验证分数决定方案。只有 `confirmed` 才允许把合同中的指标用于方案选择和性能结论；`validation_design: not_applicable` 仍可用于不作泛化声明的解释性或优化分析，但不能伪称外部验证。

仅当后续方法依赖对数正态等分布假设时，才建立 `distribution_test_contract`。`provisional` 时不得输出 p 值或接受/拒绝结论；`confirmed` 必须明确检验对象、样本筛选及零/负值处置、参数拟合方法、p 值校准、随机种子、参数自助法重复次数和结论规则。若校正或自助法无法在当前环境执行，设为 `D_only`，只能报告 KS 统计量和方法限制。

## 2. 输入发现与输出合同

输入发现至少确认：文件或表标识、格式、工作表/页码/表头、编码或分隔符、读取权限、敏感字段、原始副本位置和已知数据字典。只枚举 `input_root` 中由 `authoritative_source_list` 允许的直接候选。若用户只提供 `input_root`，只允许列出其第一层文件名和格式用于请求权威清单，不读取内容、不递归扫描，也不得把全部文件自动视为权威输入；只有用户明确授权“该目录第一层全部文件均为权威输入”时，才能将其补入 `authoritative_source_list`。若没有来源清单，先请求一个输入根目录或明确文件列表，不用工作区搜索结果猜测权威输入。

复杂 PDF、扫描件或 OCR 不在本 skill 的执行范围内。只有提取文本/表格已由用户或明确可用的提取能力提供时，本技能才验收其结构与语义；否则标记“提取能力/原始内容不可得”，不假定存在匿名下游技能。

若要写文件，先使用用户指定的输出根目录；未指定时，先在报告中提出逻辑目录，不自行假定项目路径：

```text
<output-root>/
  manifests/task_manifest.yaml
  manifests/raw_manifest.md
  data/processed_data.<format>
  review/review_copy.<format>
  logs/change_log.csv
  reports/validation_report.md
  reports/data_sources.md
  reports/feature_registry.md
```

可以按任务删减目录，但输出版本、生成时间、输入标识、规则版本和回读验证必须可关联。`inline_report` 只适用于 `advice_only`、`raw_audit` 或 `review_only`，以及未改变数据的解释性报告；实际执行会生成处理后数据、变更日志或回读核验的 `preprocessing`、`predictive_modeling` 和 `optimization` 任务必须使用 `files` 并先确认 `output_root`。仅交付对话报告时，明确标注“未生成文件产物”及建议的输出位置。

本 skill 不捆绑可执行流水线、依赖锁或统一命令入口。实际执行的最低运行时合同是可用的 Python 解释器及与输入格式相符的读取库；使用表格数据时通常至少需要 `pandas`、`numpy` 和对应 XLSX 的 `openpyxl`。只要实际执行代码，必须把解释器、核心库及版本、随机种子、不可用能力和读取/写出方式写入 `runtime`；缺少最低能力时停止实际执行并报告缺口，缺少可选库时选择适用的本地替代方法或标记不适用，不能声称跨环境可复现。

### 2.1 输出模式豁免表

| 任务模式 | 必交付 | 明确豁免或禁止 |
|---|---|---|
| `advice_only` | 适用条件、风险、建议步骤、真实执行所需输入 | 不读取/写入文件，不生成实测变更日志、数据版本或模型指标 |
| `raw_audit` | 原始质量快照、字段/语义问题、来源与结构风险、后续处理建议 | 不宣称存在处理后数据、前后对比、训练集处理器或模型验证结论 |
| `review_only` | 可观察产物、核验范围、缺失证据、风险与可复现性缺口 | 不补造原始数据统计、历史变更日志、字段语义或未提供的处理参数；所有需要原始输入、处理历史或训练范围的模块均标记不可观察 |
| `preprocessing` | 使用 `files` 输出 `task_manifest`、实际执行模块的变更日志、回读核验、处理后数据/报告 | 未触发或不可观察的模块可标记不适用；无已确认 `model_contract` 时不输出模型分数比较；没有输出根目录时不执行改变数据的处理 |
| `predictive_modeling` / `optimization` | 使用 `files` 输出 `preprocessing` 产物，加上已确认 `model_contract` 对应的划分、防泄漏和指标记录 | 未定义的指标、未确认的泛化目标或未隔离的验证数据不能用于选择方案或形成性能结论；没有输出根目录时不执行改变数据的处理 |

模式与输出形式变化时，保留同一事实状态：内联报告不能冒充文件已生成，文件产物也不能用计划值冒充实际运行结果。

## 3. 能力预检与替代路径

实际执行前，检查所选模块是否在当前环境可运行；不根据技能文字假定库已安装。至少登记解释器版本、`pandas`、`numpy`、`scipy`、`openpyxl` 及实际使用的可选库版本。

| 模块 | 常用可选库 | 不可用时的处理 |
|---|---|---|
| CSV/XLSX 读写 | `pandas`、`openpyxl` | 只读取当前环境可验证的格式，或请求转换后的权威表 |
| Parquet 读写 | `pyarrow` 或其他已验证后端 | 改用 CSV/XLSX 审阅副本并记录格式限制，不声称保留全部语义 |
| PCA、Isolation Forest、LOF、Iterative Imputer | `scikit-learn` | 不安装时不执行对应方法；改用可验证的基础统计/领域规则，或经用户同意后安装 |
| VIF、GEE 等统计推断 | `statsmodels` | 使用已验证替代实现或标记该诊断不适用 |
| SMOTE/SMOTENC | `imbalanced-learn` | 比较类别权重、阈值调整或不处理，并记录少数类限制 |

项目若需要跨环境复现，应由项目代码或环境文件锁定实际依赖版本；通用 skill 不预设所有机器都安装同一套库，也不在未授权时安装软件。

## 4. 适用性矩阵

| 模块 | 应执行 | 可标记不适用 |
|---|---|---|
| 数据划分 | 已确认 `model_contract` 需要评估未见样本、未来时段或独立实体表现 | 纯审计、描述统计、数据对账、无法且不声称外部泛化的复核 |
| 缩放/变换比较 | 已确认的下游模型或数值稳定性需要，且 `model_contract` 有评价目标 | 类别数据、树模型且无变换需求、纯描述、无可比指标 |
| 时间特征/对齐 | 存在可信时间字段且任务依赖时间 | 无时间字段、时间语义未确认、预测时点不成立 |
| 特征选择与降维性能比较 | 已确认 `model_contract` 需要控制维度、稳定性或预测表现 | 无模型合同、无可比指标、仅做字段语义或结构审计 |
| 类别不均衡处理 | 已确认分类 `model_contract`、少数类足以支持方法、训练范围可隔离 | 无标签、单一类别、少数类样本不足、描述任务 |
| 多变量异常检测 | 数值变量、样本量和协方差/邻域估计条件允许 | 非数值表、样本过小、高维病态、没有合理距离定义 |
| 分布检验 | 后续方法确实依赖该分布假设 | 无相关假设、小样本不足、变量不满足定义域 |
| 历史日志/前后对比 | 实际执行并能取得输入与输出版本 | 只拿到处理后产物或报告，无法重建历史过程 |

每个“不适用”条目须写出 `原因 + 替代检查 + 对结论的限制`。

## 5. 降级与失败处理

| 情况 | 处理 |
|---|---|
| 样本很小或分组很少 | 报告样本限制，使用可解释描述、精确/置换方法或收集更多数据；不强行做不稳定的分层或复杂模型 |
| 目标只有一个类别 | 停止分类器、PR-AUC、SMOTE 和分层分类评估；记录类别定义或采样范围问题 |
| 协方差奇异、高维远大于样本量 | 不直接运行 Mahalanobis/VIF 类诊断；先减少变量、正则化或改用可解释的单变量/领域检查 |
| 全部为非数值字段 | 不强行数值缩放、PCA 或距离异常检测；先完成编码语义和频数/交叉表检查 |
| 无可信时间字段 | 不构造时间特征、不做时间对齐或序列划分；标注无法检查时间泄漏 |
| 无原始数据、代码或日志 | 只做产物复核，列出缺失证据；不补造清洗前后数字、处理器参数或变更日志 |
| 无可用测试集但需外部泛化声明 | 说明无法独立估计泛化性能；可在训练范围内部做敏感性分析，但不得称为最终测试结果 |
| 外部来源、许可或字段语义无法确认 | 停止将其并入模型，保留候选状态、限制与替代路径 |

## 6. 跨技能交接

用户或上游已经提供的澄清结果可作为 `task_manifest` 的输入，但本技能不要求固定调用顺序，也不在执行过程中转交任何上游澄清 skill。若任务目标、范围和约束已由用户或上游结果提供，直接开始当前技能的输入发现与适用性判断。

需要图形证据时，本技能只形成下列 `plot_request`，它是用户或已确认编排器可选用的交接文件，而非隐式工具调用或对某个绘图 skill 的兼容性承诺。`handoff_actor` 是启动本技能的编排器或调用方，只有在该方已验证接收方支持此请求结构时，才负责把请求、数据产物和输出目录交给绘图能力；返回结果才记录为 `plot_evidence`。没有已验证的调用接口、未收到返回或下游不可用时，交付统计表、请求单及环境限制，不能因交接失败阻塞预处理。

```text
plot_request:
  objective:
  data_family:
  variable_count:
  ordered:
  variables:
  group_by:
  time_field:
  data_artifact:
  table_or_sheet:
  data_version_or_hash:
  output_root:
  handoff_actor:
  upstream_context_status: confirmed / partial / unavailable, with missing fields
  aggregation:
  unit:
  sample_scope:
  question:
  constraints:
```

```text
plot_evidence:
  handoff_status: not_requested / handed_off / unavailable / returned
  handoff_actor:
  receiver:
  data_artifact:
  data_version_or_hash:
  returned_artifacts:
  chosen_chart_or_reason:
  aggregation_and_scope:
  interpretation_risks:
  supported_conclusion:
```
