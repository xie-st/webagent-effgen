# 官方 SDK 固定入口

当前下载包位于 `sdk-6eee7ddab626/`，来自用户指定的 `C:/Users/hiyad/Downloads/webarena-outbound-client.zip`，2026-10-30 导入。目录内原文件逐字节保留，`SOURCE.json` 记录原包及所有文件 SHA-256。

`third_party_agent/` 负责连接、任务子进程和统一模型调用；SDK 原件不原地修改。自有算法放到 `../01_harness/vN/`；本机连接配置放到项目 `.local/agent-connection.json`。

收到新 SDK 时，新建 `sdk-<新包哈希前12位>/` 并记录来源，再更新根 `webagent.json` 的 `sdk_root`；旧 SDK 保留。启动器验证固定包内文件指纹，每次运行复制 SDK 和所选 harness 到该次结果快照中。

赛方指南要求正确导入层级，并允许通过绝对路径指定连接文件；不要求把整个 Agent 项目塞进 SDK 目录。本项目启动器负责设置 Python 导入路径，兼容 Windows spawn 子进程。
