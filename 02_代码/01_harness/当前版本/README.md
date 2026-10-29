# 当前版本

日常开发代码，初始复制自 v1。当前完成 M0 核心骨架：官方单步入口转为 `Frame`，经 `Runtime` 调用注入的 baseline 决策端口，再校验并返回一个动作。尚未接入 EffGen，官方适配仅声明单 Tab、无原生暂停、无截图。

新增模块的目录、接口和开发顺序见[开发方案](../../../01_文本/06_开发框架/开发方案.md)。各模块按功能边界开发，接入主循环时共用同一份任务状态。

| 文件 | 作用 |
|---|---|
| `my_agent.py` | 官方 reset/step/close；映射 Frame、注入 Runtime、维护 run 与步数 |
| `agent_logic.py` | 保留 `SYSTEM`、`validate_action`、`model`、`decide` 兼容入口 |
| `web_agent/contracts.py` | `Frame`、`Context`、`Capabilities` |
| `web_agent/state.py` | `TaskState`，承接 memory、恢复计数与截止剩余时间 |
| `web_agent/observe.py` | 当前 AX/ID、最多两页去重历史、最近 16 动作与恢复提示 |
| `web_agent/runtime.py` | 每轮上下文、决策端口、动作校验与状态合并 |
| `web_agent/actions.py` | 公共动作规则：完整动作、当前 ID、同源 goto |
| `web_agent/baseline.py` | 原单步决策、JSON 纠错与重复坏输出恢复 |
| `web_agent/adapters/official.py` | 官方请求到 Frame 的映射及能力声明 |
| `sdk/` | 官方通信与模型接口，保留原件和来源 |
| `run.py` | 启动、测试和保存快照 |
| `version.json` | 版本标识与 SDK 路径 |
| `tests/`、`requirements.txt` | 测试与依赖说明 |

Python 3.11 及以上，目前只用标准库。`sdk/` 内的同名 Agent 文件是官方样例，实际决策入口是本目录的 `agent_logic.py`，官方生命周期入口是 `my_agent.py`。

本目录的测试随代码一起保存。M0 回归覆盖 Frame 映射、Runtime 接线、单次模型调用、状态隔离、自定义端口动作校验、当前 ID、同源 goto、纠错与重复坏输出恢复。下一阶段把 Runtime 的 baseline 决策端口替换为 EffGen policy。

项目内使用[根入口](../README.md)。单独复制本目录后，可运行 `python run.py check`、`python run.py test`；连接用 `python run.py connect --connection-file "连接文件路径"`。独立运行的结果默认放在本目录 `results/`，可通过 `--results-dir` 指定。
