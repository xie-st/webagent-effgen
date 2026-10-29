# -*- coding: utf-8 -*-
"""生成上传版：图片本地相对路径 -> arXiv 绝对 URL，并生成索引 README。"""
import re
from pathlib import Path

BASE_DIR = Path(r"D:\Dwen\Alpha26fall\华为2026Hackathon_WebAgent\论文库")
MD_DIR = BASE_DIR / "30篇全文md"
UPLOAD_DIR = BASE_DIR / "_upload"
UPLOAD_DIR.mkdir(exist_ok=True)

PAPERS = [
    (1, "MACU", "Multi-Agent Computer Use", "任务规划", "2606.01533v1"),
    (2, "FCPAgent", "Falsifiable Commitment Planning for Self-Correcting Web Agents", "任务规划", "2607.24167v1"),
    (3, "Verifiers", "The Art of Building Verifiers for Computer Use Agents", "结果检验", "2604.06240v1"),
    (4, "ContractSkill", "ContractSkill: Repairable Contract-Based Skills for Multimodal Web Agents", "动作执行", "2603.20340v3"),
    (5, "AgentJIT", "Agent JIT Compilation for Latency-Optimizing Web Agent Planning and Scheduling", "并发调度与等待", "2605.21470v2"),
    (6, "BudgetConstrained", "Are Online Skill and Memory Modules Always Worth Their Tokens?", "模型调用效率", "2606.15017v2"),
    (7, "Region4Web", "Region4Web: Rethinking Observation Space Granularity for Web Agents", "页面观察", "2605.07134v1"),
    (8, "WebFovea", "WebFovea: Reliable Round Trips for Vision-Based Web Agents on Live Websites", "动作执行", "2610.03036v2"),
    (9, "ALTK", "Agent Lifecycle Toolkit (ALTK)", "提示词与钩子", "2603.15473v2"),
    (10, "PoS", "Beyond Memory: Harnessing Long-Horizon Agents with Explicit Belief States", "上下文管理", "2610.01415v1"),
    (11, "StressWeb", "StressWeb: A Diagnostic Benchmark for Web Agent Robustness", "Benchmark", "2604.16385v1"),
    (12, "ParaGUIBench", "Beyond Sequential Interaction: Benchmarking Parallel Execution for GUI Agents", "Benchmark", "2607.22689v1"),
    (13, "Skim", "Skim: Speculative Execution for Fast and Efficient Web Agents", "动作效率", "2605.16565v2"),
    (14, "WebChallenger", "WebChallenger: A Reliable and Efficient Generalist Web Agent", "页面观察", "2606.10423"),
    (15, "Prune4Web", "Prune4Web: DOM Tree Pruning Programming for Web Agent", "页面观察", "2511.21398v1"),
    (16, "ObservationReduction", "Revisiting Observation Reduction for Web Agents", "页面观察", "2605.29397v1"),
    (17, "CUADebug", "CUADebug: Diagnosing and Repairing Computer-Use Agent Failures", "失败处理", "2608.02643v2"),
    (18, "ActionEngine", "ActionEngine: From Reactive to Programmatic GUI Agents via State Machine Memory", "任务规划", "2602.20502v1"),
    (19, "M2_DualMemory", "M2: Dual-Memory Augmentation for Long-Horizon Web Agents", "上下文管理", "2603.00503v1"),
    (20, "ReadMoreThinkMore", "Read More, Think More: Revisiting Observation Reduction for Web Agents", "页面观察", "2604.01535v1"),
    (21, "AgentProg", "AgentProg: Program-Guided Context Management for Long-Horizon GUI Agents", "上下文管理", "2512.10371v2"),
    (22, "CUA-Skill", "CUA-Skill: Develop Skills for Computer Using Agent", "动作效率", "2601.21123v2"),
    (23, "PRISM", "Beyond Prompts: Measuring and Optimizing LLM Tool-Agent Harnesses", "提示词与钩子", "2609.05736v1"),
    (24, "MonitoringWebAgents", "Monitoring Web Agents Without Internal Signals", "结果检验", "2609.02057"),
    (25, "ReTRACE", "Lost in Recovery: Goal-Oriented Action Replay of Computer-Use Agents", "失败处理", "2610.27954v1"),
    (26, "CATTS", "Agentic Test-Time Scaling for WebAgents", "模型调用效率", "2602.12276"),
    (27, "STITCH", "Composing Task-specific Agent Harnesses at Test Time with Reusable Primitives", "提示词与钩子", "2609.38912v1"),
    (28, "AreWeDoneYet", "Are We Done Yet?: A Vision-Based Judge for Task Completion", "结果检验", "2511.20067v1"),
    (29, "SCOPE", "SCOPE: Prompt Evolution for Enhancing Agent Effectiveness", "提示词与钩子", "2512.15374v2"),
    (30, "ShopGym", "ShopGym: Realistic Simulation and Scalable Benchmarking of E-Commerce Web Agents", "Benchmark", "2605.16116v1"),
]

IMG_RE = re.compile(r"\]\(images/\d+_[^/]+/([^)]+)\)")

for idx, short, title, domain, arxiv_id in PAPERS:
    src = MD_DIR / f"{idx:02d}_{short}.md"
    text = src.read_text(encoding="utf-8")
    base = f"https://arxiv.org/html/{arxiv_id}"
    text = IMG_RE.sub(lambda m: f"]({base}/{m.group(1)})", text)
    (UPLOAD_DIR / f"{idx:02d}_{short}.md").write_text(text, encoding="utf-8", newline="\n")
    print(f"[{idx:02d}] {short}: 上传版就绪")

# 生成索引 README
rows = []
for idx, short, title, domain, arxiv_id in PAPERS:
    url = f"https://arxiv.org/html/{arxiv_id}"
    rows.append(f"| {idx:02d} | [{title}]({url}) | {domain} | `{idx:02d}_{short}.md` |")

readme = f"""# WebAgent 项目论文库（30 篇）

> 生成时间：2026-10-29 ｜ 源清单：《WebAgent项目最终30篇论文.md》
> 转换方式：arXiv 官方 HTML（LaTeXML）→ Markdown；公式为原始 LaTeX（$...$），图片链接指向 arXiv 原图。

## 使用说明

- 每篇一个文件，文件名 `{{编号}}_{{简称}}.md`，与本表编号一一对应
- 公式为 `$...$` / `$$...$$` LaTeX 源码，在支持 LaTeX 渲染的阅读器中显示最佳
- 云端版图片走 arXiv 原始链接，需联网查看

## 论文索引

| # | 论文 | 领域 | 文件 |
| --- | --- | --- | --- |
{chr(10).join(rows)}
"""
(UPLOAD_DIR / "README.md").write_text(readme, encoding="utf-8", newline="\n")
(BASE_DIR / "README.md").write_text(readme, encoding="utf-8", newline="\n")
print("索引 README 已生成")
