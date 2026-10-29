---
title: "ActionEngine : From Reactive to Programmatic GUI Agents via State Machine Memory"
arxiv_html: https://arxiv.org/html/2602.20502v1
downloaded: 2026-10-29
converted: arxiv LaTeXML HTML -> Markdown（本地图片 + alttext 公式还原）
---

# ActionEngine: From Reactive to Programmatic GUI Agents via State Machine Memory

- **Hongbin Zhong** · Georgia Tech , USA · hzhong81@gatech.edu
- **Fazle Faisal** · Microsoft Research , USA · fafaisal@microsoft.com
- **Luis França** · Microsoft Research , USA · luis.franca@microsoft.com
- **Tanakorn Leesatapornwongsa** · Microsoft Research , USA · taleesat@microsoft.com
- **Adriana Szekeres** · Microsoft Research , USA · aszekeres@microsoft.com
- **Kexin Rong** · Georgia Tech , USA · krong@gatech.edu
- **Suman Nath** · Microsoft Research , USA · Suman.Nath@microsoft.com

###### Abstract.

Existing Graphical User Interface (GUI) agents operate through step-by-step calls to vision language models–taking a screenshot, reasoning about the next action, executing it, then repeating on the new page–resulting in high costs and latency that scale with the number of reasoning steps, and limited accuracy due to no persistent memory of previously visited pages.
We propose ActionEngine, a training-free framework that transitions from reactive execution to programmatic planning through a novel two-agent architecture: a Crawling Agent that constructs an updatable state-machine memory of the GUIs through offline exploration, and an Execution Agent that leverages this memory to synthesize complete, executable Python programs for online task execution.
To ensure robustness against evolving interfaces, execution failures trigger
a vision-based re-grounding fallback that repairs the failed action and updates the memory.
This design drastically improves both efficiency and accuracy: on Reddit tasks from the WebArena benchmark, our agent achieves 95% task success with on average a single LLM call, compared to 66% for the strongest vision-only baseline, while reducing cost by 11.8 $\times$ and end-to-end latency by 2 $\times$ .
Together, these components yield scalable and reliable GUI interaction by combining global programmatic planning, crawler-validated action templates, and node-level execution with localized validation and repair.

## 1. Introduction

