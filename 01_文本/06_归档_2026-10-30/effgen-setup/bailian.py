# -*- coding: utf-8 -*-
"""bailian.py — 百炼 Qwen3.6-35B-A3B 的 effgen 快捷封装。

用法（Git Bash，环境变量已在 ~/.bashrc 里）：
    from bailian import make_agent
    agent = make_agent()
    print(agent.run("你的问题").output)
"""
import os

from effgen import Agent
from effgen.core.agent import AgentConfig
from effgen.models import OpenAIAdapter

_MODEL = os.environ.get("DASHSCOPE_MODEL", "qwen3.6-35b-a3b")
_KEY = os.environ.get("DASHSCOPE_API_KEY")
_BASE = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")


def make_model(model_name: str | None = None) -> OpenAIAdapter:
    """百炼模型实例（先 load 再用）。可传 model_name 换别的百炼模型。"""
    if not _KEY:
        raise RuntimeError("没有 DASHSCOPE_API_KEY，先执行: source ~/.bashrc")
    m = OpenAIAdapter(
        model_name=model_name or _MODEL,
        api_key=_KEY,
        base_url=_BASE,
        timeout=120,
    )
    m.load()
    return m


def make_agent(
    tools: list | None = None,
    system_prompt: str = "你是一个乐于助人的中文助手。",
    name: str = "bailian_agent",
    model_name: str | None = None,
    memory: bool = False,
) -> Agent:
    """起一个连着百炼的 effgen Agent。tools 传 effgen 工具实例列表。"""
    return Agent(
        config=AgentConfig(
            name=name,
            model=make_model(model_name),
            tools=tools or [],
            system_prompt=system_prompt,
            enable_memory=memory,
        )
    )
