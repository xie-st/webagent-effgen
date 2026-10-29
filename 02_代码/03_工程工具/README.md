# 工程入口检查

本目录仅检查项目根入口：新版本能否完整复制、默认版本选择和路径校验是否正常、复制到项目外后是否仍能检查和测试。

新增核心模块、提示、技能或依赖文件后，在这里补充完整复制检查。开发顺序与交接见[开发方案](../../01_文本/06_开发框架/开发方案.md)。

在项目根运行：

```powershell
python -m unittest discover -s "02_代码/03_工程工具/tests" -v
```

每个版本的协议测试保存在其自己的 `tests/`，由 `python run.py test` 或根 `python webagent.py test --version v1` 执行。工程工具不提供 Agent 运行依赖。
