# 无监督聚类方法索引

> 说明：`无监督分类/` 是现有目录名；本 SKILL 的概念名称统一为“无监督聚类”。

## 这类问题主要解决什么
- 无监督聚类主要处理“数据没有标签，但希望自动发现内部结构、相似群体或密度团块”的问题。
- 输出通常是聚类结果、样本分群、结构层次，或噪声点识别结果。

## 典型输入 / 输出特征
- 输入：
  - 未标注样本
  - 数值特征、距离矩阵或相似度信息
  - 图像 / 信号 / 文本 / 表格中的无标签对象
- 输出：
  - 聚类结果
  - 簇结构或层次结构
  - 代表中心、树状图或噪声点

## 候选方法清单
- K-means（详见 `k-means.md`）
- 层次聚类（详见 `hierarchical-clustering.md`）
- DBSCAN（详见 `dbscan.md`）
- BIRCH（详见 `birch.md`）

## 进入具体方法前必须读取

- 聚类目标、预处理接口、候选算法和参数敏感性：`../unsupervised-clustering-workflow.md`
- 内部/外部指标、噪声比例和稳定性：`../classification-clustering-validation.md`
- K-means、DBSCAN、层次聚类和 BIRCH 的边界：`../classification-clustering-selection.md`

## 方法选择提示
- 如果你已经大致知道要分几组，并希望有“质心”来解释每组特征，优先考虑 K-means。
- 如果你更关心样本之间的层次关系，想用树状图展示结构，优先考虑层次聚类。
- 如果你更关心密度成团、复杂形状簇以及噪声点识别，优先考虑 DBSCAN。
- 如果样本规模很大，希望先用聚类特征压缩簇信息，并接受数据更偏球形的前提，可优先考虑 BIRCH。

这些只是初筛条件。最终必须结合距离定义、标准化方式、参数敏感性、簇规模、噪声比例和业务解释；`MinPts≈p+1`、样本量阈值等都只能作为经验起点。

## 已补充的方法文档
- [K-means（均值聚类）](k-means.md)
- [层次聚类（Hierarchical Clustering）](hierarchical-clustering.md)
- [DBSCAN（基于密度的聚类）](dbscan.md)
- [BIRCH](birch.md)
