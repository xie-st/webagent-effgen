# v1：完整的单标签页 baseline

本目录保存该版本的全部运行代码。Python 3.11 及以上，无第三方 Python 依赖。

| 文件 | 作用 |
|---|---|
| `agent_logic.py` | 把任务、页面和记忆交给模型，检查返回动作 |
| `my_agent.py` | 接收任务，调用决策代码，维护任务状态 |
| `sdk/third_party_agent/` | 官方连接、任务进程和统一模型调用 |
| `sdk/SOURCE.json` | 官方下载包来源和原文件指纹 |
| `run.py` | 检查、测试、连接和保存运行快照 |
| `version.json` | 版本名称及版本内 SDK 位置 |
| `requirements.txt` | Python 与依赖说明 |
| `tests/` | 离线协议与版本快照检查 |

## 使用

在本目录运行：

```powershell
python run.py check
python run.py test
python run.py connect --connection-file "连接文件绝对路径"
```

独立启动的结果默认写入本目录 `results/`；可加 `--results-dir "结果绝对路径"`。默认连接文件为本目录 `.local/agent-connection.json`，内容包含赛方提供的 `server`、`token`，不提交 Git。

在原项目中也可用根 `python webagent.py connect --version v1`，根入口自动指定项目连接文件与统一结果目录。可把整个 v1 文件夹复制到项目外独立使用。

## 来源与变化

基于官方 `webarena-outbound-client.zip`，SHA-256 为 `6eee7ddab6264aa228c29fce8ee0aff75f8e10067b65afcce9d5377dcdce496f`。`sdk/` 保留下载包原件；根层的 Agent 文件是我们维护的实现。SDK 里的同名文件是来源样例，不会作为当前决策入口加载。

相对官方 baseline，项目决策代码移除多标签页指导并拒绝 Tab 切换。当前仍未接入 EffGen。2026-10-30 按用户要求把 SDK、启动程序、依赖说明及测试收进本版本，决策算法保持原有行为。

离线测试使用模拟模型与本机服务，覆盖单步输出、动作修正、状态隔离、SDK 子进程通信、指纹和完整快照。官方成绩须另行从平台导入。
