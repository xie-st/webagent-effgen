---
title: "Agentic Test-Time Scaling for WebAgents"
arxiv_html: https://arxiv.org/html/2602.12276
downloaded: 2026-10-29
converted: arxiv LaTeXML HTML -> Markdown（本地图片 + alttext 公式还原）
---

# Agentic Test-Time Scaling for WebAgents

- **Nicholas Lee** · UC Berkeley
- **Lutfi Eren Erdogan**
- **Chris Joseph John** · UC Berkeley
- **Surya Krishnapillai** · UC Berkeley
- **Michael W. Mahoney** · UC Berkeley; ICSI; LBNL
- **Kurt Keutzer** · UC Berkeley
- **Amir Gholami** · ICSI

###### Abstract

Test-time scaling has become a standard way to improve performance and boost reliability of neural network models.
However, its behavior on *agentic*, multi-step tasks remains less well-understood: small per-step errors can compound over long horizons; and we find that naive policies that uniformly increase sampling show diminishing returns.
In this work, we present CATTS, a simple technique for dynamically allocating compute for multi-step agents.
We first conduct an empirical study of inference-time scaling for web agents.
We find that uniformly increasing per-step compute quickly saturates in long-horizon environments.
We then investigate stronger aggregation strategies, including an LLM-based Arbiter that can outperform naive voting, but that can overrule high-consensus decisions.
We show that uncertainty statistics derived from the agent’s own vote distribution (entropy and top-1/top-2 margin) correlate with downstream success and provide a practical signal for dynamic compute allocation.
Based on these findings, we introduce Confidence-Aware Test-Time Scaling (CATTS), which uses vote-derived uncertainty to allocate compute only when decisions are genuinely contentious. CATTS improves performance on WebArena-Lite, Online-Mind2Web, and GoBrowse by up to 11.8% over majority voting while using fewer tokens than uniform scaling, providing both efficiency gains and an interpretable decision rule.

|  |
| --- |
|  |

## 1 Introduction

