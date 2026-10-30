# M2 本地故障环境早期主线程检查

2026-10-30 12:47（北京时间），主线程从当时工作树复制本地环境 Python 源码到 `snapshot/`，指纹见 `source-sha256.json`，使用本地环境 `.venv/Scripts/python.exe` 执行冻结的 `m2_acceptance.py --suite scripted --out <本目录>/scripted`。

真实 Chromium 执行10个脚本场景，9个符合预期；这属于环境检查，不是M2策略、真实模型或官方成绩。逐项业务判定与写次数见[场景汇总](scripted/summary.md)。

未通过的是 `missing_subscribe_vote`：订阅故障跳到缺项页后，脚本直接寻找该页不存在的点赞按钮，随后断言失败。独立判定器正确给出任务未完成；脚本应先通过只读导航回论坛再验证缺项目标不能成功。已交回原单元修正。

外层 stdout 采集未设置 `PYTHONUTF8`，发生解码错误，未生成有效 `test-output.txt`；子进程的 `scripted/run.json` 与各场景原始结果已完整保存，耗时39.273秒。后续正式验收修正采集环境并另建结果目录，不覆盖本次记录。
