# 工程检查

通过；具体用例见 test-output.txt。

测试版本：当前版本。验证真实 EffGen v1.3.0 接线、单动作、状态延续、SDK 子进程、日志与结果快照。使用模拟 SDK 响应，未连接平台或运行真实模型，官方成绩未填写。

遥测：telemetry.jsonl；模型调用 17 次（decision=12, correction=5）；调用前拒绝 0 次；运行结束原因：close, close, close, close, close, close, reset, close, close, reset, close。

## 跨观察日志生命周期修复验收

2026-10-30 10:21（北京时间），使用项目根 `.local/m1a-lock-venv/Scripts/python.exe` 运行：

- `webagent.py check`：通过，Python 3.12.9、EffGen 1.3.0、SDK 原件哈希与连接配置检查通过。
- `webagent.py test`：36/36 通过，7.338 秒；工程独立复制检查通过。
- 独立复制 `.local/independent-m1a-lifecycle-8613c836`：`run.py check` 与 `run.py test` 均通过（36/36）；输出保存在 `raw/independent-copy-check.txt`、`raw/independent-copy-test.txt`。
- `raw/coordinator_probes.py` 读取本目录冻结代码，5/5 探针通过；原始结果见 `raw/coordinator-probes.json`。

探针结果：

| 探针 | 结果 |
|---|---|
| 截止前拦截 | SDK 0 调用，日志 0 调用 |
| stop 结束原因 | `stop` |
| SDK 在途可追溯 | 返回前已有 `model_call_start` |
| 同一注入端口 reset 两任务 | 实际 2 调用；两个 `run_summary` 的 `model_calls` 为 1、1 |
| 兼容入口同 state 两普通步+stop | 同一 run_id；step 0/1/2；call_seq 1/2/3；唯一 `run_end` 为 `stop` 且 `model_calls=3` |

本次使用真实 EffGen 1.3.0 与假 SDK 响应，未连接平台、未调用真实竞赛模型、未运行官方任务；官方成绩未填写。新增回归同时覆盖新 state 身份与计数重置、异常结束、EffGen 内部空答重试的逐次调用记录。
