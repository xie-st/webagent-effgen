# 工程检查

通过；具体用例见 test-output.txt。

测试版本：当前版本。验证真实 EffGen v1.3.0 接线、单动作、状态延续、SDK 子进程、日志与结果快照。使用模拟 SDK 响应，未连接平台或运行真实模型，官方成绩未填写。

遥测：telemetry.jsonl；模型调用 17 次（decision=12, correction=5）；运行结束原因：close, reset, reset。

## 主线程亲验裁定（M1a 未通过）

Codex 于 2026-10-30 09:27 北京时间亲自运行 `.local/m1a-venv/Scripts/python.exe webagent.py check`、`webagent.py test`、`-m unittest discover -s 02_代码/03_工程工具/tests -v`。check、离线 29/29 与工程独立复制 1/1 均通过；当次冻结源码及指纹见 run.json。SDK 子进程绑定、合法单动作、普通决策一次调用、跨观察memory与独立复制均已有测试证据。

额外探针读取同一冻结快照，结果见本机 `raw/coordinator-probes.json`：

| 触发 | SDK实际调用 | 日志观察 | 裁定 |
|---|---|---|---|
| deadline在调用前已过期 | 0 | model_calls=1 | 调用量不准确，须把拦截与真实调用分开 |
| 模型返回 stop，随后close | 1 | end_reason=close | 无法从日志区分主动stop与普通close，须记录真实结束路径 |
| 在SDK generate内部观察日志 | 尚在途 | 尚无调用事件 | 若被强制终止会丢失该次调用，须先落开始事件并关联结束事件 |

因此本次是工程回归通过，不能据此结案 M1a。待修复、补测及独立复核后重新亲验。

生命周期额外探针见本机 `raw/coordinator-lifecycle-probes.json`：同一注入ModelPort经历reset后，第二任务实际调用1次但run_end汇总0；兼容decide入口连续2步都写step=0、call_seq=1，且没有run_end。两项均须纳入同一日志生命周期修复，不能用普通默认入口的通过结果替代。
