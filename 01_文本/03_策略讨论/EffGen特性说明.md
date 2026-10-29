# EffGen 特性说明

EffGen 是 Python Agent 框架，提供模型、工具和执行循环的组合方式。本项目已确定以它为种子 Agent，用于承载网页决策、任务状态与后续 harness 改进。

文档核查基线为 **v1.3.0**，Python 要求 **3.11 及以上**；这是本轮参考版本，项目实际运行版本尚未锁定。[官方仓库](https://github.com/ctrl-gaurav/effGen/tree/v1.3.0) · [PyPI](https://pypi.org/project/effgen/1.3.0/)

## 核心执行方式

`AgentConfig` 配置模型、工具、系统提示词和执行规则，`Agent.run()` 驱动推理与工具执行，工具结果进入后续推理，最终返回 `AgentResponse`。工具调用支持 `auto`、`native`、`react`、`hybrid` 模式；框架支持单 Agent 与子 Agent 路由。[配置源码](https://github.com/ctrl-gaurav/effGen/blob/v1.3.0/effgen/core/agent_config.py)

## 与本项目有关的能力

| 特性 | 提供的机制 | 在本项目中的用途 |
|---|---|---|
| 工具与 ReAct 循环 | 声明工具、读取调用、执行并反馈结果 | 将网页观察、决策和动作回执接入循环 |
| 模型适配 | 统一模型接口及 OpenAI 兼容服务适配 | 本地实验可用兼容服务；比赛侧单独封装官方 messages 接口 |
| 任务记忆与上下文 | 短期和长期记忆配置、会话、上下文压缩 | 保存任务条件、已核实进度和必要历史 |
| 工具调用修复与停滞处理 | 调用解析恢复、无进展检测、失败结束信息 | 定位格式错误与重复动作，衔接本项目恢复逻辑 |
| middleware | 在运行、模型调用、工具调用前后插入处理 | 添加动作校验、日志、预算和结果检查 |
| 多 Agent 与工作流 | 路由、子任务分解、工作流依赖与结果合流 | 承载真实网站的任务编排，页面隔离和写入协调由项目实现 |
| 人工交互 | 审批、澄清、输入等回调 | 衔接真实网站登录验证、暂停与用户接管 |
| 执行记录 | 结果对象、调用账本、状态与检查点 | 记录运行结束原因和调用消耗，关联项目动作日志 |

上述为框架能力；本项目的网页适配、真实网站并行和接管均尚未实现。子代理路由本身不等于多 Tab 浏览器并行，框架结束成功也不等于官方任务判分通过。

## 代码阅读入口

以下路径均相对 EffGen v1.3.0 上游源码。

| 路径 | 阅读重点 |
|---|---|
| `effgen/core/agent.py`、`agent_config.py` | Agent 构造与配置 |
| `effgen/core/agent_react.py`、`agent_tool_execution.py` | 推理循环与工具执行 |
| `effgen/models/base.py` | 自定义模型适配接口 |
| `effgen/tools/base_tool.py` | 自定义工具接口 |
| `effgen/core/middleware.py` | 模型与工具调用钩子 |
| `effgen/core/thread.py`、`effgen/memory/` | 运行历史与记忆 |
| `effgen/core/workflow.py`、`sub_agent_manager.py` | 任务编排与子代理 |
| `effgen/core/agent_response.py`、`ledger.py` | 结果、结束原因及用量 |

框架本身的设计目标是让小模型完成工具任务；本项目采用它的执行结构，验收主模型仍按比赛要求使用统一 Qwen3.6-35B-A3B。
