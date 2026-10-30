# M1 主线程最终验收：通过

验收时间：2026-10-30 11:39:06（北京时间）；固定解释器`.local/m1a-lock-venv/Scripts/python.exe`，Python3.12.9、真实EffGen1.3.0与132包锁。当前运行代码未改。

- check：通过，SDK原件哈希与环境检查通过。
- 完整回归37/37：通过，输出见[test-output.txt](test-output.txt)，包含真实EffGen＋假SDK、状态隔离、调用/拒绝日志、纠错、截止语义和SDK子进程绑定。
- 最终代码SDK子进程专项1/1：通过，见[sdk-child-test-output.txt](sdk-child-test-output.txt)。
- 工程独立复制check/test 1/1：通过，见[independent-test-output.txt](independent-test-output.txt)。
- 当前30个源码/依赖文件与M1a/M1b冻结快照一致；23份平台原件及全部26次实际调用复核通过，见[audit_m1.py](audit_m1.py)与[审计结果](m1-acceptance-audit.json)。
- 独立代码及证据复核、证据缺链补齐与主线程裁定见[review.md](review.md)。

M1a和M1b均已验收，官方成绩仍来自[既有原件基线](../20261030T025026_355479Z_当前版本_66091f22/result.md)：3/4、75%。本目录新增运行属于离线复验与原件审计，没有重新执行官方批次；snapshot/harness与run.json保存本次实际代码和指纹。