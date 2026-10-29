# -*- coding: utf-8 -*-
"""最终验证：effgen Agent + 百炼 Qwen3.6-35B-A3B 完整链路。

用法:  先 source ~/.bashrc，再运行本脚本
"""
import os
import sys

KEY = os.environ.get("DASHSCOPE_API_KEY")
BASE = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
MODEL = os.environ.get("DASHSCOPE_MODEL", "qwen3.6-35b-a3b")

if not KEY:
    sys.exit("没有 DASHSCOPE_API_KEY。先执行: source ~/.bashrc")

from effgen.models import OpenAIAdapter
from effgen import Agent
from effgen.core.agent import AgentConfig
from effgen.tools.builtin import Calculator

# ---------- 1. 适配器直连百炼 ----------
print("== 1/2 OpenAIAdapter 直连百炼 ==")
model = OpenAIAdapter(
    model_name=MODEL,
    api_key=KEY,
    base_url=BASE,
    timeout=120,
)
model.load()
res = model.generate("只回复两个字：好的")
out = getattr(res, "text", None) or getattr(res, "output", None) or str(res)
print("[OK] generate 返回:", str(out)[:100].replace("\n", " "))

# ---------- 2. 完整 Agent（带计算器工具的 ReAct 循环）----------
print()
print("== 2/2 Agent + 工具 完整链路 ==")
config = AgentConfig(
    name="bailian_agent",
    model=model,
    tools=[Calculator()],
    system_prompt="你是一个数学助手，遇到计算必须使用工具。",
)
agent = Agent(config=config)
result = agent.run("计算 1234 乘以 5678 等于多少？")
print("[OK] Agent 输出:", str(result.output)[:200].replace("\n", " "))
print()
print("=== 全部通过：effgen + 百炼 Qwen3.6-35B-A3B 完整可用 ===")
