# Skill检索与执行：补充证据

2026-10-30。范围为当前对话、根AGENTS.md、研究评估指导.md、比赛要求、整体理解及更新的33篇清单与Skill筛选材料；不使用跨项目记忆。未使用DSH或再派发。按要求只修改本分工两份文件。

## 论文与实验

|论文|原文与阅读位置|实验支撑/10|判断|
|---|---|---|---|
|22 CUA-Skill|[2601.21123v2](https://arxiv.org/html/2601.21123v2)，§2相关工作、§3技能/执行图/组合图、§4检索配置执行、§5实验与消融、附录B–F|8|独立技能执行、WAA端到端和跨规划模型技能消融支撑结构化技能故事，达标。不将best-of-three成绩当本题单次成绩。|
|23 SGDR|[2606.04391v1](https://arxiv.org/html/2606.04391v1)，§2相关工作、§3顺序学习设定、§4提取/验证/双信号检索/MMR、§5实验消融、附录A提示和参数/B案例|8|五站点双骨干、任务/状态信号、MMR、滑窗粒度消融支撑动态检索，达标。步数包含复合技能调用，不能等同官方平台单动作步数。|

CUA原文缓存：../WebAgent_20261029/独立筛选/来源文本/2601.21123v2.json。SGDR原文：../WebAgent_20261029/Skill筛选证据/SGDR.txt。SGDR定位连续研究关系为AWM/ASI/CER的任务级经验复用转向状态级调用，不杜撰同作者连续成果。

## 本轮代码核查

通过GitHub连接器读取 microsoft/cua_skill 根目录、agent目录、README，以及以下源码全文：

- agent/action/compose_action.py：确认BaseComposeAction及add_path、append_graph、step等函数；图结构与展开不等于网页后置条件验证，正文验证链为项目设计。
- agent/action/argument.py：确认Argument及其value/description/frozen封装；不将其描述为完整JSON schema校验器。
- agent/retrieval.py：确认BM25、HybridIndexer、HybridRetrieval、ActionRetriever及retrieve_actions；原实现含SentenceTransformer与辅助embedding，项目首版规则/BM25替换已标为适配。

读取 plusnli/online-skill-learning 的sgdr与retrieval目录、sgdr/retrieval/skill_store.py源码；原论文仓库地址skill-dynamic-retrieval现解析到online-skill-learning。核实Skill、SkillStore.add/save/topk与JSONL原子替换写入；topk代码评分为alpha*task+(1-alpha)*state，先topM再MMR；默认alpha=0.4，与论文表A.4的0.5不同；tau_high/tau_low默认None，语义去重不默认启用。源码另有本地缓存 Skill筛选证据/online-skill-learning_skill_store.py.txt，内容对应。

已确认state_summarizer.py和induce目录存在；正文只称入口，未声称核实其全部内部实现。未运行或复现代码。

事实核查8.5/10，达标。原文SGDR提取提示要求调用时所有参数ID来自同一当前页面；附录部分示例横跨展开/导航，不能据示例认为未来ID可预知。本项目更保守地保存语义目标并逐步重绑定，明确是单动作接口迁移设计。候选刷新门控、统一技能schema、契约连接、暂停游标和步骤证据均属项目组合，不冒充作者原实现。
