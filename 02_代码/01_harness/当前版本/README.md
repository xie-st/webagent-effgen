# 当前版本

日常开发代码，初始复制自 v1；M0 骨架保留，M1a 已接入真实 EffGen v1.3.0。官方单步入口仍是 `MyAgent.reset/step/close`：每个请求映射为 `Frame`，由 `Runtime` 组装观察、调用 EffGen policy、解析 JSON、校验动作并合并 memory，最终只返回一个动作。

M1a/M1b均已验收，官方固定基线3/4、75%，证据见[M1结案](../../../01_文本/06_开发框架/M1结案.md)。平台[视口PNG已开放](../../../01_文本/01_比赛要求/结构化资料/06_网页截图能力更新.md)，当前目录已按归档官方ZIP `23c08362` 精确升级SDK（新增`third_party_agent/browser.py`），并接入可空的截图引用与按需端口；M1的`v1`与旧运行快照保持原样。接入与验收安排见开发方案，本项目入口仍是EffGen，不被官方demo覆盖。

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

## 截图边界

新版SDK的`observation.screenshot`是可空元数据；本项目只在当前帧确有完整元数据时声明`Capabilities.screenshot=True`。旧服务缺字段或字段不完整时按纯文本运行，不报错，也不把上一帧图片当成本帧证据。

```text
Runtime.advance(frame, state, screenshot_reason="verify")
  → Runtime.request_screenshot(frame, state, reason)
  → ScreenshotPort.capture(frame)             # 默认不调用
  → third_party_agent.browser.save_screenshot(observation, raw/screenshots)
  → 校验尺寸/字节数/SHA-256/PNG IHDR
  → TaskState 只保存引用与本地路径
```

- 默认所有`step`只走AX；需要核验、恢复或诊断时显式调用`Runtime.request_screenshot(...)`，或`MyAgent.request_screenshot(reason=...)`使用最近一帧。`advance(..., screenshot_reason=...)`可在决策前先取图。
- 端口只在仍有效的SDK任务回调线程内同步调用`browser.save_screenshot`，不另起后台线程或下载；下载与本地处理共用`execution_deadline`，超时抛`TimeoutError`。
- 引用绑定`run_id`、`tab`、`observation_version`、`url`、`image_id`和截图`step`；截图`step`还必须等于当前`Frame.step`，跨帧错绑直接拒绝。成功抓取和`TaskState`引用都按含`step`的整组绑定缓存/失效：`step`前进后即使`observation_version`不变，也不复用旧引用或旧缓存。同一帧重复请求不再下载；没有本帧截图时返回`no_reference`，不沿用旧路径。
- 404/409、传输或校验失败返回失败结果并继续AX决策，不把保存提示或图片存在当作目标成功。当前帧`step`或绑定变化时`TaskState`中的旧引用失效。
- PNG只写入本次运行的`raw/screenshots/`（结果目录受Git忽略）；`Frame`、`Context`、`TaskState`、历史、日志和`ModelPort`都只含元数据/路径，绝不发送PNG、base64或图片消息给模型。
- `telemetry.jsonl`新增`screenshot`事件，记录`reason`、`result`（saved/cached/http_404/http_409/timeout/invalid/...）、`cache_hit`、`duration_ms`、`byte_size`、`sha256`、`http_status`及run/step/观察版本/URL/image_id关联；`run_end`事件汇总请求、缓存命中、成功、失败与字节数。

## 日志

`run.py` 每次 `test`/`connect` 会创建结果目录，并把结果目录通过 `WEBAGENT_RUN_DIR` 传给 SDK 子进程。日志为结果目录下的 `telemetry.jsonl`，汇总为 `telemetry-summary.json`：

- 每次模型调用先写 `model_call_start`（调用序号、purpose、step、deadline），返回后写 `model_call_end` 或 `model_call_failed`；`request_id` 在结束事件中记录。截止前拒绝的调用写 `model_call_rejected`（`sdk_invoked=false`），不计入模型调用次数。
- `stop` 是终止动作，记录 `run_end.end_reason=stop`；截止结束为 `deadline`；其他失败保留异常类型。
- 运行/步骤、UTC 时间、PID、URL、观察版本、可取得的前一动作回执和最终动作。
- 截图请求另记`screenshot`事件，含观察关联、缓存、耗时、字节数与结果；未请求截图时没有该事件。

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
| `web_agent/contracts.py` | `Frame`、`Context`、`Capabilities`（含绝对截止）和可空`ScreenshotReference` |
| `web_agent/state.py` | `TaskState`：memory、恢复计数、剩余时间、可失效截图引用 |
| `web_agent/screenshots.py` | 同步截图端口、本帧绑定/缓存、完整性核验与失败回退 |
| `web_agent/observe.py` | 当前 AX/ID、去重历史、最近动作与恢复提示 |
| `web_agent/actions.py` | 公共动作规则：完整动作、当前 ID、同源 goto |
| `web_agent/baseline.py` | M0 baseline 保留，供旧测试和对照；默认不接线 |
| `web_agent/adapters/official.py` | 官方请求到Frame的映射、可选截图引用及实际能力声明 |
| `sdk/` | 官方新客户端原件（归档`23c08362`），`SOURCE.json`核验全部文件 |
| `run.py` | 启动、检查、测试、快照和结果汇总 |
| `requirements.txt` / `requirements.lock` | 顶层依赖与完整固定环境 |
| `tests/` | M0回归、M1a验收、新版客户端/截图专项 |

## 测试

离线测试使用真实 EffGen 包和假 SDK 响应，不连接平台、不发起真实模型请求。覆盖：

- M0：Frame 映射、Runtime 接线、单次调用、状态隔离、动作校验、纠错、恢复动作、SDK 子进程。
- M1a：真实 EffGen 版本/公开接口、单 Agent/空工具/关闭特性、普通决策一次调用、连续观察 memory、纠错另计、调用开始/结束日志、截止拒绝、stop 结束原因、step 一致、消息字段约束、遥测与汇总。
- 日志生命周期：同一注入端口跨 reset 的两任务各归入 current telemetry；兼容入口同 state 的两普通步+stop 保持唯一 run_id、step 0/1/2、call_seq 1/2/3 且只在 stop 写一次累计 run_end；新 state 身份与计数重置；异常结束；EffGen 内部空答重试的每次真实调用都被记录。
- 截图专项：官方SDK指纹与`browser`接口、入口未被demo覆盖；完整/缺失/畸形元数据；run/tab/观察版本/URL错绑；截图`step`与当前帧不一致时拒绝（同观察版本的新`step`不复用旧引用/缓存）；同帧缓存与重复抓取；校验失败删除且不缓存；无本帧截图不沿用旧图；404/409回AX；请求前与处理中的绝对截止；真实SDK在任务会话内下载；消息不含PNG/base64/路径。
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
