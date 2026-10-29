---
title: "Lost in Recovery: Demystifying Recovery Behavior of Computer-Use Agents via Goal-Oriented Action Replay"
arxiv_html: https://arxiv.org/html/2610.27954v1
downloaded: 2026-10-29
converted: arxiv LaTeXML HTML -> Markdown（本地图片 + alttext 公式还原）
---

# Lost in Recovery: Demystifying Recovery Behavior of Computer-Use Agents via Goal-Oriented Action Replay

- **Byeonghun Bang** · KAIST
- **Sangwoo Park 1 1 footnotemark: 1** · KAIST
- **Jinheon Baek** · KAIST
- **Kangsan Kim** · KAIST
- **Youngwan Lee   Sung Ju Hwang** · KAIST; ETRI; DeepAuto.ai · {bh.bang, jackson0530, jinheon.baek, kangsan.kim, sungju.hwang}@kaist.ac.kr yw.lee@etri.re.kr

###### Abstract

Recent advances in large (vision) language models have enabled computer-use agents that automate digital workflows via fine-grained keyboard and mouse operations. However, such agents remain fragile in long-horizon settings, where errors accumulate and executed actions leave unintended side effects, making the ability to recover from failures critical. Yet, existing remedies remain inadequate: environment resets are infeasible in proprietary settings, action replay is prohibitively expensive over long horizons, and API-based rollback is limited to web environments, leaving model-based recovery largely unexplored. To address this gap, we present ReTrace, a scalable evaluation framework for systematically studying recovery behavior in computer-use agents. We formalize Transition-Consistent Recovery: identical downstream actions from the recovered and target states must yield identical outcomes. We operationalize this criterion through goal-oriented action replay following controlled error injection. Using ReTrace, we present the first systematic study of autonomous, model-based recovery, revealing that (i) ideal recovery can unlock model’s latent task completion capabilities, (ii) current computer-use agents fail to exploit their latent recovery capabilities, and (iii) accurate model-based recovery yields measurable end-to-end gains. Together, these findings establish recovery as a fundamental capability for building reliable computer-use agents. Our code and dataset is available at <https://github.com/BangProx/ReTRACE>.

## 1 Introduction

