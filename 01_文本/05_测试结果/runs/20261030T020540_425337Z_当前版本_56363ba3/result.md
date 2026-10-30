# 工程检查

通过；具体用例见 test-output.txt。

测试版本：当前版本。验证真实 EffGen v1.3.0 接线、单动作、状态延续、SDK 子进程、日志与结果快照。使用模拟 SDK 响应，未连接平台或运行真实模型，官方成绩未填写。

遥测：telemetry.jsonl；模型调用 17 次（decision=12, correction=5）；调用前拒绝 0 次；运行结束原因：close, decide, close, close, close, close, close, reset, close, close, reset, close。

## 主线程复验：M1a 仍未通过

2026-10-30 10:05，北京时间，Codex 使用从锁文件重建的 `.local/m1a-lock-venv` 亲跑 check 与31项回归，均通过。完整冻结代码和测试输出见本目录。

额外验收程序保存于本机 `raw/coordinator_probes.py`，结果 `raw/coordinator-probes.json`，直接读取本目录快照并使用真实EffGen+假SDK：

| 探针 | 结果 |
|---|---|
| 截止前拦截 | SDK0调用、日志0调用，通过 |
| stop结束原因 | stop，通过 |
| SDK在途可追溯 | 返回前已有model_call_start，通过 |
| 同一注入端口reset两次 | 实际各1调用，run_end计数为1、0，未通过 |
| 兼容入口连续两普通步+stop | 三步均step0/call_seq1/run_id=legacy；逐步run_end为decide、decide、stop，未通过 |

剩余两项的验收要求：同一注入端口在每次reset后汇入当前任务遥测；兼容入口必须把同一state内连续观察视为一个任务，唯一run_id，步骤0/1/2、调用序号1/2/3，最终stop只产生一次run_end且累计3调用。新任务使用新state时身份和计数重置。不得通过将每次decide声明为独立run来规避跨观察日志。

补充亲验：假SDK首空响应、随后有效响应，真实EffGen自动重试。SDK实际2次，model_call_start=2、model_call_end=2，summary_model_calls=2，返回一条click动作；框架内部额外调用未漏记。结果见本机 raw/coordinator-framework-retry.json。
