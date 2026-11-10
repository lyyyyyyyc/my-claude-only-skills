# T4 x2 / L4 x4 实现模板

以下骨架通过 `PROFILE` 参数同时支持两个 Kaggle GPU profile。替换项目训练函数时，不要破坏 GPU 绑定、任务队列、Validation-only HPO 和独立结果账本边界。

## Profile 配置

```python
PROFILE_CONFIG = {
    "t4x2": {"gpu_count": 2, "gpu_token": "T4"},
    "l4x4": {"gpu_count": 4, "gpu_token": "L4"},
}

PROFILE = "t4x2"  # 或 l4x4
GPU_COUNT = PROFILE_CONFIG[PROFILE]["gpu_count"]
GPU_TOKEN = PROFILE_CONFIG[PROFILE]["gpu_token"]
```

运行前应先执行 `preflight_gpu_profile.py --profile <profile>`，不能只依赖此常量。

## 多 Seed 动态队列

```python
from __future__ import annotations

import gc
import json
import multiprocessing as mp
import os
import traceback
from pathlib import Path


def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def seed_worker(gpu_rank: int, task_queue, result_root: str, required_gpu_token: str) -> None:
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_rank)

    # CUDA_VISIBLE_DEVICES 必须先于 Torch 和项目训练模块导入。
    import torch
    from project_training import build_worker_state, train_one_seed

    if torch.cuda.device_count() != 1:
        raise RuntimeError(f"worker {gpu_rank} expected one isolated GPU")
    gpu_name = torch.cuda.get_device_name(0)
    if required_gpu_token.lower() not in gpu_name.lower():
        raise RuntimeError(f"worker {gpu_rank} expected {required_gpu_token}, found {gpu_name}")

    torch.cuda.set_device(0)
    state = build_worker_state()
    worker_dir = Path(result_root) / f"worker_{gpu_rank}"

    while True:
        task = task_queue.get()
        if task is None:
            return
        task_id = str(task["task_id"])
        output = worker_dir / task_id / "result.json"
        record = None
        try:
            outcome = train_one_seed(state=state, task=task, device=torch.device("cuda:0"))
            record = {**task, **outcome, "status": "success", "gpu_name": gpu_name}
        except torch.cuda.OutOfMemoryError as exc:
            record = {**task, "status": "failed", "failure_kind": "cuda_oom", "error": str(exc)}
        except Exception as exc:
            record = {
                **task,
                "status": "failed",
                "failure_kind": "exception",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback_tail": traceback.format_exc(limit=8),
            }
        finally:
            write_json_atomic(output, record)
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()


def run_all_seeds(tasks: list[dict], result_root: str, profile: str) -> None:
    config = PROFILE_CONFIG[profile]
    context = mp.get_context("spawn")
    task_queue = context.Queue()
    workers = [
        context.Process(
            target=seed_worker,
            args=(gpu_rank, task_queue, result_root, config["gpu_token"]),
        )
        for gpu_rank in range(config["gpu_count"])
    ]

    for process in workers:
        process.start()
    for task in tasks:
        task_queue.put(task)
    for _ in workers:
        task_queue.put(None)
    for process in workers:
        process.join()
        if process.exitcode != 0:
            raise RuntimeError(f"worker {process.pid} exited with {process.exitcode}")
```

父进程顶层不能提前导入会初始化 CUDA 的项目模块。队列只传递 JSON 可序列化配置，不传递模型、DataLoader 或 GPU Tensor。

## 异步 HPO 控制器

父进程是唯一的 Optuna writer；GPU worker 只训练并返回 Validation metric。