The digital computing environment has become the primary interface through which users interact with software, supporting a wide spectrum of tasks ranging from simple actions (e.g., website logins) to complex workflows (document editing). Recent advances in large (vision) language models ([Bai et al., 2025](#bib.bib51); [Singh et al., 2025](#bib.bib13); [Guo et al., 2025](#bib.bib59); [Anthropic, 2026](#bib.bib37)) have made it possible to automate such workflows through *computer-use agents*, which act in digital environments via fine-grained keyboard and mouse inputs ([Gur et al., 2023](#bib.bib31); [Furuta et al., 2023](#bib.bib52); [Sager et al., 2025](#bib.bib9)).

![Refer to caption](images/25_ReTRACE/concept_figure.png)


Figure 1: Comparison of error-handling strategies in computer-use agents. (A) Reflection proceeds from the erroneous state, (B) rollback requires often-infeasible environment resets, while (C) recovery restores a prior intact state and resumes the task.

However, computer-use agents remain fragile in long-horizon and sophisticated tasks, where early mistakes accumulate and propagate across subsequent steps ([Wang et al., 2026a](#bib.bib11)), and where executed actions may leave unintended side effects that should not have occurred (e.g., an agent organizing a directory may complete the task but silently overwrite files that the user wanted to keep). As a result, the ability to revert the environment to a previously intact state is critical for reliable operation. To address this, prior work explores two directions: inducing self-reflective behaviors through textual feedback or parameter updates from reward signals that refine forward actions ([Chae et al., 2025a](#bib.bib41); [Chae et al., 2025b](#bib.bib34); [Wu et al., 2025b](#bib.bib22); [Wang et al., 2025a](#bib.bib40); [Zhang et al., 2026a](#bib.bib35); [Xue et al., 2026](#bib.bib43); [Wang et al., 2026c](#bib.bib47)), and explicit test-time rollback through full environment resets followed by re-executing all prior actions (i.e., action replay) ([Koh et al., 2024b](#bib.bib24); [He et al., 2025](#bib.bib25)) or API-based undo operations in web environments (e.g., browser back) ([Hu et al., 2025](#bib.bib18); [Zhang et al., 2026b](#bib.bib23)), utilized as a heuristic component within an inference pipeline rather than subjected to systematic study.

Yet, these heuristic remedies fall short of providing general-purpose recovery. Environment resets are often infeasible in proprietary settings such as production websites and operating systems ([Regatti et al., 2021](#bib.bib6); [Nguyen and Cheng, 2023](#bib.bib8); [Wang et al., 2026b](#bib.bib1)), action replay ([Koh et al., 2024b](#bib.bib24); [He et al., 2025](#bib.bib25)) inherits this requirement and becomes costly over long horizons, and API-based rollback ([Hu et al., 2025](#bib.bib18); [Zhang et al., 2026b](#bib.bib23)) is largely confined to web environments, leaving broader desktop settings uncovered. Consequently, autonomous model-level recovery, in which the agent itself restores a prior state without relying on such ad hoc mechanisms, emerges as an essential capability. However, whether current agents possess recovery capabilities, and how it affects overall agent performance remain largely unexplored. Therefore, we investigate several fundamental research questions:

RQ1. Is recovery necessary to unlock models’ latent capabilities?

RQ2. Do current computer-use agents possess recovery capabilities under erroneous conditions, and are such capabilities latent or entirely absent?

RQ3. Does accurate model-level recovery translate into measurable improvements in task completion?

![Refer to caption](images/25_ReTRACE/main_figure.png)


Figure 2: Overview of ReTrace. (A) On-Policy Trajectory Rollout collects successful trajectories and replays each action sequence $N$ times to build a transition-consistent dataset. (B) Trajectory Drift via Perturbation selects a recovery target and perturbs the agent into an erroneous state. (C) Goal-Oriented Action Replay replays the remaining actions from the recovered state to test whether the agent reproduces the original task outcome.

To address this, we introduce ReTrace, a pipeline that conducts the first systematic study of autonomous, model-based recovery behavior in computer-use agents. Motivated by predictive state representation theory ([Littman and Sutton, 2001](#bib.bib7)), which represents states by the formalization of predicted futures, we formalize successful recovery as *Transition-Consistent Recovery*: a recovered state matches its target if executing identical downstream actions from both states yields identical outcomes. This formulation captures latent changes beyond visual similarity by leveraging behavioral equivalence, operationalized via *goal-oriented action replay*. Specifically, we replay each on-policy trajectory multiple times and retain only those with consistent successful outcomes, ensuring deterministic environment transitions. From these trajectories, we sample intermediate states as recovery targets, perturb them into erroneous states, and evaluate whether the original task outcome can be reproduced by replaying the remaining actions.

We then instantiate ReTrace on OSWorld ([Xie et al., 2024](#bib.bib45)) and WindowsAgentArena ([Bonatti et al., 2024](#bib.bib44)) across closed- and open-source computer-use agents, and find that recovery plays a critical role in reliable agent operation. We first show that *ideal recovery, in which agents are returned to an oracle prior state, boosts performance over naive environment resets (Section [4](#S4)), identifying recovery as the key lever for unlocking agents’ latent task-solving capacity (RQ1)*. Yet current agents leave this lever unused, *lacking both the tendency and capability to recover autonomously (Section [5](#S5)) (RQ2)*. When equipped with explicit model-based recovery, however, recovery success climbs by more than an order of magnitude, revealing that the *underlying capability is latent rather than absent (Section [5](#S5)) (RQ2)*. Moreover, recovery quality in turn translates into downstream task success: *accurate model-level recovery delivers measurable end-to-end gains by unlocking otherwise latent task-solving capacity, while weak recovery can actively derail the trajectory (RQ3) (Section [6](#S6))*. These findings position accurate model-based recovery, together with reliable continuation from the recovered state, as a key step toward stronger computer-use agents.

## 2 Related Works

##### Computer-Use Agents

Computer-use agents aim to complete diverse user tasks across web-based environments ([Gur et al., 2023](#bib.bib31); [Furuta et al., 2023](#bib.bib52); [OpenAI, 2025](#bib.bib36); [Awadallah et al., 2025](#bib.bib49)), desktop operating systems such as Linux and Windows ([Wang et al., 2025b](#bib.bib42); [Yang et al., 2025](#bib.bib58); [Anthropic, 2026](#bib.bib37)), and mobile environments ([Ye et al., 2025a](#bib.bib50); [Xu et al., 2026](#bib.bib46)). Pioneering works leverage LLMs over HTML DOM content ([Liu et al., 2018](#bib.bib53); [Kim et al., 2023](#bib.bib54); [Zhou et al., 2023](#bib.bib55)), while recent studies operate LVLMs over screenshot observations ([Koh et al., 2024a](#bib.bib48); [Bai et al., 2025](#bib.bib51); [Kim et al., 2026](#bib.bib62); [Wang et al., 2026c](#bib.bib47)) and further reinforce backbone capabilities through reinforcement learning ([Wang et al., 2025a](#bib.bib40); [Xu et al., 2025](#bib.bib57); [Xue et al., 2026](#bib.bib43)) or external memories ([Zheng et al., 2023](#bib.bib33); [Fu et al., 2024](#bib.bib32)). However, these efforts concentrate on strengthening the *forward* decision policy, leaving long-horizon brittleness, where early mistakes accumulate and propagate downstream ([Wang et al., 2026a](#bib.bib11)), largely unaddressed. In contrast, we focus on the systematic analysis of *recovery* behavior in computer-use agents, a complementary but underexplored axis.

##### Agent Behaviors under Failure

Prior work explores diverse error-handling strategies across complex interactive tasks. For example, [Lightman et al. (2024)](#bib.bib29); [Shinn et al. (2023)](#bib.bib14); [Xi et al. (2024)](#bib.bib30) use outcome and process-level feedback to refine actions at test time in mathematical and code tasks ([Chen et al., 2022](#bib.bib28)). In long-horizon embodied settings, [Huang et al. (2022)](#bib.bib15); [Wang et al. (2023a)](#bib.bib27); [Wang et al. (2023b)](#bib.bib16) leverage external rewards to revise plans or acquire new skills, and [Li et al. (2025)](#bib.bib26) perform rollback through resetting the environment and executing identical actions. This problem has also been explored in computer-use agents: [Wang et al. (2024)](#bib.bib17); [Chae et al. (2025b)](#bib.bib34); [Wu et al. (2025b)](#bib.bib22) use external verifiers to induce reflective behaviors ([Hu et al., 2025](#bib.bib18)) for effective user task completion, [Koh et al. (2024b)](#bib.bib24); [He et al. (2025)](#bib.bib25) employ action replay to revert to prior states upon failure, and [Hu et al. (2025)](#bib.bib18); [Zhang et al. (2026b)](#bib.bib23) utilize explicit rollback via go-back operations in Playwright, while [Lu et al. (2026)](#bib.bib19) introduce semantic actions for state recovery within the DFS algorithm. However, previous works used these mechanisms as heuristics in inference pipelines rather than systematically analyzing their behavior and effects. In contrast, we uncover key findings on model-level recovery in computer-use agents using ReTrace, a scalable pipeline enabling the first systematic analysis of recovery behavior.

## 3 Preliminary

##### Computer-Use Task

We formulate a computer-use agent (CUA) task as a Partially Observable Markov Decision Process ([Kaelbling et al., 1998](#bib.bib60)), $\mathcal{M}=(\mathcal{S},\mathcal{A},\mathcal{O},\mathcal{E},\mathcal{T},\Omega)$ , where a policy $\pi_{\theta}$ interacts with a digital environment $\mathcal{E}$ (e.g., Linux terminals, PowerPoint) to complete a user query $q$ . Each state $s_{t}=(h_{t},o_{t})\in\mathcal{S}$ decomposes into a hidden component $h_{t}$ and an observation $o_{t}=\Omega(s_{t})\in\mathcal{O}$ , satisfying the Markov property. At each step, $\pi_{\theta}$ selects an action $a_{t}\in\mathcal{A}$ , spanning high-level (CLICK) to low-level (pyautogui.click) operations, yielding $s_{t+1}\sim\mathcal{T}(\cdot\mid s_{t},a_{t})$ .

##### Forward Policy and Trajectory

Since $\mathcal{E}$ is only partially observable, $\pi_{\theta}$ conditions on the observation–action history, $\pi_{\theta}(a_{t}\mid o_{0},a_{0},\dots,o_{t})$ , yielding a trajectory $\tau=\{(o_{t},a_{t})\}_{t=0}^{T}$ . However, this forward formulation leaves unspecified how the agent should behave once early actions drive $\tau$ into an erroneous state from which $q$ can no longer be completed, the setting we study next.

## 4 Accurate Recovery Matters

Here, we show through a preliminary experiment that accurate recovery yields measurable gains, establishing it as a powerful lever for reliable agents. For more details, please see Appendices [B.1](#A2.SS1) and [F](#A6).

##### Expected Gains from Ideal Recovery

Agents exhibit diverse trajectories across repeated rollouts of the same task, and this variance may imply substantial latent task-solving capability that any single rollout fails to exploit, motivating our hypothesis: reverting to an appropriate past state (*recovery step*) can convert it into task success.
To validate this, we measure Success@5, the success rate over 5 independent continuations, when the forward policy resumes from different recovery steps.

![](images/25_ReTRACE/success_at_k.svg)


Figure 3: Success@ $\mathrm{k}$ across different recovery steps $\mathrm{R}$ under ideal recovery, using EvoCUA-32B as the forward policy on OSWorld.

##### Setup

We focus on tasks that the forward policy fails to solve under standard rollouts, the cases where recovery can yield measurable gains, with EvoCUA-32B ([Xue et al., 2026](#bib.bib43)) as the forward policy on the OSWorld ([Xie et al., 2024](#bib.bib45)) benchmark. For each failed trajectory, we annotate the *error step* $\mathrm{E}$ (where the agent first goes off track) using an LLM-based detector, and set the recovery step $\mathrm{R}$ , from which the forward policy resumes, to one of: the initial state ( $\mathrm{R=0}$ , equivalent to a full environment reset), one step before the error ( $\mathrm{R=E\text{-}1}$ ), a uniformly sampled past step ( $\mathrm{R=E\text{-}\text{random}}$ ), or a step identified by an LLM-based recovery step detector ( $\mathrm{R=R_{\text{LLM}}}$ ). We use Qwen3.6-Plus ([Qwen Team, 2026b](#bib.bib61)) as the backbone for both detectors.

##### Results

As shown in Figure [3](#S4.F3), every non-zero recovery strategy outperforms complete environment resets ( $\mathrm{R=0}$ ), with the largest advantage observed in the low- $\mathrm{K}$ regime. This demonstrates that, under the same retry budget, recovering from the previous state utilizes each retry substantially more efficiently than restarting the task from scratch (Finding 1), resulting in significantly higher Success@ $\mathrm{K}$ . As $\mathrm{K}$ increases, the gap naturally diminishes because repeated restarts also accumulate additional opportunities for success. These findings therefore highlight the efficiency of accurate recovery in utilizing model’s internal capabilities under constrained retry budgets.

## 5 How Well Can Agents Recover?

Here, we analyze the recovery behavior of current computer-use agents using the empirical pipeline illustrated in Figure [2](#S1.F2). For more details, please see Appendices [A](#A1), [B.3](#A2.SS3), [C](#A3), and [F](#A6).

### 5.1 Transition-Consistent Recovery

Given a trajectory $\tau=\{(s_{t},a_{t})\}_{t=0}^{T}$ produced by a policy $\pi$ , the recovery task is defined as a function $f$ that maps an arbitrary state $s_{t}$ back to a past target state, $f(s_{t})=s_{\mathrm{target}}=s_{t-\mathrm{d}}$ , where $\mathrm{d}$ is the recovery distance. Whether this mapping succeeds is judged by a predefined recovery oracle $\mathcal{R}$ , which returns a binary indicator of recovery success or failure, $\mathcal{R}(f(s_{t}),s_{\mathrm{target}})\in\{0,1\}$ . Recalling from Section [3](#S3) that each state decomposes as $s_{t}=(h_{t},o_{t})$ into a hidden component $h_{t}$ and an observation $o_{t}$ , $\mathcal{R}$ should verify that $f(s_{t})$ matches $s_{\mathrm{target}}$ in both components.
A natural instantiation of $\mathcal{R}$ is to compare the observations of $f(s_{t})$ and $s_{\mathrm{target}}$ directly, e.g., via pixel- or feature-level matching. However, this surface criterion is unreliable, since latent components of the environment may be implicitly altered without any visible change ([Shani and Brafman, 2004](#bib.bib20)) (e.g., a hidden configuration file modified while the screenshot remains identical), causing observation-only oracles to falsely declare success on states that nonetheless diverge in their downstream effects. To capture such latent discrepancies, we draw on the theory of predictive state representations ([Littman and Sutton, 2001](#bib.bib7)), which defines state equivalence through identical transition dynamics, and formalize transition-consistent recovery. Specifically, in a controlled environment $\mathcal{E}$ with a deterministic transition function $\mathcal{T}_{\mathcal{E}}$ , we declare a recovery successful when executing the same downstream action $a_{t-\mathrm{d}}$ from the recovered state reproduces the next state along the original trajectory, defined as $\mathcal{R}_{\mathrm{TC}}=\mathbb{I}\big[\mathcal{T}_{\mathcal{E}}(f(s_{t}),a_{t-\mathrm{d}})=s_{t-\mathrm{d}+1}\big]$ for $(s_{t-\mathrm{d}},a_{t-\mathrm{d}},s_{t-\mathrm{d}+1})\in\tau$ , which could extend to the multi-step setting by recursively chaining transitions along $\tau$ , as $\mathcal{R}_{\mathrm{TC}}=\mathbb{I}\big[\mathcal{T}_{\mathcal{E}}(\cdots\mathcal{T}_{\mathcal{E}}(f(s_{\mathrm{t}}),a_{\mathrm{t-d}})\cdots,a_{\mathrm{t-1}})=s_{\mathrm{t}}\big].$

To complement this hidden-state check, we additionally enforce observation-level agreement to guard against cases where the visible interface itself diverges from the target. Formally, we define $\mathcal{R}_{\mathrm{O}}=\mathbb{I}[\,o=\hat{o}\,]$ , where $(h,o)=s_{\mathrm{target}}$ and $(\hat{h},\hat{o})=f(s_{t})$ . The final recovery oracle then combines both, $\mathcal{R}=\mathcal{R}_{\mathrm{TC}}\wedge\mathcal{R}_{\mathrm{O}}$ , jointly evaluating recovery on the hidden and observable axes.

### 5.2 Recovery Evaluation

ReTrace evaluates recovery in three stages (Figure [2](#S1.F2)): the first two construct a transition-consistent evaluation set, and the third measures recovery on it via goal-oriented action replay.

##### On-Policy Trajectory Rollout

As the first stage of ReTrace (Figure [2](#S1.F2) (A)), evaluating transition-consistent recovery requires a target state $s_{\mathrm{target}}$ and an error state $s_{\mathrm{error}}$ for a trajectory $\tau$ , together with a deterministic transition function $\mathcal{T}$ . To probe each policy on its own behavior, $\tau$ must remain on-policy with the evaluated $\pi_{\theta}$ . We thus begin by rolling out each $\pi_{\theta}\in\Pi$ on every user query $\mathrm{q}\in\mathcal{Q}$ , collecting ground-truth trajectories $\tau_{\mathrm{gt}}=\{(s_{t},a_{t})\}_{t=0}^{T}$ whose success is determined by an oracle $\Phi_{\mathrm{q}}$ . For each $\tau_{\mathrm{gt}}$ , we sample seed time steps $t_{\mathrm{seed}}\in\{1,\dots,T\}$ and retain only successful trajectories with $\Phi_{\mathrm{q}}(\tau_{\mathrm{gt}})=1$ , forming an evaluation set $\mathcal{D}$ for each $\pi_{\theta}$ .

We further require a reliable transition function, grounded in the formal definition of state recovery in Section [5.1](#S5.SS1). To this end, inspired by prior work that approximates the latent model distribution through iterative sampling of model outputs ([Wu et al., 2025a](#bib.bib21)), we construct an amortized deterministic transition function $\hat{\mathcal{T}}$ for a given action trajectory $\tau_{\mathrm{gt}}$ . Specifically, we replay the identical action sequence $N$ times and retain only those that yield $N$ successful outcomes, thereby ensuring reliable state transitions. This finally yields a transition-consistent trajectory dataset $\mathcal{D}_{\mathrm{TC}}$ for each policy $\pi_{\theta}\in\Pi$ .

![](images/25_ReTRACE/recovery_success_rate_comparison_short_horizon_osworld.svg)

Figure 4: Comparison of short-horizon recovery strategies across computer-use agents on OSWorld.

![](images/25_ReTRACE/recovery_success_rate_comparison_short_horizon_windowsagent_arena.svg)


Figure 5: Comparison of short-horizon recovery strategies across models on WindowsAgentArena.

![](images/25_ReTRACE/recovery_intention.svg)


Figure 6: Recovery intention under implicit vs explicit recovery, measured by the similarity between agent rationales and recovery prompts.

| Baselines | Win Rate (%) |
| --- | --- |
| w/o $\mathcal{R}_{\mathrm{O}}$ | 82.0% |
| w/o $\mathcal{R}_{\mathrm{TC}}$ | 63.0% |
| GPT-5.4 Evaluator | 54.0% |

Table 1: Average win rate of ReTrace against alternative evaluation strategies in matching human judgments, where human annotations serve as the ground truth. For more details, see Appendix [B.3](#A2.SS3).

##### Trajectory Drift via Perturbation

Given the transition-consistent dataset, for $(\tau_{\mathrm{gt}},t_{\mathrm{seed}},\hat{\mathcal{T}})\in\mathcal{D}_{\mathrm{TC}}$ we next require a ground-truth error state $s_{\mathrm{error}}$ (Figure [2](#S1.F2) (B)). Taking $s_{t_{\mathrm{seed}}}\in\tau_{\mathrm{gt}}$ as the target state $s_{\mathrm{target}}$ , we obtain $s_{\mathrm{error}}$ by drifting the trajectory into erroneous conditions with respect to the user query $\mathrm{q}$ via a perturbation policy $\pi_{\theta}^{\mathrm{p}}$ . Concretely, we first replay the action sequence of $\tau_{\mathrm{gt}}$ in $\mathcal{E}$ using $\hat{\mathcal{T}}$ up to step $t_{\mathrm{seed}}$ , with the LLM verifier $h_{\theta}$ confirming that $s_{t_{\mathrm{seed}}}$ is reproduced. From this state, $\pi_{\theta}^{\mathrm{p}}$ rolls out a perturbation trajectory $\tau_{\mathrm{p}}=\big\{(s_{t_{\mathrm{seed}}},\;a_{t_{\mathrm{seed}}}),\;\ldots,\;(s_{t_{\mathrm{seed}}+t_{\mathrm{p}}})\big\}$ up to the perturbation limit $t_{\mathrm{p}}$ . The oracle $\Phi_{\mathrm{q}}$ then assigns the final state $s_{t_{\mathrm{seed}}+t_{\mathrm{p}}}$ as $s_{\mathrm{error}}$ when it is erroneous, yielding the transition-consistent recovery evaluation set $\mathcal{D}_{\mathrm{R}}$ for each policy $\pi_{\theta}\in\Pi$ . By construction, every instance in $\mathcal{D}_{\mathrm{R}}$ pairs a verified off-track error state $s_{\mathrm{error}}$ with its reachable target $s_{\mathrm{target}}$ , enabling a controlled evaluation of agent recovery under genuine failure.

##### Goal-Oriented Action Replay

Given the recovery evaluation set $\mathcal{D}_{\mathrm{R}}$ , we initiate recovery from each $s_{\mathrm{error}}\in\mathcal{D}_{\mathrm{R}}$ , which serves as the starting state for the recovery policy $\pi_{\theta}^{\mathrm{R}}$ (Figure [2](#S1.F2) (C)). Since $s_{\mathrm{error}}$ is conditioned on $s_{\mathrm{target}}$ , we first replay $\tau_{\mathrm{gt}}$ up to $s_{\mathrm{target}}$ and then $\tau_{\mathrm{p}}$ for $t_{\mathrm{p}}$ steps, using the LLM verifier $h_{\theta}$ to confirm faithful reconstruction of $s_{\mathrm{target}}$ and $s_{\mathrm{error}}$ , respectively. With $s_{\mathrm{error}}$ thus reconstructed, the recovery policy $\pi_{\theta}^{\mathrm{R}}$ executes from it for at most $\mathrm{r}$ steps, producing the recovery trajectory $\tau_{\mathrm{R}}=\{(s_{t},a_{t})\}_{t=0}^{T}$ and the recovered state $s_{T}$ . However, single-step transition-consistent recovery is impractical, as defining oracle annotations for numerous intermediate states is infeasible. Therefore, following the multi-step formulation of transition-consistent recovery in Section [5.1](#S5.SS1), we instead leverage the pre-configured oracle $\Phi$ for user-query completion, extending the objective to test whether replaying the remaining actions of $\tau_{\mathrm{gt}}$ from the recovered state reproduces the original task outcome. The recovery oracle is thus defined as $\mathcal{R}_{\mathrm{TC}}=\mathbb{I}\big[\Phi_{\mathrm{q}}(\mathcal{T}_{\mathcal{E}}(\cdots\mathcal{T}_{\mathcal{E}}(f(s_{t}),a_{\mathrm{t-d}}),\ldots,a_{T}))=1\big]$ , together with $\mathcal{R}_{\mathrm{O}}$ for observation-level matching.

### 5.3 Recovery Policy

Given an error state, a recovery policy acts to restore a past target state. We study two instantiations, differing in whether recovery is elicited from the forward agent itself or from a dedicated policy.

##### Implicit Recovery

The implicit recovery policy reuses the forward decision policy as is, i.e., $\pi_{\theta}^{\mathrm{R}}=\pi_{\theta}$ , applying no recovery-specific instruction or parameter update. The same agent simply continues to act from the error state, which probes whether it spontaneously produces restorative actions toward prior states as an intrinsic behavior.

##### Explicit Recovery

In contrast, the explicit recovery policy $\pi_{\theta}^{\mathrm{R}}$ is an external policy specifically designed to revert the agent to a target recovery state $s_{\mathrm{target}}$ . Formally, this recovery process is defined as $\pi_{\theta}^{\mathrm{R}}(a_{t}\mid s_{t},s_{\mathrm{target}})$ , which, following the POMDP formulation in Section [3](#S3), can be expressed as $\pi_{\theta}^{\mathrm{R}}(a_{t}\mid o_{\mathrm{target}},(o_{0},a_{0},\dots,o_{t}))$ . Unlike the forward decision policy that begins from a fixed starting point, recovery may start from an arbitrary state along the forward trajectory. Moreover, since the target state itself lies within that trajectory, its hidden component cannot be inferred from $o_{\mathrm{target}}$ alone; we thus introduce an additional recovery context $\mathcal{C}$ to represent the target hidden state $h_{\mathrm{target}}\in s_{\mathrm{target}}$ , leading to the final explicit recovery formulation $\pi_{\theta}^{\mathrm{R}}(a_{t}\mid o_{\mathrm{target}},\mathcal{C},(o_{0},a_{0},\dots,o_{t}))$ .

### 5.4 Experiments

#### 5.4.1 Setup

We now describe the experimental setup, including datasets, models, and inference configurations.

##### Dataset

We evaluate recovery on two computer-use benchmarks, OSWorld ([Xie et al., 2024](#bib.bib45)) and WindowsAgentArena ([Bonatti et al., 2024](#bib.bib44)), each deployed in an isolated environment and providing a user query together with an oracle evaluator that determines whether its execution succeeds.

##### Models

We evaluate a range of state-of-the-art computer-use agents. As closed-source models, we use Claude Sonnet 4.6 ([Anthropic, 2026](#bib.bib37)) and GPT-5.4-Computer-Use ([OpenAI, 2026](#bib.bib38)), which achieve top performance on OSWorld. For open-source models, we consider two post-trained agentic models, EvoCUA-32B ([Xue et al., 2026](#bib.bib43)) and UI-TARS-1.5-7B ([Qin et al., 2025](#bib.bib12)), together with Qwen3.5-9B-Thinking ([Qwen Team, 2026a](#bib.bib39)), a strong open-source model without task-specific post-training.

##### Inference Configurations

We run experiments under short horizon and long horizon settings, with recovery distance $\mathrm{d}$ set to 1 and 5, respectively. We further vary the maximum recovery step budget $\mathrm{r}\in\{1,3,10\}$ .

![](images/25_ReTRACE/recovery_success_rate_long_horizon_maximum.svg)


Figure 7: Maximum long-horizon recovery success rate among four different explicit recovery strategies on OSWorld.

Recovery

Context
SR (%) $\uparrow$ 
 $\Delta$ $\uparrow$ 

Baseline
 $39.38\pm 1.17$ 
—

Contextualizer
 $41.06\pm 3.05$ 
 $+1.68$ 

0 $\sim$ R
 $\mathbf{44.26\pm 1.90}$ 
 $\mathbf{+4.88}$ 

0 $\sim$ E
 $40.49\pm 0.95$ 
 $+1.11$ 

w/o History
 $40.2\pm 1.84$ 
 $+0.82$


Table 2: End-to-end success rate (SR) across recovery strategies, where $\Delta$ is the change over the no-recovery baseline, with three independent runs.

![](images/25_ReTRACE/max_iteration_deltas.svg)


Figure 8: Performance change ( $\Delta$ ) across recovery iterations under Recovery Target Contextualization.

##### Recovery Context

We consider several recovery policy configurations with different contexts $\mathcal{C}$ . For the implicit recovery policy, we provide the observation–action history from the first step up to the error step, denoted 0-E. For the explicit recovery policy, we evaluate four variants: 0-E; 0-R, which instead provides the observation–action history up to the target recovery step $s_{\mathrm{target}}$ ; w/o History, which excludes the history from the context; and w/ Recovery Target Contextualization, which contextualizes the transition history leading up to the target recovery with an LLM summarizer to reduce context ([Zhou et al., 2025](#bib.bib10); [Ye et al., 2025b](#bib.bib56)).

#### 5.4.2 Results and Analysis

We now present and analyze the recovery evaluation results across both benchmarks and all agents.

##### Agents Fail to Recover Prior States

Our results in Figures [4](#S5.F4) and [5](#S5.F5) show that even the strongest computer-use agents, Claude-Sonnet-4.6 and GPT-5.4-CUA, have limited recovery capability, while the strongest open-source model, EvoCUA-32B, exhibits a near-complete inability to restore previous states, with an average recovery rate below 1%. This suggests that current forward policies lack both the intrinsic capability and the behavioral tendency to autonomously perform restorative actions under failure (Finding 2). The analysis in Figure [6](#S5.F6) reinforces this: rationales generated during implicit recovery show substantially lower similarity to the ground-truth recovery prompts, indicating that agents rarely even attempt recovery.

| Model | Setting | SR (%) $\uparrow$ |
| --- | --- | --- |
| Sonnet-4.6 | Baseline | $70.27\pm 0.70$ |
| w/ Recovery | $71.81\pm 1.51$ |  |
| Qwen3.5-9B | Baseline | $38.76\pm 0.64$ |
| w/ Recovery | $41.56\pm 4.14$ |  |
| UI-TARS-1.5-7B | Baseline | $17.25\pm 1.55$ |
| w/ Recovery | $15.74\pm 0.65$ |  |
| EvoCUA-32B | Baseline | $54.88\pm 4.39$ |
| w/ Recovery | $51.55\pm 2.54$ |  |

Table 3: End-to-end task success rate (SR) on OSWorld across different models with the Recovery Target Contextualization strategy, over two independent runs.


| Error Type | Instruction | Target State | Restored State | Action | Problem |
| --- | --- | --- | --- | --- | --- |
| Spurious Perception | Align the text of the first textbox on slide 3 to the right , on slide 4 to the center, and on slide 5 to the left. |  |  | [click] on the hovering alignment button to align slide 3 the text to the right. | Fixates on to the hovering UI element in recovered state , skipping [drag] on the text before clicking the alignment button. |
| State Tracking Failure | Change the font to "Times New Roman" throughout the text. |  |  | [scroll down] to find Times New Roman, since font selection interface is opened. | Hallucinates the restored state due to failed state synchronization with its previous states. |

Table 4: Qualitative analysis of erroneous agent behaviors induced by imperfect state restoration.

##### Analysis on Explicit Recovery

The results in Figures [4](#S5.F4) and [5](#S5.F5) further show that explicit model-based recovery substantially outperforms implicit recovery, by an average margin of 17.86% across the Linux and Windows environments. In addition, the largest improvements are observed for generalist computer-use agents, such as Claude-Sonnet-4.6, GPT-5.4-CUA, and Qwen-3.5-9B. These results suggest that the recovery capability of current computer-use agents is latent rather than absent, but such capabilities are not effectively elicited during standard forward task execution (Finding 3). In contrast, the gains are considerably smaller for post-trained open-source agents, suggesting that extensive post-training on one-directional task-completion trajectories may weaken their inherent recovery capability (Finding 4). Figure [7](#S5.F7) shows the same trend in long-horizon settings: generalist agents exhibit substantially greater recovery potential, whereas post-trained specialists consistently struggle with explicit recovery. Nevertheless, even the most capable models combined with basic explicit recovery strategies still fail to achieve complete recovery under our evaluation settings, suggesting that substantial research remains in developing more robust recovery mechanisms
for computer-use agents.

##### Efficacy of ReTrace

To assess how reliably ReTrace judges recovery success, we conduct a human evaluation study against three baselines: two ablations of our oracle $\mathcal{R}$ with either the image-wise matching component $\mathcal{R}_{O}$ or the transition-consistent component $\mathcal{R}_{\mathrm{TC}}$ removed, and GPT-5.4, a state-of-the-art model with extensive computer-use knowledge. We recruit 12 annotators to judge whether each recovered state aligns with the target state, with 50 samples per variant and each annotator rating 25 of them. As shown in Table [1](#S5.T1), ReTrace agrees with human judgments more often than all baselines, including GPT-5.4, confirming the reliability of its recovery oracle $\mathcal{R}$ . We further report an average inter-annotator agreement of 82% and a Cohen’s kappa ([Cohen, 1960](#bib.bib3)) of 0.45, indicating reliable agreement.

## 6 End-to-End Evaluation of Recovery

In this section, we analyze how recovery quality affects the end-to-end task performance of computer-use agents. For more details, please see Appendices [B.2](#A2.SS2) and [F](#A6).

### 6.1 Setup

We follow the evaluation protocols of Sections [4](#S4) and [5.4](#S5.SS4). Specifically, the forward and recovery agents share the same backbone model, on which we run the explicit recovery strategies.

### 6.2 Results and Analysis

##### Potential Gains from Model-Based Recovery

To validate the potential benefits of model-based recovery, we analyze its performance gains across diverse recovery settings. As shown in Table [2](#S5.T2), model-based recovery improves Qwen3.5-9B over the no-recovery baseline under every recovery setting, with an average gain of 2.12% in the end-to-end setting. Notably, these gains hold despite the suboptimal recovery success rates observed in Figures [4](#S5.F4) and [5](#S5.F5), *indicating that even imperfect recovery can begin to unlock the latent capabilities of current computer-use agents, and that more reliable recovery mechanisms hold substantial promise for improving the overall performance and robustness (Finding 5)*.

##### Recovery Performance Effects on Task Completion

The results in Table [3](#S5.T3) show that models with weaker recovery capabilities (UI-TARS-1.5-7B, EvoCUA-32B) suffer performance degradation during end-to-end inference, underscoring the importance of accurate recovery behavior. In addition, Figure [8](#S5.F8) demonstrates that allowing more recovery attempts yields further gains for models with comparably better recovery performance (Qwen-3.5-9B, UI-TARS-1.5-7B). EvoCUA-32B, in contrast, exhibits severely limited explicit recovery capability: while even a single successful recovery can substantially improve downstream task performance, its consistently low recovery success rate means that additional attempts more often derail the trajectory into increasingly erroneous states. This suggests that *accurate model-level recovery delivers performance gains, while weak recovery can actively derail the trajectory (Finding 6)*.

### 6.3 Qualitative Analysis

In Section [6.2](#S6.SS2), we showed that poor recovery performance can severely degrade downstream task completion, in contrast to the idealized settings of Section [4](#S4). To understand why, we examine the rationales that forward agents generate after recovering to incorrect states, and categorize the resulting behaviors into two major patterns (Table [4](#S5.T4)). Additional examples are provided in Appendix [D](#A4).

##### Spurious Perception

Our first observation is that agents fixate on elements distinct from the target state and rely on them when choosing their next action. For example, in Table [4](#S5.T4), the agent immediately clicks the right-alignment button because the cursor happens to hover over it in the restored state, skipping the drag operation on the text that should have come first and thereby deviating from the trajectory needed for correct task completion.

##### State Tracking Failure

Meanwhile, agents also hallucinate actions by assuming the restored state matches the target, failing to register the discrepancy when the two diverge. For example, as shown in Table [4](#S5.T4), although the restored state is masked by the terminal interface and no longer shows the font-selection UI, the agent acts as if that interface were still open, revealing the side effects of imperfect state restoration.

## 7 Conclusion

In this paper, we conducted the first systematic study of autonomous, model-level recovery behavior in computer-use agents through ReTrace, a scalable pipeline that formalizes successful restoration as *Transition-Consistent Recovery*, where a recovered state matches its target if identical downstream actions yield identical outcomes, and operationalizes this via *goal-oriented action replay*. Empirical evaluations across closed and open-source agents reveal that current agents lack both the tendency and capability to recover autonomously, while accurate model-based recovery substantially closes this gap and translates into measurable end-to-end gains, despite characteristic failure modes such as spurious perception and state-tracking errors. We believe these findings position accurate model-based recovery as a key step toward reliable computer-use agents.

## Limitations

ReTrace is designed to measure and analyze recovery capabilities and behaviors rather than to directly improve them. Our explicit recovery settings can only elicit capabilities already present in the underlying model and cannot compensate for fundamental deficiencies in GUI understanding, state tracking, or action planning. Consequently, inaccurate recovery by specialist agents with weaker recovery capabilities may induce additional trajectory drift and reduce task success. Potential directions for addressing this gap include recovery-aware post-training on erroneous states, target states, and corresponding corrective action trajectories, as well as auxiliary objectives for tracking latent environment states and predicting action-induced transitions. ReTrace can provide the evaluation protocol and controlled recovery scenarios needed to develop and assess such methods, but designing and validating them is beyond the scope of the present work.

## Ethical Considerations

Our work aims to advance the reliability of computer-use agents by systematically studying their recovery behavior, contributing positively to the safe and dependable deployment of digital automation. However, we acknowledge the dual-use nature of such research, as more capable agents could in principle be repurposed for harmful automation. To mitigate such risks, we conduct all experiments in sandboxed virtual environments using publicly available benchmarks in accordance with their licenses, without interaction with real user accounts or personal data, and recommend pairing deployments with appropriate safeguards.

## References

- Anthropic (2026)
  Anthropic
  Claude-sonnet-4.6.
  Note: <https://www.anthropic.com/news/claude-sonnet-4-6>
  Cited by: [§A.1](#A1.SS1.SSS0.Px2.p1.1),
  [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1),
  [§5.4.1](#S5.SS4.SSS1.Px2.p1.1).
- Awadallah et al. (2025)
  A. Awadallah, Y. Lara, R. Magazine, H. Mozannar, A. Nambi, Y. Pandya, A. Rajeswaran, C. Rosset, A. Taymanov, V. Vineet, et al.
  Fara-7b: an efficient agentic model for computer use.
  arXiv preprint arXiv:2511.19663.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Bai et al. (2025)
  S. Bai, Y. Cai, R. Chen, K. Chen, X. Chen, Z. Cheng, L. Deng, W. Ding, C. Gao, C. Ge, et al.
  Qwen3-vl technical report.
  arXiv preprint arXiv:2511.21631.
  Cited by: [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1).
- Bonatti et al. (2024)
  R. Bonatti, D. Zhao, F. Bonacci, D. Dupont, S. Abdali, Y. Li, Y. Lu, J. Wagle, K. Koishida, A. Bucker, et al.
  Windows agent arena: evaluating multi-modal os agents at scale.
  arXiv preprint arXiv:2409.08264.
  Cited by: [§A.1](#A1.SS1.SSS0.Px1.p1.1),
  [§1](#S1.p8.1),
  [§5.4.1](#S5.SS4.SSS1.Px1.p1.1).
- Chae et al. (2025a)
  H. Chae, N. Kim, K. T. Ong, M. Gwak, G. Song, J. Kim, S. Kim, D. Lee, and J. Yeo
  Web agents with world models: learning and leveraging environment dynamics in web navigation.
  In The Thirteenth International Conference on Learning Representations,
  External Links: [Link](https://openreview.net/forum?id=moWiYJuSGF)
  Cited by: [§1](#S1.p2.1).
- Chae et al. (2025b)
  H. Chae, S. Kim, J. Cho, S. Kim, S. Moon, G. Hwangbo, D. Lim, M. Kim, Y. Hwang, M. Gwak, et al.
  Web-shepherd: advancing prms for reinforcing web agents.
  arXiv preprint arXiv:2505.15277.
  Cited by: [§1](#S1.p2.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Chen et al. (2022)
  B. Chen, F. Zhang, A. Nguyen, D. Zan, Z. Lin, J. Lou, and W. Chen
  CodeT: code generation with generated tests.
  ArXiv abs/2207.10397.
  External Links: [Link](https://api.semanticscholar.org/CorpusID:250920542)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Cohen (1960)
  J. Cohen
  A coefficient of agreement for nominal scales.
  Educational and psychological measurement 20 (1), pp. 37–46.
  Cited by: [§B.3](#A2.SS3.p3.1),
  [§5.4.2](#S5.SS4.SSS2.Px3.p1.1).
- Fu et al. (2024)
  Y. Fu, D. Kim, J. Kim, S. Sohn, L. Logeswaran, K. Bae, and H. Lee
  Autoguide: automated generation and selection of context-aware guidelines for large language model agents.
  Advances in Neural Information Processing Systems 37, pp. 119919–119948.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Furuta et al. (2023)
  H. Furuta, K. Lee, O. Nachum, Y. Matsuo, A. Faust, S. S. Gu, and I. Gur
  Multimodal web navigation with instruction-finetuned foundation models.
  arXiv preprint arXiv:2305.11854.
  Cited by: [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1).
- Guo et al. (2025)
  D. Guo, D. Yang, H. Zhang, J. Song, P. Wang, Q. Zhu, R. Xu, R. Zhang, S. Ma, X. Bi, X. Zhang, X. Yu, Y. Wu, Z. F. Wu, Z. Gou, Z. Shao, Z. Li, Z. Gao, A. Liu, B. Xue, B. Wang, B. Wu, B. Feng, C. Lu, C. Zhao, C. Deng, C. Ruan, D. Dai, D. Chen, D. Ji, E. Li, F. Lin, F. Dai, F. Luo, G. Hao, G. Chen, G. Li, H. Zhang, H. Xu, H. Ding, H. Gao, H. Qu, H. Li, J. Guo, J. Li, J. Chen, J. Yuan, J. Tu, J. Qiu, J. Li, J. L. Cai, J. Ni, J. Liang, J. Chen, K. Dong, K. Hu, K. You, K. Gao, K. Guan, K. Huang, K. Yu, L. Wang, L. Zhang, L. Zhao, L. Wang, L. Zhang, L. Xu, L. Xia, M. Zhang, M. Zhang, M. Tang, M. Zhou, M. Li, M. Wang, M. Li, N. Tian, P. Huang, P. Zhang, Q. Wang, Q. Chen, Q. Du, R. Ge, R. Zhang, R. Pan, R. Wang, R. J. Chen, R. L. Jin, R. Chen, S. Lu, S. Zhou, S. Chen, S. Ye, S. Wang, S. Yu, S. Zhou, S. Pan, S. S. Li, S. Zhou, S. Wu, T. Yun, T. Pei, T. Sun, T. Wang, W. Zeng, W. Liu, W. Liang, W. Gao, W. Yu, W. Zhang, W. L. Xiao, W. An, X. Liu, X. Wang, X. Chen, X. Nie, X. Cheng, X. Liu, X. Xie, X. Liu, X. Yang, X. Li, X. Su, X. Lin, X. Q. Li, X. Jin, X. Shen, X. Chen, X. Sun, X. Wang, X. Song, X. Zhou, X. Wang, X. Shan, Y. K. Li, Y. Q. Wang, Y. X. Wei, Y. Zhang, Y. Xu, Y. Li, Y. Zhao, Y. Sun, Y. Wang, Y. Yu, Y. Zhang, Y. Shi, Y. Xiong, Y. He, Y. Piao, Y. Wang, Y. Tan, Y. Ma, Y. Liu, Y. Guo, Y. Ou, Y. Wang, Y. Gong, Y. Zou, Y. He, Y. Xiong, Y. Luo, Y. You, Y. Liu, Y. Zhou, Y. X. Zhu, Y. Huang, Y. Li, Y. Zheng, Y. Zhu, Y. Ma, Y. Tang, Y. Zha, Y. Yan, Z. Z. Ren, Z. Ren, Z. Sha, Z. Fu, Z. Xu, Z. Xie, Z. Zhang, Z. Hao, Z. Ma, Z. Yan, Z. Wu, Z. Gu, Z. Zhu, Z. Liu, Z. Li, Z. Xie, Z. Song, Z. Pan, Z. Huang, Z. Xu, Z. Zhang, and Z. Zhang
  DeepSeek-r1 incentivizes reasoning in llms through reinforcement learning.
  Nature 645 (8081), pp. 633–638.
  External Links: ISSN 1476-4687,
  [Link](http://dx.doi.org/10.1038/s41586-025-09422-z),
  [Document](https://dx.doi.org/10.1038/s41586-025-09422-z)
  Cited by: [§1](#S1.p1.1).
- Gur et al. (2023)
  I. Gur, H. Furuta, A. Huang, M. Safdari, Y. Matsuo, D. Eck, and A. Faust
  A real-world webagent with planning, long context understanding, and program synthesis.
  arXiv preprint arXiv:2307.12856.
  Cited by: [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1).
- He et al. (2025)
  S. He, Y. Cui, X. Ma, Y. Li, B. Ding, and M. Chowdhury
  Branch-and-browse: efficient and controllable web exploration with tree-structured reasoning and action memory.
  arXiv preprint arXiv:2510.19838.
  Cited by: [§1](#S1.p2.1),
  [§1](#S1.p3.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Hu et al. (2025)
  M. Hu, T. Fang, J. Zhang, J. Ma, Z. Zhang, J. Zhou, H. Zhang, H. Mi, D. Yu, and I. King
  WebCoT: enhancing web agent reasoning by reconstructing chain-of-thought in reflection, branching, and rollback.
  In Findings of the Association for Computational Linguistics: EMNLP 2025, C. Christodoulopoulos, T. Chakraborty, C. Rose, and V. Peng (Eds.),
  Suzhou, China, pp. 5155–5173.
  External Links: [Link](https://aclanthology.org/2025.findings-emnlp.276/),
  [Document](https://dx.doi.org/10.18653/v1/2025.findings-emnlp.276),
  ISBN 979-8-89176-335-7
  Cited by: [§1](#S1.p2.1),
  [§1](#S1.p3.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Huang et al. (2022)
  W. Huang, F. Xia, T. Xiao, H. Chan, J. Liang, P. Florence, A. Zeng, J. Tompson, I. Mordatch, Y. Chebotar, et al.
  Inner monologue: embodied reasoning through planning with language models.
  arXiv preprint arXiv:2207.05608.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Kaelbling et al. (1998)
  L. P. Kaelbling, M. L. Littman, and A. R. Cassandra
  Planning and acting in partially observable stochastic domains.
  Artificial intelligence 101 (1-2), pp. 99–134.
  Cited by: [§3](#S3.SS0.SSS0.Px1.p1.1).
- Kim et al. (2023)
  G. Kim, P. Baldi, and S. McAleer
  Language models can solve computer tasks.
  Advances in Neural Information Processing Systems 36, pp. 39648–39677.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Kim et al. (2026)
  S. Kim, K. Kim, and S. J. Hwang
  Learn from weaknesses: automated domain specialization for small computer-use agents.
  arXiv preprint arXiv:2605.28775.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Koh et al. (2024a)
  J. Y. Koh, R. Lo, L. Jang, V. Duvvur, M. Lim, P. Huang, G. Neubig, S. Zhou, R. Salakhutdinov, and D. Fried
  Visualwebarena: evaluating multimodal agents on realistic visual web tasks.
  In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers),
  pp. 881–905.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Koh et al. (2024b)
  J. Y. Koh, S. McAleer, D. Fried, and R. Salakhutdinov
  Tree search for language model agents.
  arXiv preprint arXiv:2407.01476.
  Cited by: [§1](#S1.p2.1),
  [§1](#S1.p3.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Kwon et al. (2023)
  W. Kwon, Z. Li, S. Zhuang, Y. Sheng, L. Zheng, C. H. Yu, J. E. Gonzalez, H. Zhang, and I. Stoica
  Efficient memory management for large language model serving with pagedattention.
  In Proceedings of the ACM SIGOPS 29th Symposium on Operating Systems Principles,
  Cited by: [§A.1](#A1.SS1.SSS0.Px2.p1.1).
- Li et al. (2025)
  X. Li, K. Chen, Y. Long, X. Bai, Y. Xu, and M. Zhang
  Generator-assistant stepwise rollback framework for large language model agent.
  In Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing, C. Christodoulopoulos, T. Chakraborty, C. Rose, and V. Peng (Eds.),
  Suzhou, China, pp. 17683–17700.
  External Links: [Link](https://aclanthology.org/2025.emnlp-main.892/),
  [Document](https://dx.doi.org/10.18653/v1/2025.emnlp-main.892),
  ISBN 979-8-89176-332-6
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Lightman et al. (2024)
  H. Lightman, V. Kosaraju, Y. Burda, H. Edwards, B. Baker, T. Lee, J. Leike, J. Schulman, I. Sutskever, and K. Cobbe
  Let’s verify step by step.
  In International Conference on Learning Representations,
  Vol. 2024, pp. 39578–39601.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Littman and Sutton (2001)
  M. Littman and R. S. Sutton
  Predictive representations of state.
  Advances in neural information processing systems 14.
  Cited by: [§1](#S1.p7.1),
  [§5.1](#S5.SS1.p1.1).
- Liu et al. (2018)
  E. Z. Liu, K. Guu, P. Pasupat, T. Shi, and P. Liang
  Reinforcement learning on web interfaces using workflow-guided exploration.
  arXiv preprint arXiv:1802.08802.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Lu et al. (2026)
  Z. Lu, T. Weng, Y. Yang, Y. Zhao, X. Huang, and W. Jiang
  BEAP-agent: backtrackable execution and adaptive planning for gui agents.
  arXiv preprint arXiv:2601.21352.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Nguyen and Cheng (2023)
  H. Nguyen and C. Cheng
  Provable reset-free reinforcement learning by no-regret reduction.
  In International Conference on Machine Learning,
  pp. 25939–25955.
  Cited by: [§1](#S1.p3.1).
- OpenAI (2025)
  OpenAI
  Operator.
  Note: <https://openai.com/ko-KR/index/introducing-operator/>
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- OpenAI (2026)
  OpenAI
  GPT-5.4-computer use.
  Note: <https://openai.com/ko-KR/index/introducing-gpt-5-4/>
  Cited by: [§A.1](#A1.SS1.SSS0.Px2.p1.1),
  [§5.4.1](#S5.SS4.SSS1.Px2.p1.1).
- Qin et al. (2025)
  Y. Qin, Y. Ye, J. Fang, H. Wang, S. Liang, S. Tian, J. Zhang, J. Li, Y. Li, S. Huang, et al.
  UI-tars: pioneering automated gui interaction with native agents.
  arXiv preprint arXiv:2501.12326.
  Cited by: [§A.1](#A1.SS1.SSS0.Px2.p1.1),
  [§B.2](#A2.SS2.SSS0.Px2.p1.1),
  [§5.4.1](#S5.SS4.SSS1.Px2.p1.1).
- Qwen Team (2026a)
  Qwen Team
  Qwen3.5: towards native multimodal agents.
  External Links: [Link](https://qwen.ai/blog?id=qwen3.5)
  Cited by: [§A.1](#A1.SS1.SSS0.Px2.p1.1),
  [§B.2](#A2.SS2.SSS0.Px2.p1.1),
  [§5.4.1](#S5.SS4.SSS1.Px2.p1.1).
- Qwen Team (2026b)
  Qwen Team
  Qwen3.6-Plus: towards real world agents.
  External Links: [Link](https://qwen.ai/blog?id=qwen3.6)
  Cited by: [§B.2](#A2.SS2.SSS0.Px3.p1.1),
  [§4](#S4.SS0.SSS0.Px2.p1.1).
- Regatti et al. (2021)
  J. R. Regatti, A. A. Deshmukh, F. Cheng, Y. H. Jung, A. Gupta, and U. Dogan
  Offline rl with resource constrained online deployment.
  arXiv preprint arXiv:2110.03165.
  Cited by: [§1](#S1.p3.1).
- Sager et al. (2025)
  P. J. Sager, B. Meyer, P. Yan, R. von Wartburg-Kottler, L. Etaiwi, A. Enayati, G. Nobel, A. Abdulkadir, B. F. Grewe, and T. Stadelmann
  AI agents for computer use: a review of instruction-based computer control, gui automation, and operator assistants.
  arXiv preprint arXiv:2501.16150, pp. 1–64.
  Cited by: [§1](#S1.p1.1).
- Shani and Brafman (2004)
  G. Shani and R. Brafman
  Resolving perceptual aliasing in the presence of noisy sensors.
  Advances in Neural Information Processing Systems 17.
  Cited by: [§5.1](#S5.SS1.p1.1).
- Shinn et al. (2023)
  N. Shinn, F. Cassano, A. Gopinath, K. Narasimhan, and S. Yao
  Reflexion: language agents with verbal reinforcement learning.
  Advances in neural information processing systems 36, pp. 8634–8652.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Singh et al. (2025)
  A. K. Singh, A. Fry, A. Perelman, A. Tart, A. Ganesh, A. El-Kishky, A. McLaughlin, A. Low, A. Ostrow, A. Ananthram, A. Nathan, A. Luo, A. Helyar, A. Madry, A. A. Efremov, A. Spyra, A. Baker-Whitcomb, A. Beutel, A. Karpenko, A. Makelov, A. Neitz, A. Z. Wei, A. Barr, A. Kirchmeyer, A.A. Ivanov, A. Christakis, A. Gillespie, A. Tam, A. Bennett, A. Wan, A. Huang, A. M. Sandjideh, A. Yang, A. Kumar, A. Saraiva, A. Vallone, A.S. Gheorghe, A. G. Garcia, A. Braunstein, A. Liu, A. M. Schmidt, A. Mereskin, A. Mishchenko, A. Applebaum, A. Rogerson, A. Rajan, A. Y. Wei, A. Kotha, A. Srivastava, A. Agrawal, A. Vijayvergiya, A. Tyra, A. Nair, A. Nayak, B. Eggers, B. Ji, B. Hoover, B. Chen, B. Chen, B. Barak, B. Minaiev, B. Hao, B. Baker, B. Lightcap, B. McKinzie, B. Wang, B. Quinn, B. Fioca, B. Hsu, B. Yang, B. Yu, B. H. Zhang, B. Brenner, C. R. Zetino, C. Raymond, C. Lugaresi, C. Paz, C. Hudson, C. Whitney, C. Li, C. Chen, C. Cole, C. Voss, C. Ding, C. Shen, C. Huang, C. Colby, C. Hallacy, C. Koch, C. Lu, C. Kaplan, C. Kim, C. Minott-Henriques, C. Frey, C. W. Yu, C. Czarnecki, C. Reid, C. Wei, C. Decareaux, C. Scheau, C. Zhang, C. Forbes, D. Tang, D. Goldberg, D. Roberts, D. Palmie, D. Kappler, D. Levine, D. Wright, D. Leo, D. Lin, D. Robinson, D. Grabb, D. Chen, D. Lim, D. Salama, D. Bhattacharjee, D. Tsipras, D. Li, D. Yu, D. Strouse, D.R. Williams, D. Hunn, E. Bayes, E. Arbus, E. Akyürek, E. Y. Le, E. Widmann, E. A. Yani, E. Proehl, E. Sert, E. Cheung, E. M. Schwartz, E. Han, E. Jiang, E. Mitchell, E. Sigler, E. Wallace, E. Ritter, E. Kavanaugh, E. Mays, E. Nikishin, F. Li, F. P. Such, F. de Avila Belbute Peres, F. Raso, F. Bekerman, F. Tsimpourlas, F. Chantzis, F. Song, F. Zhang, G. Raila, G. McGrath, G. J. Briggs, G. Yang, G. Parascandolo, G. Chabot, G. Kim, G. Zhao, G. Valiant, G. Leclerc, H. Salman, H. Wang, H. Sheng, H. Jiang, H. Wang, H. Jin, H. S. Sikchi, H. Schmidt, H. Aspegren, H. Chen, H. Qiu, H. Lightman, I. C. Covert, I. Kivlichan, I. Silber, I. Sohl, I. Hammoud, I. Clavera, I. Lan, I. Akkaya, I. N. Kostrikov, I. Kofman, I. C. Etinger, I. Singal, J. Hehir, J. Huh, J. Pan, J. Wilczynski, J. W. Pachocki, J. Lee, J. Quinn, J. R. Kiros, J. Kalra, J. Samaroo, J. Wang, J. Wolfe, J. Chen, J. Wang, J. Harb, J. Han, J. Wang, J. Zhao, J. Chen, J. Z. Yang, J. Tworek, J. Chand, J. Landon, J. Y. Liang, J. Lin, J. Liu, J. Wang, J. Tang, J. Yin, J. Jang, J. M. Morris, J. Flynn, J. Ferstad, J. Heidecke, J. Fishbein, J. Hallman, J. E. Grant, J. Chien, J. Gordon, J. Park, J. Liss, J. Kraaijeveld, J. Guay, J. Mo, J. Lawson, J. McGrath, J. Vendrow, J. Jiao, J. H. M. Lee, J. Steele, J. Wang, J. Mao, K. Chen, K. Hayashi, K. Xiao, K. Salahi, K. Wu, K. Sekhri, K. Sharma, K. Singhal, K. Li, K. Nguyen, K. Gu-Lemberg, K. King, K. Liu, K. R. Stone, K. Yu, K. Ying, K. Georgiev, K. Lim, K. Tirumala, K. Miller, L. Ahmad, L. Lv, L. Clare, L. Fauconnet, L. Itow, L. Yang, L. M. Romaniuk, L. Anise, L. Byron, L. Pathak, L. Maksin, L. Lo, L. Ho, L. Jing, L. Wu, L. Xiong, L. Mamitsuka, L. Yang, L. McCallum, L. Held, llann Bourgeois, L. Engstrom, L. Kuhn, L. Feuvrier, L. Zhang, L. Switzer, L. Kondraciuk, L. Kaiser, M. R. Joglekar, M. Singh, M. Shah, M. Stratta, M. Williams, M. Chen, M. Sun, M. Cayton, M. Li, M. Zhang, M. Aljubeh, M. Nichols, M. Haines, M. Schwarzer, M. M. Gupta, M. Shah, M. Y. Huang, M. Dong, M. Wang, M. Glaese, M. Carroll, M. Lampe, M. Malek, M. Sharman, M. Zhang, M. Wang, M. Pokrass, M. Florian, M. Pavlov, M. Wang, M. Chen, M. Wang, M. Feng, M. Bavarian, M. Lin, M. Abdool, M. Rohaninejad, N. Soto, N. M. Staudacher, N. LaFontaine, N. Marwell, N. F. Liu, N. Preston, N. Turley, N. Ansman, N. Blades, N. Pancha, N. Mikhaylin, N. Felix, N. Handa, N. Rai, N. S. Keskar, N. Brown, O. Nachum, O. Boiko, O. Murk, O. Watkins, O. Gleeson, P. Mishkin, P. Lesiewicz, P. Baltescu, P. Belov, P. Zhokhov, P. Pronin, P. Guo, P. Thacker, Q. Liu, Q. Yuan, Q. Liu, R. Dias, R. Puckett, R. K. Arora, R. T. Mullapudi, R. Gaon, R. Miyara, R. Song, R. Aggarwal, R. Marsan, R. Yemiru, R. Xiong, R. Kshirsagar, R. Nuttall, R. Tsiupa, R. Eldan, R. Wang, R. James, R. Ziv, R. Shu, R. T. Nigmatullin, S. Jain, S. Talaie, S. Altman, S. Arnesen, S. Toizer, S. Toyer, S. Miserendino, S. Agarwal, S. Yoo, S. Heon, S. Ethersmith, S. Grove, S. Taylor, S. Bubeck, S. Banesiu, S. Amdo, S. Zhao, S. Wu, S. Santurkar, S. Zhao, S. R. Chaudhuri, S. Krishnaswamy, S. Xia, S. Cheng, S. Anadkat, S. P. Fishman, S. Tobin, S. Fu, S. Jain, S. Mei, S. Egoian, S. Kim, S. L. van Golden, S. Mah, S. L. Lin, S. J. Imm, S. Sharpe, S. Yadlowsky, S. Choudhry, S. Eum, S. Sanjeev, T. Khan, T. Stramer, T. Wang, T. Xin, T. Gogineni, T. Christianson, T. Sanders, T. Patwardhan, T. Degry, T. Shadwell, T. Fu, T. Gao, T. Garipov, T. Sriskandarajah, T. Sherbakov, T. Kaftan, T. Hiratsuka, T. Wang, T. Song, T. Zhao, T. A. Peterson, V. V. Kharitonov, V. V. Chernova, V. Kosaraju, V. Kuo, V. H. Pong, V. Verma, V. G. Petrov, W. Jiang, W. Zhang, W. Zhou, W. Xie, W. Zhan, W. McCabe, W. DePue, W. Ellsworth, W. Bain, W. Thompson, X. Chen, X. Qi, X. Xiang, X. Shi, Y. Dubois, Y. Yu, Y. Khakbaz, Y. Wu, Y. Qian, Y. T. Lee, Y. Chen, Y. Zhang, Y. Xiong, Y. Tian, Y. S. Cha, Y. Bai, Y. Yang, Y. Yuan, Y. Li, Y. Zhang, Y. Yang, Y. Jin, Y. Jiang, Y. Wang, Y. Wang, Y. Liu, Z. Stubenvoll, Z. Dou, Z. Wu, and Z. Wang
  OpenAI gpt-5 system card.
  External Links: [Link](https://api.semanticscholar.org/CorpusID:284532660)
  Cited by: [§A.2](#A1.SS2.SSS0.Px2.p1.1),
  [§1](#S1.p1.1).
- Wang et al. (2023a)
  G. Wang, Y. Xie, Y. Jiang, A. Mandlekar, C. Xiao, Y. Zhu, L. Fan, and A. Anandkumar
  Voyager: an open-ended embodied agent with large language models.
  arXiv preprint arXiv:2305.16291.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Wang et al. (2025a)
  H. Wang, H. Zou, H. Song, J. Feng, J. Fang, J. Lu, L. Liu, Q. Luo, S. Liang, S. Huang, et al.
  Ui-tars-2 technical report: advancing gui agent with multi-turn reinforcement learning.
  arXiv preprint arXiv:2509.02544.
  Cited by: [§1](#S1.p2.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1).
- Wang et al. (2024)
  J. Wang, H. Xu, H. Jia, X. Zhang, M. Yan, W. Shen, J. Zhang, F. Huang, and J. Sang
  Mobile-agent-v2: mobile device operation assistant with effective navigation via multi-agent collaboration.
  Advances in Neural Information Processing Systems 37, pp. 2686–2710.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Wang et al. (2026a)
  X. J. Wang, H. Bai, Y. Sun, H. Wang, S. Zhang, W. Hu, M. Schroder, B. Mutlu, D. Song, and R. D. Nowak
  The long-horizon task mirage? diagnosing where and why agentic systems break.
  arXiv preprint arXiv:2604.11978.
  Cited by: [§1](#S1.p2.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1).
- Wang et al. (2025b)
  X. Wang, B. Wang, D. Lu, J. Yang, T. Xie, J. Wang, J. Deng, X. Guo, Y. Xu, C. H. Wu, et al.
  Opencua: open foundations for computer-use agents.
  arXiv preprint arXiv:2508.09123.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Wang et al. (2026b)
  Z. Wang, C. Xu, B. Liu, Y. Wang, S. Han, Z. Yao, H. Yao, and Y. He
  Agent world model: infinity synthetic environments for agentic reinforcement learning.
  arXiv preprint arXiv:2602.10090.
  Cited by: [§1](#S1.p3.1).
- Wang et al. (2004)
  Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli
  Image quality assessment: from error visibility to structural similarity.
  IEEE transactions on image processing 13 (4), pp. 600–612.
  Cited by: [§A.2](#A1.SS2.SSS0.Px5.p1.1).
- Wang et al. (2023b)
  Z. Wang, S. Cai, A. Liu, X. Ma, and Y. Liang
  Describe, explain, plan and select: interactive planning with large language models enables open-world multi-task agents.
  arXiv preprint arXiv:2302.01560.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Wang et al. (2026c)
  Z. Wang, L. Yang, X. Tang, S. Zhou, D. Chen, W. Jiang, and Y. Li
  History-aware reasoning for gui agents.
  In Proceedings of the AAAI Conference on Artificial Intelligence,
  Cited by: [§1](#S1.p2.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1).
- Wu et al. (2025a)
  F. Wu, W. Xuan, X. Lu, M. Liu, Y. Dong, Z. Harchaoui, and Y. Choi
  The invisible leash: why rlvr may or may not escape its origin.
  arXiv preprint arXiv:2507.14843.
  Cited by: [§5.2](#S5.SS2.SSS0.Px1.p2.1).
- Wu et al. (2025b)
  Q. Wu, P. Gao, W. Liu, and J. Luan
  Backtrackagent: enhancing gui agent with error detection and backtracking mechanism.
  In Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing,
  pp. 4250–4272.
  Cited by: [§1](#S1.p2.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Xi et al. (2024)
  Z. Xi, D. Yang, J. Huang, J. Tang, G. Li, Y. Ding, W. He, B. Hong, S. Do, W. Zhan, X. Wang, R. Zheng, T. Ji, X. Shi, Y. Zhai, R. Weng, J. Wang, X. Cai, T. Gui, Z. Wu, Q. Zhang, X. Qiu, X. Huang, and Y. Jiang
  Enhancing llm reasoning via critique models with test-time and training-time supervision.
  External Links: 2411.16579,
  [Link](https://arxiv.org/abs/2411.16579)
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- Xie et al. (2024)
  T. Xie, D. Zhang, J. Chen, X. Li, S. Zhao, R. Cao, T. J. Hua, Z. Cheng, D. Shin, F. Lei, Y. Liu, Y. Xu, S. Zhou, S. Savarese, C. Xiong, V. Zhong, and T. Yu
  OSWorld: benchmarking multimodal agents for open-ended tasks in real computer environments.
  External Links: 2404.07972
  Cited by: [§A.1](#A1.SS1.SSS0.Px1.p1.1),
  [§B.1](#A2.SS1.SSS0.Px1.p1.1),
  [§B.2](#A2.SS2.SSS0.Px1.p1.1),
  [§1](#S1.p8.1),
  [§4](#S4.SS0.SSS0.Px2.p1.1),
  [§5.4.1](#S5.SS4.SSS1.Px1.p1.1).
- Xu et al. (2026)
  H. Xu, X. Zhang, H. Liu, J. Wang, Z. Zhu, S. Zhou, X. Hu, F. Gao, J. Cao, Z. Wang, et al.
  Mobile-agent-v3. 5: multi-platform fundamental gui agents.
  arXiv preprint arXiv:2602.16855.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Xu et al. (2025)
  Y. Xu, X. Liu, X. Liu, J. Fu, H. Zhang, B. Jing, S. Zhang, Y. Wang, W. Zhao, and Y. Dong
  Mobilerl: online agentic reinforcement learning for mobile gui agents.
  arXiv preprint arXiv:2509.18119.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Xue et al. (2026)
  T. Xue, C. Peng, M. Huang, L. Guo, T. Han, H. Wang, J. Wang, X. Zhang, X. Yang, D. Zhao, et al.
  Evocua: evolving computer use agents via learning from scalable synthetic experience.
  arXiv preprint arXiv:2601.15876.
  Cited by: [§A.1](#A1.SS1.SSS0.Px2.p1.1),
  [§B.1](#A2.SS1.SSS0.Px1.p1.1),
  [§B.2](#A2.SS2.SSS0.Px2.p1.1),
  [§1](#S1.p2.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1),
  [§4](#S4.SS0.SSS0.Px2.p1.1),
  [§5.4.1](#S5.SS4.SSS1.Px2.p1.1).
- Yang et al. (2026)
  B. Yang, K. Jin, Z. Wu, Z. Liu, Q. Sun, Z. Li, J. Xie, Z. Liu, F. Xu, K. Cheng, Q. Li, Y. Wang, Y. Qiao, Z. Wang, and Z. Ding
  OS-symphony: a holistic framework for robust and generalist computer-using agent.
  External Links: 2601.07779,
  [Link](https://arxiv.org/abs/2601.07779)
  Cited by: [§A.1](#A1.SS1.SSS0.Px1.p1.1).
- Yang et al. (2025)
  Y. Yang, D. Li, Y. Dai, Y. Yang, Z. Luo, Z. Zhao, Z. Hu, J. Huang, A. Saha, Z. Chen, et al.
  Gta1: gui test-time scaling agent.
  arXiv preprint arXiv:2507.05791.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Ye et al. (2025a)
  J. Ye, X. Zhang, H. Xu, H. Liu, J. Wang, Z. Zhu, Z. Zheng, F. Gao, J. Cao, Z. Lu, et al.
  Mobile-agent-v3: fundamental agents for gui automation.
  arXiv preprint arXiv:2508.15144.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Ye et al. (2025b)
  R. Ye, Z. Zhang, K. Li, H. Yin, Z. Tao, Y. Zhao, L. Su, L. Zhang, Z. Qiao, X. Wang, et al.
  AgentFold: long-horizon web agents with proactive context management.
  arXiv preprint arXiv:2510.24699.
  Cited by: [§5.4.1](#S5.SS4.SSS1.Px4.p1.1).
- Zhang et al. (2026a)
  Y. Zhang, S. Tang, Z. Li, Z. Han, and V. Tresp
  WebArbiter: a principle-guided reasoning process reward model for web agents.
  arXiv preprint arXiv:2601.21872.
  Cited by: [§1](#S1.p2.1).
- Zhang et al. (2026b)
  Z. Zhang, T. Fang, K. Ma, W. Yu, H. Zhang, H. Mi, and D. Yu
  WebRollback: enhancing web agents with explicit rollback mechanisms.
  In Proceedings of the 19th Conference of the European Chapter of the Association for Computational Linguistics (Volume 2: Short Papers),
  pp. 187–197.
  Cited by: [§1](#S1.p2.1),
  [§1](#S1.p3.1),
  [§2](#S2.SS0.SSS0.Px2.p1.1).
- Zheng et al. (2023)
  L. Zheng, R. Wang, X. Wang, and B. An
  Synapse: trajectory-as-exemplar prompting with memory for computer control.
  arXiv preprint arXiv:2306.07863.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Zhou et al. (2023)
  S. Zhou, F. F. Xu, H. Zhu, X. Zhou, R. Lo, A. Sridhar, X. Cheng, T. Ou, Y. Bisk, D. Fried, et al.
  Webarena: a realistic web environment for building autonomous agents.
  arXiv preprint arXiv:2307.13854.
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- Zhou et al. (2025)
  Z. Zhou, A. Qu, Z. Wu, S. Kim, A. Prakash, D. Rus, J. Zhao, B. K. H. Low, and P. P. Liang
  Mem1: learning to synergize memory and reasoning for efficient long-horizon agents.
  arXiv preprint arXiv:2506.15841.
  Cited by: [§5.4.1](#S5.SS4.SSS1.Px4.p1.1).

## Appendix A ReTrace Details

Here, we provide implementation details on the evaluation set construction and recovery evaluation in ReTrace framework. We provide statistics of the filtered trajectories in Table [6](#A1.T6), and distribution of domains within our recovery evaluation set in Table [7](#A1.T7).

### A.1 Evaluation Set Construction

##### Benchmarks

We primarily leverage two publicly available benchmarks consisting of both web tasks and non-web tasks: OSWorld 11
1
<https://github.com/xlang-ai/OSWorld.git> ([Xie et al., 2024](#bib.bib45)), released under the Apache License 2.0, and WindowsAgentArena ([Bonatti et al., 2024](#bib.bib44)), released under the MIT License. Both benchmarks consist of non-web tasks with significantly higher ratio compared to web-based tasks, which we demonstrate such ratio in Table [5](#A1.T5) that underscores the importance of model-level recovery, where web-based apis such as Playwright is not supported. To accelerate evaluation, we execute multiple environments in parallel, and for WindowsAgentArena, we utilize the processed environments provided by OS-Symphony22
2
<https://github.com/OS-Copilot/OS-Symphony.git> ([Yang et al., 2026](#bib.bib5)), released under the Apache License 2.0, to enable efficient large-scale evaluation set construction. Our use of these artifacts is consistent with their intended use as public benchmark and evaluation resources. We deploy all environments within isolated Docker containers and apply a 10-second post-action settle window to ensure that pending UI updates are fully rendered before capturing the next observation. For screenshot resolution, we use $(1920,1080)$ for OSWorld and $(1280,800)$ for WindowsAgentArena. Finally, we restrict our evaluation to tasks that do not require proxy or Google Drive settings, due to constraints on proxy server budget and account configuration, respectively.

##### Models

To construct the recovery evaluation set, we use five models: Claude-Sonnet-4.6 ([Anthropic, 2026](#bib.bib37)), GPT-5.4-CUA ([OpenAI, 2026](#bib.bib38)), Qwen-3.5-9B-Thinking ([Qwen Team, 2026a](#bib.bib39)), EvoCUA-32B ([Xue et al., 2026](#bib.bib43)), and UI-TARS-1.5-7B ([Qin et al., 2025](#bib.bib12)). Claude-Sonnet-4.6 and GPT-5.4-CUA are configured with thinking mode and xhigh reasoning mode, respectively. We use the pyautogui action space for all models except Claude-Sonnet-4.6, which uses the proprietary claude-computer use action space, while providing raw screenshots as observations. We adopt the default prompts from OSWorld and adapt them to Windows environments for WindowsAgentArena evaluation (Figures
[12](#A6.F12),
[13](#A6.F13),
[14](#A6.F14),
[15](#A6.F15),
[16](#A6.F16),
[17](#A6.F17),
[18](#A6.F18),
[19](#A6.F19),
[20](#A6.F20),
[21](#A6.F21),
[22](#A6.F22),
[23](#A6.F23),
[24](#A6.F24), [25](#A6.F25), [26](#A6.F26)). All open-source models are served locally using vLLM ([Kwon et al., 2023](#bib.bib2)) with bfloat16 precision through OpenAI-compatible HTTP endpoints. Experiments are conducted using a combination of one NVIDIA H200 GPU (141GB) and two RTX A6000 GPUs.

| Benchmark | Web Tasks (%) | Non-Web Tasks (%) |
| --- | --- | --- |
| OSWorld | 12.66 | 87.34 |
| WindowsAgentArena | 21.28 | 78.72 |

Table 5: Ratio of web and non-web tasks in the OSWorld and WindowsAgentArena benchmarks.

##### On-Policy Rollout

For each model, we construct trajectories for the corresponding tasks in each benchmark. We then create an annotated dataset by selecting potential starting steps within each trajectory, while filtering out trajectories containing multiple actions within a single step or erroneous trajectories in which actions are missing from the agent output, as such cases can complicate the annotation process. Subsequently, the action sequences from each trajectory are replayed consecutively, and we retain only the trajectories that achieve a successful oracle evaluation in three consecutive replays (N=3) to minimize the effect from environment stochasticity (Transition-Consistent Filtering). This process empirically ensures deterministic transition dynamics, resulting in a filtered evaluation set in which the starting step of each trajectory is guaranteed to exhibit consistent transitions while retaining 64.4% of recovery trajectories (Table [6](#A1.T6)). For OsWorld short-horizon evaluation settings using GPT-5.4-CUA, we randomly sample 600 samples for perturbation after transition-consistent filtering to keep the API computational cost manageable prior to subsequent filtering stage (Trajectory Perturbation).

|  | Dataset Filtering Step | Claude-Sonnet-4.6 | GPT-5.4-CUA | QWEN-3.5-9B | UI-Tars-1.5-7B | EvoCUA-32B |
| --- | --- | --- | --- | --- | --- | --- |
| OsWorld | # of traj. after formatting | 2733 | 2749 | 790 | 1277 | 1259 |
| # of traj. after transition-consistent filtering | 1921 | 1912 (600) | 574 | 227 | 924 |  |
| # of traj. after perturbation | 1335 | 334 | 397 | 133 | 314 |  |
| # of traj. after final set construction | 120 | 120 | 120 | 60 | 120 |  |
| Windows AgentArena | # of traj. after formatting | 919 | 867 | 211 | N/A | 280 |
| # of traj. after transition-consistent filtering | 779 | 407 | 153 | N/A | 201 |  |
| # of traj. after perturbation | 506 | 200 | 88 | N/A | 122 |  |
| # of traj. after final set construction | 70 | 70 | 50 | N/A | 50 |  |

Table 6: Dataset statistics after each filtering step for the short-horizon settings.

##### Trajectory Perturbation

Using the filtered evaluation set consisting of annotated starting steps from each trajectory, we replay the action sequences until reaching the designated starting step, while verifying that the resulting observation matches the original state. Subsequently, a perturbation agent sharing the same backbone as the forward agent is prompted (Figures [27](#A6.F27), [28](#A6.F28)) to intentionally drift the trajectory under a maximum step budget identical to the recovery distance $\mathrm{d}$ . For short-horizon recovery evaluation, we use a perturbation budget of 1 for all models, except GPT-5.4-CUA, for which we use a budget of 2 due to its strong tendency to generate a “take a screenshot” action as the initial step which maps to time.sleep(), even under explicit instructions. We then retain only trajectories that result in oracle failure according to the benchmark evaluators (while excluding samples that were crashed due to environmental failures or gpt verification failures). This process constructs a recovery-annotated dataset, where the original starting state serves as the target recovery state, and the final perturbed state serves as the error state.

##### Final Evaluation Set Construction

Finally, using the recovery-annotated dataset, we exclude problematic samples whose perturbation trajectories generate multiple actions within a single step or fail to produce actions at arbitrary steps, as such cases complicate annotation. For short-horizon recovery evaluation, we additionally remove samples without meaningful perturbation actions, such as time.sleep() or WAIT. For GPT-5.4-CUA, we exclusively retain samples where the first action is “take a screenshot” and the second action corresponds to an actual perturbation action, due to its strong tendency to begin trajectories with screenshot actions. Furthermore, we remove samples where the error state and target recovery state show significantly high similarity, while also assuring that duplicate samples with both same error state observation and target recovery state observation do not exist, adopting SSIM as core mechanism. After filtering, we randomly sample evaluation subsets. For short-horizon evaluation in OSWorld, we sample 120 instances for all models except UI-TARS-1.5-7B, for which we sample 60 due to the limited number of remaining trajectories. For long-horizon evaluation, we sample 80 instances for Qwen-3.5-9B and EvoCUA-32B, 60 for Claude-Sonnet-4.6, and UI-TARS-1.5-7B. Finally for WindowsAgentArena, we sample 70 instances for Claude-Sonnet-4.6 and GPT-5.4-CUA, and 50 for EvoCUA-32B and Qwen-3.5-9B, due to the different number of remaining samples after the filtering process.

|  | Domain Composition (%) | Original | Claude-Sonnet-4.6 | GPT-5.4-CUA | QWEN-3.5-9B | UI-Tars-1.5-7B | EvoCUA-32B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OsWorld | chrome | 6.64 | 4.17 | 2.50 | 6.67 | 25.00 | 0.00 |
| gimp | 8.23 | 0.83 | 6.67 | 8.33 | 1.67 | 6.67 |  |
| libreoffice_calc | 14.87 | 26.67 | 14.17 | 7.50 | 0.00 | 17.50 |  |
| libreoffice_impress | 14.87 | 29.17 | 15.83 | 21.67 | 13.33 | 38.33 |  |
| libreoffice_writer | 7.28 | 5.83 | 8.33 | 5.83 | 13.33 | 14.17 |  |
| multi_apps | 23.73 | 16.67 | 35.00 | 27.50 | 3.33 | 9.17 |  |
| os | 7.59 | 4.17 | 1.67 | 2.50 | 11.67 | 8.33 |  |
| thunderbird | 4.75 | 4.17 | 1.67 | 11.67 | 11.67 | 0.00 |  |
| vlc | 5.38 | 3.33 | 5.00 | 0.83 | 15.00 | 3.33 |  |
| vscode | 6.65 | 5.00 | 9.17 | 7.50 | 5.00 | 2.50 |  |
| WindowsAgentArena | file_explorer | 13.48 | 14.29 | 17.14 | 24.00 | N/A | 48.00 |
| microsoft_paint | 2.13 | 4.29 | 0.00 | 0.00 | N/A | 0.00 |  |
| libreoffice_writer | 12.77 | 22.86 | 22.86 | 4.00 | N/A | 8.00 |  |
| libreoffice_calc | 17.02 | 11.43 | 18.57 | 0.00 | N/A | 6.00 |  |
| settings | 3.55 | 1.43 | 0.00 | 16.00 | N/A | 14.00 |  |
| vs_code | 13.48 | 10.00 | 4.29 | 40.00 | N/A | 14.00 |  |
| msedge | 9.22 | 7.14 | 7.14 | 0.00 | N/A | 0.00 |  |
| vlc | 9.92 | 8.57 | 21.43 | 8.00 | N/A | 0.00 |  |
| clock | 2.84 | 1.43 | 0.00 | 8.00 | N/A | 4.00 |  |
| windows_calc | 2.13 | 0.00 | 4.29 | 0.00 | N/A | 0.00 |  |
| notepad | 1.42 | 5.71 | 1.43 | 0.00 | N/A | 0.00 |  |
| chrome | 12.06 | 12.86 | 2.86 | 0.00 | N/A | 6.00 |  |

Table 7: Domain Composition ratio per recovery evaluation dataset (short horizon).

### A.2 Recovery Evaluation

##### Benchmarks

We use the evaluation sets constructed in Section [A.1](#A1.SS1) to measure the recovery success rates of both implicit and explicit recovery policies, where the annotated evaluation sets are instantiated in both OSWorld and WindowsAgentArena, where we set the environment settings identical with Section [A.1](#A1.SS1).

##### Models

We evaluate both implicit and explicit recovery using the five models described in Section [A.1](#A1.SS1). For Claude-Sonnet-4.6 and GPT-5.4-CUA, we use a temperature of 1.0 with thinking mode and xhigh reasoning mode enabled, respectively. For Qwen-3.5-9B and EvoCUA-32B, we use a temperature of 0.7, while UI-TARS-1.5-7B is evaluated with a temperature of 0.0. As the recovery target contextualizer, we use Claude-Sonnet-4.6 as the backbone state-transition summarizer with a temperature of 0.0 and a maximum token budget of 1024. All open-source backbones are served locally using vLLM within the same computing infrastructure described in Section [A.1](#A1.SS1). Finally, we use GPT-5-Mini ([Singh et al., 2025](#bib.bib13)) as the state-verification model with default OpenAI hyperparameters.

##### Recovery Context

For implicit recovery strategies, we provide the full history of observation–action pairs up to the error state, allowing the forward agent to infer the underlying state transitions, similar to real-world settings where agents interact continuously throughout the trajectory. In contrast, for explicit recovery strategies, we provide policies with various recovery contexts, including the observation–action history up to the error state and the target recovery state, which we denote as 0-E and 0-R, respectively. We additionally consider settings where such observations are not provided, as well as settings where the observation–action pairs up to the goal state are summarized by an LLM contextualizer that generates a compact description of the target recovery state and the transitions leading to it. When constructing observation–action histories, we maintain aligned observation–action pairs and exclude the final observation resulting from the last action, since new observation is input as current observation. The only exception is GPT-5.4-CUA, for which the final observation is included in the history due to proprietary API technical constraints.

##### Prompts

We construct the system prompts for explicit recovery by concatenating the recovery prefix prompts (Figures [29](#A6.F29),  [31](#A6.F31)) from Section [F](#A6) with the default system prompts used for each model in their respective benchmark settings. Similarly, we construct explicit recovery instructions by combining the model-specific instructions provided in the default OSWorld benchmark with the recovery instruction prefixes from Figures [30](#A6.F30) and [32](#A6.F32). In contrast, for implicit recovery policies, we use the original default system prompts and instructions without any recovery-specific prefix prompts or instructions. Meanwhile, we use prompts in Figures [34](#A6.F34) and [35](#A6.F35) for recovery target contextualizer, while leveraging prompts in Figure [33](#A6.F33) for LLM -based state verification during recovery evaluation.

##### Recovery Verification

In ReTrace, we evaluate recovery success along two axes: latent state recovery success and observation-wise state recovery success. For latent state recovery, we leverage our goal-oriented action replay framework, where recovery is considered unsuccessful if the benchmark oracle evaluator outputs 0 after executing the remaining actions from the ground-truth trajectory starting from the recovered state. For observation-wise recovery, we use SSIM ([Wang et al., 2004](#bib.bib4)) with a threshold of 0.99 to detect visual mismatches that may interfere with accurate evaluation. Furthermore, in our main recovery evaluation experiments, we exclusively sample tasks that are consistently executable across all variants without docker failures or state verification failures, thereby ensuring a fair and reliable comparison of recovery success rates.

## Appendix B Additional Experiment Details

Here, we explain the experimental settings and implementation details for experiments introduced in Sections [4](#S4) and [6](#S6), along with details on Human Evaluation introduced in Table [1](#S5.T1).

### B.1 Ideal Gains from Recovery

This experiment estimates how much end-to-end performance can improve when an agent is allowed to resume from an appropriate past state after a failure. It measures the potential gain from recovery under a controlled replay setting, where the target past state is reconstructed by action replay before the forward agent resumes execution.

##### Benchmark and model

We run the analysis on OSWorld ([Xie et al., 2024](#bib.bib45)) using EvoCUA-32B ([Xue et al., 2026](#bib.bib43)) as the forward model, following the setup from Section [A.1](#A1.SS1). We set the temperature to $0.7$ , max\_tokens to $32768$ , and max\_steps to $50$ . We first collect standard forward rollouts and keep only failed instances whose result.txt score is $0$ . For each failed instance, we identify an error step and select a corresponding recovery step using the recovery-step selection procedure described in Section [4](#S4.SS0.SSS0.Px2). The environment at the selected recovery step is reconstructed by replaying the saved action prefix up to that step. We measure Success@5 on 83 samples after excluding instances where action replay fails.

##### Fixed annotations

For each failed instance, we annotate an error step $\mathrm{E}$ once before running any recovery-step experiment. The annotation stage reads the saved trajectory, reconstructs the observation-action history, and calls the LLM error-step detector. When evaluating the LLM-selected recovery step, we also annotate a recovery step $\mathrm{R_{\text{LLM}}}$ once in the same preparation stage. These annotations are then materialized into a fixed run plan, so different recovery-step conditions are evaluated against the same underlying failed trajectory rather than re-detecting $\mathrm{E}$ or $\mathrm{R_{\text{LLM}}}$ at runtime.

##### Recovery Steps

We compare four starting steps. $\mathrm{R=0}$ restarts from the initial environment state. $\mathrm{R=E-1}$ resumes from the step immediately before the detected error. $\mathrm{R=E-\text{random}}$ samples a previous step with a fixed seed and reuses the same sampled step across runs for that instance. $\mathrm{R=R_{\text{LLM}}}$ uses the recovery step predicted by the recovery-step detector. For $\mathrm{R>0}$ , the environment is reset and the saved action prefix up to $\mathrm{R}$ is replayed before the forward agent resumes. For $\mathrm{R=0}$ , no prefix is replayed.

##### Metric

For each instance and each condition, we draw five independent continuations from the selected recovery state, and report Success@ $\mathrm{K}$ for $\mathrm{K}\in\{1,\ldots,5\}$ . Each continuation begins with action-prefix replay to reconstruct the recovery state; because replay can occasionally desynchronize from the saved trajectory (e.g., due to UI timing), we retry replay up to three times per continuation. Success@ $\mathrm{K}$ measures whether at least one of the $\mathrm{K}$ successfully reconstructed continuations from the same recovery state completes the task, and reflects how much of the agent’s latent task-solving ability is exposed by recovery.

### B.2 End-to-End Evaluation

##### Benchmark

We evaluate on the OSWorld ([Xie et al., 2024](#bib.bib45)) benchmark, where we follow a consistent setting as [A.1](#A1.SS1).

##### Forward agents

We use three open-source models as the forward agent: Qwen3.5-9B ([Qwen Team, 2026a](#bib.bib39)) with thinking mode, UI-TARS-1.5-7B ([Qin et al., 2025](#bib.bib12)), and EvoCUA-32B ([Xue et al., 2026](#bib.bib43)), following the setup in Section [A.1](#A1.SS1), where default system prompts and instructions in Section [A.1](#A1.SS1) are provided. Within each end-to-end experiment, the recovery agent shares the same backbone as the forward agent; the two differ only in their prompts and step budgets. For all forward agents we set max\_steps to $50$ . Temperatures are chosen from each model’s official inference recipe except for EvoCUA-32B: its default temperature of $0.0$ produces deterministic outputs, which would cause the forward agent to repeat the same action when it resumes from a past state, so we set it to $0.7$ to preserve action diversity after recovery. The resulting values are $0.7$ for EvoCUA-32B, $0.7$ for Qwen3.5-9B-Thinking, and $1.0$ for UI-TARS-1.5-7B. The max\_tokens budget is $32768$ for EvoCUA-32B (to accommodate its long reasoning trace), $3000$ for Qwen3.5-9B-Thinking, and $500$ for UI-TARS-1.5-7B.

##### Detectors

Both the error-step detector and the recovery-step detector are LLM-based and share Qwen3.6-Plus ([Qwen Team, 2026b](#bib.bib61)) as their backbone, accessed through the OpenRouter API33
3
<https://openrouter.ai/> with a temperature of 0.7 and custom system prompts (Figure [36](#A6.F36), [37](#A6.F37)). The error detector is queried once per forward step. Once a recovery is triggered, the error detector is frozen for the next $5$ steps; this prevents the detector from re-interrupting the forward agent before any recovery-induced changes have a chance to take effect.

##### Recovery agent

The recovery agent is given a recovery step budget of $10$ steps per attempt and is triggered at most max\_recovery\_iteration times per episode, with max\_recovery\_iteration $\in\{1,3,5\}$ , using the identical system prompt and instructions as Section [A.2](#A1.SS2). Recovery steps are tracked separately from the forward agent’s step budget. When all retries are exhausted, the forward agent continues without further recovery activation.

##### Post-recovery context

After recovery completes, the forward agent resumes from the recovery-step context where the message history is truncated to the recovery boundary, and a short transition string informing the agent that the environment has been recovered is prepended before the next forward decision.

### B.3 Human Evaluation

When constructing the human evaluation sets, we sample recovery results from three representative models, including Claude-Sonnet-4.6, Qwen3.5-9B, and EvoCUA-32B, across both short- and long-horizon evaluation settings in OSWorld, as well as the short-horizon setting in WindowsAgentArena. We compare ReTrace against three baselines: variants of our oracle evaluator with either $\mathcal{R}_{O}$ or $\mathcal{R}_{\mathrm{TC}}$ removed, and GPT-5.4, a state-of-the-art model with extensive computer-use knowledge. We collect cases where the evaluation decisions produced by the oracle implemented in ReTrace differ from those of the alternative evaluators, and randomly sample 50 instances for each variant, resulting in a total of 150 evaluation samples in Table [1](#S5.T1).
For the image-wise matching evaluator, we provide only the recovery target screenshot and the screenshot after the final recovery step. For the Transition-Consistent evaluator, success is determined solely based on whether replaying the remaining actions from the recovered state successfully reaches the original task goal. For GPT-5.4, we provide the history of observation-action pairs leading up to the error step, the recovery trajectory generated by the recovery agent, the recovery target screenshot, the error-step screenshot, and the final recovered-state screenshot. GPT-5.4 is then prompted to determine whether the semantic meaning of the recovered state aligns with the target recovery state, following the same context and inputs provided to human annotators for a fair comparison (See Figure [38](#A6.F38) for prompt details).

After constructing the evaluation set, we split the 50 samples for each variant into two subsets and assigned two human annotators to each subset. In total, we recruited 12 annotators (4 annotators for each variant) who were researchers based in South Korea and highly proficient in computer-use tasks and voluntarily consented to participate in the study, with each annotator compensated approximately 20 USD for their participation, provided with detailed guideline for objective evaluation (Figure [11](#A5.F11)). Each pair of annotators independently evaluated whether the recovery target state had been successfully restored, labeling each sample in a binary success-or-failure manner consistent with our evaluators, while optionally indicating whether their decision was made despite stochastic environment dynamics (e.g., different timestamps or pop-ups) when the recovery process was believed to be successful, allowing us to analyze the effect of such environment dynamics on oracle judgments in ReTrace (Table [11](#A3.T11)).

Using these annotations as reference labels, we compared the decisions from our oracle evaluator against those from the alternative evaluators and measured their alignment with human judgments. Specifically, we independently computed the win rate of our oracle evaluator against each baseline for every annotator pair, and report the average win rate across all four subsets per variant in Table [1](#S5.T1). Across annotator pairs, we additionally observed an average agreement rate of 82% and a Cohen’s kappa coefficient of 0.45 ([Cohen, 1960](#bib.bib3)).

## Appendix C Supplementary Experiments

Here, we provide additional experiments to further support the results and analysis in the main paper.

![](images/25_ReTRACE/recovery_success_rate_windowsagentarena_full.svg)


Figure 9: Expanded Results on WindowsAgentArena from Figure [5](#S5.F5).

##### Additional Results on WindowsAgentArena

In Figure [9](#A3.F9), we present the full results on WindowsAgentArena, reporting the individual recovery success rates of each policy model. These results complement the average recovery success rates of the implicit and explicit recovery variants reported in Figure [5](#S5.F5). The results are consistent with the overall trend observed across our experiments: current computer-use agents possess latent recovery capabilities rather than lacking them entirely, but they do not reliably invoke these capabilities during inference (Finding 2, Finding 3). Moreover, the results further support our Finding 4, where generalist agents exhibit stronger recovery capabilities overall. Specifically, Claude-Sonnet-4.6, GPT-5.4-CUA, and Qwen-3.5-9B achieve higher recovery success rates under implicit recovery and generally exhibit larger performance gains when explicitly instructed to perform recovery. These additional analyses further substantiate the claims and major findings presented in our original paper.

| Model | Max 2 | Max 4 | Max 5 | Max 10 |
| --- | --- | --- | --- | --- |
| Claude-Sonnet-4.6 | 26.98 | 13.34 | 8.76 | 6.37 |
| GPT-5.4-CUA | 17.85 | 6.30 | 5.81 | 5.15 |
| Qwen3.5-9B | 12.04 | 7.29 | 6.12 | 5.29 |
| EvoCUA-32B | 0.86 | 2.00 | 0.86 | 1.44 |
| UI-TARS-1.5-7B | 7.26 | 7.81 | 12.31 | 7.82 |

Table 8: Implicit recovery success rate (%) across diverse max recovery step budgets in OSWorld benchmark. We report the mean success rate across three different trials from three independently sampled evaluation sets.

##### Robust Suboptimal Implicit Recovery

The results in Table [8](#A3.T8) show that current computer-use agents struggle to perform restorative actions across different recovery budgets. Moreover, the recovery success rates of most agents consistently decrease as the maximum number of recovery steps increases, suggesting that simply allowing more steps does not resolve their recovery limitations. Notably, however, success rates do not drop to zero, suggesting that agents retain some latent ability to perform restorative actions but fail to reliably leverage it under failure scenarios. These findings further support our main-paper conclusion that current computer-use agents struggle to effectively realize their restorative capabilities when recovering from failures (Finding 2, Finding 3).

|  | Temperature | Max Tokens | Short Horizon | Long Horizon |
| --- | --- | --- | --- | --- |
| EvoCUA -32B | 1.0 | 32768 | 0.00 | 7.94 |
| 1.0 | 16384 | 1.75 | 4.76 |  |
| 0.0 | 32768 | 3.51 | 20.63 |  |
| 0.0 | 16384 | 4.39 | 6.35 |  |
| UI-Tars- 1.5-7B | 1.0 | 1000 | 31.67 | 25.00 |
| 1.0 | 500 | 26.67 | 26.67 |  |
| 0.0 | 1000 | 26.67 | 21.67 |  |
| 0.0 | 500 | 26.67 | 13.33 |  |

Table 9: Recovery Success Rate (%) across two different models with different hyper parameters using Recovery Target Contextualization in OSWorld benchmark.


|  | Temperature | Max Tokens | Top_P | Success Rate (%) |
| --- | --- | --- | --- | --- |
| EvoCUA -32B | 0.7 | 32768 | 0.95 | 18.00 |
| 1.0 | 32768 | 0.95 | 14.00 |  |
| 1.0 | 16384 | 0.95 | 20.00 |  |
| 0.0 | 32768 | 0.95 | 20.00 |  |
| 0.0 | 16384 | 0.95 | 18.00 |  |

Table 10: Recovery Success Rate (%) of EvoCUA-32B with different hyper parameters using Recovery Target Contextualization in WindowsAgentArena benchmark.

![](images/25_ReTRACE/recovery_success_rate_comparison_short_horizon_osworld_dataset_average.svg)


Figure 10: Three-run average recovery success rates for each recovery variant across three randomly sampled recovery evaluation sets in ReTrace.

##### Hyperparameter Ablation Study

To further validate the robustness of our findings, we provide an additional analysis of the recovery capabilities of state-of-the-art computer-use agents under different hyperparameter settings in Table [9](#A3.T9), using the Recovery Target Contextualization setting. The results consistently show that EvoCUA-32B exhibits limited recovery capability even under explicit recovery prompting, compared to UI-TARS-1.5-7B across a wide range of hyperparameter configurations. Furthermore, the recovery success rate also remains robust across diverse hyper parameter settings for EvoCUA in WindowsAgentArena (Table [10](#A3.T10)). This finding highlights the inherent limitation of the EvoCUA-32B post-trained model, despite being extensively trained on offline trajectory data. In other words, even with explicit recovery guidance, the model remains unable to reliably restore previous states regardless of the hyper parameter settings. These observations further reinforce the results presented in Figure [4](#S5.F4) and Figure [7](#S5.F7).

##### Dataset Robustness Analysis

In Figure [10](#A3.F10), we show that the trend observed in Figure [4](#S5.F4) remains consistent across different randomly sampled recovery evaluation sets. We randomly sample two additional recovery evaluation sets for respective policy model, each containing the same number of samples as the original set, and measure the recovery success rate of each policy model on all three sets (including one used in our main experiments). We then compute the macro-average success rate across the three evaluation sets for each recovery variant of each policy model. The results closely mirror the trend observed in Figure [4](#S5.F4): explicit recovery instructions yield substantial gains over implicit recovery, demonstrating that current computer-use agents possess recovery capabilities but fail to reliably invoke them during inference (Finding 2, Finding 3). Furthermore, post-trained models such as EvoCUA exhibit nearly no recovery capability, while UI-TARS shows only modest improvements with explicit recovery instructions. In contrast, generalist agents (Claude, GPT-5.4, and Qwen) exhibit substantial gains from explicit recovery instructions. These results further support our claim, suggesting that extensive post-training on one-directional task-completion trajectories may suppress or weaken the inherent recovery capabilities of computer-use agents (Finding 4). Furthermore, in Table [8](#A3.T8), we show that across three randomly sampled recovery evaluation sets, current computer-use agents rarely have restorative behavior (Finding 2), and its performance is robust regardless of evaluation set.

| Oracle | Unaffected Rate (%) |
| --- | --- |
| ReTrace (All) | 86.0 (%) |

Table 11: Analysis on the rate of oracle evaluations unaffected by stochastic environmental dynamics.

##### Effect of Environment Dynamics on ReTrace

In addition, we investigate the impact of stochastic transition dynamics, such as pop-ups, rendering variations, and dynamic timestamps, on the judgments of our oracle evaluation framework. Specifically, we conduct a human study following the same protocol as in Table [1](#S5.T1) and Appendix [B.3](#A2.SS3). Annotators are asked to determine whether a successfully recovered state differs from the target state only due to ignorable environmental variations. Since recovery failures identified by human annotators are not attributed to environmental dynamics (see the evaluation guidelines in Figure [11](#A5.F11)), this evaluation quantifies how often our oracle incorrectly judges a successful recovery as failure due to stochastic environmental variations. To obtain a reliable estimate, we consider only cases where both annotators agree on a judgment on both recovery success and environmental effect. From these cases, we sample instances where the human judgment disagrees with ReTrace, and both agree that there exists stochastic environmental dynamics. Finally, we eliminate the same recovery evaluation set distributed across the independent evaluation sets (GPT-5.4 evaluator, w/o $\mathcal{R}_{\mathrm{O}}$ , w/o $\mathcal{R}_{\mathrm{TC}}$ ) from Table [1](#S5.T1) and compute micro-average ratio. The results in Table [11](#A3.T11) show that ReTrace is largely robust to stochastic environmental dynamics: 86.0% of the ReTrace judgments were favorable decisions unaffected by stochastic environmental dynamics. Furthermore, since this analysis is performed on a challenging subset consisting exclusively of disagreement cases between different oracles, the overall adverse effect of stochastic environmental dynamics on the judgments of ReTrace is expected to be even smaller in practice.

##### Analysis on the $\mathcal{R}_{\mathrm{O}}$ and $\mathcal{R}_{\mathrm{TC}}$ disagreements

Furthermore, we analyze the quality of the judgments made by ReTrace in cases where the two oracles, $\mathcal{R}_{\mathrm{O}}$ and $\mathcal{R}_{\mathrm{TC}}$ , disagree. Specifically, we sample disagreement cases between $\mathcal{R}_{\mathrm{O}}$ and $\mathcal{R}_{\mathrm{TC}}$ from the human evaluation sets (Tables [1](#S5.T1) and [11](#A3.T11)). Following the protocol in Table [11](#A3.T11), we consider only samples for which both human annotators within each evaluation subset agree on a recovery success evaluation. We then measure the agreement rate between human judgments and oracle decisions when using $\mathcal{R}_{\mathrm{O}}$ , and $\mathcal{R}_{\mathrm{TC}}$ alone, and both oracles jointly, among such samples using the micro-average protocol demonstrated in Table [11](#A3.T11). The results in Table [12](#A3.T12) demonstrate that the joint use of two oracles provides complementary strength and that the combination of them yields higher agreement with human judgments than either oracle alone, compared to utilizing each oracle in isolation, further indicating that even in disagreement situations, ReTrace can provide objective evaluation results.

| Oracle | Alignment Rate (%) |
| --- | --- |
| $\mathcal{R}_{\mathrm{TC}}$ | 38.8 (%) |
| $\mathcal{R}_{\mathrm{O}}$ | 61.2 (%) |
| ReTrace | 81.2 (%) |

Table 12: Analysis on the alignment rate of oracle judgments with human annotations using samples under $\mathcal{R}_{\mathrm{O}}$ and $\mathcal{R}_{\mathrm{TC}}$ disagreement.


| Threshold | Alignment Rate (%) |
| --- | --- |
| 0.99 | 56.9 (%) |
| 0.95 | 33.9 (%) |
| 0.91 | 26.6 (%) |

Table 13: Analysis of the Effect of the SSIM Threshold on the Alignment Between $\mathcal{R}_{\mathrm{O}}$ and Human Judgments.

##### Analysis of ReTrace’s Sensitivity to the SSIM Threshold

Finally, we analyze the sensitivity of $\mathcal{R}_{\mathrm{O}}$ to the SSIM threshold, which is set to 0.99 by default. Table [13](#A3.T13) reports the alignment between the judgments of $\mathcal{R}_{\mathrm{O}}$ and human annotations under different SSIM thresholds. Following the protocol used in Tables [11](#A3.T11) and [12](#A3.T12), we sample a common set of instances for which both human annotators agree on whether the recovery is successful, and measure the proportion of agreement between $\mathcal{R}_{\mathrm{O}}$ and the corresponding human judgments across different thresholds among such samples. The results show that lowering the SSIM threshold causes $\mathcal{R}_{\mathrm{O}}$ to overestimate recovery success, substantially reducing its alignment with human annotations. These findings justify our design choice of adopting a strict SSIM threshold of 0.99 in ReTrace to ensure high-fidelity screenshot-level matching.

## Appendix D Qualitative Analyses

Here, we provide additional qualitative examples that explain the behavior pattern of computer agents under suboptimal recovery demonstrated in Table [14](#A4.T14).

| Error Type | Instruction | Target State | Restored State | Action | Problem |
| --- | --- | --- | --- | --- | --- |
| Spurious Perception | Align the text of the first textbox on slide 3 to the right , on slide 4 to the center, and on slide 5 to the left. |  |  | [click] on the hovering alignment button to align slide 3 the text to the right. | Fixates on to the hovering UI element in recovered state , skipping [drag] on the text before clicking the alignment button. |
| Spurious Perception | Please help me change the color theme of VS Code to Visual Studio Dark. |  |  | [click] Activities element in the top left corner to launch vscode application | Fixates on to the UI element appearing in the restored state, unable to correctly click vscode application after restoration. |
| Spurious Perception | Could you help me remove the dock on the left side of the screen in the GIMP? |  |  | [click] on windows option in the right window to explore options for removing the dock | Fixates on to the new windows option irrelevant to removing the dock option , fails to generate correct actions due to incorrect state restoration. |
| State Tracking Failure | Change the font to "Times New Roman" throughout the text. |  |  | [scroll down] to find Times New Roman, since font selection interface is opened. | Hallucinates the restored state due to failed state synchronization with its previous states. |
| State Tracking Failure | Help me freeze the range A1:B1 on this sheet to keep the headers always visible. |  |  | [Drag] from column A1 to B1, in order to accurately select the area we want to freeze | Hallucinates that the restored state allows clicking the range A1 to B1, when in fact, cannot be dragged , failing to synchronize with the actual prior state. |
| State Tracking Failure | Please modify VS Code’s settings to disable error reporting for Python missing imports. |  |  | [hotkey(key=’ctrl shift p’)] I checked the results, but there’s nothing in the search box. I’m aware of a better solution. | Hallucinates that the restored state has blank results, just like the recovery target state , leading to completely novel behavior. |
| State Tracking Failure | Find flights from Seattle to New York on 5th next month and only show those that can be purchased with miles. |  |  | [click] I located the button labeled "South Korea - English" and clicked on it to continue booking my flight. | Hallucinates the current state as clickable based on the target-state observation , failing to correctly synchronize with the actual system state. |
| State Tracking Failure | Set the background color to yellow for any slide that contains one or more images of real people, and set the title of slide 2 as "Let’s start". |  |  | [click] I’ve already changed the background on the third slide to yellow, it’s time to change fourth one. | Hallucinates the current state as being on the fourth slide instead of third, unable to synchronize with the erroneous recovered state. |

Table 14: Additional Qualitative analysis of erroneous agent behaviors induced by imperfect state restoration.

## Appendix E Human Evaluation Guidelines

In this section, we provide the guidelines for human
evaluation provided to the participants in Table
[1](#S5.T1).

Human Evaluation Guideline

You will be provided with:

- Goal Screenshot

- Error-Step Screenshot

- Final Recovery Screenshot

- Original Instruction

- Recovery Trajectory

- Original Execution Trajectory

- Your task is to determine whether the recovery process successfully restores the environment to the intended goal state.

Evaluation Objective

- Evaluate whether the Final Recovery Screenshot is functionally equivalent to the Goal Screenshot.

- Success (1): the environment is correctly restored

- Failure (0): the environment is not properly restored

Evaluation Principles

1. Prioritize Visual Similarity

The primary signal is the visual similarity between the Final Recovery Screenshot and the Goal Screenshot. Please carefully compare the screenshots at a fine-grained, segment-level detail, including interaction-dependent UI elements. Pay close attention to whether:

- active windows or pages differ,

- selected content or tabs change,

- focused text boxes differ,

- dropdowns or menus are opened differently,

- cursor positions or hover states change,

- highlighted or selected UI elements differ,

- drag-and-drop states change, or other interaction-sensitive regions are inconsistent.

Mark as Failure (0) if important visual or interaction-level differences remain.

\*\*Important\*\* Minor differences caused by dynamic environments (e.g., notifications, pop-ups, timestamps, loading indicators, rendering variations) can be ignored if the underlying functional state remains equivalent.

2. Verify Functional Recovery

The recovered state should allow the original task to continue correctly.

Even if screenshots appear visually similar, mark as Failure (0) if:-

- important interaction context is missing,

- unintended changes remain,

- incorrect files/pages/windows are active,

or the operational state is not properly restored.

Use the recovery trajectory and original trajectory to understand:

- what actions changed the environment,

- whether erroneous states were actually reverted,

- and whether the recovery process is consistent with the intended goal state.

Trajectory information is especially important when screenshots appear visually similar but the actual operational state may still differ.

Final Output

Binary Label: 1 for Success

Binary Label: 0 for Failure

Final Output (Optional If Recovery is Successful)

If you believe that the recovery is successful, please determine whether the successful recovery decision was despite ignorable observation differences caused by minor dynamic environmental changes such as notifications, pop-ups, timestamps, loading indicators, and rendering variations.

  
Binary Label: 1 for YES

Binary Label: 0 for NO

Figure 11: Human Evaluation Guideline

## Appendix F Prompts

Here, we provide the prompts in our experiments.

System Prompt for Claude-Sonnet-4.6 Forward Agent in OsWorld

<SYSTEM\_CAPABILITY>

\* You are utilising an Ubuntu virtual machine using x86\_64 architecture with internet access.

\* You can feel free to install Ubuntu applications with your bash tool. Use curl instead of wget.
\* To open browser, please just click on the Chrome icon. Note, Chrome is what is installed on your system.

\* Using bash tool you can start GUI applications, but you need to set export DISPLAY=:1 and use a subshell. For example "(DISPLAY=:1 xterm &)". GUI apps run with bash tool will appear within your desktop environment, but they may take some time to appear. Take a screenshot to confirm it did.

\* When using your bash tool with commands that are expected to output very large quantities of text, redirect into a tmp file and use str\_replace\_editor or ‘grep -n -B <lines before> -A <lines after> <query> <filename>‘ to confirm output.

\* When viewing a page it can be helpful to zoom out so that you can see everything on the page. Either that, or make sure you scroll down to see everything before deciding something isn’t available.

\* DO NOT ask users for clarification during task execution. DO NOT stop to request more information from users. Always take action using available tools.

\* When using your computer function calls, they take a while to run and send back to you. Where possible/feasible, try to chain multiple of these calls all into one function calls request.

\* TASK FEASIBILITY: You can declare a task infeasible at any point during execution - whether at the beginning after taking a screenshot, or later after attempting some actions and discovering barriers. Carefully evaluate whether the task is feasible given the current system state, available applications, and task requirements. If you determine that a task cannot be completed due to:

- Missing required applications or dependencies that cannot be installed

- Insufficient permissions or system limitations

- Contradictory or impossible requirements

- Any other fundamental barriers that make completion impossible

Then you MUST output exactly "[INFEASIBLE]" (including the square brackets) anywhere in your response to trigger the fail action. The system will automatically detect this pattern and terminate the task appropriately.

\* The current date is {current\_date}.

\* Home directory of this Ubuntu system is ’/home/user’.

\* If you need a password for sudo, the password of the computer is {password}.

</SYSTEM\_CAPABILITY>

  
<IMPORTANT>

\* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.

</IMPORTANT>

Figure 12: System Prompt for Claude-Sonnet-4.6 Forward Agent in OsWorld

System Prompt for Claude-Sonnet-4.6 Forward Agent in WindowsAgentArena

<SYSTEM\_CAPABILITY>

\* You are utilising a Windows virtual machine using x86\_64 architecture with internet access.

\* To open browser, please just click on the Chrome icon. Note, Chrome is what is installed on your system.

\* When viewing a page it can be helpful to zoom out so that you can see everything on the page. Either that, or make sure you scroll down to see everything before deciding something isn’t available.

\* When you want to open some applications on Windows, please use Double Click on it instead of clicking once.

</SYSTEM\_CAPABILITY>

Figure 13: System Prompt for Claude-Sonnet-4.6 Forward Agent in WindowsAgentArena

System Prompt for Evocua-32B forward agent in OsWorld

# Tools

You may call one or more functions to assist with the user query.

  
You are provided with function signatures within <tools></tools> XML tags:

<tools>

{tools\_xml}

</tools>

  
For each function call, return a json object with function name and arguments within <tool\_call></tool\_call> XML tags:

<tool\_call>

{"name": <function-name>, "arguments": <args-json-object>}

</tool\_call>

  
The current date is {date}

If you need a password for sudo, the password of the computer is {client\_password}

  
# Response format

Response format for every step:

1) Action: a short imperative describing what to do in the UI.

2) A single <tool\_call>...</tool\_call> block containing only the JSON: {"name": <function-name>, "arguments": <args-json-object>}.

  
Rules:

- Output exactly in the order: Action, <tool\_call>.

- Be brief: one sentence for Action.

- Do not output anything else outside those parts.

- If finishing, use action=terminate in the tool call.

Figure 14: System Prompt for Evocua-32B forward agent in OsWorld

System Prompt used for Evocua-32B forward agent in WindowsAgentArena

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:

<tools>

{tools\_xml}

</tools>

  
For each function call, return a json object with function name and arguments within <tool\_call></tool\_call> XML tags:

<tool\_call>

{"name": <function-name>, "arguments": <args-json-object>}

</tool\_call>

  
# Response format

Response format for every step:

1) Action: a short imperative describing what to do in the UI.

2) A single <tool\_call>...</tool\_call> block containing only the JSON: {"name": <function-name>, "arguments": <args-json-object>}.

  
Rules:

- Output exactly in the order: Action, <tool\_call>.

- Be brief: one sentence for Action.

- Do not output anything else outside those parts.

- If finishing, use action=terminate in the tool call.

Figure 15: System Prompt used for Evocua-32B forward agent in WindowsAgentArena

Tool description prompt used for Evocua-32B agent

{"type": "function",

  "function": {

    "name\_for\_human": "computer\_use",

    "name": "computer\_use",

    "description": description\_prompt,

    "parameters": {

     "properties": {

      "action": {

       "description": S2\_ACTION\_DESCRIPTION,

       "enum": ["key", "type", "mouse\_move", "left\_click", "left\_click\_drag",

       "right\_click", "middle\_click", "double\_click", "triple\_click",

       "scroll", "wait", "terminate", "key\_down", "key\_up"],

       "type": "string"

      },

      "keys": {

       "description": "Required only by ‘action=key‘.",

       "type": "array"

      },

      "text": {

       "description": "Required only by ‘action=type‘.",

       "type": "string"

      },

      "coordinate": {

       "description": "The x,y coordinates for mouse actions.",

       "type": "array"

      },

      "pixels": {

       "description": "The amount of scrolling.",

       "type": "number"

      },

      "time": {"description": "The seconds to wait.", "type": "number"},

      "status": {

       "description": "The status of the task.",

       "type": "string",

       "enum": ["success", "failure"]

      }

     },

     "required": ["action"],

     "type": "object"

    },

    "args\_format": "Format the arguments as a JSON object."

    }

}

Figure 16: Tool description prompt used for Evocua-32B agent

Description Prompt used for Evocua-32B agent

Use a mouse and keyboard to interact with a computer, and take screenshots.

\* This is an interface to a desktop GUI. You must click on desktop icons to start applications.

\* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn’t open, try wait and taking another screenshot.

{resolution\_info}

\* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.

\* If you tried clicking on a program or link but it failed to load even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.

\* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don’t click boxes on their edges unless asked.

Figure 17: Description Prompt used for Evocua-32B agent

Action description prompt used for Evocua-32B agent

\* ‘key‘: Performs key down presses on the arguments passed in order, then performs key releases in reverse order.

\* ‘key\_down‘: Press and HOLD the specified key(s) down in order (no release). Use this for stateful holds like holding Shift while clicking.

\* ‘key\_up‘: Release the specified key(s) in reverse order.

\* ‘type‘: Type a string of text on the keyboard.

\* ‘mouse\_move‘: Move the cursor to a specified (x, y) pixel coordinate on the screen.

\* ‘left\_click‘: Click the left mouse button at a specified (x, y) pixel coordinate on the screen.

\* ‘left\_click\_drag‘: Click and drag the cursor to a specified (x, y) pixel coordinate on the screen.

\* ‘right\_click‘: Click the right mouse button at a specified (x, y) pixel coordinate on the screen.

\* ‘middle\_click‘: Click the middle mouse button at a specified (x, y) pixel coordinate on the screen.

\* ‘double\_click‘: Double-click the left mouse button at a specified (x, y) pixel coordinate on the screen.

\* ‘triple\_click‘: Triple-click the left mouse button at a specified (x, y) pixel coordinate on the screen.

\* ‘scroll‘: Performs a scroll of the mouse scroll wheel.

\* ‘hscroll‘: Performs a horizontal scroll (mapped to regular scroll).

\* ‘wait‘: Wait specified seconds for the change to happen.

\* ‘terminate‘: Terminate the current task and report its completion status.
\* ‘answer‘: Answer a question.

Figure 18: Action description prompt used for Evocua-32B agent

Action space used for UI-Tars-1.5-7B forward agent

click(start\_box=’<|box\_start|>

(x1,y1)<|box\_end|>’)

left\_double(start\_box=’<|box\_start|>

(x1,y1)<|box\_end|>’)

right\_single(start\_box=’<|box\_start|>

(x1,y1)<|box\_end|>’)

drag(start\_box=’<|box\_start|>

(x1,y1)<|box\_end|>’,

end\_box=’<|box\_start|>

(x3,y3)<|box\_end|>’)
hotkey(key=’’)

type(content=’’) #If you want to submit your input, use "

n" at the end of ‘content‘.

scroll(start\_box=’<|box\_start|>

(x1,y1)<|box\_end|>’, direction=’down or up or right or left’)

wait() #Sleep for 5s and take a screenshot to check for any changes.

finished(content=’xxx’) # Use escape characters

’,

", and

n in content part to ensure we can parse the content in normal python string format.

Figure 19: Action space used for UI-Tars-1.5-7B forward agent

System prompt used for GPT-5.4-CUA agent in OsWorld benchmark

Here are some helpful tips:

- My computer password is "{CLIENT\_PASSWORD}" when sudo is needed.

- Stick to the website or application already opened for the task when possible.

- Prefer Chrome over Firefox/Chromium unless the task says otherwise.

- You can act without asking for confirmation.

- If the task is infeasible, say so explicitly.

Figure 20: System prompt used for GPT-5.4-CUA agent in OsWorld benchmark

System prompt used for QWEN-3.5-9B forward agent in OsWorld

You are a multi-purpose intelligent assistant. Based on my requests, you can use tools to help me complete various tasks.

# Tools

You have access to the following functions:

<tools>

{json.dumps(tools\_def)}

</tools>

  
If you choose to call a function ONLY reply in the following format with NO suffix:

<tool\_call>

<function=example\_function\_name>

<parameter=example\_parameter\_1>

value\_1

</parameter>

<parameter=example\_parameter\_2>

This is the value for the second parameter

that can span

multiple lines

</parameter>

</function>

</tool\_call>

  
<IMPORTANT>

Reminder:

- Function calls MUST follow the specified format: an inner <function=...></function> block must be nested within <tool\_call></tool\_call> XML tags

- Required parameters MUST be specified

- You may provide optional reasoning for your function call in natural language BEFORE the function call, but NOT after

- If there is no function call available, answer the question like normal with your current knowledge and do not tell the user about function calls

- The current date is {datetime.today().strftime(’%A, %B %d, %Y’)}.

- Collapsed screenshots appear as text: {self.collapse\_text}

If you need a password for sudo, the password of the computer is {self.client\_password}

</IMPORTANT>

# Response format

Response format for every step:

1) Action: a short imperative describing what to do in the UI.

2) A single <tool\_call>...</tool\_call> block.

  
Rules:

- Output exactly in the order: Action, <tool\_call>.

- Be brief: one sentence for Action.

- Do not output anything else outside those parts.

- If finishing, use action=terminate in the tool call.

Figure 21: System prompt used for QWEN-3.5-9B forward agent in OsWorld

System prompt used for GPT-5.4-CUA agent in WindowsAgentArena

Here are some helpful tips:

- Stick to the website or application already opened for the task when possible.

- Prefer Chrome over Firefox/Chromium unless the task says otherwise.

- You can act without asking for confirmation.

- If the task is infeasible, say so explicitly.

Figure 22: System prompt used for GPT-5.4-CUA agent in WindowsAgentArena

System prompt used for Qwen-3.5-9B agent in WindowsAgentArena

You are a multi-purpose intelligent assistant. Based on my requests, you can use tools to help me complete various tasks.

  
# Tools

  
You have access to the following functions:

  
<tools>

{json.dumps(tools\_def)}

</tools>

  
If you choose to call a function ONLY reply in the following format with NO suffix:

  
<tool\_call>

<function=example\_function\_name>

<parameter=example\_parameter\_1>

value\_1
</parameter>

<parameter=example\_parameter\_2>
This is the value for the second parameter

that can span

multiple lines

</parameter>

</function>

</tool\_call>

  
<IMPORTANT>

Reminder:

- Function calls MUST follow the specified format: an inner <function=...></function> block must be nested within <tool\_call></tool\_call> XML tags
- Required parameters MUST be specified

- You may provide optional reasoning for your function call in natural language BEFORE the function call, but NOT after

- If there is no function call available, answer the question like normal with your current knowledge and do not tell the user about function calls

- Collapsed screenshots appear as text: {self.collapse\_text}

</IMPORTANT>

  
# Response format

  
Response format for every step:

1) Action: a short imperative describing what to do in the UI.

2) A single <tool\_call>...</tool\_call> block.

  
Rules:

- Output exactly in the order: Action, <tool\_call>.

- Be brief: one sentence for Action.

- Do not output anything else outside those parts.

- If finishing, use action=terminate in the tool call.

Figure 23: System prompt used for Qwen-3.5-9B agent in WindowsAgentArena

Action description prompt used for QWEN3.5-9B agent

\* ‘key‘: Performs key down presses on the arguments passed in order, then performs key releases in reverse order.

\* ‘type‘: Type a string of text on the keyboard.

\* ‘mouse\_move‘: Move the cursor to a specified (x, y) pixel coordinate on the screen.

\* ‘left\_click‘: Click the left mouse button at a specified (x, y) pixel coordinate on the screen. Optional ‘text‘ parameter can specify modifier keys (e.g., "ctrl", "shift", "ctrl+shift") that will be held during the click.

\* ‘left\_click\_drag‘: Click and drag the cursor to a specified (x, y) coordinate.

\* ‘right\_click‘: Click the right mouse button at a specified (x, y) pixel coordinate on the screen.

Optional ‘text‘ parameter can specify modifier keys that will be held during the click.

\* ‘middle\_click‘: Click the middle mouse button at a specified (x, y) pixel coordinate on the screen. Optional ‘text‘ parameter can specify modifier keys that will be held during the click.

\* ‘double\_click‘: Double-click the left mouse button at a specified (x, y) pixel coordinate on the screen. Optional ‘text‘ parameter can specify modifier keys that will be held during the click.

\* ‘triple\_click‘: Triple-click the left mouse button at a specified (x, y) pixel coordinate on the screen (simulated as double-click since it’s the closest action). Optional ‘text‘ parameter can specify modifier keys that will be held during the click.

\* ‘scroll‘: Performs a scroll of the mouse scroll wheel. Optional ‘text‘ parameter can specify a modifier key (e.g., "shift", "ctrl") that will be held during scrolling.

\* ‘hscroll‘: Performs a horizontal scroll (mapped to regular scroll). Optional ‘text‘ parameter can specify a modifier key that will be held during scrolling.

\* ‘wait‘: Wait specified seconds for the change to happen.

\* ‘terminate‘: Terminate the current task and report its completion status.

\* ‘answer‘: Answer a question.

Figure 24: Action description prompt used for QWEN3.5-9B agent

User prompt used for UI-Tars-1.5-7B forward agent

You are a GUI agent. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Output Format

‘‘‘

Thought: ...

Action: ...

‘‘‘

## Action Space

{action\_space}

## Note

- Use {language} in ‘Thought‘ part.

- Write a small plan and finally summarize your next action (with its target element) in one sentence in ‘Thought‘ part.

## User Instruction

{instruction}

Figure 25: User prompt used for UI-Tars-1.5-7B forward agent

Tool description prompt used for QWEN3.5-9B agent

"type": "function",

  "function": {

    "name": "computer\_use",

    "description": description\_prompt,

    "parameters": {

     "type": "object",

     "required": ["action"],

     "properties": {

      "action": {

       "type": "string",

       "description": action\_description\_prompt,

       "enum": [

        "key",

        "type",

        "mouse\_move",

        "left\_click",

        "left\_click\_drag",

        "right\_click",

        "middle\_click",

        "double\_click",

        "triple\_click",

        "scroll",

        "hscroll",

        "wait",

        "terminate",

        "answer",

        ],

       },

      "keys": {

       "type": "array",

       "description": "Required only by ‘action=key‘."},

      "text": {

       "type": "string",

       "description": "Required by ‘action=type‘ and ‘action=answer‘.         Optional for click actions (left\_click, right\_click, middle\_click,         double\_click, triple\_click) to specify modifier keys (e.g., ’ctrl’,         ’shift’, ’ctrl+shift’). Optional for scroll actions (scroll, hscroll) to specify a modifier key (e.g., ’shift’, ’ctrl’) to hold during scrolling.",

      },

      "coordinate": {

       "type": "array", "description": "(x, y) coordinates."
       },

      "pixels": {

       "type": "number", "description": "Scroll amount."},

       "time": {"type": "number", "description": "Seconds to wait."},

       "status": {

        "type": "string",

        "description": "Task status for terminate.",

        "enum": ["success", "failure"],

       },

      },

     },

    },

Figure 26: Tool description prompt used for QWEN3.5-9B agent

Prefix prompt used for perturbation agent

<Perturbation\_AGENT\_ROLE>

\* You are a Perturbation Agent. Your primary objective is to generate series of INCORRECT actions that causes a significant DRIFT from the user’s original instruction, such that the observation is completely different.

\* Your series of generated actions should lead to a completely unrelated state to the current instruction, forcing the system state into an unexpected or divergent path, where there it shows completely different scenery.

\* You will be provided with the current state and a "correct" action (the ground truth) from the given state.

\* Your initially generated action must be DIFFERENT from the provided action and should actively disrupt the flow of the task, leading to a completely different state. Try to make the path diverge as much as possible until you believe that the scenery is completely different.

\* Do not make a minor mistake; perform an active, significantly deviant steps that has nothing to do with the original goal.

\* While trying to create a significant drift, try your best effort to signficantly drift the current state via a single action, instead of doing a series of small mistakes.

</Perturbation\_AGENT\_ROLE>

<Perturbation\_COMPLETION>

\* To complete your task, you must output a series of actions that satisfies the following criteria, which you will be also given the history of disruptive flow of observation and actions you have performed:

    1. It is DIFFERENT from the provided correct action.

    2. It is a valid, executable action in the current state.

    3. It causes a SIGNIFICANT DRIFT from the intended goal (completely unrelated or divergent), to the point where the observation completely changes to different scenery.

    4. Since the given correct action is from the initial state, try to make the action only different from the given action when there are no past perturbation history, meaning that
the correct action only applies to the inital state, and not for the rest of the perturbation process.

    \* Once you have generated this single unrelated action, that constitutes the completion of your turn, which you must perform multiple times until the system state is completely different from the original instruction.

    \* While trying to create a significant drift, try your best effort to signficantly drift the current state via a single action, instead of doing a series of small mistakes. You should not try to complete the original task at all, and you must make a mistake or go off-track intentionally.

</Perturbation\_COMPLETION>

Figure 27: Prefix prompt used for perturbation agent

Prefix prompt used for GPT-5.4-CUA perturbation agent

<Perturbation\_AGENT\_ROLE>

\* You are a Perturbation Agent. Your primary objective is to generate a series of INCORRECT computer-use actions that cause a significant DRIFT from the user’s original instruction, such that the resulting observation becomes completely different from what the original task expects.

\* Your generated actions must lead to a completely unrelated state, forcing the system into an unexpected or divergent path where the screen shows completely different scenery.

\* You will be provided with the current screenshot, the user’s original instruction, and the ’correct’ action (the ground truth) from the initial state.

\* Your initially generated action must be DIFFERENT from the provided correct action and should actively disrupt the flow of the task, leading to a completely different state. Make the path diverge as much as possible until the scenery is completely different.

\* Do not make a minor mistake; perform an active, significantly deviant step that has nothing to do with the original goal.

\* Try your best effort to significantly drift the current state via a single action, instead of doing a series of small mistakes.

\* Do not output waiting actions that do not alter anything, such as "wait". You must generate an active, significantly deviant step that has nothing to do with the original goal, instead of making a minor mistake, meaning that the
observation and the state should drasticially change.

</Perturbation\_AGENT\_ROLE>

<Perturbation\_COMPLETION>

\* To complete your task, you must output a series of computer-use actions that satisfy the following criteria:

    1. The action is DIFFERENT from the provided correct action.

    2. The action is valid and executable in the current state.

    3. The action causes a SIGNIFICANT DRIFT from the intended goal (completely unrelated or divergent), to the point where the observation completely changes to different scenery.

    4. Since the given correct action is from the initial state, only the initial action must differ from the given correct action; subsequent actions only need to keep diverging from the original task.

\* Once the system state is completely different from the original instruction’s expected scenery, you may stop emitting actions.

\* You should NOT try to complete the original task at all. You MUST go off-track intentionally.

</Perturbation\_COMPLETION>

Figure 28: Prefix prompt used for GPT-5.4-CUA perturbation agent

Prefix prompt used for recovery agent (0-E)

<RECOVERY\_AGENT\_ROLE>

\* You are a Recovery Agent. Your primary objective is to navigate from the current Error State to the Goal State.
\* The Goal State image is labeled with "This is the GOAL STATE you need to return to" - this is your target destination.

\* The current state (Error Step) is where an error or deviation occurred, and you must find the path back to the Goal State.

\* Analyze the differences between the current state and Goal State, then execute actions to bridge that gap.

\* Focus on efficiency: take the most direct path to recovery while ensuring accuracy.

</RECOVERY\_AGENT\_ROLE>

<RECOVERY\_COMPLETION>

\* When you believe you have successfully returned to the Goal State:

   1. Take a screenshot to verify the current state matches the Goal State

   2. Compare visual elements carefully:

    - Window positions and sizes

    - UI component states (buttons, menus, dialogs)

    - Text content and input fields

    - Application state and open windows

    - Cursor position if relevant

   3. If the states match, output the "done" action to complete the recovery

   4. If they don’t match, identify remaining discrepancies and continue taking recovery actions

\* Be thorough in your comparison - minor differences may indicate incomplete recovery

\* Do not declare completion until you have verified through a fresh screenshot

</RECOVERY\_COMPLETION>

Figure 29: Prefix prompt used for recovery agent (0-E)

Recovery Instruction for recovery agent (0-E)

## RECOVERY TASK
You are a Recovery Agent. Your task is to navigate the system back to the Goal State.

### Goal State

The Goal State image is labeled with "This is the GOAL STATE you need to return to".

Use the available tools to navigate the system back to that state.

  
### Current Status

- Current step: Error Step {error\_step}

- Target: Return to Goal State (Step {goal\_step})

### Your Task

Analyze the difference between the current state and the Goal State, then take the necessary actions step by step to reach the Goal State.

Figure 30: Recovery Instruction for recovery agent (0-E)

Prefix prompt used for recovery agent (0-R)

<RECOVERY\_AGENT\_ROLE>

\* You are a Recovery Agent. Your primary objective is to navigate from the current Error State to the Goal State.

\* The Goal State image is labeled with "This is the GOAL STATE you need to return to" - this is your target destination.

\* The current state (Error Step) is where an error or deviation occurred, and you must find the path back to the Goal State.

\* Analyze the differences between the current state and Goal State, then execute actions to bridge that gap.

\* Focus on efficiency: take the most direct path to recovery while ensuring accuracy.

\* You will be provided with the description of the goal state for more detailed information to assist in your recovery process.

\* You will also be provided with information regarding the transition from the initial state to the goal state. Use such information to gain knowledge of the goal state.

</RECOVERY\_AGENT\_ROLE>

  
<RECOVERY\_COMPLETION>

\* When you believe you have successfully returned to the Goal State:

   1. Take a screenshot to verify the current state matches the Goal State

   2. Compare visual elements carefully:

    - Window positions and sizes

    - UI component states (buttons, menus, dialogs)

    - Text content and input fields

    - Application state and open windows

    - Cursor position if relevant

   3. If the states match, output the "done" action to complete the recovery

   4. If they don’t match, identify remaining discrepancies and continue taking recovery actions

\* Be thorough in your comparison - minor differences may indicate incomplete recovery

\* Do not declare completion until you have verified through a fresh screenshot

</RECOVERY\_COMPLETION>

Figure 31: Prefix prompt used for recovery agent (0-R)

Recovery Instruction for recovery agent (0-R)

## RECOVERY TASK

You are a Recovery Agent. Your task is to navigate the system back to the Goal State.

### Goal State

The Goal State image is labeled with "This is the GOAL STATE you need to return to".
Use the available tools to navigate the system back to that state.

You will be provided with the description of the goal state for more detailed information to assist in your recovery process.

You will also be provided with information regarding the transition from the initial state to the goal state. Use such information to gain knowledge of the goal state.

### Current Status

  - Current step: Error Step {error\_step}

  - Target: Return to Goal State (Step {goal\_step})

### Your Task

Analyze the difference between the current state and the Goal State, then take the necessary actions step by step to reach the Goal State.

Figure 32: Recovery Instruction for recovery agent (0-R)

State-verification prompt for ReTrace

You are an expert UI-state verifier. Your job is to decide whether two screenshots show the SAME semantic/functional state for continuing an agent trajectory.

I will show you two screenshots:

1. EXPECTED STATE (ground truth): This is the reference screenshot showing the expected state from the original trajectory.

2. CURRENT STATE: This is the actual screenshot from the current VM after action replay.

Your task is to determine if these two screenshots represent the SAME semantic state.

Definition of "SAME semantic state":

   - An agent could continue the task from CURRENT STATE exactly as they would from EXPECTED STATE, without extra recovery steps.

   - The same page/view is open (same site/app and same logical screen).

   - The same critical UI state is present (same modal/popup/overlay presence, same selected tab/filter/sort, same form values/selection states, same login/account state).

   - Minor cosmetic differences are allowed.

Important considerations:

   - Ignore minor differences like exact timestamps, cursor positions, simple popups, information banners or minor visual variations.

   - Focus on the FUNCTIONAL state: Are the same windows/applications open? Are the same elements visible? Is the same content displayed?

   - Consider the overall layout and which UI components are active.

Respond in the following JSON format:

{

    "are\_same": true/false,

    "confidence": 0.0-1.0,

    "explanation": "Detailed explanation of what is the same or different between the two states"

}

Be precise about what differs if the states are not the same. Return ONLY valid JSON. No markdown. No extra keys.

Figure 33: State-verification prompt for ReTrace

State transition summarizer system prompt for Recovery Target Contextualization

<GOAL\_CONTEXTUALIZER\_ROLE>

You are a Goal State Contextualizer. Your role is to analyze the history of screenshots and contextual information
leading up to a Goal State, and produce a rich, detailed description of what the Goal State looks like and how it was reached, so that the
Recovery Agent is able to fully restore the provided goal state.

  
Your task is to describe the \*\*Goal State itself\*\* in sufficient detail so that it fully explains the state in detail.

For the provided trajectory leading to the Goal State, you must:

1. \*\*Describe the Goal State\*\*: Provide a comprehensive visual description of the Goal State screenshot — what windows are open,

what content is displayed, what UI elements are visible, what values or data are shown.

2. \*\*Contextual Background\*\*: Summarize the key steps and transitions that led to this Goal State, so that the context behind the current configuration of goal state is clear to the Recovery Agent.

3. \*\*Critical State Elements\*\*: Highlight the most important visual and functional elements that define this Goal State — these are the elements that MUST be present for the state to be considered successfully restored.

</GOAL\_CONTEXTUALIZER\_ROLE>

<OUTPUT\_GUIDELINES>

\* Be precise and detailed — the Recovery Agent will rely on your description to understand the target state.

\* Focus on observable, verifiable elements (window positions, content values, UI states, active tabs, location of the cursors, etc.).

\* Distinguish between essential state elements (must be restored) and incidental ones (may vary).
\* Structure your response clearly with labeled sections.

\* Do NOT describe actions or commands — focus on the resulting state.

</OUTPUT\_GUIDELINES>

Figure 34: State transition summarizer system prompt for Recovery Target Contextualization

State transition summarizer Instruction for Recovery Target Contextualization

## GOAL STATE CONTEXTUALIZATION TASK

You are provided with:

1. \*\*Goal State History\*\*: A sequence of screenshots and contextual information showing the trajectory of actions and state changes that led to the Goal State.

2. \*\*Goal State Screenshot\*\*: The screenshot of the Goal State — this is the target state that a Recovery Agent needs to restore.

  
### Your Task

Analyze the history and the Goal State screenshot to produce a detailed, contextualized description of the Goal State. Focus on:

  
- \*\*Visual Description\*\*: What exactly is shown on screen — open windows, active applications, displayed content, UI element states (buttons, menus, checkboxes, selections), file contents, browser tabs, etc.

- \*\*Data and Values\*\*: Specific values, text, numbers, file names, cell contents, or any data visible in the Goal State that must be accurately restored.

- \*\*Spatial Layout\*\*: The arrangement and positioning of windows, panels, and UI elements on the screen.

- \*\*Contextual History\*\*: A brief summary of the key transitions that led to this state, providing context for why the state looks the way it does.

### Output Format

Provide a structured description with:

1. \*\*Goal State Overview\*\*: A concise summary of the Goal State (1-2 sentences).

2. \*\*Detailed Visual Description\*\*: Comprehensive description of all visible elements and their states.

3. \*\*Critical Elements for Recovery\*\*: A prioritized list of the most important elements that must be present for successful recovery to this state.

4. \*\*Context Summary\*\*: Brief description of how this state was reached (what key steps led here).

Figure 35: State transition summarizer Instruction for Recovery Target Contextualization

System prompt used for the Error Detector

You are an expert Error Detector for GUI automation agents. Your task is to analyze a step-by-step trajectory of a GUI agent performing a task and determine whether any action is erroneous.

  
# Step Indexing Convention

  
- Step indices are 0-based.

- If the trajectory is observation 0, action 0, observation 1, action 1, observation 2, and error is observed in ’observation 2’, then error step is 2.

- Minimum error step is 1 because the first observation is always the initial state before any action is taken.

  
# Input Format

  
You will receive:

1. A goal instruction describing what the agent should accomplish.

2. A sequence of (Observation, Action) pairs showing what the agent saw before each action and what it decided to do.

3. A current observation after the most recent executed step. This is the current screen after the latest action and is provided as additional evidence, not as an extra step.

  
# Your Task

  
After reviewing the trajectory up to the current step, determine:

- Whether any action in the trajectory is an error (i.e., an action that moves the agent away from completing the goal, is incorrect, or is counterproductive).

- If an error is detected, identify which step contain the error.

  
# Retrospective Detection

  
You may recognize that an earlier step was erroneous based on later observations. For example, if Step 3’s action seemed reasonable at the time but Step 6 reveals it led to a wrong state, you should flag Step 3 as the error.

  
# Output Format

  
You MUST respond with a valid JSON object and nothing else. Do not include any text before or after the JSON.

  
If NO error is detected:

{"is\_error": false, "error\_step": null, "reasoning": ""}

  
If an error IS detected:

{"is\_error": true, "error\_step": <integer>, "reasoning": "Detailed explanation of what went wrong and why this step is erroneous."}

  
Where error\_step is a 0-based observation/state step index where the error becomes visible.

  
# Important Guidelines

  
- Be conservative: only flag clear errors, not merely suboptimal actions. You got only one chance to detect errors, so you should be careful.

- Consider the full context of the goal when evaluating actions.

- An action that seems wrong in isolation might be correct in context (e.g., scrolling to find an element).

- Focus on actions that clearly prevent task completion or cause damage.

- Always provide clear reasoning for your judgment.

Figure 36: System prompt used for the Error Detector

System prompt used for the Recovery Step Detector

You are an expert Recovery Step Detector for GUI agents. Your task is to analyze a step-by-step trajectory of a GUI agent performing a task, where an error has occurred at the final step shown in the trajectory, and determine the optimal step to rewind to (the recovery step).

  
# Step Indexing Convention

  
- Step indices are 0-based.

- If the trajectory is observation 0, action 0, observation 1, action 1, observation 2, and error step is 2, then the recovery step can be 0 or 1 depending on where the critical mistake occurred that led to the error observed in observation 2.

- A recovery step $k$ means: return to the observation ’observation\_k’ which is the observation before action ’action\_k’

- Therefore, recovery\_step = 0 means returning to the observation 0 which is the initial observation before the first action.

  
# Input Format

  
You will receive:

1. A goal instruction describing what the agent should accomplish.

2. A sequence of (Observation, Action) pairs showing what the agent saw before each action and what it decided to do.

3. A latest observation at the Error Step showing the current screen after the most recent executed action. This latest observation is not an extra step; it is where the error becomes visible.

  
# Your Task

  
After reviewing the trajectory up to and including the Error Step, determine:

- The single best recovery step ( $k$ ): Which observation/state step index ( $0\leq k<\text{error\_step}$ ) should the agent recover to in order to correct the mistake and successfully complete the task?

  
The recovery step is the observation point right before the agent made the critical mistake that led to the error. By rewinding to Step $k$ , the agent returns to the observation before action action\_k and can choose a different action for that same step.

Let the error step be N. The recovery step can be ’N-1’, ’N-2’, etc., depending on where the critical mistake occurred.

The recovery step should be the earliest point in the trajectory where the agent’s action diverted from the optimal path to the goal.

  
# Output Format

  
You MUST respond with a valid JSON object and NOTHING else. Do not include any text, preamble, or conversational filler before or after the JSON.

  
Your entire response must be parseable by json.loads().

  
You must output exactly this format:

{"recovery\_step": <integer>, "reasoning": "Detailed explanation of why this specific step is the optimal point to resume from."}

  
Where recovery\_step is an integer 0-based observation/state step index (0-indexed) where $0\leq\text{recovery\_step}<\text{error\_step}$ .

  
# Important Guidelines

  
- The recovery step should be the earliest point in the trajectory where the agent’s action diverted from the optimal path to the goal.

- Think carefully about the causal chain: the visible error might just be a consequence of a mistake made several steps earlier.

- Always provide clear, step-by-step reasoning for your choice.

Figure 37: System prompt used for the Recovery Step Detector

Prompt used for GPT-5.4 evaluator in Table [1](#S5.T1)

You are a strict and robust verifier responsible for determining whether the given target state has been successfuly reached from an erroneous starting state.

Your job is to explicitly understand the final reached state and determine whether it is the same as the ground truth goal state.

  
You will be provided with:

1) The ground truth goal state that must be reached.

2) The error state that the restoration to the goal state must be performed.

3) Final state of the trajectory from a computer agent.
4) The trajectory of a computer-use agent from the error step towards the ground truth goal state, consisting of a sequence of states of screenshot and executed actions.

5) The trajectory of a computer-use agent from the initial state towards the error step, consisting of a sequence of states of screenshot and executed actions.

6) The original instruction that the agent has been asked to do that led to the error state and trajectory from the intial state towards the error step.

The trajectory represents the sequence of states visited during a recovery process.

Your task is to determine whether the goal state has been reached, using the final recovery state and the history of steps towards such process, along with transitions and actions taken.

The target state represents the ground-truth recovery states that the agent is expected to reach.

  
Rules:

1. Target states are provided as visual screenshots of the environment.

2. Verification should be robust to minor visual differences that do not alter the semantic meaning of the state.

3. Focus both on the semantic meaning of the state, along with the visual appearance, and whether the goal state is functionally achieved.

4. The trajectory represents the sequence of states visited during the navigation process. The first state in the trajectory is the initial state from which navigation begins.

Output format (STRICT):
Output only true or false.
true: the final state is semantically, and visually the same as the target state.
false: the final state is not semantically, and visually the same as the target state.
Do not output any explanation, reasoning, punctuation, quotation marks, or extra whitespace.

Figure 38: Prompt used for GPT-5.4 evaluator in Table [1](#S5.T1)
