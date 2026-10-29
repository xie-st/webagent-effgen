# 测试结果固定入口

本目录持续保留，源码升级不改变入口。

| 位置 | 内容 |
|---|---|
| `index.jsonl` | 新运行的追加索引，包含版本、类型和目录 |
| `latest.json` | 最近创建的运行位置；只更新指向，不覆盖旧结果 |
| `runs/<唯一运行ID>/` | 根启动器创建的会话或协议检查 |
| `local/<唯一运行ID>/` | 本地练习运行器创建的合成测试 |
| [历史批次 ypgf_v0](historical/batch-8ed63eb9d774f28ba098cfa7bb4f8e9c/result.md) | 用户提供的官方测试导出，代码位置待定位 |
| `historical/local-before-versioning/` | 旧脚本结果，尚无 harness 版本绑定 |

`python webagent.py connect` 自动保存本次代码快照、版本与 Git 信息，再连接平台。仅预留记录位置可执行 `python webagent.py new-run --version v1 --kind official`；预留目录不表示测试已执行。

每次目录中的 `run.json` 保存元数据，`result.md` 保存任务、指标与结论。平台任务编号与批次编号写入 `platform_run_ids`；原始报告、trace 和日志下载到 `raw/`。客户端会话结束不代表任务通过，成绩必须来自平台。

新结果唯一目录名使用 UTC 时间和随机后缀，避免同版本多次测试互相覆盖。切换默认版本只修改根配置，既有运行的版本、快照与来源记录保持不变。原始日志、trace 与快照保留本机；元数据与结论提交 Git。