```python
from __future__ import annotations

import multiprocessing as mp
import os

import optuna


PROFILE = "t4x2"
GPU_COUNT = PROFILE_CONFIG[PROFILE]["gpu_count"]
GPU_TOKEN = PROFILE_CONFIG[PROFILE]["gpu_token"]
TRIAL_BUDGET = 24
N_STARTUP_TRIALS = 8  # 同时是 2 和 4 的倍数。


def make_job(study: optuna.Study) -> dict:
    trial = study.ask()
    params = {
        "lr": trial.suggest_float("lr", 1e-5, 3e-3, log=True),
        "min_lr_ratio": trial.suggest_float("min_lr_ratio", 1e-4, 1e-1, log=True),
        "weight_decay": trial.suggest_float("weight_decay", 1e-8, 1e-3, log=True),
    }
    return {
        "trial_number": trial.number,
        "params": params,
        "min_lr": params["lr"] * params["min_lr_ratio"],
        "train_seed": 420001,
    }


def hpo_worker(gpu_rank: int, jobs, results, required_gpu_token: str) -> None:
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_rank)
    import torch
    from project_training import build_worker_state, train_one_hpo_trial

    if torch.cuda.device_count() != 1:
        raise RuntimeError("HPO worker expected one isolated GPU")
    if required_gpu_token.lower() not in torch.cuda.get_device_name(0).lower():
        raise RuntimeError("HPO worker received the wrong GPU profile")
    torch.cuda.set_device(0)
    state = build_worker_state()

    while (job := jobs.get()) is not None:
        try:
            value = train_one_hpo_trial(state, job, torch.device("cuda:0"))
            results.put({"trial_number": job["trial_number"], "state": "complete", "value": float(value)})
        except Exception as exc:
            results.put({
                "trial_number": job["trial_number"],
                "state": "fail",
                "error": f"{type(exc).__name__}: {exc}",
            })


def run_async_hpo(study_db: str) -> optuna.Study:
    sampler = optuna.samplers.TPESampler(
        seed=20260818,
        n_startup_trials=N_STARTUP_TRIALS,
        multivariate=True,
        constant_liar=True,
    )
    study = optuna.create_study(
        study_name="replace_with_experiment_id",
        storage=f"sqlite:///{study_db}",
        load_if_exists=True,
        direction="maximize",
        sampler=sampler,
    )

    context = mp.get_context("spawn")
    jobs, results = context.Queue(), context.Queue()
    workers = [
        context.Process(target=hpo_worker, args=(rank, jobs, results, GPU_TOKEN))
        for rank in range(GPU_COUNT)
    ]
    for process in workers:
        process.start()

    submitted = 0
    for _ in workers:
        jobs.put(make_job(study))
        submitted += 1

    completed = 0
    while completed < TRIAL_BUDGET:
        result = results.get()
        completed += 1
        if result["state"] == "complete":
            study.tell(result["trial_number"], result["value"])
        else:
            study.tell(result["trial_number"], state=optuna.trial.TrialState.FAIL)
        if submitted < TRIAL_BUDGET:
            jobs.put(make_job(study))
            submitted += 1

    for _ in workers:
        jobs.put(None)
    for process in workers:
        process.join()
    return study
```

T4 x2 同时维护 2 个 pending Trial，L4 x4 同时维护 4 个。任一 Trial 完成后立即 tell/ask，不按固定波次等待最慢任务。

## 数据搬运基线

```python
loader = DataLoader(
    dataset,
    batch_size=batch_size,
    shuffle=True,
    num_workers=2,
    pin_memory=True,
    persistent_workers=True,
)

for features, labels in loader:
    features = features.to(device, non_blocking=True)
    labels = labels.to(device, non_blocking=True)
```

这些参数不是自动加速保证，必须比较稳定阶段 Epoch P50/P90 和 GPU 利用率。

## Canary 与测试

1. 使用至少 `2 * GPU_COUNT` 个短 Trial 或 Seed，确认每张卡都领取任务。
2. 固定同一个 Seed，对比原单任务实现与 worker 实现的样本数、指标、checkpoint 和增强。
3. 注入一个受控任务失败，确认后续任务继续且最终 ZIP 同时包含成功结果和失败账本。
4. 检查结果目录不存在重复 `(condition, seed)` 或 Trial 编号。
5. 只有 coverage、指标和 ZIP 完整性通过后才进入正式运行。
