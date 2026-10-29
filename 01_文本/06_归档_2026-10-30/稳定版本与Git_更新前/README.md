# WebAgent 本地测试环境

归属：华为 2026 Hackathon WebAgent 项目。创建依据：2026-10-30 用户要求配置本地测试环境、阅读文献并推荐五个改动起点。

## 当前布局与状态

当前种子 Agent 为 [EffGen](../../01_文本/03_策略讨论/EffGen特性说明.md)，接入尚未实现。旧五候选选型记录与 AgentLab、AgentOccam 源码已归档到 `../../01_文本/06_归档_2026-10-30/EffGen选定前调研/`。

本目录保存练习站与运行器源码；根目录 `../../本地测试环境/` 仍保存官方客户端、原始结果及部分虚拟环境。运行资源保留原路径。

| 位置 | 内容与核查结果 |
|---|---|
| 本目录 `.venv`、`.venv-browsergym`、`.venv-browser-use` | 现有环境目录；历史验证见归档任务记录，本轮未重新运行 |
| `../../本地测试环境/.venv-smolagents` | 旧候选环境，保留现址 |
| `../../本地测试环境/.venv-effgen` | 目录存在，本轮检查未找到 effgen 包 |
| `../../本地测试环境/webarena-client/` | 实际官方客户端及原 baseline |
| `../../本地测试环境/results/` | 历史脚本检查结果和 trace |

依赖锁定文件继续保存在本目录；`sources.json` 保留最初克隆信息，候选源码当前已归档。

## 运行

在此目录打开 PowerShell：

```powershell
.\start.ps1 -Mode site
.\start.ps1 -Mode site -Scenario rate
.\start.ps1 -Mode site -Scenario login
.\start.ps1 -Mode smoke
.\start.ps1 -Mode browsergym
.\start.ps1 -Mode runner-smoke
```

练习站地址为 `http://127.0.0.1:8765`；停止按 Ctrl+C。每次启动清空内存数据并生成新任务值。论坛支持修改简介、发帖、回复、订阅和点赞，电商支持购物车和下单；延迟、一次性 HTTP 429、登录暂停单独切换。练习数据只保存在当前进程。

`smoke` 是脚本驱动的环境检查；登录恢复由测试脚本模拟用户点击。`runner-smoke` 使用明确标注的脚本驱动器，验证统一循环、日志和 trace。它们均不使用模型，不是 Agent 成功率或官方任务成绩。多 Tab 计时仅验证本地受控延迟页面的浏览器 IO 重叠。

BrowserGym 的旧 Chromium 在本机出现 `spawn UNKNOWN`，入口对当前进程的两个浏览器统一使用已验证的 Chromium 1243；未修改安装包。可预先设置 `WEBAGENT_CHROMIUM` 指向其他本地 Chromium 再测试。

## 接入自己的决策函数

```powershell
.venv\Scripts\python.exe runner.py --agent your_module:decide --task profile --headed
```

函数签名：`decide(*, task, observation, history, action_history, state)`。返回一个动作字符串，或 `{"action": "...", "model_calls": 1, "tokens": 123}`；不知道用量时不填，日志记为 null。`state` 仅在本次任务内共享。`--max-steps` 默认 40、`--timeout` 默认 300 秒；时间预算在轮次之间检查，模型调用内部超时须由适配层实现。

本地动作子集：`click [id]`、`type [id] [text]`、`press [Enter]`、`scroll [down]`、`goto [本地URL]`、`stop`。每轮观察重新编号，执行后旧编号失效。本地观察由 Playwright ARIA snapshot 与当前可见控件编号组合；这不是官方观察格式的完整复刻。执行器只允许访问本练习站，不向 Agent 暴露后台判分数据或脚本执行工具。

运行器在本目录的 `results/` 写入新结果；历史结果在 `../../本地测试环境/results/`。日志存储时间、URL、动作类型、结果、模型调用量和 token 元数据的 JSONL，以及 Playwright trace。可用 `.venv\Scripts\python.exe -m playwright show-trace results\某次运行.zip` 打开回放。

`agent_logic.py` 给出调用赛方 `third_party_agent.model.generate(messages)` 的最小消息决策核心，需要实际官方客户端和连接运行上下文。官方客户端现位于 `../../本地测试环境/webarena-client/`，含 `third_party_agent/` 和连接配置。本目录的最小核心与客户端的较完整 baseline 是两个文件，均未接入 EffGen；协议以实际客户端 README 为准。连接配置仅供本机运行。

## 重建依赖

```powershell
uv venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-local.lock.txt
.venv\Scripts\python.exe -m playwright install chromium
```

其他三个环境同理，分别使用 `requirements-browsergym.lock.txt`、`requirements-browser-use.lock.txt`、`requirements-smolagents.lock.txt`。本地练习不依赖 Docker；没有部署完整 WebArena，也没有把自建用例称为官方用例。
