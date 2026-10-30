# 当前版本

日常开发代码，初始复制自 v1；M0 骨架保留，M1a 已接入真实 EffGen v1.3.0。官方单步入口仍是 `MyAgent.reset/step/close`：每个请求映射为 `Frame`，由 `Runtime` 组装观察、调用 EffGen policy、解析 JSON、校验动作并合并 memory，最终只返回一个动作。

## 运行环境

- Python 3.11+；本机固定环境为项目 `.local/m1a-lock-venv`（验收入口）和 `.local/m1a-venv`（日常），均为 Python 3.12.9。
- 依赖已完整锁定在 `requirements.lock`；顶层约束见 `requirements.txt`。
- 在项目根安装：`.\.local\m1a-lock-venv\Scripts\python.exe -m pip install -r ".\02_代码\01_harness\当前版本\requirements.lock"`。
- 启动检查会核对 Python、EffGen 版本与公开接口、`requirements.lock` 全部包版本、SDK 原件哈希；不会连接平台。

在项目根运行：

```powershell
.\.local\m1a-lock-venv\Scripts\python.exe .\webagent.py check
.\.local\m1a-lock-venv\Scripts\python.exe .\webagent.py test
```

在本目录运行：

```powershell
& "..\..\..\.local\m1a-lock-venv\Scripts\python.exe" run.py check
& "..\..\..\.local\m1a-lock-venv\Scripts\python.exe" run.py test
```

## M1a 接线

```text
MyAgent.step
  → official.frame_from_request
  → Runtime（TaskState、观察、解析、校验、memory 合并）
  → EffGenPolicy（AgentConfig + Agent.run，单 Agent、空工具）
  → PlatformModel（自定义 BaseModel）
  → ModelPort.generate(messages, purpose, deadline)
  → third_party_agent.model.generate(messages)（当前绑定线程）
```

- EffGen 固定 `1.3.0`，用公开 `AgentConfig`/`Agent.run` 和自定义 `BaseModel`；每次尝试新建 Agent，避免框架短期记忆把一个网页步骤带入下一步。
- 单 Agent、`tools=[]`、`AgentMode.SINGLE`；关闭自动子代理、额外记忆、能力探测、fallback/模型切换和 speculative execution。`max_iterations=1` 只约束框架内部循环，外层没有新增步数上限。
- 普通有效决策只调用一次模型。无效输出由 `Runtime` 解析并触发一次纠错请求；纠错和框架内部重试都通过同一 `ModelPort` 计入日志。
- `ModelPort.generate(messages, purpose, deadline)` 只把 `system`/`user`/`assistant` 字符串消息交给 SDK；不传模型名、key、采样参数。平台统一模型，无其他模型或外部 API。
- 截止时间来自任务 `execution_deadline`，同时用于 `TaskState` 剩余时间和 `ModelPort` 调用前检查；SDK 仍按自己绑定的任务截止执行。
- 跨观察事实只保存在外层 `TaskState.memory`；`reset` 新建，`close` 清理。注入的同一个 `SdkModelPort`/`Telemetry` 会在每次 `reset` 重新绑定当前任务日志，因此第二轮不会把调用记到上一轮已结束的 telemetry。
- `agent_logic.decide` 保留原签名，并以传入的 `TaskState` 或可变 dict 作为整个任务的身份与进度来源：同一 state 连续观察共用一个唯一 run_id，step 递增、调用序号累计，普通动作不结束任务；`stop` 或异常只写一次真实 `run_end`。新 state 使用新 run_id 并从调用序号 1 开始。

## 日志

`run.py` 每次 `test`/`connect` 会创建结果目录，并把结果目录通过 `WEBAGENT_RUN_DIR` 传给 SDK 子进程。日志为结果目录下的 `telemetry.jsonl`，汇总为 `telemetry-summary.json`：

- 每次模型调用先写 `model_call_start`（调用序号、purpose、step、deadline），返回后写 `model_call_end` 或 `model_call_failed`；`request_id` 在结束事件中记录。截止前拒绝的调用写 `model_call_rejected`（`sdk_invoked=false`），不计入模型调用次数。
- `stop` 是终止动作，记录 `run_end.end_reason=stop`；截止结束为 `deadline`；其他失败保留异常类型。
- 运行/步骤、UTC 时间、PID、URL、观察版本、可取得的前一动作回执和最终动作。

## 文件

| 文件 | 作用 |
|---|---|
| `my_agent.py` | 官方 reset/step/close；默认构造 M1a Runtime 与遥测 |
| `agent_logic.py` | 兼容 `decide`/`SYSTEM`/`model`/`validate_action` 入口 |
| `web_agent/policy.py` | 真实 EffGen 配置、单次 raw 决策与纠错请求 |
| `web_agent/model_port.py` | 唯一模型边界、消息校验与同步 SDK 调用 |
| `web_agent/telemetry.py` | JSONL 运行/调用日志与汇总 |
| `web_agent/environment.py` | Python/EffGen 版本和公开接口检查 |
| `web_agent/runtime.py` | JSON 解析、动作校验、纠错循环、memory 合并 |
| `web_agent/contracts.py` | `Frame`、`Context`、`Capabilities`（含绝对截止） |
| `web_agent/state.py` | `TaskState`：memory、恢复计数、剩余时间 |
| `web_agent/observe.py` | 当前 AX/ID、去重历史、最近动作与恢复提示 |
| `web_agent/actions.py` | 公共动作规则：完整动作、当前 ID、同源 goto |
| `web_agent/baseline.py` | M0 baseline 保留，供旧测试和对照；默认不接线 |
| `web_agent/adapters/official.py` | 官方请求到 Frame 的映射及能力声明 |
| `sdk/` | 官方通信与模型接口原件，未修改 |
| `run.py` | 启动、检查、测试、快照和结果汇总 |
| `requirements.txt` / `requirements.lock` | 顶层依赖与完整固定环境 |
| `tests/` | M0 回归 + M1a 验收 |

## 测试

离线测试使用真实 EffGen 包和假 SDK 响应，不连接平台、不发起真实模型请求。覆盖：

- M0：Frame 映射、Runtime 接线、单次调用、状态隔离、动作校验、纠错、恢复动作、SDK 子进程。
- M1a：真实 EffGen 版本/公开接口、单 Agent/空工具/关闭特性、普通决策一次调用、连续观察 memory、纠错另计、调用开始/结束日志、截止拒绝、stop 结束原因、step 一致、消息字段约束、遥测与汇总。
- 日志生命周期：同一注入端口跨 reset 的两任务各归入 current telemetry；兼容入口同 state 的两普通步+stop 保持唯一 run_id、step 0/1/2、call_seq 1/2/3 且只在 stop 写一次累计 run_end；新 state 身份与计数重置；异常结束；EffGen 内部空答重试的每次真实调用都被记录。
- 独立复制：复制本目录后运行 `run.py check`，验证不依赖原目录。

测试结果目录、`test-output.txt`、代码快照和 `telemetry.jsonl` 由 `run.py test` 自动保存；官方成绩不在离线测试中填写。

复制本目录后可独立使用：

```powershell
python -m pip install -r requirements.lock
python run.py check
python run.py test
```

连接平台仍需根配置中的连接文件：

```powershell
python run.py connect --connection-file "连接文件路径"
```
