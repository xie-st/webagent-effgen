# 工程检查

主线程亲跑：101/101通过，固定环境check通过。补修字段/对象证据范围、最多3页可核对历史、未知同指纹先只读查询、资源导航分类；两个原独立误判反例现均抛出GoalIncompleteError。末次源码见snapshot/harness及run.json指纹。

同一实际代码的Runtime+Chromium联调14/14通过，见`../../local/20261030T090629_384715Z_m2_runtime_bridge/summary.md`；辅助5项通过。脚本policy与核验桩无真实模型调用，不能替代后续官方成绩。

通过；具体用例见 test-output.txt。

测试版本：当前版本。验证真实 EffGen v1.3.0 接线、单动作、状态延续、SDK 子进程、日志与结果快照。使用模拟 SDK 响应，未连接平台或运行真实模型，官方成绩未填写。

遥测：telemetry.jsonl；模型调用 17 次（decision=12, correction=5）；调用前拒绝 0 次；运行结束原因：close, close, close, close, close, close, reset, close, close, reset, close。
