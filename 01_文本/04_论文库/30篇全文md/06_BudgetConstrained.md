---
title: "Are Online Skill and Memory Modules Always Worth Their Tokens? A Budget-Constrained Study of Web Agents"
arxiv_html: https://arxiv.org/html/2606.15017v2
downloaded: 2026-10-29
converted: arxiv LaTeXML HTML -> Markdown（本地图片 + alttext 公式还原）
---

ServiceNow AI Research
ÉTS Montreal
University of British Columbia
McGill University

# Are Online Skill and Memory Modules Always Worth Their Tokens? A Budget-Constrained Study of Web Agents

- **Sina Hajimiri**
- **Masih Aminbeidokhti**
- **Jose Dolz**
- **Ismail Ben Ayed**
- **Issam H. Laradji**
- **Spandana Gella**
- **Nicolas Gontier**

###### Abstract

Online web agents often augment a base actor with memory, workflow, or skill modules.
These modules can improve performance, but they also consume test-time tokens, a cost rarely reported alongside the actor’s inference cost.
We study online augmentation, where this overhead is paid on every task, and re-evaluate its benefits under a fixed total inference budget.
We compare AWM, ASI, and ReasoningBank with a token-matched vanilla baseline that uses the same budget for additional actor steps.
Across four WebArena domains and three models, Gemini 3 Flash, GPT-5.4-mini, and Qwen 3.6-27B, the vanilla baseline matches or surpasses all three augmentation methods in aggregate success rate while often using fewer total tokens.
We observe a similar trend on WorkArena-L1 with Qwen 3.6-27B, indicating that the effect extends to enterprise knowledge-work tasks.
Our results suggest that skills and workflow memory can be useful in specific domains, but their apparent gains often vanish against a budget-matched actor.
We further show that run-to-run variance materially affects outcomes and should be reported as a core evaluation criterion for online web agents.

## 1 Introduction

Controlled total inference budget per taskOnline augmentationAWM / ASI / ReasoningBankBudget-matched actorvanilla actor + more explorationactormodules


10 actor steps + module calls
actor


15 actor steps

Cost paid online:
fewer tokens left for exploration

Budget redirected:
more interaction
with the environment

![](images/06_BudgetConstrained/intro_results.svg)

