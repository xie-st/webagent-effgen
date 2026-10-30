# M0 后独立复核：代码与路线图

2026-10-30，北京时间。负责人：Codex。委托：独立验证 M0 是否支持结案，以及三项路线图调整是否必要；不启动 M1。本次代码快照对应 Git `336b68d`，项目整理基线为 `caf20c7`；运行代码与 M0 最终修正 `f518160` 一致，之后当前版本仅 README 有更新。

## 综合判断

按“建立可扩展骨架”的既定目标，M0 为 **8/10，可以结案**。模块边界与实际调用链一致，旧策略已迁入 baseline 端口，状态隔离和公共动作校验有行为证据。三项调整均有必要，主顺序保留；其中最低日志是 M1 的实现要求，M1/M3 的拆分是既有目标的分段验收。

## 独立验证

| 验证 | 结果与证据 |
|---|---|
| `python webagent.py check` | 通过；当前版本与 SDK 定位正确，SDK 原件哈希通过，连接配置仅检查形状。见 [check-output.txt](check-output.txt) |
| `python webagent.py test` | 21/21 通过；运行冻结代码与模拟模型响应，见 [test-output.txt](test-output.txt)、[run.json](run.json) |
| `python -m unittest discover -s "02_代码/03_工程工具/tests" -v` | 1/1 通过；实际复制完整版本、删除临时父项目后独立检查并运行测试，见 [workspace-test-output.txt](workspace-test-output.txt) |

已直接检查 `MyAgent.step → official.frame_from_request → Runtime.advance → observe/baseline/actions`、TaskState、旧 decide 兼容入口、两份测试及 SDK 模型会话和子进程代码；对照实施前 `4bb788d`，核对 baseline 策略、观察历史、memory、纠错、同源和当前编号规则的迁移。未发现需要重开 M0 的阻塞问题。本次是离线工程复核，不生成官方任务成绩。

## 三项调整的依据与裁定

1. **M1 分“接通”和“建立基线”：采纳。** 当前代码没有 EffGen policy；M0 测试替换的是模型响应。真实 EffGen 的额外调用、SDK 绑定和跨观察状态必须先验证，之后才有可解释的官方任务成绩。原 M1 已包含两类证据，将其标成 M1a/M1b 即可。M1a 保留真实 EffGen＋模拟 SDK 与 SDK 子进程两层检查；M1b 跑真实官方任务，记录全部逐项结果，不用成功率上涨替代接通验收。
2. **M1 明确最低调用日志：采纳，优先落实。** `web_agent/baseline.py:62` 直接调用 SDK，返回后只使用 `.text`；当前无统一 ModelPort 或 telemetry。有效回复一次调用，纠错用例两次，不能用动作步数代替调用量。本地 `runner.py` 从决策返回值读取可选 `model_calls/tokens`，当前 Runtime 只返回 action，不能提供真实调用账本。历史平台任务 731 为 8 步、10 次模型调用，也支持分别计数。最低日志随 M1a 的统一模型端口加入，记录目的、次数、耗时、错误与运行结束原因；M2/M3 按真实能力扩展事件。
3. **M3 分“真实单 Tab 闭环”和“多 Tab 调度”：采纳。** M0 只有官方适配；本地 BrowserAdapter 限于 loopback，语法也与官方协议不同。现有 smoke 的登录、429 和并行检查由测试脚本驱动，不能证明 Agent 已在真实网站闭环。M3a 先接真实观察、执行和 M2 的结果确认/恢复，实测接管与限流，留下串行参照；M3b 再验证依赖、共享写入和同任务耗时收益。

比较过三种处理：只润色原验收文字、在既有里程碑内设置验收点、另建日志等新里程碑。选择第二种：不改变 M0—M5 主结构，给不同证据设置明确关口，日志作为接入时的基础设施。M2、M4 与 M3 浏览器准备可同步的安排保持。

另校准一处状态表述：`adapters/official.py` 目前实现请求映射与能力声明，未实现统一模型端口；模型端口仍属于 M1。

## 材料与协作依据

- 按 [阅读清单](../../../06_开发框架/阅读清单.md) 阅读协作规则、比赛要求、整体理解、现有实现与本地环境、EffGen 接入材料、论文清单、优化思路及五份方法整理；本轮不新增论文方法。代码入口均以当前版本为准。
- 当前目标、架构及原验收：[开发方案](../../../06_开发框架/开发方案.md)；原完成证据：[M0结案](../../../06_开发框架/M0结案.md)。归档审查仅用于核对此前裁定，当前结论由本次读代码和复跑支持。
- 历史 75%：[成绩与原始导出索引](../../historical/batch-8ed63eb9d774f28ba098cfa7bb4f8e9c/result.md)、[report.json](../../historical/batch-8ed63eb9d774f28ba098cfa7bb4f8e9c/report.json)。其源码与依赖不可绑定到当前版本，保留历史归属，M1b 新建基线。
- Gabriel Chua：[Collaborating with Codex on Long-Running Tasks](https://www.linkedin.com/pulse/collaborating-codex-long-running-tasks-gabriel-chua-unpec)，2026-07-08；2026-10-30 读取原文。采用里程碑结束时分别审查实现与路线图、按已有证据更新下一目标的做法，沿用现有开发方案承载路线图。本文是协作经验，不作为 WebAgent 性能证据。

已核对本次范围、来源归属、完成证据、未完成阶段与原验收要求。路线图已更新；M0 保持结案，M1a 尚未开工，文件占用释放。
