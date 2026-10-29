# harness 固定入口

本目录位置保持稳定，存放本项目自己的 Agent 决策与适配代码。官方通信 SDK 独立放在[官方客户端目录](../03_官方客户端/README.md)，无需与每份 harness 或连接文件混放。

- [v1](v1/README.md)：从官方 baseline 建立的首个可回溯参照版本，修正自动化平台的单 Tab 约束。
- 后续版本使用 `v2/`、`v3/` 等独立目录，写明来源、变化和适用场景；从上一版复制后修改，保留旧版本。
- 默认版本由根 `webagent.json` 选择；启动用根 `webagent.py connect`，旧版本用 `--version v1`。
- 结果始终写入[统一测试结果目录](../../01_文本/05_测试结果/README.md)，与版本目录分开。

新版本可按如下方式建立，再补版本说明、检查并更新默认配置：

```powershell
Copy-Item -LiteralPath '02_代码/01_harness/v1' -Destination '02_代码/01_harness/v2' -Recurse
python webagent.py check --version v2
python webagent.py test --version v2
```

每次运行都有独立代码快照与文件指纹，复查旧结果时先读它的 `run.json`。旧运行没有代码指纹的，保留来源未知，不根据连接名称补认版本。
