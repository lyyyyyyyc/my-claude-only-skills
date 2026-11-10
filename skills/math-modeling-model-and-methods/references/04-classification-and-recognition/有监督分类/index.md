# 有监督分类方法索引

## 这类问题主要解决什么
- 有监督分类主要处理“样本已经有标签，希望学习输入到标签之间映射关系”的问题。
- 输出通常是类别标签、判别边界、分类概率，或针对新样本的类别预测结果。

## 典型输入 / 输出特征
- 输入：
  - 已标注样本
  - 特征向量或结构化特征
  - 图像 / 信号 / 文本 / 表格数据及其类别标签
- 输出：
  - 分类模型
  - 类别预测结果
  - 概率分布或判别边界

## 候选方法清单
- 逻辑回归（详见 `logistic-regression.md`）
- 决策树（详见 `decision-tree.md`）
- SVM（详见 `svm.md`）
- KNN（详见 `knn.md`）
- 朴素贝叶斯（详见 `naive-bayes.md`）
- 随机森林（详见 `ensemble-methods.md`）
- Bagging / Boosting / GBDT / XGBoost（详见 `ensemble-methods.md`）

## 这类方法的共性
- 需要训练集标签。
- 更强调“学会判别规则”，而不是自动发现数据结构。
- 常见评价指标包括准确率、精确率、召回率、F1 值、Balanced Accuracy、ROC-AUC、PR-AUC、LogLoss 和 Brier Score；指标要按类别平衡和误判代价选择。

## 进入具体方法前必须读取

- 执行顺序、训练/验证/测试条件和防泄漏：`../supervised-classification-workflow.md`
- 分类指标、概率校准和稳定性：`../classification-clustering-validation.md`
- 候选方法的二级分流：`../classification-clustering-selection.md`

### 数据划分条件

- 固定 baseline、无调参：训练集 + 测试集可以满足基本评估。
- 需要调参、模型比较或早停：使用训练集内交叉验证 + 独立测试集，或训练/验证/测试三分。
- 小样本：优先分层交叉验证；时间数据使用时间顺序；群组数据按群组隔离。
- 均值、中位数、IQR、标准化参数、编码映射、目标编码、特征选择和阈值都只能在训练数据/训练折中拟合。

## 按任务二级分流

```text
有标签
├── 二分类 / 多分类
├── 类别不平衡 → class_weight、阈值和 Macro-F1/PR-AUC 重点检查
├── 需要概率 → 逻辑回归或校准后的模型
├── 高维小样本 → 正则化逻辑回归、线性 SVM、朴素贝叶斯
└── 需要特征重要性/规则 → 决策树、随机森林、置换重要性或 SHAP
```

## 与无监督聚类的区别
- 有监督分类依赖标签；无监督聚类不依赖标签。
- 有监督分类更适合“识别 / 判别”；无监督聚类更适合“分群 / 结构发现”。

## 后续可扩展的方法文档
- logistic-regression.md
- decision-tree.md
- svm.md
- ensemble-methods.md
- knn.md
- naive-bayes.md

## 已补充的方法文档
- [逻辑回归（Logistic Regression）](logistic-regression.md)
- [决策树](decision-tree.md)
- [SVM](svm.md)
- [树模型集成方法](ensemble-methods.md)
- [KNN（K 近邻）](knn.md)
- [朴素贝叶斯（Naive Bayes）](naive-bayes.md)
