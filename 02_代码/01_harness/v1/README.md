# v1 — 官方 baseline 的单 Tab 参照版本

来源：官方 `webarena-outbound-client.zip`，SHA-256 为 `6eee7ddab6264aa228c29fce8ee0aff75f8e10067b65afcce9d5377dcdce496f`。

保留通用 `my_agent.MyAgent` 与 `decide()`，通过赛方统一模型生成单个动作。相对官方原件，仅移除提示中的 `tab_focus` 与多 Tab 指导，并在动作校验中拒绝 Tab 切换，匹配当前自动化比赛限制。

此版本是原始 baseline 的参照，不是 EffGen 适配实现，也不承接此前未记录源码的成绩。EffGen 后续接入在新的版本目录实现。

启动：项目根目录 `python webagent.py connect --version v1`。
验证：`python webagent.py test --version v1`，包括 SDK spawn 子进程、任务模型绑定、单步输出、状态隔离及结果快照。模拟服务只监听本机，不调用真实平台或模型。
