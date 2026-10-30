# DSH 独立复核原始返回

作业：hub-11-mvuapcmc。代码基线为本目录冻结快照；以下意见须由主线程裁定。

**范围与证据**：只读固定快照 `20261030T012723_661056Z_当前版本_08583aaf` 及指定文档；未扩展记忆、未运行测试、未写文件、未改代码。`run.json` 的 `harness_sha256`、`tests_sha256`、`sdk_sha256` 逐项与快照实际文件一致；[test-output.txt](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/test-output.txt) 为 `Ran 29 tests ... OK`；[result.md](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/result.md#L3-L5) 明确为模拟 SDK、未接平台。快照 `sdk` 与 [v1/sdk](02_代码/01_harness/v1/sdk) 逐文件 SHA256 一致，Git 相对 `ecee1e5` 无 SDK/v1 改动。

**复核结论：M1a 当前不具备验收通过条件。** 主路径接线成立，但“最低日志”验收不成立；这与主线程“M1a 暂不通过”的裁定一致。最终由主线程裁定，本复核不自报通过。

## 1. 代码正确性

### 1.1 已知三项：复核确认，不重复计为新发现

1. **截止前拦截 SDK 0 调用但日志计 1（阻塞）**  
   位置：[model_port.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/web_agent/model_port.py#L114-L151) 第 114–151 行，尤其 117–118 行预检、138–151 行失败日志；[telemetry.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/web_agent/telemetry.py#L136-L184) 第 156–163 行计数。  
   触发：`execution_deadline` 已过，`SdkModelPort.generate` 在调用 `self._sdk.generate` 前抛出 `TimeoutError`。  
   影响：`except` 仍写一条 `model_call`，`Telemetry` 仍把 `model_calls/by_purpose` 计 1；日志与真实 SDK 调用量不符，M1a/M1b 调用量审计失真。  
   修复：预检失败单独写 `model_call_rejected`/`before_call` 事件，明确 `sdk_invoked=false`，不进入调用计数与 `call_seq`；只有实际调用 SDK 才计调用。

2. **动作 `stop` 结束后结束原因只有 `close`（阻塞）**  
   位置：[my_agent.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/my_agent.py#L104-L123) 第 104–105 行 `close()` 固定 `_end_run("close")`；107–117 行；[telemetry.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/web_agent/telemetry.py#L214-L248) `finish` 幂等。  
   触发：模型返回 `stop [answer]`，平台随后发送 `/close`。  
   影响：`run_end.end_reason` 始终为 `close`，无法区分 stop、截止、错误；M1b 的逐项结束原因无法与本地日志对应。  
   修复：`step` 记录最后动作/终止意图，`close` 时若 last action 为 `stop` 则映射为 `stop`；或在记录 stop 动作后立即 `finish("stop")`，保持 `finish` 幂等，后续 close 不覆盖。补 stop 场景测试。

3. **SDK 返回前没有调用开始日志（阻塞）**  
   位置：[model_port.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/web_agent/model_port.py#L114-L127) 第 114 行只取 `started`，119 行才调用 SDK，127 行以后才写 `model_call`；[telemetry.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/web_agent/telemetry.py#L164-L184)。  
   触发：SDK 挂起、被截止终止、进程被 kill、网络等待未返回。  
   影响：日志没有任何“调用已发出”的记录；调用量、耗时、失败原因无法证明，尤其截止路径。  
   修复：SDK 调用前先写 `model_call_start`（purpose/step/deadline），返回后写 `model_call_end`/`model_call_failed`，以 `call_id` 关联；截断/超时仍保留 start 记录。

### 1.2 其他实质问题

1. **截止失败被统一记为 `error:RuntimeError`，丢失 deadline 语义（阻塞，属已知 #1 同路径的结束原因连带影响）**  
   位置：[policy.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/web_agent/policy.py#L191-L196) 将 EffGen 的失败统一抛为 `RuntimeError`；[my_agent.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/my_agent.py#L107-L117) 只用异常类型生成结束原因；[test_m1a.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/tests/test_m1a.py#L176-L194) 第 193–194 行还断言 `error:RuntimeError`。  
   触发：ModelPort 预检超时，或 SDK 调用超时；EffGen 捕获后返回 `success=False`，policy 转为 `RuntimeError`。  
   影响：`model_call.error_type` 记录 `TimeoutError`，而 `step_error/run_end` 记录 `RuntimeError`，同一路径日志互相矛盾；M1b 无法区分“截止”与“生成失败”。  
   修复：保留 EffGen `response.metadata["error"]`/原始异常原因，将 `TimeoutError` 映射为 `deadline` 结束原因，或定义独立 `DeadlineExceeded`；测试改为断言截止语义，而不是 `error:RuntimeError`。

2. **观测/动作日志与模型调用日志的 step 口径可能不一致（非阻塞）**  
   位置：[my_agent.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/my_agent.py#L72-L101) 第 72 行 `frame_from_request(request, step=self._step)`，但 74–80、95–100 行日志使用内部 `_step`；模型调用使用 `context.step`（即 `frame.step`，来自请求）见 [policy.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/web_agent/policy.py#L177-L182) 和 [official.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/web_agent/adapters/official.py#L15-L32)。  
   触发：平台请求携带的 `step` 与内部 `_step` 不同（平台重试、非 0 起编号、某步异常后继续），或 `_step` 因未成功而未推进。  
   影响：`observation/decision` 的 step 与 `model_call` 的 step 无法对齐，逐次调用与操作日志的对应关系失效；当前平台若严格 0 起连续则暂不触发。  
   修复：统一以 `frame.step` 为日志 step，成功后 `self._step = frame.step + 1`；或同时记录 `platform_step` 与 `internal_step`。

3. **验收测试固化了错误行为，29/29 不能证明日志验收（阻塞证据）**  
   位置：[test_m1a.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/tests/test_m1a.py#L176-L194) 第 188–194 行：SDK 实际 0 调用却断言 `len(calls) >= 1`，并断言 `error:RuntimeError`；[test_m1a.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/tests/test_m1a.py#L124-L127) 断言正常路径结束原因为 `close`，没有 stop 场景；整套测试没有“SDK 返回前已有开始日志”的断言。[test_version.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/tests/test_version.py#L118-L125) 只断言 `run_end.model_calls >= 1`，不校验结束原因。  
   影响：测试把三项缺陷中的两项写成了期望值；修复后这些测试会先失败。`run.json` 中 9 个 run_id 只有 3 个 `end_reasons`，也说明多数测试运行未形成完整结束记录。  
   修复：预检失败断言 0 次模型调用或单独 rejected 事件；增加 start 事件、stop 结束原因、deadline 结束原因、step 一致性测试；所有场景 close 后逐 run 校验 `run_end` 与计数。

4. **兼容入口 `agent_logic.decide` 不产生完整运行日志（非阻塞）**  
   位置：[agent_logic.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/agent_logic.py#L18-L41) 每次调用新建 `Telemetry`，但无 `run_start`、无 `finish`，step 固定 0、run_id 固定 `legacy`。  
   触发：仍通过旧 `decide()` 入口运行。  
   影响：只有 `model_call`，没有 run 边界和结束原因；与 M1a 日志验收不一致。官方 `my_agent:MyAgent` 路径不受影响。  
   修复：若保留该入口为可用路径，补齐 run 生命周期；否则在 README/接口中明确仅兼容、不作为验收入口。

5. **`PlatformModel` 依赖 EffGen 内部提示前缀精确匹配（非阻塞风险）**  
   位置：[policy.py](01_文本/05_测试结果/runs/20261030T012723_661056Z_当前版本_08583aaf/snapshot/harness/web_agent/policy.py#L45-L58) 要求 prompt 必须以 `SYSTEM + "\n\n"` 开头，否则抛 `RuntimeError`；该异常不被 Runtime 的 JSON 纠错捕获。  
   触发：EffGen 直接提示增加结尾说明、历史/压缩、answer style，或未来调整提示格式。  
   影响：整步失败而不是纠错；当前固定 1.3.0、空工具、`answer_style=""` 下测试通过，暂不触发。  
   修复：改为显式消息构造路径，或对拆分失败提供容错回退；补对应测试。

### 1.3 已通过/未发现新问题的部分

- 调用链 `MyAgent → official.frame_from_request → Runtime → EffGenPolicy → PlatformModel → ModelPort → SDK` 与文档一致；Runtime 负责解析、校验、纠错与 memory 合并，policy 只产出原始文本，任务状态由外层 `TaskState` 承接。
- `build_agent_config` 固定 `tools=[]`、`AgentMode.SINGLE`，关闭 sub-agents、memory、capability probe、fallback/model switching、speculative execution；测试覆盖这些字段。
- 真实 EffGen 1.3.0 下普通有效决策一次调用、纠错另计、连续观察 memory、SDK 子进程绑定、独立复制 `check` 均有测试覆盖；消息只含字符串 `role/content`，token/cost 记 `null`。
- `reset/close` 清理状态与身份，异常路径有 `step_error`；除上述截止原因分类外，未发现新的状态生命周期阻塞缺陷。

## 2. 路线图完整性

**匹配部分**：M1a → M1b → M2 的顺序、M1b 的“先冻结 M1a、顺序运行官方可用套件、平台原件与本地日志留结果目录”、M2 的“目标核对/结果确认/verify-recover/独立判定器”、M3 未授权，均与要求一致，见[开发方案](01_文本/06_开发框架/开发方案.md#L19-L21)、[停止点](01_文本/06_开发框架/开发方案.md#L23)、[里程碑验收](01_文本/06_开发框架/开发方案.md#L82-L84)。未发现把 M1a、M1b 或 M2 误写成“已完成”；`result.md` 的“工程检查通过”只是基础设施证据，不是里程碑结论。

**需要修正的路线图问题**：

1. **[验收证据缺口，建议阻塞]** M1a 完成证据行只列单动作、一次调用、状态延续、SDK 子进程和独立运行，没有列出三项日志探针（实际调用数、开始事件、stop/截止结束原因），见[开发方案](01_文本/06_开发框架/开发方案.md#L19)。验收行和日志要求已明确要求开始/结束、调用次数与结束原因，见[验收](01_文本/06_开发框架/开发方案.md#L82)和[日志分期](01_文本/06_开发框架/开发方案.md#L106)。否则 `29/29` 容易被误当作 M1a 通过证据。建议把“日志探针通过”写入 M1a 完成证据，并生成新快照后重新复核。

2. **[状态文字未收敛，非阻塞]** [当前状态](01_文本/06_开发框架/开发方案.md#L5-L11) 仍保留“M1a 由 DSH 作业实施中（09:00 running）”，后文又写“候选已出、M1a 暂不通过”；建议合并为一条当前状态，写清修复范围、复验快照、负责人和时间，避免执行者按旧“running”继续。

3. **[M1b 证据依赖，建议阻塞]** M1b 要求逐项耗时、调用量、结束原因及代码指纹，见[开发方案](01_文本/06_开发框架/开发方案.md#L83)。当前代码的结束原因仍为 `close`/`error:RuntimeError`，在修复前无法形成合格的 M1b 本地日志基线；M1b 应继续等待 M1a 日志修复通过后再冻结。

4. **[外部阻塞]** 账号登录 401 已记录在[开发方案](01_文本/06_开发框架/开发方案.md#L9)，属于平台账号/外部条件，不应算代码过错；但它确实阻塞 M1b 官方可用套件和原件基线。建议仍将 M1b 标为外部阻塞，不启动官方批次。

5. **[范围表述，非阻塞]** [里程碑顺序](01_文本/06_开发框架/开发方案.md#L77) 写“M3 浏览器准备可同步开始”，与[本轮停止点](01_文本/06_开发框架/开发方案.md#L23)“不得进入 M3”并存；建议明确标注“M3 本轮未授权，不启动”，避免被误读为当前授权。

6. **M2 部分清楚**：M2 依赖 M1a/M1b 分别通过，交付 goal_checks、pending、verify/recover，验收为无效果不推进、缺项不能成功停止、结果不明先查证、恢复后继续且避免重复写入，见[开发方案](01_文本/06_开发框架/开发方案.md#L21)和[验收](01_文本/06_开发框架/开发方案.md#L84)。本轮没有 M2 代码或证据，属正常未开始。

## 未完成项

- M1a：修复三项日志缺口、截止原因分类、step 日志口径；更新测试（start、stop、deadline、rejected、step 一致性）；重新生成快照并复跑。
- M1b：未冻结、未顺序运行官方套件、无平台原件/逐项结果；账号 401 待用户核对。
- M2：未实现 `goal_checks`、`pending`、`verify/recover`，无独立判定器验证。
- 路线图：补充 M1a 日志探针证据、收敛当前状态、明确 M1b 日志门禁，并标注 M3 本轮不启动。

本次只读复核，未修改、提交或推送。
