# M1a 工程检查

状态：通过（离线、真实 EffGen + 假 SDK；未连接官方平台，未运行真实模型）。

- 时间：2026-10-30（北京时间）
- 代码：`D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\02_代码\01_harness\当前版本`
- 冻结快照：`snapshot/harness`，代码指纹见 `run.json`
- Python：3.12.9，`D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\.local\m1a-venv\Scripts\python.exe`
- EffGen：1.3.0（PyPI，wheel sha256 `474a7fcf952f87995c19cfe261167d713ace9f9d8fc0773d134c42ea49d9d5e5`）
- 依赖：`requirements.lock`（132 个固定包），启动检查逐包核对版本

## 命令与结果

```text
.\.local\m1a-venv\Scripts\python.exe webagent.py test
→ 29 tests, OK
→ 本目录（run.json status=passed）
```

覆盖：M0 原有 21 项行为、真实 EffGen 接线与特性关闭、普通决策一次调用、连续观察 memory、纠错另计、截止检查、消息字段约束、遥测汇总、SDK 子进程绑定、独立复制启动。

独立复制验证：

```text
副本：D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\.local\independent-copy-m1a
run.py check → PASS（环境、EffGen、锁、SDK 哈希）
run.py test  → 29 tests, OK
```

原始输出：`test-output.txt`、`independent-check.txt`、`independent-test-output.txt`。

## 遥测

- 文件：`telemetry.jsonl`；汇总：`telemetry-summary.json`
- 本次工程测试共 17 次模型调用（decision=12，correction=5），失败 0；结束原因见汇总。
- 模型调用记录包含 purpose、call_seq、request_id、开始/结束、耗时、成功/错误；token/cost 不可取得处为 `null`。
- SDK 子进程测试单独验证了子进程内写入同一结果目录的 `telemetry.jsonl`，并记录平台返回的 `request_id=offline-test`。

## 未完成项

- 未连接官方平台，未运行真实 Qwen 模型，未产生官方成绩；这属于 M1b。
- 未提交或推送 Git（按主线程要求）。
- `requirements.lock` 在 Windows / Python 3.12.9 生成；其他平台安装前需重新确认平台专用包。
