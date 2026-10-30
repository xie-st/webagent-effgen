# M2 本地故障环境：主线程验收通过

北京时间2026-10-30 13:04–13:05，从本地环境冻结Python源码、独立判定器、故障计划，指纹见[source-sha256.json](source-sha256.json)，快照留在本目录snapshot。使用本地环境原锁定`.venv`（Flask、Playwright与Chromium），没有修改EffGen环境。

- `python -m unittest discover -s snapshot -p test_m2*.py -v`：24/24通过，见[原始输出](unit-output.txt)。新增实际浏览器注入验证：actor收不到grade/故障计划/写次数等后台真值；多步共用绝对deadline；混合已知/未知模型调用量保持null。
- 冻结`m2_acceptance.py --suite scripted --out scripted`：10/10符合预期，见[逐项结果](scripted/summary.md)和[原始输出](scripted-output.txt)。7项应完成、3项应失败，独立判定与实际业务状态/写次数一致。
- 既有smoke 11/11及runner-smoke 3步profile均由主线程亲跑通过，输出见[smoke](smoke-output.txt)、[runner](runner-smoke-output.txt)；新结果分别位于`environment/20261030T050716_203176Z`、`local/20261030T050716_749000Z`。

主线程亲查并修复了默认证据路径的Path拼接错误、代码目录归档、未知调用量低报，并补齐传给决策器的任务预算。缺项页返回论坛后再点赞的脚本修正已核实。旧9/10失败记录保留，不覆盖。

这是脚本浏览器环境检查，真实模型调用为0；尚不代表M2 Runtime或官方任务验收。后续Runtime联调另建证据。