Figure 1: 
Budget allocation under controlled test-time inference cost.
(top) Online augmentation spends budget on workflow, skill, or memory modules, while a budget-matched vanilla actor (Vanilla-IB) spends it on additional observe-act steps.
(bottom) On WebArena with Gemini 3 Flash ([Google DeepMind, 2025](#bib.bib27)), Vanilla-IB achieves the highest success rate with fewer tokens.

Web agents are evaluated on how often they solve tasks under a test-time budget.
A growing line of work augments a base actor with modules that induce reusable workflows, maintain memory, or distill skills from prior trajectories ([Wang et al., 2025a](#bib.bib8); [Wang et al., 2025b](#bib.bib7); [Ouyang et al., 2026](#bib.bib10); [Yu et al., 2026](#bib.bib9)).
Following Agent Skill Induction ([Wang et al., 2025a](#bib.bib8)) and SkillWeaver ([Zheng et al., 2025](#bib.bib11)), we use the term *skill* for executable code, typically a Python function, that wraps a reusable sequence of low-level actions.

These auxiliary modules are not free.
They consume tokens, add prompts and control logic, and in the online setting, couple performance to the order in which tasks are processed.
Their token cost is rarely reported next to the actor’s, which makes it hard to tell whether observed gains are justified within a fixed budget.
This creates a simple allocation problem: tokens spent inducing, retrieving, verifying, or injecting reusable knowledge are tokens unavailable for direct task execution, such as observing the current page, reasoning over its state, or taking additional actions.

Figure [1](#S1.F1) illustrates this tradeoff.
Under the same total inference budget, an online augmented agent splits its budget between direct environment interaction and auxiliary memory, workflow, or skill machinery.
A budget-matched vanilla actor instead redirects that budget toward additional observe-act steps.
The bottom panel previews the main empirical pattern we observe on WebArena ([Zhou et al., 2024](#bib.bib5)): once total token usage is counted, a budget-matched vanilla agent achieves the highest average success rate while using fewer tokens than the online augmentation methods.

Prior work on augmentation methods largely assumed that base models lacked the capability to complete tasks end-to-end ([Wang et al., 2025b](#bib.bib7); [Wang et al., 2025a](#bib.bib8)); more recent frontier models, however, may no longer face that constraint and may require less external scaffolding.
We therefore ask a direct question: under a fixed inference budget, is it better to allocate tokens to online memory and skill modules, or can a vanilla actor achieve comparable performance by spending the same budget on additional interaction steps?
We focus on the *online* setting, where agents update their behavior using trajectories collected during evaluation, rather than relying on offline skill libraries constructed before deployment.
In this setting, auxiliary costs are incurred repeatedly, the knowledge accumulated by memory or skill modules depends on the order in which tasks are encountered rather than the full task distribution, and task-level parallelism is constrained by the sequential dependence between tasks.

To study this tradeoff, we compare three online augmentation methods, Agent Workflow Memory (AWM; [Wang et al., 2025b](#bib.bib7)), Agent Skill Induction (ASI; [Wang et al., 2025a](#bib.bib8)), and ReasoningBank ([Ouyang et al., 2026](#bib.bib10)), against a budget-matched vanilla actor.
Unlike the augmented methods, which use the default 10-step actor horizon, this baseline allocates the same inference budget to a longer interaction horizon; we refer to it as Vanilla-Increased-Budget (Vanilla-IB).
We do not present Vanilla-IB as a new agent scaffold, but rather as a simple budget-aware control designed to test whether the overhead of online augmentation is justified.

We evaluate this comparison on WebArena ([Zhou et al., 2024](#bib.bib5)) and WorkArena-L1 ([Drouin et al., 2024](#bib.bib30)).
WebArena provides the broadest sweep in our study, spanning three models, four agent configurations, and four domains: Shopping, Reddit, Admin, and GitLab.
WorkArena-L1 tests the same budget-matching question in enterprise knowledge-work tasks under Qwen 3.6-27B.

Our main findings are as follows:
(1) On WebArena, Vanilla-IB achieves the highest aggregate success rate across all three models we test, while mostly using fewer total tokens than AWM, ASI, and ReasoningBank.
(2) On WorkArena-L1, Vanilla-IB remains competitive with the best-performing augmented methods, indicating that the budget-matching question is not specific to WebArena or consumer-style websites.
(3) Beyond these aggregate results, we show that single-run success rate hides high task-level variance, and that reporting a method’s performance from a single run is a weak basis for comparison.

These findings suggest three evaluation principles for online web agents. First, comparisons should report *total token usage* across all modules, not only the actor.
Second, online augmentation methods should be compared against *baselines within the same budget*.
Third, evaluations should report *multi-run variance*, since agent evaluation introduces stochasticity that aggregate single-run metrics do not capture.

## 2 Related work

#### Web agent benchmarks.

Mind2Web ([Deng et al., 2023](#bib.bib6)) and WebArena ([Zhou et al., 2024](#bib.bib5)) introduced large-scale benchmarks for realistic multi-step browser interaction. Subsequent work has broadened this benchmark landscape to cover visual grounding in VisualWebArena ([Koh et al., 2024](#bib.bib29)), enterprise workflows in WorkArena ([Drouin et al., 2024](#bib.bib30)) and WorkArena++ ([Boisvert et al., 2024](#bib.bib31)), live websites in Online-Mind2Web ([Xue et al., 2025](#bib.bib32)), and continuously generated open-ended tasks in WebArena-Infinity ([Zhou, 2026](#bib.bib33)). In this work, we focus on WebArena and WorkArena because they provide interactive environments in which agents must act, observe the consequences of their actions, and complete diverse tasks end-to-end. This makes them well suited for evaluating test-time compute mechanisms, where the cost of additional reasoning steps, tool calls, or memory access must be measured as part of the agent’s deployment-time behavior.

#### Online workflow, memory, and skill induction.

A growing line of work augments base actors with modules that extract reusable knowledge from evaluation-time trajectories.
AWM ([Wang et al., 2025b](#bib.bib7)) induces natural-language workflows from successful trajectories and retrieves them for later tasks.
ASI ([Wang et al., 2025a](#bib.bib8)) synthesizes reusable Python skill functions called as higher-level operations for subsequent tasks.
ReasoningBank ([Ouyang et al., 2026](#bib.bib10)) distills reasoning strategies from both successes and failures into a growing memory bank queried at test time.
PolySkill ([Yu et al., 2026](#bib.bib9)) separates a skill’s abstract goal from its concrete realization for more general reuse, and PlugMem ([Yang et al., 2026](#bib.bib13)) proposes a task-agnostic memory plugin attachable to any LLM agent.
ACE ([Zhang et al., 2026](#bib.bib23)) treats the agent’s context itself as an evolving playbook that accumulates and refines strategies through a generate-reflect-curate loop.
ERL ([Allard et al., 2026](#bib.bib24)) reflects on task trajectories to extract transferable heuristics, which are retrieved at test time to guide execution on subsequent tasks.
All these methods share a common premise: part of the test-time budget is allocated to producing and retrieving reusable knowledge, a cost that is rarely reported alongside the actor’s.
Our work asks whether that allocation is always the right choice.

#### Offline reusable knowledge.

A complementary line of work builds reusable knowledge before deployment begins, through an exploration or synthesis phase that is separate from the evaluation run.
SkillWeaver ([Zheng et al., 2025](#bib.bib11)) discovers and synthesizes Python API skills in an offline phase before deployment.
WALT ([Prabhu et al., 2026](#bib.bib12)) learns stable tool abstractions reverse-engineered from website structure prior to evaluation, and
WebXSkill ([Wang et al., 2026](#bib.bib21)) mines parameterized action programs from synthetic agent trajectories.
JEF-Hinter ([Nekoei et al., 2025](#bib.bib22)) distills offline trajectories into compact, context-aware hints, including from both successful and failed traces, and retrieves relevant hints for the agent’s current state at inference time.
Offline approaches amortize discovery or distillation cost over many subsequent uses, which is useful when an agent is deployed repeatedly on the same stable environment.
This tradeoff breaks down when the environment is visited infrequently, when its structure changes between discovery and deployment, or when the agent encounters a new domain.
These limitations motivate the online setting that is the focus of our work.

#### LLM capability and the value of scaffolding.

Frontier language models have rapidly improved in capabilities central to web agents: multi-step reasoning, instruction following, and adaptive decision-making under uncertainty.
Recent models such as GPT-5.4 ([OpenAI, 2026b](#bib.bib1)), Claude Sonnet 4.6 ([Anthropic, 2026](#bib.bib28)), and Gemini 3 ([Google DeepMind, 2025](#bib.bib27)) can solve complex long-horizon tasks with relatively lightweight scaffolding, often matching or outperforming more heavily engineered agent architectures ([Bechard et al., 2026](#bib.bib15)).
This rapid progress has consequences for augmentation methods: gains that were genuine and substantial over weaker models may shrink or disappear as the base actor becomes more capable on its own.

#### Alternative paradigms and evaluation robustness.

Most web agents use a browser, accessibility-tree, and fixed action vocabulary.
A line of work explores structurally different paradigms: API-based agents substantially outperform browser agents on WebArena, with hybrid agents reaching even higher performance ([Song et al., 2025](#bib.bib14)), and terminal-based agents operating through code and programmatic interfaces can match or outperform GUI-based agents on enterprise automation tasks ([Bechard et al., 2026](#bib.bib15)).
These approaches avoid some browser-skill fragilities, but depend on stable, documented APIs that may not exist.
Within the browser-based setting, evaluation reliability is itself a concern: timeouts, page-load failures, and non-deterministic UI behavior can change outcomes independently of agent decisions. Introducing realistic network failures into WebArena, WebVoyager ([He et al., 2024](#bib.bib19)), and REAL ([Garg et al., 2025](#bib.bib20)) has been shown to cause significant drops in success rates ([Kara et al., 2026](#bib.bib17)).
These issues reinforce the importance of multi-run reporting as a first-class evaluation criterion.

## 3 Experimental settings

### 3.1 Tasks and domains

We evaluate on WebArena ([Zhou et al., 2024](#bib.bib5)), a benchmark of realistic multi-step web tasks across isolated website environments.
We report results on four domains.
Shopping, consisting of 187 tasks, is an e-commerce site with product search, comparison, and checkout tasks.
Reddit, with 106 tasks, is a social discussion platform with navigation, posting, and search tasks.
Admin, which contains 182 tasks, is the administrator panel of the WebArena shopping site, covering product management, order processing, and account administration.
GitLab, with 180 tasks, is a collaborative software-development platform with repository browsing, issue tracking, merge-request, and project management tasks.
These domains differ in how much their tasks share navigational patterns, which is relevant to whether workflow or skill reuse can pay off.
We do not evaluate on WebArena’s Map domain due to website reliability issues, following prior work ([Ouyang et al., 2026](#bib.bib10); [Miyai et al., 2026](#bib.bib18)).

The setting is sequential and online: agents attempt tasks in order, and use modules with skill, memory, or workflow components to extract knowledge from earlier trajectories and apply it to later ones.

We also evaluate on the Level-1 collection of WorkArena ([Drouin et al., 2024](#bib.bib30)) tasks focused on common enterprise knowledge-work interactions in the ServiceNow platform.
This benchmark consists of 33 task types spanning ServiceNow operations such as dashboards, forms, knowledge-base search, list filtering, list sorting, menu navigation, and service-catalog requests.
For WorkArena-L1, we conduct the same online comparison across all task types, using three seeds per task type for each method.
This benchmark replaces consumer-style and community websites with enterprise software workflows, while preserving the browser-based interaction setting used by our agents.

### 3.2 Studied systems

We compare four agent scaffolds in our experiments. Three methods augment the actor with auxiliary modules while keeping the actor’s interaction horizon to at most 10 steps. The fourth, Vanilla-IB, is a vanilla actor without auxiliary modules but with an extended interaction budget.

AWM ([Wang et al., 2025b](#bib.bib7)): online workflow memory, in which an LLM-based auxiliary module induces and retrieves workflows from prior trajectories alongside the actor.

ASI ([Wang et al., 2025a](#bib.bib8)): online programmatic skill induction, in which an LLM-based auxiliary module synthesizes, verifies, and reuses Python skill functions.

ReasoningBank ([Ouyang et al., 2026](#bib.bib10)): online reasoning memory, in which an LLM-based auxiliary module accumulates and retrieves reasoning strategies from prior successes and failures (denoted RBank in tables).

Vanilla-IB: a vanilla actor with its interaction horizon extended to 15 steps and with rule-based pruning of the accessibility-tree.
The pruning removes text duplicated between a parent node and its direct children, a common pattern in accessibility-trees that inflates context length without adding information.
This pruning involves no LLM calls (see Appendix [B](#A2)).
We do not present these modifications as a contribution; they are included only to give the vanilla actor more interaction steps under a comparable overall budget.

The 15-step horizon for Vanilla-IB typically does not exceed the total token budget of the augmented methods, because their auxiliary modules consume a substantial fraction of the overall tokens.
Exact budget matching is difficult in exploratory web agent benchmarks such as WebArena and WorkArena.
Token usage varies across tasks because agents choose actions dynamically and task complexity differs, so there is no fixed per-task cost to target.
Moreover, for augmented methods, a single fixed budget cannot be cleanly divided between the actor and its auxiliary modules.
The augmented methods in our comparison also use different aggregate budgets, so there is no single token value against which to match Vanilla-IB. The most practical control lever is therefore the actor’s maximum step count.
Setting this horizon to 15 is an approximation rather than an exact budget match.
In many tasks, Vanilla-IB could take additional steps while still remaining within the token budget of one or more augmented baselines.
In a small number of tasks, the reverse is true: Vanilla-IB spends slightly more tokens than one or more augmented methods.
We acknowledge this as a limitation of step-count-based budget control, although such cases are uncommon in our experiments.

|  | Shopping (187) |  | Reddit (106) |  | Admin (182) |  | GitLab (180) |  | Avg. |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Method | SR $\uparrow$ | Tok $\downarrow$ | SR $\uparrow$ | Tok $\downarrow$ | SR $\uparrow$ | Tok $\downarrow$ | SR $\uparrow$ | Tok $\downarrow$ | SR $\uparrow$ | Tok $\downarrow$ |
| Gemini 3 Flash |  |  |  |  |  |  |  |  |  |  |
| Vanilla-IB | 47.77 $\pm$ 1.9 | 45.7 $\pm$ 0.8 | 47.48 $\pm$ 0.5 | 71.7 $\pm$ 2.2 | 55.68 $\pm$ 1.6 | 99.0 $\pm$ 4.0 | 29.07 $\pm$ 0.6 | 78.0 $\pm$ 1.8 | 44.78 | 73.6 |
| AWM | 41.18 $\pm$ 2.1 | 70.8 $\pm$ 3.0 | 47.48 $\pm$ 1.4 | 87.2 $\pm$ 2.0 | 47.43 $\pm$ 0.6 | 142.7 $\pm$ 5.4 | 24.44 $\pm$ 1.0 | 92.3 $\pm$ 1.1 | 39.34 | 99.3 |
| ASI | 44.74 $\pm$ 1.2 | 82.8 $\pm$ 0.3 | 44.97 $\pm$ 2.0 | 94.6 $\pm$ 4.8 | 52.75 $\pm$ 1.1 | 139.4 $\pm$ 11.2 | 22.96 $\pm$ 2.0 | 107.7 $\pm$ 5.8 | 41.02 | 107.3 |
| RBank | 45.45 $\pm$ 1.4 | 54.6 $\pm$ 1.3 | 39.93 $\pm$ 1.4 | 76.8 $\pm$ 2.8 | 48.90 $\pm$ 1.9 | 124.6 $\pm$ 3.3 | 22.96 $\pm$ 0.9 | 72.7 $\pm$ 1.0 | 39.33 | 82.6 |
| GPT-5.4-mini |  |  |  |  |  |  |  |  |  |  |
| Vanilla-IB | 38.50 $\pm$ 0.9 | 54.3 $\pm$ 0.8 | 34.59 $\pm$ 4.8 | 96.2 $\pm$ 6.6 | 35.89 $\pm$ 1.3 | 124.1 $\pm$ 8.0 | 22.22 $\pm$ 2.2 | 89.8 $\pm$ 4.4 | 32.67 | 90.2 |
| AWM | 29.95 $\pm$ 1.9 | 62.0 $\pm$ 2.0 | 29.56 $\pm$ 1.1 | 80.4 $\pm$ 12.6 | 32.24 $\pm$ 3.2 | 113.4 $\pm$ 16.8 | 17.22 $\pm$ 1.1 | 95.7 $\pm$ 2.7 | 27.02 | 88.5 |
| ASI | 33.15 $\pm$ 0.9 | 73.4 $\pm$ 9.0 | 28.93 $\pm$ 2.2 | 87.2 $\pm$ 4.9 | 32.96 $\pm$ 3.8 | 138.5 $\pm$ 10.9 | 20.74 $\pm$ 0.6 | 95.7 $\pm$ 1.9 | 29.00 | 99.8 |
| RBank | 26.38 $\pm$ 3.9 | 57.9 $\pm$ 1.6 | 22.01 $\pm$ 2.9 | 69.2 $\pm$ 2.9 | 34.25 $\pm$ 1.8 | 123.1 $\pm$ 2.3 | 14.45 $\pm$ 2.9 | 69.3 $\pm$ 2.2 | 24.58 | 81.0 |
| Qwen 3.6-27B |  |  |  |  |  |  |  |  |  |  |
| Vanilla-IB | 45.99 $\pm$ 1.4 | 58.8 $\pm$ 1.5 | 44.34 $\pm$ 2.5 | 89.7 $\pm$ 4.3 | 50.73 $\pm$ 1.4 | 130.3 $\pm$ 9.5 | 28.15 $\pm$ 1.2 | 101.8 $\pm$ 6.5 | 42.14 | 95.5 |
| AWM | 41.35 $\pm$ 1.9 | 71.8 $\pm$ 4.5 | 43.08 $\pm$ 3.0 | 103.6 $\pm$ 13.8 | 46.15 $\pm$ 3.1 | 178.5 $\pm$ 12.5 | 23.33 $\pm$ 1.1 | 102.2 $\pm$ 4.8 | 38.01 | 115.0 |
| ASI | 43.67 $\pm$ 3.5 | 78.8 $\pm$ 5.5 | 43.08 $\pm$ 1.4 | 120.5 $\pm$ 4.7 | 49.08 $\pm$ 2.3 | 182.2 $\pm$ 4.2 | 25.74 $\pm$ 1.4 | 120.6 $\pm$ 3.6 | 40.15 | 125.8 |
| RBank | 39.75 $\pm$ 0.8 | 65.4 $\pm$ 0.2 | 41.19 $\pm$ 1.4 | 99.1 $\pm$ 5.4 | 47.62 $\pm$ 1.7 | 156.9 $\pm$ 8.6 | 20.93 $\pm$ 1.7 | 86.0 $\pm$ 5.7 | 37.00 | 101.9 |

Table 1: Per-domain success rate (%) and total token usage per task (K) on WebArena.
Domain values are means over three independent runs (mean $\pm$ std); per-run details are in Appendix [G](#A7). Avg. is the task-weighted mean over tasks of all four domains.

### 3.3 Models and budget accounting

We evaluate under three models, Gemini 3 Flash ([Google DeepMind, 2025](#bib.bib27)), GPT-5.4-mini ([OpenAI, 2026a](#bib.bib2)), and Qwen 3.6-27B ([Qwen Team, 2026](#bib.bib3)), each across three independent runs on each domain.
On WorkArena-L1, we report the results under Qwen 3.6-27B.
For every configuration, we report task success rate (SR) and total token usage, which aggregates all LLM calls made by the system: actor and any auxiliary module calls (i.e., workflow induction, skill synthesis, memory construction, retrieval, and verification).
Token usage is averaged per task in thousands of tokens (K).
For both WebArena and WorkArena-L1, metrics are reported as means and standard deviations over three runs.
Prior work typically reports metrics on one run, and often does not report token usage; we treat this accounting as a first-class evaluation criterion.

## 4 Main results

#### Performance and token usage.

Table [1](#S3.T1) summarizes WebArena success rate and total token usage across domains, methods, and models.
Across WebArena domains, Vanilla-IB achieves the best average success rate for all three base models and, for Gemini 3 Flash and Qwen 3.6-27B, is also the most token-efficient configuration.
The augmented methods therefore do not simply trade extra tokens for higher accuracy; their workflow, skill, or memory modules often increase cost without producing proportional gains in task success.
This complicates the interpretation of scaffolded-agent gains: auxiliary reasoning can make a system appear stronger by giving it more computation, but much of that advantage disappears when compared with a vanilla actor that spends a similar budget on additional environment interaction.
The effect is strongest for GPT-5.4-mini, suggesting that scaffold quality is itself model-dependent: weaker models can produce noisy workflows, skills, or reasoning memories that are difficult for the actor to ignore.
For stronger models, the augmented methods are less prone to bad insights but still do not overtake Vanilla-IB, consistent with modern actors already internalizing many of the planning and navigation abilities that earlier scaffolds attempted to externalize.

#### Reddit step-sweep.

The closest case for augmentation is Reddit with Gemini 3 Flash, where AWM and Vanilla-IB have identical success rates.
We probe this case by extending the Vanilla-IB actor horizon further (Figure [2](#S4.F2)).
As the actor horizon increases, Vanilla-IB steadily improves, matching AWM from 15 steps onward and surpassing it at larger horizons while still using fewer tokens up until 25 steps.
This comparison also clarifies the role of step count: the augmented methods already exceed the 15-step Vanilla-IB token budget at their standard 10-step horizon, so giving them the same longer horizon would increase rather than resolve the cost imbalance.
The apparent benefit of workflow memory on Reddit is therefore at least partly explained by budget asymmetry rather than by a robust advantage of the auxiliary module itself.

Method
SR $\uparrow$ 
Tok $\downarrow$ 


Vanilla-IB
55.56 $\pm$ 2.9
109.4 $\pm$ 14.8

AWM
53.53 $\pm$ 3.8
102.8 $\pm$ 2.6

ASI
48.49 $\pm$ 4.3
113.8 $\pm$ 10.2

RBank
55.56 $\pm$ 2.8
120.3 $\pm$ 5.7

Table 2: Success rate (%) and total token usage per task (K) on WorkArena-L1 (33 task types) for Qwen 3.6-27B. Values are means over three independent seeds per task type.

#### WorkArena-L1.

The enterprise setting is more balanced but supports the same basic conclusion.
Table [2](#S4.T2) shows that, under Qwen 3.6-27B, Vanilla-IB is effectively tied with ReasoningBank for the best success rate, outperforms AWM and ASI, and uses fewer tokens than ASI and ReasoningBank.
Thus, Vanilla-IB remains on the success–cost frontier rather than being dominated by an augmented method.

#### Where does the token budget go?

To identify the source of the token overhead, we decompose total usage into actor tokens from environment interaction and module tokens from workflow induction, skill synthesis, retrieval, and verification, in Table [3](#S4.T3).
The overhead has two sources.
First, augmented methods pay explicit module costs.
Second, and less obviously, augmentation methods also inflate the actor’s prompt by injecting retrieved workflows, memories, or available skill functions at each step.
This implicit cost cannot be removed by making module calls cheaper: as long as retrieved knowledge is inserted into the actor context, the per-step actor cost rises with the size of that content.
Augmentation therefore imposes a double cost, combining auxiliary inference with larger actor prompts.

|  | Shopping |  |  |  | Reddit |  |  |  | Admin |  |  |  | GitLab |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | Actor |  | Modules |  | Actor |  | Modules |  | Actor |  | Modules |  | Actor |  | Modules |  |
| Method | P. | C. | P. | C. | P. | C. | P. | C. | P. | C. | P. | C. | P. | C. | P. | C. |
| Vanilla-IB | 45.2 | 0.5 | 0 | 0 | 71.3 | 0.4 | 0 | 0 | 98.4 | 0.6 | 0 | 0 | 77.3 | 0.7 | 0 | 0 |
| AWM | 64.1 | 0.4 | 6.1 | 0.2 | 82.9 | 0.4 | 3.7 | 0.2 | 135.0 | 0.5 | 6.9 | 0.3 | 86.1 | 0.6 | 5.4 | 0.2 |
| ASI | 61.8 | 0.5 | 20.0 | 0.5 | 84.6 | 0.4 | 9.3 | 0.3 | 118.1 | 0.5 | 20.2 | 0.6 | 85.2 | 0.5 | 21.4 | 0.5 |
| RBank | 36.6 | 1.1 | 16.5 | 0.4 | 53.3 | 1.0 | 22.1 | 0.4 | 96.9 | 1.2 | 26.1 | 0.4 | 51.3 | 1.8 | 19.2 | 0.4 |

Table 3: Token breakdown by component under Gemini 3 Flash on WebArena, per task in thousands (K). Actor: tokens from LLM calls made during interaction steps. Modules: tokens from auxiliary components (workflow induction, skill synthesis, retrieval, verification). Both are further split into prompt (P.) and completion (C.) tokens. Values are means over three runs. Vanilla-IB has no module calls by construction.

![](images/06_BudgetConstrained/sweep_reddit.svg)


Figure 2: Vanilla-IB horizon sweep on Reddit under Gemini 3 Flash. Success rate (left) and total tokens per task (right) are reported as a function of interaction steps. The available budget is the token usage of the best-performing augmentation baseline, in this case AWM, shaded in orange (right). At the 10-step mark, Vanilla-IB SR is below AWM, which in isolation might seem to justify augmentation. However, the right panel shows AWM already spends about 25% more tokens at that point. Extending the Vanilla-IB horizon up to 25 steps closes this gap: Vanilla-IB surpasses AWM in SR while still using fewer tokens than AWM.

#### Headroom for Vanilla-IB.

We set the Vanilla-IB horizon to 15 steps as a clean, domain-agnostic choice, but in most cases it is a conservative setting.
As the Reddit sweep shows (Figure [2](#S4.F2)), token usage at 15 steps is still well below AWM’s budget, and success rate continues to rise before saturating around 25 steps.
The unused headroom is even larger on Shopping, where the token gap to augmentation methods is wider.
Together, these results suggest that comparisons should be made along the axis of total token cost rather than nominal step count. AWM evaluated at 10 steps already spends more tokens than Vanilla-IB at 15 steps, so extending its actor horizon would only widen this cost gap rather than close it. For any step budget at which augmented methods are evaluated, a budget-matched vanilla baseline can be obtained by increasing the Vanilla-IB horizon accordingly; the same token-efficiency imbalance therefore persists across operating points.
We confirm this directly by re-running all methods at a higher budget and observe that the accuracy–cost ordering is preserved (Appendix [D](#A4)).

## 5 Audit beyond aggregate success rate

### 5.1 Run-to-run variance

#### Multi-run reporting.

A single-run aggregate success rate hides properties that matter for online web agents.
Even at a fixed temperature, LLM outputs vary across runs due to hardware-level non-determinism in distributed inference.
A given task may succeed in one run and fail in another for reasons unrelated to agent capability: a different token sample produces a different action sequence, which may or may not navigate the same interface in the same way.
Another source of variance can be the web environment itself: BrowserGym ([Le Sellier de Chezelles et al., 2025](#bib.bib25)) and Playwright ([Microsoft, 2025](#bib.bib26)) can encounter timeouts, slow page loads, or intermittent server errors, and prior work shows that injected web failures can sharply reduce success rates on web tasks ([Kara et al., 2025](#bib.bib16); [Kara et al., 2026](#bib.bib17)).
As a result, two runs of the same agent on the same task set can produce nearly identical aggregate success rates while disagreeing on a meaningful fraction of individual tasks.
This aggregate stability is reassuring for reproducibility but hides large task-level noise that single-run evaluations do not expose.

Multi-run reporting helps absorb both sources of noise and provides a more reliable picture of what the agent can actually do.
A single reported success rate is an incomplete statistic: it conflates genuine agent capability with the particular set of environment states encountered in that run, and this conflation is especially dangerous when comparing methods that differ in the number or structure of their LLM calls, since some methods have more opportunities to encounter a bad environment state. The effect is concrete even for the step-matched comparison that motivates augmentation: at a matched interaction budget, a plain vanilla actor can beat a given augmented method in one run and lose to it in another, so a single-run comparison can support opposite headlines. We therefore perform our experiments over three runs, and the detailed per-run results are provided in Appendix [G](#A7).

#### Any-of-3 and All-of-3.

To expose the task-level instability, we compute two complementary bounds:
*Any-of-3*, the fraction of tasks that succeed in at least one of the three runs (an OR across runs); and
*All-of-3*, the fraction that succeed in all three runs (an AND across runs).
Table [4](#S5.T4) reports both as illustrative bounds on the latent capability that single-run averages hide, and shows that the gaps are relatively large for all the methods.
Single-run success rate is therefore an incomplete estimate of task-level capability, especially for methods whose learned state changes across the evaluation sequence.

|  | Gemini 3 Flash |  |  |  | GPT-5.4-mini |  |  |  | Qwen 3.6-27B |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Method | Any | $\bm{\Delta_{\uparrow}}$ | All | $\bm{\Delta_{\downarrow}}$ | Any | $\bm{\Delta_{\uparrow}}$ | All | $\bm{\Delta_{\downarrow}}$ | Any | $\bm{\Delta_{\uparrow}}$ | All | $\bm{\Delta_{\downarrow}}$ |
| Vanilla-IB | 54.01 | +6.2 | 42.25 | $-$ 5.5 | 46.52 | +8.0 | 27.81 | $-$ 10.7 | 54.01 | +8.0 | 38.50 | $-$ 7.5 |
| AWM | 47.06 | +5.9 | 35.83 | $-$ 5.4 | 37.43 | +7.5 | 21.39 | $-$ 8.6 | 49.73 | +8.4 | 33.16 | $-$ 8.2 |
| ASI | 51.34 | +6.6 | 37.43 | $-$ 7.3 | 40.64 | +7.5 | 26.74 | $-$ 6.4 | 52.41 | +8.7 | 36.36 | $-$ 7.3 |
| RBank | 53.48 | +8.0 | 38.50 | $-$ 7.0 | 35.29 | +8.9 | 17.64 | $-$ 8.7 | 47.06 | +7.3 | 34.22 | $-$ 5.5 |

Table 4: Any-of-3 and All-of-3 success rates (%) on the Shopping domain of WebArena across three models. Any-of-3 is the fraction of tasks succeeding in at least one run; All-of-3 is the fraction succeeding in all three runs. $\Delta_{\uparrow}$ and $\Delta_{\downarrow}$ are the gaps from the three-run mean (Table [1](#S3.T1)).

### 5.2 Programmatic skill fragility

A structural limit of programmatic skill approaches such as ASI is that a synthesized skill is tied to the accessibility-tree state in which it was created.
These skills often wrap a sequence of low-level actions and refer to UI elements by BrowserGym accessibility-tree IDs (BIDs), which are assigned dynamically.
BIDs are not stable across interactions. After the first action in a skill, the page may reload or update, and later BIDs may then point to different elements or to nothing at all. The function then either fails silently, throws an error that disrupts the agent’s trajectory, or interacts with the wrong element.

A vanilla agent that queries the LLM at each step adapts to state changes naturally, since it observes the current accessibility-tree before choosing each action.
A function-based approach lacks this adaptability unless it inserts an extra LLM call inside the function at each sub-step, in which case its efficiency justification largely disappears.
Appendix [F](#A6) provides explanations of this and related failure modes across all three augmented methods, including concrete task-level examples where augmented agents fail and Vanilla-IB succeeds.

### 5.3 Effect of accessibility-tree pruning

Vanilla-IB combines two changes relative to a plain 10-step agent: an extended 15-step actor horizon and rule-based accessibility-tree pruning (Appendix [B](#A2)).
Table [5](#S5.T5) isolates their individual contributions.

Shopping
Reddit
Admin
GitLab

Configuration
SR $\uparrow$ 
Tok $\downarrow$ 
SR $\uparrow$ 
Tok $\downarrow$ 
SR $\uparrow$ 
Tok $\downarrow$ 
SR $\uparrow$ 
Tok $\downarrow$ 


10 steps
45.81 $\pm$ 1.5
48.0 $\pm$ 1.1
45.28 $\pm$ 1.0
75.2 $\pm$ 6.4
48.72 $\pm$ 0.3
103.5 $\pm$ 7.7
27.22 $\pm$ 0.6
65.6 $\pm$ 0.6

10 steps, pruned
46.35 $\pm$ 2.2
41.7 $\pm$ 0.5
47.17 $\pm$ 0.9
70.8 $\pm$ 1.6
51.65 $\pm$ 1.0
85.5 $\pm$ 3.9
27.04 $\pm$ 1.4
60.9 $\pm$ 0.8

15 steps
47.24 $\pm$ 2.8
54.0 $\pm$ 1.1
47.48 $\pm$ 2.2
77.7 $\pm$ 6.7
57.14 $\pm$ 0.0
119.8 $\pm$ 16.1
30.56 $\pm$ 0.0
78.0 $\pm$ 2.1

15 steps, pruned
47.77 $\pm$ 1.9
45.7 $\pm$ 0.8
47.48 $\pm$ 0.5
71.7 $\pm$ 2.2
55.68 $\pm$ 1.6
99.0 $\pm$ 4.0
29.07 $\pm$ 0.6
78.0 $\pm$ 1.8

Table 5: Effect of extending the vanilla actor horizon from 10 to 15 steps and rule-based accessibility-tree pruning, across all four domains of WebArena under Gemini 3 Flash. Per-domain success rate (%) and total token usage per task (K). Values are means over three runs (mean $\pm$ std). The last row corresponds to Vanilla-IB.

The two changes play distinct roles: the extended horizon drives the success-rate gain, while pruning acts primarily as a token-reduction mechanism.
The horizon effect can be isolated: even the unpruned 15-step actor (the *15 steps* row) already outperforms all three augmented methods, so Vanilla-IB’s accuracy advantage comes from the longer horizon rather than from pruning.
Pruning instead helps pay for that horizon: the tokens it saves largely offset the cost of the five additional interaction steps, so Vanilla-IB often uses no more tokens than the plain 10-step actor despite its longer horizon.
Pruning’s effect on success rate is small and domain-dependent, as expected, since it removes redundant accessibility-tree text rather than adding reasoning capability.
When it does help, we suspect this is because removing duplicate entries makes the context more information-dense and shortens the token distance between related elements, such as a label and its field, which may make actionable content easier to track; the mixed results across domains indicate that this benefit is not uniform.
We also apply the same pruning procedure to the augmented baselines, with results reported in Appendix [C](#A3).

## 6 Practical advantages of stateless evaluation

Beyond success rate and token cost, two practical properties differ between Vanilla-IB and the augmented methods, both stemming from the absence of cross-task state.

#### Parallelism.

Vanilla-IB treats tasks as independent episodes and maintains no shared cross-task state.
As a result, with $N$ workers, tasks can be executed concurrently, reducing end-to-end wall-clock time by up to a factor of $N$ .
In contrast, AWM, ASI, and ReasoningBank are inherently sequential: each task must finish before the next begins because the memory or skill state derived from its trajectory is reused in subsequent tasks.
This makes parallel deployability an additional practical advantage of Vanilla-IB, beyond its token efficiency.

#### Fault tolerance.

Web benchmarks are run against live or simulated website environments that are not always perfectly reliable: a server may become temporarily unresponsive, a page may time out, or a browser session may crash mid-task for reasons unrelated to the agent ([Kara et al., 2025](#bib.bib16)).
For Vanilla-IB, any such failure is local: the affected task can simply be re-run in isolation and the result substituted, since no other task depends on its outcome.
For AWM, ASI, and ReasoningBank, this repair is not possible in general.
If task $k$ fails due to an environment glitch, the knowledge state used by all subsequent tasks $k{+}1,k{+}2,\ldots$ was already formed without a potential successful trajectory from task $k$ .
Re-running task $k$ in isolation does not retroactively correct the downstream state; a proper repair would require re-running the entire experiment, which can be expensive.
A single transient environment failure can therefore silently degrade the reported performance of an online augmentation method in a way that is hard to detect.
In our experiments, when we identified a failure caused by the evaluation infrastructure rather than the agent’s decisions, such as a network issue or browser crash, we re-ran the affected task immediately so that the augmentation methods could still potentially induce knowledge from it, and so that the reported numbers reflect each method’s performance under its intended conditions.

## 7 Conclusion

We re-evaluated online web agent augmentation under a fixed total inference budget, asking whether test-time tokens are better spent on memory, workflow, or skill modules, or directly on additional actor steps. Across four WebArena domains and three models (Gemini 3 Flash, GPT-5.4-mini, and Qwen 3.6-27B), a token-matched vanilla actor matches or surpasses AWM, ASI, and ReasoningBank in aggregate success rate while often using fewer total tokens. We observed the same trend on WorkArena-L1 with Qwen 3.6-27B, indicating that the effect extends beyond consumer web tasks to enterprise knowledge-work settings. These results do not imply that skills or workflow memory are useless: they can provide gains in domains where task structure supports reuse. Rather, our findings show that such gains are conditional and often disappear once augmentation overhead is compared against a budget-matched actor. We also show that run-to-run variance materially affects outcomes, motivating the inclusion of multi-run experiments as a core evaluation criterion rather than an optional diagnostic. Overall, our results argue for stronger evaluation hygiene in online web agent research: total test-time cost should be reported transparently, augmented agents should be compared against budget-aware vanilla baselines, and robustness analyses should accompany aggregate success rates.

## 8 Limitations

This paper reports a focused empirical comparison on WebArena under three models (Gemini 3 Flash, GPT-5.4-mini, and Qwen 3.6-27B), plus WorkArena-L1 under Qwen 3.6-27B, and several limitations follow from this scope.

Our conclusions are restricted to the benchmarks we tested and should not be generalized to all web environments.
Also, our WorkArena-L1 results are restricted to Qwen 3.6-27B and three seeds per task type.
Our benchmarks also do not place heavy demands on long-term memory: tasks in WebArena and WorkArena-L1 are largely self-contained, so information seldom needs to be carried across many episodes.
Explicitly memory-intensive environments, where solving later tasks depends on information accumulated over many earlier ones, could shift the balance toward memory modules, and evaluating the budget-matching question there is an important direction for future work.
More generally, settings with more homogeneous task distributions, longer deployment horizons, or environments built around stable high-level APIs may yield a more favorable tradeoff for augmentation methods.

Besides, our budget-matching argument applies to online augmentation only; offline methods such as SkillWeaver ([Zheng et al., 2025](#bib.bib11)) and WALT ([Prabhu et al., 2026](#bib.bib12)) amortize skill-discovery cost over many uses, and a fair comparison there requires different accounting.

## Acknowledgments

This research was supported by Mitacs through the Mitacs Accelerate program and by the Fonds de recherche du Québec – Nature et technologies (FRQNT).
This work was carried out during an internship at ServiceNow AI Research.

## References

- Allard et al. (2026)
  M. Allard, A. Teinturier, V. Xing, and G. Viaud
  Experiential reflective learning for self-improving LLM agents.
  In ICLR 2026 Workshop on Memory for LLM-Based Agentic Systems,
  External Links: [Link](https://openreview.net/forum?id=hQgSl6kj1W)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Anthropic (2026)
  Anthropic
  Introducing Claude Sonnet 4.6.
  Note: <https://www.anthropic.com/news/claude-sonnet-4-6>Model announcement
  Cited by: [§2](#S2.SS0.SSS0.Px4.p1.1).
- Bechard et al. (2026)
  P. Bechard, O. Marquez Ayala, E. Chen, J. Skelton, S. Davasam, S. Sunkara, V. Yadav, and S. Rajeswar
  Terminal agents suffice for enterprise automation.
  arXiv preprint arXiv:2604.00073.
  External Links: [Document](https://dx.doi.org/10.48550/arXiv.2604.00073),
  [Link](https://arxiv.org/abs/2604.00073)
  Cited by: [§2](#S2.SS0.SSS0.Px4.p1.1),
  [§2](#S2.SS0.SSS0.Px5.p1.1).
- Boisvert et al. (2024)
  L. Boisvert, M. Thakkar, M. Gasse, M. Caccia, T. L. S. De Chezelles, Q. Cappart, N. Chapados, A. Lacoste, and A. Drouin
  WorkArena++: towards compositional planning and reasoning-based common knowledge work tasks.
  In Advances in Neural Information Processing Systems,
  Vol. 37, pp. 5996–6051.
  External Links: [Document](https://dx.doi.org/10.52202/079017-0195),
  [Link](https://proceedings.neurips.cc/paper_files/paper/2024/file/0b82662b6c32e887bb252a74d8cb2d5e-Paper-Datasets_and_Benchmarks_Track.pdf)
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Deng et al. (2023)
  X. Deng, Y. Gu, B. Zheng, S. Chen, S. Stevens, B. Wang, H. Sun, and Y. Su
  Mind2Web: towards a generalist agent for the web.
  In Advances in Neural Information Processing Systems,
  Vol. 36, pp. 28091–28114.
  External Links: [Link](https://proceedings.neurips.cc/paper_files/paper/2023/file/5950bf290a1570ea401bf98882128160-Paper-Datasets_and_Benchmarks.pdf)
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Drouin et al. (2024)
  A. Drouin, M. Gasse, M. Caccia, I. H. Laradji, M. Del Verme, T. Marty, D. Vazquez, N. Chapados, and A. Lacoste
  WorkArena: how capable are web agents at solving common knowledge work tasks?.
  In Proceedings of the 41st International Conference on Machine Learning,
  Proceedings of Machine Learning Research, Vol. 235, pp. 11642–11662.
  External Links: [Link](https://proceedings.mlr.press/v235/drouin24a.html)
  Cited by: [§1](#S1.p6.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1),
  [§3.1](#S3.SS1.p3.1).
- Garg et al. (2025)
  D. Garg, S. VanWeelden, D. Caples, A. Draguns, N. Ravi, P. Putta, N. Garg, T. Abraham, M. Lara, F. Lopez, J. Liu, A. Gundawar, P. Hebbar, Y. Joo, J. Gu, C. London, C. Schroeder de Witt, and S. Motwani
  REAL: benchmarking autonomous agents on deterministic simulations of real websites.
  arXiv preprint arXiv:2504.11543.
  External Links: [Document](https://dx.doi.org/10.48550/arXiv.2504.11543),
  [Link](https://arxiv.org/abs/2504.11543)
  Cited by: [§2](#S2.SS0.SSS0.Px5.p1.1).
- Google DeepMind (2025)
  Google DeepMind
  Gemini 3 Flash.
  Note: <https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Flash-Model-Card.pdf>Model card
  Cited by: [Figure 1](#S1.F1),
  [Figure 1](#S1.F1.7),
  [§2](#S2.SS0.SSS0.Px4.p1.1),
  [§3.3](#S3.SS3.p1.1).
- He et al. (2024)
  H. He, W. Yao, K. Ma, W. Yu, Y. Dai, H. Zhang, Z. Lan, and D. Yu
  WebVoyager: building an end-to-end web agent with large multimodal models.
  In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers),
  pp. 6864–6890.
  External Links: [Document](https://dx.doi.org/10.18653/v1/2024.acl-long.371),
  [Link](https://aclanthology.org/2024.acl-long.371/)
  Cited by: [§2](#S2.SS0.SSS0.Px5.p1.1).
- Kara et al. (2026)
  S. Kara, F. E. Faisal, and S. Nath
  WAREX: web agent reliability evaluation on existing benchmarks.
  Transactions on Machine Learning Research.
  External Links: ISSN 2835-8856,
  [Link](https://openreview.net/forum?id=o4pXVP8RCD)
  Cited by: [§2](#S2.SS0.SSS0.Px5.p1.1),
  [§5.1](#S5.SS1.SSS0.Px1.p1.1).
- Kara et al. (2025)
  S. Kara, F. Faisal, and S. Nath
  WABER: evaluating reliability and efficiency of web agents with existing benchmarks.
  In ICLR 2025 Workshop on Foundation Models in the Wild,
  External Links: [Link](https://openreview.net/forum?id=HY0VG19fHv)
  Cited by: [§5.1](#S5.SS1.SSS0.Px1.p1.1),
  [§6](#S6.SS0.SSS0.Px2.p1.1).
- Koh et al. (2024)
  J. Y. Koh, R. Lo, L. Jang, V. Duvvur, M. C. Lim, P. Huang, G. Neubig, S. Zhou, R. Salakhutdinov, and D. Fried
  VisualWebArena: evaluating multimodal agents on realistic visually grounded web tasks.
  In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers),
  pp. 881–905.
  External Links: [Document](https://dx.doi.org/10.18653/v1/2024.acl-long.50),
  [Link](https://aclanthology.org/2024.acl-long.50/)
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Kwon et al. (2023)
  W. Kwon, Z. Li, S. Zhuang, Y. Sheng, L. Zheng, C. H. Yu, J. E. Gonzalez, H. Zhang, and I. Stoica
  Efficient memory management for large language model serving with PagedAttention.
  In Proceedings of the 29th Symposium on Operating Systems Principles,
  pp. 611–626.
  External Links: [Document](https://dx.doi.org/10.1145/3600006.3613165),
  [Link](https://doi.org/10.1145/3600006.3613165)
  Cited by: [Appendix A](#A1.p3.1).
- Le Sellier de Chezelles et al. (2025)
  T. Le Sellier de Chezelles, M. Gasse, A. Lacoste, M. Caccia, A. Drouin, L. Boisvert, M. Thakkar, T. Marty, R. Assouel, S. Omidi Shayegan, L. K. Jang, X. H. Lù, O. Yoran, D. Kong, F. F. Xu, S. Reddy, G. Neubig, Q. Cappart, R. Salakhutdinov, and N. Chapados
  The BrowserGym ecosystem for web agent research.
  Transactions on Machine Learning Research.
  Note: Expert Certification
  External Links: ISSN 2835-8856,
  [Link](https://openreview.net/forum?id=5298fKGmv3)
  Cited by: [Appendix A](#A1.p1.1),
  [§5.1](#S5.SS1.SSS0.Px1.p1.1).
- Microsoft (2025)
  Microsoft
  Playwright: fast and reliable end-to-end testing for modern web apps.
  Note: <https://playwright.dev>Accessed: 2026-05-06
  Cited by: [§5.1](#S5.SS1.SSS0.Px1.p1.1).
- Miyai et al. (2026)
  A. Miyai, Z. Zhao, K. Egashira, A. Sato, T. Sunada, S. Onohara, H. Yamanishi, M. Toyooka, K. Nishina, R. Maeda, K. Aizawa, and T. Yamasaki
  WebChoreArena: evaluating web browsing agents on realistic tedious web tasks.
  In Third Conference on Language Modeling,
  External Links: [Link](https://arxiv.org/abs/2506.01952)
  Cited by: [§3.1](#S3.SS1.p1.1).
- Nekoei et al. (2025)
  H. Nekoei, A. Jaiswal, P. Bechard, O. Shliazhko, O. Marquez Ayala, M. Reymond, M. Caccia, A. Drouin, S. Chandar, and A. Lacoste
  JEF-Hinter: leveraging offline knowledge for improving web agents adaptation.
  arXiv preprint arXiv:2510.04373.
  External Links: [Document](https://dx.doi.org/10.48550/arXiv.2510.04373),
  [Link](https://arxiv.org/abs/2510.04373)
  Cited by: [§2](#S2.SS0.SSS0.Px3.p1.1).
- OpenAI (2026a)
  OpenAI
  GPT-5.4 mini.
  Note: <https://developers.openai.com/api/docs/models/gpt-5.4-mini>Model documentation
  Cited by: [§3.3](#S3.SS3.p1.1).
- OpenAI (2026b)
  OpenAI
  GPT-5.4 Thinking system card.
  Note: <https://openai.com/index/gpt-5-4-thinking-system-card/>System card
  Cited by: [§2](#S2.SS0.SSS0.Px4.p1.1).
- Ouyang et al. (2026)
  S. Ouyang, J. Yan, I. Hsu, Y. Chen, K. Jiang, Z. Wang, R. Han, L. T. Le, S. Daruki, X. Tang, V. Tirumalashetty, G. Lee, M. Rofouei, H. Lin, J. Han, C. Lee, and T. Pfister
  ReasoningBank: scaling agent self-evolving with reasoning memory.
  In The Fourteenth International Conference on Learning Representations,
  External Links: [Link](https://openreview.net/forum?id=jL7fwchScm)
  Cited by: [Appendix A](#A1.p1.1),
  [§1](#S1.p1.1),
  [§1](#S1.p5.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1),
  [§3.1](#S3.SS1.p1.1),
  [§3.2](#S3.SS2.p4.1).
- Prabhu et al. (2026)
  V. Prabhu, Y. Dai, M. Fernandez, K. Ramakrishnan, J. Gu, Y. Luo, S. Savarese, C. Xiong, J. Li, Z. Chen, and R. Xu
  WALT: web agents that learn tools.
  In The Fourteenth International Conference on Learning Representations,
  External Links: [Link](https://openreview.net/forum?id=cgIDqcJcoI)
  Cited by: [§2](#S2.SS0.SSS0.Px3.p1.1),
  [§8](#S8.p3.1).
- Qwen Team (2026)
  Qwen Team
  Qwen3.6-27B.
  Note: <https://huggingface.co/Qwen/Qwen3.6-27B>Model card
  Cited by: [§3.3](#S3.SS3.p1.1).
- Song et al. (2025)
  Y. Song, F. F. Xu, S. Zhou, and G. Neubig
  Beyond browsing: API-based web agents.
  In Findings of the Association for Computational Linguistics: ACL 2025,
  pp. 11066–11085.
  External Links: [Document](https://dx.doi.org/10.18653/v1/2025.findings-acl.577),
  [Link](https://aclanthology.org/2025.findings-acl.577/)
  Cited by: [§2](#S2.SS0.SSS0.Px5.p1.1).
- Wang et al. (2026)
  Z. Wang, Q. Wu, X. Zhang, C. Zhang, W. Yao, F. E. Faisal, B. Peng, S. Qin, S. Nath, Q. Lin, C. Bansal, D. Zhang, S. Rajmohan, J. Gao, and H. Yao
  WebXSkill: skill learning for autonomous web agents.
  arXiv preprint arXiv:2604.13318.
  External Links: [Document](https://dx.doi.org/10.48550/arXiv.2604.13318),
  [Link](https://arxiv.org/abs/2604.13318)
  Cited by: [§2](#S2.SS0.SSS0.Px3.p1.1).
- Wang et al. (2025a)
  Z. Z. Wang, A. Gandhi, G. Neubig, and D. Fried
  Inducing programmatic skills for agentic tasks.
  In Second Conference on Language Modeling,
  External Links: [Link](https://openreview.net/forum?id=lsAY6fWsog)
  Cited by: [Appendix A](#A1.p1.1),
  [Appendix E](#A5.p1.1),
  [§1](#S1.p1.1),
  [§1](#S1.p4.1),
  [§1](#S1.p5.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1),
  [§3.2](#S3.SS2.p3.1).
- Wang et al. (2025b)
  Z. Z. Wang, J. Mao, D. Fried, and G. Neubig
  Agent workflow memory.
  In Proceedings of the 42nd International Conference on Machine Learning,
  Proceedings of Machine Learning Research, Vol. 267, pp. 63897–63911.
  External Links: [Link](https://proceedings.mlr.press/v267/wang25bx.html)
  Cited by: [Appendix A](#A1.p1.1),
  [§1](#S1.p1.1),
  [§1](#S1.p4.1),
  [§1](#S1.p5.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1),
  [§3.2](#S3.SS2.p2.1).
- Xue et al. (2025)
  T. Xue, W. Qi, T. Shi, C. H. Song, B. Gou, D. Song, H. Sun, and Y. Su
  An illusion of progress? Assessing the current state of web agents.
  In Second Conference on Language Modeling,
  External Links: [Link](https://openreview.net/forum?id=6jZi4HSs6o)
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Yang et al. (2026)
  K. Yang, Z. Chen, X. He, J. Jiang, M. Galley, C. Wang, J. Gao, J. Han, and C. Zhai
  PlugMem: a task-agnostic plugin memory module for LLM agents.
  In Forty-third International Conference on Machine Learning,
  External Links: [Link](https://openreview.net/forum?id=NWKaQIKoGp)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Yu et al. (2026)
  S. Yu, G. Li, W. Shi, and P. Qi
  PolySkill: learning generalizable skills through polymorphic abstraction for continual learning.
  In The Fourteenth International Conference on Learning Representations,
  External Links: [Link](https://openreview.net/forum?id=KdEsujyiSV)
  Cited by: [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Zhang et al. (2026)
  Q. Zhang, C. Hu, S. Upasani, B. Ma, F. Hong, V. Kamanuru, J. Rainton, C. Wu, M. Ji, H. Li, U. Thakker, J. Zou, and K. Olukotun
  Agentic context engineering: evolving contexts for self-improving language models.
  In The Fourteenth International Conference on Learning Representations,
  External Links: [Link](https://openreview.net/forum?id=eC4ygDs02R)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Zheng et al. (2025)
  B. Zheng, M. Y. Fatemi, X. Jin, Z. Z. Wang, A. Gandhi, Y. Song, Y. Gu, J. Srinivasa, G. Liu, G. Neubig, and Y. Su
  SkillWeaver: web agents can self-improve by discovering and honing skills.
  arXiv preprint arXiv:2504.07079.
  External Links: [Document](https://dx.doi.org/10.48550/arXiv.2504.07079),
  [Link](https://arxiv.org/abs/2504.07079)
  Cited by: [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px3.p1.1),
  [§8](#S8.p3.1).
- Zhou et al. (2024)
  S. Zhou, F. F. Xu, H. Zhu, X. Zhou, R. Lo, A. Sridhar, X. Cheng, T. Ou, Y. Bisk, D. Fried, U. Alon, and G. Neubig
  WebArena: a realistic web environment for building autonomous agents.
  In The Twelfth International Conference on Learning Representations,
  External Links: [Link](https://openreview.net/forum?id=oKn9c6ytLx)
  Cited by: [§1](#S1.p3.1),
  [§1](#S1.p6.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1),
  [§3.1](#S3.SS1.p1.1).
- Zhou (2026)
  S. Zhou
  WebArena-Infinity: generating browser environments with verifiable tasks at scale.
  Note: <https://webarena.dev/webarena-infinity/>Accessed 2026-05-24
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).

## Appendix A Implementation details

Vanilla-IB, AWM, and ASI are all run using the unified codebase and prompts released by [Wang et al. (2025a)](#bib.bib8) to ensure that differences in results cannot be attributed to inconsistencies in agent scaffolding, prompt formatting, or environment interaction.
The codebase uses BrowserGym ([Le Sellier de Chezelles et al., 2025](#bib.bib25)) for interacting with the environment.
AWM and ASI come from the same research group ([Wang et al., 2025b](#bib.bib7); [Wang et al., 2025a](#bib.bib8)), and AWM is included as a baseline in the more recent ASI codebase.
ReasoningBank is run using the codebase released by [Ouyang et al. (2026)](#bib.bib10) due to its distinct prompt structure and agent logic.

We set the actor LLM temperature of Vanilla-IB to $0$ , the same as the default value in AWM and ASI.
ReasoningBank sets the temperature to $0.7$ and we kept the default intact.
The auxiliary modules of AWM, ASI, and ReasoningBank use their respective defaults, which we do not modify.
ReasoningBank’s codebase also ships a vendored WebArena with a custom evaluation pipeline that replaces the standard BrowserGym harness.
All methods in this paper are evaluated using the unmodified BrowserGym evaluation harness to ensure identical assessment criteria across configurations.

We host Qwen 3.6-27B on four NVIDIA H100 GPUs using vLLM ([Kwon et al., 2023](#bib.bib4)).
We used AI assistants during implementation and manuscript preparation for code-related tasks, including generating plotting scripts and LaTeX snippets.
We also used them to assist with writing, and for polishing and shortening paragraphs.

## Appendix B Accessibility-tree pruning

The accessibility-tree simplification used in Vanilla-IB is a deterministic rule-based function with no LLM call, model fine-tuning, or learned component, and therefore no additional token cost.
The function operates on the BrowserGym-style accessibility-tree, in which each node has a role (e.g., button, StaticText, heading) and an accessible name, and is rendered as one indented line per node.

#### Pruning rule.

A StaticText child node is removed when its text content is already contained verbatim in the accessible name of its immediate parent.
This handles a common pattern in web accessibility-trees, where a parent node (such as a labelled button or a list item) carries the same text as its StaticText child.
Removing the duplicate cuts context length without dropping information.
StaticText nodes whose stripped content is empty are also removed.
Non-StaticText nodes, node IDs (BIDs), roles, and tree structure are not modified.
The rule has one exception: a StaticText child is kept whenever its parent’s role is one of {article, paragraph, heading, strong, emphasis, mark, sectionheader}, even when the child’s text is already in the parent’s name.
This avoids hollowing out actual prose blocks where the StaticText child is the canonical carrier of the rendered text.

#### Icon characters.

Before comparison, Unicode private-use characters in the range U+E600--U+E6FF (typically icon-font glyphs that render as visually empty placeholders) are stripped from both the parent name and the StaticText child.
Literal \uXXXX escapes that appear in the serialized tree are also stripped.
This prevents icon characters from blocking an otherwise valid redundancy match.

## Appendix C Effect of pruning on the augmented baselines

Vanilla-IB applies rule-based accessibility-tree pruning, while AWM, ASI, and ReasoningBank are run in the released configurations of their original papers without pruning.
To characterize how the baselines behave under the same preprocessing, we apply Vanilla-IB’s pruning procedure to all three of them on the Shopping domain of WebArena, under Gemini 3 Flash and Qwen 3.6-27B.
Table [6](#A3.T6) reports the result.

|  | Gemini 3 Flash |  | Qwen 3.6-27B |  |
| --- | --- | --- | --- | --- |
| Method | SR (%) $\uparrow$ | Tok (K) $\downarrow$ | SR (%) $\uparrow$ | Tok (K) $\downarrow$ |
| AWM | 41.18 $\pm$ 2.1 | 70.8 $\pm$ 3.0 | 41.35 $\pm$ 1.9 | 71.8 $\pm$ 4.5 |
| + pruning | 43.32 $\pm$ 0.5 | 66.9 $\pm$ 4.3 | 39.04 $\pm$ 2.3 | 68.9 $\pm$ 2.7 |
| ASI | 44.74 $\pm$ 1.2 | 82.8 $\pm$ 0.3 | 43.67 $\pm$ 3.5 | 78.8 $\pm$ 5.5 |
| + pruning | 45.63 $\pm$ 0.8 | 71.6 $\pm$ 5.6 | 45.81 $\pm$ 2.4 | 76.7 $\pm$ 6.3 |
| RBank | 45.45 $\pm$ 1.4 | 54.6 $\pm$ 1.3 | 39.75 $\pm$ 0.8 | 65.4 $\pm$ 0.2 |
| + pruning | 42.25 $\pm$ 4.2 | 51.1 $\pm$ 0.2 | 39.21 $\pm$ 2.2 | 59.3 $\pm$ 1.0 |
| Vanilla-IB | 47.77 $\pm$ 1.9 | 45.7 $\pm$ 0.8 | 45.99 $\pm$ 1.4 | 58.8 $\pm$ 1.5 |

Table 6: Augmented baselines with and without Vanilla-IB’s pruning procedure on the Shopping domain of WebArena, under Gemini 3 Flash and Qwen 3.6-27B. Each baseline is shown in its released configuration and with the same rule-based accessibility-tree pruning used by Vanilla-IB (*+ pruning*). Values are means over three runs (mean $\pm$ std). Success rate (%) and total token usage per task (K).

Pruning reduces token usage for every baseline under both models, consistent with its role as a cost-reduction mechanism.
Its effect on success rate is mixed: it helps AWM and ASI under Gemini 3 Flash and ASI under Qwen 3.6-27B, while slightly lowering the success rate of the remaining configurations.
Even where pruning helps, the pruned baseline still trails Vanilla-IB on success rate at a higher token cost.
The closest case is ASI under Qwen 3.6-27B, whose pruned variant reaches 45.81% against 45.99% for Vanilla-IB, but at 76.7K versus 58.8K tokens per task, roughly 30% more.
Because pruning does not uniformly improve success rate and would depart from the configurations released by the original authors, we keep those released configurations as the primary baselines in the main results and report the pruned runs here.

## Appendix D Results at a higher step budget

Our main experiments cap the augmented methods at a 10-step actor horizon and Vanilla-IB at 15 steps.
To check whether the accuracy–cost pattern persists at a higher operating point, we shift the maximum step count: the augmented methods from 10 to 15 and Vanilla-IB from 15 to 20.
We run this comparison under Qwen 3.6-27B on the Shopping, Reddit, and Admin domains of WebArena.
Table [7](#A4.T7) reports the result.

|  | Shopping |  | Reddit |  | Admin |  |
| --- | --- | --- | --- | --- | --- | --- |
| Method | SR (%) $\uparrow$ | Tok (K) $\downarrow$ | SR (%) $\uparrow$ | Tok (K) $\downarrow$ | SR (%) $\uparrow$ | Tok (K) $\downarrow$ |
| Vanilla-IB - 20 steps | 46.52 $\pm$ 0.9 | 60.8 $\pm$ 4.1 | 47.17 $\pm$ 3.8 | 91.6 $\pm$ 3.3 | 51.65 $\pm$ 2.9 | 161.4 $\pm$ 22.4 |
| AWM - 15 steps | 41.89 $\pm$ 3.4 | 79.5 $\pm$ 3.8 | 44.03 $\pm$ 0.5 | 105.0 $\pm$ 1.4 | 47.43 $\pm$ 4.2 | 212.6 $\pm$ 6.9 |
| ASI - 15 steps | 45.63 $\pm$ 2.9 | 96.4 $\pm$ 1.4 | 43.08 $\pm$ 1.1 | 127.4 $\pm$ 13.7 | 51.83 $\pm$ 3.0 | 206.8 $\pm$ 11.3 |
| RBank - 15 steps | 42.24 $\pm$ 2.8 | 79.1 $\pm$ 1.4 | 41.83 $\pm$ 2.7 | 111.6 $\pm$ 5.4 | 50.18 $\pm$ 1.1 | 198.0 $\pm$ 24.2 |

Table 7: Success rate (%) and total token usage per task (K) at a higher step budget, under Qwen 3.6-27B on WebArena. The augmented methods use a 15-step actor horizon and Vanilla-IB a 20-step horizon. Values are means over three runs (mean $\pm$ std).

The ordering is largely preserved at this second operating point.
Vanilla-IB has the highest success rate on Shopping and Reddit and uses fewer tokens than every augmented method in all three domains.
On Admin, ASI is nominally $0.18$ points above Vanilla-IB (51.83% vs. 51.65%), a gap far smaller than the run-level standard deviations, and it spends 28% more tokens to reach it (206.8K vs. 161.4K).
Averaged over the three domains, Vanilla-IB leads ASI on both axes, at 48.6% success and 106.2K tokens per task versus 47.4% and 145.6K.
Granting the augmented methods more steps therefore does not let them overtake the vanilla actor: they improve, but so does Vanilla-IB under its matched increase, and both the ordering and the cost gap remain intact.

## Appendix E Prompt templates

Vanilla-IB, AWM, and ASI use the prompt templates released by [Wang et al. (2025a)](#bib.bib8) without modification, except as noted below.
Since the templates are publicly available in the ASI code repository, we do not report them here.

#### Model-specific modification.

The prompts are model-agnostic with one exception.
When running experiments with GPT-5.4-mini, we observed two behaviors that interfered with evaluation.
First, the model frequently produced action outputs with no accompanying reasoning or explanation.
Such explanations are important for augmentation methods: the induction modules parse them to extract reusable knowledge from trajectories.
Second, the model sometimes generated turns asking the user for clarification or additional input, which is not possible during automated benchmark evaluation.
To address both issues, the following text was appended to the action prompt for GPT-5.4-mini:

> You cannot ask for follow-up questions or hand back to the user.
> Do your best with the information already available.
> Output a summary of your reasoning and the important information you have found, followed by the best actions at this step (in one triple backticks block).

It is worth noting that Vanilla-IB is less dependent on reasoning traces in the output: the vanilla agent acts only on the current observation, so in many cases explanatory text is overhead that could in principle be removed to reduce completion tokens.
This represents an additional efficiency advantage of Vanilla-IB that our numbers do not capture.
However, to ensure a fair comparison across all methods, we applied the same prompt to all methods under each model, including the above addition for GPT-5.4-mini.

## Appendix F Failure mode analysis of augmented agents

Section [5.2](#S5.SS2) discusses the structural fragility of programmatic skills in dynamic accessibility-tree interfaces at a conceptual level.
This appendix extends that discussion with quantitative characterizations of failure modes across all three augmented methods, and presents concrete examples of tasks where augmented agents fail while Vanilla-IB succeeds.
The analysis in this section covers the Shopping, Reddit, and Admin domains under Gemini 3 Flash and GPT-5.4-mini.
Unless stated otherwise, quantities are averaged over three independent runs per domain–model pair.

### F.1 ASI: Verification confounds function success with agent recovery

ASI induces Python functions from successful trajectories and adds them to a shared action library after a verification episode.
The intended guarantee is that only working functions enter the library.
In the verification procedure, the induced function is called as the first decision. If the function changes the environment but fails on one of its underlying actions, the agent may still recover via primitive actions and solve the task. In that case, the episode can be judged a success and the function is written to disk, without actual verification.
A common instance of this failure is when the function fails because an element ID has changed after the page reloaded for the verification episode.
Functions that require arguments whose values depend on a prior action’s page state are especially prone to this: the caller cannot supply a valid BID for an element that only becomes visible after an earlier click.
The induced functions are also typically short, averaging approximately 2.4 primitive actions per function under Gemini 3 Flash and 2.5 under GPT-5.4-mini, which limits the abstraction benefit.
Some functions also hardcode task-specific values that do not generalize across tasks; for example, the function fill\_refund\_request\_form in the shopping library hardcodes the complaint message “It broke after just three days of use” regardless of the actual reason for the refund.

Table [8](#A6.T8) quantifies the verification-confound effect.
We define a *first-step verification failure* as a verification run in which the induced function fails before the second agent action.
A *recovered* verification is one that was still judged correct despite that first-step failure.
First-step failures are not rare.
Under GPT, the induced function fails immediately in 72.2% of Shopping verifications; over half of those are recovered and still produce a stored library entry.
Even under Gemini Shopping, where the first-step failure rate is lower (33.3%), two thirds of failures recover.
In both cases the result is a function library that contains entries whose correctness at verification time was not due to the function itself.

| Domain | Attempts | First-step fail | Recov. rate |
| --- | --- | --- | --- |
| Gemini 3 Flash |  |  |  |
| Shopping | 58.0 | 19.3 | 69.0% |
| Reddit | 30.0 | 9.0 | 59.3% |
| Admin | 64.3 | 6.3 | 63.2% |
| GPT-5.4-mini |  |  |  |
| Shopping | 44.3 | 32.0 | 54.2% |
| Reddit | 25.0 | 12.3 | 45.9% |
| Admin | 51.7 | 22.7 | 47.1% |

Table 8: ASI verification failures at the first high-level function call on WebArena. Values are averages over three runs. *Attempts*: total number of function induction attempts by ASI across all tasks. *First-step fail*: number of attempts where the induced function failed before the second agent action. *Recov. rate*: fraction of first-step failures where the verification episode was nonetheless judged correct, causing a potentially broken function to be stored in the shared library.

### F.2 AWM: Generic templates and induction from failed trajectories

AWM induces abstract natural-language workflows from trajectories the judge deems successful, then retrieves and injects the closest workflow into the actor’s prompt at each inference step.
Many induced workflows are too generic to add navigational value.
A stored shopping workflow for order-history aggregation reduces to: “click the account link, click the full-order-history link, send a summary”.
This describes the high-level intent without preserving operational details that determine correctness, such as whether pagination is needed, what the stopping condition is, or how totals are computed.
Similarly, a stored price-range workflow directs the agent to sort, toggle direction, navigate to the last page, and report the range, but omits checks for sort direction availability, filtered result sets, or whether the last-page element is reachable in the current state.
Because the workflow is injected into the actor’s prompt, the agent must decide at each step whether to follow it or ignore it, a burden that smaller models are especially ill-equipped to handle, as it competes with the current accessibility-tree and task instruction.

A more fundamental problem is that AWM’s induction is gated only by the judge’s verdict.
Table [9](#A6.T9) shows the fraction of workflow-induction events triggered by failed trajectories.
On Shopping, nearly half of all induction events, 49.5% under Gemini and 52.3% under GPT, originate from failed agent trajectories.
The contamination is substantially lower for Reddit (11–19%), which may help explain AWM’s stronger performance on that domain.
Because AWM’s duplicate-suppression mechanism checks only whether a new workflow semantically overlaps an existing one, it does not filter out strategies that are simply wrong: once an incorrect workflow enters the library, it can be retrieved and applied to all future tasks in the same category.

| Domain | Induced | From failed (%) | Final WFs |
| --- | --- | --- | --- |
| Gemini 3 Flash |  |  |  |
| Shopping | 105.7 | 49.5% | 37.3 |
| Reddit | 45.7 | 10.9% | 16.7 |
| Admin | 99.7 | 42.1% | 48.3 |
| GPT-5.4-mini |  |  |  |
| Shopping | 78.3 | 52.3% | 33.7 |
| Reddit | 31.3 | 19.1% | 13.7 |
| Admin | 50.0 | 42.0% | 24.3 |

Table 9: AWM workflow-induction statistics on WebArena, averaged per run. *Induced*: total induction events triggered by the judge for a run. *From failed (%)*: fraction originating from tasks the ground-truth evaluator classified as failed. *Final WFs*: distinct workflows in the final library after duplicate suppression.

### F.3 ReasoningBank: Contamination and memory over-application

ReasoningBank stores a few short lessons from every task trajectory regardless of outcome, labeling each entry as a success or failure based on the judge’s verdict.
The $K$ most semantically similar entries are retrieved at inference time and injected into the actor’s context.
Table [10](#A6.T10) reports the size and contamination of the resulting memory corpus.
On Shopping tasks, more than half of all success-labeled entries, 52.9% for Gemini and 59.5% for GPT, come from trajectories that failed according to the ground-truth evaluator.
These entries are framed with positive guidance language regardless of their true provenance, so the retrieval mechanism cannot distinguish between lessons that worked and lessons that did not.

| Domain | Total mem. | Succ.- labeled | FP in succ. (%) | FN in fail (%) |
| --- | --- | --- | --- | --- |
| Gemini 3 Flash |  |  |  |  |
| Shopping | 518 | 96 | 52.9% | 40.7% |
| Reddit | 294 | 32 | 30.2% | 25.3% |
| Admin | 507 | 86 | 42.6% | 40.4% |
| GPT-5.4-mini |  |  |  |  |
| Shopping | 544 | 67 | 59.5% | 18.4% |
| Reddit | 307 | 20 | 60.0% | 17.4% |
| Admin | 532 | 62 | 48.1% | 25.2% |

Table 10: ReasoningBank memory-corpus statistics on WebArena, averaged over three runs. Tasks processed per run: 187 (Shopping), 106 (Reddit), 182 (Admin). *Succ.-labeled*: tasks labeled successful by the judge. *FP in succ.*: fraction of success-labeled tasks from trajectories that failed according to the ground-truth evaluator. *FN in fail*: fraction of fail-labeled tasks from trajectories that succeeded according to the ground-truth evaluator.

A separate concern is injection pressure.
Even though only a few memories are retrieved per task, they are referenced heavily in the agent traces: across the domain–model configurations in Table [10](#A6.T10), we observe an average of 8–12 explicit memory-item mentions per task, with over 95% of Gemini tasks and over 75% of GPT tasks referencing at least one retrieved memory.
The retrieved memories therefore function as active policy hints rather than passive background.
When a memory is overly general or mildly mismatched to the current task, the agent may prioritize it over the current accessibility-tree, producing extra navigation steps, unnecessary checks, or incorrect early termination.
Vanilla-IB, which carries no retrieved memory layer, avoids this class of distraction entirely by grounding each action in the current observation.

### F.4 Discussion: Structural limits of judge-based quality control

The contamination patterns described above for AWM and ReasoningBank, and the verification confound in ASI, share a common structural root: each method delegates quality control to an LLM judge whose input is fundamentally incomplete for the tasks it is asked to evaluate.

The judge receives the agent’s textual output (its reasoning trace and final response) and, in some configurations, a snapshot of the browser state at the end of the episode.
It does not observe the sequence of intermediate page states the agent traversed, the specific elements it interacted with, or whether information the agent reports was actually encountered during navigation or confabulated in the reasoning trace.
For tasks where correctness depends on having visited the right pages and extracted the right values, a judge working from this terminal view cannot reliably reconstruct whether the work was actually done.

This is not necessarily a matter of judge capability.
A more powerful model receiving the same partial input faces the same gap: the evidence needed to verify navigation-dependent correctness is simply absent from the judge’s context.
Nor is it straightforwardly fixable by expanding what is passed to the judge.
Supplying the full trace at every step
would require passing on the order of hundreds of thousands of tokens per judge call for a ten-step task on a content-heavy page, making each evaluation call more expensive than the agent trajectory it is judging, and possibly exceeding practical context limits entirely.

| Method | Intent | Augmented agent behavior | Vanilla-IB behavior |
| --- | --- | --- | --- |
| AWM | “Buy the highest-rated product in Ceiling Light within a budget above $1000.” | Retrieved workflow for “Buy the highest-rated product” prescribes sorting then clicking the top result. Agent buys the wrong product because the workflow does not account for rating ties or the budget threshold. | Applies sorting, checks rating and price against the budget, and selects the correct product. |
| ASI | “Change the delivery address for my most recent order to 3 Oxford St, Cambridge, MA.” | Calls navigate_to_contact_page and fill_contact_form using the element ID from the docstring example ( ’1381’ ). Receives ValueError and TypeError ; form submission fails. | Navigates to Address Book, adds the new address, recognizes that the order address cannot be changed through the UI, and reports accordingly. |
| RBank | “What are the top-5 best-selling products in 2023?” | Retrieved memory on handling ranking ties directs attention to tie-breaking. Agent misidentifies the 4th and 5th items (reports Sparta Gym Tank and Angel Light Running Short instead of Sprite Stasis Ball and Hawkeye Yoga Short ). | Reads the same report without distraction and returns the correct ranked list. |

Table 11: Example failures of augmented agents where Vanilla-IB succeeds. Tasks are selected from WebArena (single runs shown; all from Gemini 3 Flash).

### F.5 Illustrative task-level failures

Table [11](#A6.T11) presents representative task-level failures drawn from our Gemini 3 Flash runs, showing in each case what the augmented agent does and how Vanilla-IB succeeds on the same task.

## Appendix G Per-run variance results

Tables [12](#A7.T12), [13](#A7.T13), and [14](#A7.T14) report success rate and token usage for each method across three independent runs under Gemini 3 Flash, GPT-5.4-mini, and Qwen 3.6-27B, respectively.
We report sample standard deviations across the three runs.

|  | Success Rate (%) $\uparrow$ |  |  |  | Tok/task (K) $\downarrow$ |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Method | Run a | Run b | Run c | Mean $\pm$ Std | Run a | Run b | Run c | Mean $\pm$ Std |
| Shopping |  |  |  |  |  |  |  |  |
| Vanilla-IB | 47.59 | 49.73 | 45.99 | 47.77 $\pm$ 1.9 | 46.6 | 45.5 | 45.1 | 45.7 $\pm$ 0.8 |
| AWM | 43.32 | 39.04 | 41.18 | 41.18 $\pm$ 2.1 | 68.0 | 70.6 | 73.9 | 70.8 $\pm$ 3.0 |
| ASI | 43.32 | 45.45 | 45.45 | 44.74 $\pm$ 1.2 | 82.4 | 83.0 | 83.0 | 82.8 $\pm$ 0.3 |
| RBank | 44.39 | 44.91 | 47.05 | 45.45 $\pm$ 1.4 | 56.0 | 54.1 | 53.6 | 54.6 $\pm$ 1.3 |
| Reddit |  |  |  |  |  |  |  |  |
| Vanilla-IB | 48.11 | 47.17 | 47.17 | 47.48 $\pm$ 0.5 | 71.7 | 69.5 | 73.8 | 71.7 $\pm$ 2.2 |
| AWM | 49.06 | 46.23 | 47.17 | 47.48 $\pm$ 1.4 | 87.6 | 88.9 | 85.0 | 87.2 $\pm$ 2.0 |
| ASI | 47.17 | 43.40 | 44.34 | 44.97 $\pm$ 2.0 | 98.5 | 89.3 | 96.0 | 94.6 $\pm$ 4.8 |
| RBank | 39.62 | 38.68 | 41.50 | 39.93 $\pm$ 1.4 | 78.9 | 73.6 | 77.8 | 76.8 $\pm$ 2.8 |
| Admin |  |  |  |  |  |  |  |  |
| Vanilla-IB | 53.85 | 56.59 | 56.59 | 55.68 $\pm$ 1.6 | 95.2 | 98.6 | 103.2 | 99.0 $\pm$ 4.0 |
| AWM | 47.80 | 47.80 | 46.70 | 47.43 $\pm$ 0.6 | 136.6 | 147.0 | 144.4 | 142.7 $\pm$ 5.4 |
| ASI | 53.85 | 51.65 | 52.75 | 52.75 $\pm$ 1.1 | 132.0 | 152.3 | 133.9 | 139.4 $\pm$ 11.2 |
| RBank | 47.80 | 51.10 | 47.80 | 48.90 $\pm$ 1.9 | 120.8 | 126.4 | 126.5 | 124.6 $\pm$ 3.3 |
| GitLab |  |  |  |  |  |  |  |  |
| Vanilla-IB | 28.33 | 29.44 | 29.44 | 29.07 $\pm$ 0.6 | 79.8 | 76.2 | 78.0 | 78.0 $\pm$ 1.8 |
| AWM | 25.00 | 23.33 | 25.00 | 24.44 $\pm$ 1.0 | 93.1 | 91.0 | 92.6 | 92.3 $\pm$ 1.1 |
| ASI | 22.78 | 21.11 | 25.00 | 22.96 $\pm$ 2.0 | 102.3 | 107.0 | 113.8 | 107.7 $\pm$ 5.8 |
| RBank | 22.78 | 23.89 | 22.22 | 22.96 $\pm$ 0.9 | 71.9 | 72.4 | 73.8 | 72.7 $\pm$ 1.0 |

Table 12: Per-run success rate (%) and token usage per task (K) across three independent runs under Gemini 3 Flash on WebArena.


|  | Success Rate (%) $\uparrow$ |  |  |  | Tok/task (K) $\downarrow$ |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Method | Run a | Run b | Run c | Mean $\pm$ Std | Run a | Run b | Run c | Mean $\pm$ Std |
| Shopping |  |  |  |  |  |  |  |  |
| Vanilla-IB | 37.43 | 39.04 | 39.04 | 38.50 $\pm$ 0.9 | 55.1 | 53.5 | 54.2 | 54.3 $\pm$ 0.8 |
| AWM | 27.81 | 31.02 | 31.02 | 29.95 $\pm$ 1.9 | 64.2 | 61.6 | 60.2 | 62.0 $\pm$ 2.0 |
| ASI | 34.22 | 32.62 | 32.62 | 33.15 $\pm$ 0.9 | 70.6 | 83.5 | 66.2 | 73.4 $\pm$ 9.0 |
| RBank | 21.93 | 27.81 | 29.41 | 26.38 $\pm$ 3.9 | 59.3 | 58.2 | 56.2 | 57.9 $\pm$ 1.6 |
| Reddit |  |  |  |  |  |  |  |  |
| Vanilla-IB | 38.68 | 35.85 | 29.25 | 34.59 $\pm$ 4.8 | 89.4 | 102.5 | 96.6 | 96.2 $\pm$ 6.6 |
| AWM | 30.19 | 30.19 | 28.30 | 29.56 $\pm$ 1.1 | 77.1 | 94.4 | 69.8 | 80.4 $\pm$ 12.6 |
| ASI | 26.42 | 30.19 | 30.19 | 28.93 $\pm$ 2.2 | 83.8 | 85.0 | 92.8 | 87.2 $\pm$ 4.9 |
| RBank | 18.87 | 24.53 | 22.64 | 22.01 $\pm$ 2.9 | 67.8 | 72.5 | 67.3 | 69.2 $\pm$ 2.9 |
| Admin |  |  |  |  |  |  |  |  |
| Vanilla-IB | 35.16 | 35.16 | 37.36 | 35.89 $\pm$ 1.3 | 117.4 | 133.0 | 121.9 | 124.1 $\pm$ 8.0 |
| AWM | 28.57 | 33.52 | 34.62 | 32.24 $\pm$ 3.2 | 129.3 | 95.9 | 114.9 | 113.4 $\pm$ 16.8 |
| ASI | 28.57 | 35.16 | 35.16 | 32.96 $\pm$ 3.8 | 126.1 | 146.5 | 142.9 | 138.5 $\pm$ 10.9 |
| RBank | 36.26 | 32.97 | 33.52 | 34.25 $\pm$ 1.8 | 121.0 | 125.5 | 122.8 | 123.1 $\pm$ 2.3 |
| GitLab |  |  |  |  |  |  |  |  |
| Vanilla-IB | 20.00 | 24.44 | 22.22 | 22.22 $\pm$ 2.2 | 94.4 | 85.5 | 89.6 | 89.8 $\pm$ 4.4 |
| AWM | 16.11 | 18.33 | 17.22 | 17.22 $\pm$ 1.1 | 92.5 | 97.0 | 97.5 | 95.7 $\pm$ 2.7 |
| ASI | 21.11 | 21.11 | 20.00 | 20.74 $\pm$ 0.6 | 94.8 | 97.9 | 94.4 | 95.7 $\pm$ 1.9 |
| RBank | 11.11 | 15.56 | 16.67 | 14.45 $\pm$ 2.9 | 70.9 | 70.3 | 66.8 | 69.3 $\pm$ 2.2 |

Table 13: Per-run success rate (%) and token usage per task (K) across three independent runs under GPT-5.4-mini on WebArena.


|  | Success Rate (%) $\uparrow$ |  |  |  | Tok/task (K) $\downarrow$ |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Method | Run a | Run b | Run c | Mean $\pm$ Std | Run a | Run b | Run c | Mean $\pm$ Std |
| Shopping |  |  |  |  |  |  |  |  |
| Vanilla-IB | 47.06 | 44.39 | 46.52 | 45.99 $\pm$ 1.4 | 57.9 | 60.5 | 57.9 | 58.8 $\pm$ 1.5 |
| AWM | 39.57 | 43.30 | 41.18 | 41.35 $\pm$ 1.9 | 73.6 | 66.7 | 75.1 | 71.8 $\pm$ 4.5 |
| ASI | 47.06 | 43.85 | 40.10 | 43.67 $\pm$ 3.5 | 72.6 | 81.1 | 82.8 | 78.8 $\pm$ 5.5 |
| RBank | 39.57 | 40.64 | 39.04 | 39.75 $\pm$ 0.8 | 65.6 | 65.2 | 65.3 | 65.4 $\pm$ 0.2 |
| Reddit |  |  |  |  |  |  |  |  |
| Vanilla-IB | 47.17 | 43.40 | 42.45 | 44.34 $\pm$ 2.5 | 94.5 | 86.5 | 88.0 | 89.7 $\pm$ 4.3 |
| AWM | 44.34 | 45.28 | 39.62 | 43.08 $\pm$ 3.0 | 110.3 | 87.8 | 112.8 | 103.6 $\pm$ 13.8 |
| ASI | 43.40 | 41.51 | 44.34 | 43.08 $\pm$ 1.4 | 118.1 | 125.9 | 117.6 | 120.5 $\pm$ 4.7 |
| RBank | 39.62 | 41.51 | 42.45 | 41.19 $\pm$ 1.4 | 96.1 | 95.9 | 105.4 | 99.1 $\pm$ 5.4 |
| Admin |  |  |  |  |  |  |  |  |
| Vanilla-IB | 49.45 | 52.20 | 50.54 | 50.73 $\pm$ 1.4 | 141.2 | 125.3 | 124.4 | 130.3 $\pm$ 9.5 |
| AWM | 45.60 | 43.40 | 49.45 | 46.15 $\pm$ 3.1 | 192.8 | 172.3 | 170.3 | 178.5 $\pm$ 12.5 |
| ASI | 51.65 | 48.35 | 47.25 | 49.08 $\pm$ 2.3 | 177.7 | 183.1 | 185.9 | 182.2 $\pm$ 4.2 |
| RBank | 46.15 | 47.25 | 49.45 | 47.62 $\pm$ 1.7 | 160.8 | 162.9 | 147.1 | 156.9 $\pm$ 8.6 |
| GitLab |  |  |  |  |  |  |  |  |
| Vanilla-IB | 27.22 | 29.44 | 27.78 | 28.15 $\pm$ 1.2 | 109.0 | 96.2 | 100.2 | 101.8 $\pm$ 6.5 |
| AWM | 23.33 | 22.22 | 24.44 | 23.33 $\pm$ 1.1 | 102.9 | 106.6 | 97.0 | 102.2 $\pm$ 4.8 |
| ASI | 27.22 | 25.55 | 24.44 | 25.74 $\pm$ 1.4 | 120.4 | 117.0 | 124.3 | 120.6 $\pm$ 3.6 |
| RBank | 20.56 | 22.78 | 19.44 | 20.93 $\pm$ 1.7 | 81.2 | 84.6 | 92.3 | 86.0 $\pm$ 5.7 |

Table 14: Per-run success rate (%) and token usage per task (K) across three independent runs under Qwen 3.6-27B on WebArena.