Large language models (LLMs) are increasingly used not only to produce text, but to *take actions*: they can call tools, navigate websites, operate software, and execute multi-step procedures in interactive environments.
In these settings, an agent must repeatedly choose a next action, e.g., clicking a button, typing into a form, or issuing a search query, based on the current observation and the history of what it has already done ([Patil et al., 2024](#bib.bib22); [Schick et al., 2023](#bib.bib36); [Erdogan et al., 2024](#bib.bib50)).
The sequential nature of these tasks makes reliability much more challenging than simpler single-shot question answering: a single poor decision can send the trajectory into an unrecoverable state, and small per-step error rates can compound over many steps ([Erdogan et al., 2025](#bib.bib8)).

A widely used strategy for improving LLM capabilities at test time is *test-time scaling* ([Snell et al., 2024](#bib.bib55); [Brown et al., 2024](#bib.bib53); [Cobbe et al., 2021](#bib.bib54); [Zelikman et al., 2022](#bib.bib34)). The core idea is to spend compute generating more tokens at test-time, rather than spending this compute during pretraining. For single-shot reasoning tasks, this can yield large gains because different samples can explore different reasoning paths: even if the first attempt fails, additional attempts often contain a correct solution, and majority voting ([Wang et al., 2022](#bib.bib1)) or verification ([Shinn et al., 2023](#bib.bib11)) can exploit this diversity.

An important question that remains to be answered is: *What does inference-time scaling look like for multi-step, tool-using agents?*
A direct analogue of the single-shot recipe is to consider each step separately, treating each step the same way one would treat an ordinary reasoning task.
At each step $t$ , instead of generating one action, we can sample $N$ candidate actions from the base model and then choose which action to execute.
Repeating this procedure throughout a trajectory yields a simple and appealing “knob” for scaling up compute ([Wang et al., 2022](#bib.bib1); [Venkatraman et al., 2025](#bib.bib52)).

However, a naive strategy, *uniform scaling*, where we always sample the same number of candidates and apply the same selection rule at every step, runs into two issues:
(1) Wasted computation on easy steps: many steps are obvious (form fills, clicking submit), making additional sampling redundant;
(2) High-variance decisions: when votes spread across many distinct options, majority voting provides weak signal.

A common remedy is to add an LLM-based *arbiter* that reasons over the candidate set ([Venkatraman et al., 2025](#bib.bib52); [Zhang et al., 2024](#bib.bib57); [Muennighoff et al., 2025](#bib.bib56)).
However, arbiters are prone to overthinking ([Cuadron et al., 2025](#bib.bib58)): they can override correct high-consensus decisions, making extra compute harmful rather than helpful.
This raises a key question: *where* should we spend additional inference-time compute?

We study this design space systematically by adapting several test-time scaling techniques (voting, arbitration, and confidence-aware filtering ([Fu et al., 2026](#bib.bib5))) to long-horizon web agents.
The outcome is a simple principle: *inference-time compute should be allocated where it is likely to change the decision*.
We find that the distribution of answers generated at each step predicts when additional selection helps (Section [4](#S4)).

Using this insight, we present CATTS (Confidence-Aware Test-Time Scaling), which uses vote-derived uncertainty to dynamically allocate compute only when decisions are genuinely contentious.
CATTS achieves consistent improvements on WebArena-Lite and Online-Mind2Web (up to $+11.8\%$ over majority voting) while using fewer tokens than uniform scaling.

![Refer to caption](images/26_CATTS/figure-1-rounded-v3.png)


Figure 1: Comparing agentic inference-time scaling methods. Visual comparison of selection strategies at each step. Left: Majority Voting samples $N$ candidates and selects the most frequent action via argmax over vote distribution $p_{t}(a)$ . Center-Left: Arbiter samples $N$ candidates and uses an additional LLM call to reason over candidates and select the best action. Center-Right: CATTS conditionally invokes the arbiter when vote-derived uncertainty (entropy $H_{t}$ or margin $\Delta_{t}$ ) exceeds threshold $\tau$ .

## 2 Related Work

#### Inference-Time Scaling and Test-Time Compute.

Vast amounts of recent work have explored how to improve the performance and reliability of LLMs by spending additional test-time compute.
Self-consistency decoding ([Wang et al., 2022](#bib.bib1)) demonstrated substantial gains on reasoning tasks by sampling multiple chain-of-thought traces ([Wei et al., 2022](#bib.bib20); [Kojima et al., 2022](#bib.bib46)) and taking a majority vote over final answers, treating it as an ensemble problem. Subsequent work has explored richer aggregation strategies including ranked voting and diversity-aware selection ([Wang et al., 2025](#bib.bib3); [Naik et al., 2023](#bib.bib2); [Wan et al., 2024](#bib.bib14)), although several studies highlight fundamental limits when sampled outputs share correlated errors ([Byerly and Khashabi, 2026](#bib.bib4); [Turpin et al., 2023](#bib.bib38)).

Alternative approaches allocate compute via structured search over reasoning steps ([Yao et al., 2023a](#bib.bib6); [Besta et al., 2024](#bib.bib23); [Zhou et al., 2024a](#bib.bib25); [Kim et al., 2024](#bib.bib9)) or use confidence-aware filtering to gate computation ([Fu et al., 2026](#bib.bib5); [Kadavath et al., 2022](#bib.bib24)). Recent work formalizes compute-optimal policies that trade off parallel sampling and sequential refinement ([Snell et al., 2024](#bib.bib55)), connecting to adaptive computation ideas in neural models ([Graves, 2016](#bib.bib13)). Another related line of work is DeepConf ([Fu et al., 2026](#bib.bib5)), which uses the model’s own confidence scores to dynamically filter out uncertain and low-quality chain-of-thought.
The token-level probability distribution is used to compute confidence scores which can be used for confidence-weighted majority voting or filtering.

Our work applies these principles to sequential decision-making in long-horizon tool-use settings. We use vote-derived uncertainty to gate arbitration at each step, enabling dynamic allocation without requiring token-level confidence access. Unlike prior confidence-filtering approaches that operate on single-shot reasoning traces, we derive uncertainty from agreement among multiple sampled candidates, and we operate online in environments where errors compound across steps.

#### Tool-Using Agents and Long-Horizon Tasks.

Recent progress in building LLM-driven agents has been driven by frameworks that interleave reasoning and tool execution. ReAct ([Yao et al., 2023b](#bib.bib7)) demonstrated that intermixing reasoning with tool invocations improves performance, while subsequent work introduced structured decomposition such as decoupling planning from execution ([Erdogan et al., 2025](#bib.bib8); [Xu et al., 2023](#bib.bib33); [Erdogan et al., 2024](#bib.bib50)) or leveraging code for numerical reasoning ([Gao et al., 2023b](#bib.bib30); [Chen et al., 2023](#bib.bib31)). To enable robust tool use, several frameworks teach models to invoke external APIs through self-supervised learning ([Schick et al., 2023](#bib.bib36)), retrieval-aware training ([Patil et al., 2024](#bib.bib22); [Qin et al., 2024](#bib.bib37)), or structured integration layers ([Karpas et al., 2022](#bib.bib27); [Li et al., 2023](#bib.bib18)). Complementary lines of work improve agent policies through reinforcement learning ([Liu et al., 2018](#bib.bib44)), iterative refinement via self-reflection ([Shinn et al., 2023](#bib.bib11); [Zelikman et al., 2022](#bib.bib34)), or retrieval-augmented reasoning ([Gao et al., 2023a](#bib.bib32)).

Evaluation of these methods relies on increasingly realistic benchmarks. For web navigation, environments range from early workflow-based tasks ([Shi et al., 2017](#bib.bib45)) to modern suites spanning e-commerce, forums, and content management ([Zhou et al., 2024b](#bib.bib10); [Koh et al., 2024](#bib.bib39); [Deng et al., 2023](#bib.bib26); [Yao et al., 2022](#bib.bib42); [Nakano et al., 2021](#bib.bib41); [Drouin et al., 2024](#bib.bib43); [Boisvert et al., 2024](#bib.bib49)), while computer-use benchmarks extend to desktops and OS-level interaction ([Xie et al., 2024](#bib.bib29); [Rawles et al., 2023](#bib.bib16); [Rawles et al., 2024](#bib.bib17); [Zhang et al., 2025](#bib.bib19); [Pawlowski et al., 2025](#bib.bib35)). Multi-domain suites evaluate generalization across diverse tasks ([Liu et al., 2024](#bib.bib15); [Guo et al., 2024](#bib.bib48); [Wang et al., 2024](#bib.bib40); [Park et al., 2023](#bib.bib21); [Murty et al., 2024](#bib.bib47)).

Multi-agent debate and voting strategies ([Du et al., 2024](#bib.bib28)) and extreme decomposition via massive redundancy ([Meyerson et al., 2025](#bib.bib12)) offer alternative paths to reliability, often at prohibitive computational costs.
Our work is orthogonal to these training-based and architectural improvements: we assume a fixed base agent, and we focus on how to allocate inference-time compute efficiently at test time.
The central motivation is practical deployment, where unnecessary model calls translate directly to latency, cost, and energy use, making adaptive allocation essential for real-world viability.

## 3 From Static to Dynamic Inference-Time Scaling

This section presents the main study on inference-time scaling techniques for agents.
We start from the most direct adaptation of inference-time scaling to web agents: sampling multiple candidate actions and aggregating them, progressively refining the selection mechanism based on empirical failure modes.
We find that uniformly allocating inference-time compute inconsistently and inefficiently affects performance, and that the distribution of the actions themselves is an effective test-time signal for performance.
This insight is used to propose a simple and interpretable inference-time scaling policy that dynamically allocates compute only when the candidate action distribution is uncertain.

### 3.1 Experimental Setup

We study tool-using web agents that interact with a browser over multiple steps. The underlying agent is prompted with ReAct ([Yao et al., 2023b](#bib.bib7)) and uses gpt-oss-120b as the base model.
At each step $t$ , the agent observes a cleaned HTML representation of the current page state and outputs a structured action space of 8 tools including click, type\_text, scroll, etc.
The full action space, agent prompts, conversation format, and error handling mechanisms are detailed in Appendices [A](#A1) and [B](#A2).

We evaluate on WebArena-Lite ([Liu et al., 2025](#bib.bib62)), which has 165 tasks with programmatic success checks, and Online-Mind2Web ([Xue et al., 2025](#bib.bib60)), which has 300 tasks across diverse real-world websites evaluated using an LLM-as-a-judge ([Zheng et al., 2023](#bib.bib59)) protocol with Qwen3-VL-30B-A3B-Instruct.
Online-Mind2Web features substantially longer trajectories (mean 17.4 steps) than WebArena-Lite (8–12 steps), providing a challenging testbed for long-horizon scaling.
We also evaluate on GoBrowse ([Gandhi and Neubig, 2025](#bib.bib51)) (341 tasks); full results are provided in Appendix [M](#A13). A detailed comparison of benchmark characteristics and LLM-as-judge reliability is provided in Appendix [C](#A3).
We measure compute cost using the total token count per task, defined as the sum of prompt (input) and completion (output) tokens across all model calls, as a vast majority of the tokens consumed come from the input prompt.
All results on WebArena-Lite are averaged across three different seeds unless otherwise noted; Online-Mind2Web results are single-run due to compute constraints.

#### Action Clustering and Vote Distributions.

At each time step $t$ , the agent observes $o_{t}$ and samples $N$ candidate actions from the base model:

|  | 

$$
\tilde{a}^{(i)}_{t}\sim M(\,\cdot\mid o_{t}\,),\quad i=1,\dots,N.
$$

 |  | (1) |
| --- | --- | --- | --- |

We parse candidates into structured actions to obtain a set of action clusters $\mathcal{A}_{t}$ . Let $n_{t}(a)$ denote the number of candidates assigned to cluster $a\in\mathcal{A}_{t}$ .
This induces a distribution over the sampled actions

|  | 

$$
p_{t}(a)=\frac{n_{t}(a)}{N},
$$

 |  | (2) |
| --- | --- | --- | --- |

which parameterizes how much the sampled candidates agree on each distinct action at step $t$ .

One problem that arises when trying to do majority voting in this action space is that different outputs are semantically the same, but have different text representations (e.g., “N/A” vs. “Not found”).
We therefore use a lightweight semantic deduplicator LLM to cluster candidate actions into semantically equivalent buckets before counting votes (See Appendix [B](#A2) for the prompt and Appendix [D](#A4) for additional analysis).

The central question of our study is this: *Given the current observation $o_{t}$ and a multi-set of candidates $\{\tilde{a}^{(i)}_{t}\}_{i=1}^{N}$ , how should we select the executed action $a_{t}$ to maximize task success under a token budget?*
We begin with static aggregation rules (majority voting and uniform arbitration) and then show how vote-derived uncertainty enables a dynamic allocation of computation. Figure [1](#S1.F1) provides a visual overview of the selection strategies we evaluate.

### 3.2 Static Baseline: Majority Voting

The most direct adaptation of inference-time scaling to an agent loop is to sample multiple candidate next actions and execute the action with the most support. Concretely, after clustering candidates into $\mathcal{A}_{t}$ , the executed action is

|  | 

$$
a_{t}\;=\;\arg\max_{a\in\mathcal{A}_{t}}\;p_{t}(a).
$$

 |  | (3) |
| --- | --- | --- | --- |

We refer to this as *majority voting* (or frequency voting).
Most importantly, the compute allocation is uniform: the same number of candidates $N$ is sampled at every step, and the same selection rule in Eq. [3](#S3.E3) is applied throughout the trajectory.

#### Observation: Majority Vote Yields Diminishing Returns.

As we can see in Table [1](#S3.T1), simply increasing candidate-generation compute yields diminishing or even negative returns.
On WebArena-Lite, scaling from $N{=}1$ to $N{=}10$ improves success from 38.8% to 43.2%, but doubling from $N{=}10$ to $N{=}20$ actually decreases success by 0.2% despite doubling tokens.
On Online-Mind2Web, majority voting actually *degrades* with more candidates (22.6% at $N{=}1$ to 15.1% at $N{=}20$ ), likely due to vote splitting across semantically similar but textually distinct actions in longer trajectories.
We also evaluated Plan-and-Act style agents ([Erdogan et al., 2025](#bib.bib8)) with factorized candidate-generation budgets across plan and action sampling, and the results exhibit similar non-monotonic scaling behavior, establishing that the issue affects different agent architectures (see Appendix [E](#A5) for full results).

Table 1: Static inference-time scaling with majority vote. On WebArena-Lite, the final doubling ( $N{=}10\to 20$ ) produces negligible gain. On Online-Mind2Web, majority voting *degrades* with more candidates (22.6% $\to$ 15.1%).

|  | WebArena-Lite |  | Online-Mind2Web |  |
| --- | --- | --- | --- | --- |
| Budget | Success | Tokens | Success | Tokens |
| $N{=}1$ | 38.8% | 96K | 22.6% | 169K |
| $N{=}5$ | 42.4% | 460K | 20.2% | 888K |
| $N{=}10$ | 43.2% | 920K | 17.9% | 1.7M |
| $N{=}20$ | 43.0% | 1.8M | 15.1% | 3.6M |

#### Takeaway.

For long-horizon tool use, uniformly scaling up compute is often inefficient. Empirically, we observe that some steps produce highly diverse candidate sets where votes are spread across many distinct actions rather than converging on a clear winner. In these uncertain regimes, simple vote counting provides weak signal for selecting the correct action. This motivates selection mechanisms that can reason about ambiguous candidate sets, which we explore next.

### 3.3 From Voting to Arbitration

When majority vote produces diverse, uncertain candidate sets, a natural idea is to introduce an additional inference-time mechanism that *reasons over the candidate set*.
Concretely, after sampling $N$ candidates and clustering into $\mathcal{A}_{t}$ , we construct a short prompt containing the current observation $o_{t}$ and a list of representative actions (one per cluster).
An *arbiter* model then chooses the action to execute:

|  | 

$$
a_{t}\;=\;\textsc{Arbiter}(o_{t},\mathcal{A}_{t},\{n_{t}(a)\}_{a\in\mathcal{A}_{t}}).
$$

 |  | (4) |
| --- | --- | --- | --- |

In all experiments, the arbiter uses the same model as the agent (gpt-oss-120b), and semantic deduplication is applied prior to selection. See Appendix [B](#A2) for implementation details.

#### Observation: Arbitration Improves Over Majority Vote.

Replacing frequency voting with an arbiter yields a consistent improvement over static majority voting across both benchmarks in our setting.
Intuitively, the arbiter can use the observation context to break ties among plausible actions and to discard candidates that look superficially popular but are contextually inappropriate.
Table [2](#S3.T2) summarizes the comparison between (i) majority vote, (ii) a single arbiter call per step, and (iii) scaled arbitration described below.

#### Arbiter Scaling.

Because the arbiter model itself is an LLM call, we can also apply inference-time scaling *to the selection mechanism*. With “Arbiter Scaling,” we query $K$ independent arbiters and aggregate their chosen actions by majority vote:

|  | 

$$
a_{t}=\arg\max_{a\in\mathcal{A}_{t}}\frac{1}{K}\sum_{j=1}^{K}\mathbb{I}\!\left[\textsc{Select}_{j}(\cdot){=}a\right].
$$

 |  | (5) |
| --- | --- | --- | --- |

Empirically, increasing $K$ yields further gains beyond a single arbiter call, and it consistently outperforms spending an equivalent token budget solely on increasing $N$ under majority vote.

Table 2: Arbiter scaling ( $N{=}5$ ). On WebArena-Lite, scaling improves to 44.6% ( $K{=}10$ ) but degrades at $K{=}20$ . On Online-Mind2Web, arbitration provides large gains ( $+7.2\%$ at $K{=}1$ ), with further improvements from scaling.

|  | WebArena-Lite |  | Online-Mind2Web |  |
| --- | --- | --- | --- | --- |
| Method | Success | Tokens | Success | Tokens |
| Majority vote ( $N{=}5$ ) | 42.4% | 460K | 20.2% | 888K |
| Arbiter ( $K{=}1$ ) | 42.8% | 442K | 27.4% | 960K |
| Arbiter scaling ( $K{=}5$ ) | 44.2% | 645K | 26.3% | 1.4M |
| Arbiter scaling ( $K{=}10$ ) | 44.6% | 899K | 30.7% | 2.1M |
| Arbiter scaling ( $K{=}20$ ) | 42.0% | 1.4M | 29.3% | 2.8M |

#### Observation: Arbitration is not Uniformly Beneficial.

Although arbitration improves average performance, we also observe regimes where an additional arbiter call reduces success, particularly when the candidate set already exhibits strong agreement.
For example, in Table [2](#S3.T2), increasing from $K{=}10$ to $K{=}20$ at $N{=}5$ causes performance to *drop* from 44.6% to 42.0%. Section [4](#S4) analyzes this failure mode in detail and shows it is predictable from vote-derived uncertainty statistics.
See Appendix [F](#A6) for full results.

#### Deeper Aggregation Methods.

We also evaluated Recursive Self-Aggregation (RSA) ([Venkatraman et al., 2025](#bib.bib52)), which iteratively refines candidates over multiple rounds.
Despite substantially higher compute (up to 80 LLM calls per step vs. 10–11 for majority vote and single arbiter), RSA achieved comparable but not better performance than simpler methods.
Thus, we focus on single-round arbitration for the remainder of our study; full RSA results are provided in Appendix [G](#A7).

### 3.4 DeepConf-Style Confidence Filtering

We also evaluated DeepConf ([Fu et al., 2026](#bib.bib5)), which uses token-level confidence scores for filtering and weighted voting.
The best DeepConf variant (average trace, $N{=}10$ ) achieves 43.8% on WebArena-Lite, a modest gain over majority voting (43.2%).
On Online-Mind2Web, DeepConf provides limited gains (18.3–24.7%), substantially underperforming arbitration (27.4% at $K{=}1$ ).
Critically, DeepConf requires access to token-level log probabilities, limiting applicability to API-only models.
Full results are in Appendix [L](#A12).
In the next section, we explore an alternative signal derived purely from the vote distribution that achieves stronger benefits while remaining applicable to any model.

## 4 Using Vote-Derived Uncertainty as a Test-Time Signal

We saw (in Section [3.3](#S3.SS3)) that replacing frequency voting with an arbiter improves average performance, and that scaling the arbiters can improve performance further (see Table [2](#S3.T2)).
However, closer inspection of trajectories revealed a consistent pattern: the arbiter is most helpful on *contentious* steps, where multiple plausible actions compete, but it can be harmful on *high-consensus* steps where candidates already agree.
On such steps, arbitration risks overriding a correct consensus action (see Figure [8](#A11.F8)).
This motivates the main question of this subsection: *Can we distinguish between regimes where arbitration improves decisions and where it introduces harmful overrides?*

### 4.1 Analyzing Action Distributions

Given the vote distribution $p_{t}(\cdot)$ over action clusters $\mathcal{A}_{t}$ , we compute two uncertainty statistics:

|  | $\displaystyle H_{t}\;$ | $\displaystyle=\;-\sum_{a\in\mathcal{A}_{t}}p_{t}(a)\,\log p_{t}(a),$ |  | (6) |
| --- | --- | --- | --- | --- |
|  | $\displaystyle\Delta_{t}\;$ | $\displaystyle=\;p_{t}(a^{(1)}_{t})-p_{t}(a^{(2)}_{t}),$ |  | (7) |

where $a^{(1)}_{t}$ and $a^{(2)}_{t}$ are the highest- and second-highest-probability clusters under $p_{t}(\cdot)$ . Intuitively, $H_{t}$ measures overall disagreement (higher entropy means votes are spread across multiple options), while $\Delta_{t}$ measures decisiveness (larger gaps indicate a clear winner). High-consensus regimes correspond to *low* $H_{t}$ and *high* $\Delta_{t}$ , contentious regimes correspond to *high* $H_{t}$ and *low* $\Delta_{t}$ .

#### Uncertainty profiles differ between successful and failed trajectories.

We compare successful and failed tasks by their uncertainty statistics across steps. Let $T$ be the number of steps in a trajectory, and define task-level averages

|  | 

$$
\bar{H}=\frac{1}{T}\sum_{t=1}^{T}H_{t},\qquad\bar{\Delta}=\frac{1}{T}\sum_{t=1}^{T}\Delta_{t}.
$$

 |  | (8) |
| --- | --- | --- | --- |

Empirically, successful trajectories tend to exhibit lower entropy and higher margins, whereas failed trajectories show the opposite trend. Figure [2](#S4.F2) plots $H_{t}$ and $\Delta_{t}$ against the index of each step, separately for successful and failed runs, showing that disagreement typically spikes at pivotal decision points and that these spikes are more pronounced (or more frequent) in failed runs.

![](images/26_CATTS/uncertainty_profiles_paper.svg)


Figure 2: Uncertainty profiles over trajectory steps. Entropy $H_{t}$ (top) and probability margin $\Delta_{t}$ (bottom) versus step index, separated by successful (blue) and failed (orange) runs. Failed tasks consistently exhibit higher entropy and lower margins, with the gap widening at later steps.

#### Uncertainty predicts when arbitration helps versus hurts.

The failure case in Figure [8](#A11.F8) illustrates this distinction: at the pivotal step, the sampled candidates exhibit overwhelming agreement (vote split 9/10), corresponding to a large margin $\Delta_{t}$ and low entropy $H_{t}$ . In this high-consensus regime, the arbiter overrides the dominant cluster and chooses a minority alternative that derails the trajectory. A frequency-based rule would instead execute the consensus action, which in our logs for this task, leads to success.

To quantify this pattern, we analyzed all 495 task-runs from our arbiter experiments, classifying each task by whether the arbiter overrode the majority vote on any high-consensus step ( $\Delta_{t}>0.7$ ). Figure [3](#S4.F3) summarizes the results. Tasks without high-consensus overrides succeed at 46.9%, compared to 35.0% for tasks with at least one such override: a significant 11.9% difference ( $p=0.026$ , Fisher’s exact test). This effect exhibits a dose-response pattern: tasks with zero overrides succeed at 46.9%, those with exactly one at 36.6%, and those with two or more at 29.6%. The pattern is consistent across all five website categories.

![](images/26_CATTS/override_dose_response_paper.svg)

![](images/26_CATTS/arbiter_effectiveness_by_entropy_averaged.svg)

Figure 3: Arbiter effectiveness depends on vote-derived uncertainty.
(Left) Task success rate decreases as the number of high-consensus overrides ( $\Delta_{t}>0.7$ ) increases, showing a dose-response pattern ( $p=0.026$ , Fisher’s exact test). High-consensus overrides harm performance: tasks where the arbiter overrides majority vote on high-margin steps ( $\Delta_{t}>0.7$ ) show a significant dose-response decline in success rate.
(Right) Net arbiter advantage by entropy bin shows that arbitration hurts at low entropy ( $-4.4\%$ ) but helps at high entropy ( $+4$ - $6\%$ ). Grouping tasks by average trajectory entropy reveals that arbitration is harmful at low entropy but beneficial at high entropy, motivating uncertainty-gated compute allocation.

Conversely, we find that arbitration provides benefit when uncertainty is high. Figure [3](#S4.F3) groups tasks by average trajectory entropy and compares arbiter versus majority voting outcomes across all $N$ configurations. At low entropy (0.0-0.3), the arbiter shows a net disadvantage of $-4.4\%$ , consistent with the override failures above. However, at higher entropy levels, the arbiter yields positive net advantages ( $+4$ - $6\%$ ), demonstrating that arbitration adds value when votes are diverse and majority voting lacks a clear signal.

These findings illustrate a core principle: when $\Delta_{t}$ is high and $H_{t}$ is low, the model is already confident, and arbitration introduces override risk, rather than improving the decision; conversely, when entropy is high and votes are diverse, arbitration can reason over the candidate set and improve selection.
This motivates a dynamic allocation rule: invoke arbitration primarily when vote-derived uncertainty indicates that the decision is genuinely contentious.

### 4.2 CATTS: Confidence-Aware Test-Time Scaling

We use vote-derived uncertainty to decide whether to spend extra compute on arbitration at each step. Let $U_{t}$ be a scalar uncertainty score computed from the vote distribution $p_{t}(\cdot)$ . CATTS applies a threshold $\tau$ to gate arbitration:

|  | 

$$
a_{t}=\begin{cases}\arg\max_{a}p_{t}(a),&U_{t}\leq\tau\\[4.0pt]
\textsc{Arbiter}(o_{t},\mathcal{A}_{t},\{n_{t}(a)\}_{a\in\mathcal{A}_{t}}),&U_{t}>\tau.\end{cases}
$$

 |  | (9) |
| --- | --- | --- | --- |

We instantiate $U_{t}$ in two effective variants:

|  | $\displaystyle U^{(\mathrm{ent})}_{t}$ | $\displaystyle=H_{t},\quad U^{(\mathrm{mrg})}_{t}=1-\Delta_{t}.$ |  | (10) |
| --- | --- | --- | --- | --- |

Both entropy-gated and margin-gated CATTS improved the accuracy–compute tradeoff in our experiments. For both settings, we tuned $\tau$ via running a simple grid over thresholds (e.g., $\tau\in\{0.2,0.3,\dots,0.8\}$ ) and report results across this sweep (with the best-performing setting indicated where relevant).

### 4.3 Results

CATTS consistently improves over static baselines across both benchmarks. Figure [4](#S4.F4) plots success rate versus total tokens per episode for majority voting, uniform arbitration, DeepConf, and CATTS.
The key outcome is that CATTS achieves higher success than majority voting at comparable or lower token budgets, while using fewer tokens than always-arbitrate for higher success levels.
On WebArena-Lite, margin-gated CATTS achieves 47.9% at only 405K tokens, a $+5.5\%$ gain over majority voting while using 12% *fewer* tokens.
On Online-Mind2Web, entropy-gated CATTS ( $\tau{=}0.7$ ) achieves 32.0%, a $+11.8\%$ gain over majority voting and $+4.6\%$ over always-arbitrate.
Averaging across all thresholds in our sweep on WebArena-Lite, CATTS achieves 45.6%, which is still a consistent 2.4% gain that does not depend on threshold selection (See Appendix [H](#A8) for more analysis).
We additionally conducted a bootstrap calibration study (Appendix [I](#A9)) showing that threshold selection requires minimal tuning: with only 10% of tasks as calibration data, regret is ${\leq}1.1\%$ on both benchmarks.

Because CATTS invokes the arbiter only on uncertain steps, it reduces the number of arbitration calls substantially. In our experiments, the arbiter is invoked on approximately 40–60% of steps on average, concentrating compute on the steps most likely to benefit.
This selective invocation also yields token savings: on WebArena-Lite, margin-gated CATTS uses 12% fewer tokens than majority voting (405K vs. 460K) and 8% fewer than always-arbitrate (442K), while on Online-Mind2Web it uses 4% fewer tokens than always-arbitrate (922K vs. 960K).

![](images/26_CATTS/frontier_paper_pareto.svg)


Figure 4: Accuracy–compute frontier across all methods.
Success rate versus total tokens per episode on WebArena-Lite (left) and Online-Mind2Web (right). CATTS achieves Pareto improvements on both benchmarks: on WebArena-Lite, it reaches 47.9% at ${\sim}400$ K tokens; on Online-Mind2Web, it reaches 32.0% at 922K tokens, outperforming always-arbitrate while using fewer tokens.


Table 3: CATTS results ( $N{=}5$ ). On WebArena-Lite, margin-gated CATTS achieves 47.9% at only 405K tokens, fewer than majority voting (460K). On Online-Mind2Web, entropy-gated CATTS achieves 32.0% ( $+11.8\%$ over majority vote, $+4.6\%$ over always-arbitrate).

|  | WebArena-Lite |  | Online-Mind2Web |  |
| --- | --- | --- | --- | --- |
| Method | Success | Tokens | Success | Tokens |
| Majority vote | 42.4% | 460K | 20.2% | 888K |
| Always-arbitrate | 42.8% | 442K | 27.4% | 960K |
| CATTS ( $H$ , best $\tau$ ) | 45.5% | 409K | 32.0% | 922K |
| CATTS ( $\Delta$ , best $\tau$ ) | 47.9% | 405K | 30.0% | 906K |

Our experiments reveal that per-step candidate sampling falls into two regimes.
Regime 1: Redundancy. Many steps are routine; candidates concentrate on a single cluster (low entropy, high margin). Additional sampling produces duplicates, and arbitration introduces override risk (Figure [7](#A10.F7), Appendices [J](#A10) and [K](#A11)).
Regime 2: Contention. A smaller number of steps act as trajectory pivots with diffuse vote distributions. These are where selection quality matters most, as errors compound rather than self-correct. Arbitration adds value by reasoning over plausible candidates.
These gains generalize across model families, including Gemini 3.1 Flash Lite and Qwen3.5-122B-A10B (Appendix [N](#A14)).

## 5 Conclusion

We present a systematic study of inference-time scaling for long-horizon web agents.
We find that naive per-step scaling shows diminishing or negative returns, and that LLM-based arbitration helps on contentious steps but can override correct high-consensus decisions.
Vote-derived uncertainty statistics (entropy and margin) reliably distinguish these regimes.
CATTS uses this signal to dynamically allocate compute, achieving consistent improvements across WebArena-Lite, Online-Mind2Web, and GoBrowse (up to $+11.8\%$ over majority voting) while using fewer tokens.

## Acknowledgements

We acknowledge the gracious support from the Furiosa AI, Intel, Apple, NVIDIA, Macronix, and Mozilla team.
Furthermore, we appreciate the support from
Google Cloud, the Google TRC team Prof. David Patterson, along with support from Google Gemini team, and Divy Thakkar.
Prof. Keutzer’s lab is also sponsored by funding through BDD and BAIR.
We also acknowledge support by the Director, Office of Science, Office of Advanced Scientific Computing Research, of the U.S. Department of Energy under Contract No. DE-AC02-05CH11231.
MWM would also like to acknowledge DARPA, DOE, NSF, and ONR.
DOE SciGPT grant. Our conclusions do not necessarily reflect the position or the policy of our sponsors, and no official endorsement should be inferred.

## References

- Besta et al. (2024)
  M. Besta, N. Blach, A. Kubicek, R. Gerstenberger, M. Podstawski, L. Gianinazzi, J. Gajda, T. Lehmann, H. Niewiadomski, P. Nyczyk, et al.
  Graph of thoughts: solving elaborate problems with large language models.
  In Proceedings of the AAAI conference on artificial intelligence,
  Vol. 38, pp. 17682–17690.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p2.1).
- Boisvert et al. (2024)
  L. Boisvert, M. Thakkar, M. Gasse, M. Caccia, T. Le Sellier De Chezelles, Q. Cappart, N. Chapados, A. Lacoste, and A. Drouin
  WorkArena++: towards compositional planning and reasoning-based common knowledge work tasks.
  External Links: 2407.05291,
  [Link](https://arxiv.org/abs/2407.05291)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Brown et al. (2024)
  B. Brown, J. Juravsky, R. Ehrlich, R. Clark, Q. V. Le, C. Ré, and A. Mirhoseini
  Large language monkeys: scaling inference compute with repeated sampling.
  arXiv preprint arXiv:2407.21787.
  Cited by: [§1](#S1.p2.1).
- Byerly and Khashabi (2026)
  A. Byerly and D. Khashabi
  Self-consistency falls short! the adverse effects of positional bias on long-context problems.
  Transactions of the Association for Computational Linguistics 14, pp. 292–317.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Chen et al. (2023)
  W. Chen, X. Ma, X. Wang, and W. W. Cohen
  Program of thoughts prompting: disentangling computation from reasoning for numerical reasoning tasks.
  Trans. Mach. Learn. Res. 2023.
  External Links: [Link](https://openreview.net/forum?id=YfZ4ZPt8zd)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Cobbe et al. (2021)
  K. Cobbe, V. Kosaraju, M. Bavarian, M. Chen, H. Jun, L. Kaiser, M. Plappert, J. Tworek, J. Hilton, R. Nakano, et al.
  Training verifiers to solve math word problems.
  arXiv preprint arXiv:2110.14168.
  Cited by: [§1](#S1.p2.1).
- Cuadron et al. (2025)
  A. Cuadron, D. Li, W. Ma, X. Wang, Y. Wang, S. Zhuang, S. Liu, L. G. Schroeder, T. Xia, H. Mao, et al.
  The danger of overthinking: examining the reasoning-action dilemma in agentic tasks.
  arXiv preprint arXiv:2502.08235.
  Cited by: [§1](#S1.p5.1).
- Deng et al. (2023)
  X. Deng, Y. Gu, B. Zheng, S. Chen, S. Stevens, B. Wang, H. Sun, and Y. Su
  Mind2web: towards a generalist agent for the web.
  Advances in Neural Information Processing Systems 36, pp. 28091–28114.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Drouin et al. (2024)
  A. Drouin, M. Gasse, M. Caccia, I. H. Laradji, M. D. Verme, T. Marty, D. Vázquez, N. Chapados, and A. Lacoste
  WorkArena: how capable are web agents at solving common knowledge work tasks?.
  In Forty-first International Conference on Machine Learning, ICML 2024,
  Vienna, Austria, July 21-27, 2024,
  External Links: [Link](https://openreview.net/forum?id=BRfqYrikdo)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Du et al. (2024)
  Y. Du, S. Li, A. Torralba, J. B. Tenenbaum, and I. Mordatch
  Improving factuality and reasoning in language models through multiagent debate.
  In Forty-first International Conference on Machine Learning, ICML 2024,
  Vienna, Austria, July 21-27, 2024,
  External Links: [Link](https://openreview.net/forum?id=zj7YuTE4t8)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p3.1).
- Erdogan et al. (2024)
  L. E. Erdogan, N. Lee, S. Jha, S. Kim, R. Tabrizi, S. Moon, C. R. C. Hooper, G. Anumanchipalli, K. Keutzer, and A. Gholami
  Tinyagent: function calling at the edge.
  In Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing: System Demonstrations,
  pp. 80–88.
  Cited by: [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Erdogan et al. (2025)
  L. E. Erdogan, N. Lee, S. Kim, S. Moon, H. Furuta, G. Anumanchipalli, K. Keutzer, and A. Gholami
  Plan-and-act: improving planning of agents for long-horizon tasks.
  In Forty-second International Conference on Machine Learning,
  Cited by: [Appendix E](#A5.p1.1),
  [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1),
  [§3.2](#S3.SS2.SSS0.Px1.p1.1).
- Fu et al. (2026)
  Y. Fu, X. Wang, H. Zhang, Y. Tian, and J. Zhao
  Deep think with confidence.
  In International Conference on Learning Representations,
  Vol. 2026, pp. 94355–94377.
  Cited by: [§1](#S1.p6.1),
  [§2](#S2.SS0.SSS0.Px1.p2.1),
  [§3.4](#S3.SS4.p1.1).
- Gandhi and Neubig (2025)
  A. Gandhi and G. Neubig
  Go-browse: training web agents with structured exploration.
  External Links: 2506.03533,
  [Link](https://arxiv.org/abs/2506.03533)
  Cited by: [Appendix M](#A13.p1.1),
  [§3.1](#S3.SS1.p2.1).
- Gao et al. (2023a)
  L. Gao, Z. Dai, P. Pasupat, A. Chen, A. T. Chaganty, Y. Fan, V. Y. Zhao, N. Lao, H. Lee, D. Juan, and K. Guu
  RARR: researching and revising what language models say, using language models.
  In Proceedings of the 61st Annual Meeting of the Association for Computational
  Linguistics (Volume 1: Long Papers), ACL 2023, Toronto, Canada,
  July 9-14, 2023, A. Rogers, J. L. Boyd-Graber, and N. Okazaki (Eds.),
  pp. 16477–16508.
  External Links: [Link](https://doi.org/10.18653/v1/2023.acl-long.910),
  [Document](https://dx.doi.org/10.18653/V1/2023.ACL-LONG.910)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Gao et al. (2023b)
  L. Gao, A. Madaan, S. Zhou, U. Alon, P. Liu, Y. Yang, J. Callan, and G. Neubig
  PAL: program-aided language models.
  In International Conference on Machine Learning, ICML 2023, 23-29 July
  2023, Honolulu, Hawaii, USA, A. Krause, E. Brunskill, K. Cho, B. Engelhardt, S. Sabato, and J. Scarlett (Eds.),
  Proceedings of Machine Learning Research, Vol. 202, pp. 10764–10799.
  External Links: [Link](https://proceedings.mlr.press/v202/gao23f.html)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Graves (2016)
  A. Graves
  Adaptive computation time for recurrent neural networks.
  External Links: 1603.08983,
  [Link](https://arxiv.org/abs/1603.08983)
  Cited by: [§2](#S2.SS0.SSS0.Px1.p2.1).
- Guo et al. (2024)
  Z. Guo, S. Cheng, H. Wang, S. Liang, Y. Qin, P. Li, Z. Liu, M. Sun, and Y. Liu
  StableToolBench: towards stable large-scale benchmarking on tool learning of large language models.
  In Findings of the Association for Computational Linguistics: ACL 2024,
  Bangkok, Thailand, pp. 11143–11156.
  External Links: [Link](https://aclanthology.org/2024.findings-acl.664/)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Kadavath et al. (2022)
  S. Kadavath, T. Conerly, A. Askell, T. Henighan, D. Drain, E. Perez, N. Schiefer, Z. Hatfield-Dodds, N. DasSarma, E. Tran-Johnson, S. Johnston, S. E. Showk, A. Jones, N. Elhage, T. Hume, A. Chen, Y. Bai, S. Bowman, S. Fort, D. Ganguli, D. Hernandez, J. Jacobson, J. Kernion, S. Kravec, L. Lovitt, K. Ndousse, C. Olsson, S. Ringer, D. Amodei, T. Brown, J. Clark, N. Joseph, B. Mann, S. McCandlish, C. Olah, and J. Kaplan
  Language models (mostly) know what they know.
  CoRR abs/2207.05221.
  External Links: [Link](https://doi.org/10.48550/arXiv.2207.05221),
  [Document](https://dx.doi.org/10.48550/ARXIV.2207.05221),
  2207.05221
  Cited by: [§2](#S2.SS0.SSS0.Px1.p2.1).
- Karpas et al. (2022)
  E. Karpas, O. Abend, Y. Belinkov, B. Lenz, O. Lieber, N. Ratner, Y. Shoham, H. Bata, Y. Levine, K. Leyton-Brown, D. Muhlgay, N. Rozen, E. Schwartz, G. Shachaf, S. Shalev-Shwartz, A. Shashua, and M. Tennenholtz
  MRKL systems: A modular, neuro-symbolic architecture that combines large language models, external knowledge sources and discrete reasoning.
  CoRR abs/2205.00445.
  External Links: [Link](https://doi.org/10.48550/arXiv.2205.00445),
  [Document](https://dx.doi.org/10.48550/ARXIV.2205.00445),
  2205.00445
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Kim et al. (2024)
  S. Kim, S. Moon, R. Tabrizi, N. Lee, M. W. Mahoney, K. Keutzer, and A. Gholami
  An llm compiler for parallel function calling.
  In Forty-first International Conference on Machine Learning,
  Cited by: [§2](#S2.SS0.SSS0.Px1.p2.1).
- Koh et al. (2024)
  J. Y. Koh, R. Lo, L. Jang, V. Duvvur, M. C. Lim, P. Huang, G. Neubig, S. Zhou, R. Salakhutdinov, and D. Fried
  VisualWebArena: evaluating multimodal agents on realistic visual web tasks.
  In Proceedings of the 62nd Annual Meeting of the Association for Computational
  Linguistics (Volume 1: Long Papers), ACL 2024, Bangkok, Thailand,
  August 11-16, 2024, L. Ku, A. Martins, and V. Srikumar (Eds.),
  pp. 881–905.
  External Links: [Link](https://doi.org/10.18653/v1/2024.acl-long.50),
  [Document](https://dx.doi.org/10.18653/V1/2024.ACL-LONG.50)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Kojima et al. (2022)
  T. Kojima, S. S. Gu, M. Reid, Y. Matsuo, and Y. Iwasawa
  Large language models are zero-shot reasoners.
  Advances in neural information processing systems 35, pp. 22199–22213.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Li et al. (2023)
  M. Li, Y. Zhao, B. Yu, F. Song, H. Li, H. Yu, Z. Li, F. Huang, and Y. Li
  Api-bank: a comprehensive benchmark for tool-augmented llms.
  In Proceedings of the 2023 conference on empirical methods in natural language processing,
  pp. 3102–3116.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Liu et al. (2018)
  E. Z. Liu, K. Guu, P. Pasupat, T. Shi, and P. Liang
  Reinforcement learning on web interfaces using workflow-guided exploration.
  In 6th International Conference on Learning Representations, ICLR 2018,
  Vancouver, BC, Canada, April 30 - May 3, 2018, Conference Track Proceedings,
  External Links: [Link](https://openreview.net/forum?id=ryTp3f-0-)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Liu et al. (2024)
  X. Liu, H. Yu, H. Zhang, Y. Xu, X. Lei, H. Lai, Y. Gu, H. Ding, K. Men, K. Yang, S. Zhang, X. Deng, A. Zeng, Z. Du, C. Zhang, S. Shen, T. Zhang, Y. Su, H. Sun, M. Huang, Y. Dong, and J. Tang
  AgentBench: evaluating llms as agents.
  In The Twelfth International Conference on Learning Representations,
  ICLR 2024, Vienna, Austria, May 7-11, 2024,
  External Links: [Link](https://openreview.net/forum?id=zAdUB0aCTQ)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Liu et al. (2025)
  X. Liu, T. Zhang, Y. Gu, I. L. Iong, S. XiXuan, Y. Xu, S. Zhang, H. Lai, J. Sun, X. Yang, et al.
  Visualagentbench: towards large multimodal models as visual foundation agents.
  In International Conference on Learning Representations,
  Vol. 2025, pp. 95650–95707.
  Cited by: [§3.1](#S3.SS1.p2.1).
- Meyerson et al. (2025)
  E. Meyerson, G. Paolo, R. Dailey, H. Shahrzad, O. Francon, C. F. Hayes, X. Qiu, B. Hodjat, and R. Miikkulainen
  Solving a million-step llm task with zero errors.
  External Links: 2511.09030,
  [Link](https://arxiv.org/abs/2511.09030)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p3.1).
- Muennighoff et al. (2025)
  N. Muennighoff, Z. Yang, W. Shi, X. L. Li, L. Fei-Fei, H. Hajishirzi, L. Zettlemoyer, P. Liang, E. Candès, and T. B. Hashimoto
  S1: simple test-time scaling.
  In Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing,
  pp. 20286–20332.
  Cited by: [§1](#S1.p5.1).
- Murty et al. (2024)
  S. Murty, C. D. Manning, P. Shaw, M. Joshi, and K. Lee
  BAGEL: bootstrapping agents by guiding exploration with language.
  In Proceedings of the 41st International Conference on Machine Learning, R. Salakhutdinov, Z. Kolter, K. Heller, A. Weller, N. Oliver, J. Scarlett, and F. Berkenkamp (Eds.),
  Proceedings of Machine Learning Research, Vol. 235, pp. 36894–36910.
  External Links: [Link](https://proceedings.mlr.press/v235/murty24a.html)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Naik et al. (2023)
  R. Naik, V. Chandrasekaran, M. Yuksekgonul, H. Palangi, and B. Nushi
  Diversity of thought improves reasoning abilities of llms.
  arXiv preprint arXiv:2310.07088.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Nakano et al. (2021)
  R. Nakano, J. Hilton, S. Balaji, J. Wu, L. Ouyang, C. Kim, C. Hesse, S. Jain, V. Kosaraju, W. Saunders, X. Jiang, K. Cobbe, T. Eloundou, G. Krueger, K. Button, M. Knight, B. Chess, and J. Schulman
  WebGPT: browser-assisted question-answering with human feedback.
  CoRR abs/2112.09332.
  External Links: [Link](https://arxiv.org/abs/2112.09332),
  2112.09332
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Park et al. (2023)
  J. S. Park, J. C. O’Brien, C. J. Cai, M. R. Morris, P. Liang, and M. S. Bernstein
  Generative agents: interactive simulacra of human behavior.
  In Proceedings of the 36th Annual ACM Symposium on User Interface Software
  and Technology, UIST 2023, San Francisco, CA, USA, 29 October 2023-
  1 November 2023, S. Follmer, J. Han, J. Steimle, and N. H. Riche (Eds.),
  pp. 2:1–2:22.
  External Links: [Link](https://doi.org/10.1145/3586183.3606763),
  [Document](https://dx.doi.org/10.1145/3586183.3606763)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Patil et al. (2024)
  S. G. Patil, T. Zhang, X. Wang, and J. E. Gonzalez
  Gorilla: large language model connected with massive apis.
  Advances in Neural Information Processing Systems 37, pp. 126544–126565.
  Cited by: [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Pawlowski et al. (2025)
  P. Pawlowski, K. Zawistowski, W. Lapacz, A. Wiacek, M. Skorupa, S. Postansque, and J. Hoscilowicz
  TinyClick: single-turn agent for empowering GUI automation.
  In 26th Annual Conference of the International Speech Communication Association,
  Interspeech 2025, Rotterdam, The Netherlands, 17-21 August 2025, O. Scharenborg, C. Oertel, and K. Truong (Eds.),
  External Links: [Link](https://doi.org/10.21437/Interspeech.2025-176),
  [Document](https://dx.doi.org/10.21437/INTERSPEECH.2025-176)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Qin et al. (2024)
  Y. Qin, S. Liang, Y. Ye, K. Zhu, L. Yan, Y. Lu, Y. Lin, X. Cong, X. Tang, B. Qian, S. Zhao, L. Hong, R. Tian, R. Xie, J. Zhou, M. Gerstein, D. Li, Z. Liu, and M. Sun
  ToolLLM: facilitating large language models to master 16000+ real-world apis.
  In The Twelfth International Conference on Learning Representations,
  ICLR 2024, Vienna, Austria, May 7-11, 2024,
  External Links: [Link](https://openreview.net/forum?id=dHng2O0Jjr)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Qwen Team (2026)
  Qwen Team
  Qwen3.5: towards native multimodal agents.
  External Links: [Link](https://qwen.ai/blog?id=qwen3.5)
  Cited by: [§N.2](#A14.SS2.p1.1).
- Rawles et al. (2024)
  C. Rawles, S. Clinckemaillie, Y. Chang, J. Waltz, G. Lau, M. Fair, A. Li, W. Bishop, W. Li, F. Campbell-Ajala, et al.
  Androidworld: a dynamic benchmarking environment for autonomous agents.
  arXiv preprint arXiv:2405.14573.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Rawles et al. (2023)
  C. Rawles, A. Li, D. Rodriguez, O. Riva, and T. Lillicrap
  Androidinthewild: a large-scale dataset for android device control.
  Advances in Neural Information Processing Systems 36, pp. 59708–59728.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Schick et al. (2023)
  T. Schick, J. Dwivedi-Yu, R. Dessì, R. Raileanu, M. Lomeli, E. Hambro, L. Zettlemoyer, N. Cancedda, and T. Scialom
  Toolformer: language models can teach themselves to use tools.
  Advances in Neural Information Processing Systems 36, pp. 68539–68551.
  Cited by: [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Shi et al. (2017)
  T. Shi, A. Karpathy, L. Fan, J. Hernandez, and P. Liang
  World of bits: an open-domain platform for web-based agents.
  In Proceedings of the 34th International Conference on Machine Learning,
  ICML 2017, Sydney, NSW, Australia, 6-11 August 2017, D. Precup and Y. W. Teh (Eds.),
  Proceedings of Machine Learning Research, Vol. 70, pp. 3135–3144.
  External Links: [Link](http://proceedings.mlr.press/v70/shi17a.html)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Shinn et al. (2023)
  N. Shinn, F. Cassano, A. Gopinath, K. Narasimhan, and S. Yao
  Reflexion: language agents with verbal reinforcement learning.
  Advances in Neural Information Processing Systems 36, pp. 8634–8652.
  Cited by: [§1](#S1.p2.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Snell et al. (2024)
  C. Snell, J. Lee, K. Xu, and A. Kumar
  Scaling llm test-time compute optimally can be more effective than scaling model parameters.
  arXiv preprint arXiv:2408.03314.
  Cited by: [§1](#S1.p2.1),
  [§2](#S2.SS0.SSS0.Px1.p2.1).
- Turpin et al. (2023)
  M. Turpin, J. Michael, E. Perez, and S. Bowman
  Language models don’t always say what they think: unfaithful explanations in chain-of-thought prompting.
  Advances in Neural Information Processing Systems 36, pp. 74952–74965.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Venkatraman et al. (2025)
  S. Venkatraman, V. Jain, S. Mittal, V. Shah, J. Obando-Ceron, Y. Bengio, B. R. Bartoldson, B. Kailkhura, G. Lajoie, G. Berseth, N. Malkin, and M. Jain
  Recursive self-aggregation unlocks deep thinking in large language models.
  External Links: 2509.26626,
  [Link](https://arxiv.org/abs/2509.26626)
  Cited by: [Appendix G](#A7.p1.1),
  [§1](#S1.p3.1),
  [§1](#S1.p5.1),
  [§3.3](#S3.SS3.SSS0.Px4.p1.1).
- Wan et al. (2024)
  G. Wan, Y. Wu, J. Chen, and S. Li
  Reasoning aware self-consistency: leveraging reasoning paths for efficient llm sampling.
  External Links: 2408.17017,
  [Link](https://arxiv.org/abs/2408.17017)
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Wang et al. (2024)
  G. Wang, Y. Xie, Y. Jiang, A. Mandlekar, C. Xiao, Y. Zhu, L. Fan, and A. Anandkumar
  Voyager: an open-ended embodied agent with large language models.
  Trans. Mach. Learn. Res. 2024.
  External Links: [Link](https://openreview.net/forum?id=ehfRiF0R3a)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Wang et al. (2025)
  W. Wang, Y. Wang, and H. Huang
  Ranked voting based self-consistency of large language models.
  In Findings of the Association for Computational Linguistics: ACL 2025,
  pp. 14410–14426.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Wang et al. (2022)
  X. Wang, J. Wei, D. Schuurmans, Q. Le, E. Chi, S. Narang, A. Chowdhery, and D. Zhou
  Self-consistency improves chain of thought reasoning in language models.
  arXiv preprint arXiv:2203.11171.
  Cited by: [§1](#S1.p2.1),
  [§1](#S1.p3.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1).
- Wei et al. (2022)
  J. Wei, X. Wang, D. Schuurmans, M. Bosma, B. Ichter, F. Xia, E. Chi, Q. V. Le, and D. Zhou
  Chain-of-thought prompting elicits reasoning in large language models.
  Advances in neural information processing systems 35, pp. 24824–24837.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Xie et al. (2024)
  T. Xie, D. Zhang, J. Chen, X. Li, S. Zhao, R. Cao, T. J. Hua, Z. Cheng, D. Shin, F. Lei, et al.
  Osworld: benchmarking multimodal agents for open-ended tasks in real computer environments.
  Advances in Neural Information Processing Systems 37, pp. 52040–52094.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Xu et al. (2023)
  B. Xu, Z. Peng, B. Lei, S. Mukherjee, Y. Liu, and D. Xu
  ReWOO: decoupling reasoning from observations for efficient augmented language models.
  CoRR abs/2305.18323.
  External Links: [Link](https://doi.org/10.48550/arXiv.2305.18323),
  [Document](https://dx.doi.org/10.48550/ARXIV.2305.18323),
  2305.18323
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Xue et al. (2025)
  T. Xue, W. Qi, T. Shi, C. H. Song, B. Gou, D. Song, H. Sun, and Y. Su
  An illusion of progress? assessing the current state of web agents.
  In Second Conference on Language Modeling,
  External Links: [Link](https://openreview.net/forum?id=6jZi4HSs6o)
  Cited by: [2nd item](#A3.I1.i2.p1.1),
  [§3.1](#S3.SS1.p2.1).
- Yao et al. (2022)
  S. Yao, H. Chen, J. Yang, and K. Narasimhan
  Webshop: towards scalable real-world web interaction with grounded language agents.
  Advances in Neural Information Processing Systems 35, pp. 20744–20757.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Yao et al. (2023a)
  S. Yao, D. Yu, J. Zhao, I. Shafran, T. Griffiths, Y. Cao, and K. Narasimhan
  Tree of thoughts: deliberate problem solving with large language models.
  Advances in neural information processing systems 36, pp. 11809–11822.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p2.1).
- Yao et al. (2023b)
  S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. R. Narasimhan, and Y. Cao
  ReAct: synergizing reasoning and acting in language models.
  In The Eleventh International Conference on Learning Representations,
  External Links: [Link](https://openreview.net/forum?id=WE_vluYUL-X)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1),
  [§3.1](#S3.SS1.p1.1).
- Zelikman et al. (2022)
  E. Zelikman, Y. Wu, J. Mu, and N. Goodman
  Star: bootstrapping reasoning with reasoning.
  Advances in Neural Information Processing Systems 35, pp. 15476–15488.
  Cited by: [§1](#S1.p2.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Zhang et al. (2025)
  C. Zhang, Z. Yang, J. Liu, Y. Li, Y. Han, X. Chen, Z. Huang, B. Fu, and G. Yu
  AppAgent: multimodal agents as smartphone users.
  In Proceedings of the 2025 CHI Conference on Human Factors in Computing
  Systems, CHI 2025, YokohamaJapan, 26 April 2025- 1 May 2025, N. Yamashita, V. Evers, K. Yatani, S. X. Ding, B. Lee, M. Chetty, and P. O. T. Dugas (Eds.),
  pp. 70:1–70:20.
  External Links: [Link](https://doi.org/10.1145/3706598.3713600),
  [Document](https://dx.doi.org/10.1145/3706598.3713600)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).
- Zhang et al. (2024)
  L. Zhang, A. Hosseini, H. Bansal, M. Kazemi, A. Kumar, and R. Agarwal
  Generative verifiers: reward modeling as next-token prediction.
  arXiv preprint arXiv:2408.15240.
  Cited by: [§1](#S1.p5.1).
- Zheng et al. (2023)
  L. Zheng, W. Chiang, Y. Sheng, S. Zhuang, Z. Wu, Y. Zhuang, Z. Lin, Z. Li, D. Li, E. Xing, et al.
  Judging llm-as-a-judge with mt-bench and chatbot arena.
  Advances in neural information processing systems 36, pp. 46595–46623.
  Cited by: [§3.1](#S3.SS1.p2.1).
- Zhou et al. (2024a)
  A. Zhou, K. Yan, M. Shlapentokh-Rothman, H. Wang, and Y. Wang
  Language agent tree search unifies reasoning, acting, and planning in language models.
  In Forty-first International Conference on Machine Learning, ICML 2024,
  Vienna, Austria, July 21-27, 2024,
  External Links: [Link](https://openreview.net/forum?id=njwv9BsGHF)
  Cited by: [§2](#S2.SS0.SSS0.Px1.p2.1).
- Zhou et al. (2024b)
  S. Zhou, F. F. Xu, H. Zhu, X. Zhou, R. Lo, A. Sridhar, X. Cheng, T. Ou, Y. Bisk, D. Fried, U. Alon, and G. Neubig
  Webarena: a realistic web environment for building autonomous agents.
  In International Conference on Learning Representations,
  Vol. 2024, pp. 15585–15606.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p2.1).

## Appendix A Agent Design Decisions

### A.1 Action Space

Our agents use a minimal action space with 8 tools designed for web navigation:

- •

  click(element\_id): Click on a DOM element by its unique identifier
- •

  type\_text(element\_id, text): Enter text into an input field without submitting
- •

  hover(element\_id): Hover over an element to reveal tooltips or dropdown menus
- •

  scroll(direction): Scroll the page up or down to reveal more content
- •

  select\_dropdown\_option(element\_id, value): Select an option from a dropdown menu
- •

  search(element\_id, text): Type text and submit (equivalent to type + Enter)
- •

  go\_back(): Navigate to the previous page in browser history
- •

  exit(message): Terminate the episode with a final answer or status message

All element-targeting tools require an element\_id parameter that corresponds to an injected integer id attribute in the DOM. This simplifies element identification compared to CSS selectors or XPaths.

### A.2 Error Handling and Validation

The agent framework includes several error checks that provide feedback during the retry loop:

- •

  MustCallExactlyOneToolCheck: Ensures exactly one function call per step
- •

  InvalidActionSchemaCheck: Validates that function arguments match the expected schema
- •

  ElementMustExistCheck: Verifies that referenced element IDs exist in the current DOM
- •

  MustProvideReasoningCheck: Requires the agent to provide reasoning in the analysis channel
- •

  RepeatingActionLoopCheck: Detects and prevents repeated ineffective actions

When a check fails, the agent receives an error message and has up to 5 retry attempts to produce a valid action.

### A.3 Conversation Format

Each agent turn follows a structured format with the GPT-OSS Harmony interface:

1. 1.

   System message: Establishes agent role and channel usage
2. 2.

   Developer message: Provides detailed instructions and constraints
3. 3.

   User message: Contains the task, current HTML state, and any error feedback
4. 4.

   Assistant response: Analysis in the analysis channel, function call in commentary
5. 5.

   Tool observation: Result of the action with updated HTML state

The conversation history preserves prior reasoning and actions but only includes full HTML in the most recent tool observation to manage context length. This allows the agent to reference its own reasoning trajectory while grounding decisions in the current page state.

## Appendix B Agent Prompts

This section provides the key prompts used in our system components.

### B.1 Base Agent (ReAct Executor)

The base agent uses a channel-based prompting format with separate channels for reasoning (analysis) and action emission (commentary). The system prompt establishes the agent’s role:

> You are a web-execution agent that completes browser tasks by emitting function calls in each step.
>
> How each step works:
>
> - •
>
>   Inputs you’ll see each step: User task (overall goal), prior reasoning and function calls, latest HTML snapshot of current page state.
> - •
>
>   What you must produce: First write analysis (detailed reasoning), then emit exactly one function call in commentary.
>
> Channels: analysis $\rightarrow$ deep reasoning; commentary $\rightarrow$ one function call.

The developer prompt provides detailed instructions for element targeting, function-calling discipline, and recovery from errors:

> Element targeting via numeric id (must-follow):
>
> - •
>
>   The environment injects a special id attribute that is an integer string (e.g., ‘‘15’’).
> - •
>
>   When a function requires an element, supply this integer id exactly as shown in the latest HTML.
> - •
>
>   Do not provide CSS selectors, XPaths, inner text, or made-up ids.
>
> Recovery and loop-avoidance:
>
> - •
>
>   Do not repeat an ineffective action more than once.
> - •
>
>   After an error or no-op, re-analyze the latest HTML before choosing a different action.

### B.2 Semantic Deduplicator

The semantic deduplicator clusters equivalent actions before voting. Its prompt instructs:

> You are a deterministic semantic action deduplicator for a web-navigation system.
>
> Context:
>
> - •
>
>   All inputs in one call are the same action type (TYPE | SEARCH | STOP).
> - •
>
>   All inputs act on the same element target (already checked upstream).
> - •
>
>   Your task: group semantically equivalent actions and pick a representative per group.
>
> What ‘‘equivalent’’ means:
>
> - •
>
>   Same intent after trivial normalization (case, spacing, punctuation) and minor paraphrase/synonymy.
> - •
>
>   Do NOT merge items that change intent/topic (e.g., ‘‘apple store’’ $\neq$ ‘‘apple id login’’).
> - •
>
>   If unsure, keep them separate (prefer false negatives over false positives).
>
> Output format: Clusters: [[rep\_index, other\_idx, ...], [rep\_index2, ...]]

### B.3 Arbiter

The arbiter selects the best action from deduplicated candidates. Its prompt specifies:

> You are an expert web-navigation action arbiter.
>
> You will receive: User intent, previous actions, current page state (cleaned HTML), candidate actions.
>
> Decision Criteria:
>
> 1. 1.
>
>    Progress toward intent: Prefer actions that concretely advance the task
> 2. 2.
>
>    Relevance: Target visible, relevant elements from the current HTML
> 3. 3.
>
>    Avoid repetition: Don’t repeat failed or redundant actions
> 4. 4.
>
>    Context awareness: Consider current page state and previous actions
> 5. 5.
>
>    Feasibility: Ensure the action is executable on the current page
>
> Output Format:
>   
> Thoughts: <reasoning about which action is best>
>   
> Pick: <number from 1 to N>
>   
> Confidence: <decimal from 0.0 to 1.0>

### B.4 External Planner (Plan-and-Act)

For the Plan-and-Act baseline, we use a two-agent system where an external planner generates high-level plans and a separate executor agent follows them. The planner’s system prompt establishes its role:

> You are a web-navigation agent that normally completes browser tasks by thinking in an analysis channel and then emitting exactly one function call (using the provided tools) per step.
>
> In this role, you are acting as the Planner in a two-agent system:
>
> - You see the overall User task, your earlier plans, the executed tool calls, and the latest HTML snapshot (inside the most recent tool observation).
>
> - A separate Executor agent will later read your plan and actually perform the function calls in the browser.
>
> For this planner turn:
>
> - Use the analysis channel for deep, step-by-step reasoning and scratchpad.
>
> - Use the final channel to output a clear, concrete plan for the next actions.
>
> - Do not actually call tools in this turn; only describe how the tools should be used in the future steps.

The developer prompt provides additional guidance on plan quality:

> Planner reasoning guidance:
>
> - •
>
>   Think step by step and deeply in your own natural style.
> - •
>
>   Focus on the next several actions and how to verify progress on the page.
> - •
>
>   Ground your plan in: the user task, prior plans, executed tool calls and their results, the latest HTML.
> - •
>
>   Avoid unsupported assumptions about elements or states that you have not observed.
>
> Recovery and loop-avoidance:
>
> - •
>
>   Do not repeat plans or actions that failed or produced no state change.
> - •
>
>   When something did not work, explicitly include recovery steps: different id, scroll, search, hover, go\_back, or another sensible control.
> - •
>
>   Clarify how the Executor should adapt if the page does not look as expected.
>
> Referencing future actions:
>
> - •
>
>   Refer to tools by their names (for example: click, type\_text, hover, scroll, select\_dropdown\_option, search, go\_back, exit), as they appear in the tool schemas.
> - •
>
>   Describe how the Executor should pick the target element: use the integer id from the latest HTML when known, otherwise reference robust cues (labels, nearby text, attributes, structural context).
> - •
>
>   Predict how the DOM or URL should change after key actions.
> - •
>
>   Specify what the Executor should look for to confirm success vs. failure (new headings, result lists, modals, disappearance of buttons, etc.).

## Appendix C Benchmark Characteristics and LLM-as-Judge Reliability

#### Benchmark difficulty comparison.

Our three evaluation benchmarks differ substantially in task difficulty, trajectory length, and evaluation methodology:

- •

  WebArena-Lite (165 tasks): Uses programmatic success checks that verify specific page states or database entries. Tasks often require longer trajectories with precise multi-step reasoning. Average trajectory length is approximately 8-12 steps, and success rates are generally lower (40-47% in our experiments).
- •

  Online-Mind2Web (300 tasks): Draws from 136 diverse real-world websites (e-commerce, travel, government, etc.) using the Online-Mind2Web dataset ([Xue et al., 2025](#bib.bib60)). It uses an LLM-as-judge evaluation protocol with Qwen3-VL-30B-A3B-Instruct. Also, it features the longest trajectories among our benchmarks (mean 17.4 steps), making it a particularly challenging testbed for long-horizon scaling. Success rates range from 15-32% in our experiments, reflecting both the difficulty of the tasks and the diversity of the web environments.
- •

  GoBrowse-style (341 tasks): Uses an LLM-as-judge evaluation protocol. Tasks tend to be shorter and more straightforward, with average trajectory lengths of 4-6 steps. Success rates are substantially higher (86-90% in our experiments), reflecting easier task specifications.

The three benchmarks span a wide range of difficulty levels: GoBrowse (86–90% baseline) has less room for improvement, Online-Mind2Web (15–22% baseline) provides the most headroom, and WebArena-Lite (38–43% baseline) sits in between. Nevertheless, CATTS achieves consistent gains on all three benchmarks, suggesting the underlying principles generalize across difficulty levels.

#### LLM-as-judge reliability.

Both Online-Mind2Web and GoBrowse use LLM-as-judge evaluation. For GoBrowse, we employ the evaluation protocol introduced in the original work; based on validation studies reported there, the judge achieves approximately 90% agreement with human evaluations on task success determination. For Online-Mind2Web, we use Qwen3-VL-30B-A3B-Instruct as the judge model, following the WebJudge protocol that scores trajectories based on key action points extracted from task descriptions and final screenshots.

While LLM-as-judge evaluation introduces some noise compared to programmatic checks, the consistent improvement pattern observed across all three benchmarks (WebArena-Lite with programmatic evaluation, Online-Mind2Web and GoBrowse with LLM-as-judge) provides confidence in our findings.

## Appendix D Semantic Deduplication Ablation

Table [4](#A4.T4) demonstrates the importance of semantic deduplication for majority voting. Without deduplication (“Before fixes”), increasing the number of candidates $N$ can *hurt* performance on GoBrowse: accuracy drops from 83.3% at $N{=}1$ to 80.1% at $N{=}32$ . This counterintuitive result occurs because semantically equivalent actions (e.g., “N/A” vs. “Not found”, or minor rephrasing of search queries) split votes, causing the majority vote to select incorrect minority actions.

After applying semantic deduplication (“After fixes”), scaling behavior normalizes and performance improves. For ReAct at $N{=}8$ , accuracy increases from 83.3% to 84.5%. The per-website breakdown shows consistent improvements across domains, with particularly large gains on Reddit (84.8% $\rightarrow$ 94.9%) where text input variations are common.

Table 4: Impact of semantic deduplication on GoBrowse. Without deduplication, majority voting degrades with more samples due to vote splitting among semantically equivalent actions. With deduplication, expected scaling behavior is restored and performance improves. This ablation confirms that semantic deduplication is a necessary preprocessing step for meaningful vote aggregation, not a confounding factor.

|  |  | After Deduplication (per-website) |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Setting | Before | Overall | GitLab | Map | Reddit | Shopping | Shop.Admin |
| ReAct |  |  |  |  |  |  |  |
| $N{=}1$ | 83.3% | 83.3% | 84.7% | 76.3% | 84.8% | 89.8% | 82.7% |
| $N{=}8$ | 83.3% | 84.5% | 81.9% | 77.6% | 94.9% | 86.4% | 84.0% |
| $N{=}16$ | 81.8% | 82.1% | 83.3% | 73.7% | 94.8% | 88.1% | 74.7% |
| $N{=}32$ | 80.1% | – | – | – | – | – | – |
| Plan&Act |  |  |  |  |  |  |  |
| $(1,1)$ | 82.4% | 82.4% | – | – | – | – | – |
| $(2,4)$ | 81.2% | 81.2% | – | – | – | – | – |
| $(4,2)$ | 84.2% | 85.3% | 87.5% | 77.6% | 91.4% | 91.5% | 81.3% |

This ablation addresses a potential concern that semantic deduplication artificially inflates results. On the contrary, the data shows that deduplication is *required* for majority voting to function as intended. Without it, the method exhibits behavior where more samples lead to worse outcomes. The improvement from deduplication (e.g., 80.1% $\rightarrow$ 84.5% at $N{=}8$ ) reflects the restoration of correct voting semantics, and is not an artificial boost.

## Appendix E Plan-and-Act Scaling Results

We evaluated Plan-and-Act agents ([Erdogan et al., 2025](#bib.bib8)) with factorized candidate-generation budgets to determine whether non-monotonic scaling is specific to ReAct-style agents or a more general phenomenon.
Let $P$ denote the number of plan candidates sampled and $A$ the number of action candidates per plan, yielding total budget $C=P\times A$ .
Table [5](#A5.T5) presents results on GoBrowse.

Table 5: Plan-and-Act scaling on WebArena-Lite and GoBrowse. Success rates under different budget allocations $(P,A)$ with total compute $C=P\times A$ . Non-monotonic scaling is evident on both benchmarks: on WebArena-Lite, $(2,4)$ achieves the best result (43.2%) but $(4,4)$ drops to 43.0% despite 2 $\times$ the budget; on GoBrowse, the baseline $(1,1)$ achieves 83.3%, while $(2,4)$ with $8\times$ the budget drops to 80.6%. This confirms that the non-monotonic scaling phenomenon affects multiple agent architectures, not just ReAct, strengthening the motivation for dynamic compute allocation.

| $(P,A)$ | Budget $C$ | WA | GB | Tokens |
| --- | --- | --- | --- | --- |
| $(1,1)$ | 1 | 38.8% | 83.3% | 104K |
| $(2,4)$ | 8 | 43.2% | 80.6% | 731K |
| $(4,4)$ | 16 | 43.0% | 81.5% | 1.4M |

The results mirror what we observe with ReAct: scaling up compute via more samples does not reliably improve performance.
In fact, performance *decreases* from 83.3% to 80.6% when moving from budget $C{=}1$ to $C{=}8$ .
This establishes that the non-monotonic scaling phenomenon affects multiple agent architectures, providing additional motivation for the dynamic compute allocation approach developed in Section [4.2](#S4.SS2).

## Appendix F Complete Arbiter Scaling Results

Table [6](#A6.T6) presents the complete arbiter scaling results on WebArena-Lite across all combinations of candidate count $N\in\{3,5,10,20\}$ and arbiter scaling factor $K\in\{1,5,10,20\}$ . Success rates are averaged over 3 independent runs.

Table 6: Complete arbiter scaling on WebArena-Lite. Success rates for all $(N,K)$ configurations, averaged over 3 runs. Best result for each $N$ is bolded. The optimal arbiter scaling factor $K$ varies by candidate count $N$ : small $N$ benefits from high $K$ ( $N{=}3$ , $K{=}20$ : 45.7%), while larger $N$ prefers moderate $K$ ( $N{=}10$ , $K{=}5$ : 44.6%). No single $(N,K)$ dominates, and gains from arbiter scaling plateau or decline beyond optimal $K$ . This non-monotonic behavior motivates selective arbiter use via dynamic gating rather than uniform high- $K$ allocation.

|  | Arbiter Scaling Factor $K$ |  |  |  |
| --- | --- | --- | --- | --- |
| Candidates $N$ | $K{=}1$ | $K{=}5$ | $K{=}10$ | $K{=}20$ |
| $N{=}3$ | 43.0% | 41.2% | 43.4% | 45.7% |
| $N{=}5$ | 42.8% | 44.2% | 44.6% | 42.0% |
| $N{=}10$ | 44.0% | 44.6% | 42.0% | 43.0% |
| $N{=}20$ | 43.2% | 42.8% | 44.0% | 43.6% |

## Appendix G RSA and PlanRSA Full Results

We evaluated Recursive Self-Aggregation (RSA) ([Venkatraman et al., 2025](#bib.bib52)) as an alternative to single-round arbitration. RSA iteratively refines candidates over $T$ rounds, with $K$ aggregation calls per round.
Building on top of Plan-and-Act, we combine it with RSA to create PlanRSA, where we apply RSA at the plan level.
Table [7](#A7.T7) presents results across all configurations tested on WebArena-Lite.

Table 7: Full RSA and PlanRSA results on WebArena-Lite. RSA applies iterative refinement at the action level, while PlanRSA applies it at the plan level for Plan-and-Act agents. Despite substantially higher compute costs (up to 80 LLM calls per step), RSA achieves at best comparable performance to single-round arbitration. PlanRSA underperforms all baselines, suggesting that aggregation noise accumulates more severely at higher levels of abstraction.

| Method | $N/P$ | $K$ | $T$ | Success | Calls/Step |
| --- | --- | --- | --- | --- | --- |
| Baselines |  |  |  |  |  |
| Majority Vote | 10 | – | – | 43.2% | 10 |
| Arbiter ( $K{=}1$ ) | 10 | 1 | – | 44.0% | 11 |
| CATTS (entropy, best) | 10 | 1 | – | 47.9% | $\sim$ 7 |
| RSA (action-level aggregation) |  |  |  |  |  |
| RSA | 8 | 2 | 2 | 41.0% | 24 |
| RSA | 8 | 2 | 4 | 41.0% | 40 |
| RSA | 16 | 4 | 2 | 42.0% | 48 |
| RSA | 16 | 4 | 4 | 43.6% | 80 |
| PlanRSA (plan-level aggregation) |  |  |  |  |  |
| PlanRSA (arbiter select) | 8 | 4 | 2 | 35.2% | 40 |
| PlanRSA (random select) | 8 | 4 | 2 | 35.2% | 40 |

#### Analysis.

RSA with $N{=}16,K{=}4,T{=}4$ achieves 43.6%, comparable to single-round arbitration (44.0%) but at ${\sim}7\times$ the compute cost per step. The marginal benefit of additional aggregation rounds is minimal: increasing $T$ from 2 to 4 improves performance by only 0–1.6% while roughly doubling compute. We hypothesize that RSA’s iterative refinement, designed for single-shot reasoning tasks where solutions can be progressively improved, does not transfer well to per-step action selection where the “correct” answer depends heavily on environmental context that cannot be improved through reasoning alone.

PlanRSA performs substantially worse than all baselines (35.2% vs. 43.2% for majority vote). Notably, the selection method within PlanRSA (arbiter vs. random) makes no difference, suggesting the bottleneck is the plan aggregation process itself rather than final selection. This may reflect error accumulation: aggregating plans introduces noise at a higher level of abstraction, and errors in plan formulation propagate to all downstream actions.

## Appendix H Threshold Sensitivity Analysis

Tables [8(a)](#A8.T8.st1) and [8(b)](#A8.T8.st2) present the full threshold sweep results for CATTS on WebArena-Lite across different values of $N\in\{3,5,10,20\}$ . Both entropy-gated and margin-gated variants show robust performance across a range of thresholds $\tau\in\{0.2,0.3,\ldots,0.8\}$ . The best-performing threshold for each $N$ is highlighted in bold.

Table 8: CATTS threshold sweep on WebArena-Lite. Success rates across different candidate counts ( $N$ ) and threshold values ( $\tau$ ) for entropy-gated (left) and margin-gated (right) variants. Best-performing threshold for each $N$ is bolded. Baseline majority vote success rates: $N{=}3$ : 40.2%, $N{=}5$ : 42.8%, $N{=}10$ : 43.2%, $N{=}20$ : 43.8%. Most configurations outperform their respective baselines, demonstrating robustness to threshold choice.

(a) Entropy-gated

| $\tau$ | $N{=}3$ | $N{=}5$ | $N{=}10$ | $N{=}20$ |
| --- | --- | --- | --- | --- |
| 0.2 | 44.2 | 43.0 | 47.9 | 43.6 |
| 0.3 | 43.0 | 44.2 | 46.7 | 44.2 |
| 0.4 | 46.7 | 45.5 | 44.2 | 46.1 |
| 0.5 | 43.0 | 45.5 | 45.5 | 40.6 |
| 0.6 | 44.2 | 45.5 | 46.1 | 43.0 |
| 0.7 | 44.2 | 44.2 | 47.3 | 47.3 |
| 0.8 | 42.4 | 45.5 | 45.5 | 42.4 |

(b) Margin-gated

| $\tau$ | $N{=}3$ | $N{=}5$ | $N{=}10$ | $N{=}20$ |
| --- | --- | --- | --- | --- |
| 0.2 | 44.8 | 45.5 | 45.5 | 44.8 |
| 0.3 | 43.6 | 45.5 | 42.4 | 46.7 |
| 0.4 | 46.1 | 45.5 | 46.1 | 44.2 |
| 0.5 | 43.0 | 47.9 | 44.8 | 44.2 |
| 0.6 | 43.6 | 44.2 | 44.2 | 46.7 |
| 0.7 | 44.2 | 44.2 | 44.2 | 47.9 |
| 0.8 | 47.3 | 46.1 | 46.1 | 44.2 |

The results demonstrate that CATTS is relatively robust to the choice of threshold across different values of $N$ . For entropy-gated CATTS, the best thresholds vary by $N$ but most configurations outperform the majority vote baseline. For margin-gated CATTS, similar robustness is observed with peak performance typically at $\tau\in\{0.4,0.5,0.7,0.8\}$ . In practice, a default threshold of $\tau=0.5$ provides good performance across both benchmarks without extensive tuning.

## Appendix I Threshold Calibration from Limited Data

A natural practical question is: *how should a practitioner select $\tau$ when deploying CATTS in a new setting?*
We address this through comprehensive bootstrap calibration experiments ( $R{=}200$ stratified rounds) across WebArena-Lite (165 tasks, 5 websites) and Online-Mind2Web (300 tasks), using both entropy-based and margin-based gating at $N{=}10$ .

### I.1 Methodology

We use a stratified bootstrap procedure to simulate realistic calibration:

1. 1.

   Split. Randomly draw $X\%$ of tasks (stratified by website where applicable) as the calibration set.
2. 2.

   Calibrate. On the calibration set, evaluate each candidate $\tau\in\{0.2,0.3,\ldots,0.8\}$ and select $\hat{\tau}=\arg\max_{\tau}\text{acc}_{\text{cal}}(\tau)$ .
3. 3.

   Evaluate. Apply $\hat{\tau}$ to the *entire benchmark* and measure $\text{acc}_{\text{full}}(\hat{\tau})$ .
4. 4.

   Oracle comparison. The oracle threshold $\tau^{*}=\arg\max_{\tau}\text{acc}_{\text{full}}(\tau)$ is computed on the full benchmark.
5. 5.

   Regret. $\text{regret}=\text{acc}_{\text{full}}(\tau^{*})-\text{acc}_{\text{full}}(\hat{\tau})$ .

We repeat this $R{=}200$ times for each combination of calibration fraction $X\in\{10\%,15\%,20\%,25\%,30\%,40\%,50\%\}$ and gating method (entropy, margin).
The regret measures how much accuracy is lost by using the calibrated $\hat{\tau}$ instead of the full-benchmark oracle.

### I.2 Universal Calibration Results

In *universal calibration*, we select a single $\hat{\tau}$ that applies to all tasks.
Table [9](#A9.T9) presents results on both benchmarks.

Table 9: Universal calibration results ( $N{=}10$ , 200 bootstrap rounds). “Agreement” is the fraction of rounds where $\hat{\tau}$ matches the oracle $\tau^{*}$ . “Regret” is the mean accuracy gap (%). Even at $X{=}10\%$ ( ${\sim}16$ tasks on WA-Lite), regret is ${\leq}1.1\%$ across all settings. Best results (at $X{=}50\%$ ) are highlighted.

|  | WebArena-Lite |  |  |  | Online-Mind2Web |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | Entropy |  | Margin |  | Entropy |  | Margin |  |
| $X$ | Agree. | Regret | Agree. | Regret | Agree. | Regret | Agree. | Regret |
| 10% | 42% | 0.99% | 18% | 1.01% | 18% | 1.08% | 16% | 1.81% |
| 15% | 35% | 1.12% | 24% | 0.98% | 26% | 0.76% | 14% | 1.63% |
| 20% | 40% | 0.99% | 22% | 0.98% | 22% | 0.92% | 17% | 1.12% |
| 25% | 36% | 1.08% | 26% | 0.87% | 29% | 0.63% | 19% | 1.23% |
| 30% | 40% | 0.92% | 25% | 0.77% | 22% | 0.69% | 28% | 0.81% |
| 40% | 44% | 0.91% | 27% | 0.66% | 26% | 0.59% | 18% | 0.88% |
| 50% | 46% | 0.77% | 28% | 0.55% | 25% | 0.49% | 35% | 0.56% |

Several patterns emerge:
(1) Regret is remarkably small. Even at $X{=}10\%$ ( ${\sim}16$ tasks on WebArena-Lite, ${\sim}30$ tasks on Mind2Web), regret is ${\leq}1.1\%$ for entropy gating across both benchmarks. Since CATTS typically improves over majority voting by 3–12%, losing ${\sim}1\%$ to imperfect calibration preserves the vast majority of the benefit.
(2) Regret decreases with more data. WA-Lite margin regret decreases from 1.01% to 0.55% as $X$ grows from 10% to 50%.
(3) Low agreement does not imply high regret. Agreement rates are moderate (25–46% at $X{=}50\%$ ), yet regret is minimal because the accuracy landscape is flat near the optimum.

### I.3 Why Calibration Works: Diagnostic Analysis

The coexistence of moderate agreement and very low regret is explained by the *flat accuracy landscape* near the optimum.
The threshold selection variance $\sigma_{\tau}$ remains around 0.17–0.22 across all calibration fractions, confirming that the calibration procedure does not converge to a single threshold even with abundant data, because multiple thresholds are genuinely near-optimal.
For example, on WebArena-Lite entropy ( $N{=}10$ ), the oracle is $\tau{=}0.2$ (47.9%), but $\tau{=}0.3$ achieves 46.7% and $\tau{=}0.7$ achieves 47.3%, so selecting any of these “wrong” thresholds costs at most 1.2%.

Figure [5](#A9.F5) provides a direct visualization of how regret decreases with more calibration data across both benchmarks.

![](images/26_CATTS/regret_vs_train_fraction.svg)


Figure 5: Calibration regret vs. calibration fraction ( $N{=}10$ , 200 rounds). All curves start at ${\leq}1.1\%$ even at $X{=}10\%$ and decrease monotonically. 15–20% of tasks suffices for effective calibration.

### I.4 Per-Website Threshold Calibration

Universal calibration selects a single $\hat{\tau}$ for all tasks. *Per-website calibration* selects a separate $\hat{\tau}_{w}$ for each website $w$ , gaining flexibility but losing statistical power (smaller per-website subsets).

Table [10](#A9.T10) compares universal and per-website calibration for both gating methods. Notably, per-website calibration can achieve *negative* regret, meaning it *exceeds* the global oracle accuracy by exploiting website-specific threshold preferences.

Table 10: Universal vs. per-website calibration ( $N{=}10$ ). Green cells indicate per-website regret that is negative (exceeds the global oracle). “PW Adv.” is the advantage of per-website over universal calibration. All values in %.

(a) Entropy gating

|  | WebArena-Lite |  |  | GoBrowse |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| $X$ | Univ. | PW Regret | PW Adv. | Univ. | PW Regret | PW Adv. |
| 10% | 0.99 | $-$ 0.26 | +1.25 | 1.04 | 0.44 | +0.60 |
| 20% | 0.99 | $-$ 0.61 | +1.60 | 0.92 | $-$ 0.26 | +1.18 |
| 30% | 0.92 | $-$ 1.23 | +2.15 | 0.80 | $-$ 0.63 | +1.44 |
| 50% | 0.77 | $-$ 2.14 | +2.91 | 0.77 | $-$ 1.41 | +2.18 |

(b) Margin gating

|  | WebArena-Lite |  |  | GoBrowse |  |  |
| --- | --- | --- | --- | --- | --- | --- |
| $X$ | Univ. | PW Regret | PW Adv. | Univ. | PW Regret | PW Adv. |
| 10% | 1.01 | 0.05 | +0.97 | 1.13 | 0.41 | +0.73 |
| 20% | 0.98 | $-$ 0.21 | +1.19 | 1.01 | $-$ 0.27 | +1.28 |
| 30% | 0.77 | $-$ 0.77 | +1.54 | 0.85 | $-$ 0.52 | +1.37 |
| 50% | 0.55 | $-$ 1.60 | +2.15 | 0.68 | $-$ 1.24 | +1.91 |

Figure [6](#A9.F6) visualizes the comparison across all settings.

![](images/26_CATTS/universal_vs_perwebsite_webarena_lite_entropy_threshold.svg)


(a) WA-Lite, entropy.

![](images/26_CATTS/universal_vs_perwebsite_gobrowse_entropy_threshold.svg)


(b) GoBrowse, entropy.

![](images/26_CATTS/universal_vs_perwebsite_webarena_lite_margin_threshold.svg)


(c) WA-Lite, margin.

![](images/26_CATTS/universal_vs_perwebsite_gobrowse_margin_threshold.svg)


(d) GoBrowse, margin.

Figure 6: Universal vs. per-website calibration regret. Per-website (orange) consistently achieves lower regret than universal (blue), with the gap widening at larger $X$ . Per-website regret frequently turns negative, meaning it exceeds the global oracle.

### I.5 Summary and Practical Guidance

1. 1.

   Universal calibration is remarkably effective. With as little as 10% of tasks, regret is ${\leq}1.1\%$ across all settings. The flat accuracy landscape means even imprecise threshold selection works.
2. 2.

   Per-website calibration exceeds the global oracle. At $X{\geq}15$ – $20\%$ , per-website regret turns negative, exploiting website-specific threshold preferences. The advantage grows with $X$ , reaching $+2.91\%$ for WA-Lite entropy at $X{=}50\%$ .
3. 3.

   Practical recommendation:
   (a) With no data, use $\tau{=}0.5$ as a robust default;
   (b) With 10–20% of tasks, run universal calibration ( ${\leq}1.1\%$ regret);
   (c) With 20%+ tasks and website labels, use per-website calibration to exceed the oracle.

## Appendix J Vote Distribution Analysis

Figure [7](#A10.F7) presents the detailed analysis of vote distributions across all decision steps from our experiments. This analysis provides empirical support for the two-regime interpretation discussed in Section [4.3](#S4.SS3).

![](images/26_CATTS/figure_5a_vote_distribution.svg)


Figure 7: Vote distribution profiles across all steps. Histograms aggregated over all decision steps from $N{=}10$ experiments on WebArena-Lite. (A) Top-1 probability distribution shows strong right skew: ${\sim}42\%$ of steps have near-deterministic consensus (top-1 probability ${>}0.9$ ), and mean top-1 probability is 0.762. This indicates many steps fall into a redundancy regime where additional candidates duplicate the dominant action. (B) Normalized entropy distribution is bimodal (mean 0.474): ${\sim}40\%$ of steps have zero entropy (perfect consensus), while ${\sim}49\%$ of steps have entropy ${>}0.6$ , identifying contentious steps where arbitration is most valuable. These profiles motivate dynamic gating: allocate extra compute to high-entropy steps while preserving consensus elsewhere.

The distributions reveal several key patterns: (1) Right-skewed top-1 probability: Approximately 42% of steps exhibit near-deterministic consensus with top-1 probability exceeding 0.9, indicating that many decisions fall into a redundant regime. (2) Bimodal entropy: The normalized entropy distribution is bimodal (mean 0.474), with approximately 40% of steps at zero entropy (perfect consensus) and approximately 49% showing entropy above 0.6. (3) Two-regime interpretation: The distributions strongly support the two-regime interpretation from Section [4.3](#S4.SS3): a large fraction of steps are routine (high consensus) while a comparable fraction are contentious (genuine uncertainty), motivating dynamic compute allocation.

These empirical profiles directly motivate the dynamic gating approach in CATTS: by allocating extra arbitration compute to the high-entropy tail while preserving consensus on the dominant low-entropy steps, we can improve the accuracy–compute tradeoff without the overhead of uniform scaling.

## Appendix K Failure Mode Examples

This section provides a concrete example from our experiments where the arbiter’s override of high-consensus decisions led to task failure. This example illustrates the core failure mode discussed in Section [4](#S4): when the vote distribution already exhibits strong agreement (high margin $\Delta_{t}$ , low entropy $H_{t}$ ), arbitration introduces override risk rather than improving decision quality.

Figure [8](#A11.F8) presents an example from a WebArena-Lite task requiring the agent to find “Meat Substitutes” in an online grocery store. At a critical decision point, the sampled candidates show 90% consensus for “Scroll Down”, the correct action, since the target category lies below the current viewport. However, the arbiter overrides this strong consensus and selects “Click Pantry Staples,” a minority action that navigates to an incorrect category and derails the trajectory.

This failure pattern is particularly instructive because the vote distribution provides a clear signal: with 9 out of 10 candidates agreeing on “Scroll,” the normalized entropy is low ( $H_{t}\approx 0.3$ ) and the margin is high ( $\Delta_{t}=0.8$ ). Under CATTS, this step would be classified as high-confidence and the arbiter would be bypassed entirely, preserving the consensus action. The example thus demonstrates both (i) why uniform arbitration can be harmful, and (ii) how vote-derived uncertainty enables selective intervention.

![Refer to caption](images/26_CATTS/figure-2-v3.png)


Figure 8: Arbiter failure on high-consensus step. Example trajectory where the sampled candidates exhibit strong consensus (e.g., 9/10 votes for one action), but the arbiter overrides the majority and selects a minority action, leading to task failure. This illustrates that arbitration can be harmful when vote-derived uncertainty is already low.

## Appendix L DeepConf Full Results

Table [11](#A12.T11) presents the full DeepConf results across three confidence variants and varying candidate counts $N$ on both benchmarks.

Table 11: DeepConf variants on WebArena-Lite and Online-Mind2Web. Unlike CATTS, DeepConf requires access to token-level log probabilities.

|  |  | WebArena-Lite |  | Online-Mind2Web |  |
| --- | --- | --- | --- | --- | --- |
| Variant | $N$ | Success | Tokens | Success | Tokens |
| Avg. Trace | 3 | 40.2% | 262K | 24.7% | 465K |
| 5 | 42.0% | 408K | 20.7% | 834K |  |
| 10 | 43.8% | 828K | 20.0% | 1.7M |  |
| Tail | 3 | 38.8% | 252K | 22.3% | 458K |
| 5 | 40.4% | 408K | 19.3% | 820K |  |
| 10 | 42.4% | 813K | 18.7% | 1.6M |  |
| Bottom % | 3 | 40.6% | 254K | 23.0% | 470K |
| 5 | 42.6% | 409K | 19.7% | 842K |  |
| 10 | 40.6% | 835K | 18.3% | 1.7M |  |

## Appendix M GoBrowse Results

We additionally evaluate on 341 tasks sampled from GoBrowse ([Gandhi and Neubig, 2025](#bib.bib51)), using an LLM-as-a-judge evaluation with Qwen3-VL-30B-A3B-Instruct. GoBrowse tasks tend to be shorter (4–6 steps on average) and easier (86–90% baselines), providing a complementary evaluation to the harder WebArena-Lite and Online-Mind2Web benchmarks. All results are averaged across 3 runs.

### M.1 Static Scaling with Majority Vote

Table [12](#A13.T12) shows that GoBrowse exhibits similar diminishing returns to WebArena-Lite: scaling from $N{=}1$ to $N{=}10$ provides modest gains, while $N{=}20$ shows no further improvement.

Table 12: Static scaling on GoBrowse. Majority voting success rates under varying $N$ .

| Budget | Success | Tokens |
| --- | --- | --- |
| $N{=}1$ | 86.9% | 47K |
| $N{=}5$ | 87.8% | 249K |
| $N{=}10$ | 88.0% | 481K |
| $N{=}20$ | 87.8% | 995K |

### M.2 Arbiter Scaling

Table [13](#A13.T13) shows arbiter scaling results on GoBrowse at $N{=}5$ . Unlike WebArena-Lite where $K{=}20$ degrades, GoBrowse shows steady improvement with increasing $K$ .

Table 13: Arbiter scaling on GoBrowse ( $N{=}5$ ).

| Method | Success | Tokens |
| --- | --- | --- |
| Majority vote ( $N{=}5$ ) | 87.8% | 249K |
| Arbiter ( $K{=}1$ ) | 88.6% | 227K |
| Arbiter scaling ( $K{=}5$ ) | 88.2% | 351K |
| Arbiter scaling ( $K{=}10$ ) | 88.7% | 541K |
| Arbiter scaling ( $K{=}20$ ) | 89.6% | 733K |

### M.3 DeepConf on GoBrowse

Table [14](#A13.T14) presents DeepConf results. Average trace at $N{=}20$ achieves 90.3%, the strongest DeepConf result across all three benchmarks, suggesting that token-level confidence signals are more effective on shorter, easier trajectories.

Table 14: DeepConf variants on GoBrowse.

| Variant | $N$ | Success | Tokens |
| --- | --- | --- | --- |
| Avg. Trace | 3 | 87.7% | 134K |
| 5 | 89.4% | 235K |  |
| 10 | 89.1% | 475K |  |
| 20 | 90.3% | 968K |  |
| Tail | 3 | 86.8% | 138K |
| 5 | 88.3% | 230K |  |
| 10 | 86.6% | 452K |  |
| 20 | 88.1% | 951K |  |
| Bottom % | 3 | 88.4% | 145K |
| 5 | 88.1% | 240K |  |
| 10 | 89.0% | 463K |  |
| 20 | 88.2% | 973K |  |

### M.4 CATTS on GoBrowse

Table [15](#A13.T15) presents CATTS results at $N{=}10$ . Both entropy-gated and margin-gated variants improve over majority voting (88.0%) while using fewer tokens. Margin-gated CATTS achieves 90.4% with only 372K tokens (23% fewer than majority voting at 481K).

Table 15: CATTS results on GoBrowse ( $N{=}10$ ).

| Method | Success | Tokens |
| --- | --- | --- |
| Majority vote | 88.0% | 481K |
| Always-arbitrate | 88.3% | 443K |
| CATTS ( $H$ , $\tau{=}0.5$ ) | 90.2% | 422K |
| CATTS ( $\Delta$ , $\tau{=}0.5$ ) | 90.4% | 372K |

### M.5 GoBrowse Threshold Sweep

Table [16(b)](#A13.T16.st2) presents the full threshold sweep for CATTS on GoBrowse. Performance is robust across thresholds, with most configurations outperforming the 88.0% majority voting baseline.

Table 16: CATTS threshold sweep on GoBrowse. Success rates (%) for entropy-gated (left) and margin-gated (right) at $N{=}10$ .

(a) Entropy-gated

| $\tau$ | $N{=}3$ | $N{=}5$ | $N{=}10$ | $N{=}20$ |
| --- | --- | --- | --- | --- |
| 0.2 | 88.6 | 88.9 | 90.3 | 89.4 |
| 0.3 | 88.9 | 90.3 | 90.3 | 88.9 |
| 0.4 | 88.0 | 89.7 | 89.7 | 89.7 |
| 0.5 | 88.3 | 89.7 | 91.2 | 86.8 |
| 0.6 | 88.7 | 89.3 | 87.7 | 88.9 |
| 0.7 | 88.6 | 87.7 | 90.0 | 88.0 |
| 0.8 | 88.9 | 89.4 | 89.1 | 90.9 |

(b) Margin-gated

| $\tau$ | $N{=}3$ | $N{=}5$ | $N{=}10$ | $N{=}20$ |
| --- | --- | --- | --- | --- |
| 0.2 | 90.0 | 88.3 | 89.7 | 90.3 |
| 0.3 | 88.3 | 88.6 | 89.1 | 90.6 |
| 0.4 | 88.6 | 89.4 | 88.3 | 89.6 |
| 0.5 | 88.3 | 90.0 | 90.6 | 88.3 |
| 0.6 | 91.2 | 88.3 | 89.7 | 86.8 |
| 0.7 | 89.7 | 88.9 | 88.9 | 88.0 |
| 0.8 | 89.4 | 89.9 | 89.7 | 90.6 |

## Appendix N Evaluation on Additional Model Families

This section provides additional evaluations of CATTS across different foundation model families to demonstrate the generalizability of our test-time scaling approach.

### N.1 Gemini 3.1 Flash Lite

We also conducted additional experiments to show the stability of our method across model families by evaluating several high scoring methods on the Gemini 3.1 Flash Lite model. We ran these experiments on WebArena-Lite to directly compare scaling behavior across foundation models, with results averaged across three runs. Gemini 3.1 Flash Lite was used with the high reasoning setting.

Table 17: Gemini 3.1 Flash Lite Results Summary (WebArena-Lite). Performance and token consumption across different test-time scaling methods. CATTS maintains its efficiency and performance advantages on the Gemini model family.

| $N$ | Method | Success Rate | Avg. Tokens Per Task |
| --- | --- | --- | --- |
| 5 | Majority Vote | 42.2% | 420K |
| 5 | Arbiter ( $K{=}1$ ) | 43.2% | 415K |
| 5 | CATTS ( $\Delta$ , $\tau{=}0.5$ ) | 44.0% | 410K |
| 5 | CATTS ( $\Delta$ , $\tau{=}0.8$ ) | 43.2% | 412K |

Key observations on Gemini 3.1 Flash Lite include:

- •

  The core advantages of CATTS remain consistent when shifting from gpt-oss to Gemini.
- •

  At $N{=}5$ , CATTS ( $\Delta$ , $\tau{=}0.5$ ) achieves a 44.0% success rate, outperforming both standard Majority Vote (42.2%) and the Arbiter baseline (43.2%), all while consuming fewer average tokens per task (410K vs. 420K and 415K).

### N.2 Qwen3.5-122B-A10B

To further demonstrate the generalizability of CATTS, we evaluated on Qwen3.5-122B-A10B ([Qwen Team, 2026](#bib.bib61)) served via vLLM with native tool calling and reasoning support. We ran these experiments on WebArena-Lite using the same evaluation protocol.

Table 18: Qwen3.5-122B-A10B Results Summary (WebArena-Lite). Performance across different test-time scaling methods. CATTS ( $\Delta$ ) improves over both Majority Vote and Arbiter baselines.

| $N$ | Method | Success Rate | Avg. Tokens Per Task |
| --- | --- | --- | --- |
| 1 | Pass@1 | 34.5% | 106K |
| 3 | Majority Vote | 33.9% | 316K |
| 3 | Arbiter ( $K{=}1$ ) | 36.4% | 385K |
| 5 | Majority Vote | 34.5% | 525K |
| 5 | Arbiter ( $K{=}1$ ) | 35.8% | 569K |
| 5 | CATTS ( $\Delta$ , $\tau{=}0.2$ ) | 38.8% | 483K |
| 5 | CATTS ( $\Delta$ , $\tau{=}0.5$ ) | 40.6% | 544K |
| 5 | CATTS ( $\Delta$ , $\tau{=}0.7$ ) | 40.6% | 537K |

Key observations on Qwen3.5-122B-A10B include:

- •

  CATTS demonstrates consistent improvements on WebArena-Lite, confirming that the method is not specific to gpt-oss.
- •

  At $N{=}5$ , CATTS ( $\Delta$ , $\tau{=}0.5$ ) achieves a 40.6% success rate, a +6.1 percentage point improvement over Majority Vote (34.5%) and +4.8 over the Arbiter baseline (35.8%).
- •

  Standard Majority Vote shows no scaling benefit on this model (34.5% at both $N{=}1$ and $N{=}5$ ), while CATTS successfully extracts gains from additional compute, highlighting the value of confusion-aware selection.

## Appendix O LLM Usage Disclosure

We used AI tools to assist with grammar, plotting code, and LaTeX editing. All research decisions and analysis are our own.
