---
name: kaggle-l4x4-t4x2-training
description: |-
  当需要在 Kaggle Notebook 的 GPU L4 x4 或 GPU T4 x2 环境执行深度学习训练、异步 OP 搜索、多 Seed 独立复核、DDP、GPU 利用率诊断或结果账本合并时使用。根据实际 GPU profile 自动选择 4 worker、2 worker 或多卡 DDP；提供 PyTorch 可复用调度模式、全局 Batch Size 保持、失败隔离和结果合并规则。
metadata: {}
---

# Kaggle L4 x4 与 T4 x2 训练调度

本 Skill 管理两种 Kaggle 多 GPU profile：

| Profile | CLI accelerator | GPU 数 | 默认独立 worker | 默认 competition_sources |
|---|---|---:|---:|---|
| T4 x2 | `NvidiaTeslaT4` | 2 | 2 | `[]` |
| L4 x4 | `NvidiaL4` | 4 | 4 | 由 `kaggle-run-notebook-en` 的显式 L4 协议决定 |

账号、凭据、数据集挂载、Kaggle Save Version、状态、终止和 ZIP 下载仍由 `kaggle-run-notebook-en` 负责。本 Skill 只负责 Notebook 内的 GPU 工作分解、并发调度、DDP、失败隔离与结果合并。

## 不可跳过的边界

1. **请求配置不等于真实分配。** 训练前必须运行 GPU profile 预检并保存 JSON。GPU 数量或型号不符时 fail closed，禁止按目标 profile 的吞吐量排期。
2. **HPO 只用 Validation 指标。** Test ACC 不进入 sampler、剪枝、范围收缩或 best Trial 选择。
3. **保持实验协议。** 数据划分、增强、epoch、全局 Batch Size、优化器、scheduler、best checkpoint 和指标计算必须与基线一致。
4. **一张 GPU 同时只运行一个训练任务。** 除非已经有明确的显存与吞吐 canary 证明，否则禁止在同一张卡叠加两个训练进程。
5. **并发任务不能写同一个结果文件。** 每个 Trial/Seed 写独立 JSON 与目录，全部结束后统一合并 CSV、coverage 和失败账本。
6. **失败必须被记录。** OOM、NaN/Inf、数据错误、子进程异常和缺失输出不能伪装成成功结果。
7. **独立任务优先一卡一任务。** 只有单个任务无法单卡运行，或 profile 证明 DDP 能显著缩短关键路径时，才把一个任务拆到多卡。

## Profile 识别与预检

Notebook 第一段 GPU 代码必须根据目标 profile 执行：

```python
# T4 x2
!python /kaggle/working/kaggle-l4x4-t4x2-training/scripts/preflight_gpu_profile.py --profile t4x2

# L4 x4
!python /kaggle/working/kaggle-l4x4-t4x2-training/scripts/preflight_gpu_profile.py --profile l4x4

!nvidia-smi -L
```

预检成功后统一得到：

```python
PROFILE = "t4x2"  # 或 l4x4
GPU_COUNT = 2 if PROFILE == "t4x2" else 4
GPU_NAME_TOKEN = "T4" if PROFILE == "t4x2" else "L4"
```

同时记录 GPU 名称、显存峰值、每 Epoch 时间、每任务总时间、DataLoader 等待、OOM/NaN 和 GPU 利用率。时间排期使用稳定阶段 P90，不使用最快单 Epoch。

## 工作模式选择

| 场景 | T4 x2 | L4 x4 | 首选结构 |
|---|---|---|---|
| 多个独立 Seed/Trial/SNR | 2 个单卡 worker | 4 个单卡 worker | 动态共享队列，一卡一个完整任务 |
| 异步 OP 搜索 | 同时 2 个 pending Trial | 同时 4 个 pending Trial | 单控制器 ask/tell，worker 只训练 |
| 单模型单卡 OOM | 双 T4 DDP 或梯度累积 | 2/4 卡 DDP 或分组 DDP | 保持有效全局 Batch Size |
| 单任务计算受限且不可拆 | 2 卡 DDP canary | 4 卡 DDP canary | 达到预设收益门槛后采用 |
| CPU、增强或磁盘受限 | 优化数据管线 | 优化数据管线 | 增加 DDP 不能解决 CPU 等待 |

除已验证的显存例外外，不按模型名称决定并行方式。先看任务依赖关系、单卡显存和 canary profile。

## T4 x2 如何调用两张 GPU

### 独立 Seed 或 Trial

这是 T4 x2 的默认高吞吐模式：

