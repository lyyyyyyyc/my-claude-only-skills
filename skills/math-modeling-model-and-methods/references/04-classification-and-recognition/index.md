# 分类识别类方法索引

## 这类问题主要解决什么
- 分类识别类问题主要处理“把对象判到哪一类”“识别状态 / 类型 / 标签”的问题。
- 输出通常是类别标签、识别结果、归属判断或聚类结果。

## 典型输入 / 输出特征
- 输入：
  - 特征向量
  - 已标注样本或未标注样本
  - 图像 / 信号 / 文本 / 表格特征
- 输出：
  - 类别标签
  - 分类边界
  - 聚类结果

## 分类结构
- 有监督分类（详见 `有监督分类/index.md`）
- 无监督聚类（参考目录暂保留为 `无监督分类/`，详见 `无监督分类/index.md`）

## 二级路由顺序

先读取 [`classification-clustering-selection.md`](classification-clustering-selection.md)，确认是否有标签、目标输出、类别不平衡、距离结构和解释需求；再进入监督分类或无监督聚类索引。不要在没有这些信息时直接把所有算法并列推荐。

如果用户要求从“选方法”继续到“怎么做”，按以下顺序加载：

1. 有标签：[`supervised-classification-workflow.md`](supervised-classification-workflow.md)。
2. 无标签：[`unsupervised-clustering-workflow.md`](unsupervised-clustering-workflow.md)。
3. 评价与稳健性：[`classification-clustering-validation.md`](classification-clustering-validation.md)。
4. 最后读取一个或少数几个具体方法文档。

## 候选方法清单
- 有监督分类
  - 逻辑回归（详见 `有监督分类/logistic-regression.md`）
  - 决策树（详见 `有监督分类/decision-tree.md`）
  - SVM（详见 `有监督分类/svm.md`）
  - KNN（详见 `有监督分类/knn.md`）
  - 朴素贝叶斯（详见 `有监督分类/naive-bayes.md`）
  - 随机森林（详见 `有监督分类/ensemble-methods.md`）
  - Bagging / Boosting / GBDT / XGBoost（详见 `有监督分类/ensemble-methods.md`）
- 无监督聚类
  - K-means（详见 `无监督分类/k-means.md`）
  - 层次聚类（详见 `无监督分类/hierarchical-clustering.md`）
  - DBSCAN（详见 `无监督分类/dbscan.md`）
  - BIRCH（详见 `无监督分类/birch.md`）

## 各方法适用场景 / 不适用边界
- 逻辑回归：适合二分类或多分类基础任务，解释性较好；不适合关系极其复杂的高维非线性任务。
- 决策树：适合规则可解释、特征类型混合的问题；不适合单树稳定性要求很高的场景。
- SVM：适合小样本、高维分类问题；不适合超大规模样本且参数调节成本高的场景。
- KNN：适合基线分类和局部相似识别；不适合维度高、距离度量失效的问题。
- 朴素贝叶斯：适合条件独立近似成立、快速分类的问题；不适合强相关特征主导的复杂识别任务。
- 随机森林：适用于高维数据，以及准确率要求较高的场景。
- Bagging / Boosting / GBDT / XGBoost：适合希望通过集成学习提升精度的场景；多分类复杂、类别过多或强依赖单模型解释性时要谨慎。
- 聚类：适合无标签、先做结构发现的问题；不适合用户其实要监督分类却误用无监督方法。若用户想看“固定簇数、质心更新”的直观方法，优先转 `无监督分类/k-means.md`；若更关心树状图、层次结构和后置决定簇数，优先转 `无监督分类/hierarchical-clustering.md`；若更关心密度成团、复杂形状簇与噪声识别，优先转 `无监督分类/dbscan.md`；若样本规模很大、希望用簇的压缩表示来做一次扫描式处理，可再看 `无监督分类/birch.md`。这里的“无监督分类”是历史目录名，概念上统一称为“无监督聚类”。

## 常见混淆点与误判风险
- “分类识别”不等于“评价”。前者是分类型或识别标签，后者是综合打分排序。
- 无标签数据常误用监督分类方法。
- 聚类结果不能直接当成真实类别结论，需要额外解释和验证。
- `n<10000`、`p<20`、`n<5000` 等规模条件只能作为经验起点，不能作为绝对算法边界。
- 类别不平衡时不能只报告 Accuracy；聚类时不能只凭一次轮廓系数决定方法。

## 与邻近类别的区别
- 相比统计分析类：分类识别强调分组与判别，统计分析强调解释和检验。
- 相比预测类：分类识别通常预测类别，预测类更常输出连续数值。

## 后续可扩展的方法文档
- 有监督分类
  - `有监督分类/logistic-regression.md`
  - `有监督分类/decision-tree.md`
  - `有监督分类/svm.md`
  - `有监督分类/ensemble-methods.md`
  - `有监督分类/knn.md`
  - `有监督分类/naive-bayes.md`
- 无监督聚类
  - `classification-clustering-selection.md`

## 已补充的方法文档
- [分类/聚类方法选择](classification-clustering-selection.md)
- [有监督分类执行流程](supervised-classification-workflow.md)
- [无监督聚类执行流程](unsupervised-clustering-workflow.md)
- [分类与聚类验证、稳定性与报告](classification-clustering-validation.md)
- [有监督分类索引](有监督分类/index.md)
- [逻辑回归（Logistic Regression）](有监督分类/logistic-regression.md)
- [决策树](有监督分类/decision-tree.md)
- [SVM](有监督分类/svm.md)
- [树模型集成方法](有监督分类/ensemble-methods.md)
- [KNN（K 近邻）](有监督分类/knn.md)
- [朴素贝叶斯（Naive Bayes）](有监督分类/naive-bayes.md)
- [无监督分类索引](无监督分类/index.md)
- [K-means（均值聚类）](无监督分类/k-means.md)
- [层次聚类（Hierarchical Clustering）](无监督分类/hierarchical-clustering.md)
- [DBSCAN（基于密度的聚类）](无监督分类/dbscan.md)
- [BIRCH](无监督分类/birch.md)
