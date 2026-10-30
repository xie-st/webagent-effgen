# 工程检查

通过；具体用例见 test-output.txt。

测试版本：当前版本。验证版本定位、导入、SDK 完整性、单步协议、状态隔离与结果快照。使用模拟模型响应，未连接平台或运行真实模型，官方成绩未填写。

## M1a 实施前主线程核验

2026-10-30 09:03（北京时间），Codex 亲自运行 `python webagent.py check` 与 `python webagent.py test`。check 通过，离线 21/21 通过；代码提交 `ecee1e5`，当次测试前工作区干净，完整代码指纹和快照见 run.json。此时仍是 M0 baseline，不能用本次结果宣称 EffGen 已接通。

主线程另核对实际下载的 PyPI EffGen 1.3.0 wheel：SHA-256 `474a7fcf952f87995c19cfe261167d713ace9f9d8fc0773d134c42ea49d9d5e5`，与 PyPI 版本元数据一致，Requires-Python >=3.11；M1a 环境 Python 3.12.9。安装与实际运行验收待实现交付。

评测台主页与公开管理 API 可达，SDK 连接配置目标与预期平台一致。用户提供账号登录返回 HTTP 401（用户名或密码错误），已请求核对；未创建新连接、未提交批次、未运行比赛任务。既有连接文件与凭据保持本机，不进入 Git。
