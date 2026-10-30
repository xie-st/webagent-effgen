# 新版客户端兼容：主线程本地验收通过

北京时间2026-10-30 12:58–13:00，主线程实际执行check、冻结副本61/61（包含SDK子进程及24项截图回归）、工程独立复制1/1。运行源码候选随后提交为`9fc1716`；该提交通过Git archive导出后SDK原字节指纹及入口check，输出见[Git导出检查](git-export-check.txt)。完整回归原始输出见[test-output.txt](test-output.txt)，当次源码与指纹见snapshot/harness和run.json。

主线程亲查差异并补修了官方入口对旧step元数据的拒绝及能力降级回归；此前DSH补修port和TaskState的step绑定。旧观察无字段仍保持纯文本行为，原M1模型线程绑定及生命周期通过。

该结果只确认本地兼容。没有在本目录启动官方客户端或批次，真实平台截图链路仍待后续对应运行验证。

通过；具体用例见 test-output.txt。

测试版本：当前版本。验证真实 EffGen v1.3.0 接线、单动作、状态延续、SDK 子进程、日志与结果快照。使用模拟 SDK 响应，未连接平台或运行真实模型，官方成绩未填写。

遥测：telemetry.jsonl；模型调用 17 次（decision=12, correction=5）；调用前拒绝 0 次；运行结束原因：close, close, close, close, close, close, reset, close, close, reset, close。