Autonomous GUI agents ([Nguyen et al., 2025](#bib.bib11)) (including Web agents ([Ning et al., 2025](#bib.bib12)) and App agents ([Zhang et al., 2025b](#bib.bib19))) are designed to enhance the human-computer interaction by automating complex tasks that require interacting with GUI elements (such as clicking, typing,
and navigating across diverse
platforms) ([Zhou et al., 2023](#bib.bib22); [Deng et al., 2023](#bib.bib4); [Nguyen et al., 2025](#bib.bib11)).
For example, instead of manually clicking through pages/windows, a user can simply ask a GUI agent to “find the user who posted the latest comment on a Reddit forum and count their upvotes." The rapid advancement of Multimodal Large Language Models (MLLM) has enabled these agents to interpret GUIs with increasing sophistication ([Deng et al., 2023](#bib.bib4); [Wang et al., 2023](#bib.bib16); [Nguyen et al., 2025](#bib.bib11)). Recent benchmarks for Web agents, such as WebArena, Mind2Web and AgentBench ([Zhou et al., 2023](#bib.bib22); [Deng et al., 2023](#bib.bib4); [Liu et al., 2023](#bib.bib9)), highlight the potential of these systems to navigate real-world websites and also illustrate the challenges of real-world web interactions.

Existing GUI agents largely follow a step-by-step *reactive* paradigm
([Figure 1](#S1.F1), top), where reasoning and action are interleaved
within an observe–reason–act loop ([Nguyen et al., 2025](#bib.bib11); [Ning et al., 2025](#bib.bib12)).
At each step, the agent observes the current application state, through a screenshot ([Niu et al., 2024](#bib.bib13); [Cheng et al., 2024](#bib.bib3)) and/or the HTML/DOM structure ([Tao et al., 2023](#bib.bib15); [Deng et al., 2023](#bib.bib4)).
It then invokes an MLLM to select the next action, executes that action and observes the new state.
This observe–reason–act loop repeats until task completion. The reactive approach
is intuitive and generalizable, as it closely mimics how users naturally
interact with GUI applications. We refer to agents operating under this paradigm as *reactive* GUI agents.

![](images/18_ActionEngine/motivation.svg)


Figure 1. Reactive vs. Programmatic Paradigms. Our approach (bottom) replaces $O(N)$ visual inferences with a single $O(1)$ planning phase, drastically reducing latency compared to the reactive baseline (top).

Reactive GUI agents share two fundamental limitations rooted in their architecture.
First, the step-by-step approach is both computationally expensive and prone to error accumulation.
Because the agent invokes the MLLM for each action, the number of model calls scales linearly with the number of steps in the task ( $O(N)$ ).
For instance, a task with 50 UI actions requires 50 separate, expensive LLM inferences.
Moreover, a single visual hallucination or incorrect reasoning in this process can disrupt the entire trajectory ([Cheng et al., 2024](#bib.bib3); [Tao et al., 2023](#bib.bib15)).
Second, existing agents develop only a myopic, task-specific understanding of the application ([Niu et al., 2024](#bib.bib13); [Cheng et al., 2024](#bib.bib3); [Yang et al., 2024](#bib.bib18)).
They effectively “learn” the application incrementally as they execute specific tasks, without forming a global model of how pages relate to each other, or how persistent GUI elements function across contexts.
As a result, agents often struggle to identify reusable components from previous solutions or compose them to solve new tasks.
Due to these compounding inefficiencies, even state-of-the-art reactive MLLM-based agents like SeeClick ([Cheng et al., 2024](#bib.bib3)) and ScreenAgent ([Niu et al., 2024](#bib.bib13)) achieve only $\approx$ 58% success rates on the WebArena benchmark.

![Refer to caption](images/18_ActionEngine/overview.png)


Figure 2. 
System architecture with two specialized agents. The Crawling Agent (top, offline) explores the website/app to construct and maintain the state-machine memory. The Execution Agent (bottom, online) uses this memory to generate a high-level program sketch, ground it into executable UI calls through graph search, and compile and execute the plan. When execution fails, an MLLM-based fallback recovers and updates the memory, while a Python validator handles logic errors.

To address these challenges, we propose ActionEngine, a framework that transitions GUI agents from reactive execution to global, programmatic planning.
Our key insight is to replace the iterative runtime reasoning with amortized preprocessing efforts on the target application.
This is enabled by a novel two-agent architecture:
during the offline phase, a crawling agent explores the application and constructs a task-agnostic representation of its structure; then at runtime, an execution agent uses this representation to generate and execute a complete, executable Python program in one shot.
Specifically, the crawling agent builds a compact state-machine graph for each application (*e.g.,* tens of nodes for large applications such as Reddit).
In this graph, nodes represent distinct page states (e.g., “Home Page”, “Forum List”) and edges represent concrete actions, such as clicking a button to transition to another page, or extracting specific contents on the current page.
This structured prior allows agents to treat GUI interaction as deterministic graph traversal rather than step-by-step, probabilistic MLLM reasoning.
Given a user task and the state-machine graph, the execution agent prompts a code-generating LLM to synthesize a complete, executable Python program in a single inference step.
As shown in Figure [1](#S1.F1) (bottom), LLM reasoning occurs only during this planning step; the subsequent execution proceeds deterministically without further model calls.
This programmatic paradigm effectively therefore reduces the reasoning overhead from $O(N)$ model calls to constant $O(1)$ planning cost for each task.
Finally, to ensure robustness against UI updates, we incorporate a Dynamic Adaptation Mechanism. If the pre-planned script fails at runtime, the system falls back to MLLM reasoning to resolve the anomaly and patches the memory graph for future runs.

In summary, we make the following contribution in this paper:

- •

  We propose a novel two-agent architecture that cleanly separates offline environment learning (via the Crawling Agent) from online task planning (via the Execution Agent). This decoupling enables efficient offline indexing while maintaining rapid online response times.
- •

  We introduce a *state machine graph* memory model that represents websites or apps as reusable states (nodes) and interactions as actionable transitions (edges). Unlike flat trajectory histories, this topological representation captures the functional structure of GUIs and enables efficient path reuse across tasks. A semi-automated Crawling Agent constructs this memory through offline exploration.
- •

  We design a program-based planning approach where the Execution Agent synthesizes complete Python scripts in a single LLM invocation, reducing planning complexity from $O(N)$ step-by-step calls to $O(1)$ one-shot generation. The agent leverages the pre-built state-machine graph to ground high-level task descriptions into executable programs through graph search and code generation.
- •

  We achieve 95% success rate on WebArena’s Reddit subset with an average of one LLM call per task, significantly outperforming reactive baselines (66%) while reducing end-to-end latency by $2\times$ and cost by $11.8\times$ .

Together, these components establish a new paradigm for memory-augmented, programmatic GUI agents. By combining the precision of symbolic state representations with the flexible reasoning of LLM, our work bridges the gap between rigid automation scripts and adaptive but costly visual agents, paving the way for more reliable and scalable autonomous web interaction.

## 2. System Overview

We introduce a novel two-agent architecture that separates the *application operation learning*–understanding an application’s structure and available interactions–from the *task planning and execution*.
The architecture involves a Crawling Agent, which operates *offline* to construct and maintain a structured model of the application in the form of a State Machine Graph (SMG), and an Execution Agent, which uses this model to plan and execute user tasks *online*.
Unlike traditional GUI agents that react step-by-step to raw visual observations, our system treats task automation as a one-shot program synthesis problem, shifting computational burden from expensive runtime visual processing to amortized offline preprocessing.
The system lifecycle, illustrated in [Figure 2](#S1.F2), consists of three phases:

1  Offline Construction (Crawling Agent). The Crawling Agent systematically explores the target GUI application to build and maintain the SMG – a directed graph whose nodes correspond to symbolic application *states* (e.g., a “Forum List" page) and whose edges represent *GUI operations* – a sequence of *GUI actions*, where each action interacts with a *single* GUI element (such as click, type, text box read, etc.) – that may result in state transitions (e.g., clicking the “Go to Post" button navigates from the forum list to a post page). We formally define the SMG in [Section 3.1](#S3.SS1). This agent operates independently in the background, continuously maintaining an up-to-date representation of the application.

2  Online Compilation (Execution Agent). Given a user task, the Execution Agent queries the SMG to synthesize a program to solve the task. It first generates a high-level program sketch in an intermediate representation (IR) that captures the logical control flow of the task but contains symbolic placeholders for concrete actions (e.g., “navigate to a specific forum (@forum\_name=’…’)”).
A custom compiler then resolves these placeholders by searching and composing paths in the SMG, grounding the IR into a fully specified *Execution Plan*.
At runtime, this plan is executed deterministically to complete the user request: GUI actions are executed through an automation tool (e.g., UI Automator ([Google, 2017](#bib.bib5)) for mobile apps, Playwright ([Microsoft, 2024](#bib.bib10)) for websites), and the code blocks are executed by the runtime interpreter.

3  Runtime Adaptation (Feedback Loop). During execution, if the observed environment deviates from the state machine (e.g., due to UI changes that invalidate selectors), the system falls backs to an MLLM-based mechanism to recover from the failure.
SMG updates are gated by a consistency check: failed actions are retried three times, and memory modifications are triggered only upon repeated failures.
Crucially, successful recoveries are committed back to the SMG, allowing the Crawling Agent’s knowledge to evolve based on execution-time discoveries without requiring full re-crawling.

This architecture achieves both efficiency and adaptability: the Crawling Agent’s offline investment enables the Execution Agent’s fast online response, while execution feedback continuously improves the memory quality.

The remainder of the paper details the system components. [Section 3](#S3) describes the Crawling Agent and the SMG construction process. [Section 4](#S4) presents the Execution Agent’s planning and compilation pipeline, and [Section 5](#S5) describes the execution runtime and runtime adaptation mechanisms.

## 3. Crawling Agent

The Crawling Agent simulates a user trying to “learn” the GUI application – *What is this application useful for and how do I use it?*
Rather than saving and trying to reuse task-specific solutions like some previous reactive GUI agents ([Zheng et al., 2023](#bib.bib21); [Zhang et al., 2025a](#bib.bib20)), the Crawling Agent tries to learn the entire topology of the GUI application (the distinct pages/windows and their constituent GUI elements) and the meaning of every GUI element (e.g., clicking on this next button will navigate to the next page of posts under this forum).
It then organizes this knowledge as a state machine graph (SMG) memory, which is an intuitive representation that developers already use to design GUIs.

The Crawling Agent constructs the SMG offline through systematic exploration, capturing the intrinsic structure of the application independent of any downstream task.
The design explicitly decouples the static topology (bounded by a finite set of templates) from dynamic data content (potentially unbounded) to keep the state space compact and reusable.
The resulting compact, symbolic representation serves as the foundation for the Execution Agent’s one-shot planning capabilities at runtime.

![Refer to caption](images/18_ActionEngine/memory.png)


Figure 3. Illustration of our State-Machine Graph model. The graph shows a subset of states and transitions
in a Reddit-like website, where nodes are States and edges are Operations (black: UI manipulation, red: data collection).

### 3.1. State Machine Graph

The State-Machine Graph represents a GUI application as a directed graph whose nodes correspond to symbolic states and whose edges correspond to executable operations. Formally, we define the graph as a state machine $M=(S,O,T)$ , where $S$ is a set of discrete states, $O$ is a set of executable operations, and $T:S\times O\rightarrow S$ is the transition function. [Figure 3](#S3.F3) provides a simplified visualization of the SMG for the reddit website.

A State $s\in S$ represents a unique and stable *view* of a GUI container (e.g., a webpage, a window) for UI elements (e.g., buttons, menus, tabs, text fields). It is formally defined as a collection of atoms, where an Atom represents a set of related UI elements that appear atomically (i.e., either all of the UI elements in an atom are present in the view or none of them). Although atoms may be shared between states, a state is *uniquely* identified by the *combination* of its atoms.
For example, the HomePage state in [Figure 4](#S3.F4), is characterized by four atoms: the GeneralNavigation atom containing three buttons (Postmill, Forums, Wiki), the SearchBar atom containing a text input and a button, the PostTypeSelection atom containing two buttons (Submissions and Comments) and the Filter atom containing two selection lists. The GeneralNavigation and SearchBar atoms are shared between all the states of the Postmill/Reddit application.

Interactions with the GUI application are modeled similarly using a two-level hierarchy of Actions and Operations. An Action captures a *primitive* interaction with a *single* UI element in an atom (e.g., click on a button, type in a text field, or move the scroll bar). An Operation $op\in O$ is a functional, goal-oriented unit composed of one or more low-level actions. For example, the operation Sort Posts By New includes two actions: click(‘Sort Dropdown’) followed by click(‘New Option’).

An operation is represented as an edge in the SMG ([Figure 3](#S3.F3)). It operates on atoms pertaining to a *single* state and may result in a *single* state transition.
It is possible to define *compounded operations* with multiple state transitions (spanning multiple edges in the SMG), but in the current implementation we only experimented with single state operations.
The functionality of these operations vary from simple navigation (e.g., “Next Forum Page”, "Go to Forum List", “Go to Postmill”, etc.), to
reading or updating content (“Read All Posts”, “Read Kth Post (k)”, “Read All Comments”, "Update User Bio(new\_bio)").
As shown in Figure [3](#S3.F3), UI Manipulation Operations typically induce a transition to a new state (e.g., ‘Go to Postmill‘ from ‘Home Page‘ leads to the ‘Postmill‘ state), whereas Data Collection Operations introduces self-loops because they do not change the agent’s state in the graph (e.g., ‘Read All Vote Counts‘ on the ‘XX Post Details‘ page). Instead of triggering a state transition, these operations extract information from the UI and store it in symbolic variables that can be referenced in the online execution stage.

![Refer to caption](images/18_ActionEngine/atoms.png)


Figure 4. The Home Page State is composed of four Atoms that represents the navigation bar, the search bar, post type selection and filter.

##### Challenge.

A central design challenge in constructing the SMG is preventing state explosion.
For example, a large application such as Amazon contains billions of distinct items customers can inspect, yet modeling each item-specific page as a separate state would make the state graph intractable.
To remain usable for planning, the graph size should scale with the number of distinct *state templates*, not with the number of *data instances* rendered within those templates.

Figure [5](#S3.F5) illustrates this key property of our state abstraction: a single state template may have an unbounded number of instantiations, each populated with different data.
In this example, the two forum pages for “wallstreetbets” and “AskReddit” contain different posts, but they correspond to the same SpecificForumPage state because they share an identical page structure.
This state equivalence is achieved by distinguishing *static* and *dynamic* atoms.
Static atoms encode invariant interface elements (*e.g.,* GeneralNavigation),
while dynamic atoms represent elements with data-dependent content (*e.g.,* ForumName and PostDetails).
Each dynamic atom essentially defines a “type” (analogous to a class definition in object-oriented programming) that can be instantiated zero or more times with different values.

Under this formulation, the SpecificForumPage template is defined by its atom signature: {GeneralNavigation, TypeSelection, Filter, ForumName, List $[$ PostDetails $]$ }.
The typed collection List $[$ PostDetails $]$  specifies that the page expects zero or more instances of the PostDetails atom.
Although the number of and the content of these instances differ across pages, the state identity is determined by this fixed structural signature, not by the specific data rendered within it.

![Refer to caption](images/18_ActionEngine/dynamic.png)


Figure 5. State template equivalence across dynamic page instances.

### 3.2. Graph Construction

The state-machine graph is constructed by the Crawling Agent through a semi-automated, offline crawl-and-validate pipeline.
The primary goal of graph construction is to capture the *intrinsic interaction structure* of a GUI application’s states, operations, and transitions—independent of any specific downstream task.
This process establishes a clear boundary between offline index construction (Crawling Agent’s responsibility), which defines the interaction schema of the GUI application, and online execution (Execution Agent’s responsibility), which instantiates that schema to satisfy user queries.

The Crawling Agent begins from a seed “home” state and systematically and recursively explores the GUI application.
On each visited page/window, a MLLM identifies core Atoms to generate a State ID.
Based on the detected atoms, the agent enumerates candidate operations and validates them through execution. MLLM identifies navigation controls and compiles each operation into a sequence of actions. Transitions are verified by executing these operations and observing the resulting State ID changes. For dynamic atoms, the MLLM does *not* extract the actual data values (which change in real-time). Instead, it infers a data-access schema in the form of a selector-based rule
(e.g., “iterate over elements matching ‘.comment‘ and extract text”).
This schema enables the Execution Agent to fetch live data during task execution.

To ensure the memory graph represents the inherent structure of the GUI application rather than overfitting to specific tasks, we adhere to a strict *affordance-based policy*.
Operations are defined solely based on recurring structural patterns (e.g., DOM patterns) and interactive affordances present in the UI, not on task semantics.
We specifically avoid creating “virtual” operations that encode composite or task-specific intent.
For example, if a post has three clickable entry points (Title, Thumbnail, “Read More”), each is recorded as a distinct operation inducing a parallel transition, even if they lead to the same destination state.
This forces the Execution Agent to reason over the graph during planning, rather than relying on memorized shortcuts.

The finalized graph is serialized into a YAML format optimized for the Planner.  shows an excerpt from the Reddit state-machine graph, illustrating both state-transitioning operations (e.g., navigating to a post) as well as operations on dynamic atoms (e.g., reading comments). On average, the graph for a complex domain like Reddit (Postmill) contains approximately 20-30 states and 100-150 transitions, a size that allows for efficient $O(1)$ lookups during online serving.

[⬇](data:text/plain;base64,IyA9PT09PSBOQVZJR0FUSU9OIE9QRVJBVElPTlMgPT09PT0KLSAhT3BlcmF0aW9uCiAgbmFtZTogTmF2aWdhdGUgdG8gS3RoIFBvc3QKICBzcmNfc3RhdGU6ICZTcGVjaWZpY0ZvcnVtUGFnZQogIGRzdF9zdGF0ZTogJlBvc3REZXRhaWxQYWdlCiAgYWN0aW9uczoKICAgIC0gdHlwZTogY2xpY2sKICAgICAgaW5wdXQ6IFsnQGsnXQogICAgICBsb2NhdG9yOiBsb2NhdG9yKCJuYXYuc3VibWlzc2lvbl9fbmF2IikubnRoKCR7a30pCiMgPT09PT0gQ09NTUVOVCBPUEVSQVRJT05TID09PT09Ci0gIU9wZXJhdGlvbgogIG5hbWU6IFJlYWQgYWxsIENvbW1lbnRzIHRvIGN1cnJlbnQgUG9zdAogIHNyY19zdGF0ZTogJlBvc3REZXRhaWxQYWdlCiAgZHN0X3N0YXRlOiAmUG9zdERldGFpbFBhZ2UgICMgc2VsZi1sb29wCiAgYWN0aW9uczoKICAgIC0gdHlwZTogcmVhZF90ZXh0X2FsbAogICAgICBzZWxlY3RvcjogWyJhcnRpY2xlLmNvbW1lbnQiXQogICAgICBvdXRwdXRfZm9ybWF0OiAiWyd1c2VyMTogY29tbWVudCB0ZXh0Li4uJ10iCi0gIU9wZXJhdGlvbgogIG5hbWU6IFJlcGx5IFRvIENvbW1lbnQgQnkgVXNlcm5hbWUKICBzcmNfc3RhdGU6ICZQb3N0RGV0YWlsUGFnZQogIGRzdF9zdGF0ZTogJlBvc3REZXRhaWxQYWdlICAjIHNlbGYtbG9vcAogIGFjdGlvbnM6CiAgICAtIHR5cGU6IGNsaWNrCiAgICAgIGlucHV0OiBbJ0Bjb21tZW50ZXJfdXNlcm5hbWUnXQogICAgICBsb2NhdG9yOiBsb2NhdG9yKCJhcnRpY2xlLmNvbW1lbnQiKS5maWx0ZXIoLi4uKQogICAgLSB0eXBlOiBmaWxsCiAgICAgIGlucHV0OiBbJ0ByZXBseV90ZXh0J10KICAgICAgbG9jYXRvcjogZ2V0X2J5X2xhYmVsKCJDb21tZW50Iik=)

1
# ===== NAVIGATION OPERATIONS =====

2
- !Operation

3
 name: Navigate to Kth Post

4
 src\_state: &SpecificForumPage

5
 dst\_state: &PostDetailPage

6
 actions:

7
 - type: click

8
 input: [’@k’]

9
 locator: locator("nav.submission\_\_nav").nth(${k})

10
# ===== COMMENT OPERATIONS =====

11
- !Operation

12
 name: Read all Comments to current Post

13
 src\_state: &PostDetailPage

14
 dst\_state: &PostDetailPage # self-loop

15
 actions:

16
 - type: read\_text\_all

17
 selector: ["article.comment"]

18
 output\_format: "[’user1: comment text...’]"

19
- !Operation

20
 name: Reply To Comment By Username

21
 src\_state: &PostDetailPage

22
 dst\_state: &PostDetailPage # self-loop

23
 actions:

24
 - type: click

25
 input: [’@commenter\_username’]

26
 locator: locator("article.comment").filter(...)

27
 - type: fill

28
 input: [’@reply\_text’]

29
 locator: get\_by\_label("Comment")

Listing 1: Excerpt from the Reddit state-machine graph

In the current design, we enforce a strict one-to-one correspondence between
graph edges and concrete GUI affordances to mitigate overfitting and prevent
task leakage. Nevertheless, the architecture supports principled,
experience-based refinement.

Specifically, the system may adopt a mechanism analogous to
materialized views. Frequently recurring operation sequences
(e.g., Login $\rightarrow$ Open Settings) can be identified
and cached as higher-level *compounded operations*. These abstractions
introduce controlled redundancy that improves efficiency for common workflows
while preserving the structural integrity of the base graph, which continues
to encode the intrinsic interface structure and affordances of the application.

## 4. Execution Agent

While the Crawling Agent learns the structural model of the application offline, the Execution Agent addresses the complementary question: given a state-machine graph of a website, how do we complete a specific user task?

Existing GUI agents typically follow a reactive paradigm: at each step, a Multimodal Large Language Models (MLLM) observes the current screen and predicts the next action.
This design has two fundamental limitations.
First, it suffers from stochastic error accumulation, where a single visual hallucination in a long sequence disrupts the entire task.
Second, it incurs high latency: completing a task of with $N$ steps requires $O(N)$ separate MLLM calls, making long-horizon tasks slow and expensive.

The Execution Agent instead treats task solving as a compilation problem.
Given a natural language query and the pre-built state-machine graph (SMG), it synthesizes a complete, executable Python program in three stages:
(1) generating a high-level sketch that captures the task’s control logic, (2) grounding abstract placeholders in the sketch to validated paths in the SMG, and (3) compiling the grounded representation into an executable plan.
By shifting reasoning from iterative runtime inference to one-shot planning over a symbolic model, the system reduces model invocation overhead from $O(N)$ to $O(1)$ .

##### Running Example

Throughout this section, we use the following task as the running example: "Reply to the manager of the website in this post with ’thanks! I am a big fan of your website.’"
This task requires the agent to: (1) identify which forum likely contains manager posts, (2) locate the relevant post, (3) determine whether the manager is the post author or a commenter, and (4) execute the appropriate reply action.
Solving this task requires multi-step reasoning, dynamic data collection, and conditional logic based on runtime observations.

### 4.1. Generating a Sketch Program

The Execution Agent begins by prompting a code-generating LLM (the Planner) with the user’s goal and a filtered subset of the state-machine graph containing only states and operations reachable from the current start state.
This constrains the action space for better reliability and efficiency.
The LLM outputs a Sketch Program: a Python script that specifies the task’s logical structure (e.g., loops, conditionals, and data flow) while abstracting concrete UI interactions into placeholders.

The sketch program serves as an intermediate representation (IR) that connects high-level planning and low-level execution details.
It fixes the task’s control flow in advance while deferring three environment-dependent concerns to later stages: (1) concrete navigation paths, (2) runtime data bindings, and (3) auxiliary inference logic that is not part of the core UI control flow.

First, concrete navigation steps are represented as explicit UI call placeholders using the format
UI\_CALL: [OpID]: OpName.
The OpID uniquely identifies an operation in the SMG, avoiding ambiguity when multiple operations share similar names.
Both UI Manipulation Ops and Data Collection Ops use the same ‘UI\_CALL‘ placeholder in the sketch.
Data-collection operations are tagged with metadata describing their return types and output formats, which enables the Planner to incorporate retrieved data into downstream Python logic.
At this stage, the UI calls specifies which logical operation is required, but not the sequence of transitions needed to reach and execute it from the current state. Expanding each placeholder into a validated action sequence is deferred to the linking stage.

The second defining feature of the sketch IR is support for symbolic variables, denoted by an @ prefix (e.g., @username),
to represent values that are only available at runtime.
For example, a data-collection operation may first extract raw text into a local variable (e.g., comments); a Python Node—a locally executed code block (e.g., for-loops, parsing, filtering, aggregation, and other data-processing logic)—then processes comments to derive a target value (e.g., the manager’s name).
The Planner specifies how this derived value should bind to symbolic arguments @username in downstream UI operations.
If the Planner makes errors in the binding logic, the runtime system’s validator will detect and correct them based on runtime observations during execution.

Finally, the sketch IR also supports helper functions—specialized Python function that encapsulate complex logic (e.g., LLM-based inference, multi-step parsing) separate from the main UI-driven control flow, improving modularity when tasks require sophisticated data processing.

The resulting sketch serves as a *logically complete* blueprint of the task.
Control flow and data dependencies are fixed in advance, while low-level UI navigation paths remain abstract.
To preserve this program’s logical structure during later stages, the system parses the sketch using Python’s Abstract Syntax Tree (AST) and recover the code’s nesting structure. Each UI\_CALL is associated with its enclosing control block (e.g., the body of a for loop or a conditional branch).
As a result, when a single UI\_CALL is later expanded into a multi-step action sequence, the expansion is injected into the correct scope, ensuring that the final executable program faithfully preserves the intended loop and branch semantics.

##### Running Example (Sketch Program)

For our running example, the planner generates the sketch program shown in Listing  (simplified for clarity).
The sketch demonstrates several key features: (1) UI\_CALL placeholders with operation IDs (e.g., [28], [30]) that will be grounded to concrete actions in the linking stage; (2) the helper function find\_manager encapsulates LLM-based reasoning as a specialized Python function, keeping complex inference logic separate from the main UI-driven control flow; (3) symbolic variables like @commenter\_username whose values are computed at runtime and bound dynamically; (4) control flow (if-else) is fixed at plan time based on the task structure, while the actual branch taken depends on runtime data (whether the manager is the post author or a commenter).

[⬇](data:text/plain;base64,YXN5bmMgZGVmIGZpbmRfbWFuYWdlcihwb3N0X3RpdGxlLCBjb21tZW50c19kYXRhKToKICAgICIiIkhlbHBlciBmdW5jdGlvbjogQW5hbHl6ZXMgcG9zdCBhbmQgY29tbWVudHMgdG8KICAgIGlkZW50aWZ5IHRoZSB3ZWJzaXRlIG1hbmFnZXIgYW5kIGRldGVybWluZSB3aGV0aGVyCiAgICB0aGV5IGFyZSB0aGUgcG9zdCBhdXRob3Igb3IgYSBjb21tZW50ZXIuIiIiCiAgICBwcm9tcHQgPSBmIiIiCiAgICAgICAgUG9zdDoge3Bvc3RfdGl0bGV9CiAgICAgICAgQ29tbWVudHM6IHtjb21tZW50c19kYXRhfQoKICAgICAgICBJZGVudGlmeSB3aG8gaXMgdGhlIHdlYnNpdGUgbWFuYWdlci4KICAgICAgICBSZXR1cm46IHt7fCJ8aXNfcG9zdF9hdXRob3J8Inw6IHRydWUvZmFsc2UsCiAgICAgICAgICAgICAgICAgIHwifHVzZXJuYW1lfCJ8OiB8InxtYW5hZ2VyX25hbWV8Inx9fQogICAgIiIiCiAgICByZXNwb25zZSA9IGF3YWl0IGNhbGxfbGxtKHByb21wdCkKICAgIHJldHVybiBwYXJzZV9qc29uKHJlc3BvbnNlKQoKYXN5bmMgZGVmIGV4ZWN1dGVfdGFzaygpOgogICAgcmVzdWx0ID0gTm9uZQogICAgIyBTdGVwIDE6IE5hdmlnYXRlIHRvIHBvc3QgYW5kIGNvbGxlY3QgZGF0YQogICAgVUlfQ0FMTDogWzI5XTpbTmF2aWdhdGUgdG8gS3RoIFBvc3QoQGs9MCldCiAgICBwb3N0X3RpdGxlID0gVUlfQ0FMTDogWzIxXTpbUmVhZCBQb3N0IFRpdGxlKCldCiAgICBjb21tZW50cyA9IFVJX0NBTEw6IFsyOF06W1JlYWQgYWxsIENvbW1lbnRzKCldCiAgICAjIFN0ZXAgMjogSWRlbnRpZnkgbWFuYWdlciAoUHl0aG9uIE5vZGUgd2l0aCBMTE0pCiAgICBtYW5hZ2VyX2luZm8gPSBhd2FpdCBmaW5kX21hbmFnZXIocG9zdF90aXRsZSwgY29tbWVudHMpCiAgICAjIFN0ZXAgMzogUmVwbHkgYmFzZWQgb24gbWFuYWdlcidzIHJvbGUKICAgIHJlcGx5X3RleHQgPSAiVGhhbmtzISBJIGFtIGEgYmlnIGZhbiBvZiB5b3VyIHdlYnNpdGUuIgogICAgaWYgbWFuYWdlcl9pbmZvWyJpc19wb3N0X2F1dGhvciJdOgogICAgICAgICMgTWFuYWdlciBpcyB0aGUgcG9zdCBhdXRob3IgLSBjb21tZW50IG9uIHBvc3QKICAgICAgICBVSV9DQUxMOiBbMjZdOltQb3N0IENvbW1lbnQoQHJlcGx5X3RleHQ9cmVwbHlfdGV4dCldCiAgICBlbHNlOgogICAgICAgICMgTWFuYWdlciBpcyBhIGNvbW1lbnRlciAtIHJlcGx5IHRvIHRoZWlyIGNvbW1lbnQKICAgICAgICBtYW5hZ2VyX25hbWUgPSBtYW5hZ2VyX2luZm9bInVzZXJuYW1lIl0KICAgICAgICBVSV9DQUxMOiBbMzBdOltSZXBseSBUbyBDb21tZW50IEJ5IFVzZXJuYW1lKAogICAgICAgICAgICBAY29tbWVudGVyX3VzZXJuYW1lPW1hbmFnZXJfbmFtZSwKICAgICAgICAgICAgQHJlcGx5X3RleHQ9cmVwbHlfdGV4dCldCiAgICByZXN1bHQgPSAiUmVwbHkgcG9zdGVkIHN1Y2Nlc3NmdWxseSI=)

1
async def find\_manager(post\_title, comments\_data):

2
 """Helper function: Analyzes post and comments to

3
 identify the website manager and determine whether

4
 they are the post author or a commenter."""

5
 prompt = f"""

6
 Post: {post\_title}

7
 Comments: {comments\_data}

8

9
 Identify who is the website manager.

10
 Return: {{"is\_post\_author": true/false,

11
 "username": "manager\_name"}}

12
 """

13
 response = await call\_llm(prompt)

14
 return parse\_json(response)

15

16
async def execute\_task():

17
 result = None

18
 # Step 1: Navigate to post and collect data

19
 UI\_CALL: [29]:[Navigate to Kth Post(@k=0)]

20
 post\_title = UI\_CALL: [21]:[Read Post Title()]

21
 comments = UI\_CALL: [28]:[Read all Comments()]

22
 # Step 2: Identify manager (Python Node with LLM)

23
 manager\_info = await find\_manager(post\_title, comments)

24
 # Step 3: Reply based on manager’s role

25
 reply\_text = "Thanks! I am a big fan of your website."

26
 if manager\_info["is\_post\_author"]:

27
 # Manager is the post author - comment on post

28
 UI\_CALL: [26]:[Post Comment(@reply\_text=reply\_text)]

29
 else:

30
 # Manager is a commenter - reply to their comment

31
 manager\_name = manager\_info["username"]

32
 UI\_CALL: [30]:[Reply To Comment By Username(

33
 @commenter\_username=manager\_name,

34
 @reply\_text=reply\_text)]

35
 result = "Reply posted successfully"

Listing 2: Example sketch program with UI\_CALL placeholders and helper functions.

### 4.2. Static Linking: Resolving UI Calls into Paths

This linking phase resolves abstract UI\_CALL placeholders in the sketch IR into concrete execution paths in the Crawling Agent’s state-machine graph.
The linker resolves each UI call into a valid sequence of graph edges, while preserving the control-flow semantics established in the IR.

The agent has three programmatic resolution strategies.
It first attempts a direct breadth-first search (BFS) over the SMG to find a path from the current state to the target operation’s starting state.
Because the SMG is compact and template-bounded, this lookup is efficient and resolves routine navigation (e.g., Home $\to$ Forum $\to$ Post).
If BFS fails and the UI\_CALL appears inside a for-loop (identified via AST metadata), the agent enforces loop invariants.
The resolved path must return the agent to the loop’s entry state after execution, ensuring that subsequent iterations remain valid.
This prevents invalid plans that silently violate iteration semantics fixed in the sketch.
If neither direct search nor loop-aware linking succeeds, the system applies heuristic recovery.
An LLM-based heuristic may suggest either a global reset—returning to a canonical root state and re-navigating—or a semantic replacement that substitutes the target operation with an alternative matching the original intent.
5
If all three programmatic strategies fail, the node is marked as ‘unresolvable’, instructing the Executor to trigger vision-based fallback at runtime (Section [5.2](#S5.SS2)).

We note that when highly capable LLMs (e.g., Claude Sonnet 4.5) generate the initial sketch, they often produce UI\_CALL sequences that are already correct and properly ordered.
In such cases, BFS resolution succeeds for nearly all operations without requiring path corrections.
In such cases, the linking stage primarily serves as a validation and stability guarantee that any navigation inconsistencies introduced during planning are detected and repaired before execution.
This architectural separation between planning and linking improves robustness: strong planners benefit from minimal overhead, while weaker planners receive automated path correction as a safety net.

##### Running Example (After Linking)

For the manager-reply task, the linker expands each UI\_CALL into concrete Playwright actions as shown in Listing .

[⬇](data:text/plain;base64,YXN5bmMgZGVmIGV4ZWN1dGVfdGFzaygpOgogICAgcmVzdWx0ID0gTm9uZQogICAgIyBTdGVwIDE6IENvbGxlY3QgY29tbWVudHMgKGdyb3VuZGVkIHRvIGFjdGlvbikKICAgIGNvbW1lbnRzID0gPEFDVElPTj4gcmVhZF90ZXh0X2FsbAogICAgICAgICAgICAgICBzZWxlY3Rvcj0iYXJ0aWNsZS5jb21tZW50IgogICAgIyBTdGVwIDI6IElkZW50aWZ5IG1hbmFnZXIgKHVuY2hhbmdlZCBQeXRob24gTm9kZSkKICAgIG1hbmFnZXJfaW5mbyA9IGF3YWl0IGZpbmRfbWFuYWdlcihwb3N0X3RpdGxlLCBjb21tZW50cykKICAgICMgU3RlcCAzOiBSZXBseSBiYXNlZCBvbiBtYW5hZ2VyJ3Mgcm9sZQogICAgcmVwbHlfdGV4dCA9ICJUaGFua3MhIEkgYW0gYSBiaWcgZmFuIG9mIHlvdXIgd2Vic2l0ZS4iCiAgICBpZiBtYW5hZ2VyX2luZm9bImlzX3Bvc3RfYXV0aG9yIl06CiAgICAgICAgIyBHcm91bmRlZDogUG9zdCBDb21tZW50IG9wZXJhdGlvbgogICAgICAgIDxBQ1RJT04+IGZpbGwgbG9jYXRvcj1nZXRfYnlfbGFiZWwoIkNvbW1lbnQiKQogICAgICAgICAgICAgICBpbnB1dD1bJ0ByZXBseV90ZXh0J10KICAgICAgICA8QUNUSU9OPiBjbGljayBsb2NhdG9yPWdldF9ieV9yb2xlKCJidXR0b24iLCBuYW1lPSJQb3N0IikKICAgIGVsc2U6CiAgICAgICAgIyBHcm91bmRlZDogUmVwbHkgVG8gQ29tbWVudCBCeSBVc2VybmFtZSBvcGVyYXRpb24KICAgICAgICBtYW5hZ2VyX25hbWUgPSBtYW5hZ2VyX2luZm9bInVzZXJuYW1lIl0KICAgICAgICA8QUNUSU9OPiBjbGljawogICAgICAgICAgICAgICBsb2NhdG9yPWxvY2F0b3IoImFydGljbGUuY29tbWVudCIpCiAgICAgICAgICAgICAgICAgICAgICAgLmZpbHRlcihoYXNfdGV4dD0iJHttYW5hZ2VyX25hbWV9IikKICAgICAgICAgICAgICAgICAgICAgICAuZ2V0X2J5X3JvbGUoImxpbmsiLCBuYW1lPSJSZXBseSIpCiAgICAgICAgICAgICAgIGlucHV0PVsnQG1hbmFnZXJfbmFtZSddCiAgICAgICAgPEFDVElPTj4gZmlsbCBsb2NhdG9yPWdldF9ieV9sYWJlbCgiQ29tbWVudCIpLmxhc3QKICAgICAgICAgICAgICAgaW5wdXQ9WydAcmVwbHlfdGV4dCddCiAgICAgICAgPEFDVElPTj4gY2xpY2sgbG9jYXRvcj1nZXRfYnlfcm9sZSgiYnV0dG9uIiwgbmFtZT0iUG9zdCIpLmxhc3QKICAgIHJlc3VsdCA9ICJSZXBseSBwb3N0ZWQgc3VjY2Vzc2Z1bGx5Ig==)

1
async def execute\_task():

2
 result = None

3
 # Step 1: Collect comments (grounded to action)

4
 comments = <ACTION> read\_text\_all

5
 selector="article.comment"

6
 # Step 2: Identify manager (unchanged Python Node)

7
 manager\_info = await find\_manager(post\_title, comments)

8
 # Step 3: Reply based on manager’s role

9
 reply\_text = "Thanks! I am a big fan of your website."

10
 if manager\_info["is\_post\_author"]:

11
 # Grounded: Post Comment operation

12
 <ACTION> fill locator=get\_by\_label("Comment")

13
 input=[’@reply\_text’]

14
 <ACTION> click locator=get\_by\_role("button", name="Post")

15
 else:

16
 # Grounded: Reply To Comment By Username operation

17
 manager\_name = manager\_info["username"]

18
 <ACTION> click

19
 locator=locator("article.comment")

20
 .filter(has\_text="${manager\_name}")

21
 .get\_by\_role("link", name="Reply")

22
 input=[’@manager\_name’]

23
 <ACTION> fill locator=get\_by\_label("Comment").last

24
 input=[’@reply\_text’]

25
 <ACTION> click locator=get\_by\_role("button", name="Post").last

26
 result = "Reply posted successfully"

Listing 3: Example of expanded program after linking.

Each UI\_CALL placeholder (e.g., [28]: Read all Comments) is expanded into its corresponding low-level actions (e.g., read\_text\_all selector="article.comment").
Symbolic variables like @manager\_name and @reply\_text remain as placeholders, carrying input annotations that will be resolved in the compilation stage.
The control flow structure (if-else) is preserved exactly as specified in the sketch IR.

### 4.3. Compiling into Executable Plans

Once all resolvable UI\_CALLs have been linked, the system compiles the resulting program into an executable representation that is type-safe, execution-ready, and supports runtime symbolic binding.

The compiler first performs instruction expansion.
Each linked SMG operation is expanded into a fixed sequence of primitive browser actions implemented via Playwright (e.g., Sort by New $\rightarrow$ {click(#sort), click(#new)}).
This produces a fully specified Python program with no abstract UI calls.
The compiler also extracts helper functions via AST analysis and hoists them to a root-level Python Node, ensuring helper logic is initialized before the main execution flow begins.

The expanded program is converted into a MixedActionPlan object graph.
The plan consists of three node types:

- $\bullet$ 

  UI Nodes: Store primitive browser actions (e.g., click, fill) with associated locators or selectors. Besides storing a *single* primitive action, an UI node may also contain symbolic bindings (e.g., @worcester\_forum\_name) that are resolved at runtime. Based on that, ActionEngine will run UI Nodes one by one, which will easily trigger validator(see section [5.1](#S5.SS1)) when a specific UI Node failed.
- $\bullet$ 

  Python Nodes: Encapsulate local computation and produce explicitly named output variables for data flow tracking.
- $\bullet$ 

  Control Flow Nodes: Map for/if/while to container nodes preserving nesting structure in the IR.

Each node carries its execution context, code logic, and data binding requirements.

##### Running Example (Final Executable Plan)

After compilation, the program is transformed into a MixedActionPlan with typed nodes. [4](#listing4) shows an excerpt of the structure (simplified from the full 25-node plan).
The plan demonstrates the three node types: (1) Python Nodes containing helper functions and orchestration logic; (2) UI Nodes with actions (read\_text\_all, fill, click) mapped to Playwright locators/selectors, with symbolic inputs such as ["@reply\_message"]; (3) Conditional Nodes enabling branching logic with nested action sequences.
At runtime, when the Executor encounters "input": ["@target\_index"], it resolves the symbol against the local context—where target\_index was set by the preceding Python Node—and generates the concrete Playwright command with the bound value.

Listing 4:  Excerpts from generated execution plan.

[⬇](data:text/plain;base64,ewogICJuYW1lIjogIlJlcGx5IHRvIHRoZSBtYW5hZ2VyIG9mIHRoZSB3ZWJzaXRlLi4uIiwKICAiYWN0aW9ucyI6IFsKICAgIHsKICAgICAgIm5hbWUiOiAiSGVscGVyIEZ1bmN0aW9ucyIsCiAgICAgICJ0eXBlIjogInB5dGhvbiIsCiAgICAgICJweXRob25fY29kZSI6ICJhc3luYyBkZWYgaWRlbnRpZnlfbWFuYWdlciguLi4pOiAuLi4iLAogICAgICAiZGVzY3JpcHRpb24iOiAiTExNLWJhc2VkIGZ1bmN0aW9ucyBmb3IgcmVhc29uaW5nIgogICAgfSwKICAgIHsKICAgICAgIm5hbWUiOiAiQWN0aW9uIGZyb20gb3BlcmF0aW9uOiBOYXZpZ2F0ZSB0byBLdGggRm9ydW0iLAogICAgICAidHlwZSI6ICJjbGljayIsCiAgICAgICJpbnB1dCI6IFsiQHRhcmdldF9pbmRleCJdLAogICAgICAibG9jYXRvciI6ICJsb2NhdG9yKCdhcnRpY2xlJykubnRoKHt0YXJnZXRfaW5kZXh9KSIKICAgIH0sCiAgICB7CiAgICAgICJuYW1lIjogIkFjdGlvbiBmcm9tIG9wZXJhdGlvbjogUmVhZCBhbGwgQ29tbWVudHMiLAogICAgICAidHlwZSI6ICJyZWFkX3RleHRfYWxsIiwKICAgICAgInNlbGVjdG9yIjogImFydGljbGUuY29tbWVudCIsCiAgICAgICJvdXRwdXQiOiAiY29tbWVudHNfZGF0YSIKICAgIH0sCiAgICB7CiAgICAgICJuYW1lIjogIlB5dGhvbiBCbG9jayIsCiAgICAgICJ0eXBlIjogInB5dGhvbiIsCiAgICAgICJweXRob25fY29kZSI6IFsKICAgICAgICAicmVwbHlfaW5mbyA9IGF3YWl0IGlkZW50aWZ5X21hbmFnZXIoY29tbWVudHNfZGF0YSkiLAogICAgICAgICJyZXBseV9tZXNzYWdlID0gXCJ0aGFua3MhIEkgYW0gYSBiaWcgZmFuLlwiIgogICAgICBdCiAgICB9LAogICAgewogICAgICAibmFtZSI6ICJDb25kaXRpb25hbCIsCiAgICAgICJ0eXBlIjogImNvbmRpdGlvbmFsIiwKICAgICAgImNvbmRpdGlvbiI6ICJyZXBseV9pbmZvW1wicmVwbHlfdHlwZVwiXSA9PSBcInBvc3RfY29tbWVudFwiIiwKICAgICAgImFjdGlvbnMiOiBbCiAgICAgICAgewogICAgICAgICAgIm5hbWUiOiAiQWN0aW9uIGZyb20gb3BlcmF0aW9uOiBQb3N0IENvbW1lbnQiLAogICAgICAgICAgInR5cGUiOiAiZmlsbCIsCiAgICAgICAgICAibG9jYXRvciI6ICJnZXRfYnlfbGFiZWwoXCJDb21tZW50XCIpIiwKICAgICAgICAgICJpbnB1dCI6IFsiQHJlcGx5X21lc3NhZ2UiXQogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgIm5hbWUiOiAiQWN0aW9uIGZyb20gb3BlcmF0aW9uOiBQb3N0IENvbW1lbnQiLAogICAgICAgICAgInR5cGUiOiAiY2xpY2siLAogICAgICAgICAgImxvY2F0b3IiOiAiZ2V0X2J5X3JvbGUoXCJidXR0b25cIiwgbmFtZT1cIlBvc3RcIikiCiAgICAgICAgfQogICAgICBdCiAgICB9CiAgXQp9)

1
{

2
 "name": "Reply to the manager of the website...",

3
 "actions": [

4
 {

5
 "name": "Helper Functions",

6
 "type": "python",

7
 "python\_code": "async def identify\_manager(...): ...",

8
 "description": "LLM-based functions for reasoning"

9
 },

10
 {

11
 "name": "Action from operation: Navigate to Kth Forum",

12
 "type": "click",

13
 "input": ["@target\_index"],

14
 "locator": "locator(’article’).nth({target\_index})"

15
 },

16
 {

17
 "name": "Action from operation: Read all Comments",

18
 "type": "read\_text\_all",

19
 "selector": "article.comment",

20
 "output": "comments\_data"

21
 },

22
 {

23
 "name": "Python Block",

24
 "type": "python",

25
 "python\_code": [

26
 "reply\_info = await identify\_manager(comments\_data)",

27
 "reply\_message = \"thanks! I am a big fan.\""

28
 ]

29
 },

30
 {

31
 "name": "Conditional",

32
 "type": "conditional",

33
 "condition": "reply\_info[\"reply\_type\"] == \"post\_comment\"",

34
 "actions": [

35
 {

36
 "name": "Action from operation: Post Comment",

37
 "type": "fill",

38
 "locator": "get\_by\_label(\"Comment\")",

39
 "input": ["@reply\_message"]

40
 },

41
 {

42
 "name": "Action from operation: Post Comment",

43
 "type": "click",

44
 "locator": "get\_by\_role(\"button\", name=\"Post\")"

45
 }

46
 ]

47
 }

48
 ]

49
}

## 5. Runtime Execution and Adaptation

### 5.1. Execution and Validation

The Execution Agent’s runtime environment translates the compiled program into concrete browser actions.
The runtime operates at the granularity of plan nodes, treating each node as an atomic execution unit.
This node-level execution model enables precise failure localization, allowing runtime errors to be deterministically attributed to individual nodes.
Consequently, the Validator can perform localized repair, constraining corrective actions to the minimal faulty region rather than triggering global replanning.
The Execution Agent operates *deterministically*, traversing the pre-computed execution plan node by node.
The runtime consists of two specialized components: the Executor and the Validator.

##### The Executor (Deterministic Runtime)

The Executor is a deterministic runtime engine that traverses the MixedActionPlan object graph, dispatching instructions based on node type.
Python Nodes are executed in a sandboxed environment with a restricted interpreter that only allows whitelisted safe\_builtins (e.g., math, json) while blocking unsafe system calls (e.g., network sockets, file I/O).
To enable data flow across sequential steps, the Executor maintains an *Action Execution Context*, which is a dedicated stack frame that manages variable scope.
This allows data extracted in one step (e.g., output="vote\_counts") to be dynamically bound to parameters in subsequent steps (e.g., input=["@vote\_counts"]) via runtime substitution.

Conditional Nodes are handled through standard control flow: the Executor evaluates the condition expression against the current context, and if true, recursively executes the nested actions array before continuing to the next sibling node. This enables dynamic branching based on runtime observations (e.g., choosing different reply strategies based on whether the manager is a post author or commenter).

UI Nodes are delegated to a WebUIWorker, which maintains a fixed mapping from action types to Playwright ([Microsoft, 2024](#bib.bib10)) API calls: click $\rightarrow$ page.locator().click(), fill $\rightarrow$ page.locator().fill(), read\_text $\rightarrow$ page.locator().inner\_text(). The locator field is passed directly as a Playwright selector string, while input parameters are resolved from the execution context and injected into the API call.

##### The Validator

The Validator monitors execution and handles exceptions.
Since plan nodes are typed (UI vs. Python), the Validator can directly map each failure to a corresponding recovery routine: Python-node exceptions trigger code hot-patching, while UI-node exceptions trigger interface re-grounding and memory updates.
For logic interrupts triggered by Python failures, it captures tracebacks (e.g., JSONDecodeError) and prompts a lightweight coding model to hot-patch the code, allowing execution to resume.
For IO interrupts caused by UI failures (e.g., TimeoutError), the Validator suspends execution and triggers an update to the state-machine memory graph by calling a vision-based agent to address interface-level inconsistencies.

Because execution is structured around node-level atomicity, recovery can be strictly localized.
Validator interventions modify only the faulty node or its associated metadata without invalidating the surrounding execution trajectory, thereby preventing cascading failures and avoiding costly global replanning.

Our evaluation with Claude 4.5 Sonnet shows that with a strong planning model, the generated execution plan success without validation (Section [6](#S6).
However, the Validator becomes critical with weaker models: in our experience with models like GPT-4o, approximately 20-30% of executions require validation and hot-patching, demonstrating its importance as a safety net for production deployment.

### 5.2. Dynamic Memory Update Mechanism

GUI interfaces evolve continuously as elements shift and layouts change. When the Execution Agent encounters UI failures, the system triggers a feedback loop to update the Crawling Agent’s state-machine graph.

SMG updates are triggered under two circumstances: when the Validator catches UI exceptions during execution, or when the Planner marks a milestone as ‘unresolvable’ during the linking phase (Section [4.2](#S4.SS2)). These triggers signal that the current memory representation no longer accurately reflects the live GUI interface.

Upon triggering, the system pauses execution and invokes a vision-based agent to re-ground the failed action.
This agent captures the current DOM and screenshot to identify the correct interaction point (e.g., finding the new CSS selector for a "Reply" button).
The updated metadata for the action is committed to the SMG, enabling future executions to use the corrected path without requiring screenshot-based inference. The vision-based fallback adds latency during the first recovery, though subsequent runs benefit from the updated memory.

While this mechanism effectively handles localized UI changes, it operates under the assumption that such changes are infrequent and limited in scope.
Large-scale redesigns that fundamentally alter the interface structure may require full re-crawling to rebuild the memory from scratch.

## 6. Evaluation

We evaluate ActionEngine on the WebArena benchmark ([Zhou et al., 2023](#bib.bib22)), a highly realistic execution environment.
WebArena is widely recognized as the most challenging benchmark in the field, as it requires agents to perform complex reasoning and calculation rather than simple UI interactions.
Currently, even advanced open-source solutions struggle to achieve high success rates, highlighting the significant gap between existing reactive paradigms and the requirements of real-world deployment.

### 6.1. Experimental Setup

We focus our deep-dive analysis on the Postmill (Reddit) domain in WebArena, which represents a worst-case "Long-Horizon Reasoning" scenario for reactive agents. Tasks in this domain (e.g., "Find the user who posted the latest comment and count their upvotes") require inter-page navigation, logic filtering, and arithmetic—areas where purely vision-based agents suffer catastrophic error accumulation.
We compare ActionEngine (AEngine) against AgentOccam (AOccam) ([Yang et al., 2024](#bib.bib18)), a state-of-the-art reactive baseline that uses GPT-4-Turbo with sophisticated prompting and vision-based interaction, but still relies on step-by-step planning without structured memory.

We evaluate agent systems along the following dimensions:

- $\bullet$ 

  Success Rate: Task completion rate as measured by WebArena’s evaluation framework.
- $\bullet$ 

  Query Latency: End-to-end execution time, including computation and API calls.
- $\bullet$ 

  Cost: Total API cost per task, computed from token usage (input/output tokens across all LLM calls) and model pricing. We also report the number of LLM calls per task.

### 6.2. End-to-End Performance

Table [1](#S6.T1) presents a high-level comparison between ActionEngine and AgentOccam across key performance metrics. Our method achieves a success rate of 95% on the Reddit benchmark (106 tasks), significantly outperforming AgentOccam (66%), while demonstrating cost and efficiency gains across all metrics.

Table 1. Performance summary on WebArena (Reddit Subset, 106 tasks). Cost estimates are based on Claude 4.5 Sonnet ($3/M input, $15/M output) and GPT-4-Turbo ($10/M input, $30/M output) API pricing.

| Metric | AOccam | AEngine | Improvement ( $\times$ ) |
| --- | --- | --- | --- |
|  | (GPT-4-Turbo) | (Claude 4.5) |  |
| Success Rate (%) | 66 | 95 | 1.44 $\times$ |
| Avg. Latency (s) | 237 | 118 | 2.01 $\times$ |
| Avg. Cost per Task ($) | 0.71 | 0.06 | 11.83 $\times$ |
| Avg. #InTokens | 62.3k | 8.1k | 7.69 $\times$ |
| Avg. #OutTokens | 3.0k | 2.3k | 1.30 $\times$ |
| Avg. #LLM calls | 10.2 | 1.8 | 5.67 $\times$ |

The 29 percentage point improvement in success rate validates our core architectural principle: execution logic locked into deterministic code (e.g., Python for loops for counting upvotes) eliminates the stochastic errors inherent in visual reasoning.
Overall, ActionEngine maintains high success rates across both simple tasks (e.g., 399-403: profile updates, 100% success) and complex multi-step reasoning tasks (e.g., 27-31: counting filtered comments, 100% success). In contrast, AOccam shows significant variance, with complete failures on several task groups (e.g., 66-68, 399-403, 409-410, 615-619).

Our system reduces average task completion time by 50% (from 237s to 118s) and the average number of LLM per task by 82% (from 10.2 to 1.8).
Unlike reactive agents that require $O(N)$ LLM inferences for an $N$ -step task, our offline state-machine graph allows the Execution Agent’s planner to synthesize the entire task trajectory in a single or few LLM calls.
The most dramatic efficiency improvements occur on tasks requiring multi-step reasoning with branching logic. For example, on task group 27-31, our system reduces input tokens by 95% (140.9k $\rightarrow$ 6.8k) and LLM calls by 94% (17.8 $\rightarrow$ 1.0). Even on tasks where both systems succeed (e.g., 404-408), our approach uses 78% fewer tokens and completes 2.1 $\times$ faster, validating that structured memory eliminates redundant environment perception and enables scalable web/app automation.

These efficiency gains translate directly into cost savings. Our system reduces average cost per task by 11.8 $\times$ (from $0.71 to $0.06). The reduction comes from three sources: First, 87% fewer input tokens (62.3k $\rightarrow$ 8.1k)—we provide only reachable operations to the planner, while linking uses deterministic graph algorithms. Second, using coding models (e.g., Claude Sonnet 4.5) instead of expensive vision-language models. Third, our architecture requires only one large LLM call for initial planning (avg. 6.8k tokens); the remaining calls per task are significantly smaller (for validation or error recovery) and share common prefixes with the planning context, allowing LLM providers’ prompt caching to reuse cached tokens and reduce effective costs.

### 6.3. Detailed Task-by-Task Analysis

Table 2. Detailed analysis of the WebArena benchmark – the Reddit subset. AOccam uses GPT-4-Turbo, AEngine uses Claude 4.5 Sonnet.

| Task | Success Ratio |  | Avg. Latency (s) |  | Avg. #InTokens |  | Avg. #OutTokens |  | Avg. #LLM calls |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Group | AOccam | AEngine | AOccam | AEngine | AOccam | AEngine | AOccam | AEngine | AOccam | AEngine |
| 27-31 | 0.6 | 1 | 343 | 65 | 140.9k | 6.8k | 4.8k | 2.1k | 17.8 | 1 |
| 66-69 | 0.25 | 1 | 181 | 182 | 61.3k | 22.2k | 3.0k | 3.6k | 10.0 | 8.8 |
| 399-403 | 0 | 1 | 432 | 36 | 93.7k | 6.8k | 5.7k | 1k | 20.2 | 1 |
| 404-408 | 1 | 1 | 109 | 52 | 31.2k | 7k | 1k | 1.8k | 3.8 | 1.2 |
| 409-410 | 0 | 0.5 | 155 | 33 | 60.3k | 5k | 0.6k | 1.1k | 3.0 | 1 |
| 580-584 | 1 | 1 | 160 | 40 | 43.8k | 6.8k | 3.8k | 1.2k | 13.0 | 1 |
| 595-599 | 1 | 0.8 | 201 | 63 | 90.0k | 6.8k | 2.9k | 1.9k | 7.6 | 1 |
| 600-604 | 0.8 | 1 | 145 | 85 | 34.6k | 10.7k | 2.7k | 3.3k | 9.2 | 2 |
| 605-609 | 0.6 | 1 | 178 | 82 | 32.2k | 9.7k | 1.4k | 3.5k | 5.2 | 2.6 |
| 610-614 | 1 | 1 | 106 | 53 | 16.6k | 6.8k | 1.2k | 1.8k | 4.6 | 1 |
| 615-619 | 0 | 0.8 | 82 | 76 | 166.4k | 6.4k | 7.7k | 2.9k | 26.8 | 2.25 |
| 620-624 | 0.8 | 1 | 225 | 78 | 47.7k | 9.7k | 3.9k | 2.3k | 10.8 | 2 |
| 625-629 | 0.8 | 0.8 | 183 | 95 | 27.2k | 10.6k | 2.1k | 3.4k | 7.4 | 2 |
| 630-634 | 1 | 1 | 317 | 61 | 41.3k | 6.8k | 3.1k | 1.7k | 8.4 | 1 |
| 635-639 | 0.6 | 1 | 241 | 76 | 27.6k | 9.9k | 2.4k | 2.4k | 7.0 | 2 |
| 640-644 | 1 | 1 | 103 | 66 | 15.2k | 7.3k | 1.2k | 2.5k | 4.2 | 2.2 |
| 645-649 | 1 | 1 | 176 | 68 | 30.5k | 7k | 2.2k | 2.5k | 7.8 | 2 |
| 650-652 | 1 | 1 | 187 | 23 | 30k | 5k | 0.6k | 1k | 3 | 1 |
| 714-718 | 0.4 | 0.8 | 240 | 59 | 66.8k | 6.8k | 2.6k | 1.8k | 7.4 | 1 |
| 719-724 | 0.2 | 0.83 | 692 | 592 | 140.8k | 6.8k | 5.8k | 2.5k | 19.5 | 1 |
| 725-730 | 0.5 | 1 | 360 | 400 | 99.6k | 6.8k | 3.3k | 2.8k | 11.8 | 1 |
| 731-735 | 0.8 | 1 | 212 | 89 | 34.6k | 7.6k | 1.6k | 2.4k | 5.6 | 1.6 |
| All(106) | 0.66 | 0.95 | 237.48 | 118.26 | 62.26 | 8.14 | 3.03 | 2.3 | 10.16 | 1.76 |

To provide transparency into our system’s performance characteristics, we present detailed breakdowns across all 106 Reddit tasks in Table [2](#S6.T2).
We discuss patterns observed in representative success and failure cases below.

#### 6.3.1. Representative Success Case

##### Multi-Step Reasoning (Task 27-31)

Consider the task: "Tell me the count of comments that have received more downvotes than upvotes for the user who made the latest post on the {{forum}} forum." This requires: (1) navigating to the forum, (2) identifying the latest post, (3) finding its author, (4) retrieving all comments by that author, (5) filtering by vote criteria, and (6) counting the results.
AOccam performed 17.8 LLM calls on average, attempting to navigate and reason visually at each step. This reactive strategy accumulated errors—after several navigation steps, the agent lost track of the original filtering criteria, leading to a 60% failure rate. The token consumption (140.9k) reflected repeated context-passing as the agent tried to maintain state across steps.
ActionEngine generated a single Python program in one LLM call (6.8k tokens) that encapsulated the entire logic: navigate\_to\_forum() → get\_latest\_post() → author = post.author → comments = get\_all\_comments (author) → filtered = [c for c in comments if c.downvotes > c.upvotes] → return len(filtered). This deterministic program executed reliably across all 5 test cases, completing in 65s compared to AOccam’s 343s.

##### Underspecified Tasks (Task 409-410)

Tasks 409-410 expose a benchmark ambiguity: "Reply to {{position\_description}} in this post" with positions like "the second comment" is underspecified when nested comment threads exist. Our system achieved 50% success by systematically traversing the comment tree structure encoded in our state-machine memory and selecting the second comment in depth-first order. AOccam achieved 0% because its reactive visual reasoning provided no consistent interpretation of comment hierarchy. The 50% failure rate reflects cases where our systematic interpretation differed from the ground-truth evaluator’s intent—a task specification issue rather than an agent capability limitation. In production, such ambiguities would be resolved through user clarification.

##### Vision-Dependent Tasks (Task 66-68)

Task groups 66-68 require extracting book information from post screenshots, which requires calls to vision models. Here, AOccam completely failed (0% success) despite using GPT-4o’s vision capabilities—the reactive approach couldn’t maintain the filtering logic across multiple posts. Our system achieved 100% success by generating a program that systematically called LLM APIs within a deterministic loop structure, demonstrating that programmatic control over LLM calls is more reliable than visual reasoning alone.

#### 6.3.2. Detailed Failure Analysis

ActionEngine fails to solve 6 of the 106 Reddit tasks: 409, 599, 617, 625, 715, and 722. The main cause for these failures is the ambiguity of the task, as we detail below. This is a disambiguation problem and solutions, orthogonal to our work, have been proposed to solve it ([Tanjim et al., 2025](#bib.bib14)).

Task 409 is the task we used as a running example throughout the previous sections: "Reply to the manager of the website in this post with ’thanks! I am a big fan of your website.’". While the Webarena benchmark expects ameliaspond to be found as the "manager of the website", ActionEngine chooses a different user. We believe the task is ambiguous, it is unclear who should be the "manager of the website" since no commenter acknowledges this fact. Although the code generated to solve this task is correct, it relies on LLM reasoning at execution time to analyze the current post and the comments to identify the "manager of the website", as shown in ; the exact response from the LLM call in function find\_manager is: ’Looking through the comments, I need to identify who is the "manager of the website" (bookshop.org).

Analyzing the comments:

1. ameliaspond - States "I’m a manager at an indie bookstore" - This indicates they manage a physical indie bookstore, not the website itself.

2. StDorothyMantooth23 - States "Indie bookseller here– some indie bookstores have online stores as well that you can order from. I do the online orders at the bookstore I work at" - This is also about working at a physical bookstore.

3. Fearless-Aerie-4721

…

5. TheBookShopOfBF - This username contains "BookShop" which could indicate affiliation with bookshop.org, but their comments dont́ explicitly state they manage the website.

None of the commenters explicitly identify themselves as managing the bookshop.org website. They all appear to be either customers, indie bookstore employees, or general users discussing the platform.

However, based on the username pattern, TheBookShopOfBF has the most
relevant username that could indicate website management affiliation.’

The LLM decision signal is:

[⬇](data:text/plain;base64,eyJtYW5hZ2VyX3VzZXJuYW1lIjogIlRoZUJvb2tTaG9wT2ZCRiJ9)

{"manager\_username": "TheBookShopOfBF"}

Task 599, "’Open the thread of a trending post on the forum "machine learning" and subscribe.’, fails because there is no forum named "machine learning". There is a forum named "MachineLearning" and while the code generated by the planner accounts for upper case, it does not account for the space in between the two words. We believe this task is ambiguous: it is unclear whether the agent should perform exact match on the forum name or find a forum most appropriate for "machine learning" content.

Task 617, Re-post the image of Firework in this page to earthporn subreddit and note "from /f/pics", fails because in the current prototype we do not provide a tool for the agent to analyze images, and thus is not able to find the post containing an image of the Firework. The other tasks in this group are all passing because ActionEngine is able to identify the post containing a certain image just by analyzing the post title and text content.

Task 625, ’Create a discussion post about "the effectiveness of online learning" in a relevant subreddit and ask users for their opinions with the simple prompt, "your opinion"’, fails because the LLM selects a different forum to create the post in. Webarena expects the post to be created in either the "MachineLearning" or "deeplearning" forums but the LLM selects the "AskReddit" forum. We believe this is an ambiguous task because "online learning" is not necessarily linked to computer science. The exact response of the LLM after analyzing the list of forum names:
’Looking at the list of forums, I need to find one most relevant to "the effectiveness of online learning."

This topic relates to education, learning methods, and academic discussion. Let me scan through the forums:

- AskReddit - General questions, could work but not specialized

- science - Scientific topics, could be relevant for educational research

- technology - Tech-related, online learning has a tech component

- Futurology - Future trends, online learning is a modern trend

- explainlikeimfive - Educational explanations

- askscience - Science questions

Among these options, AskReddit is the most suitable because:

1. It’s designed for open-ended discussion questions

2. It has the highest activity (10,041 submissions)

3. Questions about "effectiveness" of various topics are common there

4. It welcomes diverse opinions and experiences about real-world topics like online learning

While there’s no dedicated education forum in this list, AskReddit is the best fit for a discussion post seeking opinions and experiences about online learning effectiveness.’

The LLM decision signal is:

[⬇](data:text/plain;base64,eyJmb3J1bV9uYW1lIjoiQXNrUmVkZGl0In0=)

{"forum\_name":"AskReddit"}

Task 715, ’Thumbs down the top 2 post ever in history.’, fails because the LLM could not figure out that "history" refers to a forum. Instead, the LLM interprets the task as referring to the top 2 posts in the history of the website, across all forums. We believe this task is ambiguous.

Task 722, ’Like all submissions created by Don\_Gato1 in subreddit new york’, fails because there is no forum named "new york". While there is a forum named "nyc", the LLM performs exact matching on the forum name and thus cannot find the forum. We believe the task is ambiguous and the LLM needs to be guided more on how to perform the forum search.

## 7. Related Work

Research in autonomous GUI agents has largely been driven by the capabilities of Multimodal Large Language Models (MLLMs). Current approaches use a reactive architecture that operates through step-by-step reasoning—observing the current state, invoking an LLM to select the next action, executing it, and repeating until task completion—but differ primarily in their perception modality (vision versus text), presenting distinct trade-offs between generality and efficiency.

Vision-based agents represent a dominant paradigm, treating task automation for GUI applications as a sequence of visual reasoning tasks. Agents such as ScreenAgent ([Niu et al., 2024](#bib.bib13)) and SeeClick ([Cheng et al., 2024](#bib.bib3)) directly process screenshots of the graphical user interface (GUI) to decide on the next action.
This approach closely mimics human interaction with GUIs and generalizes to different tasks and domains.
However, they require costly MLLM calls at each step, making them slow and resource-intensive for long-horizon tasks.
In contrast, text-based agents operate on the underlying textual metadata of a webpage, such as the HTML source or Document Object Model (DOM) trees. Agents like WebWISE ([Tao et al., 2023](#bib.bib15)) and MindAct ([Deng et al., 2023](#bib.bib4)) parse this structured data to identify interactive elements and formulate an action plan. While potentially faster than vision-based methods, textual representations are often verbose, vary significantly across websites, and fail to align with human cognition, leading to brittleness and poor generalization on unseen UI structures ([Deng et al., 2023](#bib.bib4)).
Multi-modal agents like WebVoyager ([He et al., 2024](#bib.bib8)) combine visual and textual information to make more robust decisions. AgentOccam ([Yang et al., 2024](#bib.bib18)), representing state-of-the-art in reactive architectures, achieves competitive performance through sophisticated prompting and vision-based interaction, but still relies on step-by-step planning without structured memory.

Recent work improves step-wise reasoning by incorporating world models to enhance agent foresight.
For instance, WebDreamer ([Gu et al., 2024](#bib.bib6)) simulates the outcomes of potential actions before execution to select the optimal step, while ([Gur et al., 2023](#bib.bib7)) explores model-based planning for web navigation. However, these model-based approaches typically require costly training or simulation and still operate reactively on a step-by-step basis.

Several GUI agents create and maintain a memory as they execute tasks.
For example, agents like Synapse ([Zheng et al., 2023](#bib.bib21)) use a simpler form of memory by retrieving flat, past action sequences ("Trajectory-as-Exemplar") as context.
Other work has explored graph-based memory representations. PageGraph ([Chen et al., 2025](#bib.bib2)) stores page transition relationships in an offline graph structure.
AutoDroid ([Wen et al., 2024](#bib.bib17)) represents mobile apps as UI transition graphs and uses LLM-generated functional summaries to annotate UI elements. AutoDroid focuses on optimizing accuracy through richer UI annotations (e.g., injecting task descriptions into HTML ’onclick’ properties).
However, they are fundamentally different from our method:
(1) These proposed memory-based agents are still fundamentally reactive, operating in a step-by-step manner. They merely adopt graph memory to provide explicit contextual information for the MLLM.
(2) Their graph memory representations are different from our state machine. They only model UI operations that cause page transitions, whereas our memory includes both navigation operations and data collection operations that extract information without changing the state.

Our framework is orthogonal to the perception-based methods described above. Rather than competing with them, it orchestrates them as tools. When the primary programmatic plan fails or when new website/application areas need to be explored, our agent can fall back to a vision-based or text-based module to resolve the immediate step. The information learned from this successful fallback is then used to dynamically update and enrich the state-machine memory, making the primary programmatic path more robust over time. As a result, our framework gains the efficiency of global planning without sacrificing the adaptability of reactive agents, achieving both higher accuracy and significantly lower computational costs than reactive baselines.

## 8. Conclusion

In this work, we introduced a novel architecture that transitions GUI agents from a reactive, step-by-step observe–reason–act paradigm to a global, programmatic one. By leveraging an updatable state-machine graph as memory, our agent transforms GUI interaction into a deterministic graph traversal, enabling a Program-Based Planner to synthesize complete execution scripts in a single inference step, reducing reasoning complexity from $O(N)$ to $O(1)$ . This approach not only drastically improves efficiency, but it also ensures long-term robustness through a dynamic, self-correcting update mechanism that adapts to UI evolution. Empirical evaluations on the Reddit tasks in WebArena benchmark demonstrate the superiority of our framework, achieving a 95% success rate compared to 66% for the strongest baseline, while reducing end-to-end latency by 2 $\times$ and cost by 11.8 $\times$ .

## References

- Chen et al. (2025)

  Weizhi Chen, Ziwei Wang, Leyang Yang, Sheng Zhou, Xiaoxuan Tang, Jiajun Bu, Yong Li, and Wei Jiang. 2025.
  PG-Agent: An Agent Powered by Page Graph. In *Proceedings of the 33rd ACM International Conference on Multimedia*. 6878–6887.
- Cheng et al. (2024)

  Kanzhi Cheng, Qiushi Sun, Yougang Chu, Fangzhi Xu, Yantao Li, Jianbing Zhang, and Zhiyong Wu. 2024.
  Seeclick: Harnessing gui grounding for advanced visual gui agents.
  *arXiv preprint arXiv:2401.10935* (2024).
- Deng et al. (2023)

  Xiang Deng, Yu Gu, Boyuan Zheng, Shijie Chen, Sam Stevens, Boshi Wang, Huan Sun, and Yu Su. 2023.
  Mind2web: Towards a generalist agent for the web.
  *Advances in Neural Information Processing Systems* 36 (2023), 28091–28114.
- Google (2017)

  Google. 2017.
  UI Automator.
  <https://developer.android.com/training/testing/other-components/ui-automator>.


  [Accessed 11-02-2026].
- Gu et al. (2024)

  Yu Gu, Kai Zhang, Yuting Ning, Boyuan Zheng, Boyu Gou, Tianci Xue, Cheng Chang, Sanjari Srivastava, Yanan Xie, Peng Qi, et al. 2024.
  Is your llm secretly a world model of the internet? model-based planning for web agents.
  *arXiv preprint arXiv:2411.06559* (2024).
- Gur et al. (2023)

  Izzeddin Gur, Hiroki Furuta, Austin Huang, Mustafa Safdari, Yutaka Matsuo, Douglas Eck, and Aleksandra Faust. 2023.
  A real-world webagent with planning, long context understanding, and program synthesis.
  *arXiv preprint arXiv:2307.12856* (2023).
- He et al. (2024)

  Hongliang He, Wenlin Yao, Kaixin Ma, Wenhao Yu, Yong Dai, Hongming Zhang, Zhenzhong Lan, and Dong Yu. 2024.
  Webvoyager: Building an end-to-end web agent with large multimodal models.
  *arXiv preprint arXiv:2401.13919* (2024).
- Liu et al. (2023)

  Xiao Liu, Hao Yu, Hanchen Zhang, Yifan Xu, Xuanyu Lei, Hanyu Lai, Yu Gu, Hangliang Ding, Kaiwen Men, Kejuan Yang, et al. 2023.
  Agentbench: Evaluating llms as agents.
  *arXiv preprint arXiv:2308.03688* (2023).
- Microsoft (2024)

  Microsoft. 2024.
  Playwright.
  <https://playwright.dev>.


  Accessed: 2025-12-01.
- Nguyen et al. (2025)

  Dang Nguyen, Jian Chen, Yu Wang, Gang Wu, Namyong Park, Zhengmian Hu, Hanjia Lyu, Junda Wu, Ryan Aponte, Yu Xia, Xintong Li, Jing Shi, Hongjie Chen, Viet Dac Lai, Zhouhang Xie, Sungchul Kim, Ruiyi Zhang, Tong Yu, Mehrab Tanjim, Nesreen K. Ahmed, Puneet Mathur, Seunghyun Yoon, Lina Yao, Branislav Kveton, Jihyung Kil, Thien Huu Nguyen, Trung Bui, Tianyi Zhou, Ryan A. Rossi, and Franck Dernoncourt. 2025.
  GUI Agents: A Survey.
  arXiv:2412.13501 [cs.AI]
  <https://arxiv.org/abs/2412.13501>
- Ning et al. (2025)

  Liangbo Ning, Ziran Liang, Zhuohang Jiang, Haohao Qu, Yujuan Ding, Wenqi Fan, Xiao-yong Wei, Shanru Lin, Hui Liu, Philip S. Yu, and Qing Li. 2025.
  A Survey of WebAgents: Towards Next-Generation AI Agents for Web Automation with Large Foundation Models. In *Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2*.
- Niu et al. (2024)

  Runliang Niu, Jindong Li, Shiqi Wang, Yali Fu, Xiyu Hu, Xueyuan Leng, He Kong, Yi Chang, and Qi Wang. 2024.
  Screenagent: A vision language model-driven computer control agent.
  *arXiv preprint arXiv:2402.07945* (2024).
- Tanjim et al. (2025)

  Md Mehrab Tanjim, Yeonjun In, Xiang Chen, Victor S. Bursztyn, Ryan A. Rossi, Sungchul Kim, Guang-Jie Ren, Vaishnavi Muppala, Shun Jiang, Yongsung Kim, and Chanyoung Park. 2025.
  Disambiguation in Conversational Question Answering in the Era of LLMs and Agents: A Survey.
  arXiv:2505.12543 [cs.CL]
  <https://arxiv.org/abs/2505.12543>
- Tao et al. (2023)

  Heyi Tao, Sethuraman TV, Michal Shlapentokh-Rothman, and Derek Hoiem. 2023.
  Webwise: Web interface control and sequential exploration with large language models.
  *arXiv preprint arXiv:2310.16042* (2023).
- Wang et al. (2023)

  Guanzhi Wang, Yuqi Xie, Yunfan Jiang, Ajay Mandlekar, Chaowei Xiao, Yuke Zhu, Linxi Fan, and Anima Anandkumar. 2023.
  Voyager: An open-ended embodied agent with large language models.
  *arXiv preprint arXiv:2305.16291* (2023).
- Wen et al. (2024)

  Hao Wen, Yuanchun Li, Guohong Liu, Shanhui Zhao, Tao Yu, Toby Jia-Jun Li, Shiqi Jiang, Yunhao Liu, Yaqin Zhang, and Yunxin Liu. 2024.
  Autodroid: Llm-powered task automation in android. In *Proceedings of the 30th annual international conference on Mobile computing and networking*. 543–557.
- Yang et al. (2024)

  Ke Yang, Yao Liu, Sapana Chaudhary, Rasool Fakoor, Pratik Chaudhari, George Karypis, and Huzefa Rangwala. 2024.
  Agentoccam: A simple yet strong baseline for llm-based web agents.
  *arXiv preprint arXiv:2410.13825* (2024).
- Zhang et al. (2025b)

  Chi Zhang, Zhao Yang, Jiaxuan Liu, Yanda Li, Yucheng Han, Xin Chen, Zebiao Huang, Bin Fu, and Gang Yu. 2025b.
  AppAgent: Multimodal Agents as Smartphone Users. In *Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems*.
- Zhang et al. (2025a)

  Ruichen Zhang, Mufan Qiu, Zhen Tan, Mohan Zhang, Vincent Lu, Jie Peng, Kaidi Xu, Leandro Z Agudelo, Peter Qian, and Tianlong Chen. 2025a.
  Symbiotic Cooperation for Web Agents: Harnessing Complementary Strengths of Large and Small LLMs.
  *arXiv preprint arXiv:2502.07942* (2025).
- Zheng et al. (2023)

  Longtao Zheng, Rundong Wang, Xinrun Wang, and Bo An. 2023.
  Synapse: Trajectory-as-exemplar prompting with memory for computer control.
  *arXiv preprint arXiv:2306.07863* (2023).
- Zhou et al. (2023)

  Shuyan Zhou, Frank F Xu, Hao Zhu, Xuhui Zhou, Robert Lo, Abishek Sridhar, Xianyi Cheng, Tianyue Ou, Yonatan Bisk, Daniel Fried, et al. 2023.
  Webarena: A realistic web environment for building autonomous agents.
  *arXiv preprint arXiv:2307.13854* (2023).