1. 父进程创建一个共享任务队列。
2. 启动两个长期存活的 worker，物理 GPU 分别为 `0`、`1`。
3. 子进程必须在导入 Torch 和项目训练模块前设置 `CUDA_VISIBLE_DEVICES`。
4. 每个子进程只看到一张卡，因此训练代码内部统一使用 `cuda:0`。
5. worker 完成当前任务后立即领取下一个 Seed/Trial，不等待另一张卡。

```python
GPU_COUNT = 2
workers = [
    context.Process(target=worker_main, args=(rank, jobs, results))
    for rank in range(GPU_COUNT)
]
```

多 Seed 复核时，Seed 42 和 Seed 43 可分别占用 GPU 0/1；之后哪张卡先完成，哪张卡领取下一个 Seed。异步 OP 搜索同理，但下一 Trial 必须由父控制器使用所有已完成 Validation 结果生成。

### 双 T4 DDP

一个 Seed/Trial 必须使用两张 T4 时，采用一进程一卡 DDP：

```bash
torchrun --standalone --nproc_per_node=2 train_ddp.py
```

必须满足：

- `WORLD_SIZE == 2`，rank 0 使用 GPU 0，rank 1 使用 GPU 1。
- 使用 `DistributedSampler`，训练 sampler 每个 Epoch 调用 `set_epoch(epoch)`。
- Validation/Test 指标跨 rank 正确归约。
- 仅 rank 0 写 checkpoint、JSON、CSV 和 ZIP。
- 保持原有效全局 Batch Size：

```text
effective_global_batch = per_gpu_micro_batch * world_size * gradient_accumulation_steps
```

例如有效全局 Batch Size 为 16：

- 每卡 batch 8、累积 1：`8 * 2 * 1 = 16`。
- 显存不足时每卡 micro-batch 4、累积 2：`4 * 2 * 2 = 16`。

不能把每卡 batch 设为 16，否则有效全局 Batch 会变成 32，实验协议已经改变。

### `convoformer_v1_small` 已验证例外

在本项目混合域、数据增强、有效全局 Batch Size 16 的配置中：

- 单卡训练可能 OOM，禁止自动回退到单 T4 或单 L4。
- T4 x2：一个 Seed/Trial 独占两张 T4，使用 DDP；默认每卡 micro-batch 4、累积 2，先通过 30 Epoch canary 再进入正式实验。
- L4 x4：可划分为两组 `[0,1]` 与 `[2,3]`，同时运行两个独立的 2-L4 DDP Seed/Trial；每组必须使用独立端口、输出目录和结果文件。
- 任一目标卡不可见时直接记录预检失败。

## L4 x4 如何调用四张 GPU

独立任务使用四个 worker，绑定 GPU `0..3`。异步 HPO 同时允许四个 pending Trial。若一个任务使用四卡 DDP，则 `torchrun --nproc_per_node=4`，并按相同公式保持有效全局 Batch Size。

L4 x4 的账号、ARC 挂载、accelerator 和额度规则以 `kaggle-run-notebook-en` 为准。本 Skill 不自行修改 Kaggle metadata。

## 多 Seed 动态队列

建立不可变 `seed_manifest.json`，至少记录实验 ID、condition、Seed、固定 OP、增强版本、epoch 和协议版本。每个任务写入：

```text
results/worker_<gpu_rank>/<condition>_seed_<seed>/result.json
```

成功结果至少包含 `status=success`、Seed、Validation/Test 指标、best epoch、耗时、GPU 名称和 OP。失败结果使用 `status=failed`，记录 `cuda_oom`、`nan_inf`、`data_error` 或 `exception`，不得伪造缺失指标。

worker 数始终来自 profile：

```python
GPU_COUNT = {"t4x2": 2, "l4x4": 4}[PROFILE]
```

完整骨架见 [实现模板](references/implementation_patterns.md)。合并结果：

```bash
python /kaggle/working/kaggle-l4x4-t4x2-training/scripts/merge_seed_results.py \
  --results-root /kaggle/working/results \
  --seed-manifest /kaggle/working/seed_manifest.json \
  --output-dir /kaggle/working/merged
```

合并器必须检查重复任务、缺失任务、成功数、失败数和覆盖率。Mean、Std、95% CI 与 Top-k 只能使用成功 Seed；Top-k 不能替代完整多 Seed 均值。

## 异步 OP 搜索

父进程是唯一的 Optuna Study writer。GPU worker 只接收 Trial 参数并返回 Validation metric：

