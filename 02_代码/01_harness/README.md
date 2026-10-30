# 版本与启动

[当前版本](当前版本/README.md) 是日常工作目录；[v1](v1/README.md) 保存一个阶段的成果。每个目录都有完整代码，互相独立。

平时在当前版本修改，沿用[开发方案](../../01_文本/06_开发框架/开发方案.md)的模块边界，按阶段验收。阶段结束并由用户决定保存后，在项目根执行 `python webagent.py new-version v2`，保存完整大版本；之后继续开发当前版本。

以下 `python` 指已安装当前版本 `requirements.lock` 的解释器。本机使用 `.local/m1a-lock-venv/Scripts/python.exe`；环境建立与独立运行见[当前版本说明](当前版本/README.md)。

在项目根运行：

| 命令 | 用途 |
|---|---|
| `python webagent.py check` | 检查代码与连接配置 |
| `python webagent.py test` | 本机离线测试 |
| `python webagent.py connect` | 连接赛方平台 |

默认运行当前版本。使用旧版时加 `--version v1`；默认配置在根 `webagent.json`。运行结果见[测试结果](../../01_文本/05_测试结果/README.md)。
