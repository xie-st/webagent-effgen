# 当前版本：M2短期修补

默认路径：当前网页 → 一次EffGen决策 → 局部操作保护 → 一个官方动作 → 下一观察读回。无独立verify模型、无通用目标正则抽取、无模型证明JSON。M3暂停。

本轮状态及验证限制见根目录[M2短期修补交付](../../../M2短期修补交付.md)。冻结c82551e官方8项3/8；循环成本补修后88项回归通过，但未官方复测。

## 从仓库根目录启动

使用已按本目录`requirements.lock`安装依赖的Python 3.11+解释器；EffGen固定1.3.0。

```powershell
python webagent.py check
python webagent.py test
python webagent.py connect --connection-file '实际连接文件绝对路径'
```

本机专用环境位于修补工作树`.local/m2-lock-venv/Scripts/python.exe`。连接配置和环境不进Git。旧版本加`--version v1`；完整版本内也可直接运行`python run.py check/test/connect`。

## 动作与输入语义

决策返回`{"action":"完整动作","memory":"可选短记忆"}`。原始官方动作语法保持不变。

- `type`默认replace，程序跨回调执行聚焦、全选、Backspace清空、输入；下一观察读回完整值。每个回调仅返回一个动作，元素ID逐步重新绑定；不依赖type保留选区。
- 追加时显式返回`{"action":"type [当前ID] [新增文字] [0]","input_mode":"append"}`。程序先聚焦并移到末尾，基线＋增量作为全文期望；同一已观察到的追加不重复执行。
- 写入后提交前检查编辑全文，提交后查业务结果。输入框正确、保存提示或截图存在均不单独证明持久化。
- 点赞/订阅等状态按同一对象读回，已生效不得重复撤销；对象缺失不拿其他对象顶替。
- 未决业务提交期间阻止其他写入及可能覆盖待确认状态的草稿输入，允许只读查询。确定效果未生效可有限重试，未知结果不重发。
- 普通步骤不另起模型裁判；格式错误最多一次纠错。连续3次无变化观察或本地40步上限以Incomplete退出，任务绝对截止不续期，临近截止预留6秒。

低层注入的`decision_port`保留官方原始动作语义，用于协议测试；默认生产`EffGenPolicy`执行上述输入模式。`input_mode`只对type有效。

## 模块

| 文件 | 职责 |
| --- | --- |
| `my_agent.py`、`agent_logic.py` | 官方生命周期与兼容入口，使用同一Runtime |
| `web_agent/runtime.py` | 一次决策、至多一次纠错、跨回调输入续执行与预算 |
| `web_agent/operations.py` | 输入/状态/提交的局部读回、未决写入与重复操作保护 |
| `web_agent/ax.py` | 当前AX的字段、值、控件状态与对象定位；歧义不猜 |
| `web_agent/state.py` | 记忆、焦点、未决动作、最新字段草稿、已确认操作与截止 |
| `web_agent/policy.py`、`model_port.py` | EffGen单Agent调用、SDK统一模型适配，记录实际调用 |
| `web_agent/page_sources.py` | 按需DOM/HTML参考，不能将DOM编号当动作ID |
| `web_agent/screenshots.py` | 当前run/step/URL绑定的截图下载与校验 |
| `sdk/`、`run.py` | 官方原件/指纹、环境检查、冻结快照和运行结果 |

旧`verify.py/recover.py`及仅验证其证明协议的测试已从当前版本移除；历史提交与保存版本保留。操作反例在`tests/test_m2_operations.py`；其余模型接线、截止、状态隔离、SDK与截图测试继续保留。

## 观察和证据边界

执行使用当前AX元素ID；DOM/HTML仅是参考，不保证实时表单属性或后端状态。统一模型接收文本，不自动具备截图视觉理解。

普通语义要求仍由同一Agent结合原任务判断；本版本不是通用任务完成证明器。当前局部提交读回可能对多段正文、已存在相同值、缺少可读业务结果保持unknown，不能由此宣布任务已完成。

`run.py test/connect`生成独立代码快照、会话和遥测。官方成绩从平台下载放本次`raw/`，结果写`result.md`，批次编号填`run.json.platform_run_ids`。真实模型、脚本网页、离线协议分别报告。
