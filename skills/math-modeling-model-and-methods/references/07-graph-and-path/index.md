# 图论路径类方法索引

## 这类问题主要解决什么
- 图论路径类问题主要处理“节点、边、网络、连通、最短路、运输线路、配送路径”等问题。
- 输出通常是路径、网络结构、最优路线、流量分配或连通方案。

## 典型输入 / 输出特征
- 输入：
  - 节点
  - 边
  - 距离 / 花费 / 权重 / 容量
  - 网络拓扑关系
- 输出：
  - 最短路径
  - 最优巡回
  - 最大流 / 最小割结果
  - 网络结构分析结论

## 候选方法清单
- 最短路（详见 `shortest-path.md`）
- 最小生成树
- 最大流 / 最小割
- 最小费用最大流
- TSP / VRP：先转 [优化类方法索引](../02-optimization/index.md)，并在 CP-SAT、MILP、DP、ACO 与基准启发式之间选择；本目录暂不提供单独的 TSP/VRP 教程。
- 网络连通性分析：先读 [未覆盖方法兜底](../00-routing/uncovered-method-fallback.md)，补齐网络指标、扰动方案和验证证据后再进入方法设计。

## 各方法适用场景 / 不适用边界
- 最短路：适合单源 / 多源路径代价最小问题；不适合目标本质是综合资源调度的复杂优化。若用户要详细看 `Dijkstra`、`Floyd-Warshall` 和 `Bellman-Ford` 的区别、适用边界和最短路示例，转 `shortest-path.md`。
- 最小生成树：适合网络搭建成本最小类问题；不适合存在复杂时序和容量约束的场景。若用户要详细看 `Prim` 和 `Kruskal` 的区别、适用边界和建网类示例，转 `minimum-spanning-tree.md`。
- 最大流 / 最小割：适合容量受限网络流问题；不适合没有明确流量含义的问题。若用户要详细看基本概念、可行流、增广链，以及 `Ford-Fulkerson`、`Edmonds-Karp` 和 `Dinic` 的区别，转 `max-flow-min-cut.md`。
- 最小费用最大流：适合既要求总流量最大、又要求总代价最小的容量网络问题；不适合没有源汇结构或费用不能按弧成本累加表达的问题。若用户要详细看费用定义、最短路增广思路和反向弧处理，转 `min-cost-max-flow.md`。
- TSP / VRP：适合巡回访问和车辆路径问题；不适合节点间关系并非路线型的问题。需要时间窗、容量或路径构造时，优先转优化类的 CP-SAT/MILP/DP/ACO 路由。
- 网络连通性分析：适合研究网络结构、脆弱性、关键节点；不适合需要精确连续变量预测的问题。当前无专属参考，必须走受控兜底而不是凭术语直接选指标。

## 常见混淆点与误判风险
- 题目里出现“路径”不一定就只用图论；如果还伴随资源约束，常要和优化类结合。
- 很多配送题不是纯 TSP，而是 VRP 或更复杂的调度优化。
- 网络结构分析和最优路径求解是两个不同层次的问题。

## 与邻近类别的区别
- 相比优化类：图论路径类更强调网络结构和节点边关系。
- 相比仿真类：图论路径类更关注结构求解，仿真类更关注系统运行过程。

## 待补充的方法文档
- shortest-path.md
- minimum-spanning-tree.md
- max-flow-min-cut.md
- min-cost-max-flow.md
- tsp-vrp.md
- network-connectivity.md

## 已补充的方法文档
- [最短路径（当前重点：Dijkstra、Floyd-Warshall 与 Bellman-Ford）](shortest-path.md)
- [最小生成树（当前重点：Prim 与 Kruskal）](minimum-spanning-tree.md)
- [网络最大流 / 最小割（当前重点：Ford-Fulkerson、Edmonds-Karp 与 Dinic）](max-flow-min-cut.md)
- [最小费用最大流（当前重点：最短路增广思路）](min-cost-max-flow.md)