1. `GPU_COUNT=2` 时初始发出 2 个 Trial；`GPU_COUNT=4` 时初始发出 4 个 Trial。
2. 任一 Trial 完成，父进程立即 `study.tell(...)`，再为该空闲 GPU `study.ask()`。
3. 使用 `TPESampler(multivariate=True, constant_liar=True, seed=<固定值>)`，让 pending Trial 参与避让。
4. `n_startup_trials` 应不小于 `GPU_COUNT`，通常取 `GPU_COUNT` 的倍数；三个连续参数可统一使用 8 个 startup Trial。
5. 每个 Trial 使用声明好的训练 Seed policy，不能让随机 Seed 噪声替代参数优劣。
6. Trial 的 NaN/Inf 或训练异常记录后以 `FAIL`/`PRUNED` 告知 Study，不得伪造低 Validation 分数。

搜索结束后按 Validation 选择固定 OP，再使用与 HPO 不重叠的 Seed 清单进行复核。

## 基于时间上限的 Notebook 分片

使用 canary 得到单任务 P90 时间：

```text
waves = floor((notebook_cap_minutes - setup_packaging_minutes) / p90_task_minutes)
safe_independent_task_count = GPU_COUNT * waves
```

T4 x2 的独立任务每波 2 个，L4 x4 每波 4 个。DDP 任务占用的 GPU 数必须从可并发组数中扣除：

```text
parallel_ddp_groups = floor(GPU_COUNT / gpus_per_task)
safe_ddp_task_count = parallel_ddp_groups * waves
```

分片 A、B 之间若要求搜索结果互不干扰，必须使用独立 Study 名称、storage、sampler seed 和输出目录；每个分片内部仍按完成结果异步继承。

## DDP 采用门槛

DDP 用于缩短一个不可拆分任务，不用于增加独立任务总吞吐。采用前用相同数据、Seed、有效全局 Batch Size、优化器和增强做短 canary：

1. 单卡基线。
2. 目标 profile 的 DDP 版本。
3. 比较端到端墙钟、Validation 指标、样本数、OOM/NaN 和通信开销。
4. 建议只有 DDP 至少节约约 20% 墙钟时间且指标协议无异常时才采用；否则恢复一卡一任务。

参数化 DDP 模板见 [分布式训练模板](references/distributed_training_patterns.md)。

## 数据管线优化顺序

1. worker 启动后预加载只读 NPZ，避免每个 Seed 重复读取磁盘。
2. 从 `num_workers=2`、`pin_memory=True`、`persistent_workers=True` 开始测量。
3. GPU 搬运使用 `non_blocking=True`，但必须以 Epoch 时间证明收益。
4. NumPy/CPU 增强若成为瓶颈，可迁移到批量 Torch 运算，但必须先做固定输入与固定 RNG 的等价性测试。
5. AMP 只能在用户允许并完成 ACC/稳定性对照后启用；默认保持实验原精度。

## Trial 与 Seed 失败隔离

- Trial/Seed 循环内部使用 `try/except/finally`。
- 失败账本记录任务 ID、Seed、Trial、完整 OP、Epoch、最新指标、错误类型、GPU 和时间戳。
- 每个任务结束后释放模型、optimizer、scheduler、DataLoader、batch、checkpoint 引用，执行 `gc.collect()` 与 CUDA cache 清理。
- 单个任务失败后继续队列中的其他任务。
- 最终 ZIP 在任务循环之外生成，并包含 manifest、成功结果、失败账本、coverage 和参数配置。

## 提交前检查单

1. 明确 profile：`t4x2` 或 `l4x4`。
2. 远端预检确认实际 GPU 数量和型号。
3. 保存不可变 manifest 和实际 `GPU_COUNT`。
4. 选择模式：独立多 Seed、异步 HPO、双卡 DDP、四卡 DDP 或 2-GPU 分组 DDP。
5. 验证有效全局 Batch Size 没有改变。
6. 验证每个 worker/组拥有独立输出目录、端口和结果文件。
7. Validation 决定 OP；Test 只用于固定 OP 后的最终评估。
8. 合并账本并核验重复、缺失、成功、失败和 ZIP 完整性。

## 资源

- [实现模板](references/implementation_patterns.md)：参数化 2/4 worker 多 Seed 队列与异步 HPO。
- [分布式训练模板](references/distributed_training_patterns.md)：参数化 `world_size=2/4` 的 DDP、指标归约与 rank 0 写入。
- [官方资料与证据边界](references/official_sources.md)：Kaggle、Optuna 与 PyTorch 官方资料。
- `scripts/preflight_gpu_profile.py`：T4 x2 / L4 x4 fail-closed 预检。
- `scripts/preflight_l4x4.py`：旧 L4 x4 调用兼容脚本。
- `scripts/merge_seed_results.py`：合并独立 worker 结果并检测重复/缺失 Seed。
