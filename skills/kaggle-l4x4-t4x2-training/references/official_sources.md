# 官方资料与证据边界

访问日期：2026-08-18。以下链接是本技能中外部行为断言的来源；Kaggle 分配到的实际 GPU 数量仍以 Notebook 内 `preflight_gpu_profile.py` 的运行输出为准。

| 来源 | 已采用的结论 | 边界 |
|---|---|---|
| [Kaggle Notebooks Documentation](https://www.kaggle.com/docs/notebooks) | Notebook 是 Kaggle 的托管计算环境；硬件配置和运行状态应在实际 Notebook 环境中核验。 | 本技能不将请求某个 accelerator 解释为平台保证一定分配目标数量或型号的 GPU。 |
| [Optuna: Easy Parallelization](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/004_distributed.html) | Optuna 支持多进程共享同一个持久化 storage 的并行优化。 | 本技能采用单控制器访问 Study，worker 不直接写 SQLite，以减少本地数据库并发写风险。 |
| [Optuna TPESampler](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html) | constant_liar=True 会惩罚运行中的 Trial，官方建议在昂贵、耗时且多 worker 的分布式优化中用它来减少相近参数配置。 | 它是异步近似，不等同于逐 Trial 严格串行 BO；所有最终结论仍需固定 OP 后多 Seed 复核。 |
| [PyTorch DistributedDataParallel](https://docs.pytorch.org/docs/stable/generated/torch.nn.parallel.DistributedDataParallel.html) | 单机 N GPU DDP 使用 N 个进程、每进程独占一个 GPU。 | DDP 是否值得取决于模型、batch 和数据管线，不能因为有两张或四张卡就默认启用。 |
| [PyTorch Data](https://docs.pytorch.org/docs/2.7/data.html) | DataLoader 提供 pin_memory、persistent_workers、num_workers 等参数。 | 参数不是自动加速保证，应以同协议 epoch 时间和稳定性测试决定。 |
| [torch.Tensor.to](https://docs.pytorch.org/docs/2.7/generated/torch.Tensor.to.html) | non_blocking=True 尝试异步数据拷贝，官方要求谨慎使用。 | 必须基准测试，不能仅凭设置该标志声称吞吐提高。 |
| [torch.profiler](https://docs.pytorch.org/docs/2.7/profiler.html) | PyTorch 提供训练过程性能剖析工具。 | profile 用于识别 CPU、数据搬运或 GPU 计算瓶颈；不能以模型名称代替测量。 |

## 本机 Kaggle 运行证据

2026-08-18 的 T4 x2 Canary 在 `competition_sources: []` 下获得两张 `Tesla T4`。普通模型日志证明 Seed 42/43 分别绑定 GPU 0/1；Convoformer 日志证明双 T4 DDP 启动。审计位于：

`%USERPROFILE%\.kaggle\codex_runs\mixed7_t4x2_fp32_noarc_launch_20260818`
