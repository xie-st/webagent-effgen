# M1a 工程检查

状态：通过（离线、真实 EffGen + 假 SDK；未连接官方平台，未运行真实模型）。

- 时间：2026-10-30（北京时间）
- 代码：`D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\02_代码\01_harness\当前版本`
- 冻结快照：`snapshot/harness`，代码指纹见 `run.json`
- 更早的 runs 目录为过程记录；`latest.json` 指向本目录。
- Python：3.12.9，`D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\.local\m1a-venv\Scripts\python.exe`
- EffGen：1.3.0（PyPI，wheel sha256 `474a7fcf952f87995c19cfe261167d713ace9f9d8fc0773d134c42ea49d9d5e5`）
- 依赖：`requirements.lock`（132 个固定包），启动检查逐包核对版本

## 命令与结果

```text
.\.local\m1a-venv\Scripts\python.exe webagent.py test
→ 31 tests, OK
→ 本目录（run.json status=passed）
```

覆盖：M0 原有 21 项行为、真实 EffGen 接线与特性关闭、普通决策一次调用、连续观察 memory、纠错另计、调用开始/结束日志、截止前拒绝、stop 结束原因、平台 step 一致性、消息字段约束、SDK 子进程绑定、独立复制启动。

日志修复核验：

- 每次实际模型调用先有 `model_call_start`（含 call_seq、purpose、step、deadline），后有 `model_call_end` / `model_call_failed`；本目录 17 次 start 与 17 次 end 全部配对。
- 截止前拒绝写 `model_call_rejected`（`sdk_invoked=false`、无 call_seq），不计入 `model_calls`；截止场景 `run_end.end_reason=deadline`。
- `stop [answer]` 结束原因为 `stop`，其后不再接受步骤；普通 close 为 `close`。
- 观察、动作、模型调用统一使用 `Frame.step`。
- 12 次 run_start 对应 12 次 run_end；无未闭合运行。

独立复制验证：

```text
副本：D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\.local\independent-copy-m1a
run.py check → PASS（环境、EffGen、锁、SDK 哈希）
run.py test  → 31 tests, OK
```

从空环境安装锁定依赖后验证：

```text
新 venv：D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\.local\m1a-lock-venv
pip install -r requirements.lock → 成功
副本：D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\.local\fresh-copy-m1a
run.py check → PASS（132 个锁定包逐项一致）
run.py test  → 31 tests, OK
```

原始输出：`test-output.txt`、`environment-check.txt`、`root-check.txt`、`independent-check.txt`、`independent-test-output.txt`、`fresh-env-check.txt`、`fresh-env-test-output.txt`、`sdk-child/check.json`、`sdk-child/telemetry.jsonl`、`sdk-child/telemetry-summary.json`。

## 遥测

- 文件：`telemetry.jsonl`；汇总：`telemetry-summary.json`
- 本次工程测试共 17 次实际模型调用（decision=12，correction=5），成功 17，失败 0，不完整 0，调用前拒绝 0；结束原因见汇总。
- 模型调用记录包含 purpose、call_seq、call_id、request_id、开始/结束、耗时、成功/错误；token/cost 不可取得处为 `null`。
- `sdk-child/telemetry.jsonl` 为冻结快照上真实 `AgentProcess` 子进程的验收日志：1 次 start/end，`request_id=sdk-child-request`，`end_reason=close`。
- 截止测试在独立临时日志中校验 `model_calls=0`、`model_call_rejected>=1`、`end_reason=deadline`。

## 未完成项

- 未连接官方平台，未运行真实 Qwen 模型，未产生官方成绩；这属于 M1b。
- 未提交或推送 Git（按主线程要求）。
- `requirements.lock` 在 Windows / Python 3.12.9 生成；其他平台安装前需重新确认平台专用包。
