# M1a 主线程验收：通过

验收时间：2026-10-30 10:48:25（北京时间）；负责人：Codex。独立复核：DSH ds-flash，job14；原始意见见review.md。

| 交付/验收要求 | 亲验证据 |
|---|---|
| 真实EffGen1.3.0、公开AgentConfig/Agent.run/BaseModel、单Agent空工具及关闭特性 | 已安装真实包，固定132包锁；两环境导入与pip check通过；37项回归中的接线测试 |
| 统一SDK模型端口、单请求单动作、有效普通决策恰好1调用 | 37项回归及独立SDK AgentProcess测试；仅字符串role/content消息，无模型/采样参数转发 |
| TaskState跨观察memory、校验后合并、reset/close隔离 | M0保留回归及新增生命周期测试 |
| 调用开始/结束/失败/拒绝、序号/request_id、未知用量null、stop/deadline真实结束 | 5项额外日志探针全过；真实框架内部重试的所有实际调用均记录 |
| SDK子进程绑定、版本独立运行 | 实际AgentProcess绑定HTTP假SDK；工程独立复制check/test 1/1通过 |
| 共用任务时限、不续期 | 独立假时钟探针：1000/1005/1011三次观察deadline均1010，实际SDK仅前2次，结束deadline |
| 代码与路线图复核 | 初次job11发现已裁定修正；最终差异job14确认销项，无新增阻塞 |

主线程命令：`.local/m1a-lock-venv/Scripts/python.exe webagent.py check`、`webagent.py test`（37/37）、`-m unittest discover -s 02_代码/03_工程工具/tests -v`（1/1），完整测试输出见test-output.txt。五项探针程序和结果、固定截止探针结果保留本机raw/；本目录snapshot/harness与run.json保存当次代码及指纹。

运行代码与当前候选逐文件哈希一致；测试后仅README移除易过期的固定测试数量，并在父级harness说明补充固定解释器要求，没有改运行代码。SDK与v1相对M0无改动；check原件哈希通过。本机主解释器`.local/m1a-lock-venv/Scripts/python.exe`，Python3.12.9、EffGen1.3.0；独立重建成功的锁定依赖供M1b沿用。

这是离线工程验收，使用真实EffGen+假SDK，未写入官方成绩。M1a通过不等于M1结案；M1b须另行冻结并顺序运行官方可用套件保存平台原件，之后才能进入M2。

## 最终证据补齐

2026-10-30 11:39:06（北京时间）：本轮主线程在相同冻结运行代码上复跑37项回归、SDK子进程与工程独立复制，各项通过；[补齐的测试输出、源码/原件审计和独立复核](../20261030T032427_203488Z_当前版本_fbbf1014/result.md)。原文只写通过而缺少最终代码对应文件链接的问题已补齐，M1a/M1b均通过，M1已结案。
