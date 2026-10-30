# 工程检查

通过；具体用例见 test-output.txt。

测试版本：当前版本。验证真实 EffGen v1.3.0 接线、单动作、状态延续、SDK 子进程、日志与结果快照。使用模拟 SDK 响应，未连接平台或运行真实模型，官方成绩未填写。

遥测：telemetry.jsonl；模型调用 17 次（decision=12, correction=5）；调用前拒绝 0 次；运行结束原因：close, close, close, close, close, close, reset, close, close, reset, close。

## 主线程亲验裁定

2026-10-30 10:28（北京时间），Codex使用`.local/m1a-lock-venv`亲跑check、36项回归和工程独立复制1/1，均通过。此前五项日志探针全部销项：源程序本机raw/coordinator_probes.py，输出raw/coordinator-probes.json。

新增兼容入口预算探针：固定假时钟1000时state剩余10秒，第一观察deadline=1010；第二观察时钟推进至1005，deadline变成1015。结果见本机raw/coordinator-budget-probe.json。这说明agent_logic.decide每轮用当前时间加未扣除模型耗时的remaining刷新截止，不符合共用任务时限要求。应首次建立绝对截止并保存在任务state，同一任务后续观察沿用；SDK和ModelPort仍执行其各自原有截止约束。M1a尚未结案，待最小修正与回归。
