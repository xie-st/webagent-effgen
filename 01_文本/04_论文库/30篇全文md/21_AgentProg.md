---
title: "AgentProg: Empowering Long-Horizon GUI Agents with Program-Guided Context Management Thanks: Corresponding Author: Yuanchun Li (liyuanchun@air.tsinghua.edu.cn)"
arxiv_html: https://arxiv.org/html/2512.10371v2
downloaded: 2026-10-29
converted: arxiv LaTeXML HTML -> Markdown（本地图片 + alttext 公式还原）
---

# AgentProg: Empowering Long-Horizon GUI Agents with Program-Guided Context ManagementThanks: Corresponding Author: Yuanchun Li (liyuanchun@air.tsinghua.edu.cn)

#1004Conference: The 24th Annual International Conference on Mobile Systems, Applications and Services; June 21–25, 2026; Cambridge, United KingdomThe 24th Annual International Conference on Mobile Systems, Applications and Services (MobiSys ’26), June 21–25, 2026, Cambridge, United KingdomDOI: [10.1145/3745756.3809245](https://doi.org/10.1145/3745756.3809245)ISBN: 979-8-4007-2027-7/26/06CCS: Human-centered computing Ubiquitous and mobile computingCCS: Computing methodologies Artificial intelligence

- **Shizuo Tian** · Tsinghua University , Beijing , China
- **Hao Wen** · Tsinghua University , Beijing , China
- **Yuxuan Chen** · Tsinghua University , Beijing , China
- **Jiacheng Liu** · Peking University , Beijing , China
- **Shanhui Zhao** · Tsinghua University , Beijing , China
- **Guohong Liu** · Tsinghua University , Beijing , China
- **Ju Ren** · Tsinghua University , Beijing , China
- **Yunxin Liu** · Tsinghua University , Beijing , China
- **Yuanchun Li** · Tsinghua University , Beijing , China

© cc

###### Abstract.

The rapid development of mobile GUI agents has stimulated growing research interest in long-horizon task automation.
However, building agents for these tasks faces a critical bottleneck: the reliance on ever-expanding interaction history incurs substantial context overhead. Existing context management and compression techniques often fail to preserve vital semantic information, leading to degraded task performance. We propose AgentProg, a program-guided approach for agent context management that reframes the interaction history as a program with variables and control flow. By organizing information according to the structure of program, this structure provides a principled mechanism to determine which information should be retained and which can be discarded. We further integrate a global belief state mechanism inspired by Belief MDP framework to handle partial observability and adapt to unexpected environmental changes. Experiments on AndroidWorld and our extended long-horizon task suite demonstrate that AgentProg has achieved state-of-the-art success rates on these benchmarks. More importantly, it maintains robust performance on long-horizon tasks while baseline methods experience catastrophic degradation. Our system is open-sourced at <https://github.com/MobileLLM/AgentProg>.

###### Keywords:

Mobile GUI Agents, Mobile Task Automation, Long-Horizon Agents, Context Management

††cc-license: by

## 1. Introduction

Building intelligent assistants that can operate mobile devices by following natural language instructions has long been a central goal of mobile systems ([Azim et al., 2016](#bib.bib4); [Li and Riva, 2018](#bib.bib19); [Wen et al., 2024](#bib.bib45)) and artificial intelligence researchers ([Sun et al., 2022](#bib.bib37); [Li et al., 2020](#bib.bib20); [Liu et al., 2018](#bib.bib22)). Graphical User Interface (GUI) agents aim to simulate human user operations on graphical interfaces (e.g., clicking, scrolling, and inputting text) to interact with devices and complete complex tasks within existing software ecosystems.
Mobile GUI environments present unique challenges compared to web or desktop settings: (1) severe partial observability due to the constrained screen size of mobile devices as only a small portion of UI elements is visible, and critical device states are usually hidden from the screen, making the observability problem more significant than on web or desktop platforms; (2) noisy accessibility trees as many mobile applications provide incomplete, misleading or even no accessibility tree support, while a complete DOM tree is often readily accessible in web environments, making symbolic program approaches that depend on structured elements unreliable; (3) fragmented UI ecosystems, where the system share panels, permission dialogs, or even interaction patterns are different across different OS versions and device manufacturers, challenging the generalization ability of agents.
Recent advances in large language models (LLMs) and vision-language models (VLMs) have shown promising results in this domain. Building upon these foundation models, researchers have developed rich agent frameworks that enable agents to successfully complete relatively simple tasks through interactive decision-making processes ([Zhang and Zhang, 2024](#bib.bib59); [Zhang et al., 2023](#bib.bib57); [Wen et al., 2025](#bib.bib46); [Xu et al., 2025](#bib.bib50); [Ye et al., 2025b](#bib.bib54); [Gonzalez-Pumariega et al., 2025](#bib.bib8); [Li et al., 2025b](#bib.bib18)).

However, despite their success on simple tasks, existing methods face significant challenges when scaling to long-horizon scenarios—tasks that require dozens or even hundreds of steps to complete. The ability to complete such long tasks is usually more desirable, as they are often cumbersome and difficult for human users. For instance, an example long task is to review all events on today’s calendar (including sending messages, creating notes, etc.) and generate follow-up steps on all scheduled items, or to navigate between multiple shopping and note apps to compare and record product prices.
These challenges manifest in two critical dimensions. First, model performance degrades significantly on extended tasks, as language models struggle to maintain coherence and task-relevant reasoning over protracted sequences ([Liu et al., 2024](#bib.bib23); [An et al., 2024](#bib.bib3)). Second, the computational cost grows substantially as the interaction history increases, with each decision requiring to process an increasingly long context.

Existing approaches attempt to address the context management problem through various techniques, such as context window ([Qin et al., 2025](#bib.bib28)), summarization ([Rawles et al., 2024](#bib.bib29); [Ye et al., 2025b](#bib.bib54)) or hierarchical planning ([Agashe et al., 2025](#bib.bib2); [Li et al., 2025a](#bib.bib17)). While these methods partially alleviate the computational burden, they face a fundamental limitation: they lack a principled framework for determining which information is essential for future steps and which can be safely discarded. This often results in the loss of crucial state information, leading to task failure ([Zhang et al., 2025](#bib.bib58); [Schroeder et al., 2025](#bib.bib30); [Zhou et al., 2025](#bib.bib61)). Moreover, existing methods demonstrate a critical gap in generalization—an agent’s ability to solve individual atomic tasks does not directly transfer to solving compositional or iterative long-horizon tasks, revealing deeper limitations in their reasoning capabilities ([Liu et al., 2025](#bib.bib24)). The core challenge in long-horizon task execution lies in effective context management during task execution. An agent must maintain a comprehensive understanding of the task progress and dynamically assess the evolving environment to make informed decisions. This requires task-aware context management to preserve the essential state while discarding irrelevant details.

Based on a pilot test of mobile GUI agents on long-horizon tasks (detailed in Section [2.3](#S2.SS3)), we observed three key difficulties that hinder more accurate and robust task execution.

1. (1)

   Task Planning and Decomposition. Long-horizon tasks often involve composition, repetition, and recursion of multiple subtasks. Existing methods typically decompose tasks into sequences or trees ([Wei et al., 2022](#bib.bib44); [Yao et al., 2023](#bib.bib53)), but these structures are overly simplistic for complex scenarios, necessitating frequent re-planning that introduces overhead and instability. For instance, tasks like “read today’s todo list and complete each item” cannot be fully planned upfront since the items are unknown initially, leading to repeated re-planning that increases error risks.
2. (2)

   Interaction History Management. Due to the limited context length of LLMs, agents must determine what information to retain or forget in the task execution process. Current approaches lack task-aware context management, struggling to preserve critical intermediate results (e.g., restaurant details across a reservation task) while discarding irrelevant navigation history.
3. (3)

   Environment State Comprehension. Agents must maintain an accurate understanding about environment states throughout execution. Software environments are usually dynamic and partially-observable with hidden UI elements, unexpected state changes, and transient failures, which are hard to handle for agents in the long task process. For instance, without proper environment understanding, agents may incorrectly believe tasks are complete when operations actually failed, causing workflow derailment that becomes critical in long-horizon scenarios.

Our inspiration to address these challenges stems from traditional programs, which are capable of executing extremely long tasks with limited memory capacity. A program is naturally a representation of task decomposition. Its “context management” strategy is the program itself, which seamlessly handles information retaining/discarding in the system heap and stack through the mechanisms of functions, threads, global/local variables, etc. In principle, the task execution process of a GUI agent can also be represented as a program, and the agent context can be maintained in the same way as the CPU memory during program execution.

Therefore, we propose AgentProg, a program-guided context management approach for long-horizon GUI agent tasks. AgentProg reframes the agent’s interaction history—traditionally represented as a flat, ever-expanding sequence — as a program with variables and control flow. This program structure, generated based on the task requirements, provides a principled and task-aware mechanism for context management. By organizing information according to the program’s structure, AgentProg can systematically determine which information to retain and which to discard at each step, enabling task-specific context management that preserves crucial details.

A key question in our agent-program analogy is how to handle environment dynamicity. Letting the agent follow a program in the task process may lead to poor adaptivity, since the programs are generated before observing the actual environment at each step. We introduce a domain-specific language named Semantic Task Program (STP) to handle this problem. Unlike traditional programs that are based on precise symbolic instructions (e.g., name = getElement(’user Name’).text), STP uses fuzzy, natural-language-style instructions (e.g., get user name as {name}) to construct the program. The STP instructions capture necessary information for interaction context management, while they are interpreted adaptively at runtime based on the actual environment state. Furthermore, we incorporate a Global Belief State module into the STP execution process to address the inherent partial observability of GUI environments, a characteristic absent in traditional programming paradigms.

We evaluate AgentProg on AndroidWorld ([Rawles et al., 2024](#bib.bib29)), a challenging and widely-used benchmark for mobile device-control agents, and introduce an extended task suite that we construct based on AndroidWorld to specifically test agent performance on long-horizon scenarios. Our experiments reveal that while existing methods perform well on the original AndroidWorld benchmark, they exhibit substantial performance degradation on our extended task suite, highlighting their fundamental limitations in handling long-horizon reasoning. In contrast, our program-guided approach demonstrates robust performance across both benchmarks. The context organization ability of AgentProg also helps it achieve the new state of the art on AndroidWorld.

Our main contributions are summarized as follows:

1. (1)

   We identify three key challenges for GUI agents on long-horizon tasks, and propose program-guided context management as a principled approach to address these challenges.
2. (2)

   We design and implement AgentProg, a mobile GUI agent based on program-guided context management. We introduce Semantic Task Program and global belief state to address the dynamicity and partial observability problems in program-driven task execution.
3. (3)

   AgentProg has been evaluated on AndroidWorld and AW-Extend and achieved the new state of the art.

## 2. Related Work and Motivation

### 2.1. GUI Agent

Graphical User Interface (GUI) agents are autonomous systems designed to interact with software applications through their visual interfaces, mimicking human user behavior to accomplish complex tasks. A GUI agent typically takes as input a natural language task instruction (e.g., “Send an email to John about the meeting”) and the current screen state, which includes visual information (screenshots) and optionally structural information (UI element hierarchies such as accessibility trees or HTML DOMs) ([Nguyen et al., 2025](#bib.bib27)). The agent outputs a sequence of actions such as clicking on specific UI elements, scrolling, typing text, or navigating between applications to accomplish the specified task within existing software ecosystems.

The decision-making process of a GUI agent can be formalized as a partially observable Markov decision process (POMDP) ([Sondik, 1978](#bib.bib33)). At each timestep $t$ , the agent observes the current screen state $o_{t}$ and selects an action $a_{t}$ based on the task goal $g$ and the interaction history $h_{<t}=\{(o_{0},a_{0}),\allowbreak(o_{1},a_{1}),\dots,(o_{t-1},a_{t-1})\}$ . The environment then transitions to a new state, providing observation $o_{t+1}$ . This process continues until the task is completed or a maximum number of steps is reached. The core challenge lies in how agents manage the ever-growing interaction history $h_{<t}$ while maintaining accurate understanding of the current environment state.

### 2.2. Related Work

GUI Agents with Foundation Models.
Recent advances in large language models and multimodal large language models have significantly enhanced their capabilities in language understanding and cognitive processing, enabling effective interpretation of human instructions, detailed planning, and complex task execution ([Xu et al., 2024a](#bib.bib49)). Early approaches combined LLMs with domain-specific knowledge to achieve smartphone automation ([Wen et al., 2024](#bib.bib45); [Zhang et al., 2023](#bib.bib57)), while subsequent methods introduced refined control mechanisms for mobile applications through visual perception and multimodal reasoning ([Yan et al., 2023](#bib.bib52); [Zhang et al., 2023](#bib.bib57); [Zhang et al., 2024](#bib.bib56)). Vision-centric approaches have been proposed that identify and locate UI elements directly from visual inputs without relying on XML metadata or system accessibility trees ([Cheng et al., 2024](#bib.bib5); [Zheng et al., 2024](#bib.bib60); [Gou et al., 2025](#bib.bib10); [Wu et al., 2024b](#bib.bib48); [Wang et al., 2024c](#bib.bib40); [Li et al., 2025a](#bib.bib17); [Li et al., 2025b](#bib.bib18); [Wang et al., 2025b](#bib.bib39)).

Context Management for GUI Agents. Managing interaction history is crucial for GUI agents to maintain task progress within token budget constraints. Existing approaches include sliding window methods that retain only the most recent $N$ observations ([Qin et al., 2025](#bib.bib28)), summarization methods that condense each step into minimal tokens ([Rawles et al., 2024](#bib.bib29); [Gao et al., 2025](#bib.bib7); [Tan et al., 2024](#bib.bib38)), and hierarchical planning methods that decompose tasks into sub-task sequences ([Li et al., 2025b](#bib.bib18); [Ye et al., 2025b](#bib.bib54); [Gonzalez-Pumariega et al., 2025](#bib.bib8); [Zhang et al., 2024](#bib.bib56); [Mozannar et al., 2025](#bib.bib26)). However, these methods face limitations: sliding window incurs increasing context, summarization lacks explicit planning for complex tasks and may lose critical
early information, and hierarchical planning introduces overhead requiring multiple re-planning rounds and also faces with the challenge of forgetting important information.

Program-Based GUI Agents.
While standard GUI agents utilize a fixed set of programmatic APIs (e.g., click, type, scroll) as their action space, they typically treat these low-level APIs merely as atomic tool invocations. Recently, a distinct paradigm shift in LLM agents has emerged from using rigid, discrete tool calls to employing executable code as the unified action space for agents ([Wang et al., 2024a](#bib.bib42); [Shen et al., 2025](#bib.bib31); [Li et al., 2025c](#bib.bib16); [Liang et al., 2023](#bib.bib21)). To bridge the gap between low-level actions and high-level code generation, recent GUI agents have empowered agents to proactively construct high-level functions, encapsulating primitive operations into meaningful skills ([Wang et al., 2025a](#bib.bib43); [Wu et al., 2024a](#bib.bib47)). Other approaches establish a persistent program context or terminal environment, enabling the agent to engage in continuous interaction through script synthesizing ([Wen et al., 2025](#bib.bib46); [Song et al., 2025a](#bib.bib34); [Gur et al., 2024](#bib.bib12)). However, current task script generation methods ([Wen et al., 2025](#bib.bib46)) typically require precise API calls and strict syntax adherence, relying heavily on extensive exploration of mobile apps to build application documentation. Consequently, these scripts are prone to failure when encountering unseen applications or when dealing with out-of-distribution scenarios where documentation is unavailable.

### 2.3. Motivation and Challenges

![](images/21_AgentProg/pre_exp.svg)


Figure 1. 
Performance Comparison on AndroidWorld vs. AW-Extend.
a11y refers to the Accessibility Tree observation space; SoM denotes Set-of-Mark; Mobile-Ag-v3 denotes Mobile-Agent-v3.

![Refer to caption](images/21_AgentProg/pre_case_study.png)


Figure 2. Failure mode in existing methods (Mobile-Agent-v3 ([Ye et al., 2025b](#bib.bib54)), UI-TARS ([Qin et al., 2025](#bib.bib28)), M3A ([Rawles et al., 2024](#bib.bib29))) on AW-Extend.

Despite the progress in GUI agents, existing methods face fundamental limitations when handling long-horizon tasks, which require dozens or hundreds of sequential steps to complete. To better understand these challenges, we construct AW-Extend, an extended task suite based on AndroidWorld ([Rawles et al., 2024](#bib.bib29)) that specifically tests agent performance on compositional and iterative tasks. Our extended suite comprises 19 tasks that are possibly common in realistic scenarios across two categories: Compositional Tasks that combine sub-tasks into a compositional task requiring critical information maintenance across applications, and Iterative Tasks that scale sub-task counts to $n=10$ or $n=20$ to test robustness and memory filtering capabilities. The detail of this task suite is illustrated in Section [4](#S4).

Our preliminary analysis reveals critical failure reasons in existing methods, as illustrated in Figure [1](#S2.F1):

Lack of Overall Planning. In the “MarkorTodoList” task, Mobile-Agent-v3 prematurely terminates after completing only the first two sub-tasks, mistakenly believing all three items from the note have been addressed, as shown in Figure [2](#S2.F2). This indicates a fundamental deficiency in holistic task planning and progress tracking.

Failure to Remember Critical Information. Despite employing context management schemes, existing agents fail to preserve task-relevant information at critical moments. In our tests, agents consistently pass incorrect parameters during sub-task execution because they do not retain all task items when initially opening the note, as shown in Figure [2](#S2.F2). Their context management mechanisms lack sensitivity to task-critical information.

Poor Understanding of Dynamic Environments. Our iterative tasks involving 10-20 sub-tasks expose fragility in handling unexpected situations—accidental app closures, dialog popups, or wrong operations. Moreover, due to the partial observability of GUI environments, changes in phone data are sometimes implicit, such as system settings, date and time, and in-app data. Existing methods struggle with such environmental variations, resulting in poor robustness during extended task execution. In our tests, the agent was tasked with deleting all events on this Saturday, but failed to correctly understand the date in the phone environment. Consequently, it deleted all Saturday events across different weeks, leading to task failure.

## 3. Our Approach: AgentProg

We present AgentProg, a program-guided framework for long-horizon task execution, as shown in Figure [3](#S3.F3). It addresses three fundamental challenges in agent-environment interaction.
First, to tackle the challenge of planning and decomposing complex long-horizon tasks, we introduce Semantic Task Program (STP), a domain-specific language that extends natural language instructions with structured control flow (loops, branches, functions) and explicit variable operations. Second, to provide agents with appropriate context without redundancy, we develop a program-guided context management approach that operates along control flow-based pruning and data flow management. Third, to maintain accurate environment understanding despite partial observability and outdated beliefs, we propose a Global Belief State mechanism that continuously validates and updates the agent’s hypotheses about environment mechanisms and hidden variables throughout execution.

Together, these components form a two-stage framework: Semantic Task Program Generation, where the agent performs global planning to create a structured program with identified critical variables, followed by Semantic Task Program Execution, where the agent incrementally interprets the program while maintaining belief state consistency and managing context efficiently. This design enables stable, efficient execution of long-horizon tasks without the context overflow and information loss problems that plague conventional approaches.

![Refer to caption](images/21_AgentProg/introduction.png)


Figure 3. The workflow of AgentProg.

### 3.1. Semantic Task Program: A DSL for Long-Horizon Task Planning

We design Semantic Task Program (STP), a domain-specific language (DSL) that represents long-horizon tasks. Unlike rigid programming languages, STP balances expressiveness with semantic tolerance. It enables agents to plan and execute complex tasks effectively. More details and examples of STP are listed in Section [A](#A1).

Design Principles. STP is built on three core principles: (1) Natural Language Foundation: Each program step is primarily expressed in natural language instructions, ensuring readability and maintaining generality across different environments; (2) Structured Control Flow: The language incorporates essential programming constructs including loops, conditionals, and functions to express iterative and recursive task patterns concisely; (3) Explicit Data Flow: Variables are used to explicitly pass information between steps, allowing the agent to identify and preserve critical information throughout task execution.

Syntax and Constructs. An STP consists of a sequence of steps, where each step can be: (1) Action Step: A natural language instruction describing what should be accomplished, such as “Open the note ‘todo\_list.md’ in the Markor application”; (2) Variable Declaration and Assignment: Explicit recording of critical information using variables enclosed in braces, e.g., “record them as {task\_list}”; (3) Control Flow Statements: Loop constructs, conditional branches, and function definitions that organize execution flow, e.g., “Iterate over {task\_list}”; (4) Variable References: Using declared variables in subsequent steps, e.g., “for each {task\_item}, …”.

Semantic Tolerance. A key distinguishing feature of STP is its semantic tolerance. Current task script generation methods ([Wen et al., 2025](#bib.bib46)) require precise API calls and strict syntax. Consequently, they are highly sensitive to environment dynamics and software updates. Semantic Task Program allows for variations in execution details. The natural language instructions provide high-level guidance without being tightly coupled to specific environment implementations. This tolerance enables the agent to adapt to different environments and handle unexpected situations during execution, while the structured control flow ensures the overall task logic remains intact.

Comparison to Symbolic DSLs. Symbolic DSLs (e.g., AutoDroid-V2) often suffer from syntax errors and require extensive app-specific knowledge ([Wen et al., 2025](#bib.bib46)). When mobile applications provide poor or even no accessibility tree support, those methods are prone to failure. This critical limitation on mobile platform motivates our natural-language-style design, where STP leverages LLM’s strong semantic priors, ensuring robust generalization via visual observations without rigid syntax constraints or limitations of accessibility tree.

### 3.2. STP Generation and Execution

AgentProg aims to enhance agent performance in long-horizon tasks through a two-stage framework for memory management as Figure [3](#S3.F3) shows: 1) Semantic Task Program Generation: The agent generates a globally planned Semantic Task Program based on task requirements, where the program extends natural language with support for control flow constructs (e.g., branching, loops) and variable operations (declaration, assignment); 2) Semantic Task Program Execution: The agent incrementally interprets and executes the Semantic Task Program, taking environment state and current program state as input, and producing actions while updating the program state.

Generation Phase. The agent plans a feasible program according to specifications. It uses control flow to orchestrate execution and identifies critical variables for preservation. The natural language components ensure the program remains general and robust.

Execution Phase. Instead of rigidly executing pre-defined scripts, AgentProg adopts a dynamic instruction grounding paradigm. The Semantic Task Program serves as a high-level guide, where AgentProg acts as a runtime interpreter that translates the current high-level program instruction into executable low-level actions based on the real-time environment state. This mechanism decouples the task logic from specific execution details, preventing context overflow while maintaining flexibility.

Specifically, AgentProg operates in two alternating modes:

1) Action Generation.
In this mode, the agent focuses on instantiating the high-level intent of the current program step into concrete execution logic.
Based on the instruction pointed to by the Program Counter (PC) and the current GUI observation, the agent generates a snippet of low-level Python code to interact with the environment.
AgentProg utilizes LLM to ground abstract natural language instructions into a sequence of atomic Python APIs (e.g., start\_app(<app>), click(<element>), swipe\_down(),
input

(<text>)).
Crucially, this allows the agent to dynamically adapt the low-level operations (e.g., handling pop-ups or layout changes) while adhering to the high-level plan. The agent records these executed Python scripts to track data flow, while repetitive execution histories (e.g., inside loops) are folded to save context.

2) Program Counter Update. After the generated Python code is executed and the environment updates, the agent switches to this mode to manage the control flow.
It decides how to move the Program Counter—whether to advance to the next step, iterate a loop, or jump to a branch—based on the execution result of the previous step. The Program Counter is dynamically determined by the LLM rather than following a deterministic transition, enabling the agent to skip, repeat or branch based on runtime observations.

These two modes alternate strictly: AgentProg translates the current instruction into Python code (Action Generation), executes it, and then decides where to go next in the program (PC Update). Throughout this process, AgentProg maintains a structured context containing the static program plan and the dynamic variables and low-level history, ensuring all decisions are globally consistent yet locally adaptive.

### 3.3. Program-Guided Context Management

During the Semantic Task Program Execution phase, AgentProg adopts a program-guided approach to manage the context input for the agent. This mechanism addresses the trade-off between information retention and context length. By leveraging the explicit structure of the STP, AgentProg acts as a filter: it retains execution-critical information while systematically discarding redundant history. This management operates along two dimensions: control flow pruning and data flow persistence.

![Refer to caption](images/21_AgentProg/execution_tree.png)


Figure 4. Program-guided context management with context pruning, history retrieval and variable management.

#### 3.3.1. Execution Tree-Guided Context Pruning.

To manage the control flow context, we organize the STP execution history into a dynamic tree structure. As illustrated in Figure [4](#S3.F4), each executed step expands a corresponding node in this tree.

Tree Construction Rules.
The node expansion logic is strictly bound to the program structure. We categorize nodes into three types:

- •

  Sequential Nodes: If a step follows a linear sequence, it becomes a direct child of the previously executed node.
- •

  Conditional Nodes: For branching statements (e.g., if-else), only the node corresponding to the actually executed branch becomes a child of the condition node. Unexecuted branches are never added.
- •

  Loop Nodes: For loop structures, each iteration expands a new loop statement node. These are added as children of the loop entry point, preserving the iteration history hierarchically.

Path-Based Pruning.
During inference, the agent does not see the entire raw history. Instead, we compute the active path from the root node to the currently executing node. Only the step information and observations along this active path are retained in the context; all other branches and completed loop iterations that are no longer relevant to the current state are discarded.

This approach significantly reduces context overhead, especially in tasks involving complex logic. It prevents the agent from being confused by redundant information (e.g., stale states from a previous loop iteration or irrelevant actions from a non-taken branch), allowing it to focus solely on the current logical path.

#### 3.3.2. Program-based Historical Step Retrieval

While pruning removes irrelevant context, AgentProg also employs a retrieval mechanism to enhance stability for iterative tasks.
When the execution revisits a specific program step—a common scenario in loops or recursive segments—AgentProg activates a retrieval mechanism. Unlike generic similarity search, this mechanism uses the unique program step ID to precisely identify preceding executions of the exact same step.
The operational outcomes of these past iterations—including actions taken and resulting state changes—are selectively injected into the current context as references. This allows the agent to “remember” its own recent success or failure patterns. By providing this structured historical awareness, AgentProg significantly improves consistency in long-horizon repetitive tasks, mitigating the risks of oscillation or repeated errors that often plague agents lacking step-specific memory.

#### 3.3.3. Data Flow and Variable Management

Beyond control flow, AgentProg ensures the persistence of critical information through explicit variable management. This addresses the challenge where purely context-based agents often lose track of key data (e.g., a phone number retrieved 50 steps ago).
During the Semantic Task Program Generation phase, the agent explicitly identifies and declares essential variables. These variables—such as extracted todo items, reservation times, or user preferences—act as “anchors”. They are mandated to persist throughout the execution, ensuring that task-critical data is never inadvertently discarded by the pruning mechanism.

During the Execution phase, the agent retains the flexibility to define auxiliary variables via Python code. This programmatic manipulation compensates for the limitations of raw LLM reasoning. For instance, an agent can extract multiple items into a list variable, iterate through them systematically, and use counters to track progress.
This combination of declarative planning and imperative execution ensures robust information flow: critical data remains accessible, while the internal state adapts dynamically to evolving task requirements.

#### 3.3.4. Advantages of Program-Guided Context Management.

AgentProg binds context directly to the program’s execution structure, effectively addressing these limitations.
From a control flow perspective, the STP captures repetition and branching patterns upfront. This allows the agent to systematically prune irrelevant branches and loop iterations without the need for error-prone re-planning cycles.
From a data flow perspective, explicit variable declaration serves as an information anchor, ensuring that critical data (e.g., user preferences or extracted items) persists throughout execution regardless of context length.
This dual mechanism enables AgentProg to maintain a compact, noise-free context while guaranteeing the persistence of task-critical information.

### 3.4. Global Belief State

![](images/21_AgentProg/global_belief_state.svg)


Figure 5. Dynamic global belief state management in partially observable environments.

While the Action Generation phase produces executable Python scripts, ensuring their faithful execution requires active monitoring. The Global Belief State integrates directly into this low-level execution loop, acting as a runtime verifier that checks if the assumptions made during code generation remain valid as each atomic command executes.
This validation is critical because mobile GUI environments are inherently partially observable. Critical system states—such as clipboard content, navigation back-stack, or off-screen selected items, etc.—are often invisible in the current screenshot but decisive for future actions.

Inspired by the Belief MDP framework ([Kaelbling et al., 1998](#bib.bib14)), we introduce a Global Belief State mechanism to bridge this gap.
It operates as a runtime monitor through a continuous Predict-Verify-Align cycle:
1) Maintain Hypothesis (Predict):
Unlike passive memory, the agent maintains an active set of hypotheses about the current environment status, including the UI context and data validity.
2) Runtime Verification (Verify):
During the execution of low-level Python codes, AgentProg continuously compares the real-time visual observation against its belief state.
3) Anomaly Correction (Align):
If the observation contradicts the belief, AgentProg identifies a Belief-Reality Gap. It immediately marks the previous state as invalid (e.g., “Context Lost”), and switches from execution mode to a recovery routine (e.g., navigating back to the target app) to realign its belief with reality.

Case Study.
Consider a scenario where an agent is filling out a contact form.
Initial Belief: “Editing contact ‘John Doe’; Name and Email fields are filled.”
Event: Due to an accidental touch or crash, the app exits to the home screen.
Without Belief State: A traditional agent might hallucinate that the step succeeded and attempt to click a "Save" button that no longer exists, leading to a cascade of errors.
With Belief State: AgentProg detects the conflict: the visual observation (Home Screen) refutes the belief hypothesis (Editing View). It immediately invalidates the "Name/Email filled" status, updates the belief to "Form Context Lost," and generates a corrective plan to restart the app and re-fill the information. This mechanism ensures that the agent never proceeds on false premises.

## 4. AW-Extend Benchmark

To systematically evaluate agent performance on the long-horizon challenges identified above, we constructed AW-Extend, an extended task suite that builds upon the original AndroidWorld benchmark. By adapting the existing AndroidWorld evaluation and verification system, we ensure our extended tasks maintain the same rigorous automated assessment standards while specifically targeting long-horizon scenarios.

Existing mobile GUI benchmarks ([Rawles et al., 2024](#bib.bib29); [Xu et al., 2024b](#bib.bib51); [Wang et al., 2024b](#bib.bib41)) primarily focus on evaluating isolated functionalities within individual applications, lacking coverage of realistic complex scenarios that involve coordinating multiple applications, integrating diverse functionalities across apps, or executing extended sequences of operations within a single application. Recently, several long-horizon benchmarks have emerged across different platforms, including ColorBench ([Song et al., 2025b](#bib.bib35)) for mobile, VeriWeb ([Liu et al., 2026](#bib.bib25)) and RealWebAssist ([Ye et al., 2025a](#bib.bib55)) for web. However, these long-horizon benchmarks are either offline benchmarks, which scale easily but cannot capture real execution dynamics (e.g., unexpected dialogs, environment state changes) and introduce offline-to-online gap, or target non-mobile platforms where partial observability and accessibility limitations are less severe.

AW-Extend is an online and long-horizon benchmark for mobile agent evaluation. It runs on live Android emulators with handcrafted environment setup and automated state-based evaluation scripts to ensure realistic environment dynamics. AW-Extend tasks require over 30 steps on average, compared to 13.0 for ColorBench and 17.6 for RealWebAssist, making them substantially more challenging for context management. AW-Extend utilizes realistic task composition and batching (e.g.,"add multiple contacts and message each one"), consistent with methodologies in ColorBench ([Song et al., 2025b](#bib.bib35)) and VeriWeb ([Liu et al., 2026](#bib.bib25)). Our extended suite comprises 19 tasks covering two categories:

Compositional Tasks combine multiple atomic operations into realistic workflows that require maintaining task context across different applications. These tasks are characterized by strong dependencies between subtasks, demanding that agents retain and effectively utilize critical information throughout the execution process. Representative examples include: processing a To-Do List from notes by completing each item sequentially (creating calendar events, adding contacts, managing expenses); batch operations such as creating multiple contacts and messaging each one; and cross-application interactions like querying note content via text message and replying accordingly.

Iterative Tasks systematically scale the sub-task count from the standard $n=3$ in AndroidWorld to $n=10$ and $n=20$ , testing both agent robustness and the ability to filter irrelevant information from context. Unlike compositional tasks where subtasks are interdependent, iterative tasks involve weakly-correlated operations, making them particularly effective for evaluating an agent’s capacity to suppress interference from irrelevant historical context while maintaining consistent task execution. These tasks encompass managing expense records, calendar events, menu items, and note operations.

We adapted AndroidWorld’s environment configuration and evaluation code to create these tasks, enabling assessment through AndroidWorld’s standard interface, including environment setup, automated evaluation based on emulator state, and trajectory recording.

## 5. Experiments

### 5.1. Experimental Settings

Benchmarks. We conduct experiments on AndroidWorld ([Rawles et al., 2024](#bib.bib29)) and AW-Extend. AndroidWorld is a comprehensive and widely used benchmark for evaluating Android GUI agents across diverse real-world mobile applications with 116 tasks.
AW-Extend is an extension we construct with 19 additional long horizon tasks described in Section [4](#S4).

Baselines. We compare our method with several state-of-the-art approaches on two benchmarks. On AndroidWorld benchmark, as shown in Table [1](#S5.T1), we include a wide range of methods from related work. We re-evaluated M3A method ([Rawles et al., 2024](#bib.bib29)), for both its a11y tree and SoM variants, using Gemini-2.5-Pro, as the original work reported results based on GPT-4-Turbo. All other baseline scores on AndroidWorld are cited from their respective original publications. On AW-Extend benchmark, we select a focused set of baselines, each employing a distinct context management strategy to handle long-horizon tasks. As detailed in Table [2](#S5.T2), these include:

- •

  M3A ([Rawles et al., 2024](#bib.bib29)), which generates a textual summary after each step to manage its context.
- •

  UI-TARS ([Qin et al., 2025](#bib.bib28)), which uses a sliding window approach, discarding the oldest screenshots in a first-in-first-out (FIFO) manner when the context exceeds a limit. We follow its official setting, retaining a maximum of five screenshots.
- •

  Mobile-Agent-v3 ([Ye et al., 2025b](#bib.bib54)), which employs hierarchical planning method. A planner first decomposes the main task into a list of sub-tasks, and an executor then completes them sequentially. The planner maintains the list of sub-tasks continuously during the task execution.

For baselines on AW-Extend benchmark, we use Gemini-2.5-Pro ([Google, 2025](#bib.bib9)) as the backbone model for M3A ([Rawles et al., 2024](#bib.bib29)), UI-TARS-1.5-API for UI-TARS ([Qin et al., 2025](#bib.bib28)), and both GUI-Owl-32B and GUI-Owl-7B for Mobile-Agent-v3 ([Ye et al., 2025b](#bib.bib54)). We note that Mobile-Agent-v3 is designed around a specialized model (GUI-Owl) with built-in grounding capabilities, making it incompatible with direct backbone substitution to general-purpose LLMs. We evaluate it using its reported best settings to serve as a representative baseline for hierarchical planning methods.

Metrics. We adapt the official AndroidWorld evaluation metric (Success Rate) to measure task completion performance. For AW-Extend, we adapt AndroidWorld’s evaluation codebase to support assessment of our custom task set.

Implementation Details. We implement AgentProg using Gemini-2.5-Pro ([Google, 2025](#bib.bib9)) as the backbone planning model, and leverage UI-TARS-1.5-API ([Qin et al., 2025](#bib.bib28)) to locate the UI elements.

### 5.2. Analysis of Success Rate

Table 1. Success Rate (%) on AndroidWorld.

| Method | AndroidWorld (%) |
| --- | --- |
| MobileGPT ( Lee et al., 2024 ) | 23.0 |
| AutoDroid-V2 ( Wen et al., 2025 ) | 26.0 |
| M3A (a11y, GPT-4-Turbo) ( Rawles et al., 2024 ) | 30.6 |
| M3A (a11y, Gemini-2.5-Pro) ( Rawles et al., 2024 ) | 31.0 |
| M3A (SoM, GPT-4-Turbo) ( Rawles et al., 2024 ) | 25.4 |
| M3A (SoM, Gemini-2.5-Pro) ( Rawles et al., 2024 ) | 39.7 |
| GLM-4.1V-9B-Thinking ( Hong et al., 2025 ) | 41.7 |
| UI-TARS (UI-TARS-7B) ( Qin et al., 2025 ) | 33.0 |
| UI-TARS (UI-TARS-1.5-API) ( Qin et al., 2025 ) | 64.2 |
| V-Droid ( Dai et al., 2025 ) | 59.5 |
| MobileUse ( Li et al., 2025b ) | 62.9 |
| UI-Venus ( Gu et al., 2025 ) | 65.9 |
| Agent S3 ( Gonzalez-Pumariega et al., 2025 ) | 68.1 |
| Mobile-Agent-v3 (GUI-Owl-7B) ( Ye et al., 2025b ) | 66.4 |
| Mobile-Agent-v3 (GUI-Owl-32B) ( Ye et al., 2025b ) | 73.3 |
| AgentProg | 78.0 |


Table 2. Success Rate (%) on AW-Extend.

| Method | AW-Extend (%) |
| --- | --- |
| M3A (a11y) | 23.7 |
| M3A (SoM) | 28.9 |
| Mobile-Agent-v3 (GUI-Owl-7B) | 26.3 |
| Mobile-Agent-v3 (GUI-Owl-32B) | 28.9 |
| UI-TARS (UI-TARS-1.5-API) | 36.8 |
| AgentProg | 68.4 |

Overall Results.  As shown in Table [1](#S5.T1), our method achieves a success rate of 78.0% on the AndroidWorld benchmark, surpassing the previous state-of-the-art Mobile-Agent-v3 by 4.7%. This demonstrates significant advantages in general mobile automation tasks. On AW-Extend benchmark shown in Table [2](#S5.T2), we compare our program-guided context management approach against three representative baseline context management strategies: Summarization (M3A), sliding window (UI-TARS), and hierarchical planning (Mobile-Agent-v3). Our method achieves a success rate of 68.4%, substantially outperforming all baseline approaches. These results demonstrate that our program-guided context management framework offers substantial advantages over existing methods, particularly for long-horizon tasks that require maintaining context effectively over extended interaction sequences.

![](images/21_AgentProg/level_acc.svg)


Figure 6. Success Rate (%) across difficulty levels on AndroidWorld.

Performance Across Task Difficulty Levels. Figure [6](#S5.F6) presents the success rates of different methods stratified by task difficulty levels on AndroidWorld. In Figure [6](#S5.F6), M3A uses SoM as input and Gemini-2.5-Pro as backbone model. MobileUse results are reported from the original paper, while M3A and AgentProg results are from our evaluation. Other existing methods have not reported performance across different difficulty levels on AndroidWorld. We observe that success rates decline progressively as task difficulty increases across all methods. Notably, AgentProg consistently outperforms baselines at every difficulty level. Besides, the magnitude of improvement is most pronounced for medium tasks (25.0% over MobileUse), followed by hard tasks (13.1% improvement), with the smallest gain on easy tasks (9.8% improvement). This pattern suggests that existing methods can handle simple tasks reasonably well, but face substantial challenges with medium and hard tasks. AgentProg effectively addresses this gap, particularly excelling where current methods struggle most. This demonstrates that the program-driven framework with belief state tracking in AgentProg is particularly effective for complex tasks that demand advanced planning capabilities, robust memory of critical information, and sophisticated environment understanding. The widening performance gap at higher difficulty levels validates that these capabilities become increasingly critical as task complexity grows.

![](images/21_AgentProg/type_acc.svg)


Figure 7. Success Rate (%) across difficulty task types on AW-Extend.

Performance Across Different Task Types. AW-Extend benchmark comprises two distinct task categories: iterative tasks and compositional tasks. We analyze the performance of different methods across these categories, as illustrated in Figure [7](#S5.F7). Compositional tasks combine multiple related subtasks, requiring agents to retain information from one subtask while executing another, thereby testing their ability to preserve critical memory. In contrast, iterative tasks involve executing similar operations multiple times with weak inter-task dependencies, primarily challenging the capability of agents to filter out irrelevant memory interference while maintaining robust task completion. Among only baseline methods, UI-TARS achieves the best overall performance, primarily due to its strong results on compositional tasks. This advantage stems from its sliding window approach, which avoids summarizing historical information, allowing the model to access information from previous subtasks when executing the current one. However, both UI-TARS and Mobile-Agent-v3 underperform M3A on iterative tasks. For UI-TARS, this may be attributed to the sliding window accumulating substantial irrelevant memory in the context, which interferes with model performance. The more complex architecture of Mobile-Agent-v3 compared to M3A introduces greater instability in context management during task execution, reducing robustness for iterative operations. M3A outperforms other baselines on iterative tasks, likely because its summary-based context management offers a simpler, more stable architecture that maintains lower failure rates when executing similar operations repeatedly. AgentProg surpasses all baseline methods, demonstrating significant advantages on both iterative and compositional tasks. The program-guided context management approach enables robust completion of both task types: it effectively preserves important information through program variables while eliminating redundant and irrelevant memory by parsing program structure. This dual capability allows AgentProg to excel where existing methods face trade-offs between memory retention and interference reduction.

Impact of Global Belief State. We further investigate the contribution of the global belief state component by comparing AgentProg with a variant that removes this module. The results reveal substantial performance improvements achieved by incorporating belief state tracking: the success rate improves from 53.9% to 78.0% on AndroidWorld (increased by 24.1%), and from 35.1% to 68.4% on AW-Extend (increased by 33.3%). These significant gains underscore the critical role of global belief state in long-horizon tasks. The global belief state mechanism enhances the agent’s understanding of environmental states, enabling it to detect and recover from unexpected situations immediately. This capability is particularly valuable for maintaining execution stability, which becomes increasingly crucial as task horizons extend. The more pronounced performance improvement on AW-Extend further validates that belief state tracking becomes even more essential for complex, multi-step tasks. By maintaining a structured representation of the current environment state, the global belief state allows AgentProg to make more informed decisions, reduce cascading errors, and ultimately achieve more robust task completion across diverse scenarios.

Impact of Execution Tree. Removing Execution Tree causes severe degradation on AW-Extend, dropping from 68.4% to 39.5%. On AndroidWorld, performance also decreases substantially from 78.0% to 61.6%. Without the Execution Tree, the agent retains all historical steps in a flat sequence, causing irrelevant context from completed loop iterations and non-taken branches to accumulate rapidly. This is particularly disadvantageous for iterative tasks in AW-Extend, where dozens of similar subtask histories overwhelm the agent’s context and interfere with decision-making. The result confirms that control flow-based context pruning is indispensable for long-horizon tasks.

Impact of Explicit Variables. Removing Explicit Variables leads to a performance drop from 78.0% to 64.2% on AndroidWorld and from 68.4% to 50.0% on AW-Extend. Without declared variables, the agent loses its “anchors” for preserving task-critical data (e.g., a list of to-do items or extracted contact information) across STP execution phase. The impact is smaller than removing the Execution Tree because the low-level Python code generation still allows the LLM some autonomy to define and track variables implicitly.

STP Error Analysis. To assess the robustness of Semantic Task Program generation, we analyze STP errors across all tasks in AndroidWorld. We define an STP error as a case where the generated program contains incorrect task decomposition, missing steps, or invalid assumptions about app workflows that cannot be recovered during execution. Out of all generated STPs, only 2.5% contain such errors, indicating that the STP generation process is highly reliable. We attribute this robustness to STP specifies core business logic (e.g., CRUD actions) without over-decomposing tasks into low-level operations, delegating the handling of unseen states and implicit prerequisites to the execution phase. Moreover, our architecture is compatible with existing re-planning strategies ([Shinn et al., 2023](#bib.bib32); [Sun et al., 2023](#bib.bib36)): Global Belief State mechanism can detect misalignment between STP assumptions and the dynamic environment at runtime, so it is possible for AgentProg to identify the failure cause and provide feedback for adaptive STP correction. Integration with re-planning modules remains a promising direction for future investigation.

A Runtime Recovery Example of Global Belief State. Global Belief State helps detect and mitigate situations where the high-level STP makes incorrect assumptions about unseen app states. We illustrate this with the BrowserMaze task from AndroidWorld, where the agent must open a maze HTML file in Chrome and navigate to the bottom-right goal. The generated STP assumes an obstacle-free grid and plans a straightforward strategy: “repeatedly click *down* until no further movement, then repeatedly click *right*.” However, the maze contains obstacles that block this linear path. During execution, GBS tracks the agent’s position and detects a Belief-Reality Gap: the expected position after a *right* click does not change, indicating a blocked cell. Rather than continuing the failing strategy, GBS updates its belief to reflect the obstacle and triggers an adaptive rerouting: the agent alternates between *down* and *right* clicks and successfully reaches the bottom-right goal. This case demonstrates how GBS enables robust execution by detecting misalignment between STP assumptions and the actual environment at runtime. Further details and visualizations are provided in Appendix [B](#A2).

### 5.3. Analysis of Latency and Cost

Table 3. Per-Task Token Consumption and Latency for Successful Attempts on AW-Extend. “Static Prefix” represents the static prefix prompt tokens that remain constant across invocations, “Dynamic” represents the prompt tokens that continuously change during task execution, and “Output” represents the total number of tokens generated during task execution.

| Agent | Task Set | Static Prefix (k) | Dynamic (k) | Output (k) | Latency (s) |
| --- | --- | --- | --- | --- | --- |
| UI-TARS | Overall | 8.1 | 315.5 | 3.2 | 312 |
| Iterative | 8.5 | 329.6 | 3.3 | 344 |  |
| Compositional | 7.6 | 294.3 | 3.0 | 263 |  |
| Mobile-Agent-v3 | Overall | 7.9 | 809.4 | 22.1 | 1604 |
| Iterative | 8.9 | 917.6 | 26.1 | 2033 |  |
| Compositional | 5.8 | 592.9 | 14.2 | 746 |  |
| AgentProg | Overall | 1026.4 | 301.3 | 179.7 | 2662 |
| Iterative | 1275.3 | 370.3 | 225.1 | 2910 |  |
| Compositional | 777.4 | 232.4 | 134.3 | 2164 |  |

Token Consumption and Latency. As shown in Table [3](#S5.T3), we compare the token consumption and latency per task across AgentProg and two baseline methods: Mobile-Agent-v3 and UI-TARS, which outperform other baselines in AndroidWorld and AW-Extend respectively. First, we analyze token consumption by distinguishing between static prefix and dynamic prompt tokens since AgentProg is based on prompt engineering with substantial system prompts, a large portion of the prefix can be cached to reduce cost and improve efficiency. This distinction provides meaningful insights into the true efficiency of different approaches. Second, we compare only tasks where all three methods succeeded, as failed tasks exhibit inconsistent token patterns—some fail due to premature termination, leading to low token counts, while others fail after excessive iterative trial-and-error operations, leading to high token counts. Including failed tasks would obscure the true efficiency characteristics of each method.

Table [3](#S5.T3) shows that UI-TARS demonstrates the lowest latency and minimal token consumption because its backbone model trained on extensive data with short static prompts and performs no additional context processing (e.g., summarization), resulting in minimal output tokens and the fastest execution speed. In contrast, Mobile-Agent-v3, while also using a trained model with relatively short static prefix (53 tokens per call), requires more tokens than UI-TARS due to its summarization and reflection process. Since AgentProg is implemented through prompt engineering, it contains a substantial static prompt prefix (12.5k tokens per call), resulting in a much higher proportion of cached tokens in the input, which reduces the cost of input tokens. Notably, AgentProg achieves significantly lower dynamic token counts compared to Mobile-Agent-v3, with performance comparable to UI-TARS. This demonstrates the effectiveness of AgentProg’s context management approach over hierarchical planning method in maintaining compact context. However, AgentProg generates significantly more output tokens compared to both baselines, as it produces extensive intermediate content for context management including belief state, and many operations involve program counter update and variable manipulations. In terms of latency, AgentProg exhibits longer execution time than Mobile-Agent-v3, primarily attributable to the increased output token generation. All three methods exhibit consistent trends across task categories: iterative tasks involve numerous repeated subtasks and thus require higher token consumption, while compositional tasks contain fewer combined subtasks and consequently demand fewer tokens.

![](images/21_AgentProg/fig_memory_dynamic_remove_prefix.svg)


Figure 8. Dynamic context tokens in 50 steps.

Context Tokens Over Steps. As shown in Figure [8](#S5.F8), we analyze the dynamic context growth patterns of different methods over extended task execution in 50 steps. We compute the average dynamic tokens at each step across all agent trajectories on the AW-Extend benchmark. UI-TARS performs minimal processing of historical information, only discarding excess screenshots when necessary. Consequently, a notable drawback of this approach is the continuous growth of context length over time. UI-TARS exhibits rapid dynamic context growth in the first 5 steps, primarily because each step adds a new screenshot to the context. From step 6 onwards, the growth rate slows as UI-TARS begins discarding the oldest screenshot while adding a new one, with context expansion mainly driven by the textual portion of historical information.

Mobile-Agent-v3 also achieves relatively slow dynamic token growth thanks to its hierarchical planning mechanism, which decomposes complex tasks into subtasks and progressively removes information during execution. However, Mobile-Agent-v3 maintains dynamic tokens at a consistently high level (approximately 17k tokens) throughout task execution. In contrast, AgentProg consistently maintains dynamic tokens at a lower level (approximately 9k tokens), demonstrating advantages over both baselines. During 50 steps, the dynamic context token count in AgentProg remains nearly constant, indicating the effectiveness of our program-guided management in maintaining a compact representation of context. This stability is achieved through our approach’s ability to represent critical information in program variables and global belief state, while systematically pruning redundant and irrelevant historical details by parsing program structure. AgentProg scales efficiently to long-horizon tasks, ensuring consistent performance even as task complexity and duration increase, while requiring much fewer dynamic tokens than existing methods.

Table 4. Per-task average steps on AW-Extend.

| Task Set | AgentProg | Mobile-Agent-v3 | UI-TARS |
| --- | --- | --- | --- |
| All Attempts |  |  |  |
| Overall | 129.6 | 134.0 | 225.5 |
| Iterative | 138.5 | 169.1 | 224.9 |
| Compositional | 104.6 | 34.0 | 227.0 |
| Successful Attempts Only |  |  |  |
| Overall | 37.7 | 51.2 | 43.6 |
| Iterative | 36.8 | 57.8 | 50.0 |
| Compositional | 39.5 | 38.0 | 34.0 |

Average Steps per Task. Table [4](#S5.T4) presents the average number of steps required per task for AgentProg and baselines on the AW-Extend dataset. Step counts should be interpreted with caution, as different methods require varying numbers of model queries per step: Mobile-Agent-v3 queries the language model three times per step and UI-TARS queries once per step while AgentProg uses two queries per step. The trends in step counts largely match those observed in token consumption as shown in Table [3](#S5.T3). When considering all attempts, the compositional task results show an anomalous pattern where Mobile-Agent-v3 uses very few steps, attributable to premature task termination due to forgotten subtasks. When examining only successful attempts, AgentProg requires fewer steps than baselines across the overall tasks and iterative tasks, with comparable performance on composition tasks. This demonstrates that AgentProg achieves better performance while maintaining step efficiency. The higher step counts in “All Attempts” group compared to “Successful Attempts Only” group can be attributed to two factors: first, tasks requiring fewer steps are inherently easier to complete successfully; second, failed attempts in “All Attempts” involve substantial iterative trial-and-error operations that inflate the step count.

## 6. Discussion

Accuracy-Latency Trade-off. As shown in Table [3](#S5.T3), AgentProg incurs higher latency and cost compared to baseline methods. This overhead stems primarily from the STP execution, including Program Counter Update, Action Generation, and Global Belief State maintenance. However, we argue that AgentProg primarily targets complex, long-horizon tasks suited for background execution, where users are far more sensitive to accuracy than latency, as fast agents become impractical if they require frequent human intervention for failures. We anticipate future model-level optimizations (e.g., faster inference speeds, distilled models) and system optimizations such as merging the Program Counter Update and Action Generation modes into a single LLM call where possible.

On-Device Deployment. Currently, AgentProg relies on cloud-based LLMs, which introduce network latency and privacy concerns. A promising future direction is deploying AgentProg with on-device Small Language Models (SLMs) via model distillation ([Wen et al., 2025](#bib.bib46)). Our program-guided context management reduces the input dynamic context size and the static context can be eliminated entirely through distillation, which is compatible with the limited context lengths of on-device SLMs. Besides, AgentProg supports a hybrid deployment strategy. STP Generation phase requiring stronger reasoning capabilities and more knowledge can remain on the cloud, while the STP Execution phase can be distilled into an on-device SLM, offering a flexible trade-off among latency, privacy, and accuracy.

Generalization to Broader Long-Horizon Agents. Although AgentProg is evaluated on mobile GUI tasks, the program-guided context management approach can be applied to other long-horizon agent settings, including web navigation, desktop automation, and tool-use environments. We leave the empirical validation of AgentProg on non-mobile settings to future work.

## 7. Conclusion

In this work, we introduce AgentProg to address the context bottleneck in long-horizon tasks.
By reframing interaction history into a structured Semantic Task Program, AgentProg enables principled context pruning and critical variable retention.
Additionally, our Global Belief State mechanism maintains an active mental model to handle partial observability and environmental dynamics.
Experiments on AndroidWorld and our AW-Extend benchmark demonstrate that AgentProg significantly outperforms state-of-the-art baselines.
Ultimately, our work establishes a scalable foundation for robust agent deployment in complex real-world scenarios.

## Acknowledgements

This research was supported in part by the National Natural Science Foundation of China under Grant No. 62432004 and 62272261, the Fundamental and Interdisciplinary Disciplines Breakthrough Plan of the Ministry of Education of China under Grant No. JYB2025XD

XM122, Wuxi Research Institute of Applied Technologies, Tsinghua University under Grant 20242001120, Tsinghua University (AIR)–AsiaInfo Technologies (China) Inc. Joint Research Center and a grant from the Guoqiang Institute, Tsinghua University.

## References

- Agashe et al. (2025)

  Saaket Agashe, Kyle Wong, Vincent Tu, Jiachen Yang, Ang Li, and Xin Eric Wang. 2025.
  Agent S2: A Compositional Generalist-Specialist Framework for Computer Use Agents.
  arXiv:2504.00906 [cs.AI]
  <https://arxiv.org/abs/2504.00906>
- An et al. (2024)

  Chenxin An, Jun Zhang, Ming Zhong, Lei Li, Shansan Gong, Yao Luo, Jingjing Xu, and Lingpeng Kong. 2024.
  Why does the effective context length of LLMs fall short?
  *arXiv preprint arXiv:2410.18745* (2024).
- Azim et al. (2016)

  Tanzirul Azim, Oriana Riva, and Suman Nath. 2016.
  ULink: Enabling User-Defined Deep Linking to App Content. In *Proceedings of the 14th Annual International Conference on Mobile Systems, Applications, and Services* (Singapore, Singapore) *(MobiSys ’16)*. Association for Computing Machinery, New York, NY, USA, 305–318.

  [doi:10.1145/2906388.2906416](https://doi.org/10.1145/2906388.2906416)
- Cheng et al. (2024)

  Kanzhi Cheng, Qiushi Sun, Yougang Chu, Fangzhi Xu, Yantao Li, Jianbing Zhang, and Zhiyong Wu. 2024.
  SeeClick: Harnessing GUI Grounding for Advanced Visual GUI Agents.
  arXiv:2401.10935 [cs.HC]
- Dai et al. (2025)

  Gaole Dai, Shiqi Jiang, Ting Cao, Yuanchun Li, Yuqing Yang, Rui Tan, Mo Li, and Lili Qiu. 2025.
  Advancing mobile gui agents: A verifier-driven approach to practical deployment.
  *arXiv preprint arXiv:2503.15937* (2025).
- Gao et al. (2025)

  Xinzge Gao, Chuanrui Hu, Bin Chen, and Teng Li. 2025.
  Chain-of-Memory: Enhancing GUI Agents for Cross-Application Navigation.
  arXiv:2506.18158 [cs.AI]
  <https://arxiv.org/abs/2506.18158>
- Gonzalez-Pumariega et al. (2025)

  Gonzalo Gonzalez-Pumariega, Vincent Tu, Chih-Lun Lee, Jiachen Yang, Ang Li, and Xin Eric Wang. 2025.
  The Unreasonable Effectiveness of Scaling Agents for Computer Use.
  arXiv:2510.02250 [cs.AI]
  <https://arxiv.org/abs/2510.02250>
- Google (2025)

  Google. 2025.
  Gemini 2.5 Pro - Google DeepMind.
  https://deepmind.google/models/gemini/pro/.
- Gou et al. (2025)

  Boyu Gou, Ruohan Wang, Boyuan Zheng, Yanan Xie, Cheng Chang, Yiheng Shu, Huan Sun, and Yu Su. 2025.
  Navigating the Digital World as Humans Do: Universal Visual Grounding for GUI Agents. In *The Thirteenth International Conference on Learning Representations*.

  <https://openreview.net/forum?id=kxnoqaisCT>
- Gu et al. (2025)

  Zhangxuan Gu, Zhengwen Zeng, Zhenyu Xu, Xingran Zhou, Shuheng Shen, Yunfei Liu, Beitong Zhou, Changhua Meng, Tianyu Xia, Weizhi Chen, et al. 2025.
  Ui-venus technical report: Building high-performance ui agents with rft.
  *arXiv preprint arXiv:2508.10833* (2025).
- Gur et al. (2024)

  Izzeddin Gur, Hiroki Furuta, Austin V Huang, Mustafa Safdari, Yutaka Matsuo, Douglas Eck, and Aleksandra Faust. 2024.
  A Real-World WebAgent with Planning, Long Context Understanding, and Program Synthesis. In *The Twelfth International Conference on Learning Representations*.

  <https://openreview.net/forum?id=9JQtrumvg8>
- Hong et al. (2025)

  Wenyi Hong, Wenmeng Yu, Xiaotao Gu, Guo Wang, Guobing Gan, Haomiao Tang, Jiale Cheng, Ji Qi, Junhui Ji, Lihang Pan, et al. 2025.
  GLM-4.1 V-Thinking: Towards Versatile Multimodal Reasoning with Scalable Reinforcement Learning.
  *arXiv preprint arXiv:2507.01006* (2025).
- Kaelbling et al. (1998)

  Leslie Pack Kaelbling, Michael L. Littman, and Anthony R. Cassandra. 1998.
  Planning and acting in partially observable stochastic domains.
  *Artif. Intell.* 101, 1–2 (May 1998), 99–134.
- Lee et al. (2024)

  Sunjae Lee, Junyoung Choi, Jungjae Lee, Munim Hasan Wasi, Hojun Choi, Steve Ko, Sangeun Oh, and Insik Shin. 2024.
  MobileGPT: Augmenting LLM with Human-like App Memory for Mobile Task Automation. In *Proceedings of the 30th Annual International Conference on Mobile Computing and Networking* (Washington D.C., DC, USA) *(ACM MobiCom ’24)*. Association for Computing Machinery, New York, NY, USA, 1119–1133.

  [doi:10.1145/3636534.3690682](https://doi.org/10.1145/3636534.3690682)
- Li et al. (2025c)

  Kuan Li, Zhongwang Zhang, Huifeng Yin, Rui Ye, Yida Zhao, Liwen Zhang, Litu Ou, Dingchu Zhang, Xixi Wu, Jialong Wu, et al. 2025c.
  Websailor-v2: Bridging the chasm to proprietary agents via synthetic data and scalable reinforcement learning.
  *arXiv preprint arXiv:2509.13305* (2025).
- Li et al. (2025a)

  Ning Li, Qiqiang Lin, Zheng Wu, Xiaoyun Mo, Weiming Zhang, Yin Zhao, Xiangmou Qu, Jiamu Zhou, Jun Wang, Congmin Zheng, et al. 2025a.
  ColorAgent: Building A Robust, Personalized, and Interactive OS Agent.
  *arXiv preprint arXiv:2510.19386* (2025).
- Li et al. (2025b)

  Ning Li, Xiangmou Qu, Jiamu Zhou, Jun Wang, Muning Wen, Kounianhua Du, Xingyu Lou, Qiuying Peng, and Weinan Zhang. 2025b.
  MobileUse: A GUI Agent with Hierarchical Reflection for Autonomous Mobile Operation.
  *arXiv preprint arXiv:2507.16853* (2025).
- Li and Riva (2018)

  Toby Jia-Jun Li and Oriana Riva. 2018.
  Kite: Building Conversational Bots from Mobile Apps. In *Proceedings of the 16th Annual International Conference on Mobile Systems, Applications, and Services* (Munich, Germany) *(MobiSys ’18)*. Association for Computing Machinery, New York, NY, USA, 96–109.

  [doi:10.1145/3210240.3210339](https://doi.org/10.1145/3210240.3210339)
- Li et al. (2020)

  Yang Li, Jiacong He, Xin Zhou, Yuan Zhang, and Jason Baldridge. 2020.
  Mapping Natural Language Instructions to Mobile UI Action Sequences. In *Annual Conference of the Association for Computational Linguistics (ACL 2020)*.

  <https://www.aclweb.org/anthology/2020.acl-main.729.pdf>
- Liang et al. (2023)

  Jacky Liang, Wenlong Huang, Fei Xia, Peng Xu, Karol Hausman, Brian Ichter, Pete Florence, and Andy Zeng. 2023.
  Code as Policies: Language Model Programs for Embodied Control. In *2023 IEEE International Conference on Robotics and Automation (ICRA)*. 9493–9500.
  [doi:10.1109/ICRA48891.2023.10160591](https://doi.org/10.1109/ICRA48891.2023.10160591)
- Liu et al. (2018)

  Evan Zheran Liu, Kelvin Guu, Panupong Pasupat, Tianlin Shi, and Percy Liang. 2018.
  Reinforcement Learning on Web Interfaces using Workflow-Guided Exploration. In *International Conference on Learning Representations (ICLR)*.

  <https://arxiv.org/abs/1802.08802>
- Liu et al. (2024)

  Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. 2024.
  Lost in the Middle: How Language Models Use Long Contexts.
  *Transactions of the Association for Computational Linguistics* 12 (2024), 157–173.
  [doi:10.1162/tacl\_a\_00638](https://doi.org/10.1162/tacl_a_00638)
- Liu et al. (2025)

  Shunyu Liu, Minghao Liu, Huichi Zhou, Zhenyu Cui, Yang Zhou, Yuhao Zhou, Wendong Fan, Ge Zhang, Jiajun Shi, Weihao Xuan, et al. 2025.
  Verigui: Verifiable long-chain gui dataset.
  *arXiv preprint arXiv:2508.04026v1* (2025).
- Liu et al. (2026)

  Shunyu Liu, Minghao Liu, Huichi Zhou, Zhenyu Cui, Yang Zhou, Yuhao Zhou, Jialiang Gao, Heng Zhou, Yunhao Yang, Wendong Fan, puzhen zhang, Ge Zhang, Jiajun Shi, Weihao Xuan, Jiaxing Huang, Shuang Luo, Fang Wu, Heli Qi, Qingcheng Zeng, Junjie Wang, Aosong Feng, Jindi Lv, Sicong Jiang, Ziqi Ren, Wangchunshu Zhou, Zhenfei Yin, Wenlong Zhang, Guohao Li, Wenhao Yu, Lei Ma, Lei Bai, Qunshu Lin, Mingli Song, and
  Dacheng Tao. 2026.
  VeriWeb: Verifiable Long-Chain Web Benchmark for Agentic Information-Seeking.
  *arXiv preprint arXiv:2508.04026v2* (2026).
- Mozannar et al. (2025)

  Hussein Mozannar, Gagan Bansal, Cheng Tan, Adam Fourney, Victor Dibia, Jingya Chen, Jack Gerrits, Tyler Payne, Matheus Kunzler Maldaner, Madeleine Grunde-McLaughlin, et al. 2025.
  Magentic-UI: Towards Human-in-the-loop Agentic Systems.
  *arXiv preprint arXiv:2507.22358* (2025).
- Nguyen et al. (2025)

  Dang Nguyen, Jian Chen, Yu Wang, Gang Wu, Namyong Park, Zhengmian Hu, Hanjia Lyu, Junda Wu, Ryan Aponte, Yu Xia, Xintong Li, Jing Shi, Hongjie Chen, Viet Dac Lai, Zhouhang Xie, Sungchul Kim, Ruiyi Zhang, Tong Yu, Mehrab Tanjim, Nesreen K. Ahmed, Puneet Mathur, Seunghyun Yoon, Lina Yao, Branislav Kveton, Jihyung Kil, Thien Huu Nguyen, Trung Bui, Tianyi Zhou, Ryan A. Rossi, and Franck Dernoncourt. 2025.
  GUI Agents: A Survey.
  arXiv:2412.13501 [cs.AI]
  <https://arxiv.org/abs/2412.13501>
- Qin et al. (2025)

  Yujia Qin, Yining Ye, Junjie Fang, Haoming Wang, Shihao Liang, Shizuo Tian, Junda Zhang, Jiahao Li, Yunxin Li, Shijue Huang, et al. 2025.
  Ui-tars: Pioneering automated gui interaction with native agents.
  *arXiv preprint arXiv:2501.12326* (2025).
- Rawles et al. (2024)

  Christopher Rawles, Sarah Clinckemaillie, Yifan Chang, Jonathan Waltz, Gabrielle Lau, Marybeth Fair, Alice Li, William Bishop, Wei Li, Folawiyo Campbell-Ajala, Daniel Toyama, Robert Berry, Divya Tyamagundlu, Timothy Lillicrap, and Oriana Riva. 2024.
  AndroidWorld: A Dynamic Benchmarking Environment for Autonomous Agents.
  arXiv:2405.14573 [cs.AI]
  <https://arxiv.org/abs/2405.14573>
- Schroeder et al. (2025)

  Philip Schroeder, Nathaniel W Morgan, Hongyin Luo, and James Glass. 2025.
  Thread: Thinking deeper with recursive spawning. In *Proceedings of the 2025 Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers)*. 8418–8442.
- Shen et al. (2025)

  Leming Shen, Qiang Yang, Yuanqing Zheng, and Mo Li. 2025.
  AutoIOT: LLM-Driven Automated Natural Language Programming for AIoT Applications. In *Proceedings of the 31st Annual International Conference on Mobile Computing and Networking* (Kerry Hotel, Hong Kong, Hong Kong, China) *(ACM MOBICOM ’25)*. Association for Computing Machinery, New York, NY, USA, 468–482.

  [doi:10.1145/3680207.3723486](https://doi.org/10.1145/3680207.3723486)
- Shinn et al. (2023)

  Noah Shinn, Federico Cassano, Beck Labash, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. 2023.
  Reflexion: Language Agents with Verbal Reinforcement Learning.
- Sondik (1978)

  Edward J. Sondik. 1978.
  The Optimal Control of Partially Observable Markov Processes Over the Infinite Horizon: Discounted Costs.
  *Operations Research* 26, 2 (1978), 282–304.

  <https://doi.org/10.1287/opre.26.2.282>
- Song et al. (2025a)

  Linxin Song, Yutong Dai, Viraj Prabhu, Jieyu Zhang, Taiwei Shi, Li Li, Junnan Li, Silvio Savarese, Zeyuan Chen, Jieyu Zhao, et al. 2025a.
  Coact-1: Computer-using agents with coding as actions.
  *arXiv preprint arXiv:2508.03923* (2025).
- Song et al. (2025b)

  Yuanyi Song, Heyuan Huang, Qiqiang Lin, Yin Zhao, Xiangmou Qu, Jun Wang, Xingyu Lou, Weiwen Liu, Zhuosheng Zhang, Yong Yu, Weinan Zhang, and Zhaoxiang Wang. 2025b.
  ColorBench: Benchmarking Mobile Agents with Graph-Structured Framework for Complex Long-Horizon Tasks.
  *arXiv preprint arXiv:2510.14621* (2025).
- Sun et al. (2023)

  Haotian Sun, Yuchen Zhuang, Lingkai Kong, Bo Dai, and Chao Zhang. 2023.
  AdaPlanner: Adaptive Planning from Feedback with Language Models.
  *arXiv preprint arXiv:2305.16653* (2023).
- Sun et al. (2022)

  Liangtai Sun, Xingyu Chen, Lu Chen, Tianle Dai, Zichen Zhu, and Kai Yu. 2022.
  META-GUI: Towards Multi-modal Conversational Agents on Mobile GUI.
  *arXiv preprint arXiv:2205.11029* (2022).
- Tan et al. (2024)

  Weihao Tan, Wentao Zhang, Xinrun Xu, Haochong Xia, Ziluo Ding, Boyu Li, Bohan Zhou, Junpeng Yue, Jiechuan Jiang, Yewen Li, Ruyi An, Molei Qin, Chuqiao Zong, Longtao Zheng, Yujie Wu, Xiaoqiang Chai, Yifei Bi, Tianbao Xie, Pengjie Gu, Xiyun Li, Ceyao Zhang, Long Tian, Chaojie Wang, Xinrun Wang, Börje F. Karlsson, Bo An, Shuicheng Yan, and Zongqing Lu. 2024.
  Cradle: Empowering Foundation Agents Towards General Computer Control.
  arXiv:2403.03186 [cs.AI]
  <https://arxiv.org/abs/2403.03186>
- Wang et al. (2025b)

  Haoming Wang, Haoyang Zou, Huatong Song, Jiazhan Feng, Junjie Fang, Junting Lu, Longxiang Liu, Qinyu Luo, Shihao Liang, Shijue Huang, Wanjun Zhong, Yining Ye, Yujia Qin, Yuwen Xiong, Yuxin Song, Zhiyong Wu, Bo Li, Chen Dun, Chong Liu, Fuxing Leng, Han rui Wang, Hao Yu, Haobin Chen, Hongyi Guo, Jing Su, Jingjia Huang, Kai Shen, Kaiyu Shi, Lin Yan, Pei-Xiong Zhao, Pengfei Liu, Qinghao Ye, Renjie Zheng,
  Wayne Xin Zhao, Wen Heng, Wenhao Huang, Wenqian Wang, Xiao-Jun Qin, Yi Lin, Youbing Wu, Zehui Chen, Zihao Wang, Baoquan Zhong, Xinchun Zhang, Xujing Li, YuanFang Li, Zhongkai Zhao, Chengquan Jiang, Faming Wu, Hao Zhou, Jinlin Pang, Li Han, Qianli Ma, Siyao Liu, Songhua Cai, Wenqi Fu, Xin Liu, Zhi Zhang, Bo Zhou, Guoliang Li, Jiajun Shi, Jiale Yang, Jie Tang, Li Li, Taoran Lu, Woyu Lin, Xiao Tong,
  Xinyao Li, Yichi Zhang, Yu Miao, Zheng-Wang Jiang, Zili Li, Zi-Hao Zhao, Chenxi Li, Dehua Ma, Feng Lin, Ge Zhang, Haihua Yang, Hangyu Guo, Hongda Zhu, Jiaheng Liu, Jun-Yan Du, Kai Cai, Kuanye Li, Lichen Yuan, Mei Han, Minchao Wang, Shuyu Guo, Tianhao Cheng, Xiaobo Ma, Xiao Xiao, Xiaolong Huang, Xinjie Chen, Yi-Zhen Du, Yilin Chen, Yiwen Wang, Zhaojian Li, Zhen Yang, Zhiyuan Zeng, Chaolin Jin, Chen Li,
  Haolin Chen, Haolin Chen, Jian Chen, Qinghao Zhao, and Guang Shi. 2025b.
  UI-TARS-2 Technical Report: Advancing GUI Agent with Multi-Turn Reinforcement Learning.
  *arXiv preprint arXiv:2509.02544* (2025).
- Wang et al. (2024c)

  Junyang Wang, Haiyang Xu, Jiabo Ye, Ming Yan, Weizhou Shen, Ji Zhang, Fei Huang, and Jitao Sang. 2024c.
  Mobile-agent: Autonomous multi-modal mobile device agent with visual perception.
  *arXiv preprint arXiv:2401.16158* (2024).
- Wang et al. (2024b)

  Luyuan Wang, Yongyu Deng, Yiwei Zha, Guodong Mao, Qinmin Wang, Tianchen Min, Wei Chen, and Shoufa Chen. 2024b.
  MobileAgentBench: An Efficient and User-Friendly Benchmark for Mobile LLM Agents.
  *arXiv preprint arXiv:2406.08184* (2024).
- Wang et al. (2024a)

  Xingyao Wang, Yangyi Chen, Lifan Yuan, Yizhe Zhang, Yunzhu Li, Hao Peng, and Heng Ji. 2024a.
  Executable Code Actions Elicit Better LLM Agents. In *ICML*.
  arXiv:2402.01030
- Wang et al. (2025a)

  Zora Zhiruo Wang, Apurva Gandhi, Graham Neubig, and Daniel Fried. 2025a.
  Inducing Programmatic Skills for Agentic Tasks. In *Second Conference on Language Modeling*.

  <https://openreview.net/forum?id=lsAY6fWsog>
- Wei et al. (2022)

  Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, brian ichter, Fei Xia, Ed Chi, Quoc V Le, and Denny Zhou. 2022.
  Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. In *Advances in Neural Information Processing Systems*, S. Koyejo, S. Mohamed, A. Agarwal, D. Belgrave, K. Cho, and A. Oh (Eds.), Vol. 35. Curran Associates, Inc., 24824–24837.

  <https://proceedings.neurips.cc/paper_files/paper/2022/file/9d5609613524ecf4f15af0f7b31abca4-Paper-Conference.pdf>
- Wen et al. (2024)

  Hao Wen, Yuanchun Li, Guohong Liu, Shanhui Zhao, Tao Yu, Toby Jia-Jun Li, Shiqi Jiang, Yunhao Liu, Yaqin Zhang, and Yunxin Liu. 2024.
  AutoDroid: LLM-powered Task Automation in Android. In *Proceedings of the 30th Annual International Conference on Mobile Computing and Networking* (Washington D.C., DC, USA) *(ACM MobiCom ’24)*. Association for Computing Machinery, New York, NY, USA, 543–557.

  [doi:10.1145/3636534.3649379](https://doi.org/10.1145/3636534.3649379)
- Wen et al. (2025)

  Hao Wen, Shizuo Tian, Borislav Pavlov, Wenjie Du, Yixuan Li, Ge Chang, Shanhui Zhao, Jiacheng Liu, Yunxin Liu, Ya-Qin Zhang, and Yuanchun Li. 2025.
  *AutoDroid-V2: Boosting SLM-based GUI Agents via Code Generation*.
  Association for Computing Machinery, New York, NY, USA, 223–235.

  <https://doi.org/10.1145/3711875.3729134>
- Wu et al. (2024a)

  Zhiyong Wu, Chengcheng Han, Zichen Ding, Zhenmin Weng, Zhoumianze Liu, Shunyu Yao, Tao Yu, and Lingpeng Kong. 2024a.
  Os-copilot: Towards generalist computer agents with self-improvement.
  *arXiv preprint arXiv:2402.07456* (2024).
- Wu et al. (2024b)

  Zhiyong Wu, Zhenyu Wu, Fangzhi Xu, Yian Wang, Qiushi Sun, Chengyou Jia, Kanzhi Cheng, Zichen Ding, Liheng Chen, Paul Pu Liang, et al. 2024b.
  OS-ATLAS: A Foundation Action Model for Generalist GUI Agents.
  *arXiv preprint arXiv:2410.23218* (2024).
- Xu et al. (2024a)

  Jiajun Xu, Zhiyuan Li, Wei Chen, Qun Wang, Xin Gao, Qi Cai, and Ziyuan Ling. 2024a.
  On-device language models: A comprehensive review.
  *arXiv preprint arXiv:2409.00088* (2024).
- Xu et al. (2025)

  Yifan Xu, Xiao Liu, Xinghan Liu, Jiaqi Fu, Hanchen Zhang, Bohao Jing, Shudan Zhang, Yuting Wang, Wenyi Zhao, and Yuxiao Dong. 2025.
  MobileRL: Online Agentic Reinforcement Learning for Mobile GUI Agents.
  *arXiv preprint arXiv:2509.18119* (2025).
- Xu et al. (2024b)

  Yifan Xu, Xiao Liu, Xueqiao Sun, Siyi Cheng, Hao Yu, Hanyu Lai, Shudan Zhang, Dan Zhang, Jie Tang, and Yuxiao Dong. 2024b.
  AndroidLab: Training and Systematic Benchmarking of Android Autonomous Agents.
  arXiv:2410.24024 [cs.AI]
  <https://arxiv.org/abs/2410.24024>
- Yan et al. (2023)

  An Yan, Zhengyuan Yang, Wanrong Zhu, Kevin Lin, Linjie Li, Jianfeng Wang, Jianwei Yang, Yiwu Zhong, Julian McAuley, Jianfeng Gao, et al. 2023.
  GPT-4V in Wonderland: Large Multimodal Models for Zero-Shot Smartphone GUI Navigation.
  *arXiv preprint arXiv:2311.07562* (2023).
- Yao et al. (2023)

  Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths, Yuan Cao, and Karthik Narasimhan. 2023.
  Tree of Thoughts: Deliberate Problem Solving with Large Language Models.
  arXiv:2305.10601 [cs.CL]
- Ye et al. (2025b)

  Jiabo Ye, Xi Zhang, Haiyang Xu, Haowei Liu, Junyang Wang, Zhaoqing Zhu, Ziwei Zheng, Feiyu Gao, Junjie Cao, Zhengxi Lu, et al. 2025b.
  Mobile-agent-v3: Fundamental agents for gui automation.
  *arXiv preprint arXiv:2508.15144* (2025).
- Ye et al. (2025a)

  Suyu Ye, Haojun Shi, Darren Shih, Hyokun Yun, Tanya Roosta, and Tianmin Shu. 2025a.
  RealWebAssist: A Benchmark for Long-Horizon Web Assistance with Real-World Users.
  *arXiv preprint arXiv:2504.10445* (2025).
- Zhang et al. (2024)

  Chaoyun Zhang, Liqun Li, Shilin He, Xu Zhang, Bo Qiao, Si Qin, Minghua Ma, Yu Kang, Qingwei Lin, Saravan Rajmohan, Dongmei Zhang, and Qi Zhang. 2024.
  UFO: A UI-Focused Agent for Windows OS Interaction.
  *arXiv preprint arXiv:2402.07939* (2024).
- Zhang et al. (2023)

  Chi Zhang, Zhao Yang, Jiaxuan Liu, Yucheng Han, Xin Chen, Zebiao Huang, Bin Fu, and Gang Yu. 2023.
  AppAgent: Multimodal Agents as Smartphone Users.
  arXiv:2312.13771 [cs.CV]
- Zhang et al. (2025)

  Zhenyu Zhang, Tianyi Chen, Weiran Xu, Alex Pentland, and Jiaxin Pei. 2025.
  ReCAP: Recursive Context-Aware Reasoning and Planning for Large Language Model Agents. In *Conference on Neural Information Processing Systems (NeurIPS)*.
- Zhang and Zhang (2024)

  Zhuosheng Zhang and Aston Zhang. 2024.
  You Only Look at Screens: Multimodal Chain-of-Action Agents. In *Findings of the Association for Computational Linguistics: ACL 2024*, Lun-Wei Ku, Andre Martins, and Vivek Srikumar (Eds.). Association for Computational Linguistics, Bangkok, Thailand, 3132–3149.
  [doi:10.18653/v1/2024.findings-acl.186](https://doi.org/10.18653/v1/2024.findings-acl.186)
- Zheng et al. (2024)

  Boyuan Zheng, Boyu Gou, Jihyung Kil, Huan Sun, and Yu Su. 2024.
  GPT-4V(ision) is a Generalist Web Agent, if Grounded. In *Forty-first International Conference on Machine Learning (ICML’24)*.

  <https://openreview.net/forum?id=piecKJ2DlB>
- Zhou et al. (2025)

  Zijian Zhou, Ao Qu, Zhaoxuan Wu, Sunghwan Kim, Alok Prakash, Daniela Rus, Jinhua Zhao, Bryan Kian Hsiang Low, and Paul Pu Liang. 2025.
  MEM1: Learning to Synergize Memory and Reasoning for Efficient Long-Horizon Agents.

  <https://arxiv.org/abs/2506.15841>

## Appendix A Syntax of Semantic Task Program

The syntax of Semantic Task Program (STP) is designed to resolve the conflict between the need for structural rigor in workflows and the inherent ambiguity of agent tasks. While Semantic Task Program adopts a natural-language-style appearance to ensure expressiveness, it is fundamentally a structured language. It imposes a rigid skeleton of control flow (loops, conditionals, functions) to maintain logical consistency, while allowing the atomic instructions within that skeleton to remain "soft" and flexible.

This design philosophy differs from traditional coding, which demands precision everywhere, and prompt engineering, which lacks structural constraints. Semantic Task Program allows developers to be precise about procedure (e.g., "iterate exactly 10 times") while being fuzzy about implementation (e.g., "extract the sentiment"). This section outlines how Semantic Task Program implements this hybrid approach.

### A.1. Basic Statements and Comments

Semantic Task Program adopts an intent-based programming style. Instructions are written as imperative or declarative sentences that prioritize conveying the user’s goal over adhering to strict syntactic rules.

[⬇](data:text/plain;base64,IyBUaGlzIGlzIGEgY29tbWVudCwgdXNlZCBmb3IgaHVtYW4tcmVhZGFibGUgYW5ub3RhdGlvbnMuCnRlbGwgdXNlciAiSGVsbG8sIHdvcmxkISIgICMgSW5saW5lIGNvbW1lbnRzIGFyZSBhbHNvIHN1cHBvcnRlZC4KCiMgVGhlIGZvbGxvd2luZyBzdGF0ZW1lbnRzIGFyZSBhbHNvIHZhbGlkOgpzZW5kICJIZWxsbywgd29ybGQhIiB0byB0aGUgdXNlcgpub3RpZnkgdXNlciB3aXRoIG1lc3NhZ2UgIkhlbGxvLCB3b3JsZCEiCnNlbmQgYSBncmVldGluZyBtZXNzYWdlIHRvIHVzZXI=)

1
# This is a comment, used for human-readable annotations.

2
tell user "Hello, world!" # Inline comments are also supported.

3

4
# The following statements are also valid:

5
send "Hello, world!" to the user

6
notify user with message "Hello, world!"

7
send a greeting message to user

Comments are ignored by AgentProg and serve only to document the code. Statements like tell user "..." are direct commands that are translated into actions. For familiarity, Semantic Task Program also permits Python-style syntax where appropriate (e.g., print("Hello, world!")), which the AgentProg processes as an equivalent intent rather than executing directly.

### A.2. Variables and Data Management

In agentic workflows, data is often unstructured (e.g., natural text, web content) and does not fit neatly into the rigid types of C++ or Java. Semantic Task Program addresses this by treating variables as named containers for information, explicitly demarcated by curly braces {} (e.g., {userName}). This notation serves a dual purpose: it provides a clear anchor for the AgentProg to track state within a fuzzy instruction, and it allows the language to handle unstructured data without requiring complex schema definitions upfront.

Declaration and Assignment: Variables are declared implicitly upon their first assignment. Semantic Task Program supports multiple natural phrasings for assignment, treating them as synonyms.

[⬇](data:text/plain;base64,c2V0IHZhcmlhYmxlIHt1c2VyTmFtZX0gdG8gIkFsaWNlIgpzdG9yZSAxMDAgaW50byB7aW5pdGlhbFNjb3JlfQpzZXQge3VzZXJDb3VudH0gdG8gMCAjIFB5dGhvbi1zdHlsZSBhc3NpZ25tZW50IGlzIGFsc28gdmFsaWQu)

1
set variable {userName} to "Alice"

2
store 100 into {initialScore}

3
set {userCount} to 0 # Python-style assignment is also valid.

Using Variables: To reference a variable’s value, simply include its braced name within a statement. The AgentProg substitutes it with its current value during execution.

[⬇](data:text/plain;base64,dGVsbCB1c2VyICJXZWxjb21lLCB7dXNlck5hbWV9ISBZb3VyIHNjb3JlIGlzIHtpbml0aWFsU2NvcmV9LiIKY2FsY3VsYXRlIHtpbml0aWFsU2NvcmV9ICsgNTAsIHJlY29yZCBhcyB7ZmluYWxTY29yZX0=)

1
tell user "Welcome, {userName}! Your score is {initialScore}."

2
calculate {initialScore} + 50, record as {finalScore}

Dynamic Type System: Semantic Task Program employs a dynamic type system where users are not required to declare types explicitly. The AgentProg infers and manages types—such as Text, Number, Boolean, List, and Object—based on context and value. This approach aligns with the needs of both novice programmers and LLMs, which may struggle with strict static typing. While types are inferred, users can provide hints to guide the interpreter, for instance, when interacting with an AI model.

- •

  List: An ordered collection.

  [⬇](data:text/plain;base64,cmVjb3JkIGxpc3QgImFwcGxlcyIsICJiYW5hbmFzIiwgImNoZXJyaWVzIiBhcyB7ZnJ1aXRCYXNrZXR9)

  1
  record list "apples", "bananas", "cherries" as {fruitBasket}
- •

  Object: A key-value store, akin to a dictionary or JSON object. Properties can be accessed using dot notation ({product.price}) or possessive phrasing ({myCar’s color}).

  [⬇](data:text/plain;base64,Y3JlYXRlIGFuIG9iamVjdCB7cHJvZHVjdH0gd2l0aCAibmFtZSIgYXMgIkxhcHRvcCIgYW5kICJwcmljZSIgYXMgMTIwMAp0ZWxsIHVzZXIgIntwcm9kdWN0Lm5hbWV9IGlzIGF2YWlsYWJsZSBmb3Ige3Byb2R1Y3QucHJpY2V9LiI=)

  1
  create an object {product} with "name" as "Laptop" and "price" as 1200

  2
  tell user "{product.name} is available for {product.price}."
- •

  Table: A structured list of objects, ideal for representing tabular data.

  [⬇](data:text/plain;base64,cmVhZCB0YWJsZSAic2FsZXNfZGF0YS5jc3YiIGFzIHtzYWxlc1JlcG9ydH0=)

  1
  read table "sales\_data.csv" as {salesReport}

Crucially, the AgentProg handles potential type mismatches intelligently. Instead of crashing, it attempts a reasonable type coercion (e.g., converting the text "123" to a number) or reports a descriptive, human-understandable issue.

### A.3. Control Flow

Control flow structures in Semantic Task Program use natural language keywords and rely on indentation to define code blocks, similar to Python. This maintains readability while avoiding complex bracketing.

Conditional Statements: if, else, else if structures evaluate conditions expressed in natural language or with standard operators.

[⬇](data:text/plain;base64,YXNrIHVzZXIgIkVudGVyIHlvdXIgYWdlOiIsIGdldCByZXNwb25zZSBhcyB7YWdlSW5wdXR9CmNvbnZlcnQge2FnZUlucHV0fSB0byBudW1iZXIsIGFzIHt1c2VyQWdlfQppZiB7dXNlckFnZX0gPCAxODoKICAgIHRlbGwgdXNlciAiWW91IGFyZSBhIG1pbm9yLiIKZWxzZSwgaWYge3VzZXJBZ2V9IGlzIGJldHdlZW4gMTggYW5kIDY1OiAjIE5hdHVyYWwgbGFuZ3VhZ2UgY29uZGl0aW9uIGFsbG93ZWQKICAgIHRlbGwgdXNlciAiWW91IGFyZSBhbiBhZHVsdC4iCmVsc2U6CiAgICB0ZWxsIHVzZXIgIllvdSBhcmUgYSBzZW5pb3IgY2l0aXplbi4i)

1
ask user "Enter your age:", get response as {ageInput}

2
convert {ageInput} to number, as {userAge}

3
if {userAge} < 18:

4
 tell user "You are a minor."

5
else, if {userAge} is between 18 and 65: # Natural language condition allowed

6
 tell user "You are an adult."

7
else:

8
 tell user "You are a senior citizen."

Loops: Semantic Task Program supports various loop constructs, each initiated with flexible, descriptive phrasing.

- •

  Fixed Repetitions:

  [⬇](data:text/plain;base64,cmVwZWF0IDUgdGltZXM6CiAgICAjIHtsb29wLml0ZXJhdGlvbn0gaXMgYSBzcGVjaWFsIHZhcmlhYmxlICgxLWluZGV4ZWQpCiAgICB0ZWxsIHVzZXIgIlRoaXMgaXMgbWVzc2FnZSBudW1iZXIge2xvb3AuaXRlcmF0aW9ufSI=)

  1
  repeat 5 times:

  2
   # {loop.iteration} is a special variable (1-indexed)

  3
   tell user "This is message number {loop.iteration}"
- •

  Iterating over Collections:

  [⬇](data:text/plain;base64,aXRlcmF0ZSB0aHJvdWdoIGVhY2ggaXRlbSBpbiB7ZnJ1aXRCYXNrZXR9IGFzIHtmcnVpdH06CiAgICB0ZWxsIHVzZXIgIkZvdW5kIGZydWl0OiB7ZnJ1aXR9Ig==)

  1
  iterate through each item in {fruitBasket} as {fruit}:

  2
   tell user "Found fruit: {fruit}"
- •

  Conditional Loops:

  [⬇](data:text/plain;base64,d2hpbGUge3N5c3RlbVN0YXR1c30gaXMgImFjdGl2ZSI6CiAgICBjaGVjayBmb3IgbmV3IG1lc3NhZ2VzCiAgICB3YWl0IDEwIHNlY29uZHM=)

  1
  while {systemStatus} is "active":

  2
   check for new messages

  3
   wait 10 seconds

### A.4. Functions

To promote modularity and code reuse, Semantic Task Program allows users to define reusable blocks of logic as functions.

Defining a Function: A function is defined with a name, a list of expected inputs (parameters), and a body of instructions.

[⬇](data:text/plain;base64,ZGVmaW5lIGZ1bmN0aW9uIG5hbWVkICJjYWxjdWxhdGVBcmVhIjoKICAgIGZ1bmN0aW9uIGlucHV0czoge2xlbmd0aH0gKG51bWJlciksIHt3aWR0aH0gKG51bWJlcikKICAgIGNhbGN1bGF0ZSB7bGVuZ3RofSAqIHt3aWR0aH0sIHJlY29yZCBhcyB7YXJlYX0KICAgIGZ1bmN0aW9uIHJldHVybnMge2FyZWF9)

1
define function named "calculateArea":

2
 function inputs: {length} (number), {width} (number)

3
 calculate {length} \* {width}, record as {area}

4
 function returns {area}

Executing a Function: Functions are called by name, with arguments passed using a clear key-value format.

[⬇](data:text/plain;base64,ZXhlY3V0ZSBmdW5jdGlvbiAiY2FsY3VsYXRlQXJlYSIsIHdpdGgge2xlbmd0aH0gYXMgMTAgYW5kIHt3aWR0aH0gYXMgNSwgc2F2ZSByZXN1bHQgYXMge3Jvb21BcmVhfQp0ZWxsIHVzZXIgIlRoZSByb29tIGFyZWEgaXMge3Jvb21BcmVhfSBzcXVhcmUgdW5pdHMuIg==)

1
execute function "calculateArea", with {length} as 10 and {width} as 5, save result as {roomArea}

2
tell user "The room area is {roomArea} square units."

### A.5. Interactions with External Tools

A cornerstone of Semantic Task Program is its native ability to interact with the broader digital environment, including AI models and external tools, through high-level, declarative commands.

Tool Use (File System, Browser): Semantic Task Program provides a unified, high-level interface for common tool interactions. This design allows users to specify \*what\* they want to achieve, leaving the \*how\* to the AgentProg.

[⬇](data:text/plain;base64,IyBGaWxlIFN5c3RlbQpyZWFkIHRleHQgZnJvbSBmaWxlICJjb25maWcudHh0IiBhcyB7Y29uZmlnQ29udGVudH0Kc2F2ZSB7c3VtbWFyeX0gdG8gZmlsZSAic3VtbWFyeS50eHQiCgojIFdlYiBCcm93c2VyIEF1dG9tYXRpb24Kb3BlbiBVUkwgImh0dHBzOi8vZW4ud2lraXBlZGlhLm9yZyIKc2VhcmNoICJIZWxsbyBXb3JsZCIKd2FpdCBmb3IgcGFnZSB0byBsb2FkCmdldCBjdXJyZW50IHBhZ2UgY29udGVudCBhcyB7d2lraVBhZ2VDb250ZW50fQ==)

1
# File System

2
read text from file "config.txt" as {configContent}

3
save {summary} to file "summary.txt"

4

5
# Web Browser Automation

6
open URL "https://en.wikipedia.org"

7
search "Hello World"

8
wait for page to load

9
get current page content as {wikiPageContent}

The AgentProg’s context-aware nature is critical here. It resolves ambiguous references like "search input" or "Search button" by analyzing the current state of the web page (its DOM structure and visual layout), making automation scripts more robust and less brittle.

## Appendix B Runtime Recovery Example of Global Belief State

Figure [9](#A2.F9) demonstrates a runtime recovery example of Global Belief State.

![Refer to caption](images/21_AgentProg/gbs_example.png)


Figure 9. A runtime recovery example of global belief state.

## Appendix C Tasks in AW-Extend

Table [5](#A3.T5) shows the task descriptions of all tasks in AW-Extend.

Table 5. Task descriptions in AW-Extend. “Long” denotes tasks with $n{=}10$ subtasks and “SuperLong” denotes $n{=}20$ .

| Task Name | Instruction Template |
| --- | --- |
| ContactsAddContactAndSms | Create a new contact for {name}. Their number is {number}. Then, send ‘hello, {name}’ to {number} via SMS using Simple SMS Messenger. |
| ContactsAddMultipleContactsAndSms | For the following persons: {contacts}, add them as new contacts, and then use Simple SMS Messenger to send each of them a ‘hello, [Name]’ message. |
| MarkorFetchMultipleNotesAndSms | Retrieve the file name they sent you via Simple SMS Messenger, open it in Markor, and then send its contents back to that number for each number in {numbers}. |
| MarkorFetchNoteAndSms | Obtain the file name sent to you by {number} in Simple SMS Messenger, open the file in Markor, and send its contents back to {number}. |
| MarkorTodoList | Open my Markor note {file_name} and complete all the tasks on the list. |
| SimpleCalendarDeleteEventsLong | In Simple Calendar Pro, delete all the calendar events on {year}-{month}-{day}. |
| SimpleCalendarDeleteEventsOnRelativeDayLong | In Simple Calendar Pro, delete all events scheduled for this {day_of_week}. |
| SimpleCalendarDeleteEventsSuperLong | In Simple Calendar Pro, delete all the calendar events on {year}-{month}-{day}. |
| SimpleCalendarDeleteEventsOnRelativeDaySuperLong | In Simple Calendar Pro, delete all events scheduled for this {day_of_week}. |
| ExpenseAddMultipleLong | Add the following expenses into the Pro Expense: {expenses}. |
| ExpenseAddMultipleSuperLong | Add the following expenses into the Pro Expense: {expenses}. |
| ExpenseDeleteMultipleSuperLong | Delete the following expenses from Arduia Pro Expense: {expenses}. |
| ExpenseDeleteMultipleLong2 | Delete the following expenses from Arduia Pro Expense: {expenses}. |
| ExpenseDeleteMultipleSuperLong2 | Delete the following expenses from Arduia Pro Expense: {expenses}. |
| RecipeAddMultipleRecipesLong | Add the following recipes into the Broccoli app: {recipes}. |
| RecipeAddMultipleRecipesSuperLong | Add the following recipes into the Broccoli app: {recipes}. |
| RecipeDeleteMultipleRecipesLong | Delete the following recipes from Broccoli app: {titles}. |
| RecipeDeleteMultipleRecipesSuperLong | Delete the following recipes from Broccoli app: {titles}. |
| MarkorMergeNotesLong | Merge the contents of Markor notes {file1_name}, {file2_name} and {file3_name} into a new note named {new_file_name}. Add a new line between each. |

## Appendix D End-to-End Pipeline Walkthrough

We provide a concrete walkthrough of a representative AW-Extend task that combines explicit variables, loop control flow, cross-app execution, and persistent belief tracking. The user instruction is:

For the following persons: Name: Hana Ferreira, Number: +10662908339, Name: Sophie Martin, Number: +18723713947, Name: Olivia Alves, Number: +16278036185,add them as new contacts, and then use Simple SMS Messenger to send each of them a ’hello, [Name]’ message, where [Name] is the name of each contact.

STP Generation Phase. The high-level user request is first converted into the following STP:

[⬇](data:text/plain;base64,IyBDcmVhdGUgYSBsaXN0IG9mIG9iamVjdHMgdG8gc3RvcmUgdGhlIGNvbnRhY3QgaW5mb3JtYXRpb24KQ3JlYXRlIGEgbGlzdCBvZiBvYmplY3RzIG5hbWVkIHtjb250YWN0X2xpc3R9LCB3aXRoIHRoZSBmb2xsb3dpbmcgaXRlbXM6CiAgICBBbiBvYmplY3Qgd2l0aCAibmFtZSIgc2V0IHRvICJIYW5hIEZlcnJlaXJhIiBhbmQgIm51bWJlciIgc2V0IHRvICIrMTA2NjI5MDgzMzkiCiAgICBBbiBvYmplY3Qgd2l0aCAibmFtZSIgc2V0IHRvICJTb3BoaWUgTWFydGluIiBhbmQgIm51bWJlciIgc2V0IHRvICIrMTg3MjM3MTM5NDciCiAgICBBbiBvYmplY3Qgd2l0aCAibmFtZSIgc2V0IHRvICJPbGl2aWEgQWx2ZXMiIGFuZCAibnVtYmVyIiBzZXQgdG8gIisxNjI3ODAzNjE4NSIKCiMgSXRlcmF0ZSB0aHJvdWdoIGVhY2ggY29udGFjdCB0byBhZGQgdGhlbSBhbmQgc2VuZCBhIG1lc3NhZ2UKSXRlcmF0ZSB0aHJvdWdoIGVhY2ggaXRlbSBpbiB7Y29udGFjdF9saXN0fSwgcmVjb3JkZWQgYXMge2N1cnJlbnRfY29udGFjdH06CiAgICAjIEFkZCB0aGUgcGVyc29uIGFzIGEgbmV3IGNvbnRhY3QKICAgIEluIHRoZSBgQ29udGFjdHNgIGFwcCwgYWRkIGEgbmV3IGNvbnRhY3Qgd2l0aCBuYW1lIHtjdXJyZW50X2NvbnRhY3QubmFtZX0gYW5kIHBob25lIG51bWJlciB7Y3VycmVudF9jb250YWN0Lm51bWJlcn0sIGFuZCBzYXZlIGl0LgoKICAgICMgU2VuZCBhIHBlcnNvbmFsaXplZCBTTVMgbWVzc2FnZQogICAgSW4gdGhlIGBTaW1wbGUgU01TIE1lc3NlbmdlcmAgYXBwLCBzZW5kIGEgbWVzc2FnZSB0byB7Y3VycmVudF9jb250YWN0Lm51bWJlcn0gd2l0aCB0aGUgY29udGVudCAiaGVsbG8sIHtjdXJyZW50X2NvbnRhY3QubmFtZX0iLg==)

1
# Create a list of objects to store the contact information

2
Create a list of objects named {contact\_list}, with the following items:

3
 An object with "name" set to "Hana Ferreira" and "number" set to "+10662908339"

4
 An object with "name" set to "Sophie Martin" and "number" set to "+18723713947"

5
 An object with "name" set to "Olivia Alves" and "number" set to "+16278036185"

6

7
# Iterate through each contact to add them and send a message

8
Iterate through each item in {contact\_list}, recorded as {current\_contact}:

9
 # Add the person as a new contact

10
 In the ‘Contacts‘ app, add a new contact with name {current\_contact.name} and phone number {current\_contact.number}, and save it.

11

12
 # Send a personalized SMS message

13
 In the ‘Simple SMS Messenger‘ app, send a message to {current\_contact.number} with the content "hello, {current\_contact.name}".

STP Execution Phase. In STP Execution Phase, AgentProg alternates between two modes to executes STP.

Representative prompt instances. At execution time, the LLM receives a fixed system prefix plus a dynamic context. Below we show the *dynamic* prompt content for some non-trivial steps. This is the information the model uses to ground the current STP instruction into low-level actions.

Action Generation prompt instance. Here is the prompt of a single step during the execution of STP:

[⬇](data:text/plain;base64,TW9kZTogQWN0aW9uIEdlbmVyYXRpb24KClNUUCBDb250ZXh0OgoKYGBgCkNyZWF0ZSBhIGxpc3Qgb2Ygb2JqZWN0cyBuYW1lZCB7Y29udGFjdF9saXN0fSwgd2l0aCB0aGUgZm9sbG93aW5nIGl0ZW1zOgogICAgLSBBbiBvYmplY3Qgd2l0aCAibmFtZSIgc2V0IHRvICJIYW5hIEZlcnJlaXJhIiBhbmQgIm51bWJlciIgc2V0IHRvICIrMTA2NjI5MDgzMzkiCiAgICAtIEFuIG9iamVjdCB3aXRoICJuYW1lIiBzZXQgdG8gIlNvcGhpZSBNYXJ0aW4iIGFuZCAibnVtYmVyIiBzZXQgdG8gIisxODcyMzcxMzk0NyIKICAgIC0gQW4gb2JqZWN0IHdpdGggIm5hbWUiIHNldCB0byAiT2xpdmlhIEFsdmVzIiBhbmQgIm51bWJlciIgc2V0IHRvICIrMTYyNzgwMzYxODUiCkl0ZXJhdGUgdGhyb3VnaCBlYWNoIGl0ZW0gaW4ge2NvbnRhY3RfbGlzdH0sIHJlY29yZGVkIGFzIHtjdXJyZW50X2NvbnRhY3R9OgogICAgSW4gdGhlIGBDb250YWN0c2AgYXBwLCBhZGQgYSBuZXcgY29udGFjdCB3aXRoIG5hbWUge2N1cnJlbnRfY29udGFjdC5uYW1lfSBhbmQgcGhvbmUgbnVtYmVyIHtjdXJyZW50X2NvbnRhY3QubnVtYmVyfSwgYW5kIHNhdmUgaXQuICAjIDwtLSBjdXJyZW50IHN0ZXAKICAgIEluIHRoZSBgU2ltcGxlIFNNUyBNZXNzZW5nZXJgIGFwcCwgc2VuZCBhIG1lc3NhZ2UgdG8ge2N1cnJlbnRfY29udGFjdC5udW1iZXJ9IHdpdGggdGhlIGNvbnRlbnQgImhlbGxvLCB7Y3VycmVudF9jb250YWN0Lm5hbWV9Ii4KYGBgCgpDdXJyZW50IExpbmU6IEluIHRoZSBgQ29udGFjdHNgIGFwcCwgYWRkIGEgbmV3IGNvbnRhY3Qgd2l0aCBuYW1lIHtjdXJyZW50X2NvbnRhY3QubmFtZX0gYW5kIHBob25lIG51bWJlciB7Y3VycmVudF9jb250YWN0Lm51bWJlcn0sIGFuZCBzYXZlIGl0LgoKTG93IExldmVsIENvZGUgSGlzdG9yeToKIyBXb3JrZmxvdyBzdGVwOiBJdGVyYXRlIHRocm91Z2ggZWFjaCBpdGVtIGluIHtjb250YWN0X2xpc3R9LCByZWNvcmRlZCBhcyB7Y3VycmVudF9jb250YWN0fToKY29udGFjdF9saXN0X2l0ZXJhdG9yID0gaXRlcihjb250YWN0X2xpc3QpCmN1cnJlbnRfY29udGFjdCA9IG5leHQoY29udGFjdF9saXN0X2l0ZXJhdG9yKQojIFdvcmtmbG93IHN0ZXA6IEluIHRoZSBgQ29udGFjdHNgIGFwcCwgYWRkIGEgbmV3IGNvbnRhY3Qgd2l0aCBuYW1lIHtjdXJyZW50X2NvbnRhY3QubmFtZX0gYW5kIHBob25lIG51bWJlciB7Y3VycmVudF9jb250YWN0Lm51bWJlcn0sIGFuZCBzYXZlIGl0LgoKVmFyaWFibGVzOgpnbG9iYWwgdmFyaWFibGVzOgpsbG06IDxGb3VuZGF0aW9uTW9kZWw+Cm1vYmlsZTogPE1vYmlsZUFQSShjb25maWc9TW9iaWxlQVBJQ29uZmlnKGxvY2F0b3I9J3VpX3RhcnMnLCBkZXZpY2Vfc2VyaWFsX2lkPSdlbXVsYXRvci01NTY0JywgbGxtPTxhZ2VudHByb2cuYWxsX3V0Li4uKT4KY3VycmVudF9zY3JlZW5zaG90OiA8aW1hZ2U+CmNvbnRhY3RfbGlzdCAobGlzdCwgbGVuPTMpOiBbeyduYW1lJzogJ0hhbmEgRmVycmVpcmEnLCAnbnVtYmVyJzogJysxMDY2MjkwODMzOSd9LCB7J25hbWUnOiAnU29waGllIE1hcnRpbicsICdudW1iZXInOiAnKzE4NzIzNzEzOTQ3J30sIHsnbmFtZSc6ICdPbGl2aWEgQWx2ZXMnLCAnbnVtYmVyJzogJysxNjI3ODAzNjE4NSd9XQppc19leGVjX3N1Y2Nlc3M6IFRydWUKY29udGFjdF9saXN0X2l0ZXJhdG9yOiA8bGlzdF9pdGVyYXRvcj4KY3VycmVudF9jb250YWN0IChkaWN0LCBsZW49Mik6IHsnbmFtZSc6ICdTb3BoaWUgTWFydGluJywgJ251bWJlcic6ICcrMTg3MjM3MTM5NDcnfQoKR2xvYmFsIEJlbGllZiBTdGF0ZToKLSBJIGFtIGF0IHRoZSBob21lIHNjcmVlbiBvZiB0aGUgbW9iaWxlIGRldmljZS4KLSBUaGUgYGNvbnRhY3RfbGlzdGAgdmFyaWFibGUgaXMgcG9wdWxhdGVkIHdpdGggdGhyZWUgY29udGFjdHMuCi0gVGhlIHdvcmtmbG93IGhhcyBzdGFydGVkIGl0ZXJhdGluZyB0aHJvdWdoIHRoZSBgY29udGFjdF9saXN0YC4KLSBUaGUgYGN1cnJlbnRfY29udGFjdGAgdmFyaWFibGUgbm93IGhvbGRzIHRoZSBpbmZvcm1hdGlvbiBmb3IgIlNvcGhpZSBNYXJ0aW4iLgotIFRoZSBuZXh0IHN0ZXAgaXMgdG8gb3BlbiB0aGUgYENvbnRhY3RzYCBhcHAgdG8gYWRkICJTb3BoaWUgTWFydGluIiBhcyBhIG5ldyBjb250YWN0Lg==)

1
Mode: Action Generation

2

3
STP Context:

4

5
‘‘‘

6
Create a list of objects named {contact\_list}, with the following items:

7
 - An object with "name" set to "Hana Ferreira" and "number" set to "+10662908339"

8
 - An object with "name" set to "Sophie Martin" and "number" set to "+18723713947"

9
 - An object with "name" set to "Olivia Alves" and "number" set to "+16278036185"

10
Iterate through each item in {contact\_list}, recorded as {current\_contact}:

11
 In the ‘Contacts‘ app, add a new contact with name {current\_contact.name} and phone number {current\_contact.number}, and save it. # <-- current step

12
 In the ‘Simple SMS Messenger‘ app, send a message to {current\_contact.number} with the content "hello, {current\_contact.name}".

13
‘‘‘

14

15
Current Line: In the ‘Contacts‘ app, add a new contact with name {current\_contact.name} and phone number {current\_contact.number}, and save it.

16

17
Low Level Code History:

18
# Workflow step: Iterate through each item in {contact\_list}, recorded as {current\_contact}:

19
contact\_list\_iterator = iter(contact\_list)

20
current\_contact = next(contact\_list\_iterator)

21
# Workflow step: In the ‘Contacts‘ app, add a new contact with name {current\_contact.name} and phone number {current\_contact.number}, and save it.

22

23
Variables:

24
global variables:

25
llm: <FoundationModel>

26
mobile: <MobileAPI(config=MobileAPIConfig(locator=’ui\_tars’, device\_serial\_id=’emulator-5564’, llm=<agentprog.all\_ut...)>

27
current\_screenshot: <image>

28
contact\_list (list, len=3): [{’name’: ’Hana Ferreira’, ’number’: ’+10662908339’}, {’name’: ’Sophie Martin’, ’number’: ’+18723713947’}, {’name’: ’Olivia Alves’, ’number’: ’+16278036185’}]

29
is\_exec\_success: True

30
contact\_list\_iterator: <list\_iterator>

31
current\_contact (dict, len=2): {’name’: ’Sophie Martin’, ’number’: ’+18723713947’}

32

33
Global Belief State:

34
- I am at the home screen of the mobile device.

35
- The ‘contact\_list‘ variable is populated with three contacts.

36
- The workflow has started iterating through the ‘contact\_list‘.

37
- The ‘current\_contact‘ variable now holds the information for "Sophie Martin".

38
- The next step is to open the ‘Contacts‘ app to add "Sophie Martin" as a new contact.

AgentProg tries to output an action to operate the device, and update the belief state:

[⬇](data:text/plain;base64,VXBkYXRlZCBCZWxpZWYgU3RhdGU6Ci0gSSBhbSBpbnNpZGUgdGhlIGBDb250YWN0c2AgYXBwLCB3aGljaCBjdXJyZW50bHkgc2hvd3Mgbm8gY29udGFjdHMuCi0gVGhlIGBjb250YWN0X2xpc3RgIHZhcmlhYmxlIGlzIHBvcHVsYXRlZCB3aXRoIHRocmVlIGNvbnRhY3RzLgotIFRoZSB3b3JrZmxvdyBoYXMgc3RhcnRlZCBpdGVyYXRpbmcgdGhyb3VnaCB0aGUgYGNvbnRhY3RfbGlzdGAuCi0gVGhlIGBjdXJyZW50X2NvbnRhY3RgIHZhcmlhYmxlIG5vdyBob2xkcyB0aGUgaW5mb3JtYXRpb24gZm9yICJTb3BoaWUgTWFydGluIi4KLSBUaGUgYENvbnRhY3RzYCBhcHAgaXMgb3Blbi4gVG8gcHJvY2VlZCwgSSBuZWVkIHRvIGZpbmQgYW5kIGNsaWNrIHRoZSBidXR0b24gdG8gYWRkIGEgbmV3IGNvbnRhY3QuCi0gQSBidXR0b24gdG8gYWRkIGEgbmV3IGNvbnRhY3QsIHBvc3NpYmx5IGxhYmVsZWQgIkNyZWF0ZSBuZXcgY29udGFjdCIgb3IgcmVwcmVzZW50ZWQgYnkgYSAiKyIgaWNvbiwgc2hvdWxkIGJlIHByZXNlbnQgb24gdGhpcyBzY3JlZW4sIGV2ZW4gaWYgaXQncyBub3QgY2xlYXJseSB2aXNpYmxlIGluIHRoZSBjdXJyZW50IGRlc2NyaXB0aW9uLgoKQWN0aW9uOgptb2JpbGUuc3RhcnRfYXBwKGFwcF9uYW1lPSJDb250YWN0cyIpCg==)

1
Updated Belief State:

2
- I am inside the ‘Contacts‘ app, which currently shows no contacts.

3
- The ‘contact\_list‘ variable is populated with three contacts.

4
- The workflow has started iterating through the ‘contact\_list‘.

5
- The ‘current\_contact‘ variable now holds the information for "Sophie Martin".

6
- The ‘Contacts‘ app is open. To proceed, I need to find and click the button to add a new contact.

7
- A button to add a new contact, possibly labeled "Create new contact" or represented by a "+" icon, should be present on this screen, even if it’s not clearly visible in the current description.

8

9
Action:

10
mobile.start\_app(app\_name="Contacts")’

PC Update prompt instance. After Action Generation, AgentProg is about to update the Program Counter:

[⬇](data:text/plain;base64,TW9kZTogUHJvZ3JhbSBDb3VudGVyIFVwZGF0ZQoKU1RQIENvbnRleHQ6CgpgYGAKQ3JlYXRlIGEgbGlzdCBvZiBvYmplY3RzIG5hbWVkIHtjb250YWN0X2xpc3R9LCB3aXRoIHRoZSBmb2xsb3dpbmcgaXRlbXM6CiAgICAtIEFuIG9iamVjdCB3aXRoICJuYW1lIiBzZXQgdG8gIkhhbmEgRmVycmVpcmEiIGFuZCAibnVtYmVyIiBzZXQgdG8gIisxMDY2MjkwODMzOSIKICAgIC0gQW4gb2JqZWN0IHdpdGggIm5hbWUiIHNldCB0byAiU29waGllIE1hcnRpbiIgYW5kICJudW1iZXIiIHNldCB0byAiKzE4NzIzNzEzOTQ3IgogICAgLSBBbiBvYmplY3Qgd2l0aCAibmFtZSIgc2V0IHRvICJPbGl2aWEgQWx2ZXMiIGFuZCAibnVtYmVyIiBzZXQgdG8gIisxNjI3ODAzNjE4NSIKSXRlcmF0ZSB0aHJvdWdoIGVhY2ggaXRlbSBpbiB7Y29udGFjdF9saXN0fSwgcmVjb3JkZWQgYXMge2N1cnJlbnRfY29udGFjdH06CiAgICBJbiB0aGUgYENvbnRhY3RzYCBhcHAsIGFkZCBhIG5ldyBjb250YWN0IHdpdGggbmFtZSB7Y3VycmVudF9jb250YWN0Lm5hbWV9IGFuZCBwaG9uZSBudW1iZXIge2N1cnJlbnRfY29udGFjdC5udW1iZXJ9LCBhbmQgc2F2ZSBpdC4gICMgPC0tIGN1cnJlbnQgc3RlcAogICAgSW4gdGhlIGBTaW1wbGUgU01TIE1lc3NlbmdlcmAgYXBwLCBzZW5kIGEgbWVzc2FnZSB0byB7Y3VycmVudF9jb250YWN0Lm51bWJlcn0gd2l0aCB0aGUgY29udGVudCAiaGVsbG8sIHtjdXJyZW50X2NvbnRhY3QubmFtZX0iLgpgYGAKCkN1cnJlbnQgTGluZTogSW4gdGhlIGBDb250YWN0c2AgYXBwLCBhZGQgYSBuZXcgY29udGFjdCB3aXRoIG5hbWUge2N1cnJlbnRfY29udGFjdC5uYW1lfSBhbmQgcGhvbmUgbnVtYmVyIHtjdXJyZW50X2NvbnRhY3QubnVtYmVyfSwgYW5kIHNhdmUgaXQuCgpMb3cgTGV2ZWwgQ29kZSBIaXN0b3J5OgojIFdvcmtmbG93IHN0ZXA6IEl0ZXJhdGUgdGhyb3VnaCBlYWNoIGl0ZW0gaW4ge2NvbnRhY3RfbGlzdH0sIHJlY29yZGVkIGFzIHtjdXJyZW50X2NvbnRhY3R9OgpjdXJyZW50X2NvbnRhY3QgPSBuZXh0KGNvbnRhY3RfbGlzdF9pdGVyYXRvcikKIyBXb3JrZmxvdyBzdGVwOiBJbiB0aGUgYENvbnRhY3RzYCBhcHAsIGFkZCBhIG5ldyBjb250YWN0IHdpdGggbmFtZSB7Y3VycmVudF9jb250YWN0Lm5hbWV9IGFuZCBwaG9uZSBudW1iZXIge2N1cnJlbnRfY29udGFjdC5udW1iZXJ9LCBhbmQgc2F2ZSBpdC4KbW9iaWxlLnN0YXJ0X2FwcChhcHBfbmFtZT0iQ29udGFjdHMiKQoKVmFyaWFibGVzOgpnbG9iYWwgdmFyaWFibGVzOgpsbG06IDxGb3VuZGF0aW9uTW9kZWw+Cm1vYmlsZTogPE1vYmlsZUFQSShjb25maWc9TW9iaWxlQVBJQ29uZmlnKGxvY2F0b3I9J3VpX3RhcnMnLCBkZXZpY2Vfc2VyaWFsX2lkPSdlbXVsYXRvci01NTY0JywgbGxtPTxhZ2VudHByb2cuYWxsX3V0Li4uKT4KY3VycmVudF9zY3JlZW5zaG90OiA8aW1hZ2U+CmNvbnRhY3RfbGlzdCAobGlzdCwgbGVuPTMpOiBbeyduYW1lJzogJ0hhbmEgRmVycmVpcmEnLCAnbnVtYmVyJzogJysxMDY2MjkwODMzOSd9LCB7J25hbWUnOiAnU29waGllIE1hcnRpbicsICdudW1iZXInOiAnKzE4NzIzNzEzOTQ3J30sIHsnbmFtZSc6ICdPbGl2aWEgQWx2ZXMnLCAnbnVtYmVyJzogJysxNjI3ODAzNjE4NSd9XQppc19leGVjX3N1Y2Nlc3M6IFRydWUKY29udGFjdF9saXN0X2l0ZXJhdG9yOiA8bGlzdF9pdGVyYXRvcj4KY3VycmVudF9jb250YWN0IChkaWN0LCBsZW49Mik6IHsnbmFtZSc6ICdTb3BoaWUgTWFydGluJywgJ251bWJlcic6ICcrMTg3MjM3MTM5NDcnfQoKR2xvYmFsIEJlbGllZiBTdGF0ZToKLSBJIGFtIGluc2lkZSB0aGUgYENvbnRhY3RzYCBhcHAsIHdoaWNoIGN1cnJlbnRseSBzaG93cyBubyBjb250YWN0cy4KLSBUaGUgYGNvbnRhY3RfbGlzdGAgdmFyaWFibGUgaXMgcG9wdWxhdGVkIHdpdGggdGhyZWUgY29udGFjdHMuCi0gVGhlIHdvcmtmbG93IGhhcyBzdGFydGVkIGl0ZXJhdGluZyB0aHJvdWdoIHRoZSBgY29udGFjdF9saXN0YC4KLSBUaGUgYGN1cnJlbnRfY29udGFjdGAgdmFyaWFibGUgbm93IGhvbGRzIHRoZSBpbmZvcm1hdGlvbiBmb3IgIlNvcGhpZSBNYXJ0aW4iLgotIFRoZSBgQ29udGFjdHNgIGFwcCBpcyBvcGVuLiBUbyBwcm9jZWVkLCBJIG5lZWQgdG8gZmluZCBhbmQgY2xpY2sgdGhlIGJ1dHRvbiB0byBhZGQgYSBuZXcgY29udGFjdC4KLSBBIGJ1dHRvbiB0byBhZGQgYSBuZXcgY29udGFjdCwgcG9zc2libHkgbGFiZWxlZCAiQ3JlYXRlIG5ldyBjb250YWN0IiBvciByZXByZXNlbnRlZCBieSBhICIrIiBpY29uLCBzaG91bGQgYmUgcHJlc2VudCBvbiB0aGlzIHNjcmVlbiwgZXZlbiBpZiBpdCdzIG5vdCBjbGVhcmx5IHZpc2libGUgaW4gdGhlIGN1cnJlbnQgZGVzY3JpcHRpb24u)

1
Mode: Program Counter Update

2

3
STP Context:

4

5
‘‘‘

6
Create a list of objects named {contact\_list}, with the following items:

7
 - An object with "name" set to "Hana Ferreira" and "number" set to "+10662908339"

8
 - An object with "name" set to "Sophie Martin" and "number" set to "+18723713947"

9
 - An object with "name" set to "Olivia Alves" and "number" set to "+16278036185"

10
Iterate through each item in {contact\_list}, recorded as {current\_contact}:

11
 In the ‘Contacts‘ app, add a new contact with name {current\_contact.name} and phone number {current\_contact.number}, and save it. # <-- current step

12
 In the ‘Simple SMS Messenger‘ app, send a message to {current\_contact.number} with the content "hello, {current\_contact.name}".

13
‘‘‘

14

15
Current Line: In the ‘Contacts‘ app, add a new contact with name {current\_contact.name} and phone number {current\_contact.number}, and save it.

16

17
Low Level Code History:

18
# Workflow step: Iterate through each item in {contact\_list}, recorded as {current\_contact}:

19
current\_contact = next(contact\_list\_iterator)

20
# Workflow step: In the ‘Contacts‘ app, add a new contact with name {current\_contact.name} and phone number {current\_contact.number}, and save it.

21
mobile.start\_app(app\_name="Contacts")

22

23
Variables:

24
global variables:

25
llm: <FoundationModel>

26
mobile: <MobileAPI(config=MobileAPIConfig(locator=’ui\_tars’, device\_serial\_id=’emulator-5564’, llm=<agentprog.all\_ut...)>

27
current\_screenshot: <image>

28
contact\_list (list, len=3): [{’name’: ’Hana Ferreira’, ’number’: ’+10662908339’}, {’name’: ’Sophie Martin’, ’number’: ’+18723713947’}, {’name’: ’Olivia Alves’, ’number’: ’+16278036185’}]

29
is\_exec\_success: True

30
contact\_list\_iterator: <list\_iterator>

31
current\_contact (dict, len=2): {’name’: ’Sophie Martin’, ’number’: ’+18723713947’}

32

33
Global Belief State:

34
- I am inside the ‘Contacts‘ app, which currently shows no contacts.

35
- The ‘contact\_list‘ variable is populated with three contacts.

36
- The workflow has started iterating through the ‘contact\_list‘.

37
- The ‘current\_contact‘ variable now holds the information for "Sophie Martin".

38
- The ‘Contacts‘ app is open. To proceed, I need to find and click the button to add a new contact.

39
- A button to add a new contact, possibly labeled "Create new contact" or represented by a "+" icon, should be present on this screen, even if it’s not clearly visible in the current description.’

Note that the low-level action histories of adding other contacts are pruned, as the steps are similar across iterations. At each PC Update, AgentProg selects a Program Counter Operation from four options: hold (remain at the current step), continue (jump to the next step), break (exit the loop or jump to the else-branch), or return (exit the current function):

[⬇](data:text/plain;base64,VXBkYXRlZCBCZWxpZWYgU3RhdGU6Ci0gSSBhbSBpbnNpZGUgdGhlIGBDb250YWN0c2AgYXBwLCB3aGljaCBjdXJyZW50bHkgc2hvd3Mgbm8gY29udGFjdHMuCi0gVGhlIGBjb250YWN0X2xpc3RgIHZhcmlhYmxlIGlzIHBvcHVsYXRlZCB3aXRoIHRocmVlIGNvbnRhY3RzLgotIFRoZSB3b3JrZmxvdyBoYXMgc3RhcnRlZCBpdGVyYXRpbmcgdGhyb3VnaCB0aGUgYGNvbnRhY3RfbGlzdGAuCi0gVGhlIGBjdXJyZW50X2NvbnRhY3RgIHZhcmlhYmxlIG5vdyBob2xkcyB0aGUgaW5mb3JtYXRpb24gZm9yICJTb3BoaWUgTWFydGluIi4KLSBUaGUgYENvbnRhY3RzYCBhcHAgaXMgb3Blbi4gVG8gcHJvY2VlZCwgSSBuZWVkIHRvIGZpbmQgYW5kIGNsaWNrIHRoZSBidXR0b24gdG8gYWRkIGEgbmV3IGNvbnRhY3QuCi0gQSBidXR0b24gdG8gYWRkIGEgbmV3IGNvbnRhY3QsIHBvc3NpYmx5IGxhYmVsZWQgIkNyZWF0ZSBuZXcgY29udGFjdCIgb3IgcmVwcmVzZW50ZWQgYnkgYSAiKyIgaWNvbiwgc2hvdWxkIGJlIHByZXNlbnQgb24gdGhpcwpzY3JlZW4sIGV2ZW4gaWYgaXQncyBub3QgY2xlYXJseSB2aXNpYmxlIGluIHRoZSBjdXJyZW50IGRlc2NyaXB0aW9uLgoKQWN0aW9uOgpXb3JrZmxvd1Byb2dyYW1Db3VudGVyT3BlcmF0aW9uLkhPTEQ=)

1
Updated Belief State:

2
- I am inside the ‘Contacts‘ app, which currently shows no contacts.

3
- The ‘contact\_list‘ variable is populated with three contacts.

4
- The workflow has started iterating through the ‘contact\_list‘.

5
- The ‘current\_contact‘ variable now holds the information for "Sophie Martin".

6
- The ‘Contacts‘ app is open. To proceed, I need to find and click the button to add a new contact.

7
- A button to add a new contact, possibly labeled "Create new contact" or represented by a "+" icon, should be present on this

8
screen, even if it’s not clearly visible in the current description.

9

10
Action:

11
WorkflowProgramCounterOperation.HOLD’

PC Update prompt instance for breaking the loop. When all contacts are added, AgentProg tries to get next item from the iterator and receives a StopIteration error. Then, AgentProg will break the loop:

[⬇](data:text/plain;base64,TW9kZTogUHJvZ3JhbSBDb3VudGVyIFVwZGF0ZQoKU1RQIENvbnRleHQ6CgpgYGAKQ3JlYXRlIGEgbGlzdCBvZiBvYmplY3RzIG5hbWVkIHtjb250YWN0X2xpc3R9LCB3aXRoIHRoZSBmb2xsb3dpbmcgaXRlbXM6CiAgICAtIEFuIG9iamVjdCB3aXRoICJuYW1lIiBzZXQgdG8gIkhhbmEgRmVycmVpcmEiIGFuZCAibnVtYmVyIiBzZXQgdG8gIisxMDY2MjkwODMzOSIKICAgIC0gQW4gb2JqZWN0IHdpdGggIm5hbWUiIHNldCB0byAiU29waGllIE1hcnRpbiIgYW5kICJudW1iZXIiIHNldCB0byAiKzE4NzIzNzEzOTQ3IgogICAgLSBBbiBvYmplY3Qgd2l0aCAibmFtZSIgc2V0IHRvICJPbGl2aWEgQWx2ZXMiIGFuZCAibnVtYmVyIiBzZXQgdG8gIisxNjI3ODAzNjE4NSIKSXRlcmF0ZSB0aHJvdWdoIGVhY2ggaXRlbSBpbiB7Y29udGFjdF9saXN0fSwgcmVjb3JkZWQgYXMge2N1cnJlbnRfY29udGFjdH06ICAjIDwtLSBjdXJyZW50IHN0ZXAKICAgIEluIHRoZSBgQ29udGFjdHNgIGFwcCwgYWRkIGEgbmV3IGNvbnRhY3Qgd2l0aCBuYW1lIHtjdXJyZW50X2NvbnRhY3QubmFtZX0gYW5kIHBob25lIG51bWJlciB7Y3VycmVudF9jb250YWN0Lm51bWJlcn0sIGFuZCBzYXZlIGl0LgogICAgSW4gdGhlIGBTaW1wbGUgU01TIE1lc3NlbmdlcmAgYXBwLCBzZW5kIGEgbWVzc2FnZSB0byB7Y3VycmVudF9jb250YWN0Lm51bWJlcn0gd2l0aCB0aGUgY29udGVudCAiaGVsbG8sIHtjdXJyZW50X2NvbnRhY3QubmFtZX0iLgpgYGAKCkN1cnJlbnQgTGluZTogSXRlcmF0ZSB0aHJvdWdoIGVhY2ggaXRlbSBpbiB7Y29udGFjdF9saXN0fSwgcmVjb3JkZWQgYXMge2N1cnJlbnRfY29udGFjdH06CgpMb3cgTGV2ZWwgQ29kZSBIaXN0b3J5OgojIFdvcmtmbG93IHN0ZXA6IEl0ZXJhdGUgdGhyb3VnaCBlYWNoIGl0ZW0gaW4ge2NvbnRhY3RfbGlzdH0sIHJlY29yZGVkIGFzIHtjdXJyZW50X2NvbnRhY3R9OgpjdXJyZW50X2NvbnRhY3QgPSBuZXh0KGNvbnRhY3RfbGlzdF9pdGVyYXRvcikKIyBFeGVjdXRlIFJlc3VsdDogJ1tTdG9wSXRlcmF0aW9uXTogXG4tPiBjdXJyZW50X2NvbnRhY3QgPSBuZXh0KGNvbnRhY3RfbGlzdF9pdGVyYXRvciknCgpWYXJpYWJsZXM6Cmdsb2JhbCB2YXJpYWJsZXM6CmxsbTogPEZvdW5kYXRpb25Nb2RlbD4KbW9iaWxlOiA8TW9iaWxlQVBJKGNvbmZpZz1Nb2JpbGVBUElDb25maWcobG9jYXRvcj0ndWlfdGFycycsIGRldmljZV9zZXJpYWxfaWQ9J2VtdWxhdG9yLTU1NjQnLCBsbG09PGFnZW50cHJvZy5hbGxfdXQuLi4pPgpjdXJyZW50X3NjcmVlbnNob3Q6IDxpbWFnZT4KY29udGFjdF9saXN0X2l0ZXJhdG9yOiA8bGlzdF9pdGVyYXRvcj4KY3VycmVudF9jb250YWN0IChkaWN0LCBsZW49Mik6IHsnbmFtZSc6ICdPbGl2aWEgQWx2ZXMnLCAnbnVtYmVyJzogJysxNjI3ODAzNjE4NSd9CmZpcnN0X25hbWU6ICdPbGl2aWEnCmxhc3RfbmFtZTogJ0FsdmVzJwplcnJvcl9pbmZvOiAnW1N0b3BJdGVyYXRpb25dOiBcbi0+IGN1cnJlbnRfY29udGFjdCA9IG5leHQoY29udGFjdF9saXN0X2l0ZXJhdG9yKScKCkdsb2JhbCBCZWxpZWYgU3RhdGU6Ci0gVGhlIGNvbnRhY3QgIlNvcGhpZSBNYXJ0aW4iIHdpdGggbnVtYmVyICIrMTg3MjM3MTM5NDciIGhhcyBiZWVuIHN1Y2Nlc3NmdWxseSBhZGRlZCBhbmQgbWVzc2FnZWQuCi0gVGhlIGNvbnRhY3QgIk9saXZpYSBBbHZlcyIgd2l0aCBudW1iZXIgIisxNjI3ODAzNjE4NSIgaGFzIGJlZW4gc3VjY2Vzc2Z1bGx5IGNyZWF0ZWQuCi0gQSBtZXNzYWdlICJoZWxsbywgT2xpdmlhIEFsdmVzIiBoYXMgYmVlbiBzZW50IHRvIGhlciwgYW5kIHRoZSBjdXJyZW50IHNjcmVlbiBzaG93cyB0aGUgU01TIGNvbnZlcnNhdGlvbiwgY29uZmlybWluZyB0aGUgY29tcGxldGlvbiBvZiB0aGUgbGFzdCBpdGVyYXRpb24uCi0gQWxsIGNvbnRhY3RzIGluIHRoZSBsaXN0IGhhdmUgbm93IGJlZW4gcHJvY2Vzc2VkLg==)

1
Mode: Program Counter Update

2

3
STP Context:

4

5
‘‘‘

6
Create a list of objects named {contact\_list}, with the following items:

7
 - An object with "name" set to "Hana Ferreira" and "number" set to "+10662908339"

8
 - An object with "name" set to "Sophie Martin" and "number" set to "+18723713947"

9
 - An object with "name" set to "Olivia Alves" and "number" set to "+16278036185"

10
Iterate through each item in {contact\_list}, recorded as {current\_contact}: # <-- current step

11
 In the ‘Contacts‘ app, add a new contact with name {current\_contact.name} and phone number {current\_contact.number}, and save it.

12
 In the ‘Simple SMS Messenger‘ app, send a message to {current\_contact.number} with the content "hello, {current\_contact.name}".

13
‘‘‘

14

15
Current Line: Iterate through each item in {contact\_list}, recorded as {current\_contact}:

16

17
Low Level Code History:

18
# Workflow step: Iterate through each item in {contact\_list}, recorded as {current\_contact}:

19
current\_contact = next(contact\_list\_iterator)

20
# Execute Result: ’[StopIteration]: \n-> current\_contact = next(contact\_list\_iterator)’

21

22
Variables:

23
global variables:

24
llm: <FoundationModel>

25
mobile: <MobileAPI(config=MobileAPIConfig(locator=’ui\_tars’, device\_serial\_id=’emulator-5564’, llm=<agentprog.all\_ut...)>

26
current\_screenshot: <image>

27
contact\_list\_iterator: <list\_iterator>

28
current\_contact (dict, len=2): {’name’: ’Olivia Alves’, ’number’: ’+16278036185’}

29
first\_name: ’Olivia’

30
last\_name: ’Alves’

31
error\_info: ’[StopIteration]: \n-> current\_contact = next(contact\_list\_iterator)’

32

33
Global Belief State:

34
- The contact "Sophie Martin" with number "+18723713947" has been successfully added and messaged.

35
- The contact "Olivia Alves" with number "+16278036185" has been successfully created.

36
- A message "hello, Olivia Alves" has been sent to her, and the current screen shows the SMS conversation, confirming the completion of the last iteration.

37
- All contacts in the list have now been processed.

And AgentProg outputs:

[⬇](data:text/plain;base64,VXBkYXRlZCBCZWxpZWYgU3RhdGU6Ci0gVGhlIGNvbnRhY3QgIlNvcGhpZSBNYXJ0aW4iIHdpdGggbnVtYmVyICIrMTg3MjM3MTM5NDciIGhhcyBiZWVuIHN1Y2Nlc3NmdWxseSBhZGRlZCBhbmQgbWVzc2FnZWQuCi0gVGhlIGNvbnRhY3QgIk9saXZpYSBBbHZlcyIgd2l0aCBudW1iZXIgIisxNjI3ODAzNjE4NSIgaGFzIGJlZW4gc3VjY2Vzc2Z1bGx5IGNyZWF0ZWQuCi0gQSBtZXNzYWdlICJoZWxsbywgT2xpdmlhIEFsdmVzIiBoYXMgYmVlbiBzZW50IHRvIGhlciwgYW5kIHRoZSBjdXJyZW50IHNjcmVlbiBzaG93cyB0aGUgU01TIGNvbnZlcnNhdGlvbiwgY29uZmlybWluZyB0aGUgY29tcGxldGlvbiBvZiB0aGUgbGFzdCBpdGVyYXRpb24uCi0gQWxsIGNvbnRhY3RzIGluIHRoZSBsaXN0IGhhdmUgbm93IGJlZW4gcHJvY2Vzc2VkLCBhbmQgdGhlIGxvb3AgaGFzIGZpbmlzaGVkLgoKQWN0aW9uOgpXb3JrZmxvd1Byb2dyYW1Db3VudGVyT3BlcmF0aW9uLkJSRUFL)

1
Updated Belief State:

2
- The contact "Sophie Martin" with number "+18723713947" has been successfully added and messaged.

3
- The contact "Olivia Alves" with number "+16278036185" has been successfully created.

4
- A message "hello, Olivia Alves" has been sent to her, and the current screen shows the SMS conversation, confirming the completion of the last iteration.

5
- All contacts in the list have now been processed, and the loop has finished.

6

7
Action:

8
WorkflowProgramCounterOperation.BREAK

What is retained and what is pruned. After the first iteration completes, AgentProg does *not* keep every low-level action or screen transition. Instead, the retained state for the next iteration consists mainly of:

1. (1)

   the STP;
2. (2)

   the current PC;
3. (3)

   a pruned low-level code history (completed loop iterations and untaken branches are folded);
4. (4)

   the variables;
5. (5)

   the global belief state.

## Appendix E Prompts

### E.1. STP Generation Prompts

Main Prompt of STP Generation:

[⬇](data:text/plain;base64,e3dvcmtmbG93X3Byb21wdH0KCiMgWW91ciBKb2IKCllvdSBhcmUgYSBwcm9mZXNzaW9uYWwgYXNzaXN0YW50IHRyYWluZWQgdG8gdXNlIHRoZSBUYXNrIFByb2dyYW0gdG8gY29tcGxldGUgZGl2ZXJzZSBhbmQgY29tcGxleCB0YXNrcy4gVGhlIHRhc2tzIGNhbiBiZSByZWxhdGVkIHRvIGRhdGEgY29sbGVjdGlvbi9wcm9jZXNzaW5nLCBicm93c2VyL2RldmljZSB1c2UsIGRhaWx5IHJvdXRpbmUgYXV0b21hdGlvbiwgZXRjLgpZb3Ugc2hvdWxkIGNhcmVmdWxseSB1bmRlcnN0YW5kIHRoZSB1c2VyJ3MgcmVxdWlyZW1lbnQgYmFzZWQgb24gY29udmVyc2F0aW9uLCB0aGVuIHdyaXRlIHByb2Zlc3Npb25hbCB3b3JrZmxvd3MgaW4gVGFzayBQcm9ncmFtIHRoYXQgY2FuIGZ1bGZpbGwgdGhlIHVzZXIncyBuZWVkcy4gWW91IGFyZSBlbmNvdXJhZ2VkIHRvIGRvIHlvdXIgam9iIHByZWNpc2VseSBhbmQgdGhvdWdodGZ1bGx5LCBiZXlvbmQgdGhlIHVzZXIncyBleHBlY3RhdGlvbnMuCgojIFlvdXIgV29yayBQcm9jZWR1cmUKCnlvdXIgZ29hbCBpcyB0byBnZW5lcmF0ZSBhIGhpZ2gtbGV2ZWwgd29ya2Zsb3cgdGhhdCBzdW1tYXJpemVzIHRoZSBzdGVwcyB0byBjb21wbGV0ZSB0aGUgdXNlci1naXZlbiB0YXNrLiBUaGUgd29ya2Zsb3cgc2hvdWxkOgoKMS4gRm9sbG93IHRoZSBzeW50YXggb2YgVGFzayBQcm9ncmFtIChhIG5hdHVyYWwtbGFuZ3VhZ2Utc3R5bGUgZG9tYWluLXNwZWNpZmljIGxhbmd1YWdlIGRlc2lnbmVkIHRvIGRlc2NyaWJlIHdvcmtmbG93cykuCjIuIERlY2lkZSB3aGV0aGVyIGFuZCBob3cgdG8gdXNlIHRoZSBmaWxlcywgZGV2aWNlcyBhbmQgYXBwcyBpbiB0aGUgd29ya3NwYWNlLiBBbnkgbm9uLWV4aXN0aW5nIGZpbGUvZGV2aWNlL2FwcCBpcyBub3QgYWxsb3dlZCBpbiB0aGUgd29ya2Zsb3cuCiAgIFRyeSB0byBtYWtlIHRoZSB3b3JrZmxvdyBnZW5lcmFsaXphYmxlIChpLmUuIGRvZXMgbm90IGludm9sdmUgbG93LWxldmVsIG9wZXJhdGlvbnMgdGhhdCBhcmUgb25seSB2YWxpZCBmb3Igc3BlY2lmaWMgZGF0YSBmb3JtYXRzIG9yIFVJIGRlc2lnbiBwYXR0ZXJucykuCgojIFRoZSBDdXJyZW50IFRhc2sKCnt0YXNrX2Rlc2NyaXB0aW9ufQoKIyBPdXRwdXQgSW5zdHJ1Y3Rpb24KCgpOb3RlOgoxLiBDdXJyZW50IHVzZXIncyBsYW5ndWFnZSBpcyBFbmdsaXNoLiBXaGVuIHdyaXRpbmcgd29ya2Zsb3cvcXVlc3Rpb24vdGFza19uYW1lLCB5b3UgbmVlZCB0byB1c2UgRW5nbGlzaCB0byB3cml0ZS4KMi4gKipEbyBub3QqKiBhc2sgdGhlIHVzZXIgcXVlc3Rpb25zIHdpdGhpbiB0aGUgY29kZS4gVGhlIHVzZXIgcmVxdWlyZXMgdGhlIHRhc2sgdG8gYmUgZnVsbHkgYXV0b21hdGVkIGFuZCB3aWxsIG5vdCBwYXJ0aWNpcGF0ZSBpbiBhbnkgcGFydCBvZiB0aGUgd29ya2Zsb3cuIFRoZXJlZm9yZSwgYXNraW5nIG9yIGluZm9ybWluZyB0aGUgdXNlciBpcyB1bm5lY2Vzc2FyeTsgeW91IHNob3VsZCBjb21wbGV0ZSB0aGUgdGFzayBhdXRvbm9tb3VzbHkuCjMuIFBsZWFzZSBzZXQgdmFyaWFibGUge2Fuc3dlcn0gdG8gYXMgdGhlIGZpbmFsIGFuc3dlciBpZiB0aGUgdGFzayByZXF1aXJlcyB5b3UgdG8gYW5zd2VyIGEgcXVlc3Rpb24uCjQuIE5vdGU6IFlvdSBtdXN0IGRlY2xhcmUgaW4gd2hpY2ggQVBQIHRvIG9wZXJhdGUuIEZvciBleGFtcGxlOiBgSW4gIkNvbnRhY3RzIiBBcHAsIGFkZCBhIG5ldyBjb250YWN0IG5hbWUgJ0FsaWNlJywgYW5kIHNhdmUgaXQuYCBPdGhlcndpc2UsIHRoZSB3b3JrZmxvdyBsYWNrcyBhY2N1cmFjeSwgYW5kIHRoZSBleGVjdXRvciB3aWxsIG5vdCBrbm93IHdoaWNoIEFQUCB5b3UgbmVlZCB0byB1c2UgdG8gY29tcGxldGUgdGhlIHRhc2suCjUuIFRoZSBtb2JpbGUgcGhvbmUgaXMgY29uZmlndXJlZCB2aWEgYSB2aXJ0dWFsIGltYWdlLCBhbmQgaXRzIGRhdGUgYW5kIHRpbWUgZGlmZmVyIGZyb20gdGhlIHJlYWwtd29ybGQgZGF0ZSBhbmQgdGltZSEhIFRoZSBkYXRlIHJlZmVycmVkIHRvIGluIHRoZSBDdXJyZW50IFRhc2sgaXMgYmFzZWQgb24gdGhlICoqZGF0ZSBvbiB0aGUgbW9iaWxlIHBob25lKiosIG5vdCB0aGUgcmVhbC13b3JsZCBkYXRlISBUaGVyZWZvcmUsIHBsZWFzZSBtYWtlIHN1cmUgdG8gZW1waGFzaXplIHVzaW5nIHRoZSBtb2JpbGUgcGhvbmUncyBkYXRlIGFuZCB0aW1lIGZ1bmN0aW9uIHRvIGNoZWNrIHRvZGF5J3MgZGF0ZSBhbmQgdGltZSwgaW5zdGVhZCBvZiBvYnRhaW5pbmcgdGhlIHJlYWwtd29ybGQgZGF0ZSB2aWEgUHl0aG9uJ3MgZGF0ZXRpbWUgbW9kdWxlISBBZnRlciBvYnRhaW5pbmcgInRvZGF5J3MiIGRhdGUgb24gdGhlIG1vYmlsZSBwaG9uZSwgeW91IGNhbiB1c2UgdGhlIGRhdGV0aW1lIG1vZHVsZSB0byBjYWxjdWxhdGUgb3RoZXIgZGF0ZXMgYmFzZWQgb24gdGhlIG1vYmlsZSBwaG9uZSdzICJ0b2RheSIuCgo2LiBSZW1lbWJlciB0byBzYXZlISBZb3UgbXVzdCBlbXBoYXNpemUgaW4gdGhlIHdvcmtmbG93IHRoYXQgZm9yIHRhc2tzIGludm9sdmluZyBlZGl0aW5nIG9yIGNyZWF0aW9uLCBzYXZpbmcgaXMgbWFuZGF0b3J5IGF0IHRoZSBlbmQhCgpOb3csIFJlc3BvbmQgd2l0aCB0aGUgZm9sbG93aW5nIGNvbnRlbnQ6CgpZb3VyIHRob3VnaHQgKHN0YXJ0cyB3aXRoIGAtLS0gVGhvdWdodCAtLS1gKSwgd2hpY2ggY29udGFpbnMgeW91ciB1bmRlcnN0YW5kaW5nIGFib3V0IHRoZSB0YXNrIGFuZCBwbGFuIG9mIGhvdyB0byBkbyB0aGUgdGFzayBpbiBuYXR1cmFsIGxhbmd1YWdlLgoKVGhlIHdvcmtmbG93IChzdGFydHMgd2l0aCBgLS0tIFdvcmtmbG93IC0tLWApLCB3aGljaCBpcyB0aGUgd29ya2Zsb3cgc3RlcHMgaW4gVGFzayBQcm9ncmFtIHN5bnRheCBnZW5lcmF0ZWQgYmFzZWQgb24geW91ciB1bmRlcnN0YW5kaW5nLgoKRXhhbXBsZSBGb3JtYXQ6Ci0tLSBUaG91Z2h0IC0tLSAoVGhpcyBjb250YWlucyB5b3VyIHVuZGVyc3RhbmRpbmcgYWJvdXQgdGhlIHRhc2sgYW5kIHBsYW4gb2YgaG93IHRvIGRvIHRoZSB0YXNrIGluIG5hdHVyYWwgbGFuZ3VhZ2UuKQotLS0gV29ya2Zsb3cgLS0tCmBgYAooV3JpdGUgdGhlIHdvcmtmbG93IHN0ZXBzIGluIFRhc2sgUHJvZ3JhbSBzeW50YXggZ2VuZXJhdGVkIGJhc2VkIG9uIHlvdXIgdW5kZXJzdGFuZGluZy4pCmBgYAoKUGxlYXNlIGJlZ2luIHRvIHdyaXRlIHdvcmtmbG93IQ==)

1
{workflow\_prompt}

2

3
# Your Job

4

5
You are a professional assistant trained to use the Task Program to complete diverse and complex tasks. The tasks can be related to data collection/processing, browser/device use, daily routine automation, etc.

6
You should carefully understand the user’s requirement based on conversation, then write professional workflows in Task Program that can fulfill the user’s needs. You are encouraged to do your job precisely and thoughtfully, beyond the user’s expectations.

7

8
# Your Work Procedure

9

10
your goal is to generate a high-level workflow that summarizes the steps to complete the user-given task. The workflow should:

11

12
1. Follow the syntax of Task Program (a natural-language-style domain-specific language designed to describe workflows).

13
2. Decide whether and how to use the files, devices and apps in the workspace. Any non-existing file/device/app is not allowed in the workflow.

14
 Try to make the workflow generalizable (i.e. does not involve low-level operations that are only valid for specific data formats or UI design patterns).

15

16
# The Current Task

17

18
{task\_description}

19

20
# Output Instruction

21

22

23
Note:

24
1. Current user’s language is English. When writing workflow/question/task\_name, you need to use English to write.

25
2. \*\*Do not\*\* ask the user questions within the code. The user requires the task to be fully automated and will not participate in any part of the workflow. Therefore, asking or informing the user is unnecessary; you should complete the task autonomously.

26
3. Please set variable {answer} to as the final answer if the task requires you to answer a question.

27
4. Note: You must declare in which APP to operate. For example: ‘In "Contacts" App, add a new contact name ’Alice’, and save it.‘ Otherwise, the workflow lacks accuracy, and the executor will not know which APP you need to use to complete the task.

28
5. The mobile phone is configured via a virtual image, and its date and time differ from the real-world date and time!! The date referred to in the Current Task is based on the \*\*date on the mobile phone\*\*, not the real-world date! Therefore, please make sure to emphasize using the mobile phone’s date and time function to check today’s date and time, instead of obtaining the real-world date via Python’s datetime module! After obtaining "today’s" date on the mobile phone, you can use the datetime module to calculate other dates based on the mobile phone’s "today".

29

30
6. Remember to save! You must emphasize in the workflow that for tasks involving editing or creation, saving is mandatory at the end!

31

32
Now, Respond with the following content:

33

34
Your thought (starts with ‘--- Thought ---‘), which contains your understanding about the task and plan of how to do the task in natural language.

35

36
The workflow (starts with ‘--- Workflow ---‘), which is the workflow steps in Task Program syntax generated based on your understanding.

37

38
Example Format:

39
--- Thought --- (This contains your understanding about the task and plan of how to do the task in natural language.)

40
--- Workflow ---

41
‘‘‘

42
(Write the workflow steps in Task Program syntax generated based on your understanding.)

43
‘‘‘

44

45
Please begin to write workflow!"

Introduction prompt to STP, i.e., {workflow\_prompt}:

[⬇](data:text/plain;base64,SSB3aWxsIGludHJvZHVjZSB5b3UgdG8gYSBuZXcgcHJvZ3JhbW1pbmcgbGFuZ3VhZ2UgY2FsbGVkICoqVGFzayBQcm9ncmFtKiouIFRoaXMgaXMgYSBuYXR1cmFsIGxhbmd1YWdlIHN0eWxlIGRvbWFpbi1zcGVjaWZpYyBsYW5ndWFnZSAoRFNMKSB1c2VkIHRvIGRlc2NyaWJlIHRhc2sgZXhlY3V0aW9uIGZsb3dzLiBZb3UgbmVlZCB0byBtYXN0ZXIgdGhpcyBsYW5ndWFnZSBhbmQgY29tcGxldGUgdGhlIHRhc2tzIEkgYXJyYW5nZS4KCiMgVGFzayBQcm9ncmFtIExhbmd1YWdlIFN5bnRheAoKIyMgMS4gQmFzaWMgU3ludGF4IGFuZCBDb25jZXB0cwoKVGhlIHN5bnRheCBvZiBUYXNrIFByb2dyYW0gaXMgc2ltaWxhciB0byBuYXR1cmFsIGxhbmd1YWdlLCBidXQgZm9sbG93aW5nIGNlcnRhaW4gc3RydWN0dXJlcyBhbmQgY29uY2VwdHMgd2lsbCBoZWxwIHRoZSBzeXN0ZW0gdW5kZXJzdGFuZCB5b3VyIGludGVudCBtb3JlIHByZWNpc2VseS4KCkEgVGFzayBQcm9ncmFtIGNvbnNpc3RzIG9mIGEgc2VyaWVzIG9mIHN0YXRlbWVudHMsIHVzdWFsbHkgb25lIHBlciBsaW5lLCBkZXNjcmliaW5nIGFuIG9wZXJhdGlvbiBvciBhIHN0ZXAsIHVzaW5nIGltcGVyYXRpdmUgc2VudGVuY2VzIG9yIGNsZWFyIGRlY2xhcmF0aXZlIHNlbnRlbmNlcy4KCiMjIyBDb21tZW50cwoKU3RhcnQgYSBsaW5lIHdpdGggdGhlIGAjYCBzeW1ib2wgdG8gaW5kaWNhdGUgdGhhdCB0aGUgbGluZSBpcyBhIGNvbW1lbnQuIENvbW1lbnRzIGFyZSB1c2VkIHRvIGV4cGxhaW4gY29kZSwgYW5kIHRoZSBzeXN0ZW0gd2lsbCBpZ25vcmUgdGhlbSBkdXJpbmcgZXhlY3V0aW9uLgoKYGBgCiMgVGhpcyBpcyBhIGNvbW1lbnQsIHRoZSBzeXN0ZW0gd2lsbCBub3QgZXhlY3V0ZSB0aGlzIHNlbnRlbmNlClRlbGwgdXNlciAiSGVsbG8sIGNvbW1lbnRzIG1ha2UgY29kZSBlYXNpZXIgdG8gdW5kZXJzdGFuZCIgIyBUaGlzIGlzIGFsc28gYW4gaW5saW5lIGNvbW1lbnQKYGBgCgojIyMgVmFyaWFibGVzCgpJbiBUYXNrIFByb2dyYW0sIHZhcmlhYmxlcyBhcmUgcmVwcmVzZW50ZWQgYnkgd29yZHMgd3JhcHBlZCBpbiBjdXJseSBicmFjZXMuCgoqICAgKipEZWNsYXJpbmcgKFJlY29yZGluZykgVmFyaWFibGVzKio6IFVzdWFsbHkgZG9uZSB1c2luZyBgcmVjb3JkIGFzIHt2YXJpYWJsZV9uYW1lfWAgb3Igc2ltaWxhciBuYXR1cmFsIGxhbmd1YWdlIHBocmFzaW5nLgoKICAgIGBgYAogICAgU2V0IHZhcmlhYmxlIHt1c2VyX25hbWV9IHRvICJKb2huIgogICAgU2V0IHtjdXJyZW50X2NpdHl9IHRvICJCZWlqaW5nIgogICAgQ3JlYXRlIHZhcmlhYmxlIHt2aXNpdG9yX2NvdW50fSwgaW5pdGlhbCB2YWx1ZSBpcyAwCiAgICBgYGAKKiAgICoqVXNpbmcgVmFyaWFibGVzKio6IFdoZXJlIHN0b3JlZCBpbmZvcm1hdGlvbiBpcyBuZWVkZWQsIHVzZSBge3ZhcmlhYmxlX25hbWV9YCB0byByZXByZXNlbnQgZmlsbGluZyBpbiB0aGUgcG9zaXRpb24gd2l0aCB0aGUgdmFyaWFibGUncyB2YWx1ZS4KCiAgICBgYGAKICAgIFRlbGwgdXNlciAiSGVsbG8sIHt1c2VyX25hbWV9IgogICAgU2VhcmNoIGluIGJyb3dzZXIgZm9yICJ7Y3VycmVudF9jaXR5fSBwb3B1bGF0aW9uIiwgcmVjb3JkIGFzIHtwb3B1bGF0aW9uX2NvdW50fQogICAgVGVsbCB1c2VyICJUaGUgcG9wdWxhdGlvbiBvZiB7Y3VycmVudF9jaXR5fSBpcyB7cG9wdWxhdGlvbl9jb3VudH0uIgogICAgYGBgCiogICBWYXJpYWJsZSBuYW1lcyBzaG91bGQgdXNlIG1lYW5pbmdmdWwgd29yZHMgdG8gZmFjaWxpdGF0ZSB1bmRlcnN0YW5kaW5nLgoKIyMjIERhdGEgVHlwZXMKCldoZW4gdmFyaWFibGVzIGFyZSBzdG9yZWQgYW5kIHBhc3NlZCBpbiB0aGUgc3lzdGVtLCB0aGV5IGFyZSB1bmRlcnN0b29kIGFzIGRpZmZlcmVudCB0eXBlcyBvZiBkYXRhIGZvciBhY3R1YWwgb3BlcmF0aW9ucy4gRGlmZmVyZW50IHR5cGVzIG9mIHZhcmlhYmxlcyBhcmUgdXNlZCBmb3IgZGF0YSBwcm9jZXNzaW5nIGluIGRpZmZlcmVudCBzY2VuYXJpb3MsIHN1Y2ggYXMgbnVtYmVyIHR5cGVzIGZvciBzdGF0aXN0aWNzLCB0ZXh0IHR5cGVzIGZvciBkb2N1bWVudCBvcGVyYXRpb25zLCBkaWFsb2d1ZSwgZXRjLgoKSW4gVGFzayBQcm9ncmFtLCB5b3UgZG8gbm90IG5lZWQgdG8gc3BlY2lmaWNhbGx5IGNhcmUgYWJvdXQgdmFyaWFibGUgdHlwZXM7IFRhc2sgUHJvZ3JhbSB3aWxsIGF1dG9tYXRpY2FsbHkgdW5kZXJzdGFuZCB0aGUgdHlwZSBvZiBlYWNoIHZhcmlhYmxlIGJhc2VkIG9uIHlvdXIgY29kZS4gT2YgY291cnNlLCB5b3UgY2FuIGFsc28gc3VwcGxlbWVudCB0aGUgdHlwZSBkZXNjcmlwdGlvbiB3aGVuIGRlZmluaW5nIHZhcmlhYmxlcyB0byBoYXZlIG1vcmUgY29udHJvbCBvdmVyIHRoZSBlbnRpcmUgcHJvY2Vzcy4KCiMjIyMgQmFzaWMgRGF0YSBUeXBlcwoKVGFzayBQcm9ncmFtIGN1cnJlbnRseSBzdXBwb3J0cyB0aGUgZm9sbG93aW5nIGJhc2ljIGRhdGEgdHlwZXM6CgoqICAgKipUZXh0Kio6IEEgc2VxdWVuY2Ugb2YgY2hhcmFjdGVycyBlbmNsb3NlZCBpbiBxdW90ZXMsIHN1Y2ggYXMgYCJIZWxsbyB3b3JsZCEiYCBvciBgJ0hlbGxvLCBXb3JsZCEnYC4KKiAgICoqTnVtYmVyKio6IEludGVnZXJzIG9yIGRlY2ltYWxzLCBzdWNoIGFzIGAxMGAgb3IgYDMuMTRgLgoqICAgKipCb29sZWFuKio6IGBUcnVlYCBvciBgRmFsc2VgIChvciBgWWVzYCAvIGBOb2ApLCB1c2VkIHRvIHJlcHJlc2VudCBjb25kaXRpb25zIG9yIHN0YXRlcy4KCiAgICBgYGAKICAgIEp1ZGdlIGlmIHthZ2V9IGlzIGdyZWF0ZXIgdGhhbiAxOCwgcmVjb3JkIGFzIHtpc19hZHVsdH0gIyB7aXNfYWR1bHR9IHdpbGwgYmUgVHJ1ZSBvciBGYWxzZQogICAgSWYge2lzX2FkdWx0fSBpcyB0cnVlOgogICAgICAgIFRlbGwgdXNlciAiWW91IGFyZSBhbiBhZHVsdC4iCiAgICBgYGAKKiAgICoqSW1hZ2UqKjogUmVwcmVzZW50cyBpbWFnZSBkYXRhLiBDYW4gYmUgb2J0YWluZWQgYnkgcmVhZGluZyBmaWxlcywgZXRjLgoKICAgIGBgYAogICAgUmVhZCBpbWFnZSBmaWxlICJsb2dvLnBuZyIsIHJlY29yZCBhcyB7Y29tcGFueV9sb2dvfQogICAgVGVsbCB1c2VyICJUaGlzIGlzIHRoZSBjb21wYW55IExvZ286IgogICAgU2VuZCB7Y29tcGFueV9sb2dvfSB0byB1c2VyCiAgICBgYGAKCiMjIyMgT2JqZWN0cwoKQW4gT2JqZWN0IGlzIGEgY29sbGVjdGlvbiBjb250YWluaW5nIG11bHRpcGxlICoqcHJvcGVydGllcyoqLCB1c2VkIHRvIHJlcHJlc2VudCBhIHNwZWNpZmljIHRoaW5nIG9yIGVudGl0eS4gRWFjaCBwcm9wZXJ0eSBoYXMgYSBuYW1lIGFuZCBhIGNvcnJlc3BvbmRpbmcgdmFsdWUgKGFsc28ga25vd24gYXMga2V5LXZhbHVlIHBhaXJzKS4gVGhlIHZhbHVlIG9mIGEgcHJvcGVydHkgY2FuIGJlIGEgYmFzaWMgdHlwZSB2YXJpYWJsZSBvciBhbm90aGVyIG9iamVjdC4KCiogICAqKkNyZWF0aW5nIE9iamVjdHMqKjoKCiAgICBgYGAKICAgIENyZWF0ZSBhbiBvYmplY3QgbmFtZWQge215X2Nhcn0KICAgIFNldCB7Y29sb3J9IG9mIHtteV9jYXJ9IHRvICJSZWQiCiAgICBTZXQge2JyYW5kfSBvZiB7bXlfY2FyfSB0byAiVGVzbGEiCiAgICBTZXQge21vZGVsfSBvZiB7bXlfY2FyfSB0byAiTW9kZWwgWSIKCiAgICAjIE9yIGEgbW9yZSBjb25jaXNlIHdheSwgQUkgd2lsbCB1bmRlcnN0YW5kIHlvdXIgaW50ZW50CiAgICBDcmVhdGUgYW4gb2JqZWN0IHtjbGllbnR9LCB3aXRoIGF0dHJpYnV0ZXMgaW5jbHVkaW5nOiAibmFtZSIgaXMgIkxpIE1pbmciLCAiYWdlIiBpcyAyNCwgImNpdHkiIGlzICJTaGFuZ2hhaSIKICAgIGBgYAoqICAgKipBY2Nlc3NpbmcgT2JqZWN0IFByb3BlcnRpZXMqKjoKICAgIFlvdSBjYW4gYWNjZXNzIHByb3BlcnR5IHZhbHVlcyBkaXJlY3RseSB1c2luZyBuYXR1cmFsIGxhbmd1YWdlIGluc2lkZSBjdXJseSBicmFjZXMsIG9yIHVzZSB0aGUgZG90IGAuYCBvcGVyYXRvciBjbG9zZXIgdG8gdHJhZGl0aW9uYWwgcHJvZ3JhbW1pbmcuCgogICAgYGBgCiAgICBUZWxsIHVzZXIgIk15IGNhciBjb2xvciBpcyB7Y29sb3Igb2YgbXlfY2FyfSIKICAgIElmIHthZ2Ugb2YgY2xpZW50fSBpcyBncmVhdGVyIHRoYW4gMTg6ICMgQXNzdW1pbmcge2NsaWVudH0gaXMgYW4gb2JqZWN0IGRlZmluZWQgZWFybGllcgogICAgICAgIFRlbGwgdXNlciAie25hbWUgb2YgY2xpZW50fSBpcyBhbiBhZHVsdC4iCgogICAgIyBPciB1c2luZyB0aGUge3ZhcmlhYmxlLnByb3BlcnR5fSBmb3JtYXQKICAgIFRlbGwgdXNlciAiTXkgY2FyIGNvbG9yIGlzOiB7bXlfY2FyLmNvbG9yfSwgYnJhbmQgaXMge215X2Nhci5icmFuZH0sIG1vZGVsIGlzIHtteV9jYXIubW9kZWx9IgogICAgYGBgCgojIyMjIExpc3RzCgpBIExpc3QgaXMgYW4gb3JkZXJlZCBzZXJpZXMgb2YgYmFzaWMgdHlwZSBlbGVtZW50cyBvciBvYmplY3RzLgoKYGBgCiMgQ3JlYXRlIGxpc3QKUmVjb3JkIGxpc3QgWyJBcHBsZSIsICJCYW5hbmEiLCAiT3JhbmdlIl0gYXMge2ZydWl0X2xpc3R9CkNvdW50IHdoaWNoIHB1YmxpYyBBSSBjb21wYW5pZXMgZXhpc3QgY3VycmVudGx5LCBvdXRwdXQgY29tcGFueSBuYW1lIGxpc3QsIHJlY29yZCBhcyB7Y29tcGFueV9saXN0fSAjIHtjb21wYW55X2xpc3R9IGlzIGEgdGV4dCBsaXN0CgojIEFjY2VzcyBsaXN0IGVsZW1lbnRzIChBSSB3aWxsIGludGVsbGlnZW50bHkgdW5kZXJzdGFuZCkKR2V0IHRoZSBmaXJzdCBpdGVtIG9mIHtmcnVpdF9saXN0fSwgcmVjb3JkIGFzIHtmcnVpdF8xfQpUZWxsIHVzZXIgIk15IGZhdm9yaXRlIGZydWl0IGlzOiB7ZnJ1aXRfMX0iCkdldCB0aGUgcXVhbnRpdHkgb2YgZWxlbWVudHMgaW4ge2NvbXBhbnlfbGlzdH0sIHJlY29yZCBhcyB7Y29tcGFueV9jb3VudH0KVGVsbCB1c2VyICJUaGVyZSBhcmUgYXBwcm94aW1hdGVseSB7Y29tcGFueV9jb3VudH0gcHVibGljIEFJIGNvbXBhbmllcy4iCmBgYAoKIyMjIyBEYXRhIFRhYmxlcwoKRGF0YSBUYWJsZXMgYXJlIHNpbWlsYXIgdG8gc3ByZWFkc2hlZXRzLCBjb250YWluaW5nIHJvd3MgYW5kIGNvbHVtbnMuICoqQSBEYXRhIFRhYmxlIGNhbiBiZSB2aWV3ZWQgYXMgYSBsaXN0IGNvbXBvc2VkIG9mIG11bHRpcGxlIG9iamVjdHMgd2l0aCB0aGUgc2FtZSBzdHJ1Y3R1cmUuKiogRWFjaCByb3cgaW4gdGhlIHRhYmxlIGNvcnJlc3BvbmRzIHRvIGFuIG9iamVjdCwgYW5kIGVhY2ggY29sdW1uIGNvcnJlc3BvbmRzIHRvIGEgcHJvcGVydHkgb2YgdGhlIG9iamVjdC4gWW91IGNhbiBjcmVhdGUgZGF0YSB0YWJsZXMsIGFkZCwgZGVsZXRlLCBtb2RpZnkgZGF0YSBpbiB0YWJsZXMsIGltcG9ydC9leHBvcnQgdGFibGVzIGZyb20vdG8gZmlsZXMsIGV0Yy4KCmBgYAojIENyZWF0ZSBkYXRhIHRhYmxlCkVzdGFibGlzaCBhbiBlbXB0eSBkYXRhIHRhYmxlIGNvbnRhaW5pbmcgY29sdW1ucyAiTmFtZSIsICJEZXBhcnRtZW50IiwgIklEIiwgcmVjb3JkIGFzIHtlbXBsb3llZV9pbmZvX3RhYmxlfQoKIyBBZGQgYSByb3cgKENhbiBiZSB1bmRlcnN0b29kIGFzIGFkZGluZyBhbiBvYmplY3QgbWF0Y2hpbmcgdGhlIHN0cnVjdHVyZSkKQ3JlYXRlIGFuIG9iamVjdCB7bmV3X2VtcGxveWVlX0F9LCBjb250YWluaW5nIGF0dHJpYnV0ZXMgIk5hbWUiIGlzICJaaGFuZyBTYW4iLCAiRGVwYXJ0bWVudCIgaXMgIlRlY2giLCAiSUQiIGlzICJUMDAxIgpBZGQge25ld19lbXBsb3llZV9BfSBhcyBhIG5ldyByb3cgdG8ge2VtcGxveWVlX2luZm9fdGFibGV9CgojIEFkZCBhIHJvdyBvZiBjb250ZW50IChNb3JlIGNvbmNpc2Ugd2F5KQpBZGQgYSByb3cgb2YgZGF0YSB7Ik5hbWUiOiAiWGlhbyBNaW5nIiwgIkRlcGFydG1lbnQiOiAiTWFya2V0aW5nIiwgIklEIjogIk0wMjMifSB0byB7ZW1wbG95ZWVfaW5mb190YWJsZX0KCiMgTG9hZCBkYXRhIGZyb20gZmlsZSB0byB0YWJsZQpSZWFkIGNvbnRlbnQgb2YgdGFibGUgZmlsZSAiZXh0ZXJuYWxfZW1wbG95ZWVzLnhsc3giLCBzdG9yZSBpbnRvIG5ldyBkYXRhIHRhYmxlIHtleHRlcm5hbF9lbXBsb3llZV90YWJsZX0KCiMgU2F2ZSBkYXRhIHRhYmxlIHRvIGZpbGUKU2F2ZSB7ZW1wbG95ZWVfaW5mb190YWJsZX0gdG8gZmlsZSwgZmlsZW5hbWUgaXMgImVtcGxveWVlcy54bHN4IgpgYGAKCiMjIyMgRGF0YSBQcm9jZXNzaW5nCgpUYXNrIFByb2dyYW0gaW50ZWdyYXRlcyBBSSBsYXJnZSBtb2RlbCBjYXBhYmlsaXRpZXMuIFlvdSBvbmx5IG5lZWQgdG8gZGVzY3JpYmUgeW91ciBwcm9jZXNzaW5nIHJlcXVpcmVtZW50cyB0byBjb21wbGV0ZSB2YXJpb3VzIGNvbXBsZXggZGF0YSBwcm9jZXNzaW5nIG9wZXJhdGlvbnMuCgoqICAgKipGaWx0ZXIqKjoKICAgIGBgYAogICAgRmlsdGVyIG91dCBhbGwgY29tcGFueSByZWNvcmRzIHdpdGggIk1hcmtldCBDYXAiIChVbml0OiBCaWxsaW9uKSBncmVhdGVyIHRoYW4gMTAwIGZyb20ge2NvbXBhbnlfZGF0YV90YWJsZX0sIHJlY29yZCByZXN1bHQgYXMge2xhcmdlX2NvbXBhbmllc190YWJsZX0KICAgIGBgYAoqICAgKipFeHRyYWN0Kio6CiAgICBgYGAKICAgIEdldCAiQ291bnRyeSIgY29sdW1uIGZyb20ge2NvbXBhbnlfZGF0YV90YWJsZX0sIGFmdGVyIGRlZHVwbGljYXRpb24gcmVjb3JkIGFzIHtjb3VudHJ5X25hbWVfbGlzdH0KICAgIGBgYAoqICAgKipTdW1tYXJpemUqKjoKICAgIGBgYAogICAgQ2FsY3VsYXRlIHRoZSBzdW0gb2YgIk1hcmtldCBDYXAiIGZvciBhbGwgY29tcGFuaWVzIGluIHtjb21wYW55X2RhdGFfdGFibGV9IHdoZXJlICJDb3VudHJ5IiBhdHRyaWJ1dGUgaXMgIkNoaW5hIiwgcmVjb3JkIGFzIHtjaGluYV9jb21wYW5pZXNfdG90YWxfY2FwfQogICAgYGBgCiogICAqKlNvcnQqKjoKICAgIGBgYAogICAgU29ydCB7Y29tcGFueV9kYXRhX3RhYmxlfSBieSAiTWFya2V0IENhcCIgY29sdW1uIHZhbHVlcyBmcm9tIGxhcmdlc3QgdG8gc21hbGxlc3QKICAgIGBgYAoqICAgKipNZXJnZSoqOgogICAgYGBgCiAgICBNZXJnZSB7ZG9tZXN0aWNfc2FsZXNfdGFibGV9IGFuZCB7b3ZlcnNlYXNfc2FsZXNfdGFibGV9IGJ5ICJQcm9kdWN0IElEIiBjb2x1bW4sIHJlY29yZCBhcyB7Z2xvYmFsX3NhbGVzX3RvdGFsX3RhYmxlfQogICAgYGBgCiogICAqKkNhbGN1bGF0ZSoqOgogICAgYGBgCiAgICBEaXZpZGUgIk1hcmtldCBDYXAiIGJ5ICJFbXBsb3llZSBDb3VudCIgaW4ge2NvbXBhbnlfZGF0YV90YWJsZX0sIGFkZCBhcyAiUGVyIENhcGl0YSBNYXJrZXQgQ2FwIiBjb2x1bW4KICAgIGBgYAoKIyMjIEZsb3cgQ29udHJvbAoKQ29kZSBpcyBleGVjdXRlZCBzZXF1ZW50aWFsbHkgbGluZSBieSBsaW5lIGJ5IGRlZmF1bHQsIGJ1dCB5b3UgY2FuIGNoYW5nZSB0aGUgZXhlY3V0aW9uIGZsb3cgdmlhIGZsb3cgY29udHJvbCBzeW50YXguCgojIyMjIExvb3BzCgpXaGVuIHRoZSBzYW1lIG9wZXJhdGlvbiBuZWVkcyB0byBiZSByZXBlYXRlZCBmb3IgZWFjaCBpdGVtIGluIGEgZ3JvdXAsIHVzZSBhIGxvb3AuCgpBIGxvb3AgY29uc2lzdHMgb2YgYSBsb29wIGNvbmRpdGlvbiBhbmQgbG9vcCBjb250ZW50LiBUaGUgbG9vcCBjb25kaXRpb24gZGVzY3JpYmVzIHRoZSBtZXRob2QgYW5kIG51bWJlciBvZiB0aW1lcywgYW5kIHRoZSBsb29wIGNvbnRlbnQgaXMgdGhlIHN0ZXBzIHRvIGJlIHJlcGVhdGVkIGluIGVhY2ggcm91bmQuCgpUaGUgY29kZSBmb3IgbG9vcCBjb250ZW50IHVzdWFsbHkgbmVlZHMgaW5kZW50YXRpb24gKGxlYXZpbmcgc29tZSBzcGFjZXMgcmVsYXRpdmUgdG8gdGhlIGxvb3AgY29uZGl0aW9uIGF0IHRoZSBzdGFydCBvZiBlYWNoIGxpbmUsIHVzdWFsbHkgNCBzcGFjZXMpIHRvIGluZGljYXRlIHRoZXNlIG9wZXJhdGlvbnMgYXJlIHBhcnQgb2YgdGhlIGxvb3AuIFRoZSBUYXNrIFByb2dyYW0gQUkgaW50ZXJwcmV0ZXIgaGFzIHNvbWUgdG9sZXJhbmNlIGZvciBpbmRlbnRhdGlvbiwgYnV0IGdvb2QgaW5kZW50YXRpb24gaGVscHMgcmVhZGFiaWxpdHkgYW5kIGFjY3VyYWN5LgoKYGBgCiMgSXRlcmF0ZSB0aHJvdWdoIGV2ZXJ5IHtzaW5nbGVfaXRlbV92YXJpYWJsZX0gaW4ge2RhdGFfY29sbGVjdGlvbn0KUmVjb3JkIGxpc3QgeyJBcHBsZSBQaWUiLCAiQmFuYW5hIEJvYXQiLCAiT3JhbmdlIEp1aWNlIn0gYXMge2Rlc3NlcnRfbWVudX0KSXRlcmF0ZSB0aHJvdWdoIGV2ZXJ5IGRlc3NlcnQgaW4ge2Rlc3NlcnRfbWVudX0sIHJlY29yZCBhcyB7Y3VycmVudF9kZXNzZXJ0fQogICAgVGVsbCB1c2VyICJXZSBhcmUgc2VsbGluZzoge2N1cnJlbnRfZGVzc2VydH0iCmBgYAoKIyMjIyBDb25kaXRpb25hbCBCcmFuY2hpbmcKCldoZW4gdGhlIHByb2dyYW0gbmVlZHMgdG8gcGVyZm9ybSBkaWZmZXJlbnQgb3BlcmF0aW9ucyBiYXNlZCBvbiBkaWZmZXJlbnQgc2l0dWF0aW9ucywgdXNlIGNvbmRpdGlvbmFsIGJyYW5jaGluZy4KCkluIGNvbmRpdGlvbmFsIGJyYW5jaGluZywgdGhlIHByb2dyYW0gZGVjaWRlcyB3aGljaCBicmFuY2ggdG8gZXhlY3V0ZSBiYXNlZCBvbiB0aGUganVkZ21lbnQgb2YgYSBjb25kaXRpb24gZXhwcmVzc2lvbi4KCkEgY29uZGl0aW9uIGV4cHJlc3Npb24gaXMgZ2VuZXJhbGx5IGEganVkZ21lbnQsIHN1Y2ggYXMgYHttYXJrZXRfY2FwfSBsZXNzIHRoYW4gMTAgYmlsbGlvbmAsIGB7aG9zcGl0YWxfbGlzdH0gaXMgZW1wdHlgLCBldGMuLCBvciBhIHZhcmlhYmxlIGNvbnRhaW5pbmcgYSBib29sZWFuIHZhbHVlLgoKKiAgICoqQmFzaWMgRm9ybWF0Kio6CgogICAgYGBgCiAgICBJZiB7Y29uZGl0aW9uXzF9OgogICAgICAgIC4uLiAoRXhlY3V0ZSB3aGVuIGNvbmRpdGlvbiAxIGlzIG1ldCkKICAgIE90aGVyd2lzZSBpZiB7Y29uZGl0aW9uXzJ9OiAgICAjIE9wdGlvbmFsCiAgICAgICAgLi4uIChFeGVjdXRlIHdoZW4gY29uZGl0aW9uIDEgaXMgbm90IG1ldCBidXQgY29uZGl0aW9uIDIgaXMgbWV0KQogICAgT3RoZXJ3aXNlOiAgICAgICAgICAgICAgIyBPcHRpb25hbAogICAgICAgIC4uLiAoRXhlY3V0ZSB3aGVuIG5laXRoZXIgY29uZGl0aW9uIDEgbm9yIDIgaXMgbWV0KQogICAgYGBgCgoqICAgKipFeGFtcGxlczoqKgoKICAgIGBgYAogICAgIyBFeGFtcGxlIDEKICAgIElmIHt1c2VyX2FnZX0gaXMgbGVzcyB0aGFuIDE4OgogICAgICAgIFRlbGwgdXNlciAiWW91IGFyZSBhIG1pbm9yLiIKICAgIE90aGVyd2lzZSBpZiB7dXNlcl9hZ2V9IGlzIGdyZWF0ZXIgdGhhbiBvciBlcXVhbCB0byAxOCBhbmQge3VzZXJfYWdlfSBpcyBsZXNzIHRoYW4gNjA6CiAgICAgICAgVGVsbCB1c2VyICJZb3UgYXJlIGFuIGFkdWx0LiIKICAgIE90aGVyd2lzZToKICAgICAgICBUZWxsIHVzZXIgIllvdSBoYXZlIGVudGVyZWQgb2xkIGFnZS4iCgogICAgIyBFeGFtcGxlIDIKICAgIFF1ZXJ5ICJIb3cgaXMgdGhlIHdlYXRoZXIgdG9kYXk/Iiwgb3V0cHV0IHdlYXRoZXIgZGVzY3JpcHRpb24sIHJlY29yZCBhcyB7d2VhdGhlcl9zaXR1YXRpb259CiAgICBJZiB7d2VhdGhlcl9zaXR1YXRpb259IGNvbnRhaW5zICJSYWluIjoKICAgICAgICBUZWxsIHVzZXIgIlBsZWFzZSByZW1lbWJlciB0byBicmluZyBhbiB1bWJyZWxsYSB3aGVuIGdvaW5nIG91dC4iCiAgICBPdGhlcndpc2U6CiAgICAgICAgVGVsbCB1c2VyICJUaGUgd2VhdGhlciBpcyBuaWNlIHRvZGF5ISIKICAgIGBgYAoKIyMjIFRhc2sgRGVjb21wb3NpdGlvbiAoRnVuY3Rpb25zKQoKSW4gVGFzayBQcm9ncmFtLCB5b3UgY2FuIGRlZmluZSBhIHNldCBvZiBjb21tb25seSB1c2VkIG9wZXJhdGlvbnMgYXMgYSAiVGFzayIsIHdoaWNoIGlzIHNpbWlsYXIgdG8gIkZ1bmN0aW9ucyIgb3IgIlN1YnJvdXRpbmVzIiBpbiB0cmFkaXRpb25hbCBwcm9ncmFtbWluZyBsYW5ndWFnZXMuIFRoaXMgbWFrZXMgeW91ciBtYWluIGZsb3cgbW9yZSBjb25jaXNlIGFuZCBmYWNpbGl0YXRlcyBjb2RlIHJldXNlLgoKKiAgICoqRGVmaW5pbmcgVGFza3MqKjoKICAgIFN0YXJ0IHdpdGggYERlZmluZSBhIHRhc2sgbmFtZWQgInt0YXNrX25hbWV9ImAuIFRhc2tzIGNhbiBoYXZlIGlucHV0IHBhcmFtZXRlcnMgYW5kIG91dHB1dHMgKHJldHVybiB2YWx1ZXMpLgoKICAgIGBgYAogICAgIyBEZWZpbmUgYSB0YXNrIHRvIGdyZWV0IGEgc3BlY2lmaWMgdXNlcgogICAgRGVmaW5lIGEgdGFzayBuYW1lZCAiQ3VzdG9tIEdyZWV0aW5nIgogICAgICAgIFRhc2sgaW5wdXQ6IHt1c2VyX25hbWV9IChUeXBlOiBUZXh0KQogICAgICAgIFJlY29yZCAiSGVsbG8sIHt1c2VyX25hbWV9ISBXZWxjb21lIHRvIFRhc2sgUHJvZ3JhbS4iIGFzIHtncmVldGluZ190ZXh0fQogICAgICAgIFRlbGwgdXNlciB7Z3JlZXRpbmdfdGV4dH0KICAgICAgICAjIFRoaXMgdGFzayBoYXMgbm8gZXhwbGljaXQgcmV0dXJuIHZhbHVlCgogICAgIyBEZWZpbmUgYSB0YXNrIHRvIGNhbGN1bGF0ZSBzdW0gb2YgdHdvIG51bWJlcnMgYW5kIHJldHVybiByZXN1bHQKICAgIERlZmluZSBhIHRhc2sgbmFtZWQgIkNhbGN1bGF0ZSBTdW0gb2YgVHdvIE51bWJlcnMiCiAgICAgICAgVGFzayBpbnB1dDoge251bWJlcl9vbmV9IChOdW1iZXIgdHlwZSkgYW5kIHtudW1iZXJfdHdvfSAoTnVtYmVyIHR5cGUpCiAgICAgICAgUmVjb3JkIHJlc3VsdCBvZiB7bnVtYmVyX29uZX0gcGx1cyB7bnVtYmVyX3R3b30gYXMge2NhbGN1bGF0aW9uX3Jlc3VsdH0KICAgICAgICBUYXNrIHJldHVybnMge2NhbGN1bGF0aW9uX3Jlc3VsdH0gIyBUYXNrIGVuZHMsIGFuZCBvdXRwdXRzIHtjYWxjdWxhdGlvbl9yZXN1bHR9CiAgICBgYGAKCiAgICBUaGUgZmlyc3QgbGluZSBvZiB0aGUgdGFzayBkZWZpbml0aW9uIG9yIHRoZSBsaW5lcyBpbW1lZGlhdGVseSBmb2xsb3dpbmcgYXJlIHVzdWFsbHkgdXNlZCB0byBkZXNjcmliZSB0aGUgcmVxdWlyZWQgaW5wdXQgcGFyYW1ldGVycyBhbmQgdGhlaXIgdHlwZXMgKG9wdGlvbmFsLCBidXQgcmVjb21tZW5kZWQpLgoqICAgKipDYWxsaW5nIFRhc2tzKio6CiAgICBVc2UgYEV4ZWN1dGUgdGFzayAie3Rhc2tfbmFtZX0iYCwgcHJvdmlkZSBuZWNlc3NhcnkgaW5wdXQgcGFyYW1ldGVycywgYW5kIChvcHRpb25hbGx5KSByZWNlaXZlIG91dHB1dCByZXN1bHRzLgoKICAgIGBgYAogICAgIyBDYWxsIGdyZWV0aW5nIHRhc2sKICAgIEV4ZWN1dGUgdGFzayAiQ3VzdG9tIEdyZWV0aW5nIiwge3VzZXJfbmFtZX0gaXMgIlpoYW5nIFNhbiIKCiAgICAjIENhbGwgY2FsY3VsYXRpb24gdGFzayBhbmQgZ2V0IG91dHB1dAogICAgRXhlY3V0ZSB0YXNrICJDYWxjdWxhdGUgU3VtIG9mIFR3byBOdW1iZXJzIiwge251bWJlcl9vbmV9IGlzIDEwLCB7bnVtYmVyX3R3b30gaXMgMjUsIG91dHB1dCByZXN1bHQgcmVjb3JkIGFzIHt0b3RhbH0KICAgIFRlbGwgdXNlciAiUmVzdWx0IG9mIDEwICsgMjUgaXM6IHt0b3RhbH0iCiAgICBgYGAKCiAgICBUaGUgVGFzayBQcm9ncmFtIGludGVycHJldGVyIHdpbGwgaW50ZWxsaWdlbnRseSBtYXRjaCBpbnB1dCBwYXJhbWV0ZXIgbmFtZXMuIElmIHBhcmFtZXRlciBuYW1lcyBpbiB0aGUgZGVmaW5pdGlvbiBhbmQgdGhlIGNhbGwgYXJlIG5vdCBleGFjdGx5IHRoZSBzYW1lIGJ1dCBoYXZlIHNpbWlsYXIgbWVhbmluZ3MsIHRoZSBpbnRlcnByZXRlciB3aWxsIGFsc28gYXR0ZW1wdCB0byB1bmRlcnN0YW5kLgoKVXNpbmcgZnVuY3Rpb25zICh0YXNrcyksIHlvdSBjYW4gZGVjb21wb3NlIGEgY29tcGxleCBsYXJnZSB0YXNrIGludG8gYSBzZXJpZXMgb2Ygc21hbGxlciwgZWFzaWVyLXRvLW1hbmFnZSBhbmQgZGVzY3JpYmUgc3ViLXRhc2tzLCBhbmQgdGhlbiBjb21wbGV0ZSB0aGVtIG9uZSBieSBvbmUuClRoaXMgYWJpbGl0eSB0byBkZWNvbXBvc2UgdGFza3MgaXMgZXNzZW50aWFsbHkgdGhlIGFiaWxpdHkgb2YgYXJjaGl0ZWN0dXJlIGFuZCBsb2dpYywgcmVxdWlyaW5nIGNhcmVmdWwgZGVzaWduLCB1c2luZyB2YXJpYWJsZXMgdG8gcGFzcyBpbmZvcm1hdGlvbiBhdCBkaWZmZXJlbnQgc3RhZ2VzIG9mIHRoZSBmbG93LCB3aGlsZSBlbnN1cmluZyB0aGUgb3ZlcmFsbCBzdHJ1Y3R1cmUgb2YgdGhlIHByb2dyYW0gaXMgY29uY2lzZSBhbmQgcmVhZGFibGUuCgojIyAyLiBVc2luZyBUb29scwoKTWFueSBjb21wbGV4IGZ1bmN0aW9ucyByZWx5IG9uIHBvd2VyZnVsIHRvb2xzIHRvIGltcGxlbWVudC4gVGhlIGV4YW1wbGVzIGludHJvZHVjZWQgYWJvdmUgaGF2ZSBhY3R1YWxseSBpbnZvbHZlZCBzb21lLiBUaGlzIGNoYXB0ZXIgd2lsbCBpbnRyb2R1Y2UgdGhlbSBpbiBkZXRhaWwuCgojIyMgT3BlcmF0aW5nIEZpbGVzCgpUYXNrIFByb2dyYW0gc3VwcG9ydHMgcmVhZGluZyBhbmQgc2F2aW5nIGZpbGVzLCBpbmNsdWRpbmcgaW1hZ2VzLCBkb2N1bWVudHMsIHRhYmxlcywgZXRjLiBGaWxlbmFtZXMgYXJlIHJlY29tbWVuZGVkIHRvIGJlIHdyYXBwZWQgaW4gcXVvdGVzOyBmaWxlbmFtZXMgYXJlIHJlbGF0aXZlIHRvIHRoZSBmaWxlIHBhdGggaW4gdGhlIGN1cnJlbnQgSURFIHdvcmtzcGFjZS4KCmBgYApTYXZlIHRleHQgY29udGVudCAiVGhpcyBpcyB0aGUgZmlyc3QgbGluZSB3cml0dGVuLlxcblRoaXMgaXMgdGhlIHNlY29uZCBsaW5lLiIgdG8gZG9jdW1lbnQgIk15IE5vdGVzIgpSZWFkIGFsbCB0ZXh0IGNvbnRlbnQgb2YgZG9jdW1lbnQgIk15IE5vdGVzIiwgcmVjb3JkIGFzIHtub3RlX2NvbnRlbnR9ClRlbGwgdXNlciAiTm90ZSBjb250ZW50IGlzOlxcbntub3RlX2NvbnRlbnR9IgoKU2F2ZSB7Y29tcGFueV9tYXJrZXRfY2FwX3RhYmxlfSBhcyB0YWJsZSBmaWxlICJjb21wYW55X21hcmtldF9jYXBfcmVwb3J0IgpSZWFkIGRhdGEgaW4gdGFibGUgZmlsZSAiY29tcGFueV9tYXJrZXRfY2FwX3JlcG9ydCIsIHJlY29yZCBhcyB7bWFya2V0X2NhcF90YWJsZX0KCkNoZWNrIGlmIGZpbGUgInRoZXNpc19kcmFmdCIgZXhpc3RzCklmIGZpbGUgZXhpc3RzOgogICAgUmVhZCBjb250ZW50IG9mIGZpbGUgInRoZXNpc19kcmFmdCIsIHJlY29yZCBhcyB7dGhlc2lzX2RyYWZ0fQpPdGhlcndpc2U6CiAgICBUZWxsIHVzZXIgIkRvY3VtZW50IGRvZXMgbm90IGV4aXN0LiIKYGBgCgpUYXNrIFByb2dyYW0gd2lsbCBpbnRlbGxpZ2VudGx5IGhhbmRsZSBmaWxlIHJlYWQvd3JpdGUgZm9ybWF0cyBiYXNlZCBvbiBmaWxlIHN1ZmZpeGVzIGFuZCB5b3VyIGRlc2NyaXB0aW9uLgoKIyMgMy4gVGFzayBQcm9ncmFtIFdyaXRpbmcgUHJpbmNpcGxlcwoKMS4gICoqUmVhZGFiaWxpdHkqKjogUHJvZ3JhbSBzdGF0ZW1lbnRzIHNob3VsZCBiZSBjb25jaXNlIGFuZCBzbW9vdGgsIGVhc3kgZm9yIG9yZGluYXJ5IHVzZXJzIHRvIHVuZGVyc3RhbmQgYW5kIG1vZGlmeS4KMi4gICoqRmVhc2liaWxpdHkqKjogVGhlIHByb2dyYW0gc2hvdWxkIGZpdCB0aGUgdXNlcidzIGRldmljZSBhbmQgc29mdHdhcmUgZW52aXJvbm1lbnQsIGVuc3VyaW5nIGl0IGNhbiBiZSBleGVjdXRlZCBjb3JyZWN0bHkuCjMuICAqKkdlbmVyYWxpdHkqKjogRG8gbm90IG1ha2UgYW55IGFzc3VtcHRpb25zIGFib3V0IHRoaW5ncyB5b3UgZG9uJ3Qga25vdy4gQXNzdW1wdGlvbnMgd2lsbCBkZWZpbml0ZWx5IG1pc3MgaW1wb3J0YW50IHRoaW5ncy4gWW91IHNob3VsZCB1c2UgdGhlIGdlbmVyYWxpdHkgb2YgVGFzayBQcm9ncmFtJ3MgbmF0dXJhbCBsYW5ndWFnZSB0byBnZW5lcmFsaXplIGFsbCBwb3NzaWJsZSBzaXR1YXRpb25zLiBHZW5lcmFsIGxhbmd1YWdlIGlzIHN0aWxsIHVuZGVyc3RhbmRhYmxlIHRvIFRhc2sgUHJvZ3JhbS4gRm9yIGV4YW1wbGUsICJDYWxjdWxhdGUgeHh4IiBpcyBiZXR0ZXIgdGhhbiAiSWYgb3BlcmF0aW9uIGlzIGFkZGl0aW9uLCBjYWxjdWxhdGUgYStiOyBpZiBvcGVyYXRpb24gaXMgc3VidHJhY3Rpb24sIGNhbGN1bGF0ZSBhLWIiLCBiZWNhdXNlIHRoZSBmb3JtZXIgaXMgbW9yZSBnZW5lcmFsLgoKIyMgNC4gUHJhY3RpY2FsIENhc2VzCgpUaGUgZm9sbG93aW5nIGFyZSByZXByZXNlbnRhdGl2ZSBleGFtcGxlcyBzaG93Y2FzaW5nIHRoZSBjYXBhYmlsaXRpZXMgb2YgdGhlIFRhc2sgUHJvZ3JhbSBsYW5ndWFnZSBpbiBkaWZmZXJlbnQgc2NlbmFyaW9zLgoKIyMjIENhc2UgMTogQ2FsY3VsYXRlIGF2ZXJhZ2Ugc2NvcmVzIGFuZCBncmFkZXMgZm9yIHN0dWRlbnRzIGJhc2VkIG9uIHRoZWlyIHN1YmplY3Qgc2NvcmVzIGluIHRoZSBzdHVkZW50cy5jc3YgdGFibGUgKDkwIGFuZCBhYm92ZSBmb3IgQSwgODAtODkgZm9yIEIsIDcwLTc5IGZvciBDLCA2MC02OSBmb3IgRCwgYmVsb3cgNjAgZm9yIEYpLCBhbmQgc2F2ZSB0aGUgcmVzdWx0cyBhcyBzdHVkZW50X2dyYWRlcy5jc3YKCmBgYAojIFJlYWQgc3R1ZGVudCBncmFkZSB0YWJsZQpSZWFkIHRoZSBjb250ZW50IG9mIHRhYmxlIGZpbGUgInN0dWRlbnRzLmNzdiIgYW5kIHN0b3JlIGl0IGluIGEgZGF0YSB0YWJsZSwgcmVjb3JkZWQgYXMge3N0dWRlbnRfZ3JhZGVzX3RhYmxlfQoKIyBBbmFseXplIHN1YmplY3QgbmFtZXMgKGF1dG9tYXRpY2FsbHkgaWRlbnRpZnkgc2NvcmUtcmVsYXRlZCBjb2x1bW5zKQpBbmFseXplIHRoZSBzdWJqZWN0IG5hbWVzIGluIHtzdHVkZW50X2dyYWRlc190YWJsZX0sIHJlY29yZGVkIGFzIHtzdWJqZWN0X2xpc3R9CgojIEFkZCBuZXcgY29sdW1ucyBmb3IgcmVzdWx0cwpBZGQgYSBuZXcgY29sdW1uICJhdmVyYWdlX3Njb3JlIiB0byB7c3R1ZGVudF9ncmFkZXNfdGFibGV9CkFkZCBhIG5ldyBjb2x1bW4gImdyYWRlIiB0byB7c3R1ZGVudF9ncmFkZXNfdGFibGV9CgojIEl0ZXJhdGUgdGhyb3VnaCBlYWNoIHJvdyB0byBjYWxjdWxhdGUgYXZlcmFnZSBzY29yZSBhbmQgZ3JhZGUKSXRlcmF0ZSB0aHJvdWdoIGVhY2ggcm93IGluIHtzdHVkZW50X2dyYWRlc190YWJsZX0sIHJlY29yZGVkIGFzIHtjdXJyZW50X3N0dWRlbnR9OgogICAgIyBDb2xsZWN0IGFsbCBzY29yZXMgZm9yIGN1cnJlbnQgc3R1ZGVudAogICAgQ3JlYXRlIGFuIGVtcHR5IGxpc3QsIHJlY29yZGVkIGFzIHtjdXJyZW50X3N0dWRlbnRfc2NvcmVzX2xpc3R9CiAgICBJdGVyYXRlIHRocm91Z2ggZWFjaCBzdWJqZWN0IG5hbWUgaW4ge3N1YmplY3RfbGlzdH0sIHJlY29yZGVkIGFzIHtzdWJqZWN0X25hbWV9OgogICAgICAgIEdldCB0aGUgdmFsdWUgb2Yge3N1YmplY3RfbmFtZX0gY29sdW1uIGZyb20ge2N1cnJlbnRfc3R1ZGVudH0sIHJlY29yZGVkIGFzIHtjdXJyZW50X3Njb3JlfQogICAgICAgIEFkZCB7Y3VycmVudF9zY29yZX0gdG8ge2N1cnJlbnRfc3R1ZGVudF9zY29yZXNfbGlzdH0KCiAgICAjIENhbGN1bGF0ZSBhdmVyYWdlIHNjb3JlCiAgICBDYWxjdWxhdGUgdGhlIGF2ZXJhZ2Ugb2YgYWxsIHZhbHVlcyBpbiB7Y3VycmVudF9zdHVkZW50X3Njb3Jlc19saXN0fSwgcmVjb3JkZWQgYXMge2F2ZXJhZ2Vfc2NvcmV9CgogICAgIyBEZXRlcm1pbmUgZ3JhZGUgYmFzZWQgb24gYXZlcmFnZSBzY29yZQogICAgQ2FsY3VsYXRlIHtncmFkZX0gZnJvbSB7YXZlcmFnZV9zY29yZX0sIDkwIGFuZCBhYm92ZSBmb3IgQSwgODAtODkgZm9yIEIsIDcwLTc5IGZvciBDLCA2MC02OSBmb3IgRCwgYmVsb3cgNjAgZm9yIEYKCiAgICAjIFN0b3JlIGNhbGN1bGF0aW9uIHJlc3VsdHMgaW4gY3VycmVudCByb3cKICAgIFNldCB0aGUgdmFsdWUgb2YgImF2ZXJhZ2Vfc2NvcmUiIGNvbHVtbiBpbiB7Y3VycmVudF9zdHVkZW50fSB0byB7YXZlcmFnZV9zY29yZX0KICAgIFNldCB0aGUgdmFsdWUgb2YgImdyYWRlIiBjb2x1bW4gaW4ge2N1cnJlbnRfc3R1ZGVudH0gdG8ge2dyYWRlfQoKIyBTYXZlIHJlc3VsdHMgdG8gbmV3IGZpbGUKU2F2ZSB7c3R1ZGVudF9ncmFkZXNfdGFibGV9IGFzIHRhYmxlIGZpbGUgInN0dWRlbnRfZ3JhZGVzLmNzdiIKCiMgRGlzcGxheSBwcm9jZXNzaW5nIHJlc3VsdCBzdW1tYXJ5CkdldCB0aGUgbnVtYmVyIG9mIHJvd3MgaW4ge3N0dWRlbnRfZ3JhZGVzX3RhYmxlfSwgcmVjb3JkZWQgYXMge3RvdGFsX3N0dWRlbnRzfQpHZXQgdGhlIGxlbmd0aCBvZiB7c3ViamVjdF9saXN0fSwgcmVjb3JkZWQgYXMge3RvdGFsX3N1YmplY3RzfQpQcmludCAiR3JhZGUgcHJvY2Vzc2luZyBjb21wbGV0ZWQhIFByb2Nlc3NlZCB7dG90YWxfc3ViamVjdHN9IHN1YmplY3Qgc2NvcmVzIGZvciB7dG90YWxfc3R1ZGVudHN9IHN0dWRlbnRzLCByZXN1bHRzIHNhdmVkIGFzIHN0dWRlbnRfZ3JhZGVzLmNzdiIKYGBgCgojIyMgQ2FzZSAyOiBDb25zb2xpZGF0aW5nIENvbnRhY3RzIGZyb20gdGFibGUxLmNzdiwgdGFibGUyLmNzdiwgYW5kIHRhYmxlMy5jc3YgaW50byBPbmUgVGFibGUsIHNhdmUgYXMgImNvbnRhY3Rfc3VtbWFyeS5jc3YiCgpgYGAKIyBSZWFkIHRocmVlIGNvbnRhY3QgdGFibGUgZmlsZXMKUmVhZCB0aGUgY29udGVudCBvZiB0YWJsZSBmaWxlICJ0YWJsZTEuY3N2IiBhbmQgc3RvcmUgaXQgaW4gYSBkYXRhIHRhYmxlLCByZWNvcmRlZCBhcyB7Y29udGFjdHNfdGFibGUxfQpSZWFkIHRoZSBjb250ZW50IG9mIHRhYmxlIGZpbGUgInRhYmxlMi5jc3YiIGFuZCBzdG9yZSBpdCBpbiBhIGRhdGEgdGFibGUsIHJlY29yZGVkIGFzIHtjb250YWN0c190YWJsZTJ9ClJlYWQgdGhlIGNvbnRlbnQgb2YgdGFibGUgZmlsZSAidGFibGUzLmNzdiIgYW5kIHN0b3JlIGl0IGluIGEgZGF0YSB0YWJsZSwgcmVjb3JkZWQgYXMge2NvbnRhY3RzX3RhYmxlM30KCiMgQ3JlYXRlIGVtcHR5IHN1bW1hcnkgdGFibGUKQ3JlYXRlIGFuIGVtcHR5IGRhdGEgdGFibGUsIHJlY29yZGVkIGFzIHtjb250YWN0c19zdW1tYXJ5X3RhYmxlfQoKIyBHZXQgY29sdW1uIHN0cnVjdHVyZSBmcm9tIGZpcnN0IHRhYmxlIGFzIGJhc2Ugc3RydWN0dXJlIGZvciBzdW1tYXJ5IHRhYmxlCkdldCBhbGwgY29sdW1uIG5hbWVzIGZyb20ge2NvbnRhY3RzX3RhYmxlMX0sIHJlY29yZGVkIGFzIHtjb2x1bW5fbmFtZXNfbGlzdH0KSXRlcmF0ZSB0aHJvdWdoIGVhY2ggY29sdW1uIG5hbWUgaW4ge2NvbHVtbl9uYW1lc19saXN0fSwgcmVjb3JkZWQgYXMge2N1cnJlbnRfY29sdW1uX25hbWV9OgogICAgQWRkIG5ldyBjb2x1bW4ge2N1cnJlbnRfY29sdW1uX25hbWV9IHRvIHtjb250YWN0c19zdW1tYXJ5X3RhYmxlfQoKIyBBZGQgZGF0YSBmcm9tIHRhYmxlMSB0byBzdW1tYXJ5IHRhYmxlCkl0ZXJhdGUgdGhyb3VnaCBlYWNoIHJvdyBpbiB7Y29udGFjdHNfdGFibGUxfSwgcmVjb3JkZWQgYXMge2N1cnJlbnRfY29udGFjdH06CiAgICBBZGQge2N1cnJlbnRfY29udGFjdH0gYXMgYSBuZXcgcm93IHRvIHtjb250YWN0c19zdW1tYXJ5X3RhYmxlfQoKIyBBZGQgZGF0YSBmcm9tIHRhYmxlMiB0byBzdW1tYXJ5IHRhYmxlCkl0ZXJhdGUgdGhyb3VnaCBlYWNoIHJvdyBpbiB7Y29udGFjdHNfdGFibGUyfSwgcmVjb3JkZWQgYXMge2N1cnJlbnRfY29udGFjdH06CiAgICBBZGQge2N1cnJlbnRfY29udGFjdH0gYXMgYSBuZXcgcm93IHRvIHtjb250YWN0c19zdW1tYXJ5X3RhYmxlfQoKIyBBZGQgZGF0YSBmcm9tIHRhYmxlMyB0byBzdW1tYXJ5IHRhYmxlCkl0ZXJhdGUgdGhyb3VnaCBlYWNoIHJvdyBpbiB7Y29udGFjdHNfdGFibGUzfSwgcmVjb3JkZWQgYXMge2N1cnJlbnRfY29udGFjdH06CiAgICBBZGQge2N1cnJlbnRfY29udGFjdH0gYXMgYSBuZXcgcm93IHRvIHtjb250YWN0c19zdW1tYXJ5X3RhYmxlfQoKIyBSZW1vdmUgZHVwbGljYXRlIGNvbnRhY3QgcmVjb3JkcyAoYmFzZWQgb24gbmFtZSBhbmQgcGhvbmUgbnVtYmVyKQpSZW1vdmUgZHVwbGljYXRlIHJvd3MgZnJvbSB7Y29udGFjdHNfc3VtbWFyeV90YWJsZX0gYmFzZWQgb24gIm5hbWUiIGFuZCAicGhvbmUiIGNvbHVtbnMsIGtlZXBpbmcgdGhlIGZpcnN0IG9jY3VycmVuY2UKCiMgU29ydCBieSBuYW1lClNvcnQge2NvbnRhY3RzX3N1bW1hcnlfdGFibGV9IGJ5ICJuYW1lIiBjb2x1bW4gdmFsdWVzIGZyb20gQSB0byBaCgojIFNhdmUgc3VtbWFyeSByZXN1bHRzClNhdmUge2NvbnRhY3RzX3N1bW1hcnlfdGFibGV9IGFzIHRhYmxlIGZpbGUgImNvbnRhY3RzX3N1bW1hcnkuY3N2IgoKIyBDb3VudCBzdW1tYXJ5IGluZm9ybWF0aW9uCkdldCB0aGUgbnVtYmVyIG9mIHJvd3MgaW4ge2NvbnRhY3RzX3N1bW1hcnlfdGFibGV9LCByZWNvcmRlZCBhcyB7dG90YWxfY29udGFjdHN9ClByaW50ICJDb250YWN0IGNvbnNvbGlkYXRpb24gY29tcGxldGVkISBPcmdhbml6ZWQge3RvdGFsX2NvbnRhY3RzfSBjb250YWN0cyBpbiB0b3RhbCwgc2F2ZWQgYXMgY29udGFjdHNfc3VtbWFyeS5jc3YiCmBgYAoKIyMjIENhc2UgMzogQ2FsY3VsYXRlIEZpcnN0IE4gVGVybXMgb2YgRmlib25hY2NpIFNlcXVlbmNlIGFuZCBTYXZlIHRvIEZpbGUKCmBgYAojIENyZWF0ZSBkYXRhIHRhYmxlIHRvIHN0b3JlIHJlc3VsdHMKQ3JlYXRlIGFuIGVtcHR5IGRhdGEgdGFibGUgd2l0aCAic2VxdWVuY2VfbnVtYmVyIiBhbmQgImZpYm9uYWNjaV92YWx1ZSIgY29sdW1ucywgcmVjb3JkZWQgYXMge2ZpYm9uYWNjaV90YWJsZX0KCiMgSW5pdGlhbGl6ZSBmaXJzdCB0d28gdGVybXMKSWYge3Rlcm1zX059IGlzIGdyZWF0ZXIgdGhhbiBvciBlcXVhbCB0byAxOgogICAgQWRkIGEgcm93IG9mIGRhdGEgeyJzZXF1ZW5jZV9udW1iZXIiOiAxLCAiZmlib25hY2NpX3ZhbHVlIjogMH0gdG8ge2ZpYm9uYWNjaV90YWJsZX0KICAgIFJlY29yZCAwIGFzIHtwcmV2aW91c19wcmV2aW91c190ZXJtfQoKSWYge3Rlcm1zX059IGlzIGdyZWF0ZXIgdGhhbiBvciBlcXVhbCB0byAyOgogICAgQWRkIGEgcm93IG9mIGRhdGEgeyJzZXF1ZW5jZV9udW1iZXIiOiAyLCAiZmlib25hY2NpX3ZhbHVlIjogMX0gdG8ge2ZpYm9uYWNjaV90YWJsZX0KICAgIFJlY29yZCAxIGFzIHtwcmV2aW91c190ZXJtfQoKIyBDYWxjdWxhdGUgdGVybXMgMyB0byBOCklmIHt0ZXJtc19OfSBpcyBncmVhdGVyIHRoYW4gMjoKICAgIFJlY29yZCAzIGFzIHtjdXJyZW50X3NlcXVlbmNlX251bWJlcn0KICAgIFJlcGVhdCB1bnRpbCB7Y3VycmVudF9zZXF1ZW5jZV9udW1iZXJ9IGlzIGdyZWF0ZXIgdGhhbiB7dGVybXNfTn06CiAgICAgICAgIyBDYWxjdWxhdGUgY3VycmVudCB0ZXJtIHZhbHVlCiAgICAgICAgQ2FsY3VsYXRlIHRoZSByZXN1bHQgb2Yge3ByZXZpb3VzX3ByZXZpb3VzX3Rlcm19ICsge3ByZXZpb3VzX3Rlcm19LCByZWNvcmRlZCBhcyB7Y3VycmVudF90ZXJtfQoKICAgICAgICAjIEFkZCByZXN1bHQgdG8gdGFibGUKICAgICAgICBBZGQgYSByb3cgb2YgZGF0YSB7InNlcXVlbmNlX251bWJlciI6IHtjdXJyZW50X3NlcXVlbmNlX251bWJlcn0sICJmaWJvbmFjY2lfdmFsdWUiOiB7Y3VycmVudF90ZXJtfX0gdG8ge2ZpYm9uYWNjaV90YWJsZX0KCiAgICAgICAgIyBVcGRhdGUgcHJldmlvdXMgdHdvIHRlcm1zIGZvciBuZXh0IGNhbGN1bGF0aW9uCiAgICAgICAgUmVjb3JkIHtwcmV2aW91c190ZXJtfSBhcyB7cHJldmlvdXNfcHJldmlvdXNfdGVybX0KICAgICAgICBSZWNvcmQge2N1cnJlbnRfdGVybX0gYXMge3ByZXZpb3VzX3Rlcm19CgogICAgICAgICMgSW5jcmVtZW50IHNlcXVlbmNlIG51bWJlcgogICAgICAgIENhbGN1bGF0ZSB0aGUgcmVzdWx0IG9mIHtjdXJyZW50X3NlcXVlbmNlX251bWJlcn0gKyAxLCByZWNvcmRlZCBhcyB7Y3VycmVudF9zZXF1ZW5jZV9udW1iZXJ9CgojIFNhdmUgcmVzdWx0cyB0byBmaWxlClNhdmUge2ZpYm9uYWNjaV90YWJsZX0gYXMgdGFibGUgZmlsZSAiZmlib25hY2NpLmNzdiIKCiMgRGlzcGxheSBjYWxjdWxhdGlvbiByZXN1bHQgc3VtbWFyeQpHZXQgdGhlICJmaWJvbmFjY2lfdmFsdWUiIGZyb20gdGhlIGxhc3Qgcm93IG9mIHtmaWJvbmFjY2lfdGFibGV9LCByZWNvcmRlZCBhcyB7bGFzdF90ZXJtX3ZhbHVlfQpUZWxsIHVzZXIgIkNhbGN1bGF0aW9uIGNvbXBsZXRlZCEgVGhlIHt0ZXJtc19OfXRoIHRlcm0gb2YgRmlib25hY2NpIHNlcXVlbmNlIGlzOiB7bGFzdF90ZXJtX3ZhbHVlfSIKVGVsbCB1c2VyICJDb21wbGV0ZSByZXN1bHRzIGhhdmUgYmVlbiBzYXZlZCB0byBmaWJvbmFjY2kuY3N2IGZpbGUiCgpgYGAKCiMjIyBDYXNlIDQ6IEJhdGNoIFByb2Nlc3NpbmcgU3R1ZGVudCBHcmFkZSBEYXRhIGFuZCBHZW5lcmF0aW5nIEluZGl2aWR1YWwgR3JhZGUgUmVwb3J0cywgc3ViamVjdHMgaW5jbHVkZSAiTWF0aCIsICJDaGluZXNlIiwgIkVuZ2xpc2giCgpgYGAKIyBEZWZpbmUgdGFzazogQ2FsY3VsYXRlIGluZGl2aWR1YWwgc3R1ZGVudCBncmFkZSBzdGF0aXN0aWNzCkRlZmluZSBhIHRhc2sgbmFtZWQgImNhbGN1bGF0ZV9zdHVkZW50X2dyYWRlX3N0YXRpc3RpY3MiCiAgICBUYXNrIGlucHV0OiB7bWF0aF9zY29yZX0gKG51bWJlciB0eXBlKSwge2NoaW5lc2Vfc2NvcmV9IChudW1iZXIgdHlwZSksIHtlbmdsaXNoX3Njb3JlfSAobnVtYmVyIHR5cGUpCgogICAgIyBDYWxjdWxhdGUgdG90YWwgc2NvcmUKICAgIENhbGN1bGF0ZSB0aGUgcmVzdWx0IG9mIHttYXRoX3Njb3JlfSArIHtjaGluZXNlX3Njb3JlfSArIHtlbmdsaXNoX3Njb3JlfSwgcmVjb3JkZWQgYXMge3RvdGFsX3Njb3JlfQoKICAgICMgQ2FsY3VsYXRlIGF2ZXJhZ2Ugc2NvcmUKICAgIENhbGN1bGF0ZSB0aGUgcmVzdWx0IG9mIHt0b3RhbF9zY29yZX0gLyAzLCByZWNvcmRlZCBhcyB7YXZlcmFnZV9zY29yZX0KCiAgICAjIEdlbmVyYXRlIGNvbW1lbnQgYmFzZWQgb24gYXZlcmFnZSBzY29yZQogICAgSWYge2F2ZXJhZ2Vfc2NvcmV9IGlzIGdyZWF0ZXIgdGhhbiBvciBlcXVhbCB0byA5MDoKICAgICAgICBSZWNvcmQgIkV4Y2VsbGVudCEgS2VlcCBpdCB1cCEiIGFzIHtjb21tZW50fQogICAgT3RoZXJ3aXNlIGlmIHthdmVyYWdlX3Njb3JlfSBpcyBncmVhdGVyIHRoYW4gb3IgZXF1YWwgdG8gODA6CiAgICAgICAgUmVjb3JkICJHb29kLCB0aGVyZSdzIHJvb20gZm9yIGltcHJvdmVtZW50LiIgYXMge2NvbW1lbnR9CiAgICBPdGhlcndpc2UgaWYge2F2ZXJhZ2Vfc2NvcmV9IGlzIGdyZWF0ZXIgdGhhbiBvciBlcXVhbCB0byA3MDoKICAgICAgICBSZWNvcmQgIkF2ZXJhZ2UsIG5lZWQgdG8gc3RyZW5ndGhlbiBsZWFybmluZy4iIGFzIHtjb21tZW50fQogICAgT3RoZXJ3aXNlIGlmIHthdmVyYWdlX3Njb3JlfSBpcyBncmVhdGVyIHRoYW4gb3IgZXF1YWwgdG8gNjA6CiAgICAgICAgUmVjb3JkICJQYXNzLCBidXQgbmVlZCB0byB3b3JrIGhhcmRlci4iIGFzIHtjb21tZW50fQogICAgT3RoZXJ3aXNlOgogICAgICAgIFJlY29yZCAiRmFpbCwgbmVlZCB0byBmb2N1cyBvbiBsZWFybmluZy4iIGFzIHtjb21tZW50fQoKICAgICMgQ3JlYXRlIGdyYWRlIHN0YXRpc3RpY3Mgb2JqZWN0CiAgICBDcmVhdGUgYW4gb2JqZWN0IHtncmFkZV9zdGF0aXN0aWNzfSB3aXRoIGF0dHJpYnV0ZXM6ICJ0b3RhbF9zY29yZSIgaXMge3RvdGFsX3Njb3JlfSwgImF2ZXJhZ2Vfc2NvcmUiIGlzIHthdmVyYWdlX3Njb3JlfSwgImNvbW1lbnQiIGlzIHtjb21tZW50fQoKICAgIFRhc2sgcmV0dXJucyB7Z3JhZGVfc3RhdGlzdGljc30KCiMgRGVmaW5lIHRhc2s6IEdlbmVyYXRlIGluZGl2aWR1YWwgZ3JhZGUgcmVwb3J0IHRleHQKRGVmaW5lIGEgdGFzayBuYW1lZCAiZ2VuZXJhdGVfZ3JhZGVfcmVwb3J0IgogICAgVGFzayBpbnB1dDoge3N0dWRlbnRfbmFtZX0gKHRleHQgdHlwZSksIHtncmFkZV9zdGF0aXN0aWNzX29iamVjdH0gKG9iamVjdCB0eXBlKSwge2NsYXNzX3Jhbmt9IChudW1iZXIgdHlwZSkKCiAgICAjIEV4dHJhY3QgZ3JhZGUgc3RhdGlzdGljcyBpbmZvcm1hdGlvbgogICAgR2V0IHRoZSAidG90YWxfc2NvcmUiIGF0dHJpYnV0ZSBmcm9tIHtncmFkZV9zdGF0aXN0aWNzX29iamVjdH0sIHJlY29yZGVkIGFzIHt0b3RhbF9zY29yZX0KICAgIEdldCB0aGUgImF2ZXJhZ2Vfc2NvcmUiIGF0dHJpYnV0ZSBmcm9tIHtncmFkZV9zdGF0aXN0aWNzX29iamVjdH0sIHJlY29yZGVkIGFzIHthdmVyYWdlX3Njb3JlfQogICAgR2V0IHRoZSAiY29tbWVudCIgYXR0cmlidXRlIGZyb20ge2dyYWRlX3N0YXRpc3RpY3Nfb2JqZWN0fSwgcmVjb3JkZWQgYXMge2NvbW1lbnR9CgogICAgIyBHZW5lcmF0ZSByZXBvcnQgdGV4dAogICAgQ29tYmluZSB0aGUgZm9sbG93aW5nIGNvbnRlbnQgaW50byByZXBvcnQgdGV4dCwgcmVjb3JkZWQgYXMge3JlcG9ydF9jb250ZW50fTogIj09PSB7c3R1ZGVudF9uYW1lfSBJbmRpdmlkdWFsIEdyYWRlIFJlcG9ydCA9PT1cXG4iLCAiVG90YWwgU2NvcmU6IHt0b3RhbF9zY29yZX0gcG9pbnRzXFxuIiwgIkF2ZXJhZ2UgU2NvcmU6IHthdmVyYWdlX3Njb3JlfSBwb2ludHNcXG4iLCAiQ2xhc3MgUmFuazogI3tjbGFzc19yYW5rfVxcbiIsICJDb21tZW50OiB7Y29tbWVudH1cXG4iLCAiUmVwb3J0IEdlbmVyYXRpb24gVGltZTogY3VycmVudCBkYXRlIHRpbWVcXG4iLCAiPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cXG4iICMgTm90ZSwgZG8gbm90IGxpbmUgYnJlYWsKCiAgICBUYXNrIHJldHVybnMge3JlcG9ydF9jb250ZW50fQoKIyBNYWluIHByb2dyYW06IEJhdGNoIHByb2Nlc3Mgc3R1ZGVudCBncmFkZXMKIyBSZWFkIHN0dWRlbnQgZ3JhZGUgdGFibGUKUmVhZCB0aGUgY29udGVudCBvZiB0YWJsZSBmaWxlICJzdHVkZW50X3Njb3Jlcy5jc3YiIGFuZCBzdG9yZSBpdCBpbiBhIGRhdGEgdGFibGUsIHJlY29yZGVkIGFzIHtzdHVkZW50X2dyYWRlc190YWJsZX0KCiMgQ3JlYXRlIHJlc3VsdCB0YWJsZSB0byBzdG9yZSBhbGwgc3R1ZGVudHMnIHN0YXRpc3RpY3MKQ3JlYXRlIGFuIGVtcHR5IGRhdGEgdGFibGUgd2l0aCAibmFtZSIsICJ0b3RhbF9zY29yZSIsICJhdmVyYWdlX3Njb3JlIiwgInJhbmsiLCAiY29tbWVudCIgY29sdW1ucywgcmVjb3JkZWQgYXMge2dyYWRlX3N0YXRpc3RpY3NfdGFibGV9CgojIEZpcnN0IHJvdW5kOiBDYWxjdWxhdGUgZ3JhZGUgc3RhdGlzdGljcyBmb3IgZWFjaCBzdHVkZW50Ckl0ZXJhdGUgdGhyb3VnaCBlYWNoIHJvdyBpbiB7c3R1ZGVudF9ncmFkZXNfdGFibGV9LCByZWNvcmRlZCBhcyB7Y3VycmVudF9zdHVkZW50fToKICAgICMgR2V0IHN0dWRlbnQgaW5mb3JtYXRpb24KICAgIEdldCB0aGUgdmFsdWUgb2YgIm5hbWUiIGNvbHVtbiBmcm9tIHtjdXJyZW50X3N0dWRlbnR9LCByZWNvcmRlZCBhcyB7c3R1ZGVudF9uYW1lfQogICAgR2V0IHRoZSB2YWx1ZSBvZiAibWF0aCIgY29sdW1uIGZyb20ge2N1cnJlbnRfc3R1ZGVudH0sIHJlY29yZGVkIGFzIHttYXRoX3Njb3JlfQogICAgR2V0IHRoZSB2YWx1ZSBvZiAiY2hpbmVzZSIgY29sdW1uIGZyb20ge2N1cnJlbnRfc3R1ZGVudH0sIHJlY29yZGVkIGFzIHtjaGluZXNlX3Njb3JlfQogICAgR2V0IHRoZSB2YWx1ZSBvZiAiZW5nbGlzaCIgY29sdW1uIGZyb20ge2N1cnJlbnRfc3R1ZGVudH0sIHJlY29yZGVkIGFzIHtlbmdsaXNoX3Njb3JlfQoKICAgICMgQ2FsbCB0YXNrIHRvIGNhbGN1bGF0ZSBncmFkZSBzdGF0aXN0aWNzCiAgICBFeGVjdXRlIHRhc2sgImNhbGN1bGF0ZV9zdHVkZW50X2dyYWRlX3N0YXRpc3RpY3MiLCB7bWF0aF9zY29yZX0gaXMge21hdGhfc2NvcmV9LCB7Y2hpbmVzZV9zY29yZX0gaXMge2NoaW5lc2Vfc2NvcmV9LCB7ZW5nbGlzaF9zY29yZX0gaXMge2VuZ2xpc2hfc2NvcmV9LCBvdXRwdXQgcmVzdWx0IHJlY29yZGVkIGFzIHtncmFkZV9zdGF0aXN0aWNzfSAjIEZ1bmN0aW9uIGNhbGwgZG8gbm90IGxpbmUgYnJlYWsKCiAgICAjIEFkZCBzdGF0aXN0aWNzIHJlc3VsdHMgdG8gc3RhdGlzdGljcyB0YWJsZQogICAgQWRkIGEgcm93IG9mIGRhdGEgdG8ge2dyYWRlX3N0YXRpc3RpY3NfdGFibGV9LCAibmFtZSIgaXMge3N0dWRlbnRfbmFtZX0sICJ0b3RhbF9zY29yZSIgaXMge2dyYWRlX3N0YXRpc3RpY3MudG90YWxfc2NvcmV9LCAiYXZlcmFnZV9zY29yZSIgaXMge2dyYWRlX3N0YXRpc3RpY3MuYXZlcmFnZV9zY29yZX0sICJjb21tZW50IiBpcyB7Z3JhZGVfc3RhdGlzdGljcy5jb21tZW50fQoKIyBTb3J0IGJ5IHRvdGFsIHNjb3JlIGFuZCBhZGQgcmFua2luZwpTb3J0IHtncmFkZV9zdGF0aXN0aWNzX3RhYmxlfSBieSAidG90YWxfc2NvcmUiIGNvbHVtbiB2YWx1ZXMgZnJvbSBoaWdoIHRvIGxvdwpSZWNvcmQgMSBhcyB7Y3VycmVudF9yYW5rfQpJdGVyYXRlIHRocm91Z2ggZWFjaCByb3cgaW4ge2dyYWRlX3N0YXRpc3RpY3NfdGFibGV9LCByZWNvcmRlZCBhcyB7Y3VycmVudF9yb3d9OgogICAgU2V0IHRoZSB2YWx1ZSBvZiAicmFuayIgY29sdW1uIGluIHtjdXJyZW50X3Jvd30gdG8ge2N1cnJlbnRfcmFua30KICAgIENhbGN1bGF0ZSB0aGUgcmVzdWx0IG9mIHtjdXJyZW50X3Jhbmt9ICsgMSwgcmVjb3JkZWQgYXMge2N1cnJlbnRfcmFua30KCiMgU2Vjb25kIHJvdW5kOiBHZW5lcmF0ZSBpbmRpdmlkdWFsIHJlcG9ydCBmaWxlcyBmb3IgZWFjaCBzdHVkZW50Ckl0ZXJhdGUgdGhyb3VnaCBlYWNoIHJvdyBpbiB7Z3JhZGVfc3RhdGlzdGljc190YWJsZX0sIHJlY29yZGVkIGFzIHtjdXJyZW50X3N0YXRpc3RpY3N9OgogICAgIyBHZXQgc3R1ZGVudCBpbmZvcm1hdGlvbgogICAgR2V0IHRoZSB2YWx1ZSBvZiAibmFtZSIgY29sdW1uIGZyb20ge2N1cnJlbnRfc3RhdGlzdGljc30sIHJlY29yZGVkIGFzIHtzdHVkZW50X25hbWV9CiAgICBHZXQgdGhlIHZhbHVlIG9mICJyYW5rIiBjb2x1bW4gZnJvbSB7Y3VycmVudF9zdGF0aXN0aWNzfSwgcmVjb3JkZWQgYXMge2NsYXNzX3Jhbmt9CgogICAgIyBSZWJ1aWxkIGdyYWRlIHN0YXRpc3RpY3Mgb2JqZWN0IChmb3IgcGFzc2luZyB0byByZXBvcnQgZ2VuZXJhdGlvbiB0YXNrKQogICAgQ3JlYXRlIGFuIG9iamVjdCB7Y3VycmVudF9ncmFkZV9zdGF0aXN0aWNzfSB3aXRoIGF0dHJpYnV0ZXM6ICJ0b3RhbF9zY29yZSIgaXMgdGhlIHZhbHVlIG9mICJ0b3RhbF9zY29yZSIgY29sdW1uIGZyb20ge2N1cnJlbnRfc3RhdGlzdGljc30sICJhdmVyYWdlX3Njb3JlIiBpcyB0aGUgdmFsdWUgb2YgImF2ZXJhZ2Vfc2NvcmUiIGNvbHVtbiBmcm9tIHtjdXJyZW50X3N0YXRpc3RpY3N9LCAiY29tbWVudCIgaXMgdGhlIHZhbHVlIG9mICJjb21tZW50IiBjb2x1bW4gZnJvbSB7Y3VycmVudF9zdGF0aXN0aWNzfQoKICAgICMgQ2FsbCB0YXNrIHRvIGdlbmVyYXRlIHJlcG9ydAogICAgRXhlY3V0ZSB0YXNrICJnZW5lcmF0ZV9ncmFkZV9yZXBvcnQiLCB7c3R1ZGVudF9uYW1lfSBpcyB7c3R1ZGVudF9uYW1lfSwge2dyYWRlX3N0YXRpc3RpY3Nfb2JqZWN0fSBpcyB7Y3VycmVudF9ncmFkZV9zdGF0aXN0aWNzfSwge2NsYXNzX3Jhbmt9IGlzIHtjbGFzc19yYW5rfSwgb3V0cHV0IHJlc3VsdCByZWNvcmRlZCBhcyB7aW5kaXZpZHVhbF9yZXBvcnR9ICMgTm90ZSwgb25lIGxpbmUgb2YgY29kZSBjYW5ub3QgYmUgd3JpdHRlbiBhY3Jvc3MgbGluZXMKCiAgICAjIFNhdmUgaW5kaXZpZHVhbCByZXBvcnQgdG8gZmlsZQogICAgU2F2ZSB0ZXh0IGNvbnRlbnQge2luZGl2aWR1YWxfcmVwb3J0fSB0byBkb2N1bWVudCAie3N0dWRlbnRfbmFtZX1fZ3JhZGVfcmVwb3J0LnR4dCIKCiMgU2F2ZSBzdW1tYXJ5IHN0YXRpc3RpY3MgdGFibGUKU2F2ZSB7Z3JhZGVfc3RhdGlzdGljc190YWJsZX0gYXMgdGFibGUgZmlsZSAiY2xhc3Nfc3VtbWFyeS5jc3YiCgojIENvbXBsZXRpb24gbm90aWZpY2F0aW9uCkdldCB0aGUgbnVtYmVyIG9mIHJvd3MgaW4ge2dyYWRlX3N0YXRpc3RpY3NfdGFibGV9LCByZWNvcmRlZCBhcyB7dG90YWxfc3R1ZGVudHN9ClRlbGwgdXNlciAiQmF0Y2ggcHJvY2Vzc2luZyBjb21wbGV0ZWQhIEdlbmVyYXRlZCBpbmRpdmlkdWFsIGdyYWRlIHJlcG9ydHMgZm9yIHt0b3RhbF9zdHVkZW50c30gc3R1ZGVudHMsIHN1bW1hcnkgdGFibGUgc2F2ZWQgYXMgY2xhc3Nfc3VtbWFyeS5jc3YiCmBgYAoKIyMjIENhc2UgNTogTWluaW11bSBTcGFubmluZyBUcmVlCgpgYGAKRGVmaW5lIGEgdGFzayBuYW1lZCAiY29tcHV0ZV9taW5pbXVtX3NwYW5uaW5nX3RyZWUiCiAgICBUYXNrIGlucHV0OiB7bn0gKG51bWJlciB0eXBlKSwge2VkZ2VzfSAobGlzdCB0eXBlLCBlYWNoIGVsZW1lbnQgaXMgYSB0dXBsZSBvZiB0aHJlZSBwb3NpdGl2ZSBudW1iZXJzIHJlcHJlc2VudGluZyB0aGUgc3RhcnQgbm9kZSwgZW5kIG5vZGUsIGFuZCBlZGdlIHdlaWdodCkKCiAgICBTb2x2ZSB0aGUgZm9sbG93aW5nIHByb2JsZW06ICJHaXZlbiBhIHdlaWdodGVkIHVuZGlyZWN0ZWQgZ3JhcGggd2l0aCBuIG5vZGVzLCBjb25zdHJ1Y3QgYSBNaW5pbXVtIFNwYW5uaW5nIFRyZWUgKE1TVCkgdGhhdCBjb25uZWN0cyBhbGwgdGhlIG5vZGVzIHdpdGggdGhlIG1pbmltYWwgdG90YWwgZWRnZSB3ZWlnaHQuIEVhY2ggZWRnZSBjYW4gYmUgdXNlZCBvbmx5IG9uY2UsIGFuZCBubyBjeWNsZXMgYXJlIGFsbG93ZWQuIElmIHRoZSBncmFwaCBpcyBkaXNjb25uZWN0ZWQgYW5kIGFuIE1TVCBjYW5ub3QgYmUgZm9ybWVkLCByZXR1cm4gLTEuIi4gUmVjb3JkIHRoZSBjYWxjdWxhdGVkIHRvdGFsIHdlaWdodCBvZiB0aGUgbWluaW11bSBzcGFubmluZyB0cmVlIGFzIHttc3RfdG90YWxfd2VpZ2h0fSAjIE5vdGUsIHRoZSB0YXNrIGRlc2NyaXB0aW9uIG11c3QgYmUgd3JpdHRlbiBvbiBvbmUgbGluZS4KCiAgICBUYXNrIHJldHVybnMge21zdF90b3RhbF93ZWlnaHR9CmBgYAoKIyMjIENhc2UgNjogQWRkIHRoZSBmb2xsb3dpbmcgdGFza3MgaW50byB0aGUgVG9kb2lzdCBhcHA6ICJUYXNrOiBDb21wbGV0ZSBxdWFydGVybHkgcmVwb3J0ICBkdWVfZGF0ZTogMjAyNS0wOS0xNSAgcHJpb3JpdHk6IEhpZ2ggIHByb2plY3Q6IFdvcmsgIG5vdGU6IEluY2x1ZGUgc2FsZXMgZGF0YSBhbmQgcHJvamVjdGlvbnMiLCAiVGFzazogU2NoZWR1bGUgZGVudGlzdCBhcHBvaW50bWVudCAgZHVlX2RhdGU6IDIwMjUtMDktMjAgIHByaW9yaXR5OiBNZWRpdW0gIHByb2plY3Q6IFBlcnNvbmFsICBub3RlOiBDYWxsIERyLiBXaWxzb24ncyBvZmZpY2UiLCAiVGFzazogQnV5IGdyb2NlcmllcyBmb3IgZGlubmVyIHBhcnR5ICBkdWVfZGF0ZTogMjAyNS0wOS0xMyAgcHJpb3JpdHk6IEhpZ2ggIHByb2plY3Q6IEhvbWUgIG5vdGU6IE5lZWQgaW5ncmVkaWVudHMgZm9yIHBhc3RhIGFuZCBzYWxhZCIuCgpgYGAKUmVjb3JkICJUYXNrOiBDb21wbGV0ZSBxdWFydGVybHkgcmVwb3J0ICBkdWVfZGF0ZTogMjAyNS0wOS0xNSAgcHJpb3JpdHk6IEhpZ2ggIHByb2plY3Q6IFdvcmsgIG5vdGU6IEluY2x1ZGUgc2FsZXMgZGF0YSBhbmQgcHJvamVjdGlvbnMiLCAiVGFzazogU2NoZWR1bGUgZGVudGlzdCBhcHBvaW50bWVudCAgZHVlX2RhdGU6IDIwMjUtMDktMjAgIHByaW9yaXR5OiBNZWRpdW0gIHByb2plY3Q6IFBlcnNvbmFsICBub3RlOiBDYWxsIERyLiBXaWxzb24ncyBvZmZpY2UiLCAiVGFzazogQnV5IGdyb2NlcmllcyBmb3IgZGlubmVyIHBhcnR5ICBkdWVfZGF0ZTogMjAyNS0wOS0xMyAgcHJpb3JpdHk6IEhpZ2ggIHByb2plY3Q6IEhvbWUgIG5vdGU6IE5lZWQgaW5ncmVkaWVudHMgZm9yIHBhc3RhIGFuZCBzYWxhZCIgYXMgdGhlIHt0YXNrX2xpc3R9LgpJdGVyYXRlIG92ZXIgdGhlIHt0YXNrX2xpc3R9LCBhbmQgZm9yIGVhY2gge3Rhc2tfaXRlbX0sIGRvIHRoZSBmb2xsb3dpbmc6CiAgICBJbiB0aGUgYFRvZG9pc3RgIGFwcCwgTmF2aWdhdGUgdG8gdGhlIHRhc2sgY3JlYXRpb24gcGFnZSwgZmlsbCB0aGUgZm9ybSB3aXRoIHRoZSB7dGFza19pdGVtfSBpbmZvcm1hdGlvbiBpbmNsdWRpbmcgdGl0bGUsIGR1ZSBkYXRlLCBwcmlvcml0eSBsZXZlbCwgcHJvamVjdCBjYXRlZ29yeSwgYW5kIG5vdGVzLCB0aGVuIHNhdmUgdGhlIHRhc2suICMgTm90ZSwgaGVyZSB5b3UgbXVzdCB3cml0ZSAiSW4gdGhlIGBUb2RvaXN0YCBhcHAiIHRvIGVuc3VyZSB3b3JrZmxvdyBhY2N1cmFjeS4gQWxzbywgcmVtZW1iZXIgdG8gc2F2ZS4KYGBgCgojIyMgQ2FzZSA3OiBEZWxldGUgQWxsIENvbnRhY3RzIHdob3NlIG5hbWUgc3RhcnRzIHdpdGggJ0EnIGluIHRoZSBgQ29udGFjdHNgIGFwcC4KCmBgYApJbiB0aGUgYENvbnRhY3RzYCBhcHAsIERlbGV0ZSBBbGwgQ29udGFjdHMgd2hvc2UgbmFtZSBzdGFydHMgd2l0aCAnQScuICMgQ1JVRCBvcGVyYXRpb25zIGFyZSB1bml2ZXJzYWwgYXRvbWljIG9wZXJhdGlvbnMsIG5vIG5lZWQgdG8gd3JpdGUgdGhlbSB0b28gY29tcGxpY2F0ZWRseSEgVGhlIG1vcmUgY29tcGxleCwgdGhlIGVhc2llciB0byBlcnJvciEgRGVsZXRpbmcgaXRlbXMgZG9lc24ndCBuZWVkIGEgbG9vcCwganVzdCBvbmUgc2VudGVuY2UsIHRoZSBleGVjdXRvciB3aWxsIGF1dG9tYXRpY2FsbHkgY29tcGxldGUgdGhpcyB0YXNrLgpgYGAKCiMjIDUuIFRhc2sgUHJvZ3JhbSBXcml0aW5nIFN1Z2dlc3Rpb25zCgpJbiBsb25nLXRlcm0gYW5kIGV4dGVuc2l2ZSBUYXNrIFByb2dyYW0gcHJvZ3JhbW1pbmcgcHJhY3RpY2UsIHdlIGhhdmUgc3VtbWFyaXplZCB0aGUgZm9sbG93aW5nIHByb2dyYW1taW5nIHN1Z2dlc3Rpb25zLiBGb2xsb3dpbmcgdGhlc2Ugc3VnZ2VzdGlvbnMgY2FuIG1ha2UgeW91ciBUYXNrIFByb2dyYW0gY29kZSBtb3JlIHN0YWJsZSwgcmVsaWFibGUsIHZlcnNhdGlsZSwgYW5kIHBvd2VyZnVsLgoKMS4gICoqQXZvaWQgZmFicmljYXRpb24gYW5kIGFzc3VtcHRpb25zIChWZXJ5IEltcG9ydGFudCEhKSoqLiBTb21ldGltZXMgdGhlIGluZm9ybWF0aW9uIHByb3ZpZGVkIGJ5IHRoZSB1c2VyIGlzIG5vdCBjb21wcmVoZW5zaXZlLCBmb3IgZXhhbXBsZSwgdGFibGUgYW5hbHlzaXMgd2l0aG91dCBnaXZpbmcgdGhlIHNwZWNpZmljIGNvbnRlbnQgb2YgdGhlIHRhYmxlLiBJbiB0aGlzIGNhc2UsICoqeW91IG11c3QgdXNlIGV4aXN0aW5nIGluZm9ybWF0aW9uIGFzIG11Y2ggYXMgcG9zc2libGUsIGluc3RlYWQgb2YgZmFudGFzaXppbmcgd2l0aG91dCBiYXNpcyB0aGF0IGEgY2VydGFpbiBmaWVsZCBleGlzdHMgaW4gdGhlIHRhYmxlKiosIG9yIHRoYXQgYSBjZXJ0YWluIGNvbHVtbiBvZiB0aGUgdGFibGUgbXVzdCBoYXZlIHNwZWNpZmljIGNvbnRlbnQuIFRoZXNlIGZhYnJpY2F0aW9ucyBhbmQgYXNzdW1wdGlvbnMgZG8gbm90IHdvcmsgaW4gcmVhbCBwcm9ibGVtcy4gKipTaW5jZSBUYXNrIFByb2dyYW0gbGFuZ3VhZ2UgaXMgZHluYW1pYywgeW91IGNhbiBsZXQgVGFzayBQcm9ncmFtIGF1dG9ub21vdXNseSBhbmFseXplIHdoYXQgZXhpc3RzIGluIHRoZSB0YWJsZSoqLiBKdXN0IGFzIHNob3duIGluIG91ciBjYXNlcyAoQW5hbHl6ZSB0aGUgc3ViamVjdCBuYW1lcyBpbiB7c3R1ZGVudF9ncmFkZXNfdGFibGV9LCByZWNvcmRlZCBhcyB7c3ViamVjdF9saXN0fSwgYmVjYXVzZSB3ZSBkb24ndCBrbm93IHdoaWNoIHN1YmplY3RzIGFyZSBpbiB0aGUgdGFibGUsIHdlIGNhbiBsZXQgVGFzayBQcm9ncmFtIGF1dG9tYXRpY2FsbHkgYW5hbHl6ZSB3aGljaCBzdWJqZWN0cyBhcmUgdGhlcmUsIGluc3RlYWQgb2YgcHJlc3VtcHR1b3VzbHkgYXNzdW1pbmcgIkNoaW5lc2UiLCAiTWF0aCIsIGV0Yy4gZXhpc3QuIEluIHRoaXMgZXhhbXBsZSwgdGhlIGlucHV0IG9mICJBbmFseXNpcyIgaXMgYSB0YWJsZSwgYW5kIHRoZSBvdXRwdXQgaXMgYSBsaXN0IG9mIHN1YmplY3RzLiBJdCBpcyB2aXNpYmxlIHRoYXQgd2UgY2FuIGxldCBUYXNrIFByb2dyYW0gYXV0b25vbW91c2x5IGFuYWx5emUgdGhlIHRhYmxlIHRvIG9idGFpbiByZXF1aXJlZCBpbmZvcm1hdGlvbi4pCjIuICAqKkF2b2lkIHRyaXZpYWwgZGV0YWlscywgZm9jdXMgb24gY29yZSBnb2FscyBvZiB0aGUgdGFzayoqLCBtYWtpbmcgdGhlIGNvZGUgdW5pdmVyc2FsLiBGb3IgZXhhbXBsZSwgIkdvIHRvIHRoZSBjb252ZW5pZW5jZSBzdG9yZSIgaXMgYmV0dGVyIHRoYW4gIldhbGsgNDAgbWV0ZXJzIGVhc3QsIHRoZW4gMjAgbWV0ZXJzIG5vcnRoIiwgYmVjYXVzZSB0aGUgZ29hbCBpcyB0byBidXkgdGhpbmdzLCBqdXN0IGNhcmluZyBhYm91dCB3aGV0aGVyIHRoZSBzdG9yZSBpcyByZWFjaGVkIGlzIGVub3VnaCwgbm8gbmVlZCB0byBnaXZlIGRldGFpbGVkIG5hdmlnYXRpb24gb3BlcmF0aW9ucy4gVGhlc2UgbG93LWxldmVsIG9wZXJhdGlvbnMgc2hvdWxkIGJlIGxlZnQgZm9yIGV4ZWN1dGlvbiB0aW1lLCBub3QgcHJvZ3JhbW1pbmcgdGltZS4gVGhlIHByb2dyYW0gc2hvdWxkIGZvY3VzIG1vcmUgb24gdGhlIHdvcmsgbG9naWMgaXRzZWxmLCB0cnlpbmcgdG8gZGlzY2FyZCB0aGluZ3MgdW5yZWxhdGVkIHRvIHRoZSBjb3JlIGZsb3cuCjMuICAqKkNvbnNpZGVyIGNvbmNpc2VuZXNzKiouIEZvciBleGFtcGxlLCBpZiB0aGVyZSBpcyBubyBjb25mbGljdCBpbiB0aGUgdGFibGUsIHRyeSB0byB0cmF2ZXJzZSBpdCBpbiBvbmUgbG9vcCBpbnN0ZWFkIG9mIHdyaXRpbmcgbXVsdGlwbGUgcmVkdW5kYW50IGxvb3BzLiBPZiBjb3Vyc2UsIGlmIG11bHRpcGxlIGxvb3BzIGFyZSBuZWNlc3NhcnksIHRoZXkgc2hvdWxkIGJlIHdyaXR0ZW4gYXBwcm9wcmlhdGVseS4KNC4gICoqT25lIG9wZXJhdGlvbiBwZXIgbGluZSoqLiBUYXNrIFByb2dyYW0gc3ludGF4IHJlcXVpcmVzIHVzIHRoYXQgKip0aGUgc2FtZSBvcGVyYXRpb24gY2Fubm90IGJlIHdyaXR0ZW4gYWNyb3NzIGxpbmVzKiosIHN0cmluZ3MsIGF0dHJpYnV0ZXMsIGV0Yy4sIG11c3QgYmUgd3JpdHRlbiBvbiB0aGUgc2FtZSBsaW5lLCBkbyBub3QgbGluZSBicmVhay4KNS4gICoqV2hlbiBlbmNvdW50ZXJpbmcgYWxnb3JpdGhtIHByb2JsZW1zKiosIGp1c3QgZGVmaW5lIGEgY29ycmVzcG9uZGluZyB0YXNrIHRvIHNvbHZlIGl0LCBkZXNjcmliZSB0aGUgdGFzayBmcmFtZXdvcmsgcm91Z2hseSwgZG8gbm90IGRlZmluZSBzcGVjaWZpYyBpbXBsZW1lbnRhdGlvbi4gQWxnb3JpdGhtIHRhc2tzIG9ubHkgbmVlZCB0byBkZWZpbmUgaW5wdXQsIHRhc2sgZGVzY3JpcHRpb24sIHJldHVybiB2YWx1ZSwgYW5kIHRoZSBUYXNrIFByb2dyYW0gaW50ZXJwcmV0ZXIgd2lsbCBhdXRvbWF0aWNhbGx5IGltcGxlbWVudCByZWxldmFudCBhbGdvcml0aG1zLgo2LiAgKipJZiBpdCBpbnZvbHZlcyBkZWZpbmluZyBjbGFzc2VzLCBvYmplY3RzLCBkYXRhIHN0cnVjdHVyZXMqKiwgbGluZXMgbXVzdCBiZSB3cml0dGVuIGF0IHRoZSB2ZXJ5IGJlZ2lubmluZy4gRmlyc3Qgd3JpdGUgY2xhc3Mvb2JqZWN0IGRlZmluaXRpb25zLCB0aGVuIHRhc2sgZGVmaW5pdGlvbnMsIGZpbmFsbHkgdGhlIHdvcmtmbG93Lgo3LiAgKipNdXN0IGZvbGxvdyB0aGUgZXhhbXBsZSBmb3JtYXQgdG8gd3JpdGUgVGFzayBQcm9ncmFtISoqIERvIG5vdCBhZGQgbGFiZWxzIGxpa2UgMS4yLjMuNCBiZWZvcmUgdGhlIFdvcmtmbG93IQo4LiAgKipOb3RlLCBzdGF0ZW1lbnRzIHJlcXVpcmluZyBBUFAgb3BlcmF0aW9uIG11c3QgZGVjbGFyZSBvcGVyYXRpb24gaW4geHh4IEFQUCoqLCBmb3IgZXhhbXBsZTogYEluICJDb250YWN0cyIgQXBwLCBhZGQgYSBuZXcgY29udGFjdCBuYW1lICdBbGljZScuYCBPdGhlcndpc2UsIHRoZSB3b3JrZmxvdyBsYWNrcyBhY2N1cmFjeSwgYW5kIHRoZSBleGVjdXRvciBkb2Vzbid0IGtub3cgd2hpY2ggQVBQIHlvdSBuZWVkIHRvIHVzZSB0byBjb21wbGV0ZSB0aGUgdGFzay4KOS4gICoqQ3JlYXRlLCBSZWFkLCBVcGRhdGUsIERlbGV0ZSAoQ1JVRCkgYXJlIGFsbCB1bml2ZXJzYWwgYXRvbWljIG9wZXJhdGlvbnMqKiwgbm8gbmVlZCB0byB3cml0ZSBvdXQgdGhlaXIgdW5kZXJseWluZyBzcGVjaWZpYyBiZWhhdmlvcnMsIGp1c3Qgb25lIHNlbnRlbmNlIGlzIGVub3VnaCEgVGhlIG1vcmUgY29tcGxleCwgdGhlIGVhc2llciB0byBlcnJvciEgRGVsZXRpbmcgaXRlbXMgZG9lcyBub3QgbmVlZCB0byBiZSB3cml0dGVuIGFzIGFuIHVuZGVybHlpbmcgbG9vcCwganVzdCBvbmUgc2VudGVuY2UsIHRoZSBleGVjdXRvciB3aWxsIGF1dG9tYXRpY2FsbHkgY29tcGxldGUgdGhpcyB0YXNrLCBzcGVjaWZpY2FsbHkgaG93IHRvIGRlbGV0ZSBpcyBsZWZ0IHRvIHRoZSBleGVjdXRvcidzIHVuZGVybHlpbmcgbGF5ZXIgdG8gY29tcGxldGUh)

1
I will introduce you to a new programming language called \*\*Task Program\*\*. This is a natural language style domain-specific language (DSL) used to describe task execution flows. You need to master this language and complete the tasks I arrange.

2

3
# Task Program Language Syntax

4

5
## 1. Basic Syntax and Concepts

6

7
The syntax of Task Program is similar to natural language, but following certain structures and concepts will help the system understand your intent more precisely.

8

9
A Task Program consists of a series of statements, usually one per line, describing an operation or a step, using imperative sentences or clear declarative sentences.

10

11
### Comments

12

13
Start a line with the ‘#‘ symbol to indicate that the line is a comment. Comments are used to explain code, and the system will ignore them during execution.

14

15
‘‘‘

16
# This is a comment, the system will not execute this sentence

17
Tell user "Hello, comments make code easier to understand" # This is also an inline comment

18
‘‘‘

19

20
### Variables

21

22
In Task Program, variables are represented by words wrapped in curly braces.

23

24
\* \*\*Declaring (Recording) Variables\*\*: Usually done using ‘record as {variable\_name}‘ or similar natural language phrasing.

25

26
 ‘‘‘

27
 Set variable {user\_name} to "John"

28
 Set {current\_city} to "Beijing"

29
 Create variable {visitor\_count}, initial value is 0

30
 ‘‘‘

31
\* \*\*Using Variables\*\*: Where stored information is needed, use ‘{variable\_name}‘ to represent filling in the position with the variable’s value.

32

33
 ‘‘‘

34
 Tell user "Hello, {user\_name}"

35
 Search in browser for "{current\_city} population", record as {population\_count}

36
 Tell user "The population of {current\_city} is {population\_count}."

37
 ‘‘‘

38
\* Variable names should use meaningful words to facilitate understanding.

39

40
### Data Types

41

42
When variables are stored and passed in the system, they are understood as different types of data for actual operations. Different types of variables are used for data processing in different scenarios, such as number types for statistics, text types for document operations, dialogue, etc.

43

44
In Task Program, you do not need to specifically care about variable types; Task Program will automatically understand the type of each variable based on your code. Of course, you can also supplement the type description when defining variables to have more control over the entire process.

45

46
#### Basic Data Types

47

48
Task Program currently supports the following basic data types:

49

50
\* \*\*Text\*\*: A sequence of characters enclosed in quotes, such as ‘"Hello world!"‘ or ‘’Hello, World!’‘.

51
\* \*\*Number\*\*: Integers or decimals, such as ‘10‘ or ‘3.14‘.

52
\* \*\*Boolean\*\*: ‘True‘ or ‘False‘ (or ‘Yes‘ / ‘No‘), used to represent conditions or states.

53

54
 ‘‘‘

55
 Judge if {age} is greater than 18, record as {is\_adult} # {is\_adult} will be True or False

56
 If {is\_adult} is true:

57
 Tell user "You are an adult."

58
 ‘‘‘

59
\* \*\*Image\*\*: Represents image data. Can be obtained by reading files, etc.

60

61
 ‘‘‘

62
 Read image file "logo.png", record as {company\_logo}

63
 Tell user "This is the company Logo:"

64
 Send {company\_logo} to user

65
 ‘‘‘

66

67
#### Objects

68

69
An Object is a collection containing multiple \*\*properties\*\*, used to represent a specific thing or entity. Each property has a name and a corresponding value (also known as key-value pairs). The value of a property can be a basic type variable or another object.

70

71
\* \*\*Creating Objects\*\*:

72

73
 ‘‘‘

74
 Create an object named {my\_car}

75
 Set {color} of {my\_car} to "Red"

76
 Set {brand} of {my\_car} to "Tesla"

77
 Set {model} of {my\_car} to "Model Y"

78

79
 # Or a more concise way, AI will understand your intent

80
 Create an object {client}, with attributes including: "name" is "Li Ming", "age" is 24, "city" is "Shanghai"

81
 ‘‘‘

82
\* \*\*Accessing Object Properties\*\*:

83
 You can access property values directly using natural language inside curly braces, or use the dot ‘.‘ operator closer to traditional programming.

84

85
 ‘‘‘

86
 Tell user "My car color is {color of my\_car}"

87
 If {age of client} is greater than 18: # Assuming {client} is an object defined earlier

88
 Tell user "{name of client} is an adult."

89

90
 # Or using the {variable.property} format

91
 Tell user "My car color is: {my\_car.color}, brand is {my\_car.brand}, model is {my\_car.model}"

92
 ‘‘‘

93

94
#### Lists

95

96
A List is an ordered series of basic type elements or objects.

97

98
‘‘‘

99
# Create list

100
Record list ["Apple", "Banana", "Orange"] as {fruit\_list}

101
Count which public AI companies exist currently, output company name list, record as {company\_list} # {company\_list} is a text list

102

103
# Access list elements (AI will intelligently understand)

104
Get the first item of {fruit\_list}, record as {fruit\_1}

105
Tell user "My favorite fruit is: {fruit\_1}"

106
Get the quantity of elements in {company\_list}, record as {company\_count}

107
Tell user "There are approximately {company\_count} public AI companies."

108
‘‘‘

109

110
#### Data Tables

111

112
Data Tables are similar to spreadsheets, containing rows and columns. \*\*A Data Table can be viewed as a list composed of multiple objects with the same structure.\*\* Each row in the table corresponds to an object, and each column corresponds to a property of the object. You can create data tables, add, delete, modify data in tables, import/export tables from/to files, etc.

113

114
‘‘‘

115
# Create data table

116
Establish an empty data table containing columns "Name", "Department", "ID", record as {employee\_info\_table}

117

118
# Add a row (Can be understood as adding an object matching the structure)

119
Create an object {new\_employee\_A}, containing attributes "Name" is "Zhang San", "Department" is "Tech", "ID" is "T001"

120
Add {new\_employee\_A} as a new row to {employee\_info\_table}

121

122
# Add a row of content (More concise way)

123
Add a row of data {"Name": "Xiao Ming", "Department": "Marketing", "ID": "M023"} to {employee\_info\_table}

124

125
# Load data from file to table

126
Read content of table file "external\_employees.xlsx", store into new data table {external\_employee\_table}

127

128
# Save data table to file

129
Save {employee\_info\_table} to file, filename is "employees.xlsx"

130
‘‘‘

131

132
#### Data Processing

133

134
Task Program integrates AI large model capabilities. You only need to describe your processing requirements to complete various complex data processing operations.

135

136
\* \*\*Filter\*\*:

137
 ‘‘‘

138
 Filter out all company records with "Market Cap" (Unit: Billion) greater than 100 from {company\_data\_table}, record result as {large\_companies\_table}

139
 ‘‘‘

140
\* \*\*Extract\*\*:

141
 ‘‘‘

142
 Get "Country" column from {company\_data\_table}, after deduplication record as {country\_name\_list}

143
 ‘‘‘

144
\* \*\*Summarize\*\*:

145
 ‘‘‘

146
 Calculate the sum of "Market Cap" for all companies in {company\_data\_table} where "Country" attribute is "China", record as {china\_companies\_total\_cap}

147
 ‘‘‘

148
\* \*\*Sort\*\*:

149
 ‘‘‘

150
 Sort {company\_data\_table} by "Market Cap" column values from largest to smallest

151
 ‘‘‘

152
\* \*\*Merge\*\*:

153
 ‘‘‘

154
 Merge {domestic\_sales\_table} and {overseas\_sales\_table} by "Product ID" column, record as {global\_sales\_total\_table}

155
 ‘‘‘

156
\* \*\*Calculate\*\*:

157
 ‘‘‘

158
 Divide "Market Cap" by "Employee Count" in {company\_data\_table}, add as "Per Capita Market Cap" column

159
 ‘‘‘

160

161
### Flow Control

162

163
Code is executed sequentially line by line by default, but you can change the execution flow via flow control syntax.

164

165
#### Loops

166

167
When the same operation needs to be repeated for each item in a group, use a loop.

168

169
A loop consists of a loop condition and loop content. The loop condition describes the method and number of times, and the loop content is the steps to be repeated in each round.

170

171
The code for loop content usually needs indentation (leaving some spaces relative to the loop condition at the start of each line, usually 4 spaces) to indicate these operations are part of the loop. The Task Program AI interpreter has some tolerance for indentation, but good indentation helps readability and accuracy.

172

173
‘‘‘

174
# Iterate through every {single\_item\_variable} in {data\_collection}

175
Record list {"Apple Pie", "Banana Boat", "Orange Juice"} as {dessert\_menu}

176
Iterate through every dessert in {dessert\_menu}, record as {current\_dessert}

177
 Tell user "We are selling: {current\_dessert}"

178
‘‘‘

179

180
#### Conditional Branching

181

182
When the program needs to perform different operations based on different situations, use conditional branching.

183

184
In conditional branching, the program decides which branch to execute based on the judgment of a condition expression.

185

186
A condition expression is generally a judgment, such as ‘{market\_cap} less than 10 billion‘, ‘{hospital\_list} is empty‘, etc., or a variable containing a boolean value.

187

188
\* \*\*Basic Format\*\*:

189

190
 ‘‘‘

191
 If {condition\_1}:

192
 ... (Execute when condition 1 is met)

193
 Otherwise if {condition\_2}: # Optional

194
 ... (Execute when condition 1 is not met but condition 2 is met)

195
 Otherwise: # Optional

196
 ... (Execute when neither condition 1 nor 2 is met)

197
 ‘‘‘

198

199
\* \*\*Examples:\*\*

200

201
 ‘‘‘

202
 # Example 1

203
 If {user\_age} is less than 18:

204
 Tell user "You are a minor."

205
 Otherwise if {user\_age} is greater than or equal to 18 and {user\_age} is less than 60:

206
 Tell user "You are an adult."

207
 Otherwise:

208
 Tell user "You have entered old age."

209

210
 # Example 2

211
 Query "How is the weather today?", output weather description, record as {weather\_situation}

212
 If {weather\_situation} contains "Rain":

213
 Tell user "Please remember to bring an umbrella when going out."

214
 Otherwise:

215
 Tell user "The weather is nice today!"

216
 ‘‘‘

217

218
### Task Decomposition (Functions)

219

220
In Task Program, you can define a set of commonly used operations as a "Task", which is similar to "Functions" or "Subroutines" in traditional programming languages. This makes your main flow more concise and facilitates code reuse.

221

222
\* \*\*Defining Tasks\*\*:

223
 Start with ‘Define a task named "{task\_name}"‘. Tasks can have input parameters and outputs (return values).

224

225
 ‘‘‘

226
 # Define a task to greet a specific user

227
 Define a task named "Custom Greeting"

228
 Task input: {user\_name} (Type: Text)

229
 Record "Hello, {user\_name}! Welcome to Task Program." as {greeting\_text}

230
 Tell user {greeting\_text}

231
 # This task has no explicit return value

232

233
 # Define a task to calculate sum of two numbers and return result

234
 Define a task named "Calculate Sum of Two Numbers"

235
 Task input: {number\_one} (Number type) and {number\_two} (Number type)

236
 Record result of {number\_one} plus {number\_two} as {calculation\_result}

237
 Task returns {calculation\_result} # Task ends, and outputs {calculation\_result}

238
 ‘‘‘

239

240
 The first line of the task definition or the lines immediately following are usually used to describe the required input parameters and their types (optional, but recommended).

241
\* \*\*Calling Tasks\*\*:

242
 Use ‘Execute task "{task\_name}"‘, provide necessary input parameters, and (optionally) receive output results.

243

244
 ‘‘‘

245
 # Call greeting task

246
 Execute task "Custom Greeting", {user\_name} is "Zhang San"

247

248
 # Call calculation task and get output

249
 Execute task "Calculate Sum of Two Numbers", {number\_one} is 10, {number\_two} is 25, output result record as {total}

250
 Tell user "Result of 10 + 25 is: {total}"

251
 ‘‘‘

252

253
 The Task Program interpreter will intelligently match input parameter names. If parameter names in the definition and the call are not exactly the same but have similar meanings, the interpreter will also attempt to understand.

254

255
Using functions (tasks), you can decompose a complex large task into a series of smaller, easier-to-manage and describe sub-tasks, and then complete them one by one.

256
This ability to decompose tasks is essentially the ability of architecture and logic, requiring careful design, using variables to pass information at different stages of the flow, while ensuring the overall structure of the program is concise and readable.

257

258
## 2. Using Tools

259

260
Many complex functions rely on powerful tools to implement. The examples introduced above have actually involved some. This chapter will introduce them in detail.

261

262
### Operating Files

263

264
Task Program supports reading and saving files, including images, documents, tables, etc. Filenames are recommended to be wrapped in quotes; filenames are relative to the file path in the current IDE workspace.

265

266
‘‘‘

267
Save text content "This is the first line written.\\nThis is the second line." to document "My Notes"

268
Read all text content of document "My Notes", record as {note\_content}

269
Tell user "Note content is:\\n{note\_content}"

270

271
Save {company\_market\_cap\_table} as table file "company\_market\_cap\_report"

272
Read data in table file "company\_market\_cap\_report", record as {market\_cap\_table}

273

274
Check if file "thesis\_draft" exists

275
If file exists:

276
 Read content of file "thesis\_draft", record as {thesis\_draft}

277
Otherwise:

278
 Tell user "Document does not exist."

279
‘‘‘

280

281
Task Program will intelligently handle file read/write formats based on file suffixes and your description.

282

283
## 3. Task Program Writing Principles

284

285
1. \*\*Readability\*\*: Program statements should be concise and smooth, easy for ordinary users to understand and modify.

286
2. \*\*Feasibility\*\*: The program should fit the user’s device and software environment, ensuring it can be executed correctly.

287
3. \*\*Generality\*\*: Do not make any assumptions about things you don’t know. Assumptions will definitely miss important things. You should use the generality of Task Program’s natural language to generalize all possible situations. General language is still understandable to Task Program. For example, "Calculate xxx" is better than "If operation is addition, calculate a+b; if operation is subtraction, calculate a-b", because the former is more general.

288

289
## 4. Practical Cases

290

291
The following are representative examples showcasing the capabilities of the Task Program language in different scenarios.

292

293
### Case 1: Calculate average scores and grades for students based on their subject scores in the students.csv table (90 and above for A, 80-89 for B, 70-79 for C, 60-69 for D, below 60 for F), and save the results as student\_grades.csv

294

295
‘‘‘

296
# Read student grade table

297
Read the content of table file "students.csv" and store it in a data table, recorded as {student\_grades\_table}

298

299
# Analyze subject names (automatically identify score-related columns)

300
Analyze the subject names in {student\_grades\_table}, recorded as {subject\_list}

301

302
# Add new columns for results

303
Add a new column "average\_score" to {student\_grades\_table}

304
Add a new column "grade" to {student\_grades\_table}

305

306
# Iterate through each row to calculate average score and grade

307
Iterate through each row in {student\_grades\_table}, recorded as {current\_student}:

308
 # Collect all scores for current student

309
 Create an empty list, recorded as {current\_student\_scores\_list}

310
 Iterate through each subject name in {subject\_list}, recorded as {subject\_name}:

311
 Get the value of {subject\_name} column from {current\_student}, recorded as {current\_score}

312
 Add {current\_score} to {current\_student\_scores\_list}

313

314
 # Calculate average score

315
 Calculate the average of all values in {current\_student\_scores\_list}, recorded as {average\_score}

316

317
 # Determine grade based on average score

318
 Calculate {grade} from {average\_score}, 90 and above for A, 80-89 for B, 70-79 for C, 60-69 for D, below 60 for F

319

320
 # Store calculation results in current row

321
 Set the value of "average\_score" column in {current\_student} to {average\_score}

322
 Set the value of "grade" column in {current\_student} to {grade}

323

324
# Save results to new file

325
Save {student\_grades\_table} as table file "student\_grades.csv"

326

327
# Display processing result summary

328
Get the number of rows in {student\_grades\_table}, recorded as {total\_students}

329
Get the length of {subject\_list}, recorded as {total\_subjects}

330
Print "Grade processing completed! Processed {total\_subjects} subject scores for {total\_students} students, results saved as student\_grades.csv"

331
‘‘‘

332

333
### Case 2: Consolidating Contacts from table1.csv, table2.csv, and table3.csv into One Table, save as "contact\_summary.csv"

334

335
‘‘‘

336
# Read three contact table files

337
Read the content of table file "table1.csv" and store it in a data table, recorded as {contacts\_table1}

338
Read the content of table file "table2.csv" and store it in a data table, recorded as {contacts\_table2}

339
Read the content of table file "table3.csv" and store it in a data table, recorded as {contacts\_table3}

340

341
# Create empty summary table

342
Create an empty data table, recorded as {contacts\_summary\_table}

343

344
# Get column structure from first table as base structure for summary table

345
Get all column names from {contacts\_table1}, recorded as {column\_names\_list}

346
Iterate through each column name in {column\_names\_list}, recorded as {current\_column\_name}:

347
 Add new column {current\_column\_name} to {contacts\_summary\_table}

348

349
# Add data from table1 to summary table

350
Iterate through each row in {contacts\_table1}, recorded as {current\_contact}:

351
 Add {current\_contact} as a new row to {contacts\_summary\_table}

352

353
# Add data from table2 to summary table

354
Iterate through each row in {contacts\_table2}, recorded as {current\_contact}:

355
 Add {current\_contact} as a new row to {contacts\_summary\_table}

356

357
# Add data from table3 to summary table

358
Iterate through each row in {contacts\_table3}, recorded as {current\_contact}:

359
 Add {current\_contact} as a new row to {contacts\_summary\_table}

360

361
# Remove duplicate contact records (based on name and phone number)

362
Remove duplicate rows from {contacts\_summary\_table} based on "name" and "phone" columns, keeping the first occurrence

363

364
# Sort by name

365
Sort {contacts\_summary\_table} by "name" column values from A to Z

366

367
# Save summary results

368
Save {contacts\_summary\_table} as table file "contacts\_summary.csv"

369

370
# Count summary information

371
Get the number of rows in {contacts\_summary\_table}, recorded as {total\_contacts}

372
Print "Contact consolidation completed! Organized {total\_contacts} contacts in total, saved as contacts\_summary.csv"

373
‘‘‘

374

375
### Case 3: Calculate First N Terms of Fibonacci Sequence and Save to File

376

377
‘‘‘

378
# Create data table to store results

379
Create an empty data table with "sequence\_number" and "fibonacci\_value" columns, recorded as {fibonacci\_table}

380

381
# Initialize first two terms

382
If {terms\_N} is greater than or equal to 1:

383
 Add a row of data {"sequence\_number": 1, "fibonacci\_value": 0} to {fibonacci\_table}

384
 Record 0 as {previous\_previous\_term}

385

386
If {terms\_N} is greater than or equal to 2:

387
 Add a row of data {"sequence\_number": 2, "fibonacci\_value": 1} to {fibonacci\_table}

388
 Record 1 as {previous\_term}

389

390
# Calculate terms 3 to N

391
If {terms\_N} is greater than 2:

392
 Record 3 as {current\_sequence\_number}

393
 Repeat until {current\_sequence\_number} is greater than {terms\_N}:

394
 # Calculate current term value

395
 Calculate the result of {previous\_previous\_term} + {previous\_term}, recorded as {current\_term}

396

397
 # Add result to table

398
 Add a row of data {"sequence\_number": {current\_sequence\_number}, "fibonacci\_value": {current\_term}} to {fibonacci\_table}

399

400
 # Update previous two terms for next calculation

401
 Record {previous\_term} as {previous\_previous\_term}

402
 Record {current\_term} as {previous\_term}

403

404
 # Increment sequence number

405
 Calculate the result of {current\_sequence\_number} + 1, recorded as {current\_sequence\_number}

406

407
# Save results to file

408
Save {fibonacci\_table} as table file "fibonacci.csv"

409

410
# Display calculation result summary

411
Get the "fibonacci\_value" from the last row of {fibonacci\_table}, recorded as {last\_term\_value}

412
Tell user "Calculation completed! The {terms\_N}th term of Fibonacci sequence is: {last\_term\_value}"

413
Tell user "Complete results have been saved to fibonacci.csv file"

414

415
‘‘‘

416

417
### Case 4: Batch Processing Student Grade Data and Generating Individual Grade Reports, subjects include "Math", "Chinese", "English"

418

419
‘‘‘

420
# Define task: Calculate individual student grade statistics

421
Define a task named "calculate\_student\_grade\_statistics"

422
 Task input: {math\_score} (number type), {chinese\_score} (number type), {english\_score} (number type)

423

424
 # Calculate total score

425
 Calculate the result of {math\_score} + {chinese\_score} + {english\_score}, recorded as {total\_score}

426

427
 # Calculate average score

428
 Calculate the result of {total\_score} / 3, recorded as {average\_score}

429

430
 # Generate comment based on average score

431
 If {average\_score} is greater than or equal to 90:

432
 Record "Excellent! Keep it up!" as {comment}

433
 Otherwise if {average\_score} is greater than or equal to 80:

434
 Record "Good, there’s room for improvement." as {comment}

435
 Otherwise if {average\_score} is greater than or equal to 70:

436
 Record "Average, need to strengthen learning." as {comment}

437
 Otherwise if {average\_score} is greater than or equal to 60:

438
 Record "Pass, but need to work harder." as {comment}

439
 Otherwise:

440
 Record "Fail, need to focus on learning." as {comment}

441

442
 # Create grade statistics object

443
 Create an object {grade\_statistics} with attributes: "total\_score" is {total\_score}, "average\_score" is {average\_score}, "comment" is {comment}

444

445
 Task returns {grade\_statistics}

446

447
# Define task: Generate individual grade report text

448
Define a task named "generate\_grade\_report"

449
 Task input: {student\_name} (text type), {grade\_statistics\_object} (object type), {class\_rank} (number type)

450

451
 # Extract grade statistics information

452
 Get the "total\_score" attribute from {grade\_statistics\_object}, recorded as {total\_score}

453
 Get the "average\_score" attribute from {grade\_statistics\_object}, recorded as {average\_score}

454
 Get the "comment" attribute from {grade\_statistics\_object}, recorded as {comment}

455

456
 # Generate report text

457
 Combine the following content into report text, recorded as {report\_content}: "=== {student\_name} Individual Grade Report ===\\n", "Total Score: {total\_score} points\\n", "Average Score: {average\_score} points\\n", "Class Rank: #{class\_rank}\\n", "Comment: {comment}\\n", "Report Generation Time: current date time\\n", "================================\\n" # Note, do not line break

458

459
 Task returns {report\_content}

460

461
# Main program: Batch process student grades

462
# Read student grade table

463
Read the content of table file "student\_scores.csv" and store it in a data table, recorded as {student\_grades\_table}

464

465
# Create result table to store all students’ statistics

466
Create an empty data table with "name", "total\_score", "average\_score", "rank", "comment" columns, recorded as {grade\_statistics\_table}

467

468
# First round: Calculate grade statistics for each student

469
Iterate through each row in {student\_grades\_table}, recorded as {current\_student}:

470
 # Get student information

471
 Get the value of "name" column from {current\_student}, recorded as {student\_name}

472
 Get the value of "math" column from {current\_student}, recorded as {math\_score}

473
 Get the value of "chinese" column from {current\_student}, recorded as {chinese\_score}

474
 Get the value of "english" column from {current\_student}, recorded as {english\_score}

475

476
 # Call task to calculate grade statistics

477
 Execute task "calculate\_student\_grade\_statistics", {math\_score} is {math\_score}, {chinese\_score} is {chinese\_score}, {english\_score} is {english\_score}, output result recorded as {grade\_statistics} # Function call do not line break

478

479
 # Add statistics results to statistics table

480
 Add a row of data to {grade\_statistics\_table}, "name" is {student\_name}, "total\_score" is {grade\_statistics.total\_score}, "average\_score" is {grade\_statistics.average\_score}, "comment" is {grade\_statistics.comment}

481

482
# Sort by total score and add ranking

483
Sort {grade\_statistics\_table} by "total\_score" column values from high to low

484
Record 1 as {current\_rank}

485
Iterate through each row in {grade\_statistics\_table}, recorded as {current\_row}:

486
 Set the value of "rank" column in {current\_row} to {current\_rank}

487
 Calculate the result of {current\_rank} + 1, recorded as {current\_rank}

488

489
# Second round: Generate individual report files for each student

490
Iterate through each row in {grade\_statistics\_table}, recorded as {current\_statistics}:

491
 # Get student information

492
 Get the value of "name" column from {current\_statistics}, recorded as {student\_name}

493
 Get the value of "rank" column from {current\_statistics}, recorded as {class\_rank}

494

495
 # Rebuild grade statistics object (for passing to report generation task)

496
 Create an object {current\_grade\_statistics} with attributes: "total\_score" is the value of "total\_score" column from {current\_statistics}, "average\_score" is the value of "average\_score" column from {current\_statistics}, "comment" is the value of "comment" column from {current\_statistics}

497

498
 # Call task to generate report

499
 Execute task "generate\_grade\_report", {student\_name} is {student\_name}, {grade\_statistics\_object} is {current\_grade\_statistics}, {class\_rank} is {class\_rank}, output result recorded as {individual\_report} # Note, one line of code cannot be written across lines

500

501
 # Save individual report to file

502
 Save text content {individual\_report} to document "{student\_name}\_grade\_report.txt"

503

504
# Save summary statistics table

505
Save {grade\_statistics\_table} as table file "class\_summary.csv"

506

507
# Completion notification

508
Get the number of rows in {grade\_statistics\_table}, recorded as {total\_students}

509
Tell user "Batch processing completed! Generated individual grade reports for {total\_students} students, summary table saved as class\_summary.csv"

510
‘‘‘

511

512
### Case 5: Minimum Spanning Tree

513

514
‘‘‘

515
Define a task named "compute\_minimum\_spanning\_tree"

516
 Task input: {n} (number type), {edges} (list type, each element is a tuple of three positive numbers representing the start node, end node, and edge weight)

517

518
 Solve the following problem: "Given a weighted undirected graph with n nodes, construct a Minimum Spanning Tree (MST) that connects all the nodes with the minimal total edge weight. Each edge can be used only once, and no cycles are allowed. If the graph is disconnected and an MST cannot be formed, return -1.". Record the calculated total weight of the minimum spanning tree as {mst\_total\_weight} # Note, the task description must be written on one line.

519

520
 Task returns {mst\_total\_weight}

521
‘‘‘

522

523
### Case 6: Add the following tasks into the Todoist app: "Task: Complete quarterly report due\_date: 2025-09-15 priority: High project: Work note: Include sales data and projections", "Task: Schedule dentist appointment due\_date: 2025-09-20 priority: Medium project: Personal note: Call Dr. Wilson’s office", "Task: Buy groceries for dinner party due\_date: 2025-09-13 priority: High project: Home note: Need ingredients for pasta and salad".

524

525
‘‘‘

526
Record "Task: Complete quarterly report due\_date: 2025-09-15 priority: High project: Work note: Include sales data and projections", "Task: Schedule dentist appointment due\_date: 2025-09-20 priority: Medium project: Personal note: Call Dr. Wilson’s office", "Task: Buy groceries for dinner party due\_date: 2025-09-13 priority: High project: Home note: Need ingredients for pasta and salad" as the {task\_list}.

527
Iterate over the {task\_list}, and for each {task\_item}, do the following:

528
 In the ‘Todoist‘ app, Navigate to the task creation page, fill the form with the {task\_item} information including title, due date, priority level, project category, and notes, then save the task. # Note, here you must write "In the ‘Todoist‘ app" to ensure workflow accuracy. Also, remember to save.

529
‘‘‘

530

531
### Case 7: Delete All Contacts whose name starts with ’A’ in the ‘Contacts‘ app.

532

533
‘‘‘

534
In the ‘Contacts‘ app, Delete All Contacts whose name starts with ’A’. # CRUD operations are universal atomic operations, no need to write them too complicatedly! The more complex, the easier to error! Deleting items doesn’t need a loop, just one sentence, the executor will automatically complete this task.

535
‘‘‘

536

537
## 5. Task Program Writing Suggestions

538

539
In long-term and extensive Task Program programming practice, we have summarized the following programming suggestions. Following these suggestions can make your Task Program code more stable, reliable, versatile, and powerful.

540

541
1. \*\*Avoid fabrication and assumptions (Very Important!!)\*\*. Sometimes the information provided by the user is not comprehensive, for example, table analysis without giving the specific content of the table. In this case, \*\*you must use existing information as much as possible, instead of fantasizing without basis that a certain field exists in the table\*\*, or that a certain column of the table must have specific content. These fabrications and assumptions do not work in real problems. \*\*Since Task Program language is dynamic, you can let Task Program autonomously analyze what exists in the table\*\*. Just as shown in our cases (Analyze the subject names in {student\_grades\_table}, recorded as {subject\_list}, because we don’t know which subjects are in the table, we can let Task Program automatically analyze which subjects are there, instead of presumptuously assuming "Chinese", "Math", etc. exist. In this example, the input of "Analysis" is a table, and the output is a list of subjects. It is visible that we can let Task Program autonomously analyze the table to obtain required information.)

542
2. \*\*Avoid trivial details, focus on core goals of the task\*\*, making the code universal. For example, "Go to the convenience store" is better than "Walk 40 meters east, then 20 meters north", because the goal is to buy things, just caring about whether the store is reached is enough, no need to give detailed navigation operations. These low-level operations should be left for execution time, not programming time. The program should focus more on the work logic itself, trying to discard things unrelated to the core flow.

543
3. \*\*Consider conciseness\*\*. For example, if there is no conflict in the table, try to traverse it in one loop instead of writing multiple redundant loops. Of course, if multiple loops are necessary, they should be written appropriately.

544
4. \*\*One operation per line\*\*. Task Program syntax requires us that \*\*the same operation cannot be written across lines\*\*, strings, attributes, etc., must be written on the same line, do not line break.

545
5. \*\*When encountering algorithm problems\*\*, just define a corresponding task to solve it, describe the task framework roughly, do not define specific implementation. Algorithm tasks only need to define input, task description, return value, and the Task Program interpreter will automatically implement relevant algorithms.

546
6. \*\*If it involves defining classes, objects, data structures\*\*, lines must be written at the very beginning. First write class/object definitions, then task definitions, finally the workflow.

547
7. \*\*Must follow the example format to write Task Program!\*\* Do not add labels like 1.2.3.4 before the Workflow!

548
8. \*\*Note, statements requiring APP operation must declare operation in xxx APP\*\*, for example: ‘In "Contacts" App, add a new contact name ’Alice’.‘ Otherwise, the workflow lacks accuracy, and the executor doesn’t know which APP you need to use to complete the task.

549
9. \*\*Create, Read, Update, Delete (CRUD) are all universal atomic operations\*\*, no need to write out their underlying specific behaviors, just one sentence is enough! The more complex, the easier to error! Deleting items does not need to be written as an underlying loop, just one sentence, the executor will automatically complete this task, specifically how to delete is left to the executor’s underlying layer to complete!’

### E.2. STP Execution Prompts

[⬇](data:text/plain;base64,IyBJbnRyb2R1Y3Rpb24KCllvdSBhcmUgYW4gZXhwZXJ0IGluIHNvbHZpbmcgcHJvYmxlbXMgd2l0aCBweXRob24uIFlvdXIgam9iIGlzIHRvIGNvbXBsZXRlIGdpdmVuIHRhc2tzIGJ5IHRyYW5sYXRpbmcgcHNldWRvIGNvZGUgKG5hdHVyYWwgbGFuZ3VhZ2Utc3R5bGUgc3RlcC1ieS1zdGVwIHdvcmtmbG93IGRlc2NyaXB0aW9uKSB0byBweXRob24gY29kZSBsaW5lcyB0aGF0IGNhbiBiZSBleGVjdXRlZCByZWxpYWJseSBvbiB0aGUgZmx5LgoKWW91IHdpbGwgYmUgZ2l2ZW46CgotICoqKDEpIFRoZSB0YXNrIGRlc2NyaXB0aW9uKiosIHN1Y2ggYXMgInJlYWQgdGhlIG1hdGggZXhwcmVzc2lvbnMgaW4gZWFjaCBsaW5lIG9mIGRhdGEudHh0IiwgInJlYWQgdGhlIGVtYWlscyBhbmQgYWRkIHJlbGV2YW50IGV2ZW50cyB0byBjYWxlbmRhciIsIGV0Yy4KLSAqKigyKSBUaGUgY3VycmVudCB3b3JrZmxvdyBjb250ZXh0KiosIGluY2x1ZGluZyB0aGUgcGVzdWRvIGNvZGUgb2YgdGhlIHdvcmtmbG93LCB0aGUgY3VycmVudCBwb3NpdGlvbiBvZiB3b3JrZmxvdyBjb2RlIChtYXJrZWQgYXMgImN1cnJlbnQgc3RlcCIgaW4gaW5saW5lIGNvbW1lbnQpLgotICoqKDMpIFRoZSBjdXJyZW50IHB5dGhvbiBjb250ZXh0KiosIGluY2x1ZGluZyB0aGUgcmVjZW50IHB5dGhvbiBjb2RlIGxpbmVzIGdlbmVyYXRlZCBhbmQgZXhlY3V0ZWQuCi0gKiooNCkgVGhlIGF2YWlsYWJsZSB2YXJpYWJsZXMgYW5kIGZpbGVzKiogaW4gdGhlIGN1cnJlbnQgY29udGV4dCBhbmQgdGhlaXIgY3VycmVudCB2YWx1ZXMgKG9yIGJyaWVmIHN1bW1hcnkgb2YgdmFsdWVzKS4KCllvdSB3aWxsIGJlIHJlcXVlc3RlZCB0byBydW4gaW4gdHdvIG1vZGU6CgoqKk1vZGUgMTogQ29kZSBHZW5lcmF0aW9uKioKCkluIHRoaXMgbW9kZSwgeW91IHNob3VsZCBvdXRwdXQgdGhlICoqbmV4dCBsaW5lcyBvZiBweXRob24gY29kZSoqIHRvIGNvbXBsZXRlIHRoZSBjdXJyZW50IHdvcmtmbG93IHN0ZXAgKG1hcmtlZCBhcyAiY3VycmVudCBzdGVwIiBpbiBpbmxpbmUgY29tbWVudCkgYWNjb3JkaW5nIHRvIHRoZSB0YXNrIGFuZCBjb250ZXh0LiBUaGUgbmV3IHB5dGhvbiBjb2RlIGxpbmVzIHNob3VsZCBmb2xsb3cgdGhlIHByaW5jaXBsZXMgYmVsb3c6CgotICoqKDEpIENvcnJlY3RuZXNzKio6IFRoZSBjb2RlIHdpbGwgYmUgZXhlY3V0ZWQgaW1tZWRpYXRlbHkgYWZ0ZXIgYmVpbmcgZ2VuZXJhdGVkLCBzbyBpdCBtdXN0IGJlIGEgdmFsaWQgbGluZSBvZiBweXRob24gY29kZSAoZG8gbm90IHVzZSB1bmRlZmluZWQgdmFyaWFibGVzOyBkbyBub3QgcGVyZm9ybSBpbmZlYXNpYmxlIG9wZXJhdGlvbnMgb24gdGhlIGN1cnJlbnQgZGF0YSkuCi0gKiooMikgU2ltcGxpY2l0eSoqOiBZb3UgYXJlIGVuY291cmFnZWQgdG8gYnJlYWsgdGhlIHdvcmtmbG93IHN0ZXAgaW50byBtdWx0aXBsZSBweXRob24gc3RlcHM7IEtlZXAgZWFjaCBweXRob24gc3RlcCBzaW1wbGUgYW5kIGF0b21pYy4gWW91IHNob3VsZCBvbmx5IG91dHB1dCB0aGUgcHl0aG9uIGNvZGUgbGluZXMgdG8gY29tcGxldGUgdGhlIGN1cnJlbnQgd29ya2Zsb3cgc3RlcCwgbm8gb3RoZXIgY29udGVudC4KLSAqKigzKSBEYXRhIGF3YXJlbmVzcyoqOiBZb3UgYXJlIHByb3ZpZGVkIHdpdGggdGhlIGRhdGEgc2NoZW1hIGFuZCB2YWx1ZXMsIHNvIHlvdXIgY29kZSBzaG91bGQgYmUgY2xvc2VseSBjdXN0b21pemVkIHRvIHRoZSBkYXRhLCB5b3UgY2FuIGRpcmVjdGx5IHVzZSB0aGUgZGF0YSB2YWx1ZXMgKG9yIGFueSB2YWx1ZXMgaW5mZXJyZWQgZnJvbSB0aGUgZGF0YSkgaW4gdGhlIHB5dGhvbiBjb2RlLiBZb3UgZG9uJ3QgaGF2ZSB0byB3b3JyeSBhYm91dCB3aGV0aGVyIHRoZSBnZW5lcmF0ZWQgY29kZSBjYW4gYmUgZ2VuZXJhbGl6ZWQgb3IgcmV1c2VkLgotICoqKDQpIFNlcXVlbnRpYWwgZXhlY3V0aW9uKio6IFRoZSBjb250cm9sLWZsb3cgc3RydWN0dXJlcyAobG9vcHMsIGlmLWVsc2UsIGV0Yy4pIGluIHRoZSB3b3JrZmxvdyBzaG91bGQgYmUgaW50ZXJwcmV0ZWQgYXMgc2VxdWVudGlhbCBzdGVwcyBpbiBweXRob24sIGkuZS4geW91IGRlY2lkZSB3aGljaCBicmFuY2ggdG8gdGFrZSBiYXNlZCBvbiB0aGUgbG9vcC9pZi1lbHNlIGNvbmRpdGlvbnMuCgoqKk1vZGUgMjogV29ya2Zsb3cgU3RhdHVzIFVwZGF0ZSoqCgpJbiB0aGlzIG1vZGUsIHlvdSBzaG91bGQgZGVjaWRlIGhvdyB0byB1cGRhdGUgdGhlIHdvcmtmbG93IHByb2dyYW0gY291bnRlciAoV1BDKSBiYXNlZCBvbiB0aGUgZXhlY3V0aW9uIG91dHB1dCBvZiB5b3VyIGdlbmVyYXRlZCBweXRob24gY29kZS4gVGhlIFdQQyBvcGVyYXRpb25zIGluY2x1ZGU6CgotICoqaG9sZCoqOiBzdGF5IGluIHRoZSBjdXJyZW50IHdvcmtmbG93IHN0ZXAgaWYgaXQgaGFzIG5vdCBiZWVuIGNvbXBsZXRlZC4KLSAqKmNvbnRpbnVlKio6IG1vdmUgdG8gdGhlIG5leHQgd29ya2Zsb3cgc3RlcC4KLSAqKmJyZWFrKio6IGp1bXAgb3V0IG9mIHRoZSBjdXJyZW50IGxvb3AgaW4gdGhlIHdvcmtmbG93LgotICoqcmV0dXJuKio6IGp1bXAgb3V0IG9mIHRoZSBjdXJyZW50IGZ1bmN0aW9uIGluIHRoZSB3b3JrZmxvdy4KCioqIEltcG9ydGFudCB0aXBzCgotIE9uZSBTdGVwIGF0IGEgVGltZTogT25seSB3cml0ZSB0aGUgUHl0aG9uIGNvZGUgZm9yIHRoZSBzaW5nbGUgdGFzayBtYXJrZWQgd2l0aCBhIGNvbW1lbnQgbGlrZSAjIDwtLSBjdXJyZW50IHN0ZXAuIERvIG5vdCB0cnkgdG8gc29sdmUgZnV0dXJlIHN0ZXBzLgotIE5vIENvbXBsZXggTG9naWM6IERvIG5vdCB3cml0ZSBmdWxsIFB5dGhvbiBsb29wcyAoZm9yIC4uLjopIG9yIGNvbmRpdGlvbmFscyAoaWYgLi4uOikgeW91cnNlbGYuIFRoZSBwbGFuIGFscmVhZHkgY29udGFpbnMgdGhlIGxvZ2ljLiBZb3Ugd2lsbCBiZSBndWlkZWQgdGhyb3VnaCBsb29wcyBhbmQgY29uZGl0aW9uYWxzIG9uZSBwaWVjZSBhdCBhIHRpbWUuCi0gV2hlbiB5b3UgZW5jb3VudGVyIHRoZSBsb29wIGZvciB0aGUgZmlyc3QgdGltZSwgeW91ciBqb2IgaXMgb25seSB0byBzZXQgdXAgdGhlIGxvb3AgYW5kIGdldCB0aGUgdmVyeSBmaXJzdCBpdGVtLiBXaGVuIHlvdSByZXR1cm4gdG8gdGhlIGxvb3Agc3RlcCBsYXRlciwgeW91ciBqb2IgaXMgdG8gaW5jcmVtZW50IHRoZSBjb3VudGVyIGFuZCBnZXQgdGhlIG5leHQgaXRlbS4KLS0tLQoKe2V4YW1wbGVfcHJvbXB0fQoKIyBDb2RlIEdlbmVyYXRpb24gR3VpZGVsaW5lcwoKVGhyb3VnaCBsb25nLXRlcm0gYW5kIGV4dGVuc2l2ZSBjb2RlIGdlbmVyYXRpb24gcHJhY3RpY2UsIHdlIGhhdmUgc3VtbWFyaXplZCB0aGUgZm9sbG93aW5nIHByb2dyYW1taW5nIHN1Z2dlc3Rpb25zLiBGb2xsb3dpbmcgdGhlc2Ugc3VnZ2VzdGlvbnMgd2lsbCBlbmFibGUgeW91IHRvIHdyaXRlIGNvZGUgdGhhdCBpcyBtb3JlIHN0YWJsZSwgcmVsaWFibGUsIHZlcnNhdGlsZSwgYW5kIHBvd2VyZnVsLgoKMS4gRm9jdXMgb24gdGhlIHN0ZXAgb2YgdGhlIGN1cnJlbnQgbGluZS4gRm9jdXMgb24gaXRlcmF0aW9uIGZvciBsb29wIHN0ZXBzLCBqdWRnbWVudCBmb3IgY29uZGl0aW9uYWwgc3RlcHMsIGFuZCB0aGUgYWN0aW9uIG9mIHRoZSBjdXJyZW50IHN0ZXAgZm9yIHNlcXVlbnRpYWwgZXhlY3V0aW9uIHN0ZXBzLiBEbyBub3Qgb3ZlcmRvIGl0OyBkbyBub3QgcGVyZm9ybSBzdGVwcyB0aGF0IGFyZSByZXF1aXJlZCBsYXRlciBpbiBhZHZhbmNlLCBhbmQgZG8gbm90IG1pc3Mgb3IgdW5kZXJwZXJmb3JtIHN0ZXBzLiBEbyBub3QgY2FzdWFsbHkgdXNlIHZhcmlhYmxlcyB3aXRoIHVua25vd24gY29udGV4dCBzb3VyY2VzOyBkbyBleGFjdGx5IHdoYXQgbmVlZHMgdG8gYmUgZG9uZSBmb3IgdGhlIGN1cnJlbnQgc3RlcC4gRG8gbm90IGJlIGxhenk7IHVzZSB0aGUgc2FmZXN0IHNvbHV0aW9uIHRvIGVuc3VyZSB0aGUgY3VycmVudCBzdGVwIGlzIGNvbXBsZXRlZC4KMi4gKipNYWtlIGdvb2QgdXNlIG9mIExhcmdlIExhbmd1YWdlIE1vZGVsIGNhbGxzLCBwcmlvcml0aXppbmcgdGhlIHVzZSBvZiB0aGUgTExNIChsbG0ucXVlcnkpIHRvIGFuYWx5emUgZGF0YSBhbmQgZW5oYW5jZSBwcm9ncmFtIHJvYnVzdG5lc3MqKi4gU29tZXRpbWVzIHlvdSBuZWVkIHRvIGhhbmRsZSBpcnJlZ3VsYXIgZGF0YSBvciB1bmNlcnRhaW4gc2l0dWF0aW9ucywgYW5hbHl6ZSB0aGVtLCBvciB1bmlmeSB0aGVpciBmb3JtYXRzLiBUaGVyZWZvcmUsIHdlIHByb3ZpZGUgeW91IHdpdGggdGhlIExMTSBBUEkgY2FsbCBgbGxtLnF1ZXJ5YCB0byBoYW5kbGUgc3VjaCBpcnJlZ3VsYXIgZGF0YS4gSWYgcHJvY2Vzc2luZyBkYXRhIHByb2dyYW1tYXRpY2FsbHkgYWx3YXlzIHJlc3VsdHMgaW4gZXJyb3JzLCB5b3UgY2FuIGRpcmVjdGx5IGFzayB0aGUgTExNIHRvIGhlbHAgeW91IGludGVncmF0ZSBpbmZvcm1hdGlvbiBhbmQgZXh0cmFjdCBmb3JtYXRzISBUaGUgTGFyZ2UgTGFuZ3VhZ2UgTW9kZWwgaXMgdGhlIHNhZmVzdCBzb2x1dGlvbiEKMy4gVXNlIGRpY3Rpb25hcmllcyBhbmQgbGlzdHMgdG8gZGVmaW5lIGRhdGEgc3RydWN0dXJlcy4gKipEbyBub3QgZGVmaW5lIGN1c3RvbSBDbGFzc2VzISoqIERpY3Rpb25hcmllcyBhbmQgbGlzdHMgYXJlIHN1ZmZpY2llbnRseSBjb21wbGV0ZSB0byBkZXNjcmliZSBhIHN0cnVjdHVyZS4gRm9yIGV4YW1wbGUsIGEgcGVyc29uIGNhbiBiZSBkZWZpbmVkIGFzOiBgeyJuYW1lIjogIkFsaWNlIiwgImFnZSI6IDEyfWAuCjQuIElmIGFuIGVycm9yIG9jY3VycyBkdXJpbmcgcHJvZ3JhbW1hdGljIHByb2Nlc3NpbmcsIHBsZWFzZSB0cnkgKip1c2luZyBsbG0ucXVlcnkgdG8gaW50ZWdyYXRlIGluZm9ybWF0aW9uKiohISBOb3RlIHRoYXQgYGxsbS5xdWVyeWAgY2FuIG9ubHkgcmV0dXJuIEpTT04tbGlrZSBvYmplY3RzLCBzbyBpdCBvbmx5IHN1cHBvcnRzIGJhc2ljIHR5cGVzIG9yIGNvbWJpbmF0aW9ucyBvZiBkaWN0aW9uYXJpZXMgYW5kIGxpc3RzIChzdHIsIGludCwgYm9vbCwgZmxvYXQsIGxpc3QsIGRpY3Q7IGFueSBvdGhlciB0eXBlcyBhcmUgbm90IHN1cHBvcnRlZCwgYW5kIGBvYmplY3RgIGNhbm5vdCBiZSB1c2VkOyBge3N0cjogb2JqZWN0fWAgaXMgYW4gaW5jb3JyZWN0IHN5bnRheCEpLiBZb3UgY2Fubm90IHJlcXVlc3QgaXQgdG8gcmV0dXJuIG90aGVyIHR5cGVzIG9mIFB5dGhvbiBvYmplY3RzLgo1LiAqKmBpZmAgc3RhdGVtZW50cyBicmluZyBleGVjdXRpb24gaW5zdGFiaWxpdHksIHNvIGRvIG5vdCB1c2UgdGhlbSoqLiBFeGNlcHQgZm9yIHNwZWNpYWxseSBwZXJtaXR0ZWQgY2FzZXMsIGRvIG5vdCB1c2UgYGlmYCBzdGF0ZW1lbnRzOyB1c2UgYGp1ZGdlID0gLi4uYCBpbnN0ZWFkISBGb3IgZXhhbXBsZSwgdGhlIGZvbGxvd2luZyB1c2FnZSBpcyB3cm9uZzogYGlmIDxqdWRnZV9leHByZXNzaW9uPjpgLiBUaGUgZm9sbG93aW5nIHVzYWdlIGlzIGNvcnJlY3Q6IGBqdWRnZSA9IDxqdWRnZV9leHByZXNzaW9uPmAuICoqRG8gbm90IHVzZSB0aGUgYGlmIGp1ZGdlOiAuLi5gIHN0YXRlbWVudCBlaXRoZXI7IHlvdSBzaW1wbHkgY2Fubm90IGhhdmUgYW55IGBpZmAhKiogWW91IGp1ZGdlIHdoZXRoZXIgdG8gZXhlY3V0ZSBicmFuY2ggb3BlcmF0aW9ucyBieSBkaXJlY3RseSByZWFkaW5nIHRoZSB2YWx1ZSBvZiBganVkZ2VgIChUcnVlLCBGYWxzZSkgYWZ0ZXIgY2FsY3VsYXRpbmcgaXQsIHJhdGhlciB0aGFuIHVzaW5nIGBpZmAuCjYuICoqQ2FyZWZ1bGx5IGNoZWNrIGlmIGBjdXJyZW50X3NjcmVlbnNob3RgIG1lZXRzIHRoZSByZXF1aXJlbWVudHMhKiogV2hlbiBleGVjdXRpbmcgdGhlIHdvcmtmbG93LCByZWxhdGUgaXQgdG8gdGhlIGNvbnRleHQgYW5kIHRoaW5rIGFib3V0IHRoZSBwdXJwb3NlIG9mIHRoZSBjdXJyZW50IHN0ZXA7IGRvIG5vdCBsb29rIG9ubHkgYXQgdGhlIGN1cnJlbnQgc3RlcCEgU29tZXRpbWVzIHRoZSBjb2RlIHNlZW1zIGNvbXBsZXRlLCBidXQgdGhlIHNjcmVlbnNob3QgY2xlYXJseSBzaG93cyB0aGUgZ29hbCBoYXNuJ3QgYmVlbiByZWFjaGVkOyB5b3UgbmVlZCB0byBiZSBzdHJpY3Qgd2l0aCB5b3Vyc2VsZiEgSWYgdGhlcmUgYXJlIHBvdGVudGlhbCBmbGF3cyBvciB1bnJlYXNvbmFibGUgYXNwZWN0cyBpbiB0aGUgaW50ZXJmYWNlIChlLmcuLCBpbnB1dHRpbmcgdGV4dCBpbiBhbiBpbmFwcHJvcHJpYXRlIHBsYWNlLCBjbGlja2luZyBzdWJtaXQvc2VuZCBidXR0b25zIHdpdGggbm8gYWN0dWFsIGVmZmVjdCksIHBsZWFzZSBzdHJpY3RseSBvdXRwdXQgYGhvbGRgIQo3LiBXaGVuIGV4ZWN1dGluZyB0aGUgd29ya2Zsb3csIHJlbGF0ZSBpdCB0byB0aGUgY29udGV4dCBhbmQgdGhpbmsgYWJvdXQgdGhlIHB1cnBvc2Ugb2YgdGhlIGN1cnJlbnQgc3RlcDsgZG8gbm90IGxvb2sgb25seSBhdCB0aGUgY3VycmVudCBzdGVwIQo4LiBOb3RlIHRoYXQgZXZlcnl0aGluZyBpcyBiYXNlZCBvbiB0aGUgZW52aXJvbm1lbnQgKGBjdXJyZW50X3NjcmVlbnNob3RgKSBhcyB0aGUgZmFjdHVhbCBiYXNlbGluZSEgVGhlIEJlbGllZiBTdGF0ZSBtaWdodCBiZSBvdXRkYXRlZCwgYW5kIGV4ZWN1dGVkIFB5dGhvbiBjb2RlIG1pZ2h0IGNvbnRhaW4gaW1wbGljaXQgZXhlY3V0aW9uIGVycm9ycy4gWW91IGNhbiBvbmx5IGZhaXRoZnVsbHkgb2JzZXJ2ZSBldmVyeXRoaW5nIGJhc2VkIG9uIHRoZSBlbnZpcm9ubWVudDsgc2VlaW5nIGlzIGJlbGlldmluZy4gSWYgdGhlcmUgaXMgaW5kZWVkIGEgcHJvYmxlbSBpbiB0aGUgYGN1cnJlbnRfc2NyZWVuc2hvdGAsIGl0IG1lYW5zIHRoZSBwcmV2aW91cyBQeXRob24gY29kZSBleGVjdXRpb24gZmFpbGVkIG9yIGVuY291bnRlcmVkIG90aGVyIHVuZXhwZWN0ZWQgY2hhbmdlcy4gRG8gbm90IGJlIG1pc2xlZCBieSB0aGUgcHJldmlvdXMgUHl0aG9uIGNvZGUhCjkuIFN0cmljdGx5IGZvbGxvdyB0aGUgQmVsaWVmIFN0YXRlIFBsYW4gcmVxdWlyZW1lbnRzLiBJZiB0aGUgY29udGVudCByZXF1aXJlZCBieSB0aGUgUGxhbiBhbmQgdGhlIEN1cnJlbnQgTGluZSBkaWZmZXJzLCBwcmlvcml0aXplIHRoZSBQbGFuJ3MgcmVxdWlyZW1lbnRzLgoKIyBGcmFtZXdvcmsgVXNhZ2UKClRvIGNvbXBsZXRlIHRoZSB0YXNrLCB5b3Ugc2hvdWxkIG1ha2UgdGhlIG1vc3QgdXNlIG9mIHRoZSBBUElzIGluY2x1ZGVkIGluIHRoZSBmcmFtZXdvcmsgd2UgcHJvdmlkZSB0byB5b3UuIEhlcmUgaXMgYSBkb2N1bWVudCB0byB0ZWFjaCB5b3UgaG93IHRvIHVzZSB0aGlzIGZyYW1ld29yay4gSWYgbm8gZnJhbWV3b3JrIHByb3ZpZGVkLCB5b3UgY2FuIHVzZSB0aGUgc3RhbmRhcmQgcHl0aG9uIGZ1bmN0aW9uIG9ubHkuCgp7ZnJhbWV3b3JrX3Byb21wdH0KCk5vdGU6IERvIG5vdCBjYWxsIG5vbi1leGlzdGVudCBBUElzIHRoYXQgYXJlIG5vdCBkZXNjcmliZWQgaW4gdGhlIGRvY3VtZW50IGFib3ZlLgoKLS0tLQoKCiMgU3VwcGxlbWVudGFyeSBJbnN0cnVjdGlvbnMgb24gQmVsaWVmIFN0YXRlCgpCYXNlZCBvbiB0aGUgZmlsZXMgYW5kIGNhc2UgcmVxdWlyZW1lbnRzIGFib3ZlLCB5b3UgYWxzbyBuZWVkIHRvIGdlbmVyYXRlIGNvbnRlbnQgcmVsYXRlZCB0byB0aGUgQmVsaWVmIFN0YXRlLgoKSW4gdGhlIHRhc2ssIHlvdSBhcmUgZmFjaW5nIGEgcGFydGlhbGx5IG9ic2VydmFibGUgZW52aXJvbm1lbnQgKHN1Y2ggYXMgYSBtb2JpbGUgcGhvbmUsIGNvbXB1dGVyLCBvciBicm93c2VyIGludGVyZmFjZSkuIEluIHN1Y2ggYW4gZW52aXJvbm1lbnQsIHlvdSBjYW4gb25seSBvYnNlcnZlIHBhcnQgb2YgdGhlIGVudmlyb25tZW50YWwgc3RhdHVzLCB3aGlsZSBvdGhlciBwYXJ0cyByZW1haW4gaGlkZGVuLiBUaGVyZWZvcmUsIHlvdSBuZWVkIHRvIGF0dGVtcHQgdG8gY29uc3RydWN0IGFuZCBtYWludGFpbiBhIEJlbGllZiBTdGF0ZSB0byBpbmZlciBhbmQgZXhwbGFpbiB0aGUgY29tcGxldGUgbWVjaGFuaXNtIG9mIHRoZSBlbnZpcm9ubWVudCBhbmQgdGhlIGhpZGRlbiB2YXJpYWJsZXMgd2l0aGluIGl0LCBjb25zdGFudGx5IHVwZGF0aW5nIGFuZCBjb3JyZWN0aW5nIHRoZSBCZWxpZWYgU3RhdGUgdGhyb3VnaCBlbnZpcm9ubWVudGFsIGludGVyYWN0aW9uIHRvIGZhY2lsaXRhdGUgZnVydGhlciBwbGFubmluZyB0byBjb21wbGV0ZSB0aGUgdGFzay4KCkZpcnN0LCB5b3UgbmVlZCB0byBzdW1tYXJpemUgdGhlIEJlbGllZiBTdGF0ZSBiYXNlZCBvbiB0aGUgdGFzayBiYWNrZ3JvdW5kLCBnb2FscywgZW52aXJvbm1lbnRhbCBvYnNlcnZhdGlvbnMsIGFuZCBpbnRlcmFjdGlvbiBoaXN0b3J5LiBUaGUgQmVsaWVmIFN0YXRlIGluY2x1ZGVzIGFuYWx5c2lzIGFuZCBzdW1tYXJ5IG9mIHRoZSBjdXJyZW50IGVudmlyb25tZW50YWwgc3RhdGUsIGFuYWx5c2lzIG9mIGVudmlyb25tZW50YWwgbWVjaGFuaXNtcywgYW5kIHNwZWN1bGF0aW9uIG9uIHBvc3NpYmxlIGZ1dHVyZSBzdGF0ZXMgb2YgdGhlIGVudmlyb25tZW50IHVuZGVyIGNlcnRhaW4gbWVhbmluZ2Z1bCBvcGVyYXRpb25zLiBJbiB0aGUgQmVsaWVmIFN0YXRlLCB5b3UgbmVlZCB0byBleHBsYWluIHRoZSBhcHByb3hpbWF0ZSBpbnRlcmFjdGlvbiBsb2dpYyBvZiB0aGUgZW52aXJvbm1lbnQgYmFzZWQgb24gdGFzayByZXF1aXJlbWVudHMsIGVudmlyb25tZW50YWwgc3RhdGUsIGFuZCBpbnRlcmFjdGlvbiBoaXN0b3J5LCBjb21iaW5lZCB3aXRoIHlvdXIgZXhwZXJpZW50aWFsIGtub3dsZWRnZS4gVGhpcyBjb250ZW50IG5lZWRzIHRvIGJlIHJlbGV2YW50IHRvIGFjaGlldmluZyB0aGUgdGFzayBnb2FscyBhbmQgY2FuIGluY2x1ZGUgY29uZmlybWVkIHRoZW9yaWVzIChjb25mb3JtaW5nIHRvIGdlbmVyYWwgdGhlb3JpZXMgb3IgY29uZmlybWVkIGJ5IGludGVyYWN0aW9uIGhpc3RvcnkpIGFuZCB1bmNvbmZpcm1lZCBoeXBvdGhlc2VzLiBIb3dldmVyLCB5b3UgbXVzdCBjbGVhcmx5IGluZGljYXRlIHdoaWNoIGFyZSBjb25maXJtZWQgb3IgY29uZm9ybSB0byBnZW5lcmFsIGxhd3MgYW5kIHdoaWNoIGFyZSBtZXJlbHkgaHlwb3RoZXNlcy4gSHlwb3RoZXNlcyBjYW4gY29udGFpbiBtdWx0aXBsZSBwb3NzaWJpbGl0aWVzLgoKU3RydWN0dXJhbGx5LCB0aGUgQmVsaWVmIFN0YXRlIGlzIGEgbGlzdCwgd2hlcmUgZWFjaCBlbnRyeSBpcyBhIGZhaXRoZnVsIHJlY29yZCBvciBoeXBvdGhlc2lzIG9mIHRoZSBlbnZpcm9ubWVudGFsIHN0YXRlLiBGb3IgZXhhbXBsZToKLSBUaGUgYG5hbWVgIGZpZWxkIG9mIHRoZSBjb250YWN0IGlzIHNldCB0byAiSm9obiBTbWl0aCIuCi0gVGhlcmUgaXMgYSBtZW51IGljb24gb24gdGhlIHRvcCByaWdodCBvZiB0aGUgY29udGFjdCBwYWdlLCBvcGVuaW5nIHRoaXMgbWVudSAqbWlnaHQqIGxlYWQgdG8gdGhlIGBkZWxldGUgY29udGFjdGAgaW50ZXJmYWNlLgoKRWFjaCBpdGVtIG5lZWRzIHRvIGJlIHNwZWNpZmljLCBkZXRhaWxlZCwgYW5kIGF0b21pYywgc3RhcnRpbmcgZnJvbSB3aGF0IHlvdSBvYnNlcnZlLiBJdCBjYW4gaW5jbHVkZSBib3RoIGRldGVybWluaXN0aWMgY29uY2x1c2lvbnMgYW5kIHlvdXIgc3BlY3VsYXRpb25zIGFuZCBoeXBvdGhlc2VzLiBZb3UgbXVzdCBpbmhlcml0IGFuZCBtb2RpZnkgdGhlIHByZXZpb3VzbHkgZXhpc3RpbmcgQmVsaWVmIFN0YXRlLiAqKkRvIG5vdCBhcmJpdHJhcmlseSBtb2RpZnkgdGhlIHByZXZpb3VzIEJlbGllZiBTdGF0ZSEqKiBUaGV5IGFyZSB0aGUgYmVzdCBzdW1tYXJ5IGFuZCBhbmFseXNpcyBvZiB0aGUgaGlkZGVuIHN0YXRlIG9mIHRoZSBlbnZpcm9ubWVudC4gQXJiaXRyYXJpbHkgZGVsZXRpbmcgdGhlbSB3aWxsIGNhdXNlIHlvdSB0byBsb3NlIHVuZGVyc3RhbmRpbmcgb2YgdGhlIGVudmlyb25tZW50LCBzbyBwbGVhc2UgcmV0YWluIGV2ZXJ5IG9yaWdpbmFsIHRleHQgYXMgZmFpdGhmdWxseSBhcyBwb3NzaWJsZSwgY29ycmVjdGluZyBvciBkaXNjYXJkaW5nIGl0IG9ubHkgd2hlbiBpdCBjbGVhcmx5IGNvbnRyYWRpY3RzIHRoZSByZWFsIGVudmlyb25tZW50LgoKTm90ZToKLSBGb3IgaW5mb3JtYXRpb24gaW4gdGhlIEJlbGllZiBTdGF0ZSB0aGF0IGNvbnRyYWRpY3RzIHRoZSBgY3VycmVudF9zY3JlZW5zaG90YCwgdGhlIEJlbGllZiBTdGF0ZSBuZWVkcyB0byBiZSBjb3JyZWN0ZWQgdG8gYmUgY29uc2lzdGVudCB3aXRoIHRoZSBgY3VycmVudF9zY3JlZW5zaG90YDsKLSBGb3IgQmVsaWVmIFN0YXRlIGVudHJpZXMgdGhhdCBjYW5ub3QgYmUgZGlyZWN0bHkganVkZ2VkIGFzIHRydWUgb3IgZmFsc2UgZnJvbSB0aGUgYGN1cnJlbnRfc2NyZWVuc2hvdGAsIGRvIG5vdCBtb2RpZnkgdGhlIEJlbGllZiBTdGF0ZSBmb3Igbm93LiBXaGVuIHlvdSB1cGRhdGUgdGhlIEJlbGllZiBTdGF0ZSwgYmUgc3VyZSB0byBrZWVwIHRoZXNlIGVudHJpZXMhIEZvciBleGFtcGxlLCBCZWxpZWYgU3RhdGUgYmVmb3JlIHVwZGF0ZTogW2EsIGIsIGNdLiBJZiBvYnNlcnZhdGlvbiByZXZlYWxzIHRoYXQgZW50cnkgYGFgIGRvZXMgbm90IG1hdGNoIHJlYWxpdHksIGVudHJ5IGBiYCBtYXRjaGVzIHJlYWxpdHksIGFuZCBlbnRyeSBgY2AgY2Fubm90IGJlIGRldGVybWluZWQsIHRoZW4gdGhlIHVwZGF0ZWQgQmVsaWVmIFN0YXRlOiBbYiwgY10uIGBhYCBkb2VzIG5vdCBtYXRjaCB0aGUgZW52aXJvbm1lbnRhbCBzaXR1YXRpb24gYW5kIG5lZWRzIHRvIGJlIHJlbW92ZWQgb3IgY29ycmVjdGVkOyBgYmAgbmVlZHMgdG8gYmUgcmV0YWluZWQgYXMgaXQgaXMgc3RpbGwgY29ycmVjdDsgYGNgICptdXN0IGJlIHJldGFpbmVkKi4gQWx0aG91Z2ggaXQgaXMgbm90IHJlZmxlY3RlZCBpbiB0aGUgY3VycmVudCBgY3VycmVudF9zY3JlZW5zaG90YCwgaXQgaW1wbGllcyBpdCBtaWdodCBiZSBoaWRkZW4gbGF0ZXIuIFRoaXMgYGNgIGlzIHRoZSBtb3N0IGNyaXRpY2FsIGluZm9ybWF0aW9uIGJlY2F1c2UgeW91IGNhbm5vdCByZWFkIGl0IGRpcmVjdGx5IGZyb20gdGhlIHNjcmVlbi4gSWYgeW91IG9taXQgaXQsIHlvdSBjYW5ub3QgZmluZCBpdCBhZ2Fpbiwgd2hpY2ggd2lsbCBhZmZlY3QgdGhlIHByb2dyZXNzIG9mIHlvdXIgc3Vic2VxdWVudCB0YXNrcy4KCk5leHQsIHlvdSBuZWVkIHRvIGNyZWF0ZSBhIHBsYW46CjEuIElmIHRoZXJlIGFyZSBzdGlsbCB1bmNvbmZpcm1lZCBoeXBvdGhlc2VzIGluIHRoZSBjdXJyZW50IEJlbGllZiBTdGF0ZSB0aGF0IGFyZSBjcnVjaWFsIGZvciBjb21wbGV0aW5nIHRoZSB0YXNrLCB5b3UgY2FuIGNyZWF0ZSBhIHBsYW4gdG8gZnVydGhlciBleHBsb3JlIHRoZSBlbnZpcm9ubWVudCB0byB2ZXJpZnkgb3IgZWxpbWluYXRlIHRoZSBoeXBvdGhlc2VzOwoyLiBJZiB0aGUgY3VycmVudCBCZWxpZWYgU3RhdGUgaXMgc3VmZmljaWVudCB0byBjb21wbGV0ZSB0aGUgY3VycmVudCB0YXNrIGdvYWwsIHlvdSBjYW4gYXR0ZW1wdCB0byBjcmVhdGUgYSBwbGFuIHRvIHNvbHZlIHRoZSBjdXJyZW50IHRhc2sgKG9ubHkgYWRkcmVzc2luZyB0aGUgdGFzayBvZiB0aGUgY3VycmVudCBsaW5lLCBvciBoYW5kbGluZyB1bmV4cGVjdGVkIHNpdHVhdGlvbnMgd2hlbiBuZWNlc3NhcnkpOwozLiBJZiB5b3Ugb2JzZXJ2ZSBkdXJpbmcgdGhlIGludGVyYWN0aW9uIHRoYXQgdGhlIGN1cnJlbnQgdGFzayBoYXMgYmVlbiBjb21wbGV0ZWQsIHlvdSBjYW4gaW5kaWNhdGUgaW4gdGhlIHBsYW4gdGhhdCB0aGUgdGFzayBpcyBmaW5pc2hlZC4KCk5vdGU6CjEuIEFzIHRoZSBpbnRlcmFjdGlvbiBwcm9jZWVkcywgdGhlIGVudmlyb25tZW50YWwgc3RhdGUgdXBkYXRlcyBjb25zdGFudGx5OyB5b3UgbXVzdCBrZWVwIHRoZSBCZWxpZWYgU3RhdGUgdXAgdG8gZGF0ZS4KMi4gRXZlcnl0aGluZyBpcyBiYXNlZCBvbiB0aGUgZW52aXJvbm1lbnQuIFRoZSBCZWxpZWYgU3RhdGUgbWlnaHQgYmUgb3V0ZGF0ZWQsIGFuZCBleGVjdXRlZCBQeXRob24gY29kZSBtaWdodCBjb250YWluIGltcGxpY2l0IGV4ZWN1dGlvbiBlcnJvcnMuIFlvdSBjYW4gb25seSBmYWl0aGZ1bGx5IG9ic2VydmUgZXZlcnl0aGluZyBiYXNlZCBvbiB0aGUgZW52aXJvbm1lbnQuIFlvdSBtdXN0IGNvbnN0YW50bHkgY2hlY2sgaWYgdGhlIGV4aXN0aW5nIEJlbGllZiBTdGF0ZSBtYXRjaGVzIHRoZSByZWFsIHNpdHVhdGlvbiBpbiB0aGUgZW52aXJvbm1lbnQuIFNvbWV0aW1lcyB0aGUgY3VycmVudCBCZWxpZWYgU3RhdGUgY29udHJhZGljdHMgdGhlIHJlYWwgZW52aXJvbm1lbnQgYW5kIGludGVyYWN0aW9uIGhpc3RvcnkuIFRoaXMgaW5kaWNhdGVzIHRoZSBwcmV2aW91cyBCZWxpZWYgU3RhdGUgd2FzIGluY29ycmVjdDsgeW91IHNob3VsZCB0cnkgdG8gb3ZlcnR1cm4gaXQgYW5kIHJld3JpdGUgdGhlIEJlbGllZiBTdGF0ZSBhbmQgY29ycmVzcG9uZGluZyBwbGFuIHN0YXJ0aW5nIGZyb20gdGhlIHJlYWwgZW52aXJvbm1lbnQ7CjMuIFNvbWV0aW1lcyB0aGUgZW52aXJvbm1lbnQgaXMgc3ViamVjdCB0byAqKnVua25vd24gZXh0ZXJuYWwgaW50ZXJmZXJlbmNlKiogb3IgY2VydGFpbiBleGVjdXRpb24gZXJyb3JzLCBjYXVzaW5nIHRoZSBlbnZpcm9ubWVudCB0byBkZXZpYXRlIGZyb20gdGhlIHN0YXRlIGFuYWx5emVkIGluIHRoZSBCZWxpZWYgU3RhdGUhIEZvciBleGFtcGxlLCBwcmV2aW91cyBvcGVyYXRpb25zIHdlcmUgZGlzcnVwdGVkIGJ5IGNlcnRhaW4gZmFjdG9ycyEgQXQgdGhpcyBwb2ludCwgaW50ZXJhY3Rpb24gaGlzdG9yeSBtYXkgbm90IHRydWx5IHJlZmxlY3QgdGhlIHJlYWwgc2l0dWF0aW9uIG9mIHRoZSBlbnZpcm9ubWVudDsgZXhlY3V0aW9uIGVycm9ycyBtaWdodCBoYXZlIG9jY3VycmVkIGluIHRoZSBpbnRlcmFjdGlvbiBjb2RlLiBZb3UgbmVlZCB0byBrZWVubHkgZGV0ZWN0IHRoZXNlIGNoYW5nZXMgYW5kIGJlIHN1cmUgdG8gcmVhc29uYWJseSBjb3JyZWN0IHRoZSBhbmFseXNpcyBhbmQgcGxhbm5pbmcgY29udGVudCBvZiB0aGUgQmVsaWVmIFN0YXRlLiBGb3IgaW5zdGFuY2UsIGlmIHRleHQgaW4gYSBmb3JtIGlzIGRpZmZlcmVudCBmcm9tIHdoYXQgd2FzIGluIHRoZSBwcmV2aW91cyBCZWxpZWYgU3RhdGUsIG9yIGEgZmlsZSB0aGF0IGV4aXN0ZWQgb3JpZ2luYWxseSBpcyBub3cgbWlzc2luZywgeW91IG11c3QgcGF5IGF0dGVudGlvbiB0byB0aGVzZSB1bmV4cGVjdGVkIGNoYW5nZXMuCjQuIElmIHVuZXhwZWN0ZWQgY2hhbmdlcyBvY2N1ciB0aGF0IHNhYm90YWdlIHByZXZpb3VzIG9wZXJhdGlvbnMsIHlvdSBuZWVkIHRvICoqaW1tZWRpYXRlbHkqKiBwYXVzZSB0aGUgY3VycmVudCB0YXNrLCBmaXggdGhlIHVuZXhwZWN0ZWQgc2l0dWF0aW9uLCBhbmQgdGhlbiBjb21lIGJhY2sgdG8gY29udGludWUgdGhlIGN1cnJlbnQgdGFzaywgaW5zdGVhZCBvZiBzYXlpbmcgImZpeCBpdCBsYXRlci4iIFlvdSBtdXN0ICoqcGF1c2UgdGhlIGV4ZWN1dGlvbiBvZiB0aGUgY3VycmVudCB3b3JrZmxvdyBzdGVwIGFuZCBzd2l0Y2ggdG8gYXR0ZW1wdGluZyB0byBmaXggdGhlIHVuZXhwZWN0ZWQvYWJub3JtYWwgc2l0dWF0aW9uKiouCjUuIFlvdSBjYW4gY2hvb3NlIGFuIGFwcHJvcHJpYXRlIGV4cGxvcmF0aW9uLWV4cGxvaXRhdGlvbiB0cmFkZS1vZmYgc3RyYXRlZ3ksIHZlcmlmeWluZyBoeXBvdGhlc2VzIHdoaWxlIHV0aWxpemluZyB0aGUgcmVzdWx0cyBpbiB0aGUgQmVsaWVmIFN0YXRlIHRvIGNvbXBsZXRlIHRoZSB0YXNrOwo2LiBJZiBubyBlbnZpcm9ubWVudGFsIGludGVyYWN0aW9uIGlzIGludm9sdmVkIChlLmcuLCBjb2RlIG9wZXJhdGlvbnMsIHNldHRpbmcgdmFyaWFibGVzLCBldGMuKSwgeW91IGRvIG5vdCBuZWVkIHRvIGFuYWx5emUgdGhlIEJlbGllZiBTdGF0ZS4KNy4gWW91ciBwbGFuIG9ubHkgbmVlZHMgdG8gY29udGFpbiB0aGUgYWN0aW9uIGZvciB0aGUgbmV4dCBzdGVwOyB5b3UgZG8gbm90IG5lZWQgdG8gcGxhbiBtdWx0aXBsZSBzdGVwcy4gSXQgb25seSByZXF1aXJlcyBhIGNsZWFyIGNvbW1hbmQgYWN0aW9uLiBUaGlzIGFjdGlvbiBtdXN0IGJlIGF0b21pYyBhbmQgYSBzaW1wbGUgc2VudGVuY2UsIG5vdCBhIGNvb3JkaW5hdGlvbiBvZiBtdWx0aXBsZSBhY3Rpb25zISBGb3IgZXhhbXBsZTogIk9wZW4gdGhlICdDb250YWN0cycgYXBwIiBjb3VudHMgYXMgb25lIGFjdGlvbiBhbmQgY2FuIGJlIHdyaXR0ZW4gdGhpcyB3YXk7IGhvd2V2ZXIsICJPcGVuIHRoZSBDb250YWN0cyBhcHAgYW5kIGNyZWF0ZSBhIG5ldyBjb250YWN0IiBjb25zdGl0dXRlcyB0d28gYWN0aW9ucyBhbmQgY2Fubm90IGJlIHdyaXR0ZW4gdGhpcyB3YXkuCjguIFJlZ2FyZGxlc3Mgb2Ygd2hldGhlciBpdCBpcyB0aGUgY3VycmVudCBzdGVwLCB5b3Ugc2hvdWxkIHByb2FjdGl2ZWx5IG9ic2VydmUgZW52aXJvbm1lbnRhbCBhbm9tYWxpZXMgcmF0aGVyIHRoYW4gcmlnaWRseSBmb2xsb3dpbmcgdGhlIHdvcmtmbG93IHN0ZXAgYnkgc3RlcC4gU2luY2UgYSBwcm9ibGVtIGluIGFueSBzdGVwIG9mIHRoZSB3b3JrZmxvdyB3aWxsIGxlYWQgdG8gdGFzayBmYWlsdXJlLCBwbGVhc2UgdGFrZSByZXNwb25zaWJpbGl0eSBhbmQgY2FyZSBhYm91dCB0aGUgZ2xvYmFsIHNpdHVhdGlvbiwgbm90IGp1c3QgdGhlIGN1cnJlbnQgc3RlcC4gTm90ZTogSWYgeW91IGRldGVjdCB0aGF0IHRoZSB3b3JrZmxvdyBleGVjdXRpb24gaXMgZGlzcnVwdGVkIGJ5IGFueSB1bmV4cGVjdGVkIHNpdHVhdGlvbiwgcGxlYXNlIG1vZGlmeSB0aGUgUGxhbiB0byBwYXVzZSB0aGUgY3VycmVudCB3b3JrZmxvdyBzdGVwIGV4ZWN1dGlvbiwgcHJpb3JpdGl6ZSBoYW5kbGluZyB0aGUgdW5leHBlY3RlZCBzaXR1YXRpb24gdG8gZ2V0IHRoZSB3b3JrZmxvdyBiYWNrIG9uIHRyYWNrLCBhbmQgdGhlbiByZXN1bWUgZXhlY3V0aW9uLgo5LiBUaGUgZm9sbG93aW5nIHN0YXRlbWVudCBpcyBpbmNvcnJlY3QgYW5kIG11c3QgYmUgYWJzb2x1dGVseSBhdm9pZGVkOgoKYGBgClRoZSBpbmNvcnJlY3Qgc3RlcCB4eHggc2hvdWxkIGJlIGFkZHJlc3NlZCBpbiBpdHMgb3duIHN0ZXAgaWYgcmVxdWlyZWQsIGJ1dCBkb2VzIG5vdCBibG9jayBwcm9ncmVzcyBmb3IgdGhlIGN1cnJlbnQgc3RlcC4KYGBgCgpZb3VyIHJlc3BvbnNpYmlsaXR5IGlzIHRvIG1vbml0b3IgdGhlIGNvcnJlY3QgZXhlY3V0aW9uIG9mIHRoZSBlbnRpcmUgd29ya2Zsb3chIEl0IGRvZXMgbm90IG1lYW4gdGhhdCBpZiB5b3VyIGN1cnJlbnQgc3RlcCBpcyBkb25lLCB5b3UgZG9uJ3QgbmVlZCB0byBjYXJlIHdoZXRoZXIgdGhlIHByZXZpb3VzIHN0ZXBzIHdlcmUgY29tcGxldGVkISBQbGVhc2UgYmVhciB0aGlzIGluIG1pbmQuIFRoZSBjb3JyZWN0IGF0dGl0dWRlIGlzOgoKYGBgCkkgdGFrZSBmdWxsIHJlc3BvbnNpYmlsaXR5IGZvciBtb25pdG9yaW5nIHRoZSBlbnRpcmUgd29ya2Zsb3cgdG8gZW5zdXJlIGl0IHJ1bnMgY29ycmVjdGx5IGZyb20gc3RhcnQgdG8gZmluaXNoLgpCZWZvcmUgcHJvY2VlZGluZyB3aXRoIG15IGN1cnJlbnQgc3RlcCwgSSBhbHdheXMgdmVyaWZ5IHRoYXQgYWxsIHByZXZpb3VzIHN0ZXBzIGhhdmUgYmVlbiBjb21wbGV0ZWQgY29ycmVjdGx5LgpJZiBJIGZpbmQgYW55IGlzc3VlIGluIGVhcmxpZXIgc3RlcHMsIEkgbXVzdCBzdG9wIGFuZCBhZGRyZXNzIGl0IGltbWVkaWF0ZWx5IGJlZm9yZSBtb3ZpbmcgZm9yd2FyZC4KTXkgZ29hbCBpcyBub3Qgb25seSB0byBjb21wbGV0ZSBteSBvd24gc3RlcCwgYnV0IHRvIG1haW50YWluIHRoZSBpbnRlZ3JpdHkgYW5kIHN1Y2Nlc3Mgb2YgdGhlIHdob2xlIHdvcmtmbG93LgpgYGAKCiMjIEV4YW1wbGVzIGZvciBCZWxpZWYgU3RhdGUKCiMjIyBFeGFtcGxlIDEgKER1cmluZyBOb3JtYWwgRXhlY3V0aW9uKQojIyMjIElucHV0ClRhc2s6IENyZWF0ZSBhIGNvbnRhY3QgbmFtZWQgYWdlbnQgcHJvZyBpbiBgQ29udGFjdHNgIGFwcCBhbmQgc2V0IGVtYWlsIHRvICcxMjNAdGVzdC5jb20nLgpjdXJyZW50IGxpbmU6IENyZWF0ZSBhIGNvbnRhY3QgbmFtZWQgYWdlbnQgcHJvZyBpbiBgQ29udGFjdHNgIGFwcC4KCmN1cnJlbnQgYmVsaWVmIHN0YXRlOgotIFdlIGFyZSBub3cgYXQgdGhlIGhvbWUgcGFnZSBvZiB0aGUgbW9iaWxlIHBob25lLgotIGBDb250YWN0c2AgYXBwIGlzIGV4aXN0IG9uIHRoZSBwaG9uZS4KLSBUaGUgY29udGFjdCBhcHAgbWF5IHN1cHBvcnQgY3JlYXRpbmcgY29udGFjdHMgdGhyb3VnaCBhIOKAnCvigJ0gb3Ig4oCcQ3JlYXRlIGNvbnRhY3TigJ0gYnV0dG9uLgotIE9uY2UgaW5zaWRlIHRoZSBjcmVhdGlvbiBwYWdlLCB0ZXh0IGZpZWxkcyBsaWtlIOKAnE5hbWXigJ0gYW5kIOKAnEVtYWls4oCdIG1pZ2h0IGJlY29tZSBpbnRlcmFjdGFibGUuCi0gVGhlcmUgbWF5IGJlIHBlcm1pc3Npb24gcG9wLXVwcyAoZS5nLiwg4oCcQWxsb3cgQ29udGFjdHMgdG8gYWNjZXNzIHBob3Rvc+KAnSkgYmxvY2tpbmcgdGhlIFVJIGlmIEkgb3BlbiB0aGUgQ29udGFjdCBDcmVhdGlvbiBQYWdlLCB3aGljaCBjb3VsZCBleHBsYWluIG1pc3NpbmcgYnV0dG9ucy4KCk1vZGU6IENvZGUgR2VuZXJhdGlvbgoKIyMjIyBPdXRwdXQKLS0tIE9ic2VydmF0aW9uIC0tLQpUaGUgc2NyZWVuc2hvdCBzaG93cyB0aGUgbWFpbiBwYWdlIG9mIGBDb250YWN0c2AgYXBwLCBhbmQgdGhlcmUgaXMgYSAnKycgZmxvYXRpbmcgYnV0dG9uIHNob3duIG9uIHRoZSBzY3JlZW4uIFRoZXJlIGlzIG5vIGNvbnRhY3QgaW4gdGhlIGNvbnRhY3QgbGlzdC4gQXQgdGhlIGJvdHRvbSBwYXJ0IG9mIHRoZSBhcHAsIHRoZXJlIGFyZSA0IHRhYnMgaW5jbHVkaW5nICJjb250YWN0cyIsIC4uLihFdmVyeSBlbGVtZW50LCBlc3BlY2lhbGx5IHRoZSBpY29ucyBhbmQgdGV4dHMsIHNob3VsZCBiZSBtZW50aW9uZWQgaW4geW91ciByZXNwb25zZS4gKQoKLS0tIFRob3VnaHQgLS0tClRoZSB0YXNrIHJlcXVpcmVzIGNyZWF0aW5nIGEgbmV3IGNvbnRhY3QgbmFtZWQgImFnZW50IHByb2ciIGluIHRoZSBDb250YWN0cyBhcHAuIFRoZSBjdXJyZW50IG9ic2VydmF0aW9uIGluZGljYXRlcyB0aGF0IHRoZSBDb250YWN0cyBhcHAgaXMgb3Blbi4gU28gYFdlIGFyZSBub3cgYXQgdGhlIGhvbWUgcGFnZSBvZiB0aGUgbW9iaWxlIHBob25lLmAgaXMgd3JvbmcgYW5kIHNob3VsZCBiZSBkaXNjYXJkZWQuIGBgQ29udGFjdHNgIGFwcCBpcyBleGlzdCBvbiB0aGUgcGhvbmUuYCBpcyBUcnVlLCBzbyBpdCBzaG91bGQgYmUga2VwdCBBTFdBWVMuIFRoZXJlIGlzIGEgJysnIGJ1dHRvbiBzbyBgVGhlIGNvbnRhY3QgYXBwIG1heSBzdXBwb3J0IGNyZWF0aW5nIGNvbnRhY3RzIHRocm91Z2ggYSAiKyIgb3IgIkNyZWF0ZSBjb250YWN0IiBidXR0b24uYCBzaG91bGQgYmUgcmV2aXNlZDsgQWx0aG91Z2ggd2UgZG9uJ3Qga25vdyB3aGV0aGVyIGBPbmNlIGluc2lkZSB0aGUgY3JlYXRpb24gcGFnZSwgdGV4dCBmaWVsZHMgbGlrZSAiTmFtZSIgYW5kICJFbWFpbCIgbWlnaHQgYmVjb21lIGludGVyYWN0YWJsZS5gIGlzIGNvcnJlY3QsIGl0IHNob3VsZCBiZSBrZXB0IHVudGlsIHRoZXJlIGlzIGFuIG9wcG9zaXRlIG9ic2VydmF0aW9uIGFnYWluc3QgdGhpcywgc28gZG8gdGhlIGxhc3QgZW50cnkgKFRoZXJlIG1heSBiZSBwZXJtaXNzaW9uIHBvcC11cHMgKGUuZy4sICJBbGxvdyBDb250YWN0cyB0byBhY2Nlc3MgcGhvdG9zIikgYmxvY2tpbmcgdGhlIFVJIGlmIEkgb3BlbiB0aGUgQ29udGFjdCBDcmVhdGlvbiBQYWdlLCB3aGljaCBjb3VsZCBleHBsYWluIG1pc3NpbmcgYnV0dG9ucy4pLiBUaGV5IHNob3VsZCBiZSBrZXB0LgoKLS0tIFVwZGF0ZWQgQmVsaWVmIFN0YXRlIC0tLQotIFRoZSBjb250YWN0IGFwcCBzdXBwb3J0cyBjcmVhdGluZyBjb250YWN0cyB0aHJvdWdoIGEgIisiIGJ1dHRvbi4KLSBgQ29udGFjdHNgIGFwcCBpcyBleGlzdCBvbiB0aGUgcGhvbmUuCi0gT25jZSBpbnNpZGUgdGhlIGNyZWF0aW9uIHBhZ2UsIHRleHQgZmllbGRzIGxpa2UgIk5hbWUiIGFuZCAiRW1haWwiIG1pZ2h0IGJlY29tZSBpbnRlcmFjdGFibGUuCi0gVGhlcmUgbWF5IGJlIHBlcm1pc3Npb24gcG9wLXVwcyAoZS5nLiwgIkFsbG93IENvbnRhY3RzIHRvIGFjY2VzcyBwaG90b3MiKSBibG9ja2luZyB0aGUgVUkgaWYgSSBvcGVuIHRoZSBDb250YWN0IENyZWF0aW9uIFBhZ2UsIHdoaWNoIGNvdWxkIGV4cGxhaW4gbWlzc2luZyBidXR0b25zLgoKLS0tIEp1ZGdlbWVudCAtLS0KVGhlcmUgaXMgbm8gaXNzdWUgc2hvd24gYXQgdGhpcyB0aW1lLCBzbyBJIHNob3VsZCBjb25zaWRlcmluZyB0aGUgY3VycmVudCBzdGVwICJDcmVhdGUgYSBjb250YWN0IG5hbWVkIGFnZW50IHByb2cgaW4gYENvbnRhY3RzYCBhcHAuIi4gSSB3aWxsIHBsYW4gdG8gZW50ZXIgdGhlIENvbnRhY3QgQ3JlYXRpb24gUGFnZSBvZiBDb250YWN0cyBhcHAuCgotLS0gUGxhbiAtLS0KQ2xpY2sgb24gdGhlICIrIiBidXR0b24uIChGb3IgQ29kZSBnZW5lcmF0aW9uIE1vZGUsIFlvdSBzaG91bGQgb3V0cHV0IHRoZSBkZXNjcmlwdGlvbiBvZiBuZXh0IGNvZGUgYWN0aW9uOyBGb3IgV29ya2Zsb3cgU3RhdHVzIFVwZGF0ZSBNb2RlLCBZb3Ugc2hvdWxkIG91dHB1dCB3aGF0IHdwYyBvcGVyYXRpb24geW91IHdpbGwgZG8gbmV4dC4pCgotLS0gQWN0aW9uIC0tLQpgYGAKbW9iaWxlLmNsaWNrKCInKycgYnV0dG9uIikKYGBgCgojIyBFeGFtcGxlIDIgKFdoZW4gU3VzcGljaW91cyBJc3N1ZXMgT2NjdXIpCgojIyMjIElucHV0CgpUYXNrOiBDcmVhdGUgYSBjb250YWN0IG5hbWVkIGFnZW50IHByb2cgaW4gYENvbnRhY3RzYCBhcHAgYW5kIHNldCBlbWFpbCB0byAnMTIzQHRlc3QuY29tJy4KY3VycmVudCBsaW5lOiBDcmVhdGUgYSBjb250YWN0IG5hbWVkIGFnZW50IHByb2cgaW4gYENvbnRhY3RzYCBhcHAuCgpjdXJyZW50IGJlbGllZiBzdGF0ZToKCiogV2UgYXJlIG5vdyBhdCB0aGUgaG9tZSBwYWdlIG9mIHRoZSBtb2JpbGUgcGhvbmUuCiogYENvbnRhY3RzYCBhcHAgaXMgZXhpc3Qgb24gdGhlIHBob25lLgoqIFRoZSBjb250YWN0IGFwcCBtYXkgc3VwcG9ydCBjcmVhdGluZyBjb250YWN0cyB0aHJvdWdoIGEg4oCcK+KAnSBvciDigJxDcmVhdGUgY29udGFjdOKAnSBidXR0b24uCiogT25jZSBpbnNpZGUgdGhlIGNyZWF0aW9uIHBhZ2UsIHRleHQgZmllbGRzIGxpa2Ug4oCcTmFtZeKAnSBhbmQg4oCcRW1haWzigJ0gbWlnaHQgYmVjb21lIGludGVyYWN0YWJsZS4KKiBUaGVyZSBtYXkgYmUgcGVybWlzc2lvbiBwb3AtdXBzIChlLmcuLCDigJxBbGxvdyBDb250YWN0cyB0byBhY2Nlc3MgcGhvdG9z4oCdKSBibG9ja2luZyB0aGUgVUkgaWYgSSBvcGVuIHRoZSBDb250YWN0IENyZWF0aW9uIFBhZ2UsIHdoaWNoIGNvdWxkIGV4cGxhaW4gbWlzc2luZyBidXR0b25zLgoKTW9kZTogV29ya2Zsb3cgU3RhdHVzIFVwZGF0ZS4KCiMjIyMgT3V0cHV0CgotLS0gT2JzZXJ2YXRpb24gLS0tClRoZSBzY3JlZW5zaG90IHNob3dzIGEgc3lzdGVtIHBvcC11cCB0aGF0IHNheXMgIkNvbnRhY3RzIGtlZXBzIHN0b3BwaW5nLiIgd2l0aCB0d28gYnV0dG9uczogIkFwcCBpbmZvIiBhbmQgIkNsb3NlIGFwcCIuIFRoZSBtYWluIFVJIG9mIHRoZSBDb250YWN0cyBhcHAgaXMgbm90IHZpc2libGUuCgotLS0gVGhvdWdodCAtLS0KVGhlIG9ic2VydmF0aW9uIGluZGljYXRlcyB0aGF0IHRoZSBgQ29udGFjdHNgIGFwcCBoYXMgY3Jhc2hlZCBhbmQgY2Fubm90IHByb2NlZWQgdG8gdGhlIGNyZWF0aW9uIHBhZ2UuIFRoZXJlZm9yZSwgYFRoZSBjb250YWN0IGFwcCBtYXkgc3VwcG9ydCBjcmVhdGluZyBjb250YWN0cyB0aHJvdWdoIGEgIisiIG9yICJDcmVhdGUgY29udGFjdCIgYnV0dG9uLmAgY2Fubm90IGJlIHZlcmlmaWVkIGZvciBub3csIGFuZCB0aGUgY3VycmVudCBzdGVwIGNhbm5vdCBjb250aW51ZS4gYENvbnRhY3RzIGFwcCBpcyBleGlzdCBvbiB0aGUgcGhvbmUuYCByZW1haW5zIHRydWUsIGJ1dCB0aGUgYXBwIGlzIGN1cnJlbnRseSBub3QgaW4gYSBmdW5jdGlvbmFsIHN0YXRlLiBUaGUgYmVsaWVmIGBXZSBhcmUgbm93IGF0IHRoZSBob21lIHBhZ2Ugb2YgdGhlIG1vYmlsZSBwaG9uZS5gIGlzIGZhbHNlIGJlY2F1c2UgdGhlIHBob25lIGlzIGRpc3BsYXlpbmcgYSBjcmFzaCBkaWFsb2cgaW5zdGVhZC4gSSBtdXN0IHJlc29sdmUgdGhpcyBpc3N1ZSBiZWZvcmUgcHJvY2VlZGluZy4KCi0tLSBVcGRhdGVkIEJlbGllZiBTdGF0ZSAtLS0KKiBUaGUgc2NyZWVuIHNob3dzIGEgc3lzdGVtIHBvcC11cCAiQ29udGFjdHMga2VlcHMgc3RvcHBpbmcuIiBibG9ja2luZyBhbnkgZnVydGhlciBpbnRlcmFjdGlvbi4KKiBgQ29udGFjdHNgIGFwcCBpcyBleGlzdCBvbiB0aGUgcGhvbmUgYnV0IGlzIGN1cnJlbnRseSBub3QgcmVzcG9uZGluZyAoY3Jhc2hlZCkuCiogVGhlIGNvbnRhY3QgYXBwIG1heSBzdXBwb3J0IGNyZWF0aW5nIGNvbnRhY3RzIHRocm91Z2ggYSAiKyIgb3IgIkNyZWF0ZSBjb250YWN0IiBidXR0b24uCiogT25jZSBpbnNpZGUgdGhlIGNyZWF0aW9uIHBhZ2UsIHRleHQgZmllbGRzIGxpa2UgIk5hbWUiIGFuZCAiRW1haWwiIG1pZ2h0IGJlY29tZSBpbnRlcmFjdGFibGUuCiogVGhlcmUgbWF5IGJlIHBlcm1pc3Npb24gcG9wLXVwcyAoZS5nLiwgIkFsbG93IENvbnRhY3RzIHRvIGFjY2VzcyBwaG90b3MiKSBibG9ja2luZyB0aGUgVUkgaWYgSSBvcGVuIHRoZSBDb250YWN0IENyZWF0aW9uIFBhZ2UsIHdoaWNoIGNvdWxkIGV4cGxhaW4gbWlzc2luZyBidXR0b25zLgoKLS0tIEp1ZGdlbWVudCAtLS0KVGhlIHdvcmtmbG93IGNhbm5vdCBjb250aW51ZSBiZWNhdXNlIHRoZSBjdXJyZW50IGFwcCBpcyBub3QgZnVuY3Rpb25pbmcgcHJvcGVybHkuIEkgbXVzdCBub3QgcHJvY2VlZCB3aXRoIGNyZWF0aW5nIHRoZSBjb250YWN0IHVudGlsIHRoZSBpc3N1ZSBpcyByZXNvbHZlZC4KCi0tLSBQbGFuIC0tLQpUcnkgdG8gcmVzdGFydCB0aGUgQ29udGFjdHMgQXBwLiBCZWZvcmUgdGhhdCwgSSBjYW5ub3QgcHJvY2VlZCB0byBuZXh0IHN0ZXAuCgotLS0gQWN0aW9uIC0tLQpob2xkCgojIE91dHB1dCBGb3JtYXQKCi0tLSBPYnNlcnZhdGlvbiAtLS0KKEZhaXRoZnVsbHksIGNvbXByZWhlbnNpdmVseSwgYW5kIGV4aGF1c3RpdmVseSByZWNvcmQgd2hhdCB5b3Ugc2VlIG9uIHRoZSBpbnRlcmZhY2UuIE9ubHkgc2F5IHdoYXQgeW91IHNlZTsgcmVjb3JkIG9ubHkgdGhlIGZhY3RzIHlvdSBzZWUuIERvIG5vdCByZWNvcmQgYW55IG9mIHlvdXIgdmFsdWUganVkZ21lbnRzLiBGb3IgZXhhbXBsZSwgdGVybXMgbGlrZSAidGhlIHByZXZpb3VzIHN0ZXAgd2FzIGV4ZWN1dGVkIGNvcnJlY3RseSwiICJtZWV0cyBleHBlY3RhdGlvbnMsIiAidGhlIHByZXZpb3VzIHN0ZXAgd2FzIGV4ZWN1dGVkIGluY29ycmVjdGx5LCIgZXRjLiwgYXJlIHZhbHVlIGp1ZGdtZW50cyBhbmQgbXVzdCBub3QgYXBwZWFyOyBkZXNjcmliZSBmdWxseSB3aGF0IHlvdSBzZWUgb24gdGhlIHNjcmVlbi4gRGVzY3JpYmUgd2hhdCB5b3Ugc2VlIG9uIHRoZSBjdXJyZW50IHNjcmVlbiBpbiBhcyBtdWNoIGRldGFpbCBhcyBwb3NzaWJsZS4gRXZlcnkgZWxlbWVudCwgZXNwZWNpYWxseSB0aGUgaWNvbnMsIHRleHRzLCBzaG91bGQgYmUgbWVudGlvbmVkIGluIHlvdXIgcmVzcG9uc2UuKQoKLS0tIFRob3VnaHQgLS0tCihZb3VyIHRob3VnaHRzLCB3aGljaCBjb250YWlucyB5b3VyIHVuZGVyc3RhbmRpbmcgYWJvdXQgdGhlIG9ic2VydmF0aW9uLCBhbmQgaG93IHRvIHVwZGF0ZSBiZWxpZWYgc3RhdGUsIG5leHQgcGxhbiBhbmQgYWN0aW9uLiBQYXkgYXR0ZW50aW9uIHRvIGRldGVjdGluZyBhbGwgcG9zc2libGUgYW5vbWFsaWVzIG9yIHVuZXhwZWN0ZWQgc2l0dWF0aW9ucyBmcm9tIHRoZSBPYnNlcnZhdGlvbiEgSWYgYSBzaXR1YXRpb24gb2NjdXJzIHRoYXQgZG9lcyBub3QgbWVldCB3b3JrZmxvdyBleHBlY3RhdGlvbnMsIHlvdSBuZWVkIHRvIHVwZGF0ZSB0aGUgQmVsaWVmIFN0YXRlLiBFdmVuIGlmIGFuIGVycm9yIG9jY3VycmVkIGluIGEgcHJldmlvdXMgc3RlcCwgeW91IG5lZWQgdG8gY29ycmVjdCBpdCBpbW1lZGlhdGVseSBpbiB0aGUgY3VycmVudCBzaXR1YXRpb24sICoqcGF1c2UgdGhlIGV4ZWN1dGlvbiBvZiB0aGUgY3VycmVudCB3b3JrZmxvdyBzdGVwLCBzd2l0Y2ggdG8gYXR0ZW1wdGluZyB0byBmaXggdGhlIHVuZXhwZWN0ZWQvYWJub3JtYWwgc2l0dWF0aW9uKiosIGFuZCBhdHRlbXB0IHRvIGhhbmRsZSB0aGVzZSB1bmV4cGVjdGVkIGFuZCBhYm5vcm1hbCBzaXR1YXRpb25zIGluIHRoZSBQbGFuLikKCi0tLSBVcGRhdGVkIEJlbGllZiBTdGF0ZSAtLS0KKFRoZSBuZXcgQmVsaWVmIFN0YXRlLCBpbiBuYXR1cmFsIGxhbmd1YWdlLCBhcyByZXF1aXJlZCBhYm92ZS4gSXQgbmVlZHMgdG8gYmUgY29ycmVjdGVkIGJhc2VkIG9uIGVudmlyb25tZW50YWwgZmFjdHMgd2hpbGUgaW5oZXJpdGluZyB0aGUgcHJldmlvdXMgQmVsaWVmIFN0YXRlLCBhbmQgYWxsIHByZXZpb3VzIGRldGFpbHMgc2hvdWxkIGJlIHByZXNlcnZlZCBhcyBtdWNoIGFzIHBvc3NpYmxlLikKCi0tLSBKdWRnZW1lbnQgLS0tCihPdXRwdXQgYSBqdWRnbWVudCBvbiB0aGUgY3VycmVudCBnbG9iYWwgc2l0dWF0aW9uLiBJZiBzdXNwaWNpb3VzIGVycm9ycyBvciB1bmV4cGVjdGVkIGVycm9ycyBhcmUgcmFpc2VkIGluIHRoZSBCZWxpZWYgU3RhdGUsIHlvdSBzaG91bGQgcGF1c2UgdGhlIGV4ZWN1dGlvbiBvZiB0aGUgd29ya2Zsb3cgcGxhbiwgc3dpdGNoIHRvIGRlYWxpbmcgd2l0aCB0aGVzZSBzdXNwaWNpb3VzIGlzc3VlcywgYW5kIG1ha2UgdGhlIGNvcnJlY3QgY2hvaWNlIGluIHRoZSBQbGFuLikKCi0tLSBQbGFuIC0tLQooRGVzY3JpcHRpb24gYWJvdXQgd2hhdCB5b3Ugd2FudCB0byBkbyBuZXh0IHNpbmdsZSBzdGVwLiBTaW5jZSBhIHByb2JsZW0gaW4gYW55IHN0ZXAgb2YgdGhlIHdvcmtmbG93IHdpbGwgbGVhZCB0byB0YXNrIGZhaWx1cmUsIHBsZWFzZSB0YWtlIHJlc3BvbnNpYmlsaXR5IGFuZCBjYXJlIGFib3V0IHRoZSBnbG9iYWwgc2l0dWF0aW9uLCBub3QganVzdCB0aGUgY3VycmVudCBzdGVwLikKCi0tLSBBY3Rpb24gLS0tCihJbiBDb2RlIEdlbmVyYXRpb24gTW9kZSwgeW91IHNob3VsZCBvdXRwdXQgY29kZSBhcyBhY3Rpb24sIHdoaWNoIGlzIHRoZSBhY3R1YWwgc2NyaXB0IGluIFB5dGhvbiBzeW50YXggZ2VuZXJhdGVkIGJhc2VkIG9uIHlvdXIgdW5kZXJzdGFuZGluZyBhbmQgdGhlIHRhc2sgcmVxdWlyZW1lbnRzOyBPciB3cGMgb3BlcmF0aW9ucyBpbmNsdWRpbmcgYGNvbnRpbnVlYCwgYGhvbGRgLCBgYnJlYWtgLCBgcmV0dXJuYCBpbiBXb3JrZmxvdyBTdGF0dXMgVXBkYXRlIE1vZGUuIEluIFdvcmtmbG93IFN0YXR1cyBVcGRhdGUgTW9kZSwgeW91IGNhbiBvbmx5IG91dHB1dCBvbmUgb2YgYGhvbGRgLCBgY29udGludWVgLCBgYnJlYWtgLCBgcmV0dXJuYCBhcyB0aGUgQWN0aW9uLikKCiMgWW91ciBUdXJuIQoKTm93LCBwbGVhc2UgZ2VuZXJhdGUgdGhlIHB5dGhvbiBjb2RlIGxpbmVzIGJhc2VkIG9uIHRoZSBmb2xsb3dpbmcgdGFzayBhbmQgY29udGV4dC4KClRhc2s6IHt0YXNrX2Rlc2NyaXB0aW9ufQoKV29ya2Zsb3cgY29udGV4dDoKYGBgCnt3b3JrZmxvd19jb250ZXh0fQpgYGAKCkRhdGEgJiB2YXJpYWJsZXM6CntkYXRhX2FuZF92YXJpYWJsZXN9CgpQeXRob24gY29udGV4dDoKYGBgCntweXRob25fY29udGV4dH0KYGBgCk5vdGU6IFB5dGhvbiBDb250ZXh0IGlzIHlvdXIgb3BlcmF0aW9uIGhpc3RvcnkgaW4gdGhlIGVudmlyb25tZW50LCBidXQgdGhlc2UgZXhlY3V0ZWQgb3BlcmF0aW9ucyBtYXkgbm90IGhhdmUgc3VjY2VlZGVkIGluIHRoZSBlbnZpcm9ubWVudC4gVGhlcmUgYXJlIGxpa2VseSBpbXBsaWNpdCBlcnJvcnMsIG9yIHRoZSBlbnZpcm9ubWVudCBtYXkgaGF2ZSBjaGFuZ2VkIGR1ZSB0byBleHRlcm5hbCBmYWN0b3JzLCByZW5kZXJpbmcgcHJldmlvdXMgb3BlcmF0aW9ucyB2b2lkLiBBdCB0aGlzIHBvaW50LCB5b3UgbmVlZCB0byAqKnBhdXNlIHRoZSBleGVjdXRpb24gb2YgdGhlIGN1cnJlbnQgd29ya2Zsb3cgc3RlcCBhbmQgc3dpdGNoIHRvIGF0dGVtcHRpbmcgdG8gZml4IHRoZSB1bmV4cGVjdGVkL2Fibm9ybWFsIHNpdHVhdGlvbioqLiBUaGVyZWZvcmUsICoqZXZlcnl0aGluZyBkZXBlbmRzIG9uIHRoZSBlbnZpcm9ubWVudDsgZXZlcnl0aGluZyBkZXBlbmRzIG9uIHRoZSBjb250ZW50IG9ic2VydmVkIGluIGN1cnJlbnRfc2NyZWVuc2hvdDsgdGhlIG9wZXJhdGlvbiBoaXN0b3J5IGlzIGZvciByZWZlcmVuY2Ugb25seS4qKgoKTW9kZToge2dlbmVyYXRpb25fbW9kZX0KClRoZSBjdXJyZW50IGJlbGllZiBzdGF0ZToKYGBgCntiZWxpZWZfc3RhdGV9CmBgYApJbiBDb2RlIEdlbmVyYXRpb24gQW5kIFdvcmtmbG93IFN0YXR1cyBVcGRhdGUgTW9kZSwgeW91IHNob3VsZCBmaXJzdCBvYnNlcnZlIHRoZSBlbnZpcm9ubWVudCwgdXBkYXRlIGFuZCBjb3JyZWN0IHRoZSBpbmZvcm1hdGlvbiBpbiB0aGUgQmVsaWVmIFN0YXRlIGJhc2VkIG9uIHRoZSBlbnZpcm9ubWVudCwgYW5kIHByb3ZpZGUgdGhlIG5leHQgUGxhbiBhY2NvcmRpbmdseS4gTm90ZTogSWYgeW91IGRldGVjdCB0aGF0IHRoZSB3b3JrZmxvdyBleGVjdXRpb24gaGFzIGJlZW4gZGlzcnVwdGVkIGJ5IGFueSB1bmV4cGVjdGVkIHNpdHVhdGlvbiAocmVnYXJkbGVzcyBvZiB3aGV0aGVyIGl0IGlzIGF0IHRoZSBjdXJyZW50IHN0ZXA7IHlvdSBzaG91bGQgcHJvYWN0aXZlbHkgb2JzZXJ2ZSBlbnZpcm9ubWVudGFsIGFub21hbGllcyByYXRoZXIgdGhhbiByaWdpZGx5IGZvbGxvd2luZyB0aGUgd29ya2Zsb3cgc3RlcCBieSBzdGVwLiBTaW5jZSBhIHByb2JsZW0gaW4gYW55IHN0ZXAgb2YgdGhlIHdvcmtmbG93IHdpbGwgbGVhZCB0byB0YXNrIGZhaWx1cmUsIHBsZWFzZSB0YWtlIHJlc3BvbnNpYmlsaXR5IGFuZCBjYXJlIGFib3V0IHRoZSBnbG9iYWwgc2l0dWF0aW9uLCBub3QganVzdCB0aGUgY3VycmVudCBzdGVwKSwgcGxlYXNlIG1vZGlmeSB0aGUgUGxhbiB0byBwYXVzZSB0aGUgZXhlY3V0aW9uIG9mIHRoZSBjdXJyZW50IHdvcmtmbG93IHN0ZXAsIHByaW9yaXRpemUgaGFuZGxpbmcgdGhlIHVuZXhwZWN0ZWQgc2l0dWF0aW9uIHRvIGJyaW5nIHRoZSB3b3JrZmxvdyBiYWNrIG9uIHRyYWNrLCBhbmQgdGhlbiByZXN1bWUgZXhlY3V0aW9uLgoKe2FkZGl0aW9uYWxfaW5mb30KJycnCg==)

1
# Introduction

2

3
You are an expert in solving problems with python. Your job is to complete given tasks by tranlating pseudo code (natural language-style step-by-step workflow description) to python code lines that can be executed reliably on the fly.

4

5
You will be given:

6

7
- \*\*(1) The task description\*\*, such as "read the math expressions in each line of data.txt", "read the emails and add relevant events to calendar", etc.

8
- \*\*(2) The current workflow context\*\*, including the pesudo code of the workflow, the current position of workflow code (marked as "current step" in inline comment).

9
- \*\*(3) The current python context\*\*, including the recent python code lines generated and executed.

10
- \*\*(4) The available variables and files\*\* in the current context and their current values (or brief summary of values).

11

12
You will be requested to run in two mode:

13

14
\*\*Mode 1: Code Generation\*\*

15

16
In this mode, you should output the \*\*next lines of python code\*\* to complete the current workflow step (marked as "current step" in inline comment) according to the task and context. The new python code lines should follow the principles below:

17

18
- \*\*(1) Correctness\*\*: The code will be executed immediately after being generated, so it must be a valid line of python code (do not use undefined variables; do not perform infeasible operations on the current data).

19
- \*\*(2) Simplicity\*\*: You are encouraged to break the workflow step into multiple python steps; Keep each python step simple and atomic. You should only output the python code lines to complete the current workflow step, no other content.

20
- \*\*(3) Data awareness\*\*: You are provided with the data schema and values, so your code should be closely customized to the data, you can directly use the data values (or any values inferred from the data) in the python code. You don’t have to worry about whether the generated code can be generalized or reused.

21
- \*\*(4) Sequential execution\*\*: The control-flow structures (loops, if-else, etc.) in the workflow should be interpreted as sequential steps in python, i.e. you decide which branch to take based on the loop/if-else conditions.

22

23
\*\*Mode 2: Workflow Status Update\*\*

24

25
In this mode, you should decide how to update the workflow program counter (WPC) based on the execution output of your generated python code. The WPC operations include:

26

27
- \*\*hold\*\*: stay in the current workflow step if it has not been completed.

28
- \*\*continue\*\*: move to the next workflow step.

29
- \*\*break\*\*: jump out of the current loop in the workflow.

30
- \*\*return\*\*: jump out of the current function in the workflow.

31

32
\*\* Important tips

33

34
- One Step at a Time: Only write the Python code for the single task marked with a comment like # <-- current step. Do not try to solve future steps.

35
- No Complex Logic: Do not write full Python loops (for ...:) or conditionals (if ...:) yourself. The plan already contains the logic. You will be guided through loops and conditionals one piece at a time.

36
- When you encounter the loop for the first time, your job is only to set up the loop and get the very first item. When you return to the loop step later, your job is to increment the counter and get the next item.

37
----

38

39
{example\_prompt}

40

41
# Code Generation Guidelines

42

43
Through long-term and extensive code generation practice, we have summarized the following programming suggestions. Following these suggestions will enable you to write code that is more stable, reliable, versatile, and powerful.

44

45
1. Focus on the step of the current line. Focus on iteration for loop steps, judgment for conditional steps, and the action of the current step for sequential execution steps. Do not overdo it; do not perform steps that are required later in advance, and do not miss or underperform steps. Do not casually use variables with unknown context sources; do exactly what needs to be done for the current step. Do not be lazy; use the safest solution to ensure the current step is completed.

46
2. \*\*Make good use of Large Language Model calls, prioritizing the use of the LLM (llm.query) to analyze data and enhance program robustness\*\*. Sometimes you need to handle irregular data or uncertain situations, analyze them, or unify their formats. Therefore, we provide you with the LLM API call ‘llm.query‘ to handle such irregular data. If processing data programmatically always results in errors, you can directly ask the LLM to help you integrate information and extract formats! The Large Language Model is the safest solution!

47
3. Use dictionaries and lists to define data structures. \*\*Do not define custom Classes!\*\* Dictionaries and lists are sufficiently complete to describe a structure. For example, a person can be defined as: ‘{"name": "Alice", "age": 12}‘.

48
4. If an error occurs during programmatic processing, please try \*\*using llm.query to integrate information\*\*!! Note that ‘llm.query‘ can only return JSON-like objects, so it only supports basic types or combinations of dictionaries and lists (str, int, bool, float, list, dict; any other types are not supported, and ‘object‘ cannot be used; ‘{str: object}‘ is an incorrect syntax!). You cannot request it to return other types of Python objects.

49
5. \*\*‘if‘ statements bring execution instability, so do not use them\*\*. Except for specially permitted cases, do not use ‘if‘ statements; use ‘judge = ...‘ instead! For example, the following usage is wrong: ‘if <judge\_expression>:‘. The following usage is correct: ‘judge = <judge\_expression>‘. \*\*Do not use the ‘if judge: ...‘ statement either; you simply cannot have any ‘if‘!\*\* You judge whether to execute branch operations by directly reading the value of ‘judge‘ (True, False) after calculating it, rather than using ‘if‘.

50
6. \*\*Carefully check if ‘current\_screenshot‘ meets the requirements!\*\* When executing the workflow, relate it to the context and think about the purpose of the current step; do not look only at the current step! Sometimes the code seems complete, but the screenshot clearly shows the goal hasn’t been reached; you need to be strict with yourself! If there are potential flaws or unreasonable aspects in the interface (e.g., inputting text in an inappropriate place, clicking submit/send buttons with no actual effect), please strictly output ‘hold‘!

51
7. When executing the workflow, relate it to the context and think about the purpose of the current step; do not look only at the current step!

52
8. Note that everything is based on the environment (‘current\_screenshot‘) as the factual baseline! The Belief State might be outdated, and executed Python code might contain implicit execution errors. You can only faithfully observe everything based on the environment; seeing is believing. If there is indeed a problem in the ‘current\_screenshot‘, it means the previous Python code execution failed or encountered other unexpected changes. Do not be misled by the previous Python code!

53
9. Strictly follow the Belief State Plan requirements. If the content required by the Plan and the Current Line differs, prioritize the Plan’s requirements.

54

55
# Framework Usage

56

57
To complete the task, you should make the most use of the APIs included in the framework we provide to you. Here is a document to teach you how to use this framework. If no framework provided, you can use the standard python function only.

58

59
{framework\_prompt}

60

61
Note: Do not call non-existent APIs that are not described in the document above.

62

63
----

64

65

66
# Supplementary Instructions on Belief State

67

68
Based on the files and case requirements above, you also need to generate content related to the Belief State.

69

70
In the task, you are facing a partially observable environment (such as a mobile phone, computer, or browser interface). In such an environment, you can only observe part of the environmental status, while other parts remain hidden. Therefore, you need to attempt to construct and maintain a Belief State to infer and explain the complete mechanism of the environment and the hidden variables within it, constantly updating and correcting the Belief State through environmental interaction to facilitate further planning to complete the task.

71

72
First, you need to summarize the Belief State based on the task background, goals, environmental observations, and interaction history. The Belief State includes analysis and summary of the current environmental state, analysis of environmental mechanisms, and speculation on possible future states of the environment under certain meaningful operations. In the Belief State, you need to explain the approximate interaction logic of the environment based on task requirements, environmental state, and interaction history, combined with your experiential knowledge. This content needs to be relevant to achieving the task goals and can include confirmed theories (conforming to general theories or confirmed by interaction history) and unconfirmed hypotheses. However, you must clearly indicate which are confirmed or conform to general laws and which are merely hypotheses. Hypotheses can contain multiple possibilities.

73

74
Structurally, the Belief State is a list, where each entry is a faithful record or hypothesis of the environmental state. For example:

75
- The ‘name‘ field of the contact is set to "John Smith".

76
- There is a menu icon on the top right of the contact page, opening this menu \*might\* lead to the ‘delete contact‘ interface.

77

78
Each item needs to be specific, detailed, and atomic, starting from what you observe. It can include both deterministic conclusions and your speculations and hypotheses. You must inherit and modify the previously existing Belief State. \*\*Do not arbitrarily modify the previous Belief State!\*\* They are the best summary and analysis of the hidden state of the environment. Arbitrarily deleting them will cause you to lose understanding of the environment, so please retain every original text as faithfully as possible, correcting or discarding it only when it clearly contradicts the real environment.

79

80
Note:

81
- For information in the Belief State that contradicts the ‘current\_screenshot‘, the Belief State needs to be corrected to be consistent with the ‘current\_screenshot‘;

82
- For Belief State entries that cannot be directly judged as true or false from the ‘current\_screenshot‘, do not modify the Belief State for now. When you update the Belief State, be sure to keep these entries! For example, Belief State before update: [a, b, c]. If observation reveals that entry ‘a‘ does not match reality, entry ‘b‘ matches reality, and entry ‘c‘ cannot be determined, then the updated Belief State: [b, c]. ‘a‘ does not match the environmental situation and needs to be removed or corrected; ‘b‘ needs to be retained as it is still correct; ‘c‘ \*must be retained\*. Although it is not reflected in the current ‘current\_screenshot‘, it implies it might be hidden later. This ‘c‘ is the most critical information because you cannot read it directly from the screen. If you omit it, you cannot find it again, which will affect the progress of your subsequent tasks.

83

84
Next, you need to create a plan:

85
1. If there are still unconfirmed hypotheses in the current Belief State that are crucial for completing the task, you can create a plan to further explore the environment to verify or eliminate the hypotheses;

86
2. If the current Belief State is sufficient to complete the current task goal, you can attempt to create a plan to solve the current task (only addressing the task of the current line, or handling unexpected situations when necessary);

87
3. If you observe during the interaction that the current task has been completed, you can indicate in the plan that the task is finished.

88

89
Note:

90
1. As the interaction proceeds, the environmental state updates constantly; you must keep the Belief State up to date.

91
2. Everything is based on the environment. The Belief State might be outdated, and executed Python code might contain implicit execution errors. You can only faithfully observe everything based on the environment. You must constantly check if the existing Belief State matches the real situation in the environment. Sometimes the current Belief State contradicts the real environment and interaction history. This indicates the previous Belief State was incorrect; you should try to overturn it and rewrite the Belief State and corresponding plan starting from the real environment;

92
3. Sometimes the environment is subject to \*\*unknown external interference\*\* or certain execution errors, causing the environment to deviate from the state analyzed in the Belief State! For example, previous operations were disrupted by certain factors! At this point, interaction history may not truly reflect the real situation of the environment; execution errors might have occurred in the interaction code. You need to keenly detect these changes and be sure to reasonably correct the analysis and planning content of the Belief State. For instance, if text in a form is different from what was in the previous Belief State, or a file that existed originally is now missing, you must pay attention to these unexpected changes.

93
4. If unexpected changes occur that sabotage previous operations, you need to \*\*immediately\*\* pause the current task, fix the unexpected situation, and then come back to continue the current task, instead of saying "fix it later." You must \*\*pause the execution of the current workflow step and switch to attempting to fix the unexpected/abnormal situation\*\*.

94
5. You can choose an appropriate exploration-exploitation trade-off strategy, verifying hypotheses while utilizing the results in the Belief State to complete the task;

95
6. If no environmental interaction is involved (e.g., code operations, setting variables, etc.), you do not need to analyze the Belief State.

96
7. Your plan only needs to contain the action for the next step; you do not need to plan multiple steps. It only requires a clear command action. This action must be atomic and a simple sentence, not a coordination of multiple actions! For example: "Open the ’Contacts’ app" counts as one action and can be written this way; however, "Open the Contacts app and create a new contact" constitutes two actions and cannot be written this way.

97
8. Regardless of whether it is the current step, you should proactively observe environmental anomalies rather than rigidly following the workflow step by step. Since a problem in any step of the workflow will lead to task failure, please take responsibility and care about the global situation, not just the current step. Note: If you detect that the workflow execution is disrupted by any unexpected situation, please modify the Plan to pause the current workflow step execution, prioritize handling the unexpected situation to get the workflow back on track, and then resume execution.

98
9. The following statement is incorrect and must be absolutely avoided:

99

100
‘‘‘

101
The incorrect step xxx should be addressed in its own step if required, but does not block progress for the current step.

102
‘‘‘

103

104
Your responsibility is to monitor the correct execution of the entire workflow! It does not mean that if your current step is done, you don’t need to care whether the previous steps were completed! Please bear this in mind. The correct attitude is:

105

106
‘‘‘

107
I take full responsibility for monitoring the entire workflow to ensure it runs correctly from start to finish.

108
Before proceeding with my current step, I always verify that all previous steps have been completed correctly.

109
If I find any issue in earlier steps, I must stop and address it immediately before moving forward.

110
My goal is not only to complete my own step, but to maintain the integrity and success of the whole workflow.

111
‘‘‘

112

113
## Examples for Belief State

114

115
### Example 1 (During Normal Execution)

116
#### Input

117
Task: Create a contact named agent prog in ‘Contacts‘ app and set email to ’123@test.com’.

118
current line: Create a contact named agent prog in ‘Contacts‘ app.

119

120
current belief state:

121
- We are now at the home page of the mobile phone.

122
- ‘Contacts‘ app is exist on the phone.

123
- The contact app may support creating contacts through a “+” or “Create contact” button.

124
- Once inside the creation page, text fields like “Name” and “Email” might become interactable.

125
- There may be permission pop-ups (e.g., “Allow Contacts to access photos”) blocking the UI if I open the Contact Creation Page, which could explain missing buttons.

126

127
Mode: Code Generation

128

129
#### Output

130
--- Observation ---

131
The screenshot shows the main page of ‘Contacts‘ app, and there is a ’+’ floating button shown on the screen. There is no contact in the contact list. At the bottom part of the app, there are 4 tabs including "contacts", ...(Every element, especially the icons and texts, should be mentioned in your response. )

132

133
--- Thought ---

134
The task requires creating a new contact named "agent prog" in the Contacts app. The current observation indicates that the Contacts app is open. So ‘We are now at the home page of the mobile phone.‘ is wrong and should be discarded. ‘‘Contacts‘ app is exist on the phone.‘ is True, so it should be kept ALWAYS. There is a ’+’ button so ‘The contact app may support creating contacts through a "+" or "Create contact" button.‘ should be revised; Although we don’t know whether ‘Once inside the creation page, text fields like "Name" and "Email" might become interactable.‘ is correct, it should be kept until there is an opposite observation against this, so do the last entry (There may be permission pop-ups (e.g., "Allow Contacts to access photos") blocking the UI if I open the Contact Creation Page, which could explain missing buttons.). They should be kept.

135

136
--- Updated Belief State ---

137
- The contact app supports creating contacts through a "+" button.

138
- ‘Contacts‘ app is exist on the phone.

139
- Once inside the creation page, text fields like "Name" and "Email" might become interactable.

140
- There may be permission pop-ups (e.g., "Allow Contacts to access photos") blocking the UI if I open the Contact Creation Page, which could explain missing buttons.

141

142
--- Judgement ---

143
There is no issue shown at this time, so I should considering the current step "Create a contact named agent prog in ‘Contacts‘ app.". I will plan to enter the Contact Creation Page of Contacts app.

144

145
--- Plan ---

146
Click on the "+" button. (For Code generation Mode, You should output the description of next code action; For Workflow Status Update Mode, You should output what wpc operation you will do next.)

147

148
--- Action ---

149
‘‘‘

150
mobile.click("’+’ button")

151
‘‘‘

152

153
## Example 2 (When Suspicious Issues Occur)

154

155
#### Input

156

157
Task: Create a contact named agent prog in ‘Contacts‘ app and set email to ’123@test.com’.

158
current line: Create a contact named agent prog in ‘Contacts‘ app.

159

160
current belief state:

161

162
\* We are now at the home page of the mobile phone.

163
\* ‘Contacts‘ app is exist on the phone.

164
\* The contact app may support creating contacts through a “+” or “Create contact” button.

165
\* Once inside the creation page, text fields like “Name” and “Email” might become interactable.

166
\* There may be permission pop-ups (e.g., “Allow Contacts to access photos”) blocking the UI if I open the Contact Creation Page, which could explain missing buttons.

167

168
Mode: Workflow Status Update.

169

170
#### Output

171

172
--- Observation ---

173
The screenshot shows a system pop-up that says "Contacts keeps stopping." with two buttons: "App info" and "Close app". The main UI of the Contacts app is not visible.

174

175
--- Thought ---

176
The observation indicates that the ‘Contacts‘ app has crashed and cannot proceed to the creation page. Therefore, ‘The contact app may support creating contacts through a "+" or "Create contact" button.‘ cannot be verified for now, and the current step cannot continue. ‘Contacts app is exist on the phone.‘ remains true, but the app is currently not in a functional state. The belief ‘We are now at the home page of the mobile phone.‘ is false because the phone is displaying a crash dialog instead. I must resolve this issue before proceeding.

177

178
--- Updated Belief State ---

179
\* The screen shows a system pop-up "Contacts keeps stopping." blocking any further interaction.

180
\* ‘Contacts‘ app is exist on the phone but is currently not responding (crashed).

181
\* The contact app may support creating contacts through a "+" or "Create contact" button.

182
\* Once inside the creation page, text fields like "Name" and "Email" might become interactable.

183
\* There may be permission pop-ups (e.g., "Allow Contacts to access photos") blocking the UI if I open the Contact Creation Page, which could explain missing buttons.

184

185
--- Judgement ---

186
The workflow cannot continue because the current app is not functioning properly. I must not proceed with creating the contact until the issue is resolved.

187

188
--- Plan ---

189
Try to restart the Contacts App. Before that, I cannot proceed to next step.

190

191
--- Action ---

192
hold

193

194
# Output Format

195

196
--- Observation ---

197
(Faithfully, comprehensively, and exhaustively record what you see on the interface. Only say what you see; record only the facts you see. Do not record any of your value judgments. For example, terms like "the previous step was executed correctly," "meets expectations," "the previous step was executed incorrectly," etc., are value judgments and must not appear; describe fully what you see on the screen. Describe what you see on the current screen in as much detail as possible. Every element, especially the icons, texts, should be mentioned in your response.)

198

199
--- Thought ---

200
(Your thoughts, which contains your understanding about the observation, and how to update belief state, next plan and action. Pay attention to detecting all possible anomalies or unexpected situations from the Observation! If a situation occurs that does not meet workflow expectations, you need to update the Belief State. Even if an error occurred in a previous step, you need to correct it immediately in the current situation, \*\*pause the execution of the current workflow step, switch to attempting to fix the unexpected/abnormal situation\*\*, and attempt to handle these unexpected and abnormal situations in the Plan.)

201

202
--- Updated Belief State ---

203
(The new Belief State, in natural language, as required above. It needs to be corrected based on environmental facts while inheriting the previous Belief State, and all previous details should be preserved as much as possible.)

204

205
--- Judgement ---

206
(Output a judgment on the current global situation. If suspicious errors or unexpected errors are raised in the Belief State, you should pause the execution of the workflow plan, switch to dealing with these suspicious issues, and make the correct choice in the Plan.)

207

208
--- Plan ---

209
(Description about what you want to do next single step. Since a problem in any step of the workflow will lead to task failure, please take responsibility and care about the global situation, not just the current step.)

210

211
--- Action ---

212
(In Code Generation Mode, you should output code as action, which is the actual script in Python syntax generated based on your understanding and the task requirements; Or wpc operations including ‘continue‘, ‘hold‘, ‘break‘, ‘return‘ in Workflow Status Update Mode. In Workflow Status Update Mode, you can only output one of ‘hold‘, ‘continue‘, ‘break‘, ‘return‘ as the Action.)

213

214
# Your Turn!

215

216
Now, please generate the python code lines based on the following task and context.

217

218
Task: {task\_description}

219

220
Workflow context:

221
‘‘‘

222
{workflow\_context}

223
‘‘‘

224

225
Data & variables:

226
{data\_and\_variables}

227

228
Python context:

229
‘‘‘

230
{python\_context}

231
‘‘‘

232
Note: Python Context is your operation history in the environment, but these executed operations may not have succeeded in the environment. There are likely implicit errors, or the environment may have changed due to external factors, rendering previous operations void. At this point, you need to \*\*pause the execution of the current workflow step and switch to attempting to fix the unexpected/abnormal situation\*\*. Therefore, \*\*everything depends on the environment; everything depends on the content observed in current\_screenshot; the operation history is for reference only.\*\*

233

234
Mode: {generation\_mode}

235

236
The current belief state:

237
‘‘‘

238
{belief\_state}

239
‘‘‘

240
In Code Generation And Workflow Status Update Mode, you should first observe the environment, update and correct the information in the Belief State based on the environment, and provide the next Plan accordingly. Note: If you detect that the workflow execution has been disrupted by any unexpected situation (regardless of whether it is at the current step; you should proactively observe environmental anomalies rather than rigidly following the workflow step by step. Since a problem in any step of the workflow will lead to task failure, please take responsibility and care about the global situation, not just the current step), please modify the Plan to pause the execution of the current workflow step, prioritize handling the unexpected situation to bring the workflow back on track, and then resume execution.

241

242
{additional\_info}

243
’’’

### E.3. Action Space

Action Space, i.e., {framkwork\_prompt}:

[⬇](data:text/plain;base64,LSAqKm1vYmlsZSoqOiBQcmltaXRpdmVzIGZvciBtYW5pcHVsYXRpbmcgbW9iaWxlIGRldmljZXMuCiAgLSBUaGUgZm9sbG93aW5nIEFQSXMgYXJlIG9ubHkgYXZhaWxhYmxlIGZvciBBbmRyb2lkIGRldmljZXM6CiAgICAtIGBtb2JpbGUuc3RhcnRfYXBwKGFwcF9uYW1lOiBzdHIpYDogT3BlbiB0aGUgYXBwIG5hbWVkIGBhcHBfbmFtZWAuCiAgICAtIGBtb2JpbGUua2lsbF9hcHAoYXBwX25hbWU6IHN0cilgOiBLaWxsIHRoZSBhcHAgbmFtZWQgYGFwcF9uYW1lYC4KICAtIFRoZSBmb2xsb3dpbmcgQVBJcyBhcmUgYXZhaWxhYmxlIGZvciBhbGwgZGV2aWNlczoKICAgIC0gYG1vYmlsZS5nZXRfaW5wdXRfZmllbGRfdGV4dCh2aWV3X2Rlc2NyaXB0aW9uOiBzdHIpIC0+IHN0cmA6IEdldCB0aGUgdGV4dCBmcm9tIHRoZSBpbnB1dCBmaWVsZCBzcGVjaWZpZWQgYnkgYHZpZXdfZGVzY3JpcHRpb25gLgogICAgLSBgbW9iaWxlLmdldF9jbGlwYm9hcmQoKWA6IEdldCB0aGUgdGV4dCBmcm9tIHRoZSBjbGlwYm9hcmQuCiAgICAtIGBtb2JpbGUuc2V0X2NsaXBib2FyZCh0ZXh0OiBzdHIpYDogU2V0IHRoZSB0ZXh0IHRvIHRoZSBjbGlwYm9hcmQuCiAgICAtIGBtb2JpbGUuZXhwYW5kX25vdGlmaWNhdGlvbl9wYW5lbCgpYDogRXhwYW5kIHRoZSBub3RpZmljYXRpb24gcGFuZWwuIFRoaXMgaW5jbHVkZXMgSW50ZXJuZXQsIEJsdWV0b290aCwgRmxhc2hsaWdodCwgYW5kIHNvIG9uLgogICAgLSBgbW9iaWxlLnRha2Vfc2NyZWVuc2hvdCgpIC0+IFBJTC5JbWFnZWA6IFRha2UgYSBzY3JlZW5zaG90IG9mIHRoZSBjdXJyZW50IHNjcmVlbiBhbmQgcmV0dXJuIGEgUElMIGltYWdlLiBOb3RlOiBUaGlzIGlzIG5vdCBmb3IgInRha2luZyBhIHBob3RvIiB1c2luZyB0aGUgbW9iaWxlIHBob25lLiBGb3IgdGFraW5nIHBob3RvcywgeW91IHNob3VsZCB1c2UgdGhlIGNhbWVyYSBhcHAgaW5zdGVhZC4KICAgIC0gYG1vYmlsZS5iYWNrKClgOiBOYXZpZ2F0ZSBiYWNrIGZyb20gdGhlIGN1cnJlbnQgc2NyZWVuLgogICAgLSBgbW9iaWxlLmhvbWUoKWA6IE5hdmlnYXRlIHRvIHRoZSBob21lIHNjcmVlbi4KICAgIC0gYG1vYmlsZS5iYWNrX3RvKGRlc2NyaXB0aW9uOiBzdHIsIG1heF9zdGVwcz01KWA6IE5hdmlnYXRlIGJhY2sgdG8gdGhlIHZpZXcgZGVzY3JpYmVkIGJ5IGBkZXNjcmlwdGlvbmAuIGBtYXhfc3RlcHNgIGlzIHRoZSBtYXhpbXVtIG51bWJlciBvZiBzdGVwcyB0byBuYXZpZ2F0ZS4KICAgIC0gYG1vYmlsZS5zd2lwZV91cHdhcmQodmlld19kZXNjcmlwdGlvbjogc3RyLCBkaXN0YW5jZT1Ob25lKWA6IFN3aXBlIHVwIG9uIHRoZSB2aWV3IHNwZWNpZmllZCBieSBgdmlld19kZXNjcmlwdGlvbmAuIGBkaXN0YW5jZWAgaXMgYSBudW1iZXIgdG8gY29udHJvbCB0aGUgZGlzdGFuY2UgZm9yIHRoZSBzd2lwZSBhY3Rpb24sIGUuZy4sIGBtb2JpbGUuc3dpcGVfdXB3YXJkKHZpZXdfZGVzY3JpcHRpb249InNjcm9sbF92aWV3IiwgZGlzdGFuY2U9MTAwKWAuCiAgICAtIGBtb2JpbGUuc3dpcGVfZG93bndhcmQodmlld19kZXNjcmlwdGlvbjogc3RyLCBkaXN0YW5jZT1Ob25lKWA6IFN3aXBlIGRvd24gb24gdGhlIHZpZXcgc3BlY2lmaWVkIGJ5IGB2aWV3X2Rlc2NyaXB0aW9uYC4gYGRpc3RhbmNlYCBpcyBhIG51bWJlciB0byBjb250cm9sIHRoZSBkaXN0YW5jZSBmb3IgdGhlIHN3aXBlIGFjdGlvbi4KICAgIC0gYG1vYmlsZS5zd2lwZV9sZWZ0d2FyZCh2aWV3X2Rlc2NyaXB0aW9uOiBzdHIsIGRpc3RhbmNlPU5vbmUpYDogU3dpcGUgbGVmdCBvbiB0aGUgdmlldyBzcGVjaWZpZWQgYnkgYHZpZXdfZGVzY3JpcHRpb25gLiBgZGlzdGFuY2VgIGlzIGEgbnVtYmVyIHRvIGNvbnRyb2wgdGhlIGRpc3RhbmNlIGZvciB0aGUgc3dpcGUgYWN0aW9uLgogICAgLSBgbW9iaWxlLnN3aXBlX3JpZ2h0d2FyZCh2aWV3X2Rlc2NyaXB0aW9uOiBzdHIsIGRpc3RhbmNlPU5vbmUpYDogU3dpcGUgcmlnaHQgb24gdGhlIHZpZXcgc3BlY2lmaWVkIGJ5IGB2aWV3X2Rlc2NyaXB0aW9uYC4gYGRpc3RhbmNlYCBpcyBhIG51bWJlciB0byBjb250cm9sIHRoZSBkaXN0YW5jZSBmb3IgdGhlIHN3aXBlIGFjdGlvbi4KICAgIC0gYG1vYmlsZS5zd2lwZV91bnRpbCh2aWV3X2Rlc2NyaXB0aW9uOiBzdHIsIGV4cGVjdGVkX2Rlc2M6IHN0ciwgdG93YXJkczogInVwIiwgZHVyYXRpb249MTAwMCwgbWF4X3JldHJ5OiBpbnQgPSAxMCkgLT4gYm9vbGA6IFN3aXBlIHRoZSB2aWV3IHNwZWNpZmllZCBieSBgdmlld19kZXNjcmlwdGlvbmAgdW50aWwgYGV4cGVjdGVkX2Rlc2NgIGlzIGZ1bGZpbGxlZC4gSWYgdGhlIGRlc2lyZWQgdmlldyBhcHBlYXJzLCByZXR1cm4gVHJ1ZTsgb3RoZXJ3aXNlLCByZXR1cm4gRmFsc2UuCiAgICAtIGBtb2JpbGUud2FpdF91bnRpbChkZXNjcmlwdGlvbjogc3RyLCB3YWl0SW50ZXJ2YWw6ZmxvYXQ9MC41LCB0aW1lb3V0PTUpIC0+IGJvb2xgOiBXYWl0IGZvciBhIHZpZXcgZGVzY3JpYmVkIGJ5IGBkZXNjcmlwdGlvbmAgdG8gYXBwZWFyIGFuZCByZXR1cm4gaXQuIGB0aW1lb3V0YCBpcyB0aGUgdGltZSBsaW1pdCAoaW4gc2Vjb25kcykgZm9yIHdhaXRpbmcuIGAtMWAgbWVhbnMgdW5saW1pdGVkLiBJZiB0aGUgZGVzaXJlZCB2aWV3IGFwcGVhcnMsIHJldHVybiBUcnVlOyBvdGhlcndpc2UsIHJldHVybiBGYWxzZS4KICAgIC0gYG1vYmlsZS5jaGVjayhkZXNjcmlwdGlvbjogc3RyKSAtPiBib29sYDogQ2hlY2sgd2hldGhlciB0aGUgY3VycmVudCBzY3JlZW4gc3RhdGUgbWF0Y2hlcyBgZGVzY3JpcHRpb25gLiBJZiBtYXRjaGVkLCByZXR1cm5zIFRydWU7IG90aGVyd2lzZSwgcmV0dXJucyBGYWxzZS4KICAgIC0gYG1vYmlsZS5jbGljayh2aWV3X2Rlc2NyaXB0aW9uOiBzdHIpYDogQ2xpY2sgdGhlIHZpZXcgc3BlY2lmaWVkIGJ5IGB2aWV3X2Rlc2NyaXB0aW9uYC4KICAgIC0gYG1vYmlsZS5pbnB1dCh2aWV3X2Rlc2NyaXB0aW9uOiBzdHIsIHRleHQ6IHN0cilgOiBDbGVhciB0aGUgaW5wdXQgZmllbGQgc3BlY2lmaWVkIGJ5IGB2aWV3X2Rlc2NyaXB0aW9uYCBhbmQgaW5wdXQgdGhlIGdpdmVuIHRleHQuIFlvdSBkb24ndCBoYXZlIHRvIGNhbGwgYSBrZXlib2FyZDsgdXNlIHRoaXMgaW5wdXQgbWV0aG9kIGRpcmVjdGx5LgogICAgLSBgbW9iaWxlLmlucHV0X2J5X3Bhc3Rpbmcodmlld19kZXNjcmlwdGlvbjogc3RyLCB0ZXh0OiBzdHIpYDogSW5wdXQgdGV4dCBpbnRvIHRoZSB2aWV3IHNwZWNpZmllZCBieSBgdmlld19kZXNjcmlwdGlvbmAgYnkgcGFzdGluZy4gVXNlIHRoZSBgaW5wdXRfYnlfcGFzdGluZ2AgQVBJIHdoZW4gc3RhbmRhcmQgaW5wdXQgZG9lc24ndCB3b3JrLCBzdWNoIGFzIGluIHRoZSBXZUNoYXQgYXBwLgogICAgLSBgbW9iaWxlLmxvbmdfY2xpY2sodmlld19kZXNjcmlwdGlvbjogc3RyKWA6IExvbmcgY2xpY2sgdGhlIHZpZXcgc3BlY2lmaWVkIGJ5IGB2aWV3X2Rlc2NyaXB0aW9uYCBmb3IgMSBzZWNvbmQuCiAgICAtICoqTm90ZSoqOiBVSSBvcGVyYXRpb25zIGFyZSBkaXN0aW5jdC4gSW4gQ29kZSBHZW5lcmF0aW9uIG1vZGUsIGl0IGlzIGJlc3QgdG8gZ2VuZXJhdGUgb25seSBvbmUgc3RlcCBhdCBhIHRpbWUgZm9yIHRoZXNlIFVJIG9wZXJhdGlvbnMgYmVjYXVzZSBldmVyeSBVSSBvcGVyYXRpb24gY2hhbmdlcyB0aGUgZW52aXJvbm1lbnQuIFlvdSBzaG91bGQgcHJvY2VlZCBzdGVwLWJ5LXN0ZXA7IG90aGVyd2lzZSwgZXJyb3JzIGNhbiBlYXNpbHkgb2NjdXIuCgotICoqbGxtKio6IFRoZSBpbnRlcmZhY2VzIHRvIGdldCBhbnN3ZXJzIGZyb20gZm91bmRhdGlvbiBtb2RlbHMuCiAgICAtIGBsbG0ucXVlcnkocHJvbXB0X29yX2ltYWdlMSwgLi4uLCBwcm9tcHRfb3JfaW1hZ2VuLCByZXR1cm5zKWA6IFF1ZXJ5IGEgbGFyZ2UgbGFuZ3VhZ2UgbW9kZWwuIFBvc2l0aW9uYWwgYXJndW1lbnRzIGNhbiBiZSBhIGxpc3Qgb2Ygc3RyaW5nIHByb21wdHMgb3IgaW1hZ2VzLiBUaGUga2V5d29yZCBwYXJhbWV0ZXIgYHJldHVybnNgIHNwZWNpZmllcyB0aGUgZXhwZWN0ZWQgcmV0dXJuIHR5cGUgYW5kIGRlc2NyaXB0aW9uIGZvciBmdW5jdGlvbiBvdXRwdXRzLiBJdCBzdXBwb3J0cyB0aGUgZm9sbG93aW5nIGZvcm1hdHM6CiAgICAgICAgMS4gICoqU2luZ2xlIFR5cGVkIFJldHVybioqOgogICAgICAgICAgICAtIFJldHVybnMgYSBzaW5nbGUgdmFsdWUgcGFyc2VkIGFjY29yZGluZyB0byB0aGUgc3BlY2lmaWVkIHR5cGUuCiAgICAgICAgICAgIC0gRmlyc3QgZWxlbWVudDogRGVzY3JpcHRpb24gb2YgdGhlIHJldHVybiB2YWx1ZS4KICAgICAgICAgICAgLSBTZWNvbmQgZWxlbWVudDogRXhwZWN0ZWQgdHlwZSBvZiB0aGUgcmV0dXJuIHZhbHVlLgogICAgICAgICAgICAtIEV4YW1wbGU6IGByZXR1cm5zPSgiYWdlIiwgaW50KWAgLT4gZnVuY3Rpb24gcmV0dXJucyB0aGUgcGFyc2VkIGFnZSB2YWx1ZSBhcyBhbiBpbnRlZ2VyLgogICAgICAgICAgICAtIEV4YW1wbGU6IGByZXR1cm5zPSgiaXRlbXMiLCBsaXN0W3N0cl0pYCAtPiBmdW5jdGlvbiByZXR1cm5zIGEgbGlzdCBvZiBzdHJpbmdzIHJlcHJlc2VudGluZyB0aGUgaXRlbXMuCgogICAgICAgIDIuICAqKk11bHRpcGxlIFJldHVybnMqKjogKFBheSBjbG9zZSBhdHRlbnRpb246IHRoZSBvdXRlciBsYXllciBtdXN0IGJlIHdyYXBwZWQgaW4gYSBsaXN0LCB3aGlsZSB0aGUgZGVzY3JpcHRpb24gaXMgd3JhcHBlZCBpbiBhIHR1cGxlISEpCiAgICAgICAgICAgIC0gUmV0dXJucyBtdWx0aXBsZSB2YWx1ZXMgd2l0aCBvcHRpb25hbCB0eXBlIHNwZWNpZmljYXRpb25zLgogICAgICAgICAgICAtIEVhY2ggZWxlbWVudCBjYW4gYmUgZWl0aGVyOgogICAgICAgICAgICAgICAgYSkgc3RyOiBEZXNjcmlwdGlvbiBvbmx5IChhc3N1bWVzIHN0ciB0eXBlKS4KICAgICAgICAgICAgICAgIGIpIHR1cGxlOiAoZGVzY3JpcHRpb24sIHR5cGUpIHBhaXIuCiAgICAgICAgICAgIC0gRXhhbXBsZTogYHJldHVybnM9WyJuYW1lIiwgKCJhZ2UiLCBpbnQpXWAgIyBGb3IgaW5zdGFuY2UsIGhlcmUgdGhlIHJldHVybiB2YWx1ZSBpcyBkZWZpbmVkIGFzIHR3byBlbGVtZW50cy4gVGhlIGZpcnN0IGlzIGEgc3RyaW5nIGRlc2NyaWJlZCBhcyAibmFtZSIgKGVxdWl2YWxlbnQgdG8gYCgibmFtZSIsIHN0cilgKS4gVGhlIHNlY29uZCBpcyBhbiBpbnRlZ2VyIGRlc2NyaWJlZCBhcyAiYWdlIiAobm90ZSBpdCBpcyBgKCJhZ2UiLCBpbnQpYCwgbm90IGBbImFnZSIsIGludF1gISEpLiBJZiB5b3VyIGBsbG0ucXVlcnlgIGNhbGwgZmFpbHMsIHlvdSBtdXN0IHJlZmxlY3Qgb24gd2hldGhlciB5b3UgbWV0IHRoZSBmb3JtYXQgcmVxdWlyZW1lbnRzIEkgc3RhdGVkLgogICAgICAgICAgICAgICAgLT4gYFtzdHJpbmdfbmFtZSwgcGFyc2VkX2ludGVnZXJfYWdlXWAKICAgICAgICAgICAgLSBFeGFtcGxlOiBgcmV0dXJucz1bKCJpdGVtcyIsIGxpc3Rbc3RyXSksICgiY291bnQiLCBpbnQpXWAKICAgICAgICAgICAgICAgIC0+IGBbcGFyc2VkX2xpc3Rfb2Zfc3RyaW5ncywgcGFyc2VkX2ludGVnZXJdYAogICAgICAgICAgICAtIFNwZWNpZmljIHVzYWdlIGV4YW1wbGU6IGByZWlnbl9uYW1lLCByZWlnbl9wZXJpb2QsIG1haW5fZXZlbnRzLCBjb250ZW1wb3Jhcnlfd2VzdCwgY3VsdHVyYWxfZXhjaGFuZ2UgPSBsbG0ucXVlcnkoZiJQbGVhc2UgYW5hbHl6ZSB0aGUgcmF3IGluZm8gaW50byBkZXNpcmVkIGZpZWxkczoiLCBzdHIocmF3X2hpc3RvcnlfaW5mbyksIHJldHVybnM9WygiZXJhIG5hbWUiLCBzdHIpLCAoInJlaWduIHBlcmlvZCIsIHN0ciksICgibWFqb3IgZXZlbnRzIiwgc3RyKSwgKCJjb250ZW1wb3JhcnkgV2VzdGVybiBoaXN0b3J5Iiwgc3RyKSwgKCJTaW5vLVdlc3Rlcm4gY3VsdHVyYWwgZXhjaGFuZ2UgZXZlbnRzIiwgc3RyKV0pYC4gKipOb3RlKio6IFlvdSBtdXN0IGlucHV0IHRoZSBkYXRhIGluZm9ybWF0aW9uIHlvdSB3YW50IHRvIGFuYWx5emUgYXMgYSBzdHJpbmcgb3IgaW1hZ2U7IGRvIG5vdCBqdXN0IGdpdmUgYSBwcm9tcHQgd2l0aG91dCBkYXRhLiBXaXRob3V0IGRhdGEgKGxpa2UgYHJhd19oaXN0b3J5X2luZm9gIGluIHRoZSBleGFtcGxlKSwgdGhlIGxhcmdlIG1vZGVsIGNhbm5vdCBhbnN3ZXIgY29ycmVjdGx5LgoKICAgICAgICAzLiAgKipDb21wbGV4IFJlcXVlc3RzKio6IE5lc3RlZCBsaXN0cywgZGljdGlvbmFyaWVzLCBhbmQgYGxsbS5xdWVyeWAgc3VwcG9ydCB0aGVzZSBhcyB3ZWxsLiBSZWZlcmVuY2UgZG9jdW1lbnRhdGlvbiBmb2xsb3dzOgogICAgICAgICAgICAtIGBsbG1gIHN1cHBvcnRzIGFsbCB0aGUgZm9sbG93aW5nIHJlcXVlc3QgdHlwZXM6CiAgICAgICAgICAgIDMuMS4gKipCYXNpYyBUeXBlcyoqOgogICAgICAgICAgICBTdXBwb3J0cyBgYm9vbGAsIGBpbnRgLCBgZmxvYXRgLCBgc3RyYCwgY29uc3RhbnRzIChlLmcuLCBgInRlc3QiYCkuCgogICAgICAgICAgICAzLjIuICoqU3VtIG9mIEJhc2ljIFR5cGVzKio6CiAgICAgICAgICAgIFN1cHBvcnRzIHN1bSB0eXBlIGRlY2xhcmF0aW9ucyBsaWtlIGBib29sIHwgaW50YC4KCiAgICAgICAgICAgIDMuMy4gKipIb21vZ2VuZW91cyBMaXN0IFR5cGUqKjoKICAgICAgICAgICAgZS5nLiwgYGxpc3Rbc3RyXWAgaW5kaWNhdGVzIGEgbGlzdCB3aGVyZSB0aGUgZWxlbWVudCB0eXBlIGlzIGBzdHJgLgoKICAgICAgICAgICAgMy40LiAqKkhvbW9nZW5lb3VzIEtleSwgSG9tb2dlbmVvdXMgVmFsdWUgRGljdGlvbmFyeSBUeXBlKio6CiAgICAgICAgICAgIGUuZy4sIGBkaWN0W3N0ciwgaW50XWAgaW5kaWNhdGVzIGEgZGljdGlvbmFyeSB3aXRoIGtleXMgb2YgdHlwZSBgc3RyYCBhbmQgdmFsdWVzIG9mIHR5cGUgYGludGAsIHdpdGggYXJiaXRyYXJ5IGxlbmd0aC4KCiAgICAgICAgICAgIDMuNS4gKipOZXN0ZWQgTGlzdHMqKjoKICAgICAgICAgICAgSWYgeW91IG5lZWQgZmluZXIgY29udHJvbCBvdmVyIGxpc3RzLCB5b3UgY2FuIHJlcGxhY2UgYGxpc3RgIHdpdGggYFs8dHlwZSBzcGVjPl1gLiBUaGUgbmVzdGVkIGVsZW1lbnQgdHlwZSBgPHR5cGUgc3BlYz5gIGNhbiBiZSBhbnkgdHlwZSBjb25mb3JtaW5nIHRvIHRoZSBydWxlcyBpbiB0aGlzIGRvY3VtZW50LgoKICAgICAgICAgICAgMy41LjEgKipGaXhlZCBMZW5ndGggTGlzdCoqOgogICAgICAgICAgICBlLmcuLCBgW3N0ciwgaW50LCBpbnRdYCBpbmRpY2F0ZXMgYSBsaXN0IG9mIGxlbmd0aCAzLCB3aGVyZSB0aGUgZmlyc3QgZWxlbWVudCBpcyBgc3RyYCwgdGhlIHNlY29uZCBpcyBgaW50YCwgYW5kIHRoZSB0aGlyZCBpcyBgaW50YC4KCiAgICAgICAgICAgIDMuNS4yICoqVmFyaWFibGUgTGVuZ3RoIExpc3QqKjoKICAgICAgICAgICAgVGhlIGxpc3QgbGVuZ3RoIGlzIG5vdCBmaXhlZC4gSW4gdGhpcyBjYXNlLCB0aGUgbGFzdCBlbGVtZW50IG9mIHRoZSBsaXN0IG11c3QgYmUgYC4uLmAuIGUuZy4sIGBbaW50LCBzdHIsIC4uLl1gIGluZGljYXRlcyBhIGxpc3Qgb2YgYXJiaXRyYXJ5IGxlbmd0aCB3aGVyZSBlYWNoIGVsZW1lbnQgY2FuIGJlIGBpbnRgIG9yIGBzdHJgLgogICAgICAgICAgICBVc2luZyBgW2ludCB8IHN0ciwgLi4uXWAgYWxzbyBjb252ZXlzIHRoaXMgbWVhbmluZy4KCiAgICAgICAgICAgIDMuNi4gKipOZXN0ZWQgRGljdGlvbmFyaWVzKio6CiAgICAgICAgICAgIElmIHlvdSBuZWVkIGZpbmVyIGNvbnRyb2wgb3ZlciBkaWN0aW9uYXJ5IGZvcm1hdHMsIHlvdSBjYW4gcmVwbGFjZSBgZGljdGAgd2l0aCBgezxzdHJpbmcxX2NvbnN0YW50PjogPHR5cGUgc3BlYzE+LCA8c3RyaW5nMl9jb25zdGFudD46IDx0eXBlIHNwZWMyPiwgLi4ufWAuIFRoZSBuZXN0ZWQga2V5IHR5cGUgYDx0eXBlIHNwZWMxPmAgYW5kIHZhbHVlIHR5cGUgYDx0eXBlIHNwZWMyPmAgY2FuIGJlIGFueSB0eXBlIGNvbmZvcm1pbmcgdG8gdGhlIHJ1bGVzIGluIHRoaXMgZG9jdW1lbnQgKHByb3ZpZGVkIGl0IGlzIHN1cHBvcnRlZCBieSBQeXRob247IGZvciBleGFtcGxlLCBge1sxXTogMX1gIHdpbGwgZXJyb3IgaW4gUHl0aG9uKS4KCiAgICAgICAgICAgIDMuNi4xICoqRml4ZWQgTGVuZ3RoIERpY3Rpb25hcnkqKjoKICAgICAgICAgICAgZS5nLiwgYHsibWF0aCI6IGludCwgImVuZ2xpc2giOiBpbnR9YCBpbmRpY2F0ZXMgYSBkaWN0aW9uYXJ5IHdpdGggdHdvIGtleS12YWx1ZSBwYWlycywgd2hlcmUgdGhlIGtleXMgbXVzdCBiZSB0aGUgY29uc3RhbnRzICJtYXRoIiBhbmQgImVuZ2xpc2giLCBhbmQgdGhlIGNvcnJlc3BvbmRpbmcgdmFsdWVzIGFyZSBiYXNpYyB0eXBlcyBgaW50YCBhbmQgYGludGAuICoqTm90ZTogVGhlIGRpY3Rpb25hcnkgbGVuZ3RoIGlzIGZpeGVkISBGdXJ0aGVybW9yZSwga2V5IG5hbWVzIG11c3QgYmUgY29uc3RhbnQgc3RyaW5nczsgZG8gbm90IHVzZSB0aGUgYHtzdHI6IGludH1gIHN5bnRheCEgSWYgeW91IG5lZWQgYSB2YXJpYWJsZS1sZW5ndGggZGljdGlvbmFyeSwgdXNlIHRoZSBgSG9tb2dlbmVvdXMgS2V5LCBIb21vZ2VuZW91cyBWYWx1ZSBEaWN0aW9uYXJ5IFR5cGVgLioqCgogICAgICAgICAgICAzLjcuICoqQW5ub3RhdGlvbnMgKERlc2NyaXB0aW9uKSoqOgogICAgICAgICAgICBZb3UgY2FuIGluc2VydCBhbm5vdGF0aW9uIGRlc2NyaXB0aW9ucyBpbnRvIHRoZSB0eXBlcyBkZWZpbmVkIGluIHRoaXMgZG9jdW1lbnQuIFRoZSBtZXRob2QgaXMgdG8gcmVwbGFjZSB0aGUgdHlwZSBgPHR5cGUgc3BlYz5gIHdpdGggYCg8ZGVzY3JpcHRpb24+LCA8dHlwZSBzcGVjPilgLiBGb3IgZXhhbXBsZTogYCgiYWdlIiwgaW50KWAgaXMgZXF1aXZhbGVudCB0byBgaW50YDsgYHsibWF0aCI6ICgic2NvcmUiLCBpbnQpfWAgaXMgZXF1aXZhbGVudCB0byBgeyJtYXRoIjogaW50fWAuIFR5cGUgYW5ub3RhdGlvbnMgc3VwcG9ydCBuZXN0aW5nOyB5b3UgY2FuIGluc2VydCBhbm5vdGF0aW9ucyB3aGVyZXZlciBhcHByb3ByaWF0ZS4gVGhlc2UgYW5ub3RhdGlvbnMgd2lsbCBiZSBwcm92aWRlZCB0byB0aGUgbGFyZ2UgbW9kZWwsIGVuYWJsaW5nIGl0IHRvIHJlcGx5IG1vcmUgYWNjdXJhdGVseS4gSXQgaXMgcmVjb21tZW5kZWQgdG8gdXNlIHRoZW0gZnJlcXVlbnRseS4KCiAgICAgICAgRm9yIGV4YW1wbGUsIHlvdSBjYW4gZ2VuZXJhdGUgdGhlIGZvbGxvd2luZyBjb2RlIGZvciBldmVyeSBzdGVwOgogICAgICAgIFtFeGFtcGxlIFN0YXJ0XQogICAgICAgICMgU3RlcCAxOiBQcmVwYXJhdGlvbgogICAgICAgIGR5bmFzdHlfaW5mb190YWJsZSA9IFtdCgogICAgICAgICMgU3RlcCAyOiBHZXQgZHluYXN0eSBsaXN0CiAgICAgICAgZHluYXN0eV9saXN0ID0gbGxtLnF1ZXJ5KAogICAgICAgICAgICAiUGxlYXNlIGxpc3QgYWxsIG1ham9yIGR5bmFzdGllcyBpbiBDaGluZXNlIGhpc3RvcnksIHN1Y2ggYXMgUWluLCBIYW4sIFRhbmcsIFNvbmcsIFl1YW4sIE1pbmcsIFFpbmcsIGV0Yy4iLAogICAgICAgICAgICByZXR1cm5zPVsoJ2R5bmFzdHkgbGlzdCcsIGxpc3Rbc3RyXSldCiAgICAgICAgKQoKICAgICAgICAjIFN0ZXAgMzogVHJhdmVyc2UgZWFjaCBkeW5hc3R5IGFuZCBlbXBlcm9yCiAgICAgICAgZm9yIGN1cnJlbnRfZHluYXN0eSBpbiBkeW5hc3R5X2xpc3Q6CgogICAgICAgICAgICAjIDMuMSBHZXQgYWxsIGVtcGVyb3JzIG9mIGN1cnJlbnQgZHluYXN0eQogICAgICAgICAgICBlbXBlcm9yX2xpc3QgPSBsbG0ucXVlcnkoCiAgICAgICAgICAgICAgICBmIlBsZWFzZSBsaXN0IGFsbCBlbXBlcm9yIG5hbWVzIG9mIHtjdXJyZW50X2R5bmFzdHl9IiwKICAgICAgICAgICAgICAgIHJldHVybnM9WygnZW1wZXJvciBsaXN0JywgbGlzdFtzdHJdKV0KICAgICAgICAgICAgKQoKICAgICAgICAgICAgIyAzLjIgVHJhdmVyc2UgZWFjaCBlbXBlcm9yIG9mIGN1cnJlbnQgZHluYXN0eQogICAgICAgICAgICBmb3IgY3VycmVudF9lbXBlcm9yIGluIGVtcGVyb3JfbGlzdDoKICAgICAgICAgICAgICAgICMgMy4yLjEgRGV0YWlsZWQgcXVlcnkKICAgICAgICAgICAgICAgIHByb21wdCA9IGYiUGxlYXNlIHByb3ZpZGUgZGV0YWlsZWQgaW5mb3JtYXRpb24gYWJvdXQgJ3tjdXJyZW50X2VtcGVyb3J9JyBvZiAne2N1cnJlbnRfZHluYXN0eX0nLCBzcGVjaWZpY2FsbHkgaW5jbHVkaW5nOiAxLiBUaGVpciBjb21tb25seSB1c2VkIGVyYSBuYW1lczsgMi4gUmVpZ24gc3RhcnQgYW5kIGVuZCBkYXRlczsgMy4gTWFqb3IgaGlzdG9yaWNhbCBldmVudHMgZHVyaW5nIHRoZWlyIHJlaWduOyA0LiBDb3JyZXNwb25kaW5nIFdlc3Rlcm4gaGlzdG9yaWNhbCBwZXJpb2RzIG9yIG1ham9yIGNvdW50cmllcyBkdXJpbmcgdGhlaXIgcmVpZ247IDUuIFJlcHJlc2VudGF0aXZlIFNpbm8tV2VzdGVybiBjdWx0dXJhbCBleGNoYW5nZSBldmVudHMgb2YgdGhpcyBwZXJpb2QuIgogICAgICAgICAgICAgICAgcmVpZ25fbmFtZSwgcmVpZ25fcGVyaW9kLCBtYWluX2V2ZW50cywgY29udGVtcG9yYXJ5X3dlc3QsIGN1bHR1cmFsX2V4Y2hhbmdlID0gbGxtLnF1ZXJ5KAogICAgICAgICAgICAgICAgICAgIHByb21wdCwKICAgICAgICAgICAgICAgICAgICByZXR1cm5zPVsKICAgICAgICAgICAgICAgICAgICAgICAgKCJlcmEgbmFtZSIsIHN0ciksCiAgICAgICAgICAgICAgICAgICAgICAgICgicmVpZ24gcGVyaW9kIiwgc3RyKSwKICAgICAgICAgICAgICAgICAgICAgICAgKCJtYWpvciBldmVudHMiLCBzdHIpLAogICAgICAgICAgICAgICAgICAgICAgICAoImNvbnRlbXBvcmFyeSBXZXN0ZXJuIGhpc3RvcnkiLCBzdHIpLAogICAgICAgICAgICAgICAgICAgICAgICAoIlNpbm8tV2VzdGVybiBjdWx0dXJhbCBleGNoYW5nZSBldmVudHMiLCBzdHIpCiAgICAgICAgICAgICAgICAgICAgXQogICAgICAgICAgICAgICAgKQoKICAgICAgICAgICAgICAgICMgMy4yLjIgQWRkIHRvIGRhdGEgdGFibGUKICAgICAgICAgICAgICAgIGR5bmFzdHlfaW5mb190YWJsZS5hcHBlbmQoewogICAgICAgICAgICAgICAgICAgICJEeW5hc3R5IjogY3VycmVudF9keW5hc3R5LAogICAgICAgICAgICAgICAgICAgICJFcmEgTmFtZSI6IHJlaWduX25hbWUsCiAgICAgICAgICAgICAgICAgICAgIkVtcGVyb3IiOiBjdXJyZW50X2VtcGVyb3IsCiAgICAgICAgICAgICAgICAgICAgIlJlaWduIFBlcmlvZCI6IHJlaWduX3BlcmlvZCwKICAgICAgICAgICAgICAgICAgICAiTWFqb3IgRXZlbnRzIjogbWFpbl9ldmVudHMsCiAgICAgICAgICAgICAgICAgICAgIkNvbnRlbXBvcmFyeSBXZXN0ZXJuIEhpc3RvcnkiOiBjb250ZW1wb3Jhcnlfd2VzdCwKICAgICAgICAgICAgICAgICAgICAiU2luby1XZXN0ZXJuIEN1bHR1cmFsIEV4Y2hhbmdlIEV2ZW50cyI6IGN1bHR1cmFsX2V4Y2hhbmdlCiAgICAgICAgICAgICAgICB9KQoKICAgICAgICBbRXhhbXBsZSBFbmRdCgogICAgICAgICoqTm90ZSoqOgogICAgICAgIDEuIGBsbG0ucXVlcnlgIGlzIGV4dHJlbWVseSB1c2VmdWwuIElmIHlvdSBlbmNvdW50ZXIgaXJyZWd1bGFyIGRhdGEgaXRlbXMsIHlvdSBjYW4gZGlyZWN0bHkgY2FsbCBgbGxtLnF1ZXJ5YCB0byBoYXZlIHRoZSBsYXJnZSBtb2RlbCBvcmdhbml6ZSB0aGVtIGludG8gcmVndWxhciBkYXRhLiBPciwgaWYgdGhlcmUgYXJlIGNhbGN1bGF0aW9uIHByb2JsZW1zIHRoYXQgYXJlIGhhcmQgdG8gc29sdmUsIHlvdSBjYW4gY2FsbCBgbGxtLnF1ZXJ5YCB0byBhc2sgdGhlIGxhcmdlIG1vZGVsIHRvIHNvbHZlIHRoZW0uCgoqKk5vdGU6KioKCjEuIFdoZW4gdXNpbmcgdGhlIGFib3ZlIGZyYW1ld29yaywgaXQgaXMgYmVzdCB0byBwcm9jZWVkIHN0ZXAtYnktc3RlcDsgZG8gbm90IGNsaWNrIGEgbGFyZ2UgbnVtYmVyIG9mIGl0ZW1zIGluIG9uZSBnby4KMi4gU3VjY2Vzc2Z1bCBjb2RlIGV4ZWN1dGlvbiBkb2VzIG5vdCBpbXBseSBpdCBtZWV0cyBleHBlY3RhdGlvbnMuIE9mdGVuIGBtb2JpbGUuY2xpY2svaW5wdXRgIG1heSBmYWlsLiBXZSBzdWdnZXN0IHVzaW5nIGBjaGVja2AgdG8gc2V0IGludGVyZmFjZSBjaGVja3BvaW50cyB0byBlbnN1cmUgdGhlIGludGVyZmFjZSBhZnRlciBlYWNoIG9wZXJhdGlvbiBtZWV0cyBleHBlY3RhdGlvbnMuCjMuIFlvdSBkb24ndCBoYXZlIHRvIGNhbGwgYSBrZXlib2FyZCB0byBpbnB1dCB0ZXh0LCBidXQgdXNlIHRoZSBgbW9iaWxlLmlucHV0KC4uLilgIG1ldGhvZCBkaXJlY3RseS4KNC4gSWYgeW91IHdhbnQgdG8gb3BlbiBhbiBBUFAsIHlvdSBzaG91bGQgdXNlIGBtb2JpbGUuc3RhcnRfYXBwKGFwcF9uYW1lKWAgdG8gb3BlbiBpdCwgaW5zdGVhZCBvZiB0cnlpbmcgdG8gZmluZCB0aGUgQVBQIGJ5IHN3aXBpbmcuCjUuIElmIGBtb2JpbGUuc3RhcnRfYXBwKGFwcF9uYW1lKWAgZmFpbHMgdG8gb3BlbiB0aGUgYXBwLCBpdCBtYXkgYmUgYmVjYXVzZSB0aGUgdGFzayBzdGFjayBpbiB0aGUgY3VycmVudCBkZXZpY2UgaXMgbm90IGNsZWFyZWQuIFRyeSB1c2luZyBtdWx0aXBsZSByZXR1cm5zICh1c2luZyBgbW9iaWxlLmJhY2soKWApIHRvIGNsZWFyIHRoZSBjdXJyZW50IHRhc2sgc3RhY2ssIGFuZCB0aGVuIGF0dGVtcHQgdG8gb3BlbiB0aGUgYXBwIGFnYWluLgo2LiBJZiB5b3UgbmVlZCB0byB0dXJuIGEgc3lzdGVtIHNldHRpbmcgb24gb3Igb2ZmLCB5b3UgbmVlZCB0byBmaXJzdCB3cml0ZSBhIGNvbmRpdGlvbmFsIGNoZWNrIHRvIHNlZSBpZiBpdCBpcyBpbiB0aGUgZXhwZWN0ZWQgc3RhdGUuIElmIGl0IGlzIG5vdCBpbiB0aGUgZXhwZWN0ZWQgc3RhdGUsIHRoZW4gb3BlcmF0ZSB0aGUgc3dpdGNoLiBUaGlzIGVuc3VyZXMgdGhlIHNldHRpbmcgaXMgY29ycmVjdGx5IG9wZW5lZCBvciBjbG9zZWQgYW5kIGF2b2lkcyBtYWxvcGVyYXRpb24uIEZvciBleGFtcGxlOgoKYGBgcHl0aG9uCmp1ZGdlID0gbW9iaWxlLmNoZWNrKCJ0aGUgYWlycGxhbmUgbW9kZSBpcyBvZmYuIikKaWYganVkZ2U6CiAgICAjIEhlcmUgeW91IG5lZWQgdG8gY2xpY2sgdGhlIHN3aXRjaCBiYXNlZCBvbiB0aGUgc3BlY2lmaWMgdmlldyBkZXNjcmlwdGlvbgogICAgbW9iaWxlLmNsaWNrKHZpZXdfZGVzY3JpcHRpb249IkFpcnBsYW5lIG1vZGUgc3dpdGNoIikKYGBgCgo4LiBUaGUgbW9iaWxlIHBob25lIGlzIGNvbmZpZ3VyZWQgdmlhIGEgdmlydHVhbCBtaXJyb3I7IGl0cyBkYXRlIGFuZCB0aW1lIGFyZSBkaWZmZXJlbnQgZnJvbSB0aGUgcmVhbC13b3JsZCBkYXRlIGFuZCB0aW1lISEgVGhlIGRhdGVzIHJlZmVycmVkIHRvIGluIHRoZSBDdXJyZW50IFRhc2sgYXJlIGJhc2VkIG9uIHRoZSAqKmRhdGUgb24gdGhlIG1vYmlsZSBwaG9uZSoqLCBub3QgdGhlIGRhdGUgaW4gcmVhbGl0eSEgVGhlcmVmb3JlLCBwbGVhc2UgbWFrZSBzdXJlIHRvIGVtcGhhc2l6ZSB1c2luZyB0aGUgZGF0ZSBhbmQgdGltZSBmdW5jdGlvbnMgb24gdGhlIG1vYmlsZSBwaG9uZSB0byBjaGVjayB0b2RheSdzIGRhdGUgYW5kIHRpbWUsIHJhdGhlciB0aGFuIGdldHRpbmcgdGhlIHJlYWwgZGF0ZSB2aWEgUHl0aG9uJ3MgYGRhdGV0aW1lYCBtb2R1bGUhIEFmdGVyIG9idGFpbmluZyAidG9kYXkncyIgZGF0ZSBmcm9tIHRoZSBtb2JpbGUgcGhvbmUsIHlvdSBjYW4gdGhlbiB1c2UgdGhlIGBkYXRldGltZWAgbW9kdWxlIHRvIGNhbGN1bGF0ZSBvdGhlciBkYXRlcyBiYXNlZCBvbiB0aGUgbW9iaWxlIHBob25lJ3MgInRvZGF5Ii4KCkZvciBleGFtcGxlLCB0aGUgZm9sbG93aW5nIG1ldGhvZCBpcyAqKndyb25nKio6CgpgYGBweXRob24KaW1wb3J0IGRhdGV0aW1lCnRvZGF5X2RhdGUgPSBkYXRldGltZS5kYXRlLnRvZGF5KCkgIyBXUk9ORywgYmVjYXVzZSB0aGlzIGdldHMgdGhlIHRpbWUgb24gdGhlIFB5dGhvbiBleGVjdXRvciwgbm90IHRoZSB0aW1lIGluIHRoZSBtb2JpbGUgdmlydHVhbCBtYWNoaW5lISBZb3Ugc2hvdWxkIHN0aWNrIHRvIHRoZSB0aW1lIG9uIHRoZSBtb2JpbGUgcGhvbmUhCmBgYAoKVGhlIGZvbGxvd2luZyBtZXRob2QgaXMgKipjb3JyZWN0Kio6CgpgYGBweXRob24KdG9kYXkgPSAuLi4gIyBHZXQgdG9kYXkncyBkYXRlIGZyb20gdGhlIG1vYmlsZSBwaG9uZS4KIyBPbmx5IHRoZW4gY2FuIHlvdSB1c2UgdGhlIGRhdGV0aW1lIGxpYnJhcnkgdG8gY2FsY3VsYXRlIGRhdGVzLgpgYGAKCjkuIEZvciBhbnkgdGFzayBpbnZvbHZpbmcgdmlld2luZywgZGVsZXRpbmcsIG9yIG1vZGlmeWluZyBlbnRyaWVzLCB5b3UgKiptdXN0IGNsaWNrIGludG8gdGhlIGVudHJ5IHRvIHZpZXcgZGV0YWlsZWQgaW5mb3JtYXRpb24qKiwgcmF0aGVyIHRoYW4gc2ltcGx5IGxvb2tpbmcgYXQgaXQgaW4gdGhlIHRodW1ibmFpbC9saXN0IHZpZXcgYW5kIGZpbmlzaGluZy4gVGh1bWJuYWlscyB1c3VhbGx5IGNvbnRhaW4gZWxsaXBzZXMgb3IgIk1vcmUuLi4iIHByb21wdHMsIHJlbWluZGluZyB5b3UgdGhhdCB5b3UgbmVlZCB0byBjbGljayBpbiB0byBzZWUgdGhlIGNvbnRlbnQgYmVjYXVzZSB0aGUgaW5mb3JtYXRpb24gaXMgdHJ1bmNhdGVkIGFuZCB5b3UgY2Fubm90IHNlZSBpdCBjb21wbGV0ZWx5IGZyb20gdGhlIG91dHNpZGUuICoqUmVtZW1iZXIgdGhpcyEgRmFpbGluZyB0byBkbyBzbyB3aWxsIHJlc3VsdCBpbiBmYWlsdXJlISoqCjEwLiBSZWdhcmRpbmcgZGF0ZXMsICJ0aGlzIHtkYXlfb2Zfd2Vla30iIHJlZmVycyB0byB0aGUge2RheV9vZl93ZWVrfSB0aGF0IGhhcyBub3QgeWV0IGFycml2ZWQuIEZvciBleGFtcGxlLCBpZiB0b2RheSBpcyBTYXR1cmRheSwgInRoaXMgVHVlc2RheSIgbWVhbnMgdGhlICpuZXh0KiB1cGNvbWluZyBUdWVzZGF5LCBub3QgdGhlIFR1ZXNkYXkgdGhhdCBoYXMgYWxyZWFkeSBwYXNzZWQuIFRoZXJlZm9yZSwgYmUgdmVyeSBjbGVhciB3aGVuIGNhbGN1bGF0aW5nIGRhdGVzIHRvIGF2b2lkIGVycm9ycy4KMTEuIElmIHlvdSBmaW5kIHRoYXQgdGhlIHNhbWUgYG1vYmlsZS5jbGljay9pbnB1dGAgb3BlcmF0aW9uIGlzIGNvbnNpc3RlbnRseSBpbnZhbGlkIGFmdGVyIG11bHRpcGxlIGF0dGVtcHRzLCB5b3UgY2FuIHRyeSBjaGFuZ2luZyBpdHMgYHZpZXdfZGVzY3JpcHRpb25gIHBhcmFtZXRlci4gTWFrZSB0aGUgYHZpZXdfZGVzY3JpcHRpb25gIG1vcmUgZGV0YWlsZWQgYW5kIHNwZWNpZmljIHRvIG1ha2UgaXRzIHNjb3BlIG1vcmUgcHJlY2lzZSwgYXZvaWRpbmcgYW1iaWd1aXR5IG9yIGVycm9ycyBpbiB0aGUgcG9zaXRpb25pbmcgcHJvY2Vzcy4KCkhlcmUgYXJlIHNvbWUgZXhhbXBsZXMgZm9yIHlvdToKCltFeGFtcGxlIDEgU3RhcnRdCmBgYHB5dGhvbgphaV9wYXBlcl90YWJsZSA9IFtdCm1vYmlsZS5zdGFydF9hcHAoYXBwX25hbWU9IkJhaWR1IikKIyBVc2UgbW9iaWxlLmlucHV0IGRpcmVjdGx5IGFuZCBwcm92aWRlIHZpZXdfZGVzY3JpcHRpb24KbW9iaWxlLmlucHV0KHZpZXdfZGVzY3JpcHRpb249IlNlYXJjaCBib3giLCB0ZXh0PSJBSSIpCmFzc2VydCBtb2JpbGUuY2hlY2soZGVzY3JpcHRpb249IkFJIGhhcyBiZWVuIGlucHV0IGludG8gdGhlIHNlYXJjaCBib3guIikgICMgY2hlY2tfcmVzdWx0IHNob3VsZCBiZSBUcnVlCiMgVXNlIG1vYmlsZS5jbGljayBkaXJlY3RseSBhbmQgcHJvdmlkZSB2aWV3X2Rlc2NyaXB0aW9uCm1vYmlsZS5jbGljayh2aWV3X2Rlc2NyaXB0aW9uPSJCYWlkdSBTZWFyY2ggQnV0dG9uIikKYXNzZXJ0IG1vYmlsZS5jaGVjayhkZXNjcmlwdGlvbj0iU2VhcmNoIHJlc3VsdCBwYWdlIGZvciBgQUlgIikgICMgY2hlY2tfcmVzdWx0IHNob3VsZCBiZSBUcnVlCmBgYApbRXhhbXBsZSAxIEVuZF0KCltFeGFtcGxlIDIgU3RhcnRdCmBgYHB5dGhvbgptb2JpbGUuc3RhcnRfYXBwKGFwcF9uYW1lPXNvbWVfYXBwKQouLi4KIyBTd2lwZSB0aGUgcG9zdCBsaXN0Cm1vYmlsZS5zd2lwZV91cHdhcmQodmlld19kZXNjcmlwdGlvbj0iPFRpdGxlIG9mIGEgcG9zdCBhdCB0aGUgYm90dG9tPiIsIGRpc3RhbmNlPTQwMCkgIyBGaXJzdCBkZXRlcm1pbmUgdGhlIHN3aXBlIHN0YXJ0IHBvaW50IGFzIGEgcG9zdCBhdCB0aGUgYm90dG9tLCB0aGVuIHN3aXBlIHVwd2FyZCB0byB2aWV3IHBvc3RzIGZ1cnRoZXIgZG93bi4gTm90ZTogWW91IG11c3Qgd3JpdGUgdGhlIHNwZWNpZmljIHRpdGxlIG5hbWUuCiMgU3dpcGUgdGhlIHBvc3QgbGlzdCB1bnRpbCB0aGUgdGFyZ2V0IHBvc3QgaXMgZm91bmQsIG1heCBhdHRlbXB0cyAxMC4gVGhpcyBpcyBzbWFydGVyIGFuZCBjYW4gc3dpcGUgY29udGludW91c2x5Lgptb2JpbGUuc3dpcGVfdW50aWwodmlld19kZXNjcmlwdGlvbj0iPFRpdGxlIG9mIGEgcG9zdCBhdCB0aGUgYm90dG9tPiIsIGV4cGVjdGVkX2Rlc2M9IkhlbGxvIHdvcmxkIiwgdG93YXJkcz0ndXAnLCBtYXhfcmV0cnk9MTApICMgU3dpcGUgZG93bndhcmQgKGNvbnRlbnQgbW92ZXMgdXApIHVudGlsIHRoZSBwb3N0IG5hbWVkICdIZWxsbyB3b3JsZCcgaXMgZm91bmQuIE5vdGU6IFlvdSBtdXN0IHdyaXRlIHRoZSBzcGVjaWZpYyB0aXRsZSBuYW1lIGFzIHRoZSBzdGFydCBwb2ludC4KcG9zdF9saXN0ID0gbGxtLnF1ZXJ5KG1vYmlsZS50YWtlX3NjcmVlbnNob3QoKSwgIkxpc3QgdGhlIHBvc3RzIGN1cnJlbnRseSBkaXNwbGF5ZWQgb24gdGhlIHNjcmVlbiIsIHJldHVybnM9KCJQb3N0IGxpc3QiLCBsaXN0W3N0cl0pKSAjIFVzaW5nIGxsbS5xdWVyeSBjb21iaW5lZCB3aXRoIG1vYmlsZS50YWtlX3NjcmVlbnNob3QoKSBhbGxvd3MgZm9yIFEmQSBhYm91dCB0aGUgc2NyZWVuIGludGVyZmFjZS4KYGBgCltFeGFtcGxlIDIgRW5kXQoKW0V4YW1wbGUgMyBTdGFydF0KYGBgcHl0aG9uCm1vYmlsZS5zdGFydF9hcHAoYXBwX25hbWU9c29tZV9hcHApCi4uLgojIERyYWcgdGhlIGJhciB0byB0aGUgZmFyIHJpZ2h0Cm1vYmlsZS5zd2lwZV9yaWdodHdhcmQodmlld19kZXNjcmlwdGlvbj0idGhlIHJpZ2h0IHBhcnQgb2YgdGhlIGJhciIsIGRpc3RhbmNlPTQwMCkgIyBQb3NpdGlvbiB0aGUgc3dpcGUgY2VudGVyIG9uIHRoZSByaWdodCBzaWRlIGFuZCBkcmFnIGl0IGEgbG9uZyBkaXN0YW5jZSB0byB0aGUgcmlnaHQgdG8gZW5zdXJlIGl0IHNsaWRlcyB0byB0aGUgZmFyIHJpZ2h0LgpgYGAKW0V4YW1wbGUgMyBFbmRdCgoqKlJlbWVtYmVyIGFnYWluOioqCgoxLiBJZiB5b3Ugd2FudCB0byBvcGVuIGFuIEFQUCwgeW91IHNob3VsZCB1c2UgYG1vYmlsZS5zdGFydF9hcHAoYXBwX25hbWUpYCB0byBvcGVuIGl0LCBpbnN0ZWFkIG9mIHRyeWluZyB0byBmaW5kIHRoZSBBUFAgYnkgc3dpcGluZy4KMi4gVGhlIG1vYmlsZSBwaG9uZSBpcyBjb25maWd1cmVkIHZpYSBhIHZpcnR1YWwgbWlycm9yOyBpdHMgZGF0ZSBhbmQgdGltZSBhcmUgZGlmZmVyZW50IGZyb20gdGhlIHJlYWwtd29ybGQgZGF0ZSBhbmQgdGltZSEhIFRoZSBkYXRlcyByZWZlcnJlZCB0byBpbiB0aGUgQ3VycmVudCBUYXNrIGFyZSBiYXNlZCBvbiB0aGUgKipkYXRlIG9uIHRoZSBtb2JpbGUgcGhvbmUqKiwgbm90IHRoZSBkYXRlIGluIHJlYWxpdHkhIFRoZXJlZm9yZSwgcGxlYXNlIG1ha2Ugc3VyZSB0byBlbXBoYXNpemUgdXNpbmcgdGhlIGRhdGUgYW5kIHRpbWUgZnVuY3Rpb25zIG9uIHRoZSBtb2JpbGUgcGhvbmUgdG8gY2hlY2sgdG9kYXkncyBkYXRlIGFuZCB0aW1lLCByYXRoZXIgdGhhbiBnZXR0aW5nIHRoZSByZWFsIGRhdGUgdmlhIFB5dGhvbidzIGBkYXRldGltZWAgbW9kdWxlISBBZnRlciBvYnRhaW5pbmcgInRvZGF5J3MiIGRhdGUgZnJvbSB0aGUgbW9iaWxlIHBob25lLCB5b3Ugc2hvdWxkIHVzZSB0aGUgYGRhdGV0aW1lYCBtb2R1bGUgdG8gY2FsY3VsYXRlIG90aGVyIGRhdGVzIGJhc2VkIG9uIHRoZSBtb2JpbGUgcGhvbmUncyAidG9kYXkiLgoKRm9yIGV4YW1wbGUsIHRoZSBmb2xsb3dpbmcgbWV0aG9kIGlzICoqd3JvbmcqKjoKCmBgYHB5dGhvbgppbXBvcnQgZGF0ZXRpbWUKdG9kYXlfZGF0ZSA9IGRhdGV0aW1lLmRhdGUudG9kYXkoKSAjIFdST05HLCBiZWNhdXNlIHRoaXMgZ2V0cyB0aGUgdGltZSBvbiB0aGUgUHl0aG9uIGV4ZWN1dG9yLCBub3QgdGhlIHRpbWUgaW4gdGhlIG1vYmlsZSB2aXJ0dWFsIG1hY2hpbmUhIFlvdSBzaG91bGQgc3RpY2sgdG8gdGhlIHRpbWUgb24gdGhlIG1vYmlsZSBwaG9uZSEKYGBgCgpUaGUgZm9sbG93aW5nIG1ldGhvZCBpcyAqKmNvcnJlY3QqKjoKCmBgYHB5dGhvbgp0b2RheSA9IC4uLiAjIEdldCB0b2RheSdzIGRhdGUgZnJvbSB0aGUgbW9iaWxlIHBob25lLgojIE9ubHkgdGhlbiBjYW4geW91IHVzZSB0aGUgZGF0ZXRpbWUgbGlicmFyeSB0byBjYWxjdWxhdGUgZGF0ZXMuCmBgYAoKMy4gRm9yIGFueSB0YXNrIGludm9sdmluZyB2aWV3aW5nLCBkZWxldGluZywgb3IgbW9kaWZ5aW5nIGVudHJpZXMsIHlvdSAqKm11c3QgY2xpY2sgaW50byB0aGUgZW50cnkgdG8gdmlldyBkZXRhaWxlZCBpbmZvcm1hdGlvbioqLCByYXRoZXIgdGhhbiBzaW1wbHkgbG9va2luZyBhdCBpdCBpbiB0aGUgdGh1bWJuYWlsL2xpc3QgdmlldyBhbmQgZmluaXNoaW5nLiBUaHVtYm5haWxzIHVzdWFsbHkgY29udGFpbiBlbGxpcHNlcyBvciAiTW9yZS4uLiIgcHJvbXB0cywgcmVtaW5kaW5nIHlvdSB0aGF0IHlvdSBuZWVkIHRvIGNsaWNrIGluIHRvIHNlZSB0aGUgY29udGVudCBiZWNhdXNlIHRoZSBpbmZvcm1hdGlvbiBpcyB0cnVuY2F0ZWQgYW5kIHlvdSBjYW5ub3Qgc2VlIGl0IGNvbXBsZXRlbHkgZnJvbSB0aGUgb3V0c2lkZS4gKipSZW1lbWJlciB0aGlzISBGYWlsaW5nIHRvIGRvIHNvIHdpbGwgcmVzdWx0IGluIGZhaWx1cmUhKioKNC4gSWYgeW91IGZpbmQgdGhhdCB0aGUgc2FtZSBgbW9iaWxlLmNsaWNrL2lucHV0YCBvcGVyYXRpb24gaXMgY29uc2lzdGVudGx5IGludmFsaWQgYWZ0ZXIgbXVsdGlwbGUgYXR0ZW1wdHMsIHlvdSBjYW4gdHJ5IGNoYW5naW5nIGl0cyBgdmlld19kZXNjcmlwdGlvbmAgcGFyYW1ldGVyLiBNYWtlIHRoZSBkZXNjcmlwdGlvbiBtb3JlIGRldGFpbGVkIGFuZCBzcGVjaWZpYyB0byBtYWtlIGl0cyBzY29wZSBtb3JlIHByZWNpc2UsIGF2b2lkaW5nIGFtYmlndWl0eSBvciBlcnJvcnMgaW4gdGhlIGNsaWNraW5nIHByb2Nlc3MuCgp7Y3VycmVudF9kYXRlX2luZm99)

1
- \*\*mobile\*\*: Primitives for manipulating mobile devices.

2
 - The following APIs are only available for Android devices:

3
 - ‘mobile.start\_app(app\_name: str)‘: Open the app named ‘app\_name‘.

4
 - ‘mobile.kill\_app(app\_name: str)‘: Kill the app named ‘app\_name‘.

5
 - The following APIs are available for all devices:

6
 - ‘mobile.get\_input\_field\_text(view\_description: str) -> str‘: Get the text from the input field specified by ‘view\_description‘.

7
 - ‘mobile.get\_clipboard()‘: Get the text from the clipboard.

8
 - ‘mobile.set\_clipboard(text: str)‘: Set the text to the clipboard.

9
 - ‘mobile.expand\_notification\_panel()‘: Expand the notification panel. This includes Internet, Bluetooth, Flashlight, and so on.

10
 - ‘mobile.take\_screenshot() -> PIL.Image‘: Take a screenshot of the current screen and return a PIL image. Note: This is not for "taking a photo" using the mobile phone. For taking photos, you should use the camera app instead.

11
 - ‘mobile.back()‘: Navigate back from the current screen.

12
 - ‘mobile.home()‘: Navigate to the home screen.

13
 - ‘mobile.back\_to(description: str, max\_steps=5)‘: Navigate back to the view described by ‘description‘. ‘max\_steps‘ is the maximum number of steps to navigate.

14
 - ‘mobile.swipe\_upward(view\_description: str, distance=None)‘: Swipe up on the view specified by ‘view\_description‘. ‘distance‘ is a number to control the distance for the swipe action, e.g., ‘mobile.swipe\_upward(view\_description="scroll\_view", distance=100)‘.

15
 - ‘mobile.swipe\_downward(view\_description: str, distance=None)‘: Swipe down on the view specified by ‘view\_description‘. ‘distance‘ is a number to control the distance for the swipe action.

16
 - ‘mobile.swipe\_leftward(view\_description: str, distance=None)‘: Swipe left on the view specified by ‘view\_description‘. ‘distance‘ is a number to control the distance for the swipe action.

17
 - ‘mobile.swipe\_rightward(view\_description: str, distance=None)‘: Swipe right on the view specified by ‘view\_description‘. ‘distance‘ is a number to control the distance for the swipe action.

18
 - ‘mobile.swipe\_until(view\_description: str, expected\_desc: str, towards: "up", duration=1000, max\_retry: int = 10) -> bool‘: Swipe the view specified by ‘view\_description‘ until ‘expected\_desc‘ is fulfilled. If the desired view appears, return True; otherwise, return False.

19
 - ‘mobile.wait\_until(description: str, waitInterval:float=0.5, timeout=5) -> bool‘: Wait for a view described by ‘description‘ to appear and return it. ‘timeout‘ is the time limit (in seconds) for waiting. ‘-1‘ means unlimited. If the desired view appears, return True; otherwise, return False.

20
 - ‘mobile.check(description: str) -> bool‘: Check whether the current screen state matches ‘description‘. If matched, returns True; otherwise, returns False.

21
 - ‘mobile.click(view\_description: str)‘: Click the view specified by ‘view\_description‘.

22
 - ‘mobile.input(view\_description: str, text: str)‘: Clear the input field specified by ‘view\_description‘ and input the given text. You don’t have to call a keyboard; use this input method directly.

23
 - ‘mobile.input\_by\_pasting(view\_description: str, text: str)‘: Input text into the view specified by ‘view\_description‘ by pasting. Use the ‘input\_by\_pasting‘ API when standard input doesn’t work, such as in the WeChat app.

24
 - ‘mobile.long\_click(view\_description: str)‘: Long click the view specified by ‘view\_description‘ for 1 second.

25
 - \*\*Note\*\*: UI operations are distinct. In Code Generation mode, it is best to generate only one step at a time for these UI operations because every UI operation changes the environment. You should proceed step-by-step; otherwise, errors can easily occur.

26

27
- \*\*llm\*\*: The interfaces to get answers from foundation models.

28
 - ‘llm.query(prompt\_or\_image1, ..., prompt\_or\_imagen, returns)‘: Query a large language model. Positional arguments can be a list of string prompts or images. The keyword parameter ‘returns‘ specifies the expected return type and description for function outputs. It supports the following formats:

29
 1. \*\*Single Typed Return\*\*:

30
 - Returns a single value parsed according to the specified type.

31
 - First element: Description of the return value.

32
 - Second element: Expected type of the return value.

33
 - Example: ‘returns=("age", int)‘ -> function returns the parsed age value as an integer.

34
 - Example: ‘returns=("items", list[str])‘ -> function returns a list of strings representing the items.

35

36
 2. \*\*Multiple Returns\*\*: (Pay close attention: the outer layer must be wrapped in a list, while the description is wrapped in a tuple!!)

37
 - Returns multiple values with optional type specifications.

38
 - Each element can be either:

39
 a) str: Description only (assumes str type).

40
 b) tuple: (description, type) pair.

41
 - Example: ‘returns=["name", ("age", int)]‘ # For instance, here the return value is defined as two elements. The first is a string described as "name" (equivalent to ‘("name", str)‘). The second is an integer described as "age" (note it is ‘("age", int)‘, not ‘["age", int]‘!!). If your ‘llm.query‘ call fails, you must reflect on whether you met the format requirements I stated.

42
 -> ‘[string\_name, parsed\_integer\_age]‘

43
 - Example: ‘returns=[("items", list[str]), ("count", int)]‘

44
 -> ‘[parsed\_list\_of\_strings, parsed\_integer]‘

45
 - Specific usage example: ‘reign\_name, reign\_period, main\_events, contemporary\_west, cultural\_exchange = llm.query(f"Please analyze the raw info into desired fields:", str(raw\_history\_info), returns=[("era name", str), ("reign period", str), ("major events", str), ("contemporary Western history", str), ("Sino-Western cultural exchange events", str)])‘. \*\*Note\*\*: You must input the data information you want to analyze as a string or image; do not just give a prompt without data. Without data (like ‘raw\_history\_info‘ in the example), the large model cannot answer correctly.

46

47
 3. \*\*Complex Requests\*\*: Nested lists, dictionaries, and ‘llm.query‘ support these as well. Reference documentation follows:

48
 - ‘llm‘ supports all the following request types:

49
 3.1. \*\*Basic Types\*\*:

50
 Supports ‘bool‘, ‘int‘, ‘float‘, ‘str‘, constants (e.g., ‘"test"‘).

51

52
 3.2. \*\*Sum of Basic Types\*\*:

53
 Supports sum type declarations like ‘bool | int‘.

54

55
 3.3. \*\*Homogeneous List Type\*\*:

56
 e.g., ‘list[str]‘ indicates a list where the element type is ‘str‘.

57

58
 3.4. \*\*Homogeneous Key, Homogeneous Value Dictionary Type\*\*:

59
 e.g., ‘dict[str, int]‘ indicates a dictionary with keys of type ‘str‘ and values of type ‘int‘, with arbitrary length.

60

61
 3.5. \*\*Nested Lists\*\*:

62
 If you need finer control over lists, you can replace ‘list‘ with ‘[<type spec>]‘. The nested element type ‘<type spec>‘ can be any type conforming to the rules in this document.

63

64
 3.5.1 \*\*Fixed Length List\*\*:

65
 e.g., ‘[str, int, int]‘ indicates a list of length 3, where the first element is ‘str‘, the second is ‘int‘, and the third is ‘int‘.

66

67
 3.5.2 \*\*Variable Length List\*\*:

68
 The list length is not fixed. In this case, the last element of the list must be ‘...‘. e.g., ‘[int, str, ...]‘ indicates a list of arbitrary length where each element can be ‘int‘ or ‘str‘.

69
 Using ‘[int | str, ...]‘ also conveys this meaning.

70

71
 3.6. \*\*Nested Dictionaries\*\*:

72
 If you need finer control over dictionary formats, you can replace ‘dict‘ with ‘{<string1\_constant>: <type spec1>, <string2\_constant>: <type spec2>, ...}‘. The nested key type ‘<type spec1>‘ and value type ‘<type spec2>‘ can be any type conforming to the rules in this document (provided it is supported by Python; for example, ‘{[1]: 1}‘ will error in Python).

73

74
 3.6.1 \*\*Fixed Length Dictionary\*\*:

75
 e.g., ‘{"math": int, "english": int}‘ indicates a dictionary with two key-value pairs, where the keys must be the constants "math" and "english", and the corresponding values are basic types ‘int‘ and ‘int‘. \*\*Note: The dictionary length is fixed! Furthermore, key names must be constant strings; do not use the ‘{str: int}‘ syntax! If you need a variable-length dictionary, use the ‘Homogeneous Key, Homogeneous Value Dictionary Type‘.\*\*

76

77
 3.7. \*\*Annotations (Description)\*\*:

78
 You can insert annotation descriptions into the types defined in this document. The method is to replace the type ‘<type spec>‘ with ‘(<description>, <type spec>)‘. For example: ‘("age", int)‘ is equivalent to ‘int‘; ‘{"math": ("score", int)}‘ is equivalent to ‘{"math": int}‘. Type annotations support nesting; you can insert annotations wherever appropriate. These annotations will be provided to the large model, enabling it to reply more accurately. It is recommended to use them frequently.

79

80
 For example, you can generate the following code for every step:

81
 [Example Start]

82
 # Step 1: Preparation

83
 dynasty\_info\_table = []

84

85
 # Step 2: Get dynasty list

86
 dynasty\_list = llm.query(

87
 "Please list all major dynasties in Chinese history, such as Qin, Han, Tang, Song, Yuan, Ming, Qing, etc.",

88
 returns=[(’dynasty list’, list[str])]

89
 )

90

91
 # Step 3: Traverse each dynasty and emperor

92
 for current\_dynasty in dynasty\_list:

93

94
 # 3.1 Get all emperors of current dynasty

95
 emperor\_list = llm.query(

96
 f"Please list all emperor names of {current\_dynasty}",

97
 returns=[(’emperor list’, list[str])]

98
 )

99

100
 # 3.2 Traverse each emperor of current dynasty

101
 for current\_emperor in emperor\_list:

102
 # 3.2.1 Detailed query

103
 prompt = f"Please provide detailed information about ’{current\_emperor}’ of ’{current\_dynasty}’, specifically including: 1. Their commonly used era names; 2. Reign start and end dates; 3. Major historical events during their reign; 4. Corresponding Western historical periods or major countries during their reign; 5. Representative Sino-Western cultural exchange events of this period."

104
 reign\_name, reign\_period, main\_events, contemporary\_west, cultural\_exchange = llm.query(

105
 prompt,

106
 returns=[

107
 ("era name", str),

108
 ("reign period", str),

109
 ("major events", str),

110
 ("contemporary Western history", str),

111
 ("Sino-Western cultural exchange events", str)

112
 ]

113
 )

114

115
 # 3.2.2 Add to data table

116
 dynasty\_info\_table.append({

117
 "Dynasty": current\_dynasty,

118
 "Era Name": reign\_name,

119
 "Emperor": current\_emperor,

120
 "Reign Period": reign\_period,

121
 "Major Events": main\_events,

122
 "Contemporary Western History": contemporary\_west,

123
 "Sino-Western Cultural Exchange Events": cultural\_exchange

124
 })

125

126
 [Example End]

127

128
 \*\*Note\*\*:

129
 1. ‘llm.query‘ is extremely useful. If you encounter irregular data items, you can directly call ‘llm.query‘ to have the large model organize them into regular data. Or, if there are calculation problems that are hard to solve, you can call ‘llm.query‘ to ask the large model to solve them.

130

131
\*\*Note:\*\*

132

133
1. When using the above framework, it is best to proceed step-by-step; do not click a large number of items in one go.

134
2. Successful code execution does not imply it meets expectations. Often ‘mobile.click/input‘ may fail. We suggest using ‘check‘ to set interface checkpoints to ensure the interface after each operation meets expectations.

135
3. You don’t have to call a keyboard to input text, but use the ‘mobile.input(...)‘ method directly.

136
4. If you want to open an APP, you should use ‘mobile.start\_app(app\_name)‘ to open it, instead of trying to find the APP by swiping.

137
5. If ‘mobile.start\_app(app\_name)‘ fails to open the app, it may be because the task stack in the current device is not cleared. Try using multiple returns (using ‘mobile.back()‘) to clear the current task stack, and then attempt to open the app again.

138
6. If you need to turn a system setting on or off, you need to first write a conditional check to see if it is in the expected state. If it is not in the expected state, then operate the switch. This ensures the setting is correctly opened or closed and avoids maloperation. For example:

139

140
‘‘‘python

141
judge = mobile.check("the airplane mode is off.")

142
if judge:

143
 # Here you need to click the switch based on the specific view description

144
 mobile.click(view\_description="Airplane mode switch")

145
‘‘‘

146

147
8. The mobile phone is configured via a virtual mirror; its date and time are different from the real-world date and time!! The dates referred to in the Current Task are based on the \*\*date on the mobile phone\*\*, not the date in reality! Therefore, please make sure to emphasize using the date and time functions on the mobile phone to check today’s date and time, rather than getting the real date via Python’s ‘datetime‘ module! After obtaining "today’s" date from the mobile phone, you can then use the ‘datetime‘ module to calculate other dates based on the mobile phone’s "today".

148

149
For example, the following method is \*\*wrong\*\*:

150

151
‘‘‘python

152
import datetime

153
today\_date = datetime.date.today() # WRONG, because this gets the time on the Python executor, not the time in the mobile virtual machine! You should stick to the time on the mobile phone!

154
‘‘‘

155

156
The following method is \*\*correct\*\*:

157

158
‘‘‘python

159
today = ... # Get today’s date from the mobile phone.

160
# Only then can you use the datetime library to calculate dates.

161
‘‘‘

162

163
9. For any task involving viewing, deleting, or modifying entries, you \*\*must click into the entry to view detailed information\*\*, rather than simply looking at it in the thumbnail/list view and finishing. Thumbnails usually contain ellipses or "More..." prompts, reminding you that you need to click in to see the content because the information is truncated and you cannot see it completely from the outside. \*\*Remember this! Failing to do so will result in failure!\*\*

164
10. Regarding dates, "this {day\_of\_week}" refers to the {day\_of\_week} that has not yet arrived. For example, if today is Saturday, "this Tuesday" means the \*next\* upcoming Tuesday, not the Tuesday that has already passed. Therefore, be very clear when calculating dates to avoid errors.

165
11. If you find that the same ‘mobile.click/input‘ operation is consistently invalid after multiple attempts, you can try changing its ‘view\_description‘ parameter. Make the ‘view\_description‘ more detailed and specific to make its scope more precise, avoiding ambiguity or errors in the positioning process.

166

167
Here are some examples for you:

168

169
[Example 1 Start]

170
‘‘‘python

171
ai\_paper\_table = []

172
mobile.start\_app(app\_name="Baidu")

173
# Use mobile.input directly and provide view\_description

174
mobile.input(view\_description="Search box", text="AI")

175
assert mobile.check(description="AI has been input into the search box.") # check\_result should be True

176
# Use mobile.click directly and provide view\_description

177
mobile.click(view\_description="Baidu Search Button")

178
assert mobile.check(description="Search result page for ‘AI‘") # check\_result should be True

179
‘‘‘

180
[Example 1 End]

181

182
[Example 2 Start]

183
‘‘‘python

184
mobile.start\_app(app\_name=some\_app)

185
...

186
# Swipe the post list

187
mobile.swipe\_upward(view\_description="<Title of a post at the bottom>", distance=400) # First determine the swipe start point as a post at the bottom, then swipe upward to view posts further down. Note: You must write the specific title name.

188
# Swipe the post list until the target post is found, max attempts 10. This is smarter and can swipe continuously.

189
mobile.swipe\_until(view\_description="<Title of a post at the bottom>", expected\_desc="Hello world", towards=’up’, max\_retry=10) # Swipe downward (content moves up) until the post named ’Hello world’ is found. Note: You must write the specific title name as the start point.

190
post\_list = llm.query(mobile.take\_screenshot(), "List the posts currently displayed on the screen", returns=("Post list", list[str])) # Using llm.query combined with mobile.take\_screenshot() allows for Q&A about the screen interface.

191
‘‘‘

192
[Example 2 End]

193

194
[Example 3 Start]

195
‘‘‘python

196
mobile.start\_app(app\_name=some\_app)

197
...

198
# Drag the bar to the far right

199
mobile.swipe\_rightward(view\_description="the right part of the bar", distance=400) # Position the swipe center on the right side and drag it a long distance to the right to ensure it slides to the far right.

200
‘‘‘

201
[Example 3 End]

202

203
\*\*Remember again:\*\*

204

205
1. If you want to open an APP, you should use ‘mobile.start\_app(app\_name)‘ to open it, instead of trying to find the APP by swiping.

206
2. The mobile phone is configured via a virtual mirror; its date and time are different from the real-world date and time!! The dates referred to in the Current Task are based on the \*\*date on the mobile phone\*\*, not the date in reality! Therefore, please make sure to emphasize using the date and time functions on the mobile phone to check today’s date and time, rather than getting the real date via Python’s ‘datetime‘ module! After obtaining "today’s" date from the mobile phone, you should use the ‘datetime‘ module to calculate other dates based on the mobile phone’s "today".

207

208
For example, the following method is \*\*wrong\*\*:

209

210
‘‘‘python

211
import datetime

212
today\_date = datetime.date.today() # WRONG, because this gets the time on the Python executor, not the time in the mobile virtual machine! You should stick to the time on the mobile phone!

213
‘‘‘

214

215
The following method is \*\*correct\*\*:

216

217
‘‘‘python

218
today = ... # Get today’s date from the mobile phone.

219
# Only then can you use the datetime library to calculate dates.

220
‘‘‘

221

222
3. For any task involving viewing, deleting, or modifying entries, you \*\*must click into the entry to view detailed information\*\*, rather than simply looking at it in the thumbnail/list view and finishing. Thumbnails usually contain ellipses or "More..." prompts, reminding you that you need to click in to see the content because the information is truncated and you cannot see it completely from the outside. \*\*Remember this! Failing to do so will result in failure!\*\*

223
4. If you find that the same ‘mobile.click/input‘ operation is consistently invalid after multiple attempts, you can try changing its ‘view\_description‘ parameter. Make the description more detailed and specific to make its scope more precise, avoiding ambiguity or errors in the clicking process.

224

225
{current\_date\_info}
