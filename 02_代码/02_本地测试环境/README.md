# 当前本地练习环境

本目录是唯一的当前练习环境入口，包含练习网页、浏览器运行器和脚本检查；Agent 决策代码统一在 `../01_harness/`，不在这里另存一份。

后续扩展见[架构与路线图](../../01_文本/06_开发框架/开发方案.md)。场景与脚本检查用于 Agent 联调；新增场景沿用现有运行器和结果目录。

| 文件 | 用途 |
|---|---|
| `sandbox.py` | 本机论坛、电商练习站、业务状态与故障注入 |
| `runner.py` | 观察页面、调用传入的决策函数、执行动作、保存回放 |
| `smoke_test.py` | 脚本检查网页与运行器；`profile_driver` 只用于检查 |
| `browsergym_smoke.py` | BrowserGym 环境检查 |
| `start.ps1` | 上述功能的统一入口 |
| `m2_faults.py` | 按写操作配置的可复现故障计划与激活记录 |
| `m2_grading.py` | 七类及复合任务的独立判定（实际状态+写入次数） |
| `m2_acceptance.py` | M2 浏览器验收运行器；脚本套件或注入 `decide` |
| `test_m2_fixtures.py` | 故障、判定与复合任务单元测试 |
| `m2_fault_plans/` | 可复现故障计划示例，可直接传给验收运行器 |
| `evidence/` | M2 手工证据，供主线程归档；不自动进入项目结果目录 |
| `requirements-*.lock.txt` | 各本地环境的固定依赖 |

## 启动与检查

在本目录运行：

```powershell
.\start.ps1 -Mode site
.\start.ps1 -Mode site -Scenario rate
.\start.ps1 -Mode site -Scenario login
.\start.ps1 -Mode smoke
.\start.ps1 -Mode runner-smoke
.\start.ps1 -Mode browsergym
```

练习站地址 `http://127.0.0.1:8765`，Ctrl+C 停止。支持修改简介、发帖、回复、订阅、点赞、购物车和下单。场景可选 `normal`、`slow`、`rate`、`login`；重启后重新生成任务数据。

这些检查使用脚本验证网页、运行器和回放。Agent 成功率需另用真实模型执行整项任务；当前官方模型调用依赖比赛任务上下文，本地模型入口按开发方案接入。

## M2 故障与判定

M2 本地单元只扩展本目录，不改 harness。故障按写操作配置，激活 `times` 次后自动恢复正常，种子可设置旧值，便于复现“追加而非替换”等场景。

```powershell
.\.venv\Scripts\python.exe -m unittest test_m2_fixtures -v
.\.venv\Scripts\python.exe m2_acceptance.py --suite scripted
.\.venv\Scripts\python.exe m2_acceptance.py --task profile --agent 模块:函数 `
  --fault-plan .\m2_fault_plans\profile_unknown.json
```

`--suite scripted` 是脚本化浏览器环境检查，`model_calls` 恒为 0；`--agent` 注入决策函数，任一步调用量未知时汇总为 null。默认写 `01_文本/05_测试结果/local/<UTC时间>_<标签>/`，不覆盖旧结果。判定器只读取实际 Fixture 业务状态和原任务要求，actor 的 `goal_checks` 仅作附注。故障 API、判定语义和故障计划格式见[M2 本地故障环境](M2本地故障环境.md)。

## 结果

所有新结果统一写入项目 `01_文本/05_测试结果/`：浏览器运行器写入 `local/<运行ID>/`，环境检查写入 `environment/<运行ID>/`。保留 `run.json`、摘要及回放；旧结果不移动。

本地动作是 `click [id]`、`type [id] [text]`、`press [Enter]`、`scroll [down]`、`goto [本地URL]`、`stop`。每轮页面重新编号；只允许访问本机练习站。本地观察与输入语法不完全等同官方协议。

## 环境

本目录的 `.venv` 用于练习站和运行器，`.venv-browsergym` 用于 BrowserGym 检查。启动脚本只使用这里的环境。

重建基础环境：

```powershell
uv venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-local.lock.txt
.venv\Scripts\python.exe -m playwright install chromium
```

BrowserGym 检查默认使用本机 Chromium 1243，可通过 `WEBAGENT_CHROMIUM` 指定其他 Chromium。
