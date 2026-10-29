# 当前版本

日常开发代码，初始复制自 v1。目前是单标签页 baseline，尚未接入 EffGen。

新增模块的目录、接口和开发顺序见[开发方案](../../../01_文本/06_开发框架/开发方案.md)。各模块按功能边界开发，接入主循环时共用同一份任务状态。

| 文件 | 作用 |
|---|---|
| `agent_logic.py` | 决策、任务记忆和动作检查 |
| `my_agent.py` | 接收平台任务，调用决策代码 |
| `sdk/` | 官方通信与模型接口，保留原件和来源 |
| `run.py` | 启动、测试和保存快照 |
| `version.json` | 版本标识与 SDK 路径 |
| `tests/`、`requirements.txt` | 测试与依赖说明 |

Python 3.11 及以上，目前只用标准库。`sdk/` 内的同名 Agent 文件是官方样例，实际决策入口是本目录的 `agent_logic.py`。

本目录的测试随代码一起保存。新增模块应先能独立验证，再接入 `agent_logic.py`；交接说明实际覆盖的行为和待接入的位置。

项目内使用[根入口](../README.md)。单独复制本目录后，可运行 `python run.py check`、`python run.py test`；连接用 `python run.py connect --connection-file "连接文件路径"`。独立运行的结果默认放在本目录 `results/`，可通过 `--results-dir` 指定。
