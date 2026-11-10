# 优化类方法索引

## 这类问题主要解决什么
- 优化类问题主要处理“在给定约束下，让目标最大 / 最小 / 最优”的问题。
- 输出通常是最优方案、最优值、资源分配方案、调度方案或路径方案。

## 典型输入 / 输出特征
- 输入：
  - 目标函数
  - 约束条件
  - 决策变量
  - 资源、容量、预算、时间等限制
- 输出：
  - 最优解
  - 最优目标值
  - 可行方案集合中的优选方案

## 候选方法清单
- 线性规划（详见 `linear-programming.md`）
- 整数规划 / 0-1 规划（详见 `integer-programming.md`）
- 非线性规划 / 混合整数非线性规划（详见 `nonlinear-programming.md`）
- CP-SAT（详见 [cp-sat.md](cp-sat.md)）：适合整数、0-1、逻辑与组合约束；应先与 IP/MILP/DP 比较
- 动态规划（详见 `dynamic-programming.md`）
- 遗传算法（GA，详见 `genetic-algorithm.md`）
- 粒子群（PSO，详见 `particle-swarm-optimization.md`）
- 模拟退火（SA，详见 `simulated-annealing.md`）
- 差分进化（DE，详见 `differential-evolution.md`）：适合作为连续黑箱优化候选；代码生成与参数确认转交 `math-modeling-intelligent-optimization-coder`
- 蚁群算法（ACO，详见 `ant-colony-optimization.md`）：适合路径逐步构造、排列和组合优化；代码生成与参数确认转交 `math-modeling-intelligent-optimization-coder`
- 多目标优化（详见 `multi-objective-optimization.md`）

## 各方法适用场景 / 不适用边界
- 线性规划：适合目标和约束均可线性表达的问题；不适合明显非线性关系。
- 整数规划 / 0-1 规划：适合选 / 不选、开 / 不开、分配决策类问题；不适合变量本质连续的问题。
- 非线性规划：适合目标或约束天然非线性的问题；不适合结构太复杂且无法稳定求解的场景。
- 动态规划：适合阶段决策、状态转移明显的问题；不适合状态爆炸严重的问题。
- 遗传算法：适合复杂、非凸、离散或难解析的问题；不适合可直接精确求解且规模适中的线性问题。若用户要详细看流程、选择/交叉/变异算子、优缺点与改进框架，转 `genetic-algorithm.md`。
- 粒子群：适合连续变量优化和参数寻优；不适合强离散和复杂逻辑约束主导的问题。若用户要详细看流程、公式、优缺点和改进框架，转 `particle-swarm-optimization.md`。
- 模拟退火：适合组合优化和局部最优多的问题；不适合需要高重复稳定性的严格精确解任务。若用户要详细看流程、参数、Metropolis 准则、优缺点与改进框架，转 `simulated-annealing.md`。
- 差分进化：适合连续、有边界、不可导或黑箱目标；不适合强离散、排列结构和约束逻辑主导的问题，除非另有离散化与修复设计。
- 蚁群算法：适合 TSP、VRP、路径构建和排列组合问题，前提是能定义启发式信息、信息素更新和可行路径修复；不应替代纯静态最短路/最大流图算法，也不能把离散 ACO 规则直接套到连续变量。
- 多目标优化：适合目标彼此冲突的问题；不适合实际只存在单一主目标却被人为复杂化的情况。

## 常见混淆点与误判风险
- “要求最优”不一定都需要智能算法；若能线性化，优先考虑规划模型。
- 很多路径 / 调度题虽然看起来像图论，本质仍是优化问题。
- 有多个目标时，不一定立即用多目标算法，也可能通过加权转单目标。

## 与邻近类别的区别
- 相比图论路径类：优化类更泛化，图论路径类更强调网络结构和节点边。
- 相比预测类：优化类是做决策，预测类是估计未来。

## 后续可扩展的方法文档
- linear-programming.md
- integer-programming.md
- nonlinear-programming.md
- cp-sat.md
- differential-evolution.md
- ant-colony-optimization.md
- dynamic-programming.md
- genetic-algorithm.md
- particle-swarm-optimization.md
- simulated-annealing.md
- multi-objective-optimization.md

## 已补充的方法文档
- [线性规划](linear-programming.md)
- [整数规划 / 0-1 规划](integer-programming.md)
- [非线性规划 / MINLP](nonlinear-programming.md)
- [CP-SAT 建模与验证入口](cp-sat.md)
- [动态规划](dynamic-programming.md)
- [优化算法选择指南](optimization-method-selection-summary.md)
- [遗传算法（GA）](genetic-algorithm.md)
- [粒子群优化（PSO）](particle-swarm-optimization.md)
- [模拟退火（SA）](simulated-annealing.md)
- [差分进化（DE）](differential-evolution.md)
- [蚁群算法（ACO）](ant-colony-optimization.md)
- [多目标优化](multi-objective-optimization.md)
