# -*- coding: utf-8 -*-
"""验证百炼 Qwen3.6-35B-A3B 连通 + effgen OpenAI 适配器可用性。

第 1 步：直连百炼（openai SDK，验证 key 和模型名）
第 2 步：探测 effgen 的 OpenAIAdapter（模型名前缀不匹配 gpt-*，
         load_model 自动检测会把 qwen3.6-35b-a3b 误判为本地模型，
         所以必须直接实例化适配器）
"""
import importlib
import inspect
import os
import sys

KEY = os.environ.get("DASHSCOPE_API_KEY")
BASE = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
MODELS = [os.environ.get("DASHSCOPE_MODEL", "qwen3.6-35b-a3b"), "qwen3.6-flash"]

if not KEY:
    sys.exit("没有 DASHSCOPE_API_KEY。先执行: source ~/.bashrc")

# ---------- 第 1 步 ----------
print("== 第 1 步：直连百炼（验证 key 和模型名）==")
from openai import OpenAI

client = OpenAI(api_key=KEY, base_url=BASE)
ok_model = None
for m in MODELS:
    try:
        r = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "用一句话介绍你自己"}],
            max_tokens=2000,
        )
        msg = r.choices[0].message
        text = (msg.content or getattr(msg, "reasoning_content", "") or "").strip()
        print(f"[OK] 模型 {m} 连通成功")
        print("     回复:", (text or "(空，可能被思考模式吃掉了)")[:120].replace("\n", " "))
        ok_model = m
        break
    except Exception as e:
        print(f"[失败] {m}: {type(e).__name__}: {str(e)[:200]}")

if not ok_model:
    sys.exit("两个模型名都失败——检查 key 是否有效、百炼服务是否开通")

# ---------- 第 2 步 ----------
print()
print("== 第 2 步：effgen 的 OpenAI 适配器 ==")
adapter = None
for mod, attr in [
    ("effgen.models.adapters", "OpenAIAdapter"),
    ("effgen.models.api_adapters", "OpenAIAdapter"),
    ("effgen.models", "OpenAIAdapter"),
]:
    try:
        adapter = getattr(importlib.import_module(mod), attr)
        print(f"[OK] 找到 OpenAIAdapter: {mod}.{attr}")
        break
    except Exception:
        pass

if adapter is None:
    import effgen.models as em
    print("[未找到] effgen.models 下可见:", [x for x in dir(em) if not x.startswith("_")])
    sys.exit("把上面这行列名发给我，我来定位适配器的正确位置。")

sig = inspect.signature(adapter.__init__)
print("     构造参数:", sig)

# 按签名探测式实例化；base_url 若不存在则靠 OPENAI_BASE_URL 环境变量生效
kw = {}
params = sig.parameters
if "model" in params:
    kw["model"] = ok_model
if "model_name" in params:
    kw["model_name"] = ok_model
if "api_key" in params:
    kw["api_key"] = KEY
if "base_url" in params:
    kw["base_url"] = BASE

try:
    inst = adapter(**kw)
    print("[OK] 实例化成功")
except TypeError as e:
    print(f"[实例化失败] {e}")
    sys.exit("把『构造参数 + 这行报错』发给我，我来写正确的调用代码。")

try:
    res = inst.generate("只回复两个字：好的")
    out = getattr(res, "text", None) or getattr(res, "output", None) or str(res)
    print("     generate 返回:", str(out)[:150].replace("\n", " "))
    print()
    print("=== 全部通过：effgen + 百炼 Qwen3.6-35B-A3B 配置完成 ===")
except Exception as e:
    print(f"[generate 失败] {type(e).__name__}: {str(e)[:300]}")
    print("实例化没问题但调用方式可能不同——把这行报错发给我即可。")
