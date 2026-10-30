# M1a 最终独立差异复核

作业 hub-14-mvud65fg；代码基线 a3771e43，与主线程fb2859f2运行代码相同。以下为DSH原始返回；主线程已逐项裁定。

## 结论

代码：已知 08583aaf 五项日志缺口及裁定的截止语义、frame.step、兼容入口、reset、固定截止均已销项，未发现新的真实阻塞。路线图：主链路准确，仅两处文字未收敛，不影响 M1a 裁定。本轮未跑测试、未写文件、未核 SDK/依赖指纹。

## 代码核对（固定快照 a3771e43）

基址：`01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/`

| 修复目标 | 证据 | 判定 |
|---|---|---|
| 过期前拒绝不计 SDK 调用 | [model_port.py:127-139](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/web_agent/model_port.py#L127-L139) 预检即写 `model_call_rejected` 并抛错；[telemetry.py:245-297](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/web_agent/telemetry.py#L245-L297) 该事件无 `call_seq`、不进 `model_calls/by_purpose`；[run.py:167-175](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/run.py#L167-L175) 汇总分开计数 | 销项 |
| start 先于进入 SDK | [model_port.py:141-153](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/web_agent/model_port.py#L141-L153)：先落 `model_call_start`（含 `call_seq`）再 `generate`；end/failed 以 `call_id`+`call_seq` 关联；token/cost 全 null | 销项 |
| stop 真实结束 | [my_agent.py:104-113](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/my_agent.py#L104-L113) 决策即 `finish("stop")`；[my_agent.py:124-137](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/my_agent.py#L124-L137) close 仍映射 stop；[telemetry.py:330-337](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/web_agent/telemetry.py#L330-L337) finish 幂等，只一条 `run_end` | 销项 |
| deadline 语义 | [policy.py:27-45](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/web_agent/policy.py#L27-L45) `DeadlineExceeded(TimeoutError)`；[policy.py:200-226](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/web_agent/policy.py#L200-L226) 异常与 `metadata.error` 两路映射；[my_agent.py:127-133](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/my_agent.py#L127-L133) 结束原因记 `deadline` | 销项 |
| frame.step 一致 | [my_agent.py:82-115](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/my_agent.py#L82-L115) observation/decision/step_error 全用 `frame.step`，游标 `frame.step+1`；模型调用仍取 frame 口径 | 销项 |
| 注入端口 reset 两任务各 1 次 | [my_agent.py:54-58](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/my_agent.py#L54-L58) 每次 reset 重绑；[model_port.py:73-83](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/web_agent/model_port.py#L73-L83) `bind_telemetry` | 销项 |
| 兼容 decide 生命周期 | [agent_logic.py:60-110](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/agent_logic.py#L60-L110) 同 state 共享 run_id、step 游标与 telemetry；[agent_logic.py:111-175](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/agent_logic.py#L111-L175) 普通步不结束、stop/异常各一次 `finish`；新 state 新 run_id 隔离 | 销项 |
| 首次有限 remaining 固定绝对截止 | [agent_logic.py:68-86](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/agent_logic.py#L68-L86) 首值加当前时钟后存 `_execution_deadline`，后续复用；[test_m1a.py:258-309](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/tests/test_m1a.py#L258-L309) 断言 1000/1005 均 1010、1011 拒绝、end=deadline | 销项 |
| 测试固化错误期望 | [test_m1a.py:231-256](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/tests/test_m1a.py#L231-L256) 改为过期不触达 SDK、end=deadline；新增 stop、reset、兼容入口、retry、step 用例，共 15 个用例 | 销项（总数 37 以 worker 记录与主线程亲验为准，我未复跑） |

**残余（非阻塞，不影响 M1a 判定）**：
- `MyAgent.reset` 若复用同一外部注入的 `Telemetry` 对象，其已 `finish` 后幂等不写第二条 `run_end`（[telemetry.py:336-337](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/web_agent/telemetry.py#L336-L337)）。官方入口每 reset 走 `from_env` 新建，不触发；仅注入遥测跨 reset 的探针需确认是否覆盖。
- `model_call_end` 自身写盘失败会落入 except 再写 `model_call_failed`，同一 `call_seq` 出现 end+failed（[model_port.py:161-186](01_文本/05_测试结果/runs/20261030T023533_659935Z_当前版本_a3771e43/snapshot/harness/web_agent/model_port.py#L161-L186)），属极端 I/O 故障，不构成验收阻塞。

## 路线图

准确：M1a 仍“暂待最终裁定”，未提前冻结；M1b 明确以 M1a 通过并冻结代码/依赖为门禁，记 4 项×300 秒而非前端 10 项；M2 以 M1a/M1b 分别通过为前提，范围与停止点（推送交接后停、不进 M3）一致（[开发方案.md:9-24](01_文本/06_开发框架/开发方案.md#L9-L24)）。M1a 完成证据已补日志探针门禁（[:20](01_文本/06_开发框架/开发方案.md#L20)），M3 已标“后续授权、本轮不启动”（[:78](01_文本/06_开发框架/开发方案.md#L78)）。

小项（非阻塞）：[:5](01_文本/06_开发框架/开发方案.md#L5) 仍留“M1a 开工”，与 [:9-11](01_文本/06_开发框架/开发方案.md#L9-L11) 的“候选待裁定”并存；[:20](01_文本/06_开发框架/开发方案.md#L20) 证据列用完成时态写探针“通过”，而主线程亲验未结束，宜在裁定后定稿。
