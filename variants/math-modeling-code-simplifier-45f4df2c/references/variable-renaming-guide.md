# 变量命名与去中文化参考

> 调用 `$math-modeling-code-simplifier` 且涉及变量、字段、类别值处理时，默认优先读取本文件；不能跳过本文件直接凭印象改名。

## 目标
- 保持代码主体尽量不出现中文。
- 严格区分“注释中文、代码英文”：中文优先留在注释里，代码主体、变量名、函数名和路径名默认保持英文或拼音。
- 保持变量名可读、可区分、可复现，不因为改名而破坏含义。
- 对复杂英文变量，先给出拼音候选，再由用户决定是否采用。

## 三类处理对象

### 1. 建议保留英文的变量
- 简单、通用、稳定的变量优先保留英文或短字母：
  - `df`
  - `data`
  - `row`
  - `idx`
  - `cost`
  - `price`
  - `profit`
  - `loss`
  - `seed`
  - `rate`
  - `year`
  - `alpha`
  - `beta`
- 原因：
  - 这些变量是广泛通用表达，保留英文更稳、更容易读。

### 2. 建议改成拼音的复杂英文变量
- 较长、组合复杂、但又不是标准术语的变量，可以先提拼音候选：
  - `population_size -> zhongqun_size`
  - `correlation_matrix -> xiangguan_juzhen`
  - `early_stopping_threshold -> zao_ting_yuzhi`
  - `yield_per_acre -> danchan`
  - `price_correlation_factor -> jiage_xg_xishu`
- 原因：
  - 这类变量较长，改成拼音后仍能保留业务含义；
  - 同时不会像把所有变量都改成拼音那样明显损害可读性。

### 3. 必须去掉中文的中文变量
- 中文变量、中文函数名、中文中间量，默认必须改掉。
- 可改成：
  - 简单英文字母
  - 简洁英文
  - 拼音
- 例如：
  - `地块面积 -> dk_area` 或 `mianji`
  - `作物编号 -> crop_id`
  - `需求量 -> xuqiu` 或 `demand`

### 4. 必须去掉半转码变量
- 自动转换过程中若出现 `u8d77_point`、`u95ee_u9898_2_count_u636e_dir`、`avg_u9a8c_u8bc1_rmse` 这类半转码命名，默认视为“未完成去中文化”。
- 这类名字不能直接交付，必须继续改成：
  - 正常英文
  - 或可读的拼音 snake_case
- 例如：
  - `u8d77_point -> qi_point`
  - `u5b9a_u4f4d_project_root -> ding_wei_project_root`
  - `avg_u9a8c_u8bc1_rmse -> avg_yan_zheng_rmse`

## 中文字段与类别值处理
- 对原始中文列名、类别值，读取后第一步就重命名或编码。
- 推荐模式：
```python
lie_map = {
    "地块名称": "plot_name",
    "地块面积": "plot_area",
    "作物编号": "crop_id",
    "需求量": "demand",
}

df = df.rename(columns=lie_map)
```
- 若类别值为中文，可在读取后集中映射：
```python
zuowu_map = {
    "粮食": "liangshi",
    "蔬菜": "shucai",
    "食用菌": "junlei",
}

df["crop_type"] = df["crop_type"].replace(zuowu_map)
```

## 对话框变量候选表模板
在真正写代码前，先给用户一张候选表：

| 类别 | 原名 | 建议名 | 默认动作 | 理由 |
| --- | --- | --- | --- | --- |
| 保留英文 | profit | profit | 保留 | 通用且短，保留英文更稳 |
| 建议拼音 | correlation_matrix | xiangguan_juzhen | 待用户选 | 变量较长，拼音后仍保留含义 |
| 必须改掉中文 | 地块面积 | plot_area | 必改 | 代码主体尽量不保留中文 |

## 向用户解释时的固定口径
- 对“建议拼音”的变量：
  - 说明它是复杂长英文，改拼音后仍保留业务含义。
- 对“建议保留英文”的变量：
  - 说明它是通用、稳定、短小变量，保留英文更清楚。
- 对“必须去中文化”的变量：
  - 说明代码主体尽量不出现中文，所以必须先清理。

## 默认回退策略
- 若用户不细选：
  - 默认只改最明显的复杂长英文变量；
  - 默认改掉所有中文变量、中文函数名和中文中间量；
  - 默认继续清理所有半转码变量；
  - 默认保留短小通用英文变量。

## 默认不改的对象
- 第三方库别名与 API：
  - `np`
  - `pd`
  - `plt`
  - `random`
- 标准数学符号和常见短变量：
  - `i`
  - `j`
  - `k`
  - `t`
  - `x`
  - `y`
  - `z`
  - `alpha`
  - `beta`
- 广泛通用的业务短变量：
  - `cost`
  - `price`
  - `loss`
  - `profit`
  - `seed`
