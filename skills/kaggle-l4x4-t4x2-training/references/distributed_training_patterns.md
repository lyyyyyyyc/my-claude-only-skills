# T4 x2 / L4 x4 参数化 DDP 模板

仅当一个训练任务不可拆分、单卡 OOM，或 canary 证明 DDP 能缩短关键路径时使用。独立 Seed/Trial 默认采用一卡一任务。

## 启动命令

```bash
# T4 x2
torchrun --standalone --nproc_per_node=2 train_ddp.py --profile t4x2

# L4 x4
torchrun --standalone --nproc_per_node=4 train_ddp.py --profile l4x4
```

`torchrun` 已提供 `LOCAL_RANK`、`RANK` 和 `WORLD_SIZE`。训练脚本中不要再次修改 `CUDA_VISIBLE_DEVICES`。

## 代码骨架

```python
from __future__ import annotations

import os
from time import perf_counter

import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler


PROFILE_CONFIG = {
    "t4x2": {"world_size": 2, "gpu_token": "T4"},
    "l4x4": {"world_size": 4, "gpu_token": "L4"},
}


def setup_ddp(profile: str) -> tuple[int, int]:
    expected = PROFILE_CONFIG[profile]
    local_rank = int(os.environ["LOCAL_RANK"])
    world_size = int(os.environ["WORLD_SIZE"])
    if world_size != expected["world_size"]:
        raise RuntimeError(f"expected world_size={expected['world_size']}, received {world_size}")
    if torch.cuda.device_count() != world_size:
        raise RuntimeError("visible CUDA device count does not match world size")
    names = [torch.cuda.get_device_name(index) for index in range(world_size)]
    if any(expected["gpu_token"].lower() not in name.lower() for name in names):
        raise RuntimeError(f"wrong GPU profile: {names}")
    torch.cuda.set_device(local_rank)
    dist.init_process_group(backend="nccl", init_method="env://")
    return local_rank, world_size


def reduce_validation(local_loss_sum, local_correct, local_count, device):
    values = torch.tensor(
        [local_loss_sum, local_correct, local_count],
        dtype=torch.float64,
        device=device,
    )
    dist.all_reduce(values, op=dist.ReduceOp.SUM)
    loss_sum, correct, count = values.tolist()
    if count <= 0:
        raise RuntimeError("validation has zero samples")
    return {"loss": loss_sum / count, "acc": correct / count, "count": int(count)}


def run_ddp_canary(
    profile,
    train_dataset,
    val_dataset,
    build_model,
    build_optimizer,
    train_epoch,
    validate_epoch,
    global_batch_size,
    seed,
    gradient_accumulation_steps=1,
    canary_epochs=20,
):
    local_rank, world_size = setup_ddp(profile)
    divisor = world_size * gradient_accumulation_steps
    if global_batch_size % divisor:
        raise ValueError("global batch must be divisible by world_size * accumulation_steps")
    per_rank_micro_batch = global_batch_size // divisor
    if per_rank_micro_batch <= 0:
        raise ValueError("per-rank micro batch must be positive")

    set_project_determinism(seed)
    train_sampler = DistributedSampler(
        train_dataset,
        num_replicas=world_size,
        rank=local_rank,
        shuffle=True,
        seed=seed,
    )
    val_sampler = DistributedSampler(
        val_dataset,
        num_replicas=world_size,
        rank=local_rank,
        shuffle=False,
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=per_rank_micro_batch,
        sampler=train_sampler,
        num_workers=2,
        pin_memory=True,
        persistent_workers=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=per_rank_micro_batch,
        sampler=val_sampler,
        num_workers=2,
        pin_memory=True,
        persistent_workers=True,
    )

    raw_model = build_model().to(local_rank)
    model = DDP(raw_model, device_ids=[local_rank], output_device=local_rank)
    optimizer, scheduler = build_optimizer(model)

    started = perf_counter()
    for epoch in range(1, canary_epochs + 1):
        train_sampler.set_epoch(epoch)
        train_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            device=local_rank,
            accumulation_steps=gradient_accumulation_steps,
        )
        scheduler.step()

    local_loss_sum, local_correct, local_count = validate_epoch(model, val_loader, local_rank)
    validation = reduce_validation(local_loss_sum, local_correct, local_count, local_rank)
    elapsed_seconds = perf_counter() - started

    result = None
    if local_rank == 0:
        result = {
            "status": "success",
            "profile": profile,
            "world_size": world_size,
            "global_batch_size": global_batch_size,
            "per_rank_micro_batch_size": per_rank_micro_batch,
            "gradient_accumulation_steps": gradient_accumulation_steps,
            "effective_global_batch_size": per_rank_micro_batch * world_size * gradient_accumulation_steps,
            "canary_epochs": canary_epochs,
            "validation": validation,
            "elapsed_seconds": elapsed_seconds,
            "gpu_names": [torch.cuda.get_device_name(index) for index in range(world_size)],
        }
        write_result_json_atomically(result)

    dist.barrier()
    dist.destroy_process_group()
    return result
```

项目必须复用原始 determinism、optimizer、scheduler、增强、数据划分和指标实现。

## Batch Size 示例

有效全局 Batch Size 固定为 16：

| Profile | world size | 每卡 micro-batch | 累积步数 | 有效全局 Batch |
|---|---:|---:|---:|---:|
| T4 x2 | 2 | 8 | 1 | 16 |
| T4 x2 显存受限 | 2 | 4 | 2 | 16 |
| L4 x4 | 4 | 4 | 1 | 16 |
| L4 x4 显存受限 | 4 | 2 | 2 | 16 |

BatchNorm 等依赖本地 batch 统计的层可能因每 rank batch 改变而产生差异，必须通过 ACC canary 验证，不能只看有效全局 Batch Size。

## 分组 DDP

L4 x4 可划分为两个 2-GPU DDP 组并发两个独立任务：

```text
任务 A: CUDA_VISIBLE_DEVICES=0,1 + 独立 MASTER_PORT
任务 B: CUDA_VISIBLE_DEVICES=2,3 + 另一 MASTER_PORT
```

每组必须使用独立输出目录、rendezvous 端口和结果文件。T4 x2 只有一组双卡 DDP，因此同一时刻只能运行一个双卡任务。

## 采用 DDP 前的对照

| 项目 | 单卡基线 | DDP canary |
|---|---|---|
| 数据、标签、划分 | 相同 | 相同 |
| Seed | 相同 | 相同且记录 sampler epoch |
| 有效全局 Batch | 原始值 | 相同 |
| optimizer/scheduler/增强 | 原始值 | 相同 |
| Validation | 记录 | 跨 rank 归约 |
| 结果账本 | 单条 | 仅 rank 0 写单条 |
| 决策 | 基线 | 达到预设时长收益且指标无协议外变化才采用 |

如果任务可拆成独立 Seed/Trial，应先比较 2/4 个单卡 worker 的总完成任务数，再决定是否牺牲总吞吐换取单任务 DDP 时延。
