# WebAgent 项目最终 33 篇论文

2026-10-30 · 12 个维度 · 按项目重要程度排序。综合质量、实验、影响力、适配性与代码，优先成功率和容错，再看并行、耗时与成本；适配统一 Qwen3.6-35B-A3B、可访问性树及单动作接口。

筛选依据：[主要参考](调研记录/WebAgent_20261029/独立筛选/每维度三篇.md) · [辅助参考](调研记录/WebAgent_20261029/每维度三篇_言语独立筛选.html) · [Skill 补充筛选](调研记录/WebAgent_20261029/Skill筛选任务记录.md)。

## 最关键的 5 篇

| 优先级 | 论文 | 重点 |
|---|---|---|
| 1 | [MACU](https://arxiv.org/html/2606.01533v1) | 并行调度框架 |
| 2 | [FCPAgent](https://arxiv.org/html/2607.24167v1) | 检查时机与局部修复 |
| 3 | [The Art of Building Verifiers](https://arxiv.org/html/2604.06240v1) | 完成判定 |
| 4 | [ContractSkill](https://arxiv.org/html/2603.20340v3) | 可验证、可修复的动作技能 |
| 5 | [Agent JIT Compilation](https://arxiv.org/html/2605.21470v2) | 执行计划与耗时优化 |

## 01. [Multi-Agent Computer Use](https://arxiv.org/html/2606.01533v1)

**任务规划｜MACU** · 代码：[代码](https://github.com/kohjingyu/multi-agent-computer-use)。

用动态任务依赖图组织并行执行、传递证据和持续重规划，搭建真实网站多 Tab 调度框架。

## 02. [Falsifiable Commitment Planning for Self-Correcting Web Agents](https://arxiv.org/html/2607.24167v1)

**任务规划｜FCPAgent** · 代码：未定位到公开实现。

为子目标明确成功与失败证据，按需检查并局部修复，及时纠正任务偏离。

## 03. [The Art of Building Verifiers for Computer Use Agents](https://arxiv.org/html/2604.06240v1)

**结果检验** · 代码：[Fara 验证器](https://github.com/microsoft/fara)，入口 `webeval/scripts/verify_trajectories.py`。

分开检查执行过程与最终结果，用页面证据确认完成，减少误报成功。

## 04. [ContractSkill: Repairable Contract-Based Skills for Multimodal Web Agents](https://arxiv.org/html/2603.20340v3)

**动作执行** · 代码：[代码](https://github.com/underfitting-lu/contractskill)。

将网页流程封装为带前后置条件的技能，定位并修补错误步骤，保留已完成操作。

## 05. [Agent JIT Compilation for Latency-Optimizing Web Agent Planning and Scheduling](https://arxiv.org/html/2605.21470v2)

**并发调度与等待** · 代码：[关联框架 A1](https://github.com/stanford-mast/a1)；完整实验代码未确认。

结合动作契约和延迟估计选择执行计划与并行策略，减少关键路径等待。

## 06. [Are Online Skill and Memory Modules Always Worth Their Tokens? A Budget-Constrained Study of Web Agents](https://arxiv.org/html/2606.15017v2)

**模型调用效率** · 代码：[实验代码](https://github.com/ServiceNow/budget-constrained-web-agents)。

在统一 token 预算下比较基础代理与附加模块，判断规划、记忆和技能是否值得启用。

## 07. [Region4Web: Rethinking Observation Space Granularity for Web Agents](https://arxiv.org/html/2605.07134v1)

**页面观察与信息提取** · 代码：[代码](https://github.com/kwondu/region4web)。

按功能区域组织可访问性树并维护摘要，减少当前子任务的无关输入。

## 08. [WebFovea: When the Model Is Right but the Click Is Wrong — Reliable Round Trips for Vision-Based Web Agents on Live Websites](https://arxiv.org/html/2610.03036v2)

**动作执行** · 代码：[代码](https://github.com/jianganghan/WebFovea)。

检查动作解析、执行、回执和观察链路，定位真实网站中决策正确却操作失败的问题。

## 09. [Agent Lifecycle Toolkit (ALTK): Reusable Middleware Components for Robust AI Agents](https://arxiv.org/html/2603.15473v2)

**提示词与钩子** · 代码：[altk-boost](https://github.com/AgentToolkit/altk-boost)。

在模型与工具调用前后设置钩子，统一参数校验、静默错误检查和修复反馈。

## 10. [Beyond Memory: Harnessing Long-Horizon Agents with Explicit Belief States](https://arxiv.org/html/2610.01415v1)

**上下文管理｜PoS** · 代码：[代码](https://github.com/luoyu100/PoS)。

维护当前状态、未满足要求和执行进度，发现无进展循环并支持恢复。

## 11. [StressWeb: A Diagnostic Benchmark for Web Agent Robustness under Realistic Interaction Variability](https://arxiv.org/html/2604.16385v1)

**Benchmark** · 代码：[StressWeb 代码](https://github.com/inclusionAI/AWorld-RL/tree/main/StressWeb)。

通过布局、交互语义和执行故障的成对扰动，测试异常后的任务完成能力。

## 12. [Beyond Sequential Interaction: Benchmarking Parallel Execution and Coordination for GUI Agents](https://arxiv.org/html/2607.22689v1)

**Benchmark｜ParaGUIBench** · 代码：[基准与代理代码](https://github.com/pkgunboat/ParaGUIBench)。

区分串行、独立并行与协调任务，用成功率、关键路径和成本衡量并行收益。

## 13. [Skim: Speculative Execution for Fast and Efficient Web Agents](https://arxiv.org/html/2605.16565v2)

**动作效率与技能复用** · 代码：未定位到公开实现。

为稳定流程设置可验证的快速路径，失败后从当前页面接回通用代理。

## 14. [WebChallenger: A Reliable and Efficient Generalist Web Agent](https://arxiv.org/html/2606.10423)

**页面观察与信息提取** · 代码：[代码](https://github.com/jayoohwang1/webchallenger)。

用分层 PageMem 组织页面区域、元素和站点记忆，按需展开观察。

## 15. [Prune4Web: DOM Tree Pruning Programming for Web Agent](https://arxiv.org/html/2511.21398v1)

**页面观察与信息提取** · 代码：未定位到公开实现。

由模型生成筛选规则、程序过滤页面元素，减少无关输入 token。

## 16. [Revisiting Observation Reduction for Web Agents: Comprehensive Evaluation with a Lightweight Framework](https://arxiv.org/html/2605.29397v1)

**页面观察与信息提取** · 代码：未定位到公开实现。

同时比较关键元素保留、成功率与压缩后的总耗时，选择页面精简规则。

## 17. [CUADebug: Diagnosing and Repairing Computer-Use Agent Failures](https://arxiv.org/html/2608.02643v2)

**失败处理与恢复** · 代码：[AgentDebugX GUI 模块](https://github.com/AgentDebugX/AgentDebugX)。

从日志定位最早的因果错误，用页面证据指导修正和重试。

## 18. [ActionEngine: From Reactive to Programmatic GUI Agents via State Machine Memory](https://arxiv.org/html/2602.20502v1)

**任务规划** · 代码：未定位到公开实现。

用页面状态机生成参数化执行计划，偏离时局部回退，减少逐步推理。

## 19. [M²: Dual-Memory Augmentation for Long-Horizon Web Agents via Trajectory Summarization and Insight Retrieval](https://arxiv.org/html/2603.00503v1)

**上下文管理** · 代码：未定位到公开实现。

结合任务轨迹摘要与历史经验检索，保留进度并压缩长任务上下文。

## 20. [Read More, Think More: Revisiting Observation Reduction for Web Agents](https://arxiv.org/html/2604.01535v1)

**页面观察与信息提取** · 代码：未定位到公开实现。

依据模型能力选择观察表示，用页面差异保留历史变化，指导固定 Qwen 的输入设计。

## 21. [AgentProg: Empowering Long-Horizon GUI Agents with Program-Guided Context Management](https://arxiv.org/html/2512.10371v2)

**上下文管理** · 代码：[代码](https://github.com/MobileLLM/AgentProg)。

按控制流和变量依赖保留必要上下文，统一计划分支与执行状态。

## 22. [CUA-Skill: Develop Skills for Computer Using Agent](https://arxiv.org/html/2601.21123v2)

**动作效率与技能复用** · 代码：[技能库与框架](https://github.com/microsoft/cua_skill)。

用参数化技能、组合图和恢复结构构建网页动作库，减少重复决策。

## 23. [Online Skill Learning for Web Agents via State-Grounded Dynamic Retrieval](https://arxiv.org/html/2606.04391v1)

**Skill｜SGDR** · 代码：[技能提取与检索框架](https://github.com/plusnli/skill-dynamic-retrieval)。

结合任务目标与当前页面状态按需检索技能，将短流程拆成逐步执行的动作，适配可访问性树与单动作接口。

## 24. [Trace2Skill: Distill Trajectory-Local Lessons into Transferable Agent Skills](https://arxiv.org/html/2603.25158v5)

**Skill** · 代码：[技能演化框架与技能样例](https://github.com/Qwen-Applications/Trace2Skill)。

从成功与失败轨迹提炼操作规则，合并为可迁移的技能文件，在不更新模型权重的条件下改进流程与恢复策略。

## 25. [SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks](https://arxiv.org/html/2602.12670v4)

**Skill** · 代码：[基准、验收器与实验记录](https://github.com/benchflow-ai/skillsbench)。

固定模型与执行框架，对照有无技能的成功率、耗时和成本，选择精简、有效的技能及加载方式。

## 26. [Beyond Prompts: Measuring and Optimizing LLM Tool-Agent Harnesses](https://arxiv.org/html/2609.05736v1)

**提示词与钩子｜PRISM** · 代码：[优化框架](https://github.com/airbnb/agent-harness-optimizer)。

区分提示词与工具中间件问题，通过受约束修改和留出评价改进固定模型的执行框架。

## 27. [Monitoring Web Agents Without Internal Signals: Observable Trajectories and Key-Step Supervision](https://arxiv.org/html/2609.02057)

**结果检验** · 代码：未定位到公开实现。

用重复动作、循环和决策一致性预测风险，设计黑盒模型接口的中途检查条件。

## 28. [Lost in Recovery: Demystifying Recovery Behavior of Computer-Use Agents via Goal-Oriented Action Replay](https://arxiv.org/html/2610.27954v1)

**失败处理与恢复｜ReTRACE** · 代码：[作者仓库：代码待发布](https://github.com/BangProx/ReTRACE)。

检查恢复后能否正确执行后续动作，验证回退和重放是否恢复了任务状态。

## 29. [Agentic Test-Time Scaling for WebAgents](https://arxiv.org/html/2602.12276)

**模型调用效率｜CATTS** · 代码：未定位到公开实现。

按候选动作的投票分歧决定是否追加仲裁，平衡成功率与调用成本。

## 30. [Composing Task-specific Agent Harnesses at Test Time with Reusable Primitives](https://arxiv.org/html/2609.38912v1)

**提示词与钩子｜STITCH** · 代码：未定位到公开实现。

按任务组合状态、验证、上下文和终止原语，减少不必要的检查开销。

## 31. [“Are We Done Yet?”: A Vision-Based Judge for Autonomous Task Completion of Computer Use Agents](https://arxiv.org/html/2511.20067v1)

**结果检验** · 代码：[代码](https://github.com/martasumyk/vision-based-judge)。

核对任务要求与最终页面证据，将未完成原因反馈给代理并从当前状态续做。

## 32. [SCOPE: Prompt Evolution for Enhancing Agent Effectiveness](https://arxiv.org/html/2512.15374v2)

**提示词与钩子** · 代码：[代码](https://github.com/JarvisPei/SCOPE)。

将失败轨迹提炼为即时修正与长期提示规则，支持离线提示词迭代。

## 33. [ShopGym: An Integrated Framework for Realistic Simulation and Scalable Benchmarking of E-Commerce Web Agents](https://arxiv.org/html/2605.16116v1)

**Benchmark** · 代码：未定位到公开实现。

参考电商任务组合、购物状态与完成条件，补充电商流程测试。
