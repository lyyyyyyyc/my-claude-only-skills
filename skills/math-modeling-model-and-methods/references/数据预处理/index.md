# 数据预处理方法索引

## 这类问题主要解决什么
- 数据预处理主要处理“原始数据还不能直接建模，必须先清洗、统一、补齐、转换、筛选”的问题。
- 输出通常是可建模的数据表、预处理规则说明、字段保留与删除依据，或供论文直接引用的处理流程说明。

## 典型输入 / 输出特征
- 输入：
  - 原始表格数据
  - 缺失值、异常值、重复值、编码不统一的数据
  - 时间序列、调查问卷、统计报表、实验观测数据
- 输出：
  - 清洗后的数据
  - 预处理策略
  - 特征转换结果
  - 可复核的处理说明

## 候选方法清单
- 缺失值处理（详见 `missing-value-handling.md`）
- 异常值处理（详见 `outlier-handling.md`）
- 重复值处理（详见 `duplicate-value-handling.md`）
- 数据标准化（详见 `normalization-and-standardization.md`）
- 数据离散化（详见 `data-discretization.md`）
- 特征选取（详见 `feature-selection.md`）
- 相关性分析（详见 `correlation-analysis.md`）
- 正态分布与 QQ 图（详见 `normality-and-qq-plot.md`）

## 方法选择提示
- 如果问题集中在空值、NULL、未知值、插补、删除、补全、特征保留与否，优先阅读“缺失值处理”。
- 如果问题集中在极端值、箱线图、3σ 原则、IQR 区间等，优先阅读“异常值处理”。
- 如果问题集中在重复记录、重复样本、去重规则，优先阅读“重复值处理”。
- 如果问题集中在 Min-Max、Z-Score、RobustScaler、MaxAbs 等缩放方式，优先阅读“数据标准化”。
- 如果问题集中在把连续变量变成类别区间、分箱、分位数法、等距法、等频法等，优先阅读“数据离散化”。
- 如果问题集中在筛选特征、F 检验、互信息法、过滤法，优先阅读“特征选取”。
- 如果问题集中在皮尔逊相关系数、斯皮尔曼相关系数、相关强度比较，优先阅读“相关性分析”。
- 如果问题集中在正态分布判断、QQ 图、是否服从正态分布，优先阅读“正态分布与 QQ 图”。

## 后续可扩展的方法文档
- outlier-handling.md
- duplicate-value-handling.md
- normalization-and-standardization.md
- data-discretization.md
- feature-selection.md
- correlation-analysis.md
- normality-and-qq-plot.md
- encoding-and-feature-transformation.md
- time-effect-processing.md

## 已补充的方法文档
- [缺失值处理](missing-value-handling.md)
- [异常值处理](outlier-handling.md)
- [重复值处理](duplicate-value-handling.md)
- [数据标准化](normalization-and-standardization.md)
- [数据离散化](data-discretization.md)
- [特征选取](feature-selection.md)
- [相关性分析](correlation-analysis.md)
- [正态分布与 QQ 图](normality-and-qq-plot.md)
