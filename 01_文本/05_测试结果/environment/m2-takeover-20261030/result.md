# 本机接手 M2：写保护与纠错预算

2026-10-30，北京时间。基线：远端交接 `68f0892`（运行代码 `d6d26df`）；本地分支 `codex/m2-takeover-review`。仅修改当前版本，不改 SDK、大版本或运行中的另一台机器副本。

## 发现与修复

1. **危险查询漏判**：路径危险动词与查询 action/do/op/operation/cmd 的判断列表不一致；`action=cancel/checkout/vote/like/purchase/addcart` 可被误当只读，unknown pending 下仍被允许。现在查询操作复用路径危险分类，并保留 submit 等原有判断；普通 `q=delete` 和 `action=view` 继续允许。
2. **菜单元数据覆盖危险操作**：带 `hasPopup: menu` 的 Delete 按钮或指向 `/delete/1` 的 More 链接会提前返回 read。现在明确危险名称/URL 优先，Account 菜单与普通 Tab 仍为导航。
3. **纠错没有次数边界**：每次不同的无效动作可持续触发模型纠错，直到耗尽任务截止。现在每观察最多两次纠错，重复答案仍提前结束；随后返回原有轮换观察恢复动作，经 `_accept_action` 统一守卫与登记。不限制任务总步数，不替代绝对 deadline，也不声称整个任务最多三次模型调用（核验等另计）。

新增测试先在原实现上运行，产生 33 个失败断言/子测试；修复后 6/6 通过（其中一个参数化方法覆盖 9 个操作 × 5 个查询键）。原独立复核 4/4、投票证据 11/11 同样通过，总计 **21/21**。已运行核心模块语法编译与 `git diff --check`。

## 证据与限度

运行环境：本机 Python 3.12.7（`D:\ProgramData\anaconda3\python.exe`），没有 EffGen 包及原 132 包锁定环境。本轮测试直接使用实际 Runtime/recover/verify 与确定性 policy，不伪造 EffGen 或平台；没有真实模型调用，也没有浏览器实测。

命令（项目根，PYTHONPATH 指向当前版本）：

```powershell
& D:\ProgramData\anaconda3\python.exe -m unittest discover -s 02_代码/01_harness/当前版本/tests -p 'test_m2_*.py' -v
```

[测试输出](test-output.txt)与[源码 SHA-256](source-sha256.json)对应本轮修改。历史 123/123 只适用于原冻结代码，不冒充本轮完整回归。

后续需要在锁定环境跑完整回归，再取回已提交的第二轮论坛成绩与日志、顺序验证电商 2 项，并对本轮补修独立复核。已提交实验仍使用旧冻结代码，不能据其结果评估本轮修复。模型服务/连接配置目前未迁移到本机，不重复提交批次、不启动同连接第二客户端。

M2 仍未结案；用户已取消自动接续 M3，本机只推进 M2。以上代码是经专项验证的候选改进，尚未合入 main 或推送。
