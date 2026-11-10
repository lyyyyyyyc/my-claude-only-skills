# 评价类方法索引

## 这类问题主要解决什么
- 评价类问题主要处理“多指标综合打分、排序、优劣比较、方案评价、风险等级评估”。
- 输出通常是综合得分、排序结果、等级划分或优先级顺序。

## 典型输入 / 输出特征
- 输入：
  - 多个评价对象
  - 多个指标
  - 指标权重、偏好或专家判断
- 输出：
  - 综合得分
  - 排名
  - 等级 / 类别

## 候选方法清单
- AHP
- 熵权法
- TOPSIS
- 灰色关联分析
- 模糊综合评价
- CRITIC
- 变异系数法

## 已补充的具体方法文档
- 评价类方法选择总结：见 [evaluation-method-selection-summary.md](evaluation-method-selection-summary.md)
- AHP：见 [ahp.md](ahp.md)
- TOPSIS：见 [topsis.md](topsis.md)
- 熵权法：见 [entropy-weight.md](entropy-weight.md)
- 熵权法计算复核：见 [entropy-weight-checklist.md](entropy-weight-checklist.md)
- 灰色关联分析：见 [grey-relation.md](grey-relation.md)
- 模糊综合评价：见 [fuzzy-comprehensive-evaluation.md](fuzzy-comprehensive-evaluation.md)
- CRITIC：见 [critic.md](critic.md)
- 变异系数法：见 [coefficient-of-variation.md](coefficient-of-variation.md)
- 通用模型检验索引：见 [../validation/index.md](../validation/index.md)
- 评价稳健性：见 [evaluation-robustness.md](evaluation-robustness.md)

## 如何先做方法选择
- 如果你当前不是要学习某个具体方法，而是要先判断“评价类问题到底该选哪一种方法”，优先先看 [evaluation-method-selection-summary.md](evaluation-method-selection-summary.md)。
- 先看总结文档里的“优点 / 缺点 / 适用情况 / 数据量要求 / 是否用于权重计算”，再决定是否进入某个具体方法文档。
- 推荐顺序：
  1. 先看 [evaluation-method-selection-summary.md](evaluation-method-selection-summary.md)
  2. 先判断是进入赋权层、综合评价层还是稳健性验证层；稳健性验证先读通用模型检验索引
  3. 再根据题目特点进入 `ahp.md`、`entropy-weight.md`、`critic.md`、`coefficient-of-variation.md`、`topsis.md`、`fuzzy-comprehensive-evaluation.md`、`grey-relation.md` 或 `evaluation-robustness.md`

## 各方法适用场景 / 不适用边界
- AHP：适合层级清楚、专家判断强的问题；不适合指标很多且主观判断难统一的场景。
- 熵权法：适合数据较完整、希望弱化主观权重的问题；不适合完全缺少有效指标波动的信息。
- TOPSIS：适合多指标优劣接近“理想解 / 负理想解”比较的问题；不适合指标方向和标准化规则不清的情况。
- 灰色关联分析：适合样本少、信息不充分、重视趋势接近度的问题；不适合需要严格概率解释的场景。
- 模糊综合评价：适合边界模糊、等级划分不硬的问题；不适合想要非常刚性的精确排序。
- CRITIC：适合同时考虑指标冲突性和信息量的客观赋权；不适合指标高度共线且解释需求很强的场景。
- 变异系数法：适合正值、比率尺度且希望依据相对离散程度客观赋权的场景；不适合均值接近 0、均值为负或指标不满足比率尺度的场景。
- 评价稳健性分析：适合已经得到候选结果、需要检验权重、参数、标准化方式或方法替换后结论是否稳定的场景；它不是独立的主评价方法。

## 评价类二级路由与方法层级
先区分“赋权”“综合评价”和“稳健性验证”，再选择具体方法：

```text
评价指标体系
    ↓
赋权层
├── AHP：有专家判断或主观偏好
├── 熵权法：数据区分度驱动
├── CRITIC：区分度 + 指标冲突性
└── 变异系数法：相对离散程度驱动
    ↓
综合评价层
├── TOPSIS：输出数值排名
├── 模糊综合评价：输出等级隶属度或模糊等级
└── GRA：输出与参考序列的接近度
    ↓
稳健性验证
└── 权重扰动、参数敏感性、方法对照、排名稳定性
```

路由时至少记录：评价对象、评价指标、指标方向、是否有专家判断、样本量与对象差异、目标输出和权重来源。若需要最终排名，不能把单独的熵权法、CRITIC 或变异系数法直接当作完整排序方法，应继续进入 TOPSIS、GRA 或其他明确的综合评价层方法。

## 常见混淆点与误判风险
- “评价类”不等于“统计分析类”。评价类重点是综合打分和排序，统计分析类重点是解释关系和检验差异。
- 只要有多个指标，不一定就是评价类；如果目标是预测未来值，那应优先看预测类。
- 排名问题常误上 TOPSIS，但如果权重来源才是关键，可能更该先考虑赋权方法。
- 如果要在评价类方法之间进一步做“选型”，优先参考 [evaluation-method-selection-summary.md](evaluation-method-selection-summary.md) 里的优缺点、适用场景和共性总结。

## 与邻近类别的区别
- 相比优化类：评价类更关注“谁更好”，优化类更关注“怎样最优”。
- 相比统计分析类：评价类强调综合结果，统计分析类强调关系、显著性和解释。

## 后续可扩展的方法文档
- evaluation-method-selection-summary.md
- ahp.md
- entropy-weight.md
- entropy-weight-checklist.md
- topsis.md
- grey-relation.md
- fuzzy-comprehensive-evaluation.md
- critic.md
- coefficient-of-variation.md
- evaluation-robustness.md
