# Pillar 3: 工作量包装操作手册

## 一、研究背景中的学术故事

### 1.1 讲好"为什么"
Introduction 的第一段必须回答两个问题：
1. 这个研究领域的工程/科学重要性是什么？
2. 存在什么亟待解决的重要问题？

**模板**：
```
[工程/科学背景] plays a critical role in [重要领域]. However, 
[具体的挑战/问题] remains a significant challenge, primarily due to 
[根本原因]. Addressing this challenge is essential for [实际意义].
```

### 1.2 禁忌
- 不要泛泛而谈（"XX is very important in engineering" — 太模糊）
- 要说具体数字、具体场景、具体影响
- 把背景和你的研究方向紧密关联

---

## 二、文献综述：精准且全面

### 2.1 精准原则
针对你的研究问题和创新点，专门总结该方向的研究进展。不要为了凑字数而罗列与本文关系不大的文献。

### 2.2 全面原则
不能故意遗漏与你工作高度相关的文献（审稿人可能正是这些文献的作者）。

### 2.3 文献综述组织方式

**按主题分组**（推荐）：
```
Research on [topic] has progressed along several directions. 

In terms of [方向A], [作者] proposed [方法], which [成果] [citation]. 
[作者] further extended this by [改进] [citation]. 

Regarding [方向B], studies have focused on [具体方面] [citation, citation]. 
...

Despite these advances, [转折到"现有研究不足"].
```

**不要**：逐篇罗列（"Author A did X. Author B did Y. Author C did Z."）——这暴露了文献综述的浅薄。

---

## 三、参数介绍和标定过程

### 3.1 每个参数需要回答三个问题
1. **这个参数是什么？** — 物理/几何/统计含义
2. **这个参数从哪里来？** — 参考文献 / 实验测量 / 经验公式 / 标定过程
3. **这个参数为什么要取这个值？** — 物理依据 / 敏感性分析 / 前人经验

### 3.2 参数标定章节模板

```
The parameters used in the model are summarized in Table X. 

[参数名] represents [物理含义]. This value was determined based on 
[确定方法, e.g., calibration against experimental data from [citation] / 
direct measurement using [设备] / sensitivity analysis (see Section X)].

The [参数名] was set to [值], which is consistent with the range reported 
in previous studies ([citation], typically [范围]). A sensitivity analysis 
confirming the robustness of the results to this parameter is provided in 
[位置].
```

### 3.3 实用技巧
- 即使你实际上随意调的参，也要呈现出一个"科学合理"的参数确定过程
- 增加敏感性分析：即使只分析了一个参数，也能大大增加"工作量感"
- 用表格汇总所有参数（参数名、含义、取值、来源/依据），一张表顶半页纸

---

## 四、实验/模型介绍全面

### 4.1 详细描述清单

**实验类**：
- [ ] 实验设备（型号、厂家、关键参数）
- [ ] 实验材料（规格、来源、预处理过程）
- [ ] 实验流程（步骤、条件、持续时间）
- [ ] 数据采集方式（传感器类型、采样频率、精度）
- [ ] 对照组设置（为什么选择这些对照）
- [ ] 干扰因素排除（边界效应如何消除？环境因素如何控制？）

**数值模拟类**：
- [ ] 数值方法（FEM/FDM/FVM/...，求解器）
- [ ] 几何模型（尺寸、简化假设、边界条件）
- [ ] 网格（类型、数量、网格敏感性验证）
- [ ] 时间步长（取值依据、收敛性验证）
- [ ] 边界条件（类型、取值、物理依据）
- [ ] 求解设置（收敛准则、迭代方法）

### 4.2 排除干扰因素
审稿人最关心的一个问题：**你怎么知道你的结果是可靠的，不是被某种干扰因素造成的假象？**

必须回答：
- 边界效应如何消除？
- 网格敏感性如何验证？
- 实验可重复性如何？
- 环境影响如何排除？

---

## 五、深挖数据分析

### 5.1 分析层次

**Level 1 — 表层呈现**（4区水平）：
"Figure X shows the results. Parameter A increases with B."
→ 太浅！

**Level 2 — 规律分析**（3区水平）：
增加：变化趋势、线性/非线性、拐点、饱和等

**Level 3 — 机理分析**（2区水平）：
增加：为什么呈现这样的规律？背后的物理/化学/力学机制是什么？

**Level 4 — 对比与验证**（1区水平）：
增加：与文献/理论预测的对比、一致性讨论、差异原因分析

### 5.2 深挖清单
对每组数据，依次问：

1. **变化趋势**：随变量增大，结果如何变化？（线性？非线性？有无阈值？）
2. **影响因素**：什么因素主导了结果？有竞争关系吗？
3. **异常解释**：有无异常数据点？可能的原因？（不要回避！主动解释异常数据显示你的专业性）
4. **机制关联**：观察到的规律可以用什么已知的物理/化学机制解释？
5. **对比意义**：和已有研究/理论预测是否一致？不一致说明什么？

### 5.3 从数据到机制的过渡句式
```
This behavior can be understood by considering [机制]...

The observed [现象] is attributed to [机制], whereby [解释过程]...

This trend is consistent with [已知理论/模型], which predicts that 
[预期结果]...

The deviation from [预期] at [条件] suggests that [额外因素] 
may also play a role...
```

---

## 六、验证过程

### 6.1 为什么需要验证？
对论文中提出的新模型、新算法、发现的新现象，审稿人会问：**你怎么证明这是对的？**

### 6.2 验证层次

**基础验证**：
- 与实验数据对比
- 与解析解/理论解对比
- 与已有经典结果对比

**进阶验证**：
- 网格/时间步收敛性分析
- 参数敏感性分析
- 统计显著性检验
- 与多个已有方法/模型的系统性对比

### 6.3 验证段落模板
```
To validate the proposed model, the numerical results were compared with 
[基准数据来源]. As shown in Figure X, the model predictions show good 
agreement with [基准], with a maximum deviation of [X%] under [条件]. 
This level of agreement is comparable to or better than existing models 
([citation]), confirming the reliability of the proposed approach.

Further validation through [第二种验证方式] is provided in [附录/补充材料].
```

---

## 七、附录建议

在诊断报告中建议作者增加以下附录（不直接在正文中添加）：

- **附录A**：模型代码（如适用）
- **附录B**：补充实验结果
- **附录C**：网格/时间步收敛性分析细节
- **附录D**：参数敏感性分析
- **附录E**：更详细的实验/模拟设置

现实中大多数作者不公开代码/原始数据，但**建议放附录**本身就是一种工作量包装——让审稿人看到你做了额外工作。
