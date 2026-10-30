# M2短期修补接续验证

2026-10-31，北京时间。运行代码：接续DSH `3dabc09`工作树后补修，最终提交见本报告对应Git记录。M3暂停。

## 当前可确认结果

- `tests/test_m2_operations.py`23/23，通过；脚本/协议测试，无真实模型调用。
- 最终原132包锁环境Python3.12.7/EffGen1.3.0：根`check`与SDK指纹通过，完整87/87，22.901秒；[运行摘要](../../runs/20261030T163127_952243Z_当前版本_15c86c14/result.md)、[指纹与环境记录](../../runs/20261030T163127_952243Z_当前版本_15c86c14/run.json)。原始输出与源码快照留本机。
- 正常环境原快照64项中1失败1错误；预算测试与依赖问题已在最终专用环境检查消除，早期失败原件保留。
- 沙箱完整回归86项受EffGen数据库与临时目录访问限制，不计为策略成绩；详细输出和代码快照保存在本机runs目录。
- 真实Edge受控探针先验证替换保存，再发现追加光标问题；已补修，重跑被拒。未取得最终三项全通过结果。
- 官方测试：未启动。用户明确其他模型正在使用平台，先同步GitHub；不得将历史官方结果转记本版本。

## 运行入口

工作树：`D:\HackathonWebAgent\webagent-effgen-m2-short-fix`。

专项命令：将当前版本及其sdk加入PYTHONPATH，使用可用解释器运行`python -m unittest discover -s 02_代码/01_harness/当前版本/tests -p test_m2_operations.py -q`。

完整回归：使用按requirements.lock建立的解释器，从根目录运行`python webagent.py check`及`python webagent.py test`。真实模型和官方分数另行归档。
