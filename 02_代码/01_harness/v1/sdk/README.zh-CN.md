# WebArena 选手接入：300 秒、统一模型

## 十分钟开始

要求 Python 3.10+。下载并解压客户端，在在线平台「Agent 连接」创建连接，把 `agent-connection.json` 放到能直接看到 `third_party_agent/` 的目录。连接文件是平台令牌，不能提交或分享。

```sh
python3 -m third_party_agent connect --connection-file agent-connection.json --agent my_agent:MyAgent
```

看到 `Agent connected` 后保持终端运行，网页选择在线 Agent 开始整批评测。包内 `agent_logic.py` 是可运行 baseline，直接使用平台模型；无需模型 SDK、模型 API key 或本机浏览器。

## 只改算法入口

```python
from third_party_agent import model

def decide(*, task, observation, history, action_history, state):
    messages = build_prompt(task, observation, state)
    reply = model.generate(messages)
    return parse_action(reply.text)
```

`build_prompt` 和 `parse_action` 表示你的算法；可直接参考包内 baseline。`messages` 是非空列表，每项只含 `role` 和字符串 `content`，role 为 system/user/assistant。总输入 JSON 最多 1 MiB，最多 256 条消息。`generate` 只接受 messages，不接受模型名、temperature、输出上限、工具参数、服务地址或密钥。模型及推理参数由服务器固定；接口只返回 `.text` 和平台 `.request_id`，不返回供应商模型标识。

每任务最多一个模型调用同时执行；调用供应商的网络等待上限为 90 秒且不超过任务剩余时间。调用失败不自动重新请求供应商，避免重复计费。需要重试可由算法在剩余预算内再次调用。平台记录 token 用量、按管理员定价计算费用，usage 或定价缺失会显示费用待核对。

可在自己的虚拟环境中安装算法依赖。`model.generate` 在当前 Agent 调用线程中使用任务绑定；自建线程须显式传播 contextvars 上下文，且不能突破单任务并发限制。禁止通过 import 阶段启动常驻程序，multiprocessing 入口须有 `if __name__ == '__main__':` 保护。SDK 每任务使用独立 spawn 子进程；关闭/超时后结束进程，避免阻塞后续任务。

## 输入和动作

- task：当前任务文字，不含隐藏判分条件。
- observation：type=`accessibility_tree`、url、text。text 为当前视口带编号的页面树；不含截图或完整 DOM。
- history：先前观察和动作；action_history：文字动作描述。
- state：仅在本项任务内复用的本地字典，新任务清空。

URL 的 `127.0.0.1:动态端口` 指服务器内部网站，不可从选手本机直接访问。通过返回动作让服务器操作。同一页面编号会变化，必须使用本次观察里的真实编号。

| 动作 | 格式 |
|---|---|
| 点击 | `click [编号]` |
| 输入 | `type [编号] [文字] [0或1]`；1 随后回车 |
| 按键 | `press [Ctrl+A]` |
| 滚动 | `scroll [down]` / `scroll [up]` |
| 导航 | `goto [当前实例内的网址]` |
| 返回/前进 | `go_back` / `go_forward` |
| 完成 | `stop [答案或说明]` |

一次只返回一个动作字符串或 `{"action":"..."}`。输入可能追加，覆盖前须点击并全选。不要自动重放可能已经生效的发帖或提交动作。`reset` 不一定含任务文字；第一份 step 才有完整 task。

## 时间和判分

浏览器与登录准备完成后，平台开始每项固定 300 秒执行计时；模型等待、网络往返、算法计算和浏览器动作均计入，不限制步数，不因重复动作或三次解析错误提前停止。主动 stop 或到期后撤销执行权限，再按网站最终状态及任务所需答案判分。截止之后的动作和模型结果不会继续驱动网页；已产生或迟到的供应商用量仍归属原任务。临近截止的在途网站请求可能完成，不能承诺撤销已经提交的业务操作。

环境准备有独立 600 秒故障保护；最终判分和清理有截止后 60 秒保护，不占执行预算。平台是 POSIX worker 部署；选手客户端支持 Windows/macOS/Linux。

运行记录显示 score 和 finish_reason（stop/deadline/error），以及模型调用、token 和费用统计。每组十项，成功率=通过项数/10。执行截止不是直接判零；最终判分出错仍为未评分。整批无额外总时限。

旧版 `WEBARENA_AGENT_WAIT`、本地模型 .env、24 步规则不再适用，请重新下载客户端。同一连接文件只运行一个客户端。停止可在网页取消整批或按 Ctrl+C。

本地执行模式无法从技术上阻止自带模型或外部网络；正式比赛应配套规则审计，需要强约束时使用平台受控容器。
