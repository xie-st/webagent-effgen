---
title: "ShopGym: An Integrated Framework for Realistic Simulation and Scalable Benchmarking of E-Commerce Web Agents"
arxiv_html: https://arxiv.org/html/2605.16116v1
downloaded: 2026-10-29
converted: arxiv LaTeXML HTML -> Markdown（本地图片 + alttext 公式还原）
---

# ShopGym: An Integrated Framework for Realistic Simulation and Scalable Benchmarking of E-Commerce Web Agents

- **Chinmay Savadikar** · North Carolina State University; Shopify
- **Mingyu Zhao** · Shopify
- **Yuanzheng Zhu** · Shopify
- **Han Li** · Shopify
- **Shuang Xie** · Shopify
- **Alberto Castelo** · Shopify
- **Tianfu Wu** · North Carolina State University
- **Lingyun Wang** · Shopify

###### Abstract

Developing and evaluating e-commerce web agents requires environments that preserve meaningful task structure while enabling controllable, reproducible, and scalable scientific comparison. Existing methodologies force a tradeoff: live storefronts provide realism but are non-stationary, difficult to inspect, and irreproducible, while hand-built sandbox benchmarks provide control but cover only a narrow range of layouts, catalogs, policies, and interaction patterns. We argue that the core bottleneck is methodological: the field lacks a scalable way to construct evaluation settings that are simultaneously realistic, diverse, controllable, inspectable, and reproducible. We introduce ShopGym, an integrated framework for realistic simulation and scalable benchmarking of e-commerce web agents. ShopGym is a framework for constructing e-commerce simulation environments and grounded benchmark tasks. Its simulation layer, ShopArena, converts live seed storefronts into self-contained sandbox shops through anonymized shop specifications and a staged, validated generation process. On top of these simulated storefronts, ShopGuru synthesizes benchmark tasks across seven skill categories, grounding each task in the shop’s catalog, navigation structure, policies, and interaction affordances. Together, ShopArena and ShopGuru produce self-contained, resettable, inspectable, and stable evaluation artifacts that preserve structural properties and agent-evaluation signals relevant to shopping tasks. We validate the framework through graph-based structural analysis and agent-based behavioral evaluation with 224 generated tasks across six sandbox shops: three constructed with synthetic data and three with real data. Our results show that the synthetic shops preserve key structural properties of live storefronts, with agent performance on synthetic shops positively correlated with performance on live storefronts.

## 1 Introduction

As web agents become more capable, the field increasingly needs stable environments that support long-horizon interaction in realistic, user-facing settings. E-commerce is a particularly demanding domain for this purpose: shopping tasks require agents to navigate multi-page interfaces, interpret product information, satisfy user constraints, compare alternatives, and execute actions such as selecting variants or adding items to cart. These tasks combine perception, reasoning, and sequential decision-making in a grounded setting, making storefronts a compelling testbed for web-agent evaluation. The importance of this domain is reflected in growing interest in shopping assistants [[23](#bib.bib23), [25](#bib.bib25), [17](#bib.bib17)], offline A/B testing [[2](#bib.bib2), [15](#bib.bib15)], and user behavior simulation for e-commerce applications [[10](#bib.bib10), [23](#bib.bib23), [26](#bib.bib26), [20](#bib.bib20)].

Existing environments for e-commerce agents face a fundamental tradeoff between realism and experimental control. Live-websites [[21](#bib.bib21), [7](#bib.bib7), [11](#bib.bib11)] offer strong realism: agents are run and evaluated against realistic layouts, and naturally occurring variation and interaction patterns. But live storefronts are inherently non-stationary. Catalogs, layouts, and webpage design on live storefronts can change, collections can be reorganized, and storefronts participating in live A/B testing can serve separate variants for different requests. This non-stationary behavior makes reproducible training and evaluation of web agents challenging. The evaluation performance can reflect not only agent capability but also incidental variation from website drift, location-specific behavior, and operational noise, making results difficult to reproduce and agents difficult to compare fairly [[21](#bib.bib21)], and training runs difficult to reproduce.

Sandbox environments [[28](#bib.bib28), [8](#bib.bib8), [22](#bib.bib22), [16](#bib.bib16), [18](#bib.bib18), [12](#bib.bib12)], in contrast, are controllable and repeatable by design, but at the cost of realism and diversity of live websites. Manually constructing realistic storefront environments is expensive and covers only a narrow range of layouts, catalog structures, and interaction patterns.

Existing work proposing environments for e-commerce agents has largely explored the two methodologies, with works like DeepShop [[11](#bib.bib11)] using live websites, and WebShop [[22](#bib.bib22)], ShoppingBench [[16](#bib.bib16)], ShopSimulator [[18](#bib.bib18)], and WebMall [[12](#bib.bib12)] manually building sandbox environments. We argue that the deeper bottleneck is methodological: the field lacks a scalable way to *construct reliable simulated environments that are realistic, controllable, inspectable, and reproducible*.

To address this gap, we propose ShopGym, a framework for constructing realistic e-commerce simulation environments and grounded web-agent benchmarks. ShopGym comprises two complementary components in a synergistic workflow: (a) the simulation environment layer, ShopArena, transforms one or more live seed storefronts into a self-contained sandbox shop; and (b) ShopGuru synthesizes benchmark tasks grounded in the sandbox shops.

![Refer to caption](images/30_ShopGym/full_pipeline_v4.png)


Figure 1: 
ShopGym comprises two components. ShopArena provides a simulation environment populated with synthetic sandbox shops, along with a scalable pipeline that generates new sandbox shops from one or more live seed storefronts through specification synthesis followed by data and code generation. ShopGuru then consumes the resulting catalog, collections, pages, and shop statistics to generate both short-horizon tasks covering primitive skills and long-horizon shopping journeys that combine these skills.

ShopArena: validated simulation environment. To generate the simulation environment grounded in real storefronts, ShopArena separates storefront understanding (exploration) from sandbox synthesis (generation) through an intermediate specification document that serves as the sole interface between exploration and generation. Given one or more seed storefronts, ShopArena autonomously explores the sites and writes an anonymized specification capturing their navigation structure, user-facing affordances, high-level page organization, and catalog statistics. When multiple seeds are provided, ShopArena composes their structural and behavioral signals into a single specification, so one sandbox shop can span diversity that no individual source storefront would cover. A staged generation pipeline then synthesizes a runnable sandbox shop from the specification, iteratively refining the implementation through build checks, type checking, and multimodal visual validation. ShopArena does not aim to clone a particular storefront; it produces behaviorally aligned approximations – synthetic shops grounded in real storefront structure and interaction patterns, but with synthetic brand identity, products, descriptions, and imagery. The goal is not visual or brand-level fidelity but structural, behavioral, and statistical alignment sufficient for controlled evaluation. *Because the specification is human-readable, benchmark creators can also edit generated environments in controlled ways without re-exploring the source storefronts*.

ShopGuru: grounded task generation. ShopGuru consumes the sandbox shop’s catalog, navigation graph, and store policies and synthesizes tasks that are valid against the environment they will be executed in. This design separates live-web exploration from benchmark execution. The generated shops are stable and resettable, while the intermediate specification provides an inspectable control surface that benchmark creators can edit without re-exploring the source storefronts.

We evaluate ShopGym by generating synthetic sandbox shops and anonymized twin shops, then validating them using structural metrics and agent-based behavioral comparisons. Across paired tasks defined over source and generated shops, agent success rates on sandbox environments positively correlate with success rates on live storefronts, indicating that generated storefronts retain meaningful evaluative signal from live-web settings while substantially improving control and reproducibility. While it does not completely replace live-web evaluation, ShopGym provides a stronger methodology for standardized benchmarking and analysis. To summarize, our contributions are:

- •

  We identify the realism-control tradeoff in e-commerce environments and agent evaluation as a methodological bottleneck, and argue that the missing capability is scalable construction of realistic, controllable, and reproducible environments and evaluation benchmarks.
- •

  We bridge this gap with ShopGym, a framework for constructing realistic, controlable, and reproducible e-commerce agent evaluation environments.
- •

  We present ShopArena, a pipeline that converts live seed storefronts into anonymized, self-contained sandbox shops through specification synthesis and staged code generation.
- •

  We present ShopGuru, a grounded task-generation pipeline that created short-horizon and long-horizon shopping tasks tied to each generated shop’s catalog, navigation structure, filters, and policies.
- •

  We validate that the simulated environments preserve meaningful signal from live storefront evaluation, supporting their use as controlled, behaviorally aligned benchmarking environments.

## 2 ShopGym

ShopGym combines two complementary frameworks: ShopArena, a simulation environment composed of interactable sandbox shops, and ShopGuru, an evaluation framework with a synthetic task generation pipeline grounded in the sandbox shops. ShopArena consists of a simulation environment containing multiple sandbox shops. It also provides a scalable pipeline to extend the environment by generating new synthetic sandbox shops: given one or more seed storefronts $\{S\}_{N}$ (real e-commerce websites), the ShopArena generation pipeline can generate a stable, self-contained, and anonymized sandbox shop $E$ using a multi-agent shop exploration and code synthesis pipeline. The ShopGuru evaluation framework generates a set of instruction following tasks $T$ defined over the sandbox shop $E$ . Following standard practice [[28](#bib.bib28), [1](#bib.bib1)], we define a task $T=(E,{s_{0}},p,V)$ as a sandbox shop $E$ with initial state $s_{0}$ , a natural-language intent $p$ , and a verification function $V$ that maps the agent’s trajectory to a binary success score. Figure [1](#S1.F1) illustrates the full pipeline.

### 2.1 ShopArena

To generate each sandbox shop in the ShopArena environment, we propose a scalable pipeline that converts one or more live seed storefronts $\{S\}_{N}$ into a realistic, self-contained, inspectable and reproducible sandbox shop. *Importantly, the pipeline can be extended to any live storefront, making ShopArena an evolving environment that can be updated with new sandbox stores*.

The generation pipeline. Doing this end-to-end in one pass is an extremely long-horizon task: it combines storefront exploration and understanding, synthetic catalog construction, and source-code generation in a single trajectory that is hard to control and debug, and prone to incomplete outputs as agentic LLMs accumulate context [[9](#bib.bib9), [14](#bib.bib14)]. We instead split synthesis into two phases connected by a single intermediate artifact: an anonymized design specification $M$ . The *exploration* phase (§[2.1.1](#S2.SS1.SSS1)) browses $\{S\}_{N}$ and writes $M$ ; the *generation* phase (§[2.1.2](#S2.SS1.SSS2)) reads $M$ and writes the source code for a runnable sandbox shop. This split confines all live-web dependence to exploration, lets either phase be re-run independently, and turns the human-readable specification into a control surface for editing the generated environment without re-exploring the source.

Multi-agent framework. Both phases are organized as small sets of agents communicating through the file system. Each agent is an instance of a coding agent (Claude Code, with Claude Opus 4.6 as the underlying model) differentiated by (a) the tools it is given access to and (b) the objective described by its system prompt. Agents share a workspace directory but do not share a conversational context.

#### 2.1.1 Exploration: From Live Storefront to Specifications

The exploration phase browses one or more seed storefronts $\{S\}_{N}$ , extracts the properties of a live storefront that matter for downstream environment generation, and generates a specification document $M$ . The specification consists of three facets: (i) a design manual, which is a natural language description of the store and its visual style; (ii) a structured list of its attributes that are typically present on storefronts such as filter attributes, navigation menu design, pagination information, etc. (iii) statistics such as number of products, price range and distribution, etc. Figure [2](#S2.F2) shows the full exploration pipeline.

Static prefetch. The phase begins with a deterministic prefetch of canonical surfaces (homepage HTML, sitemap, search and cart endpoints, public catalog JSON, policy pages).

Planner agent ( $\textsc{Agent}_{\text{plan}}$ ). A single planner consumes the prefetched files and, with a small live-browsing budget, writes a plan that decomposes exploration of $S_{i}$ into focused subtasks. The planner is shown an example plan but is required to adapt it to $S_{i}$ , so coverage is grounded in what the storefront actually exposes rather than in a fixed template. An example plan is shown in Fig [G.1](#A7.SS1).

Specification agent ( $\textsc{Agent}_{\text{spec}}$ ). For each planned subtask, the harness spawns a fresh specification agent equipped with browser-automation tools (Playwright). The agent performs targeted browsing, captures evidence (screenshots, snapshots, optional XHR traces), and writes an anonymized fragment of $M$ for its subtask. $\textsc{Agent}_{\text{spec}}$ is instructed to ignore brand names, product names, named individuals, and absolute URLs at write time, so everything downstream of exploration is anonymous by construction — no separate redaction pass is required.

Consolidation and multi-seed composition. A non-agentic LLM merges the per-subtask fragments into one specification per feature, yielding $M$ . For a sandbox shop calibrated on multiple seeds, exploration runs independently on each storefront, producing one $M(S_{i})$ per seed; a second LLM merge composes them into a single composite specification. Multi-seed composition is how ShopArena scales *within* a shop: a single sandbox can span structural and behavioral diversity that no individual source storefront would cover.

At the end of the exploration phase, the pipeline produces the anonymized shop specifications $M$ for the sandbox shop, with the design document divided into multiple predefined *features* (website skeleton, homepage, collections, etc.) A full list of features and an example of the full specifications is provided in Appendix [F](#A6)

![](images/30_ShopGym/shop_explore.svg)


Figure 2: The exploration phase fetches key pages, and the public product catalogue. A planner agent then writes a plan using a list of predefined features to implement. Finally, Specification agents write anonymized specifications for each sub-task, which are merged to form the shop specifications.

#### 2.1.2 Generation: From Specifications to Sandbox Shop

The generation phase synthesizes a runnable storefront from $M$ . Because it sees only $M$ and never the prefetched evidence, generation is anonymous by construction. The generation phase has two parts: a catalog synthesis pipeline and a source-code synthesis loop.

Synthetic catalog generation. The generation step first synthesizes the collection details (description, associated products), product names, product descriptions, and product images using the design manual and statistics from $M$ . The data synthesis is structured as simple LLM calls that generate the data for one collection at a time. The details of the models used for the data generation are provided in Appendix [B.1](#A2.SS1).

Stepwise source-code synthesis. ShopArena generates the storefront source code in a fixed sequence of *steps*, each scoped to one feature: site shell and homepage, collection pages, product detail page, cart, search and filtering, policy pages, and a final integration pass. Each step is given only the slice of $M$ relevant to its feature, the catalog, and the current state of the codebase, and is executed by a dedicated execution–verification loop. Steps run in a fixed order over a shared workspace, so later steps build on a stable surface produced by earlier ones, and a failure in one step can be repaired without regenerating the rest of the shop.

![](images/30_ShopGym/shop_gen.svg)


Figure 3: The generation phase. A staged sequence of feature-scoped steps is each driven by an execution–verification loop in which a fresh Execution Agent edits the codebase and a separate Verification Agent writes natural-language feedback.

Execution–verification loop. Within each step, code generation is structured in the spirit of the Ralph technique11
1
<https://ghuntley.com/ralph/>: a fresh agent process is spawned at each iteration, reads the current state of the workspace from disk, edits the codebase, and exits; the harness then runs verification, writes feedback to disk, and spawns the next iteration. Two specialised agents alternate within the loop:

- •

  Execution Agent ( $\textsc{Agent}_{\text{exec}}$ ). At each iteration, a coding agent with the codebase and terminal access receives the feature to implement, the slice of $M$ , the catalog, and (if present) the verifier’s most recent feedback. It edits the source code and runs lightweight checks (type checking, build).
- •

  Verifiers. The code generated by $\textsc{Agent}_{\text{exec}}$ is checked by both rule-based verifiers and a multimodal verification agent. The rule-based verifiers ensure the site builds successfully, required pages return valid HTTP success codes, and outputs are properly structured. The verification agent then hosts the shop locally, uses browser automation to inspect the rendered site for visual and functional issues, and produces natural-language feedback for the next $\textsc{Agent}_{\text{exec}}$ iteration.

Long-context management. Each step could in principle be driven by one long-running agent that holds the codebase, the verifier’s reports, and the slice of $M$ in a single context window. We avoid this because long-horizon code generation degrades as context grows [[9](#bib.bib9), [14](#bib.bib14)], and we observed the same failure mode in our own development: partially broken outputs the agent itself reports as complete. Spawning a fresh process at each iteration externalises three concerns that would otherwise pile up inside one prompt: the *state context* (the current source code, read directly from disk), the *implementation context* (the agent’s prior tool-use traces, discarded), and the *evaluation context* (the verifier’s most recent feedback, at a known path). Each fresh $\textsc{Agent}_{\text{exec}}$ iteration sees only what the workspace and the latest verifier note convey; the prompt does not grow unboundedly, and the agent re-establishes context from the artifacts that matter. The loop runs for a fixed iteration budget (30 by default) or terminates early when the agent reports no further action is required.

Final consolidation. After all feature-specific steps complete, ShopArena runs a final consolidation pass: a global agent navigates a tour of canonical routes, and fixes the remaining defects raised by the verifiers in prior steps.

### 2.2 ShopGuru: Grounded Task Generation

ShopGuru uses the collections, product details, and statistics from ShopArena’s generation phase (§[2.1.2](#S2.SS1.SSS2)) and generates synthetic tasks grounded in the sandbox shop. The pipeline uses a small set of *deterministic generators*, which construct short horizon tasks meant for evaluating primitive skills, and a single *LLM-authored* generator for long-horizon shopping journeys. The pipeline is structured as an execution-verification loop: the generated tasks (using rule-based or LLM-based generators) are verified using multiple rule-based verifiers. The verifiers validate that the collections, products, filter types and options, and pages referenced by the task are present in the shop’s data. A detailed description of the verifiers can be found in Table [2](#A11.T2). Figure [4](#S2.F4)
illustrates the full pipeline.

#### 2.2.1 Skill Catalog

We organize ShopGuru’s seven skill categories into three short-horizon groups and one long-horizon group, summarized in Table [1](#A8.T1) in Appendix [H](#A8). The three short-horizon groups are themselves the underlying primitives that the long-horizon journeys re-combine.

#### 2.2.2 Short-Horizon Task Generation

Short-Horizon tasks are meant to evaluate the basic instruction following capabilities of agents. The short-horizon tasks are generated using rule-based generators to evaluate three primitive skills:

Product Discovery (search-exact, search-substitute).
The discovery generators sample products from the catalog and emit two
task variants per product: one asking the agent to find the product by
its exact title, and one asking for a semantically similar
alternative. To keep the dataset diverse, the sampler accepts at most
one product per product\_type, and excludes inactive products,
gift cards, and products with no available variant (so an agent is
never asked to add an out-of-stock item).

Filter-Selection (browse, filter).
Browse tasks pick a populated, non-generic collection (at least three
products; generic catchall handles like all, sale,
featured, or best-sellers excluded) and ask the
agent to navigate to the collection page and add any product to cart.
The filter generator additionally pairs the collection with a
realistic facet $(\textit{dim},\textit{value})$ . The non-trivial
design decision here is feasibility: shop-wide option statistics are
a poor source for per-collection filter facets because a dimension
can be common in the catalog overall yet absent from a specific
collection. We therefore build a *per-collection* option index
from the collection’s own products and only emit a task when at least
one product in the collection actually has the chosen
$(\textit{dim},\textit{value})$ pair. As a fallback, when no priority
variant-option dimension is feasible in a collection, we use the
universal product fields Vendor (storefront-rendered as
“Brand”) and ProductType (rendered as “Type”), which
every storefront filter UI exposes regardless of variant-option
coverage.

Information-Seeking (shipping, returns).
The policy generator searches the shop’s extracted pages.json
for pages whose title or handle matches a small keyword list
(shipping/delivery for shipping;
return/refund/exchange for returns). Both
the /pages/ $\langle$ handle $\rangle$  route and the platform-default
/policies/ $\langle$ name $\rangle$ -policy route are emitted as
soft URL hints (url\_contains plus a
url\_contains\_alt list), since some storefronts surface the
policy under a custom page handle and others under the platform
default.

![](images/30_ShopGym/shopguru-task-gen.svg)


Figure 4: The ShopGuru task generation pipeline. Deterministic generators emit short-horizon tasks (search-exact, search-substitute, browse, filter, shipping, returns); an LLM-authored generator emits long-horizon shopping journeys reconciled against the shop data via a validator-driven polish loop. All emitted tasks are checked by rule-based verifiers (Table [2](#A11.T2)).

#### 2.2.3 LLM-Authored Long-Horizon Journeys

Long-horizon journeys are the workhorse of the benchmark’s
hard\_long\_horizon bundle. They mimic the kind of multi-step
behavior we observe in real human shopper traces — filter
$\rightarrow$ sort $\rightarrow$ inspect $\rightarrow$ detour to a
policy page $\rightarrow$ add to cart $\rightarrow$ edit
quantity — which the primitive-task generators by themselves do not
cover. Authoring such journeys by hand is prohibitively expensive at
scale, so ShopGuru delegates the long-horizon
authoring to an LLM (e.g. GPT-5 or Gemini 3 Pro) with two structural
guards: (i) a few-shot prompt grounded in the shop’s actual catalog,
navigation, and policy pages, and (ii) a polish loop that uses the
same validator from §[2.2.4](#S2.SS2.SSS4) as a feedback
signal.

Listing [3](#LST3) shows a representative end-to-end (E2E) task that chains
collection navigation, a Color filter, a price sort option, and a
final cart action. The few-shot examples in the user prompt template
(eight in total; the full prompt and three representative examples are
in Appendix [L](#A12)) are constructed to reflect
commonly observed click-stream patterns in human shopper sessions on production
storefronts, drawing on prior characterizations of online shopping
behavior [[19](#bib.bib19), [10](#bib.bib10)]: multi-pet household shopping,
returns-cautious browse-without-purchase, free-shipping-threshold
calculation, cross-brand comparison, filter-recover, first-time-visitor
info-page detour, homepage-callout brand drilldown, and so on.

The polish loop (Appendix [J](#A10)) follows from a known
weakness of single-pass LLM authoring: the model occasionally
hallucinates a product into the wrong collection, asks for a variant
option that a product does not expose (e.g. “select a Color” on a
gift card), or names a filter dimension that has no realizable values
in the target collection. We close this gap by reusing the validator
as a critic. After each generation pass, the validator returns a list
of per-task issues; ShopGuru filters to the actionable subset (every
error-severity finding plus the hallucination-class warnings) and
constructs a polish prompt that lists *only the flagged tasks*
alongside their specific issues and the shop context, and asks the
LLM to regenerate *only those tasks* while preserving their IDs.
The polish loop runs for at most two rounds. In our experiments, this
is sufficient to drive the residual error rate to zero on most shops
without human review. When tasks still fail validation after two
rounds, the build halts with a non-zero exit code rather than
silently shipping the flawed tasks; a human curator then either
re-runs generation with a different seed or hand-authors replacements
under data\_sources/, which override the auto-generated
outputs in the next build.

#### 2.2.4 Post-Generation Validation

A small dependency-free validator runs over every emitted benchmark
file as the final gate. Its seven core rules
(Table [2](#A11.T2))—four error-severity and three
warning-severity—target the failure modes we observed during
multi-shop benchmark regeneration; collectively they catch every
class of grounding mismatch we encountered. An actionable subset
of the validator’s findings (every error plus the two
hallucination-class warnings) is also reused as the polish signal
for the LLM-authored journey generator (§[2.2.3](#S2.SS2.SSS3)),
so the same audit logic both gates the output and steers the LLM
toward feasible tasks; the remaining unknown-page warning
is advisory only.

## 3 Evaluating Sandbox Shop Quality

For the synthetic shops in the ShopArena environment to be a reasonable substitute for live storefronts, we want the sandbox shops to be structurally and behaviorally similar to real websites. Structural validation aims to evaluate the static structure of the synthetic shop against the real shops, whereas behavioral validation evaluates shopping workflows.

To demonstrate and validate the ShopArena as a structurally and behaviorally aligned environment, we generate three synthetic sandbox shops spanning clothing, cookware and electronics hardware domains. We refer to these shops as sandbox shops. The screenshots of the sandbox shops can be found in Section [E](#A5), along with the links to the live hosted sandbox shops. We further generate three synthetic shops using real product data instead of synthetic data, which we refer to as twin shops. When generating the twin shops, we use an additional visual verification agent that matches the visual theme and structure of the real storefronts.

### 3.1 Structural Validity

To validate the structure of the sandbox shops, we compare them with real shops along two axes: Observation and Interaction Complexity, and State Transition Complexity. We use 7 real shops and 3 synthetic shops for the comparisons. We note that this is an unpaired validation.

Observation/Interaction Complexity. To compare the observation space, we use the depth of the simplified accessibility tree as a proxy for evaluating the nesting complexity of the websites22
2
As defined by BrowserGym. The nesting complexity evaluates how much structured content the agents must parse. We compare the interaction complexity by counting the number of unique elements on the website that support the fill action, click action, or elements that support select style controls (choice). Figure [5(c)](#S3.F5.sf3) shows that the synthetic sandbox shops are comparable in terms of observation and interaction complexity.

State Transition Complexity. To compare the state transition complexity, we treat the website as a directed state-transition graph, where each node corresponds to a distinct UI state, as illustrated in Figure [5(a)](#S3.F5.sf1). Each pink node (for example /) denotes individual pages, and violet nodes (/:navigation) denote alternate UI configurations of those pages when interactive elements are opened. Edges denote the actions that trigger transitions between the states, for instance, the red arrow shows clicking the navigation bar on / transitions the state to /:navigation.

The aggregated statistics in Figure [5(b)](#S3.F5.sf2) show that the synthetic sandbox shops have a comparable number of nodes to the real shops, indicating similar coverage of distinct UI states. However, they exhibit fewer edges and a lower average out-degree, meaning that each state tends to have fewer outgoing transitions. This reduction is largely because real storefronts contain additional navigation paths through external links, marketing pages, and auxiliary site components that are intentionally excluded from the sandbox environments. Overall, the synthetic shops closely match real storefronts in observation complexity, action affordances, and transition-graph scale, supporting their use as realistic sandbox environments.

![Refer to caption](images/30_ShopGym/shop-arena-pipeline-tx_graph_v2.png)


(a)

![](images/30_ShopGym/shop_statistics_transition.svg)


(b)

![](images/30_ShopGym/shop_statistics_observation_action.svg)


(c)

Figure 5: (a) An example directed graph visualization of the website; (b) the State Transition statistics; (c) the Observation/Interaction statistics

### 3.2 Behavioral Validation

![](images/30_ShopGym/bgym_calibration_easy_vs_complex_twin.svg)


(a) BrowserGym Harness.

![](images/30_ShopGym/calibration_easy_vs_complex_twin.svg)


(b) Internal Harness.

Figure 6: Success rates on real storefronts vs. ShopArena twins.

We use the twin shops to perform behavioral validation of the ShopArena pipeline. The twin shops are visually and structurally similar to real shops, with the shop-specific information such as names, locations, contact details, etc. replaced with mock information. We then generate the ShopGuru evaluation suite for the real and twin shops, and evaluate multiple frontier models on both variants. We evaluate GPT-5-mini, GPT5 [[13](#bib.bib13)], and Gemini 3 Flash.

We evaluate the models using two harnesses: a BrowserGym [[4](#bib.bib4)] based implementation that uses accessibility trees (AXTrees), and a proprietary implementation that uses screenshots along with AXTrees. We use GPT-5 as a judge in both implementations, which analyzes the agent trajectories and provides a binary success rate. The implementation details are provided in Appendix [B](#A2).

Figure [6](#S3.F6) shows that all models achieve similar performance on the real storefront and its twin variant. Furthermore, the performance on the complex
tasks improves with stronger models. This shows that from the
perspective of agent behavior, the sandbox shops are behaviorally
consistent with real shops.

## 4 Validating ShopGuru task complexity

![](images/30_ShopGym/bgym_composite_easy_vs_complex_twin_v2.svg)


(a) BrowserGym Harness.

![](images/30_ShopGym/composite_easy_vs_complex_twin_v2.svg)


(b) Internal Harness.

Figure 7: Success rates on the synthetic sandbox shops.

To validate that the ShopGuru task generation pipeline can generate complex tasks, we evaluate frontier models with the ShopGuru evaluation suite on the sandbox shops. We use the same web agent, harness, and judge setup as §[3.2](#S3.SS2).

As seen in Figure [7(a)](#S4.F7.sf1) GPT-5-mini with the BrowserGym harness achieves a success rate of 47.9% on the Long-Horizon complex tasks, Gemini 3 Flash achieves 59%, and GPT-5 achieves 62.5%. The results with the custom harness show similar performance across all models. A low performance of frontier models shows that the ShopGuru task generation pipeline can generate meaningfully hard tasks which are useful for training and evaluation of next generation e-commerce agents.

## 5 Conclusion

We presented ShopGym, an integrated framework for realistic simulation and scalable benchmarking of e-commerce web agents. ShopGym addresses a central methodological gap in current environments: live storefronts provide realism but are non-stationary and irreproducible, while sandbox environments are controllable but limited in diversity and realism. By combining ShopArena for sandbox shop generation and ShopGuru for grounded task synthesis, ShopGym produces evaluation artifacts that are self-contained, inspectable, resettable, and stable across runs.

Our results show that the generated shops are structurally comparable to real storefronts and preserve meaningful behavioral signal for agent evaluation. In particular, agent performance on synthetic twins positively tracks performance on live storefronts, while fully synthetic composite shops yield benchmarks of comparable difficulty. These findings suggest that ShopGym provides a practical middle ground between live-web realism and sandbox control, and offers a scalable foundation for more reproducible and interpretable evaluation of e-commerce web agents.

## References

- [1]

  Pranjal Aggarwal, Graham Neubig, and Sean Welleck.
  Gym-anything: Turn any software into an agent environment.
  *arXiv preprint arXiv:2604.06126*, 2026.
- [2]

  Alberto Castelo, Zahra Zanjani Foumani, Ailin Fan, Keat Yang Koay, Vibhor Malik, Yuanzheng Zhu, Han Li, Meysam Feghhi, Ronie Uliana, Shuang Xie, Zhaoyu Zhang, Angelo Ocana Martins, Mingyu Zhao, Francis Pelland, Jonathan Faerman, Nikolas LeBlanc, Aaron Glazer, Andrew McNamara, Lingyun Wang, and Zhong Wu.
  Simgym: Traffic-grounded browser agents for offline A/B testing in e-commerce.
  *CoRR*, abs/2602.01443, 2026.
  doi: 10.48550/ARXIV.2602.01443.
  URL <https://doi.org/10.48550/arXiv.2602.01443>.
- [3]

  Hyungjoo Chae, Jungsoo Park, and Alan Ritter.
  Safe and scalable web agent learning via recreated websites.
  *CoRR*, abs/2603.10505, 2026.
  doi: 10.48550/ARXIV.2603.10505.
  URL <https://doi.org/10.48550/arXiv.2603.10505>.
- [4]

  Thibault Le Sellier de Chezelles, Maxime Gasse, Alexandre Lacoste, Massimo Caccia, Alexandre Drouin, Léo Boisvert, Megh Thakkar, Tom Marty, Rim Assouel, Sahar Omidi Shayegan, Lawrence Keunho Jang, Xing Han Lù, Ori Yoran, Dehan Kong, Frank F. Xu, Siva Reddy, Graham Neubig, Quentin Cappart, Russ Salakhutdinov, and Nicolas Chapados.
  The browsergym ecosystem for web agent research.
  *Transactions on Machine Learning Research*, 2025.
  ISSN 2835-8856.
  URL <https://openreview.net/forum?id=5298fKGmv3>.
  Expert Certification.
- [5]

  Xiang Deng, Yu Gu, Boyuan Zheng, Shijie Chen, Samual Stevens, Boshi Wang, Huan Sun, and Yu Su.
  Mind2web: Towards a generalist agent for the web.
  In Alice Oh, Tristan Naumann, Amir Globerson, Kate Saenko, Moritz Hardt, and Sergey Levine, editors, *Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023*, 2023.
  URL <http://papers.nips.cc/paper_files/paper/2023/hash/5950bf290a1570ea401bf98882128160-Abstract-Datasets_and_Benchmarks.html>.
- [6]

  Apurva Gandhi and Graham Neubig.
  Go-browse: Training web agents with structured exploration.
  In *The Fourteenth International Conference on Learning Representations*, 2026.
  URL <https://openreview.net/forum?id=IpzRWE52yw>.
- [7]

  Hongliang He, Wenlin Yao, Kaixin Ma, Wenhao Yu, Yong Dai, Hongming Zhang, Zhenzhong Lan, and Dong Yu.
  Webvoyager: Building an end-to-end web agent with large multimodal models.
  In Lun-Wei Ku, Andre Martins, and Vivek Srikumar, editors, *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), ACL 2024, Bangkok, Thailand, August 11-16, 2024*, pages 6864–6890. Association for Computational Linguistics, 2024.
  doi: 10.18653/V1/2024.ACL-LONG.371.
  URL <https://doi.org/10.18653/v1/2024.acl-long.371>.
- [8]

  Jing Yu Koh, Robert Lo, Lawrence Jang, Vikram Duvvur, Ming Chong Lim, Po-Yu Huang, Graham Neubig, Shuyan Zhou, Ruslan Salakhutdinov, and Daniel Fried.
  Visualwebarena: Evaluating multimodal agents on realistic visual web tasks.
  In *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), ACL 2024*, 2024.
  URL <https://arxiv.org/abs/2401.13649>.
- [9]

  Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang.
  Lost in the middle: How language models use long contexts.
  *Transactions of the Association for Computational Linguistics*, 12:157–173, 2023.
  URL <https://api.semanticscholar.org/CorpusID:259360665>.
- [10]

  Yuxuan Lu, Jing Huang, Yan Han, Bingsheng Yao, Sisong Bei, Jiri Gesi, Yaochen Xie, Qi He, Dakuo Wang, et al.
  Can llm agents simulate multi-turn human behavior? evidence from real online customer behavior data.
  *arXiv preprint arXiv:2503.20749*, 2025.
- [11]

  Yougang Lyu, Xiaoyu Zhang, Lingyong Yan, Maarten de Rijke, Zhaochun Ren, and Xiuyi Chen.
  Deepshop: A benchmark for deep research shopping agents.
  *ArXiv*, abs/2506.02839, 2025.
  URL <https://api.semanticscholar.org/CorpusID:279118560>.
- [12]

  Ralph Peeters, Aaron Steiner, Luca Schwarz, Julian Yuya Caspary, and Christian Bizer.
  Webmall–a multi-shop benchmark for evaluating web agents [technical report].
  *arXiv preprint arXiv:2508.13024*, 2025.
- [13]

  Aaditya Singh, Adam Fry, Adam Perelman, Adam Tart, Adi Ganesh, Ahmed El-Kishky, Aidan McLaughlin, Aiden Low, AJ Ostrow, Akhila Ananthram, et al.
  Openai gpt-5 system card.
  *arXiv preprint arXiv:2601.03267*, 2025.
- [14]

  Akshit Sinha, Arvindh Arun, Shashwat Goel, Steffen Staab, and Jonas Geiping.
  The illusion of diminishing returns: Measuring long horizon execution in llms.
  *ArXiv*, abs/2509.09677, 2025.
  URL <https://api.semanticscholar.org/CorpusID:281252776>.
- [15]

  Dakuo Wang, Ting-Yao Hsu, Yuxuan Lu, Hansu Gu, Limeng Cui, Yaochen Xie, William Headean, Bingsheng Yao, Akash Veeragouni, Jiapeng Liu, et al.
  Agenta/b: Automated and scalable web a/btesting with interactive llm agents.
  *arXiv preprint arXiv:2504.09723*, 2025a.
- [16]

  Jiang Wang, Kejun Xiao, Qi Sun, Huaipeng Zhao, Tao Luo, Jiandong Zhang, and Xiaoyi Zeng.
  Shoppingbench: A real-world intent-grounded shopping benchmark for llm-based agents.
  In *AAAI Conference on Artificial Intelligence*, 2025b.
  URL <https://api.semanticscholar.org/CorpusID:280536823>.
- [17]

  Jiangyuan Wang, Kejun Xiao, Huaipeng Zhao, Tao Luo, and Xiaoyi Zeng.
  Productresearch: Training e-commerce deep research agents via multi-agent synthetic trajectory distillation.
  *CoRR*, abs/2602.23716, 2026a.
  doi: 10.48550/ARXIV.2602.23716.
  URL <https://doi.org/10.48550/arXiv.2602.23716>.
- [18]

  Pei Wang, Yanan Wu, Xiaoshuai Song, Weixun Wang, Gengru Chen, Zhongwen Li, Ke Yan, Ken Deng, Qi Liu, Shu-Man Zhao, Shaopan Xiong, Xuepeng Liu, Xuefeng Chen, Wanxi Deng, Wenbo Su, and Bo Zheng.
  Shopsimulator: Evaluating and exploring rl-driven llm agent for shopping assistants.
  *ArXiv*, abs/2601.18225, 2026b.
  URL <https://api.semanticscholar.org/CorpusID:285050373>.
- [19]

  Ziyi Wang, Yuxuan Lu, Wenbo Li, Amir A. Amini, Bo Sun, Yakov Bart, Weimin Lyu, Jiri Gesi, Tian Wang, Jing Huang, Yu Su, Upol Ehsan, Malihe Alikhani, Toby Jia-Jun Li, Lydia B. Chilton, and Dakuo Wang.
  Opera: A dataset of observation, persona, rationale, and action for evaluating llms on human online shopping behavior simulation.
  *ArXiv*, abs/2506.05606, 2025c.
  URL <https://api.semanticscholar.org/CorpusID:279244562>.
- [20]

  Ziyi Wang, Yuxuan Lu, Yimeng Zhang, Jing Huang, and Dakuo Wang.
  Customer-r1: Personalized simulation of human behaviors via rl-based llm agent in online shopping.
  *arXiv preprint arXiv:2510.07230*, 2025d.
- [21]

  Tianci Xue, Weijian Qi, Tianneng Shi, Chan Hee Song, Boyu Gou, Dawn Song, Huan Sun, and Yu Su.
  An illusion of progress? assessing the current state of web agents.
  *CoRR*, abs/2504.01382, 2025.
  doi: 10.48550/ARXIV.2504.01382.
  URL <https://doi.org/10.48550/arXiv.2504.01382>.
- [22]

  Shunyu Yao, Howard Chen, John Yang, and Karthik Narasimhan.
  Webshop: Towards scalable real-world web interaction with grounded language agents.
  In Sanmi Koyejo, S. Mohamed, A. Agarwal, Danielle Belgrave, K. Cho, and A. Oh, editors, *Advances in Neural Information Processing Systems 35: Annual Conference on Neural Information Processing Systems 2022, NeurIPS 2022, New Orleans, LA, USA, November 28 - December 9, 2022*, 2022.
  URL <http://papers.nips.cc/paper_files/paper/2022/hash/82ad13ec01f9fe44c01cb91814fd7b8c-Abstract-Conference.html>.
- [23]

  Zijian Yu, Kejun Xiao, Huaipeng Zhao, Tao Luo, and Xiaoyi Zeng.
  Shopping companion: A memory-augmented LLM agent for real-world e-commerce tasks.
  *CoRR*, abs/2603.14864, 2026.
  doi: 10.48550/ARXIV.2603.14864.
  URL <https://doi.org/10.48550/arXiv.2603.14864>.
- [24]

  Peng Yuan, Yuyang Yin, Yuxuan Cai, and Zheng Wei.
  Webforge: Breaking the realism-reproducibility-scalability trilemma in browser agent benchmark.
  *arXiv preprint arXiv:2604.10988*, 2026.
- [25]

  Shuo Zhang, Boci Peng, Xinping Zhao, Boren Hu, Yun Zhu, Yanjia Zeng, and Xuming Hu.
  Llasa: Large language and e-commerce shopping assistant.
  *CoRR*, abs/2408.02006, 2024.
  doi: 10.48550/ARXIV.2408.02006.
  URL <https://doi.org/10.48550/arXiv.2408.02006>.
- [26]

  Yimeng Zhang, Jiri Gesi, Ran Xue, Tian Wang, Ziyi Wang, Yuxuan Lu, Sinong Zhan, Huimin Zeng, Qingjun Cui, Yufan Guo, et al.
  See, think, act: Online shopper behavior simulation with vlm agents.
  *arXiv preprint arXiv:2510.19245*, 2025.
- [27]

  Shuyan Zhou.
  Webarena-infinity: Generating browser environments with verifiable tasks at scale.
  *shuyanzhou.com*, March 2026.
  URL <https://webarena.dev/webarena-infinity/>.
- [28]

  Shuyan Zhou, Frank F. Xu, Hao Zhu, Xuhui Zhou, Robert Lo, Abishek Sridhar, Xianyi Cheng, Tianyue Ou, Yonatan Bisk, Daniel Fried, Uri Alon, and Graham Neubig.
  Webarena: A realistic web environment for building autonomous agents.
  In *The Twelfth International Conference on Learning Representations, ICLR 2024, Vienna, Austria, May 7-11, 2024*. OpenReview.net, 2024.
  URL <https://openreview.net/forum?id=oKn9c6ytLx>.

## Appendix A Related Work

##### Static web environments and benchmarks.

Prior work on web-agent evaluation has pursued two goals: broad coverage
of real websites and reproducible executable environments. Mind2Web
[[5](#bib.bib5)] provides large-scale offline traces from 137 real
websites across 31 domains, emphasizing breadth and cross-site
generalization. OPeRA [[19](#bib.bib19)] similarly collects observations,
personas, rationales, and actions from real human shopping sessions on
Amazon. In contrast, WebArena [[28](#bib.bib28)] provides self-hosted,
fully functional websites with executable tasks, and VisualWebArena
[[8](#bib.bib8)] extends this setting to visually grounded tasks.
Such environments support autonomous exploration and reproducible
evaluation, unlike purely offline datasets. Several benchmarks focus specifically on e-commerce. WebShop
[[22](#bib.bib22)] offers a synthetic storefront with 1.25M products.
ShoppingBench [[16](#bib.bib16)] provides a large shopping sandbox
with API-based interaction, aimed primarily at intent grounding.
ShopSimulator [[18](#bib.bib18)] introduces a Chinese web environment
for multi-turn shopping dialog and fine-grained product
differentiation. WebMall [[12](#bib.bib12)] expands to four simulated shops
with authentic product offers and comparison-shopping tasks. Although
these benchmarks enable controlled evaluation, they remain tied to a
fixed set of layouts, taxonomies, and policies, and therefore capture
only a limited slice of real-world e-commerce diversity.

Live-website evaluation. To address this limitation, Online-Mind2Web [[21](#bib.bib21)],
WebVoyager [[7](#bib.bib7)], and DeepShop [[11](#bib.bib11)] evaluate
agents directly on live websites, including real shopping domains.
These settings improve diversity and realism, but depend on external
sites whose layouts, inventories, flows, and access policies may change
without notice. This non-stationarity makes comparisons over time
difficult and limits reproducibility, especially for RL training.

Automated environment and task generation. A recent line of work uses LLMs to automate environment construction.
Gym-Anything [[1](#bib.bib1)] treats setup as a multi-agent pipeline
that installs and configures existing software, producing CUA-World with
10K+ tasks. WebArena-Infinity [[27](#bib.bib27)] generates
synthetic web apps from user manuals. WebForge [[24](#bib.bib24)] uses a
Plan/Generate/Refine/Validate pipeline to create self-contained web
environments at scale, and VeriEnv [[3](#bib.bib3)] constructs executable
synthetic versions of real websites with deterministic rewards exposed
through a Python SDK. These approaches scale well, but often sacrifice
fidelity: their environments are derived from manuals or ungrounded LLM
design choices and may miss the layouts, integrations, and edge cases of
production storefronts. In contrast, ShopArena grounds generation in
observed real shops: it first explores a live storefront to produce an
anonymised Shop Manual capturing taxonomy, navigation, capabilities, and
statistics, then synthesises a calibrated sandbox shop from that manual.
This preserves much more of the diversity of real storefronts while
retaining determinism and reset-ability. Go-Browse [[6](#bib.bib6)] proposes a multi-agent pipeline for generating
tasks and trajectories by navigating websites and maintaining a graph of
visited URLs for efficient exploration.

## Appendix B Implementation Details

### B.1 Models used for agent implementations

- •

  Planning Agent: Claude Code with Claude Opus 4.6
- •

  Specification Agent: Claude Code with Claude Opus 4.6
- •

  Collections generator: Claude Opus 4.6
- •

  Product name and description generator: Claude Sonnet 4.6
- •

  Product Image Generator: Gemini 3 Pro
- •

  Execution Agent: Claude Code with Claude Opus 4.6
- •

  Visual Verification Agent: Claude Code with Claude Opus 4.6, enabled with Playwright for browser automation

### B.2 Harness A: BrowserGym Agent

Observation. The BrowserGym harness uses the accessibility tree as the observation. We do not use screenshots for simplicity.

Action Space. The agent is allowed to use 20 actions:

- •

  noop: Do nothing, optionally waiting for the given number of milliseconds.
- •

  send\_msg\_to\_user: Send a message to the user (terminal action that ends the episode).
- •

  scroll: Scroll the page horizontally and vertically by the given pixel deltas.
- •

  fill: Type a value into an <input>, <textarea>, or [contenteditable] element.
- •

  select\_option: Select one or multiple options in a <select> element by value or label.
- •

  click: Click an element with a given mouse button and optional modifier keys.
- •

  dblclick: Double-click an element with a given mouse button and optional modifier keys.
- •

  hover: Move the mouse over an element to hover it.
- •

  press: Focus an element and press a key combination (e.g. Control+Enter, ArrowDown).
- •

  focus: Move keyboard focus to the matching element.
- •

  clear: Clear the contents of an input field.
- •

  drag\_and\_drop: Drag one element and drop it onto another.
- •

  upload\_file: Click an element to open a file chooser and upload one or more files.
- •

  go\_back: Navigate back to the previous page in browser history.
- •

  go\_forward: Navigate forward to the next page in browser history.
- •

  goto: Navigate the current tab to the given URL.
- •

  tab\_close: Close the currently active tab.
- •

  tab\_focus: Activate the tab at the given index, bringing it to the front.
- •

  new\_tab: Open a new tab and make it the active one.
- •

  report\_infeasible: Declare the task impossible with a short reason (terminal action that ends the episode).

Browser. We use a headless chromium browser for all experiments with BrowserGym, with Playwright for browser interaction.

Trajectory details. The BrowserGym agent uses a think - action - memory loop, where only the observation from the current step is used as context. The agent is instructed to reason first using <think>...</think> tags, output a single action in <action>...</action> tags, and write whatever it thinks is necessary to solve the task in <memory>...</memory> tags. The think, action and memory tags from all the steps are used as context in the future steps, along with any execution errors. The agent is allowed a maximum of 30 steps, and the episode terminates when the agent sends a message to the user using the send\_msg\_to\_user action, reports the task as infeasible using the report\_infeasible action, or the step threshold is reached. Episodes that reach the step budget are graded as failed.

### B.3 Harness B: Internal Harness

The internal harness implements a single-call-per-step planner–executor
agent that runs over a textual page projection and emits one
Playwright-grounded action per step. Each task is
evaluated across several independent browser sessions to absorb
agent and storefront stochasticity.

##### Observation.

At each step, the current page is rendered into a tree-shaped textual
projection that fuses the rendered DOM and the accessibility tree
into a single representation. Every interactive element (clickable
control, text input, combobox, menu item, etc.) is tagged with a
stable identifier of the form [elem-N] that the agent uses
to reference the element in its action. For all experiments in this
paper the agent additionally receives a viewport screenshot of the
current page at each step, so the observation is multimodal (page
projection plus rendered pixels).
The agent prompt also
includes the current URL and a running *memory*: a per-step
textual log of prior decisions, action outcomes (success / error
strings), and the agent’s own analysis. The full LLM transcript is
discarded at the end of each step — only the memory summary, the
fresh page projection, and (optionally) the latest screenshot survive
into the next prompt — so context length grows linearly in
*step count*, not in cumulative LLM output.

##### Action space.

Each step’s LLM call is constrained by a fixed structured-output
schema with the following fields:

- •

  analysis — free-form chain-of-thought over the current
  state, prior memory, and the task goal.
- •

  shouldEnd — boolean flag terminating the rollout.
- •

  instruction — a short natural-language description
  of the intended next action (e.g. “click on the filter menu titled
  *Price*”, “type *lunch box for kids* in the header search
  field”).
- •

  elementId — the elem-N target of the action,
  referencing one of the IDs in the current page projection.
- •

  method — a Playwright interaction method
  (click, fill, selectOption,
  press, check, etc.).
- •

  arguments — an optional list of method arguments
  (e.g. the value to type into a text field).

The harness translates the (elementId, method,
arguments) tuple into a Playwright call against the live
browser session. Failures (selector misses, navigation errors,
timeouts) are surfaced back to the agent as an error string in the
next step’s prompt and recorded verbatim in memory.

##### Termination and budgets.

A rollout terminates on (i) shouldEnd=true
emitted by the agent, (ii) hitting the per-task step budget of
$40$  steps, or (iii) hitting the per-task wall-clock budget of
$850$  s. Rollouts that exit via the step or time budget are scored
as failures regardless of the cart state at termination
(§[B.4](#A2.SS4)), since the agent itself did not declare
goal completion.

##### Browser.

The agent runs against a remote, Playwright-compatible browser
session provisioned per task. Each session is initialised at the
task’s starting URL (\*\_real for the live source storefront
or \*\_twin for the ShopArena sandbox), accepts a
*cart-only* terminal-state convention (every shopping task in
ShopGuru ends with the agent ending the session once the cart
contains the requested items, never by clicking a Checkout button),
and is torn down at the end of the rollout.

##### LLM client and models.

All LLM calls use an OpenAI-compatible chat-completion API with
structured-output (JSON) decoding. We evaluate three models spanning
compact and flagship capability tiers: GPT-5 mini, Gemini 3 Flash,
and GPT-5. Where the underlying model exposes it, reasoning effort is
set to medium. Each LLM call is retried up to three times
on transient API errors before the rollout is marked failed.

##### Repeats and aggregation.

We run three independent rollouts per (task, model, environment) cell.
Per-task verdicts are averaged within each cell, and the error bars
in Figs. [6](#S3.F6)b and
[7](#S4.F7)b span the per-cell standard error of
the mean across the three repeats. Per-bundle pass rates aggregate
across all tasks in the bundle (easy\_short\_horizon or
hard\_long\_horizon) and all repeats.

### B.4 LLM-as-Judge

Both harnesses score every rollout with the same LLM-as-judge model but slightly different protocols. After each rollout, the judge LLM (GPT-5) receives:

- •

  the original task intent and the task’s
  success\_criteria JSON (URL hint plus any cart/response
  constraints);
- •

  the agent’s per-step memory log (textual summary of
  decisions and action outcomes);
- •

  the agent’s URL trajectory (every URL visited, in order);
- •

  the rollout’s terminationType
  (goal\_reached, steps\_limit\_reached, or
  time\_limit\_reached).

The judge prompt instructs the model to weigh task satisfaction first,
followed by output quality, tool-use effectiveness, and recovery
from transient errors; it returns a structured JSON object with a
binary success field and a free-form reasoning
explanation. The verdict is then post-processed by a hard rule:
rollouts that did not terminate via the agent’s own
shouldEnd are forced to success=false
regardless of the judge’s opinion. This guards against a class of
spurious successes where the agent times out on a page whose final
state happens to look correct (e.g. the requested product is on the
page but was never added to cart) but never emits a deliberate
end-of-session signal.

With the BrowserGym harness, url\_contains field is treated as a hard gate, where the trajectory is graded as failed if the expected URL is not present in the trajectory. The judge LLM receives the entire cart history, the agent’s reasoning, action and memory traces, as well as the screenshots of the webpages in the trajectory and outputs a binary pass/fail decision along with it’s reasoning.

### B.5 Infrastructure Requirements

We perform all evaluations using the official APIs from the model providers. To parallelize the evaluation suite, the agent harnesses are orchestrated on a standard cloud virtual machine.

## Appendix C Limitations

ShopGym improves control, reproducibility, and scalability, but it is not a full substitute for live-web evaluation. By construction, ShopArena removes many sources of real-world non-stationarity, including inventory churn, personalization, A/B tests, third-party integrations, latency variation, and other operational noise. This is desirable for controlled benchmarking, but it also means that strong performance in ShopGym should be interpreted as evidence of capability under stabilized conditions, not as a guarantee of robustness on live storefronts. More broadly, the generated shops are behaviorally aligned approximations rather than exact reconstructions, so some fine-grained brand-specific, visual, or platform-specific cues are intentionally not preserved.

Our validation metrics are proxies for realism: the structural analysis uses accessibility-tree depth, interaction counts, and transition-graph statistics, which capture meaningful aspects of interface and navigation complexity, but do not fully measure semantic ambiguity, visual fidelity, content quality, or all sources of user-facing behavioral variation. Likewise, the behavioral validation shows that model performance on twin shops positively tracks performance on live storefronts, but correlation in aggregate success rate does not imply that the same latent capabilities or failure modes are being exercised in exactly the same way.

Finally, the current task suite covers only part of the e-commerce agent problem. ShopGuru focuses on product discovery, browsing, filtering, information seeking, and multi-step in-store shopping journeys. It does not yet cover several important settings, including login-protected flows, checkout and payment, recommendation modules and sponsored content, customer-service interactions, cross-store comparison, post-purchase workflows, multi-session memory, multilingual settings, or safety- and policy-critical edge cases. Extending the framework to these settings is an important direction for future work.

## Appendix D Broader Impact and Safeguards

ShopGym is intended to improve the reproducibility, controllability, and inspectability of e-commerce web-agent evaluation. By converting live storefronts into sandboxed evaluation environments, the framework reduces reliance on non-stationary live websites and enables more reliable comparison across agents.

Potential positive impact. ShopGym is a framework for constructing e-commerce simulation environments and grounded benchmark tasks. The simulation layer, ShopArena, provides a framework for creating diverse, stable and realistic simulation environments from live storefronts. Beyond evaluations, the environments can be used for any agent simulations, such as training of e-commerce agents using Reinforcement Learning.

Potential negative impact. We nevertheless identify several potential negative broader impacts. First, progress on web-agent evaluation may indirectly contribute to stronger agents that could be misused for unauthorized browsing automation, large-scale scraping, spammy shopping behavior, inventory manipulation, or deceptive commercial activity. Second, because the pipeline uses live storefronts during the exploration phase, careless use could raise privacy, copyright, fair-use, or terms-of-service concerns if raw source-store content, identifiable commercial information, or original assets were copied or redistributed. Third, generated benchmarks may not be representative of all e-commerce websites, merchant categories, languages, geographic regions, accessibility patterns, or user populations. Claims about benchmark diversity should therefore be interpreted relative to the seed storefronts and task families used to instantiate a particular ShopGym benchmark.

Mitigations. We mitigate these risks through several safeguards. ShopGym is designed as a sandboxed research environment rather than a tool for acting on live commercial websites. Generated shops are self-contained, locally hostable, resettable, and inspectable. Login is disabled and checkout is mocked, so the benchmark does not support real purchases, account access, or interaction with real customers. During exploration, the pipeline extracts public, user-facing structural information such as navigation affordances, catalog statistics, page organization, and policy-page structure. Downstream generation uses anonymized specifications and does not preserve brand names, product names, named individuals, contact details, or absolute URLs. Released benchmark artifacts use synthetic brand identities, products, descriptions, and imagery rather than direct copies of source-store assets.

We will document the intended use, limitations, task schema, environment setup, dependency versions, and licenses of released artifacts. We do not release raw source-store data or original commercial assets. Users who instantiate ShopGym on additional storefronts should respect applicable website terms, robots policies where relevant, copyright restrictions, and regional legal requirements. These safeguards are intended to support responsible research use while reducing the risk that the framework is used for unauthorized live-web automation or redistribution of commercial content.

## Appendix E ShopArena Generation Artifact Example

This appendix demonstrates the sandbox shops generated by the ShopArena shop generation pipeline. These sandbox shops are built from exploration artifacts generated from ShopArena exploration tasks.

![Refer to caption](images/30_ShopGym/mock_clothing_home.png)


(a) Mock Clothing

![Refer to caption](images/30_ShopGym/mock_hardware_home.png)


(b) Mock Hardware

![Refer to caption](images/30_ShopGym/mock_cookware_home.png)


(c) Mock Cookware

Figure 8: Screenshots of Sandbox Shop Homepages

Figure [9](#A5.F9) shows more detailed interaction surfaces within the generated sandbox shops. Built from specifications, the examples include a collection page with faceted filters, a homepage with a promotional popup, and a product detail page with search suggestions and purchasing controls. These screenshots highlight that the generated shops contain not only realistic visual layouts, but also functional e-commerce elements that support browsing, filtering, promotion handling, search, and product-level decision making.

![Refer to caption](images/30_ShopGym/mock_clothing_collection.png)


(a) Collection page with filters

![Refer to caption](images/30_ShopGym/mock_hardware_popup.png)


(b) Homepage with promotion popup

![Refer to caption](images/30_ShopGym/mock_cookware_pdp.png)


(c) Product detail page

Figure 9: Screenshots of Sandbox Shop Details

Live versions of the sandbox shops can be accessed at:

- •

  Mock Clothing: <https://shop-arena-96c172e4-kqqx5567kq-uc.a.run.app/>
- •

  Mock Hardware: <https://shop-arena-53473e65-kqqx5567kq-uc.a.run.app/>
- •

  Mock Cookware: <https://shop-arena-7e92090d-kqqx5567kq-uc.a.run.app/>

## Appendix F ShopArena Exploration Artifact Example

This appendix reproduces the three top-level outputs that
shop\_arena.explore writes for a single live storefront
exploration run. The example was produced from a premium hybrid
cookware storefront; all store, brand, designer, product, and URL
strings were anonymized at write time per the explorer’s
constitution, so only structural and behavioral facts remain.

### F.1 Shop Manual (manual.md)

The manual instructs the generation pipeline to implement the cookware shop by dividing it into 7 features: Site Shell, Homepage, Collections & Navigation, Cart, Search, Floating UX, Policy & info pages.

[⬇](data:text/plain;base64,IyBTaG9wIE1hbnVhbCAtLSBQcmVtaXVtIEh5YnJpZCBDb29rd2FyZSBhbmQgS2l0Y2hlbiBBY2Nlc3NvcmllcyBTaG9wCgojIyBPdmVydmlldwoKVGhpcyBpcyBhIHByZW1pdW0gaHlicmlkIGNvb2t3YXJlIGFuZCBraXRjaGVuIGFjY2Vzc29yaWVzIHN0b3JlZnJvbnQgcHJpY2VkIGluIFVTRC4gVGhlIGJyYW5kIHZvaWNlIGlzIGJvbGQsIGNoZWYtZW5kb3JzZWQsIGFuZCBkaXJlY3QtdG8tY29uc3VtZXIsIGxlYW5pbmcgb24gY3VsaW5hcnktcHJvZmVzc2lvbmFsIGNyZWRpYmlsaXR5IGFuZCBhICJidXkgb25jZSIgZHVyYWJpbGl0eSBuYXJyYXRpdmUuIEFnZ3JlZ2F0ZSByZXZpZXcgY291bnRzIGluIHRoZSA1MCwwMDArIHJhbmdlIGFuZCBhIHN0YXRlZCBsaWZldGltZSB3YXJyYW50eSBzaWduYWwgYSBzaXplYWJsZSwgZXN0YWJsaXNoZWQgY2F0YWxvZyByYXRoZXIgdGhhbiBhIG5pY2hlIGJvdXRpcXVlLgoKIyMgU2l0ZSBzaGVsbAoKQSBwZXJzaXN0ZW50IGRpc21pc3NpYmxlIGFubm91bmNlbWVudCBiYXIgc2l0cyBhYm92ZSBhIHR3by1yb3cgc3RpY2t5IGhlYWRlci4gUm93IDEgaXMgYSB1dGlsaXR5IGJhcjogYSBsZWZ0IGNsdXN0ZXIgb2YgdGhyZWUgZWRpdG9yaWFsIHRleHQgbGlua3MgcGx1cyBhICJQYXJ0bmVycyIgZHJvcGRvd24gYnV0dG9uIGxpc3RpbmcgMi0zIG5hbWVkIGNvbGxhYm9yYXRvciBwYWdlcywgYSBjZW50ZXJlZCBsb2dvLCBhbmQgYSByaWdodCBjbHVzdGVyIG9mIHNlYXJjaCwgYWNjb3VudCwgYW5kIGNhcnQgaWNvbiBidXR0b25zLiBSb3cgMiBpcyB0aGUgcHJpbWFyeSBjYXRlZ29yeSBuYXZpZ2F0aW9uIC0tIGVpZ2h0IHRvcC1sZXZlbCBlbnRyaWVzIHJlbmRlcmVkIGFzIGlubGluZSBidXR0b25zLiBNb3N0IGVudHJpZXMgb3BlbiBmbHlvdXQgcGFuZWxzIHJhdGhlciB0aGFuIGEgc2luZ2xlIG1lZ2EgbWVudSwgc28gbmF2aWdhdGlvbiBkZXB0aCB0b3BzIG91dCBhdCB0d28gbGV2ZWxzICh0b3AtbGV2ZWwgLT4gc3ViLWxpbmspLiBFYWNoIGZseW91dCBpcyBhIGZ1bGwtd2lkdGggdHdvLWNvbHVtbiBwYW5lbDogYSB2ZXJ0aWNhbCBzdWItbGluayBsaXN0IGVuZGluZyBpbiAiU2hvcCBBbGwgW0NhdGVnb3J5XSIgb24gdGhlIGxlZnQsIHBsdXMgMi0zIGZlYXR1cmVkIHByb2R1Y3QgY2FyZHMgb24gdGhlIHJpZ2h0IChpbWFnZSwgbmFtZSwgcHJpY2Ugd2l0aCBvcHRpb25hbCBjb21wYXJlLWF0LCBzYXZpbmdzIGJhZGdlLCBhbmQgc3RhciByYXRpbmcpLiBPbmUgdG9wLWxldmVsIGVudHJ5IGJlaGF2ZXMgYXMgYSBkaXJlY3QgbGluayBpbnN0ZWFkIG9mIG9wZW5pbmcgYSBmbHlvdXQuCgpBIG1vYmlsZSBvZmYtY2FudmFzIGRyYXdlciBtaXJyb3JzIHRoZSBzYW1lIHRheG9ub215IGFzIGFjY29yZGlvbnMsIHdpdGggZXh0cmEgZGlyZWN0IGxpbmtzIGZvciBzYWxlLCBnaWZ0IGNhcmRzLCAiU2hvcCBBbGwiLCBhbmQgdGhlIFBhcnRuZXJzIGdyb3VwLgoKVGhlIGZvb3RlciBvY2N1cGllcyBhIGBjb250ZW50aW5mb2AgbGFuZG1hcmsgb24gZXZlcnkgcGFnZSBhbmQgaXMgc3BsaXQgaW50byBhIHRvcCBiYW5kIGFuZCBhIGJvdHRvbSBiYW5kLiBUaGUgdG9wIGJhbmQgaGFzIHRocmVlIG5hbWVkIGxpbmsgZ3JvdXBzIChTaG9wLCBIZWxwLCBNZWRpYSkgcGx1cyBhIGZvdXJ0aCBjb2x1bW4gb2YgZm91ciBzb2NpYWwgaWNvbiBsaW5rcyBvcGVuaW5nIGluIG5ldyB0YWJzLiBUaGUgYm90dG9tIGJhbmQgaXMgYSBmbGV4IHJvdyBwYWlyaW5nIGEgY29weXJpZ2h0IGxpbmUgd2l0aCB0d28gbGVnYWwgbGlua3MgKHRlcm1zIG9mIHNlcnZpY2UsIGFjY2Vzc2liaWxpdHkgY29tbWl0bWVudCkgYWdhaW5zdCBhIGJyYW5kIHdvcmRtYXJrIGltYWdlLiBUaGUgZm9vdGVyIGNhcnJpZXMgbm8gaW5saW5lIG5ld3NsZXR0ZXIgZm9ybSwgbm8gcGF5bWVudCBpY29ucywgYW5kIG5vIGxvY2FsZSBvciBjdXJyZW5jeSBzd2l0Y2hlci4KCiMjIEhvbWVwYWdlCgpUaGUgaG9tZXBhZ2UgaXMgYSBsb25nLCBtb2R1bGFyIGNvbXBvc2l0aW9uIG9mIHNpeHRlZW4gc2VjdGlvbnMgaW4gdGhpcyBvcmRlcjoKCi0gRnVsbC13aWR0aCBoZXJvIHdpdGggYXV0b3BsYXkgbXV0ZWQgbG9vcGluZyBiYWNrZ3JvdW5kIHZpZGVvIGFuZCBhIGNlbnRlcmVkIGhlYWRsaW5lICsgc2luZ2xlIENUQSBvdmVybGF5LgotICJTaG9wIGJ5IENhdGVnb3J5IiBjaGlwIHNsaWRlciAtLSBhIGhvcml6b250YWxseSBzY3JvbGxpbmcgcm93IG9mIHNldmVuIGltYWdlLWJhY2tlZCBzdWItY29sbGVjdGlvbiBjaGlwcyB3aXRoIHByZXYvbmV4dCBhcnJvd3MgYW5kIGEgIlNob3AgQWxsIiBsaW5rLgotIEZlYXR1cmVkIHNldHMgcHJvbW8gYmxvY2sgLS0gdGV4dC1sZWZ0IC8gcHJvZHVjdC1jYXJkcy1yaWdodCwgd2l0aCBhIDMtY2FyZCByb3cgc2hvd2luZyBpbWFnZSwgc2F2aW5ncyBiYWRnZSwgbmFtZSwgY3VycmVudCBwcmljZSwgYW5kIG9yaWdpbmFsIHByaWNlLgotIFNwZWNpYWx0eSBwcm9kdWN0IGJhbm5lciAtLSBhIHJldmVyc2VkIHR3by1jb2x1bW4gYmxvY2sgcGFpcmluZyB0d28gcHJvZHVjdCBjYXJkcyBvbiB0aGUgbGVmdCB3aXRoIGRlc2NyaXB0aXZlIGNvcHkgb24gdGhlIHJpZ2h0IGludHJvZHVjaW5nIGEgbGltaXRlZC10aW1lIHN1Yi1saW5lLgotIENoZWYgZW5kb3JzZW1lbnQgYmxvY2sgLS0gYXV0b3BsYXkgdmlkZW8gdGh1bWJuYWlsIHdpdGggYSBwbGF5IG92ZXJsYXkgb3BlbmluZyBmdWxsc2NyZWVuIHBsYXliYWNrLCBwYWlyZWQgd2l0aCBhbiBhdHRyaWJ1dGVkIGJsb2NrcXVvdGUgYW5kIGEgc3RhciArIGFnZ3JlZ2F0ZS1yZXZpZXctY291bnQgc29jaWFsLXByb29mIGxpbmUuCi0gMngyIGZlYXR1cmUgY2FyZCBncmlkIC0tIGZvdXIgY2FyZHMgY292ZXJpbmcgaGlnaC1oZWF0IGNhcGFiaWxpdHksIFBGQVMtZnJlZSBub25zdGljaywgZGlzaHdhc2hlciBzYWZldHksIGFuZCBkdXJhYmlsaXR5L3dhcnJhbnR5LCBlYWNoIHdpdGggYSBzbWFsbCBhdHRyaWJ1dGUgYmFkZ2UsIGFuIGFsbC1jYXBzIGhlYWRsaW5lLCBhbmQgYSBvbmUtIHRvIHR3by1zZW50ZW5jZSBkZXNjcmlwdG9yLgotIFJldmlld3MgYmFubmVyIC0tIGFnZ3JlZ2F0ZSByYXRpbmcgKyByb3RhdGluZyBjdXN0b21lciBxdW90ZSBvbiBvbmUgc2lkZSwgYSB0aHJlZS1pY29uIHRydXN0IHN0cmlwIChsaWZldGltZSB3YXJyYW50eSwgZnJlZSBzaGlwcGluZywgMzAtZGF5IHJldHVybnMpIG9uIHRoZSBvdGhlci4KLSAiQmVzdCBTZWxsZXJzIiBob3Jpem9udGFsIHByb2R1Y3QgY2Fyb3VzZWwgd2l0aCBwcmV2L25leHQgYXJyb3dzIGFuZCBhICJTaG9wIEFsbCIgbGluay4KLSBLbmlmZSBjYXRlZ29yeSBoZXJvIHdpdGggdHdvIHByb2R1Y3QgY2FyZHMgb24gdGhlIGxlZnQgYW5kIGEgY2F0ZWdvcnkgdmFsdWUtcHJvcCArIGN1c3RvbWVyIHF1b3RlIGNoaXAgb24gdGhlIHJpZ2h0LgotIFVHQyB2aWRlbyBjYXJvdXNlbCAtLSBzaXggdmlkZW8gdGh1bWJuYWlsIHRpbGVzIHdpdGggcGxheSBvdmVybGF5czsgdGlsZXMgb3BlbiBhIGZ1bGxzY3JlZW4gcG9wdXAgcGxheWVyLgotIDMtdXAgc3BlY2lhbHR5IGNhdGVnb3J5IGJhbm5lcnMgLS0gdGhyZWUgZXF1YWwtd2lkdGggY2FyZHMgZWFjaCBjb21iaW5pbmcgYSBwcm9kdWN0IGltYWdlLCBoZWFkbGluZSwgZGVzY3JpcHRvciwgQ1RBIGxpbmssIGFuZCBhIGN1c3RvbWVyIHF1b3RlIGNoaXAgd2l0aCBzdGFyIHJhdGluZy4KLSBDdWxpbmFyeSBjb3VuY2lsIHNlY3Rpb24gaW50cm9kdWNpbmcgdGhlIGJyYW5kJ3MgY2hlZiBhZHZpc29yeSBncm91cCB3aXRoIGZpdmUgcHJvZmVzc2lvbmFsIG5hbWVzIChyb2xlcyBvbmx5KSBhbmQgYSBDVEEgdG8gYSBkZWRpY2F0ZWQgcGFnZS4KLSAiUmVjaXBlcyIgY2Fyb3VzZWwgb2YgcmVjaXBlIGNhcmRzIHdpdGggaW1hZ2UsIHRpdGxlLCB5aWVsZCwgYW5kIHRpbWUsIGxpbmtpbmcgaW50byB0aGUgcmVjaXBlcyBibG9nLgotICJBcnRpY2xlcyIgY2Fyb3VzZWwgb2YgZWRpdG9yaWFsIGJsb2cgY2FyZHMgdXNpbmcgdGhlIHNhbWUgY2FyZCBjaHJvbWUgbWludXMgdGhlIHJlY2lwZSBtZXRhZGF0YS4KLSBGb3VuZGVyIG1lc3NhZ2UgLS0gYSBzaG9ydCB0d28tcGFyYWdyYXBoIGZpcnN0LXBlcnNvbiBub3RlIHNpZ25lZCB3aXRoIGEgcGxhaW4tdGV4dCBuYW1lLgotIElubGluZSBuZXdzbGV0dGVyIHNlY3Rpb24gYXQgdGhlIHBhZ2UgYm90dG9tIHdpdGggYW4gZW1haWwgaW5wdXQsIGhpZGRlbiBob25leXBvdCwgYW5kICJTdWJzY3JpYmUiIGJ1dHRvbi4KClRoZXJlIGlzIG5vIGhvbWVwYWdlIG1vZGFsIHBvcHVwLiBBIHNlcGFyYXRlIEtsYXZpeW8tZHJpdmVuIHBvcHVwIGlzIGNvbmZpZ3VyZWQgYnV0IGRpZCBub3QgZmlyZSBkdXJpbmcgZXhwbG9yYXRpb24uCgojIyBDb2xsZWN0aW9ucyAmIG5hdmlnYXRpb24KCkNvbGxlY3Rpb24gcGFnZXMgcmVuZGVyIGFzIGEgdGhyZWUtY29sdW1uIGdyaWQgb24gZGVza3RvcC4gRWFjaCBjYXJkIHNob3dzIGEgcHJvZHVjdCBpbWFnZSwgYW4gb3B0aW9uYWwgcHJvbW90aW9uYWwgb3ZlcmxheSBiYWRnZSAoIlNBTEUiLCAiTmV3IiwgIkJlc3RzZWxsZXIiKSwgcHJvZHVjdCB0aXRsZSwgc3RhciByYXRpbmcgd2l0aCByZXZpZXcgY291bnQsIGFuZCBwcmljZSAoc3RyaWtldGhyb3VnaCBvcmlnaW5hbCBwcmljZSBwbHVzIGEgcGVyY2VudGFnZS1vZmYgYmFkZ2Ugd2hlbiBkaXNjb3VudGVkKS4gVGhlIGNvbGxlY3Rpb24gdGl0bGUgZGlzcGxheXMgYSBsaXZlIHByb2R1Y3QgY291bnQgaW4gcGFyZW50aGVzZXMuCgpBYm92ZSB0aGUgZ3JpZCBzaXRzIGEgaG9yaXpvbnRhbCBmaWx0ZXIgYmFyIHdpdGggdHdvIGNvbGxhcHNpYmxlIGNvbnRyb2xzLiBUaGUgIkZpbHRlciIgcGFuZWwgZXhwb3NlcyB0d28gY2hlY2tib3ggZmFjZXRzIC0tICJBdmFpbGFibGUiIGFuZCAiT24gU2FsZSIgLS0gdGhhdCB1cGRhdGUgVVJMIHBhcmFtZXRlcnMgaW1tZWRpYXRlbHksIHJlbmRlciBzZXJ2ZXItc2lkZSwgYW5kIGNvbWJpbmUgY2xlYW5seS4gVGhlICJTb3J0IGJ5IiBkcm9wZG93biBvZmZlcnMgZWlnaHQgb3B0aW9uczogZmVhdHVyZWQsIGJlc3Qgc2VsbGluZywgYWxwaGFiZXRpY2FsbHkgQS1aLCBhbHBoYWJldGljYWxseSBaLUEsIHByaWNlIGFzY2VuZGluZywgcHJpY2UgZGVzY2VuZGluZywgZGF0ZSBuZXctdG8tb2xkLCBhbmQgZGF0ZSBvbGQtdG8tbmV3LiBTb3J0aW5nIHVwZGF0ZXMgdGhlIGBzb3J0X2J5YCBVUkwgcGFyYW1ldGVyIHdpdGhvdXQgYSBmdWxsIHJlbG9hZC4KClBhZ2luYXRpb24gdXNlcyBhICJMb2FkIG1vcmUiIGJ1dHRvbi4gVGhlIGluaXRpYWwgcmVuZGVyIHNob3dzIDI0IGNhcmRzOyBjbGlja2luZyB0aGUgYnV0dG9uIGFwcGVuZHMgdGhlIHJlc3Qgb2YgdGhlIGNvbGxlY3Rpb24gaW4gYSBzaW5nbGUgYmF0Y2ggYW5kIHRoZSBidXR0b24gdGhlbiBkaXNhcHBlYXJzLiBUaGVyZSBpcyBubyBpbmZpbml0ZSBzY3JvbGwsIG5vIG51bWJlcmVkIHBhZ2luYXRpb24sIGFuZCBubyBgcGFnZT1gIFVSTCBwYXJhbWV0ZXIuCgojIyBQcm9kdWN0IHBhZ2UKClRoZSBwcm9kdWN0IHBhZ2UgbGVhZHMgd2l0aCBhIGhvcml6b250YWwgaW1hZ2UgY2Fyb3VzZWwgdGhhdCBoYXMgcHJldi9uZXh0IGFycm93IGNvbnRyb2xzIGFuZCBhbiBvcHRpb25hbCBsZWZ0LXNpZGUgdGh1bWJuYWlsIHN0cmlwIGZvciBkaXJlY3Qgc2xpZGUgc2VsZWN0aW9uLiBCZWxvdyB0aGUgdGl0bGUgc2l0cyB0aGUgcHJpY2UgYmxvY2s6IHByb21pbmVudCBjdXJyZW50IHByaWNlLCBvcHRpb25hbCBzdHJpa2V0aHJvdWdoIG9yaWdpbmFsIHByaWNlLCBvcHRpb25hbCBwZXJjZW50YWdlIHNhdmluZ3MgYmFkZ2UsIGFuZCBhIGJ1eS1ub3ctcGF5LWxhdGVyIGZpbmFuY2luZyBsaW5lIHRoYXQgb3BlbnMgYSBtb2RhbC4gQSB0cnVzdCBiYWRnZSByb3cgYmVuZWF0aCB0aGUgcHJpY2Ugc3VtbWFyaXplcyBmcmVlIHNoaXBwaW5nLCBhIDMwLWRheSByZXR1cm4gZ3VhcmFudGVlLCBhbmQgKHdoZXJlIGFwcGxpY2FibGUpIGEgbGlmZXRpbWUgd2FycmFudHksIHBsdXMgYW4gZXhwYW5kYWJsZSBjbGFpbSBidXR0b24gbGlzdGluZyBjaGVtaWNhbC1zYWZldHkgYXR0cmlidXRlcyBmb3Igbm9uc3RpY2sgaXRlbXMuCgpWYXJpYW50IHNlbGVjdG9ycyByZW5kZXIgYXMgcmFkaW8gYnV0dG9ucyBpbiBhIHNpbmdsZSBob3Jpem9udGFsIHJvdy4gQXBwYXJlbCBleHBvc2VzIGEgc2l6ZSBheGlzIChYUy1YWEwpIHdpdGggYSAiU2l6ZSBHdWlkZSIgbGluayBhYm92ZSB0aGUgZ3JvdXAuIFNpbmdsZS12YXJpYW50IHByb2R1Y3RzIHNraXAgdGhlIHNlbGVjdG9yIGVudGlyZWx5LiBBIHF1YW50aXR5IHN0ZXBwZXIgKGRlY3JlbWVudCwgbnVtZXJpYyBkaXNwbGF5LCBpbmNyZW1lbnQpIHNpdHMgaW1tZWRpYXRlbHkgYWRqYWNlbnQgdG8gdGhlICJBZGQgdG8gQ2FydCIgQ1RBLgoKRGVzY3JpcHRpb25zIHZhcnkgYnkgY2F0ZWdvcnkuIFNpbXBsZXIgcHJvZHVjdHMgcmVuZGVyIGFuIGlubGluZSBwcm9zZSBwYXJhZ3JhcGggcGx1cyBhIGJ1bGxldGVkIGZlYXR1cmUgbGlzdC4gQ29tcGxleCBwcm9kdWN0cyB1c2UgYW4gYWNjb3JkaW9uLXRhYiBsYXlvdXQgKGUuZy4gIkRlc2NyaXB0aW9uIiArICJIeWJyaWQgVGVjaG5vbG9neSIgdGFicykgZm9sbG93ZWQgYnkgYSBob3Jpem9udGFsIHNldmVuLWljb24gYXR0cmlidXRlIHN0cmlwICh3YXJyYW50eSwgdXRlbnNpbCBzYWZldHksIG5vbnN0aWNrLCBvdmVuLXNhZmUsIGRpc2h3YXNoZXItc2FmZSwgaW5kdWN0aW9uLXJlYWR5LCBzdGF5LWNvb2wgaGFuZGxlKS4gU29tZSBQRFBzIGluY2x1ZGUgYSAiR2lmdCBXaXRoIFB1cmNoYXNlIiBjYWxsb3V0IGFib3ZlIHRoZSBxdWFudGl0eSBzdGVwcGVyIHNob3dpbmcgYSBidW5kbGVkIGZyZWUgaXRlbS4KClJldmlld3MgdXNlIGFuIE9rZW5kby1zdHlsZSB3aWRnZXQuIFByb2R1Y3RzIHdpdGhvdXQgcmV2aWV3cyBzaG93IGEgIkJlIHRoZSBmaXJzdCB0byBsZWF2ZSBhIHJldmlldyIgcHJvbXB0IGFuZCBhICJXcml0ZSBhIHJldmlldyIgQ1RBLiBQcm9kdWN0cyB3aXRoIHJldmlld3Mgc2hvdyBhbiBhZ2dyZWdhdGUgc2NvcmUsIGEgY2xpY2thYmxlIHN0YXItZGlzdHJpYnV0aW9uIGJyZWFrZG93biwgYW4gYXV0by1nZW5lcmF0ZWQgQUkgc3VtbWFyeSBibG9jaywgc2VhcmNoIGFuZCBzb3J0L2ZpbHRlciBkcm9wZG93bnMgKGxhdGVzdCwgb2xkZXN0LCBoaWdoZXN0LCBsb3dlc3QsIG1vc3QgaGVscGZ1bDsgcmF0aW5nIDEtNSBvciBhbGwpLCBhbmQgaW5kaXZpZHVhbCByZXZpZXcgY2FyZHMgd2l0aCByZXZpZXdlciBuYW1lLCBzdGFyIHJhdGluZywgcmVsYXRpdmUgZGF0ZSwgaGVhZGxpbmUsIGJvZHksIGFuZCBoZWxwZnVsLXZvdGUgYnV0dG9ucy4KClJlY29tbWVuZGF0aW9uIHJhaWxzIGRpZmZlciBieSB0ZW1wbGF0ZS4gU29tZSBQRFBzIHJlbmRlciBhICJDdXN0b21lcnMgYWxzbyBsb3ZlIiByYWlsIG9mIHByb2R1Y3QgY2FyZHMgd2l0aCBxdWljay1hZGQgYnV0dG9ucyBhbmQgaW5saW5lIGNvbG9yLXN3YXRjaCBzZWxlY3RvcnMuIE90aGVycyByZW5kZXIgdHdvIHN0YWNrZWQgcmFpbHMgLS0gYSAiRnJlcXVlbnRseSBCb3VnaHQgVG9nZXRoZXIiIHRyaW8gd2l0aCBpbmxpbmUgIkFkZCB0byBDYXJ0IiBidXR0b25zLCBhbmQgYSAiUmVjZW50bHkgVmlld2VkIiBjYXJvdXNlbCB3aXRoIHByZXYvbmV4dCBhcnJvd3MuIE5vIGN1c3RvbWl6YXRpb24gb3IgcGVyc29uYWxpemF0aW9uIGZpZWxkcyAoZW5ncmF2aW5nLCBtb25vZ3JhbSwgZ2lmdCBub3RlKSBhcmUgZXhwb3NlZCBvbiB0aGUgUERQLgoKIyMgQ2FydAoKVGhlIGNhcnQgb3BlbnMgYXMgYSByaWdodC1zaWRlIHNsaWRlLW91dCBkcmF3ZXIgKEFSSUEgYGRpYWxvZ2AgbGFiZWxlZCAiWW91ciBDYXJ0IikgdHJpZ2dlcmVkIGJ5IHRoZSBoZWFkZXIgY2FydCBpY29uLiBUaGUgaWNvbiBzaG93cyBhIG51bWVyaWMgaXRlbS1jb3VudCBiYWRnZSBvbmNlIHRoZSBjYXJ0IGhhcyBhbnkgaXRlbXMuCgpFbXB0eSBzdGF0ZSBzaG93cyB0aGUgIllvdXIgQ2FydCIgaGVhZGluZyB3aXRoIGEgYDBgIGJhZGdlLCBhIHNob3J0IGVtcHR5LWNhcnQgc2VudGVuY2UsIGEgQ1RBIGxpbmsgaW50byBhIGJlc3Qtc2VsbGVycyBjb2xsZWN0aW9uLCBhIGAkMC4wMGAgc3VidG90YWwgbGluZSwgYW5kIHRoZSBzYW1lIHRydXN0LWJhZGdlIHRyaW8gKGxpZmV0aW1lIHdhcnJhbnR5LCBmcmVlIHNoaXBwaW5nLCAzMC1kYXkgcmV0dXJucykgcmVwZWF0ZWQgbmVhciB0aGUgZm9vdGVyLgoKRmlsbGVkIHN0YXRlIHJlcGxhY2VzIHRoZSBlbXB0eSBjb3B5IHdpdGggYSBmcmVlLXNoaXBwaW5nIHF1YWxpZmllciBiYW5uZXIgb25jZSB0aGUgdGhyZXNob2xkIGlzIG1ldC4gRWFjaCBsaW5lIGl0ZW0gc2hvd3MgYSB0aHVtYm5haWwsIG5hbWUgKGJvdGggbGlua2VkIHRvIHRoZSBQRFApLCB0aGUgcHJpY2UgYmxvY2sgKGN1cnJlbnQgcHJpY2UgcGx1cyBzdHJpa2V0aHJvdWdoIGNvbXBhcmUtYXQgd2hlbiBkaXNjb3VudGVkKSwgYSAiUmVtb3ZlIEl0ZW0iIGFmZm9yZGFuY2UsIGFuZCBhIHRocmVlLWJ1dHRvbiBxdWFudGl0eSBzdGVwcGVyLiBRdWFudGl0eSBjaGFuZ2VzIGFwcGx5IHZpYSBBamF4IGFuZCBpbW1lZGlhdGVseSByZWNvbXB1dGUgdGhyZWUgc3VtbWFyeSByb3dzOiBwcm9kdWN0cyBhdCBsaXN0IHByaWNlLCB0b3RhbCBzYXZpbmdzLCBhbmQgc3VidG90YWwuIEEgZnVsbC13aWR0aCAiQ2hlY2tvdXQiIGJ1dHRvbiBzaXRzIGJlbG93LCB3aXRoIGEgZm9vdG5vdGUgYXN0ZXJpc2sgZm9yIGZyZWUtc2hpcHBpbmcgZWxpZ2liaWxpdHkgYW5kIHRoZSB0cnVzdCBiYWRnZXMgcmVwZWF0ZWQuCgpUaGUgZHJhd2VyIGNhcnJpZXMgYSAiRnJlcXVlbnRseSBCb3VnaHQgVG9nZXRoZXIiIHVwc2VsbCByYWlsICh0aHJlZSBwcm9kdWN0IGNhcmRzIHdpdGggaW5saW5lICJBZGQgdG8gQ2FydCIpIGluIGJvdGggc3RhdGVzOyBjYXJ0ZWQgaXRlbXMgYXJlIHN3YXBwZWQgb3V0IG9mIHRoZSByYWlsIGZvciBmcmVzaCBzdWdnZXN0aW9ucy4gQSAiUmVjZW50bHkgVmlld2VkIiByYWlsIHdpdGggcHJldi9uZXh0IGFycm93cyBhcHBlYXJzIGJlbmVhdGguIFRoZXJlIGlzIG5vIGlubGluZSBwcm9tby1jb2RlIGZpZWxkIC0tIGRpc2NvdW50IGNvZGVzIGFyZSBjb2xsZWN0ZWQgb24gdGhlIG5hdGl2ZSBjaGVja291dCAtLSBhbmQgdGhlcmUgaXMgbm8gaW5saW5lIHNoaXBwaW5nIGVzdGltYXRlIGNhbGN1bGF0b3I7IGZyZWUtc2hpcHBpbmcgZWxpZ2liaWxpdHkgaXMgY29udmV5ZWQgb25seSB2aWEgdGhlIHF1YWxpZmllciBiYW5uZXIgYW5kIGZvb3Rub3RlLgoKIyMgU2VhcmNoCgpTZWFyY2ggaXMgdHJpZ2dlcmVkIGJ5IGEgbWFnbmlmeWluZy1nbGFzcyBpY29uIGJ1dHRvbiBpbiB0aGUgaGVhZGVyIHV0aWxpdHkgcm93LiBDbGlja2luZyBpdCBleHBhbmRzIGFuIGlubGluZSBkcm9wZG93biBkaXJlY3RseSBiZWxvdyB0aGUgaWNvbiAtLSB0aGUgcGFnZSBpcyBub3QgZGltbWVkIGFuZCBuYXZpZ2F0aW9uIHJlbWFpbnMgdmlzaWJsZS4KClByZWRpY3RpdmUgc2VhcmNoIHJlbmRlcnMgYSBzdGF0aWMgIlN1Z2dlc3RlZCIgcGFuZWwgaW5zaWRlIHRoZSBkcm9wZG93bjogdHlwaWNhbGx5IGZvdXIgbGlua3MgY29tYmluaW5nIG9uZSBjb2xsZWN0aW9uIHNob3J0Y3V0IGFuZCB0aHJlZSBwcmUtc2V0IHNlYXJjaC1xdWVyeSBsaW5rcy4gVGhlIGxpc3QgaXMgZml4ZWQgYW5kIGRvZXMgbm90IGNoYW5nZSB3aXRoIGtleXN0cm9rZXMuIFRoZSBkcm9wZG93biBpdHNlbGYgZG9lcyBub3QgcmVuZGVyIHByb2R1Y3QgdGh1bWJuYWlscywgcHJpY2VzLCBvciBwcm9kdWN0IGNhcmRzIC0tIG9ubHkgc3VnZ2VzdGVkIHF1ZXJpZXMgYW5kIGNvbGxlY3Rpb24gc2hvcnRjdXRzLgoKQSBgL3NlYXJjaC9zdWdnZXN0Lmpzb25gIHByZWRpY3RpdmUgZW5kcG9pbnQgaXMgYWN0aXZlIGluIHRoZSBiYWNrZ3JvdW5kIGFuZCByZXR1cm5zIHByb2R1Y3Qtc2hhcGVkIEpTT04gKHRpdGxlLCBoYW5kbGUsIHByaWNlLCBjb21wYXJlLWF0IHJhbmdlLCBhdmFpbGFiaWxpdHksIFVSTCwgdmVuZG9yLCBmZWF0dXJlZCBpbWFnZSwgdGFncywgdHlwZSkgYnV0IGl0cyByZXN1bHRzIGFyZSBub3Qgc3VyZmFjZWQgaW4gdGhlIGhlYWRlciBkcm9wZG93bi4gU3VibWl0dGluZyB0aGUgZm9ybSBuYXZpZ2F0ZXMgdG8gYSBmdWxsLXBhZ2UgYC9zZWFyY2g/cT08cXVlcnk+YCByZXN1bHRzIGxpc3RpbmcuIEEgc2Vjb25kIHNlYXJjaCBpbnB1dCBhcHBlYXJzIGluIHRoZSBtb2JpbGUgb2ZmLWNhbnZhcyBkcmF3ZXIgd2l0aCB0aGUgc2FtZSBmb3JtIGFjdGlvbiBhbmQgbm8gcHJlZGljdGl2ZSBwYW5lbC4KCiMjIEZsb2F0aW5nIFVYCgpBIHRoaXJkLXBhcnR5IENNUCByZW5kZXJzIGEgZnVsbC13aWR0aCBjb29raWUgY29uc2VudCBiYW5uZXIgYXQgdGhlIGJvdHRvbSBvZiB0aGUgdmlld3BvcnQgb24gZmlyc3QgdmlzaXQuIFRoZSBiYW5uZXIgb2ZmZXJzIGEgcHJpdmFjeS1wb2xpY3kgbGluaywgIkFsbG93IEFsbCIsICJSZWplY3QgQWxsIiwgYW5kICJDb25maXJtIE15IENob2ljZXMiIGJ1dHRvbnMuIEdyYW51bGFyIHByZWZlcmVuY2UgY29udHJvbHMgY292ZXIgZm91ciBjb25zZW50IGNhdGVnb3JpZXMgKGFuYWx5dGljcywgbWFya2V0aW5nLCBwcmVmZXJlbmNlcywgc2FsZSBvZiBkYXRhKS4gQ2hvaWNlIGlzIHN0b3JlZCBpbiBsb2NhbFN0b3JhZ2UgYW5kIGludGVncmF0ZXMgd2l0aCBHb29nbGUgQ29uc2VudCBNb2RlIFYyIGZvciBkb3duc3RyZWFtIHRhZyBnYXRpbmcuCgpBIEtsYXZpeW8tcG93ZXJlZCBuZXdzbGV0dGVyIHBvcHVwIGlzIGNvbmZpZ3VyZWQgKGxvYWRlZCB2aWEgYXN5bmMgc2NyaXB0KS4gSXQgaXMgdGltZS0gb3Igc2Vzc2lvbi1nYXRlZCBhbmQgZGlkIG5vdCBhcHBlYXIgZHVyaW5nIGNvbGQtc2Vzc2lvbiBleHBsb3JhdGlvbi4gVGhlIGlubGluZSBuZXdzbGV0dGVyIHNlY3Rpb24gaW4gdGhlIHBhZ2UgZm9vdGVyIGFyZWEgcmVtYWlucyB0aGUgYWx3YXlzLW9uIGNhcHR1cmUgc3VyZmFjZS4KCk5vIGNoYXQgd2lkZ2V0LCBubyBhZ2UgZ2F0ZSwgYW5kIG5vIGhvbWVwYWdlIG1vZGFsIHBvcHVwIHdlcmUgb2JzZXJ2ZWQuCgojIyBQb2xpY3kgJiBpbmZvIHBhZ2VzCgpTZXZlbiBpbmZvcm1hdGlvbmFsIHBhZ2VzIGFyZSBleHBvc2VkLiBGb3VyIGFyZSBuYXRpdmUgcG9saWNpZXMgdW5kZXIgYC9wb2xpY2llcy88c2x1Zz5gIC0tIHNoaXBwaW5nLCByZWZ1bmQsIHByaXZhY3ksIGFuZCB0ZXJtcyBvZiBzZXJ2aWNlIC0tIGFsbCBzaGFyaW5nIGEgbWluaW1hbCBzaW5nbGUtY29sdW1uIHRlbXBsYXRlOiBIMSB0aXRsZSwgdGhlbiByaWNoIHRleHQgcGFyYWdyYXBocywgSDIgc3ViLXNlY3Rpb25zLCBhbmQgYnVsbGV0IGxpc3RzLCB3aXRoIG5vIGltYWdlcyBvciBzaWRlYmFycy4KClRocmVlIGN1c3RvbSBwYWdlcyBsaXZlIHVuZGVyIGAvcGFnZXMvPHNsdWc+YC4gVGhlIGNvbnRhY3QgcGFnZSB1c2VzIGEgaGVybyBzcGxpdCBsYXlvdXQgd2l0aCBhIGhlYWRsaW5lLCBhIG9uZS0gdG8gdHdvLXNlbnRlbmNlIGJvZHksIGFuZCBhIENUQSBidXR0b24gZGVlcC1saW5raW5nIGludG8gYW4gZXh0ZXJuYWwgY3VzdG9tZXItc3VwcG9ydCBwb3J0YWwgKG5vIGlubGluZSBmb3JtKSwgZm9sbG93ZWQgYnkgYSB0aHJlZS1jYXJkIGluZm9ybWF0aW9uYWwgZ3JpZCBjb3ZlcmluZyB3YXJyYW50eSwgcHJvZHVjdCByZWdpc3RyYXRpb24sIGFuZCAyNC83IHN1cHBvcnQuIFRoZSBGQVEgcGFnZSB1c2VzIGEgY3VzdG9tIGFuY2hvcmVkLXNlY3Rpb24gdGVtcGxhdGU6IGFuIEgxLCBhIGhvcml6b250YWwgaW4tcGFnZSBuYXZpZ2F0aW9uIGJhciB3aXRoIGZvdXIgYW5jaG9ycyAoUHJvZHVjdHMgYW5kIFVzYWdlLCBPcmRlcnMsIENvbnRhY3QsIFdhcnJhbnR5KSwgYW5kIGZvdXIgSDIgc2VjdGlvbnMgb2YgYWNjb3JkaW9uLXN0eWxlIHF1ZXN0aW9uL2Fuc3dlciBpdGVtcy4gVGhlIGFib3V0IHBhZ2UgaXMgYSBjdXN0b20gZWRpdG9yaWFsIGxheW91dCB3aXRoIGEgY2VsZWJyaXR5LWNoZWYgaGVybyBxdW90ZSwgYSBicmFuZC1zdG9yeSBzZWN0aW9uIHBhaXJpbmcgY29weSB3aXRoIGltYWdlcnksIGEgZml2ZS1yb3cgbnVtYmVyZWQgZmVhdHVyZSBsaXN0LCBhIHRocmVlLWxpbmsgIlNob3AiIENUQSByb3csIGFuZCBhbiBpbmxpbmUgZW1haWwgc3Vic2NyaWJlIGZvcm0gd2l0aCBhIGhpZGRlbiBob25leXBvdC4=)

# Shop Manual -- Premium Hybrid Cookware and Kitchen Accessories Shop

## Overview

This is a premium hybrid cookware and kitchen accessories storefront priced in USD. The brand voice is bold, chef-endorsed, and direct-to-consumer, leaning on culinary-professional credibility and a "buy once" durability narrative. Aggregate review counts in the 50,000+ range and a stated lifetime warranty signal a sizeable, established catalog rather than a niche boutique.

## Site shell

A persistent dismissible announcement bar sits above a two-row sticky header. Row 1 is a utility bar: a left cluster of three editorial text links plus a "Partners" dropdown button listing 2-3 named collaborator pages, a centered logo, and a right cluster of search, account, and cart icon buttons. Row 2 is the primary category navigation -- eight top-level entries rendered as inline buttons. Most entries open flyout panels rather than a single mega menu, so navigation depth tops out at two levels (top-level -> sub-link). Each flyout is a full-width two-column panel: a vertical sub-link list ending in "Shop All [Category]" on the left, plus 2-3 featured product cards on the right (image, name, price with optional compare-at, savings badge, and star rating). One top-level entry behaves as a direct link instead of opening a flyout.

A mobile off-canvas drawer mirrors the same taxonomy as accordions, with extra direct links for sale, gift cards, "Shop All", and the Partners group.

The footer occupies a `contentinfo` landmark on every page and is split into a top band and a bottom band. The top band has three named link groups (Shop, Help, Media) plus a fourth column of four social icon links opening in new tabs. The bottom band is a flex row pairing a copyright line with two legal links (terms of service, accessibility commitment) against a brand wordmark image. The footer carries no inline newsletter form, no payment icons, and no locale or currency switcher.

## Homepage

The homepage is a long, modular composition of sixteen sections in this order:

- Full-width hero with autoplay muted looping background video and a centered headline + single CTA overlay.

- "Shop by Category" chip slider -- a horizontally scrolling row of seven image-backed sub-collection chips with prev/next arrows and a "Shop All" link.

- Featured sets promo block -- text-left / product-cards-right, with a 3-card row showing image, savings badge, name, current price, and original price.

- Specialty product banner -- a reversed two-column block pairing two product cards on the left with descriptive copy on the right introducing a limited-time sub-line.

- Chef endorsement block -- autoplay video thumbnail with a play overlay opening fullscreen playback, paired with an attributed blockquote and a star + aggregate-review-count social-proof line.

- 2x2 feature card grid -- four cards covering high-heat capability, PFAS-free nonstick, dishwasher safety, and durability/warranty, each with a small attribute badge, an all-caps headline, and a one- to two-sentence descriptor.

- Reviews banner -- aggregate rating + rotating customer quote on one side, a three-icon trust strip (lifetime warranty, free shipping, 30-day returns) on the other.

- "Best Sellers" horizontal product carousel with prev/next arrows and a "Shop All" link.

- Knife category hero with two product cards on the left and a category value-prop + customer quote chip on the right.

- UGC video carousel -- six video thumbnail tiles with play overlays; tiles open a fullscreen popup player.

- 3-up specialty category banners -- three equal-width cards each combining a product image, headline, descriptor, CTA link, and a customer quote chip with star rating.

- Culinary council section introducing the brand's chef advisory group with five professional names (roles only) and a CTA to a dedicated page.

- "Recipes" carousel of recipe cards with image, title, yield, and time, linking into the recipes blog.

- "Articles" carousel of editorial blog cards using the same card chrome minus the recipe metadata.

- Founder message -- a short two-paragraph first-person note signed with a plain-text name.

- Inline newsletter section at the page bottom with an email input, hidden honeypot, and "Subscribe" button.

There is no homepage modal popup. A separate Klaviyo-driven popup is configured but did not fire during exploration.

## Collections & navigation

Collection pages render as a three-column grid on desktop. Each card shows a product image, an optional promotional overlay badge ("SALE", "New", "Bestseller"), product title, star rating with review count, and price (strikethrough original price plus a percentage-off badge when discounted). The collection title displays a live product count in parentheses.

Above the grid sits a horizontal filter bar with two collapsible controls. The "Filter" panel exposes two checkbox facets -- "Available" and "On Sale" -- that update URL parameters immediately, render server-side, and combine cleanly. The "Sort by" dropdown offers eight options: featured, best selling, alphabetically A-Z, alphabetically Z-A, price ascending, price descending, date new-to-old, and date old-to-new. Sorting updates the `sort\_by` URL parameter without a full reload.

Pagination uses a "Load more" button. The initial render shows 24 cards; clicking the button appends the rest of the collection in a single batch and the button then disappears. There is no infinite scroll, no numbered pagination, and no `page=` URL parameter.

## Product page

The product page leads with a horizontal image carousel that has prev/next arrow controls and an optional left-side thumbnail strip for direct slide selection. Below the title sits the price block: prominent current price, optional strikethrough original price, optional percentage savings badge, and a buy-now-pay-later financing line that opens a modal. A trust badge row beneath the price summarizes free shipping, a 30-day return guarantee, and (where applicable) a lifetime warranty, plus an expandable claim button listing chemical-safety attributes for nonstick items.

Variant selectors render as radio buttons in a single horizontal row. Apparel exposes a size axis (XS-XXL) with a "Size Guide" link above the group. Single-variant products skip the selector entirely. A quantity stepper (decrement, numeric display, increment) sits immediately adjacent to the "Add to Cart" CTA.

Descriptions vary by category. Simpler products render an inline prose paragraph plus a bulleted feature list. Complex products use an accordion-tab layout (e.g. "Description" + "Hybrid Technology" tabs) followed by a horizontal seven-icon attribute strip (warranty, utensil safety, nonstick, oven-safe, dishwasher-safe, induction-ready, stay-cool handle). Some PDPs include a "Gift With Purchase" callout above the quantity stepper showing a bundled free item.

Reviews use an Okendo-style widget. Products without reviews show a "Be the first to leave a review" prompt and a "Write a review" CTA. Products with reviews show an aggregate score, a clickable star-distribution breakdown, an auto-generated AI summary block, search and sort/filter dropdowns (latest, oldest, highest, lowest, most helpful; rating 1-5 or all), and individual review cards with reviewer name, star rating, relative date, headline, body, and helpful-vote buttons.

Recommendation rails differ by template. Some PDPs render a "Customers also love" rail of product cards with quick-add buttons and inline color-swatch selectors. Others render two stacked rails -- a "Frequently Bought Together" trio with inline "Add to Cart" buttons, and a "Recently Viewed" carousel with prev/next arrows. No customization or personalization fields (engraving, monogram, gift note) are exposed on the PDP.

## Cart

The cart opens as a right-side slide-out drawer (ARIA `dialog` labeled "Your Cart") triggered by the header cart icon. The icon shows a numeric item-count badge once the cart has any items.

Empty state shows the "Your Cart" heading with a `0` badge, a short empty-cart sentence, a CTA link into a best-sellers collection, a `$0.00` subtotal line, and the same trust-badge trio (lifetime warranty, free shipping, 30-day returns) repeated near the footer.

Filled state replaces the empty copy with a free-shipping qualifier banner once the threshold is met. Each line item shows a thumbnail, name (both linked to the PDP), the price block (current price plus strikethrough compare-at when discounted), a "Remove Item" affordance, and a three-button quantity stepper. Quantity changes apply via Ajax and immediately recompute three summary rows: products at list price, total savings, and subtotal. A full-width "Checkout" button sits below, with a footnote asterisk for free-shipping eligibility and the trust badges repeated.

The drawer carries a "Frequently Bought Together" upsell rail (three product cards with inline "Add to Cart") in both states; carted items are swapped out of the rail for fresh suggestions. A "Recently Viewed" rail with prev/next arrows appears beneath. There is no inline promo-code field -- discount codes are collected on the native checkout -- and there is no inline shipping estimate calculator; free-shipping eligibility is conveyed only via the qualifier banner and footnote.

## Search

Search is triggered by a magnifying-glass icon button in the header utility row. Clicking it expands an inline dropdown directly below the icon -- the page is not dimmed and navigation remains visible.

Predictive search renders a static "Suggested" panel inside the dropdown: typically four links combining one collection shortcut and three pre-set search-query links. The list is fixed and does not change with keystrokes. The dropdown itself does not render product thumbnails, prices, or product cards -- only suggested queries and collection shortcuts.

A `/search/suggest.json` predictive endpoint is active in the background and returns product-shaped JSON (title, handle, price, compare-at range, availability, URL, vendor, featured image, tags, type) but its results are not surfaced in the header dropdown. Submitting the form navigates to a full-page `/search?q=<query>` results listing. A second search input appears in the mobile off-canvas drawer with the same form action and no predictive panel.

## Floating UX

A third-party CMP renders a full-width cookie consent banner at the bottom of the viewport on first visit. The banner offers a privacy-policy link, "Allow All", "Reject All", and "Confirm My Choices" buttons. Granular preference controls cover four consent categories (analytics, marketing, preferences, sale of data). Choice is stored in localStorage and integrates with Google Consent Mode V2 for downstream tag gating.

A Klaviyo-powered newsletter popup is configured (loaded via async script). It is time- or session-gated and did not appear during cold-session exploration. The inline newsletter section in the page footer area remains the always-on capture surface.

No chat widget, no age gate, and no homepage modal popup were observed.

## Policy & info pages

Seven informational pages are exposed. Four are native policies under `/policies/<slug>` -- shipping, refund, privacy, and terms of service -- all sharing a minimal single-column template: H1 title, then rich text paragraphs, H2 sub-sections, and bullet lists, with no images or sidebars.

Three custom pages live under `/pages/<slug>`. The contact page uses a hero split layout with a headline, a one- to two-sentence body, and a CTA button deep-linking into an external customer-support portal (no inline form), followed by a three-card informational grid covering warranty, product registration, and 24/7 support. The FAQ page uses a custom anchored-section template: an H1, a horizontal in-page navigation bar with four anchors (Products and Usage, Orders, Contact, Warranty), and four H2 sections of accordion-style question/answer items. The about page is a custom editorial layout with a celebrity-chef hero quote, a brand-story section pairing copy with imagery, a five-row numbered feature list, a three-link "Shop" CTA row, and an inline email subscribe form with a hidden honeypot.

### F.2 Capabilities (capabilities.json)

[⬇](data:text/plain;base64,ewogICJ2ZXJzaW9uIjogIjAuMSIsCiAgInNob3AiOiB7CiAgICAiZGVzY3JpcHRvciI6ICJQcmVtaXVtIGh5YnJpZCBjb29rd2FyZSBhbmQga2l0Y2hlbiBhY2Nlc3NvcmllcyBzaG9wIiwKICAgICJjYXRlZ29yeSI6ICJDb29rd2FyZSAvIEtpdGNoZW4iLAogICAgImN1cnJlbmN5IjogIlVTRCIsCiAgICAidG9uZSI6IFsKICAgICAgInByZW1pdW0iLAogICAgICAiYm9sZCIsCiAgICAgICJjaGVmLWVuZG9yc2VkIiwKICAgICAgImRpcmVjdC10by1jb25zdW1lciIKICAgIF0KICB9LAogICJzaXRlX3NoZWxsIjogewogICAgImhhc19hbm5vdW5jZW1lbnRfYmFyIjogdHJ1ZSwKICAgICJoZWFkZXJfc3R5bGUiOiAidHdvLXJvdyBzdGlja3kiLAogICAgImhhc19tZWdhX21lbnUiOiBmYWxzZSwKICAgICJuYXZfZGVwdGgiOiAyLAogICAgImZvb3Rlcl9ncm91cHMiOiAzCiAgfSwKICAiaG9tZXBhZ2UiOiB7CiAgICAic2VjdGlvbl90eXBlcyI6IFsKICAgICAgImhlcm9fdmlkZW8iLAogICAgICAiY2F0ZWdvcnlfY2hpcF9zbGlkZXIiLAogICAgICAiZmVhdHVyZWRfcHJvZHVjdF9ncmlkIiwKICAgICAgInNwZWNpYWx0eV9wcm9kdWN0X2Jhbm5lciIsCiAgICAgICJ2aWRlb19lbmRvcnNlbWVudCIsCiAgICAgICJmZWF0dXJlX2NhcmRzX2dyaWQiLAogICAgICAicmV2aWV3c19iYW5uZXIiLAogICAgICAicHJvZHVjdF9jYXJvdXNlbCIsCiAgICAgICJwcm9kdWN0X2hlcm9fcXVvdGUiLAogICAgICAidWdjX3ZpZGVvX2Nhcm91c2VsIiwKICAgICAgImNhdGVnb3J5X2Jhbm5lcnNfM3VwIiwKICAgICAgImN1bGluYXJ5X2NvdW5jaWwiLAogICAgICAicmVjaXBlX2Nhcm91c2VsIiwKICAgICAgImFydGljbGVfY2Fyb3VzZWwiLAogICAgICAiZm91bmRlcl9tZXNzYWdlIiwKICAgICAgIm5ld3NsZXR0ZXJfaW5saW5lIgogICAgXSwKICAgICJzZWN0aW9uX2NvdW50IjogMTYsCiAgICAiaGFzX3BvcHVwX21vZGFsIjogZmFsc2UKICB9LAogICJjb2xsZWN0aW9uIjogewogICAgImxheW91dCI6ICJncmlkIiwKICAgICJjb2x1bW5zX2Rlc2t0b3AiOiAzLAogICAgImZpbHRlcnMiOiBbCiAgICAgICJhdmFpbGFiaWxpdHkiLAogICAgICAib25fc2FsZSIKICAgIF0sCiAgICAic29ydCI6IFsKICAgICAgImZlYXR1cmVkIiwKICAgICAgImJlc3Rfc2VsbGluZyIsCiAgICAgICJhbHBoYWJldGljYWxseV9heiIsCiAgICAgICJhbHBoYWJldGljYWxseV96YSIsCiAgICAgICJwcmljZV9hc2MiLAogICAgICAicHJpY2VfZGVzYyIsCiAgICAgICJkYXRlX25ldyIsCiAgICAgICJkYXRlX29sZCIKICAgIF0sCiAgICAicGFnaW5hdGlvbiI6ICJsb2FkX21vcmUiCiAgfSwKICAicHJvZHVjdCI6IHsKICAgICJnYWxsZXJ5X3N0eWxlIjogImhvcml6b250YWxfY2Fyb3VzZWxfd2l0aF9wcmV2X25leHQiLAogICAgInZhcmlhbnRfc2VsZWN0b3JzIjogWwogICAgICAicmFkaW9fYnV0dG9ucyIKICAgIF0sCiAgICAiaGFzX3F1YW50aXR5X3NlbGVjdG9yIjogdHJ1ZSwKICAgICJkZXNjcmlwdGlvbl9sYXlvdXQiOiAiYWNjb3JkaW9uX3RhYnMiLAogICAgImhhc19yZXZpZXdzIjogdHJ1ZSwKICAgICJoYXNfcmVjb21tZW5kYXRpb25zIjogdHJ1ZSwKICAgICJoYXNfcGVyc29uYWxpemF0aW9uIjogZmFsc2UKICB9LAogICJjYXJ0IjogewogICAgInR5cGUiOiAiZHJhd2VyIiwKICAgICJoYXNfcHJvbW9faW5wdXQiOiBmYWxzZSwKICAgICJoYXNfdXBzZWxscyI6IHRydWUsCiAgICAiaGFzX3NoaXBwaW5nX2VzdGltYXRlIjogZmFsc2UKICB9LAogICJzZWFyY2giOiB7CiAgICAidHJpZ2dlciI6ICJpY29uX2J1dHRvbiIsCiAgICAiaGFzX3ByZWRpY3RpdmUiOiB0cnVlLAogICAgInByZWRpY3RpdmVfdHlwZXMiOiBbCiAgICAgICJzdWdnZXN0ZWRfcXVlcmllcyIsCiAgICAgICJjb2xsZWN0aW9uX3Nob3J0Y3V0cyIKICAgIF0sCiAgICAicmVzdWx0c19sYXlvdXQiOiAiZnVsbHBhZ2UiCiAgfSwKICAiaW50bCI6IHsKICAgICJoYXNfbG9jYWxlX3N3aXRjaGVyIjogbnVsbCwKICAgICJoYXNfY3VycmVuY3lfc3dpdGNoZXIiOiBudWxsCiAgfSwKICAiZmxvYXRpbmciOiB7CiAgICAiaGFzX2NoYXRfd2lkZ2V0IjogZmFsc2UsCiAgICAiaGFzX2FnZV9nYXRlIjogZmFsc2UsCiAgICAiaGFzX2Nvb2tpZV9iYW5uZXIiOiB0cnVlLAogICAgImhhc19uZXdzbGV0dGVyX3BvcHVwIjogdHJ1ZQogIH0sCiAgImluZm9fcGFnZXNfcHJlc2VudCI6IFsKICAgICJzaGlwcGluZy1wb2xpY3kiLAogICAgInJlZnVuZC1wb2xpY3kiLAogICAgInByaXZhY3ktcG9saWN5IiwKICAgICJ0ZXJtcy1vZi1zZXJ2aWNlIiwKICAgICJjb250YWN0IiwKICAgICJmYXEiLAogICAgImFib3V0LXVzIgogIF0KfQ==)

{

"version": "0.1",

"shop": {

"descriptor": "Premium hybrid cookware and kitchen accessories shop",

"category": "Cookware / Kitchen",

"currency": "USD",

"tone": [

"premium",

"bold",

"chef-endorsed",

"direct-to-consumer"

]

},

"site\_shell": {

"has\_announcement\_bar": true,

"header\_style": "two-row sticky",

"has\_mega\_menu": false,

"nav\_depth": 2,

"footer\_groups": 3

},

"homepage": {

"section\_types": [

"hero\_video",

"category\_chip\_slider",

"featured\_product\_grid",

"specialty\_product\_banner",

"video\_endorsement",

"feature\_cards\_grid",

"reviews\_banner",

"product\_carousel",

"product\_hero\_quote",

"ugc\_video\_carousel",

"category\_banners\_3up",

"culinary\_council",

"recipe\_carousel",

"article\_carousel",

"founder\_message",

"newsletter\_inline"

],

"section\_count": 16,

"has\_popup\_modal": false

},

"collection": {

"layout": "grid",

"columns\_desktop": 3,

"filters": [

"availability",

"on\_sale"

],

"sort": [

"featured",

"best\_selling",

"alphabetically\_az",

"alphabetically\_za",

"price\_asc",

"price\_desc",

"date\_new",

"date\_old"

],

"pagination": "load\_more"

},

"product": {

"gallery\_style": "horizontal\_carousel\_with\_prev\_next",

"variant\_selectors": [

"radio\_buttons"

],

"has\_quantity\_selector": true,

"description\_layout": "accordion\_tabs",

"has\_reviews": true,

"has\_recommendations": true,

"has\_personalization": false

},

"cart": {

"type": "drawer",

"has\_promo\_input": false,

"has\_upsells": true,

"has\_shipping\_estimate": false

},

"search": {

"trigger": "icon\_button",

"has\_predictive": true,

"predictive\_types": [

"suggested\_queries",

"collection\_shortcuts"

],

"results\_layout": "fullpage"

},

"intl": {

"has\_locale\_switcher": null,

"has\_currency\_switcher": null

},

"floating": {

"has\_chat\_widget": false,

"has\_age\_gate": false,

"has\_cookie\_banner": true,

"has\_newsletter\_popup": true

},

"info\_pages\_present": [

"shipping-policy",

"refund-policy",

"privacy-policy",

"terms-of-service",

"contact",

"faq",

"about-us"

]

}

### F.3 Statistics (stats.json)

[⬇](data:text/plain;base64,ewogICJwcm9kdWN0c190b3RhbCI6IDE2NCwKICAiY29sbGVjdGlvbnNfdG90YWwiOiA1MCwKICAicHJvZHVjdHNfcGVyX2NvbGxlY3Rpb24iOiB7CiAgICAiYXZnIjogMTUuNDIsCiAgICAibWVkaWFuIjogOC4wLAogICAgIm1heCI6IDE3OQogIH0sCiAgInByaWNlIjogewogICAgIm1pbiI6IDAuOTgsCiAgICAibWF4IjogNTQ5OS4wLAogICAgIm1lZGlhbiI6IDU5Ljk5LAogICAgImN1cnJlbmN5IjogIlVTRCIKICB9LAogICJwcm9kdWN0c193aXRoX3ZhcmlhbnRzX3BjdCI6IDAuMDczMTcwNzMxNzA3MzE3MDcsCiAgInZhcmlhbnRfYXhlc19vYnNlcnZlZCI6IFsKICAgICJ0aXRsZSIsCiAgICAic2l6ZSIKICBdLAogICJuYXZpZ2F0aW9uX2RlcHRoX21heCI6IDIsCiAgImhvbWVwYWdlX3NlY3Rpb25fY291bnQiOiAxNiwKICAiaW5mb19wYWdlc19jb3VudCI6IDcsCiAgImZlYXR1cmVfY291bnQiOiA0OAp9)

{

"products\_total": 164,

"collections\_total": 50,

"products\_per\_collection": {

"avg": 15.42,

"median": 8.0,

"max": 179

},

"price": {

"min": 0.98,

"max": 5499.0,

"median": 59.99,

"currency": "USD"

},

"products\_with\_variants\_pct": 0.07317073170731707,

"variant\_axes\_observed": [

"title",

"size"

],

"navigation\_depth\_max": 2,

"homepage\_section\_count": 16,

"info\_pages\_count": 7,

"feature\_count": 48

}

## Appendix G ShopArena Exploration Plan Example

This appendix reproduces the plan.md document emitted by
the planner iteration of shop\_arena.explore for the same
exploration run shown in Appendix [F](#A6). The
plan enumerates the per-task work items the executor loop then
consumes one task at a time; checkbox state ([x] /
[!]) is updated by the executor at the end of each
iteration.

### G.1 Plan (plan.md)

[⬇](data:text/plain;base64,IyBQbGFuIC0tIFByZW1pdW0gSHlicmlkIENvb2t3YXJlIFNob3AKCkEgZGlyZWN0LXRvLWNvbnN1bWVyIHNob3Agc3BlY2lhbGl6aW5nIGluIHByZW1pdW0gaHlicmlkIGNvb2t3YXJlLCBrbml2ZXMsIGtpdGNoZW4gdG9vbHMsIHNlYXNvbmluZ3MsIGFuZCBicmFuZGVkIGFwcGFyZWwsIGVuZG9yc2VkIGJ5IGEgY2VsZWJyaXR5IGNoZWYuIFNlbGxzIHZpYSBVU0QgcHJpY2luZyB3aXRoIFVTLWZvY3VzZWQgc2hpcHBpbmcuIFRoZSBzaG9wIHVzZXMgYSB0d28tcm93IHN0aWNreSBoZWFkZXIsIGZseW91dCBkcm9wZG93biBuYXZpZ2F0aW9uLCBhbmQgYSBjYXJ0IGRyYXdlciBhcmNoaXRlY3R1cmUuCgojIyBUYXNrcwoKLSBbeF0gaG9tZXBhZ2Vfc2VjdGlvbnMgLS0gbmF2aWdhdGUgdG8gYC9gOyBjYXB0dXJlIGhlcm8gc2VjdGlvbiwgZWFjaCBiZWxvdy1oZXJvIHNlY3Rpb24gKGNhdGVnb3J5IGdyaWQsIGVuZG9yc2VtZW50IGJsb2NrLCBmZWF0dXJlcyBzZWN0aW9uLCBiZXN0LXNlbGxlcnMgY2Fyb3VzZWwsIHNvY2lhbC1wcm9vZi90ZXN0aW1vbmlhbHMsIHNwZWNpYWx0eS1wcm9kdWN0IGJhbm5lcnMsIHJlY2lwZSBjYXJvdXNlbCksIG5vdGUgYW55IG5ld3NsZXR0ZXIgcG9wdXAgYmVoYXZpb3I7IGZ1bGwtcGFnZSBzY3JlZW5zaG90ICsgcGVyLXNlY3Rpb24gZXZpZGVuY2UgW3ByaW9yaXR5OiA5XQotIFt4XSBjYXJ0X2RyYXdlciAtLSBhZGQgMSBwcm9kdWN0IHRvIGNhcnQ7IGNhcHR1cmUgZHJhd2VyIGluIGVtcHR5IHN0YXRlLCBmaWxsZWQgc3RhdGUsIHF0eS1jaGFuZ2Ugc3RhdGU7IGNoZWNrIGZvciBwcm9tby1jb2RlIGlucHV0LCB1cHNlbGwgcmFpbCwgYW5kIHNoaXBwaW5nLWVzdGltYXRlIHdpZGdldCBbcHJpb3JpdHk6IDhdCi0gW3hdIGhlYWRlcl9uYXZpZ2F0aW9uIC0tIHNuYXBzaG90IG1haW4gbmF2IGluIGNsb3NlZCBzdGF0ZSwgdGhlbiB0cmlnZ2VyIGVhY2ggdG9wLWxldmVsIGZseW91dCBidXR0b24gKDggY2F0ZWdvcmllcyk7IGNhcHR1cmUgb25lIG9wZW4gZmx5b3V0OyByZWNvcmQgbmF2IGRlcHRoIGFuZCBzdWItbGluayBjb3VudCBwZXIgY2F0ZWdvcnkgW3ByaW9yaXR5OiA3XQotIFt4XSBzZWFyY2hfcHJlZGljdGl2ZSAtLSBvcGVuIHNlYXJjaCBtb2RhbDsgdHlwZSAyIHNob3J0IHByZWZpeGVzICgicyIgYW5kICJwYW4iKTsgY2FwdHVyZSBzdWdnZXN0aW9uIHBhbmVsIHNob3dpbmcgcHJvZHVjdHM7IGNhcHR1cmUgb25lIG5ldHdvcmsgcmVxdWVzdCB2aWEgbmV0d29yay5qc29ubCBbcHJpb3JpdHk6IDddCi0gW3hdIGNvbGxlY3Rpb25fZmlsdGVycyAtLSB2aXNpdCB0aGUgbGFyZ2VzdCBjb29rd2FyZSBjb2xsZWN0aW9uOyBleGVyY2lzZSAiQXZhaWxhYmxlIiBhbmQgIk9uIFNhbGUiIGZpbHRlciBjaGVja2JveGVzOyB0ZXN0IGFsbCBzb3J0IG9wdGlvbnM7IHNjcm9sbCB0byBib3R0b20gdG8gY29uZmlybSBwYWdpbmF0aW9uIGJlaGF2aW9yOyBzY3JlZW5zaG90IGdyaWQgYW5kIHJlY29yZCBjb2x1bW4gY291bnQgW3ByaW9yaXR5OiA2XQotIFt4XSBwcm9kdWN0X3ZhcmlhbnRzIC0tIHZpc2l0IDIgUERQczogb25lIGFwcGFyZWwgcHJvZHVjdCAoaGFzIHNpemUgcmFkaW8gYnV0dG9ucykgYW5kIG9uZSBjb29rd2FyZSBzZXQgKHNpbmdsZS12YXJpYW50KTsgY2FwdHVyZSBnYWxsZXJ5IGNhcm91c2VsIHN0YXRlcyAocHJldi9uZXh0KSwgdmFyaWFudCBzZWxlY3RvciBzdGF0ZXMsIHF0eSBzdGVwcGVyLCBkZXNjcmlwdGlvbiBsYXlvdXQsIHJldmlld3Mgd2lkZ2V0IChPa2VuZG8pLCBhbmQgIkN1c3RvbWVycyBhbHNvIGxvdmUiIHJlY29tbWVuZGF0aW9ucyByYWlsIFtwcmlvcml0eTogNV0KLSBbeF0gZm9vdGVyIC0tIHNjcmVlbnNob3QgZnVsbCBmb290ZXI7IHJlY29yZCBsaW5rIGdyb3Vwcywgc29jaWFsIGljb25zLCBhbmQgYm90dG9tLWJhciBjb3B5cmlnaHQvbGVnYWwgbGlua3MgW3ByaW9yaXR5OiA0XQotIFt4XSBpbmZvX3BhZ2VzIC0tIHZpc2l0IGAvcG9saWNpZXMvc2hpcHBpbmctcG9saWN5YCwgYC9wb2xpY2llcy9yZWZ1bmQtcG9saWN5YCwgYC9wb2xpY2llcy9wcml2YWN5LXBvbGljeWAsIGAvcG9saWNpZXMvdGVybXMtb2Ytc2VydmljZWAsIGAvcGFnZXMvY29udGFjdGAsIGAvcGFnZXMvZmFxYCwgYC9wYWdlcy9hYm91dC11c2A7IG9uZSBzY3JlZW5zaG90IGVhY2g7IG5vdGUgcGFnZSBsYXlvdXQgdHlwZSAocG9saWN5IHRlbXBsYXRlIHZzIGN1c3RvbSBwYWdlKSBbcHJpb3JpdHk6IDNdCi0gW3hdIGZsb2F0aW5nX3dpZGdldHMgLS0gd2FpdCBmb3IgYW5kIGNhcHR1cmUgS2xhdml5byBuZXdzbGV0dGVyIHBvcHVwOyBpbnNwZWN0IENyaXNwIGNoYXQgd2lkZ2V0IGxhdW5jaGVyOyBjaGVjayBPbmVUcnVzdCBjb29raWUgYmFubmVyIHByZXNlbmNlOyBvbmUgc2NyZWVuc2hvdCBwZXIgd2lkZ2V0IGlmIHZpc2libGUgW3ByaW9yaXR5OiAxXQoKIyMgT21pdHRlZCBBcmVhcwoKLSBtZWdhX21lbnUgLS0gbmF2IHVzZXMgZmx5b3V0IGRyb3Bkb3duIHBhbmVscyBwZXIgY2F0ZWdvcnkgKHNpbmdsZS1jb2x1bW4gc3ViLWxpbmsgbGlzdHMpLCBub3QgYSBmdWxsLWdyaWQgbWVnYSBtZW51IGxheW91dDsgb2JzZXJ2ZWQgaW4gaG9tZXBhZ2Ugc25hcHNob3QKLSBpbnRsX3N3aXRjaGVycyAtLSBvbmx5IGBlbl9VU2AgbG9jYWxlIHByZXNlbnQ7IG5vIGxvY2FsZSBvciBjdXJyZW5jeSBzd2l0Y2hlciB2aXNpYmxlIGluIGhlYWRlciwgZm9vdGVyLCBvciBob21lcGFnZSBzbmFwc2hvdDsgYGluZGV4Lmh0bWxgIGxvY2FsZSBtZXRhZGF0YSBpcyBgZW5fVVNgIG9ubHkKLSBhZ2VfZ2F0ZSAtLSBub3Qgb2JzZXJ2ZWQgb24gYC9gIGhvbWVwYWdlIHNuYXBzaG90IG9yIGluIGBpbmRleC5odG1sYCBIVE1MIHN0cnVjdHVyZQ==)

# Plan -- Premium Hybrid Cookware Shop

A direct-to-consumer shop specializing in premium hybrid cookware, knives, kitchen tools, seasonings, and branded apparel, endorsed by a celebrity chef. Sells via USD pricing with US-focused shipping. The shop uses a two-row sticky header, flyout dropdown navigation, and a cart drawer architecture.

## Tasks

- [x] homepage\_sections -- navigate to `/`; capture hero section, each below-hero section (category grid, endorsement block, features section, best-sellers carousel, social-proof/testimonials, specialty-product banners, recipe carousel), note any newsletter popup behavior; full-page screenshot + per-section evidence [priority: 9]

- [x] cart\_drawer -- add 1 product to cart; capture drawer in empty state, filled state, qty-change state; check for promo-code input, upsell rail, and shipping-estimate widget [priority: 8]

- [x] header\_navigation -- snapshot main nav in closed state, then trigger each top-level flyout button (8 categories); capture one open flyout; record nav depth and sub-link count per category [priority: 7]

- [x] search\_predictive -- open search modal; type 2 short prefixes ("s" and "pan"); capture suggestion panel showing products; capture one network request via network.jsonl [priority: 7]

- [x] collection\_filters -- visit the largest cookware collection; exercise "Available" and "On Sale" filter checkboxes; test all sort options; scroll to bottom to confirm pagination behavior; screenshot grid and record column count [priority: 6]

- [x] product\_variants -- visit 2 PDPs: one apparel product (has size radio buttons) and one cookware set (single-variant); capture gallery carousel states (prev/next), variant selector states, qty stepper, description layout, reviews widget (Okendo), and "Customers also love" recommendations rail [priority: 5]

- [x] footer -- screenshot full footer; record link groups, social icons, and bottom-bar copyright/legal links [priority: 4]

- [x] info\_pages -- visit `/policies/shipping-policy`, `/policies/refund-policy`, `/policies/privacy-policy`, `/policies/terms-of-service`, `/pages/contact`, `/pages/faq`, `/pages/about-us`; one screenshot each; note page layout type (policy template vs custom page) [priority: 3]

- [x] floating\_widgets -- wait for and capture Klaviyo newsletter popup; inspect Crisp chat widget launcher; check OneTrust cookie banner presence; one screenshot per widget if visible [priority: 1]

## Omitted Areas

- mega\_menu -- nav uses flyout dropdown panels per category (single-column sub-link lists), not a full-grid mega menu layout; observed in homepage snapshot

- intl\_switchers -- only `en\_US` locale present; no locale or currency switcher visible in header, footer, or homepage snapshot; `index.html` locale metadata is `en\_US` only

- age\_gate -- not observed on `/` homepage snapshot or in `index.html` HTML structure

## Appendix H ShopGuru Skill Catalog

This appendix accompanies §[2.2.1](#S2.SS2.SSS1) and summarizes the seven skill categories generated by ShopGuru.

Table 1: ShopGuru’s seven skill categories grouped by horizon.
Short-horizon tasks are produced by deterministic, pure-function
generators over ShopArena’s extracted JSON; long-horizon tasks are
LLM-authored from few-shot examples reflecting human-shopper behaviors
and reconciled against the same extracted data via a validator-driven
polish loop (§[2.2.3](#S2.SS2.SSS3)).

| Group | Bundle | Source data | Skill primitives |
| --- | --- | --- | --- |
| Discovery | short-horizon | products.json | exact title search, substitute search |
| Filter-Selection | short-horizon | collections.json + per-collection options | collection browse, collection filter |
| Information-Seeking | short-horizon | pages.json (+ default policy fallback) | shipping policy lookup, returns policy lookup |
| E2E shopping journey | long-horizon | all of the above + few-shot human-trace examples | LLM-authored multi-step intents |

## Appendix I Examples of ShopGuru tasks

[⬇](data:text/plain;base64,ewogICAgImlkIjogIm1vY2tfY2xvdGhpbmctZmlsdGVyLTEiLAogICAgInR5cGUiOiAic2hvcHBpbmciLAogICAgImludGVudCI6ICJOYXZpZ2F0ZSB0byB0aGUgXCJGcm9zdCBTZWFzb24gQ29sbGVjdGlvblwiIGNvbGxlY3Rpb24gb24gdGhpcyBzdG9yZS4gRmluZCBhbmQgdXNlIHRoZSBDb2xvciBmaWx0ZXIgKGUuZy4gQmxhY2spIHRvIHNlbGVjdCBhbiBvcHRpb24uIElmIHByb2R1Y3RzIGFyZSBzaG93biBhZnRlciBmaWx0ZXJpbmcsIHNlbGVjdCBhbnkgdmFyaWFudCBvZiBhIHByb2R1Y3QgYW5kIGFkZCBpdCB0byBjYXJ0LiBJdCBpcyBvayBpZiBubyBwcm9kdWN0cyBtYXRjaCB0aGUgZmlsdGVyOyB1c2luZyBmaWx0ZXIgY29ycmVjdGx5IG1lYW5zIHRoZSBuYXZpZ2F0aW9uIHRhc2sgaXMgY29tcGxldGVkIHN1Y2Nlc3NmdWxseS4iLAogICAgInN1Y2Nlc3NfY3JpdGVyaWEiOiB7CiAgICAgICJ1cmxfY29udGFpbnMiOiAiL2NvbGxlY3Rpb25zL2Zyb3N0LXNlYXNvbi1jb2xsZWN0aW9uIiwKICAgICAgInR5cGUiOiAibmF2aWdhdGlvbiIKICAgIH0sCn0=)

{

"id": "mock\_clothing-filter-1",

"type": "shopping",

"intent": "Navigate to the \"Frost Season Collection\" collection on this store. Find and use the Color filter (e.g. Black) to select an option. If products are shown after filtering, select any variant of a product and add it to cart. It is ok if no products match the filter; using filter correctly means the navigation task is completed successfully.",

"success\_criteria": {

"url\_contains": "/collections/frost-season-collection",

"type": "navigation"

},

}

Listing 1: Example collection-filter task emitted by the deterministic
generator. url\_contains is a soft URL hint to the LLM judge,
not a hard pass/fail gate.


[⬇](data:text/plain;base64,ewogICAgImlkIjogIm1vY2tfaGFyZHdhcmUtcmV0dXJucy0xIiwKICAgICJ0eXBlIjogIm5hdmlnYXRpb24iLAogICAgImludGVudCI6ICJGaW5kIHRoZSByZXR1cm5zIGFuZCByZWZ1bmQgcG9saWN5IHBhZ2Ugb24gdGhpcyBzdG9yZS4gTG9vayBmb3IgcmV0dXJuIHBvbGljeSBpbmZvcm1hdGlvbiBpbiB0aGUgZm9vdGVyLCBtZW51LCBvciBhbnkgbmF2aWdhdGlvbiBsaW5rcy4gUmVhZCB0aGUgcmVmdW5kIHBvbGljeSBkZXRhaWxzLCB0aGVuIGxlYXZlIHRoZSBzaXRlLiIsCiAgICAic3VjY2Vzc19jcml0ZXJpYSI6IHsKICAgICAgInVybF9jb250YWlucyI6ICIvcG9saWNpZXMvcmVmdW5kLXBvbGljeSIsCiAgICAgICJ0eXBlIjogInBhZ2VfbmF2aWdhdGlvbiIKICAgIH0sCiAgICAidXJsX2NvbnRhaW5zX2FsdCI6IFsKICAgICAgIi9wYWdlcy9yZXR1cm4tcG9saWN5IgogICAgXSwKfQ==)

{

"id": "mock\_hardware-returns-1",

"type": "navigation",

"intent": "Find the returns and refund policy page on this store. Look for return policy information in the footer, menu, or any navigation links. Read the refund policy details, then leave the site.",

"success\_criteria": {

"url\_contains": "/policies/refund-policy",

"type": "page\_navigation"

},

"url\_contains\_alt": [

"/pages/return-policy"

],

}

Listing 2: Example page-navigation task to find specific policy on the shop, also emitted by the deterministic
generator.


[⬇](data:text/plain;base64,ewogICAgImlkIjogIm1vY2tfY29va3dhcmUtZTJlLXYxLTMiLAogICAgInR5cGUiOiAic2hvcHBpbmciLAogICAgImludGVudCI6ICJTaG9wcGluZyBmb3IgYSBuZXcgY2hlZidzIGtuaWZlIG9uIGEgYnVkZ2V0LiBOYXZpZ2F0ZSB0byB0aGUgS25pdmVzIGNvbGxlY3Rpb24uIEFwcGx5IGEgZmlsdGVyIGZvciBDb2xvciBpZiBhdmFpbGFibGUsIG9yIHNvcnQgdGhlIGNvbGxlY3Rpb24gYnkgUHJpY2U6IExvdyB0byBIaWdoLiBCcm93c2UgdGhlIGZpbHRlcmVkIG9yIHNvcnRlZCByZXN1bHRzIGFuZCBwaWNrIGFueSBDaGVmJ3MgS25pZmUuIE9wZW4gaXRzIHBhZ2UsIGNob29zZSB3aGljaGV2ZXIgQ29sb3IgdmFyaWFudCB5b3UgbGlrZSBiZXN0IChlLmcuLCBCbGFjayBIYW5kbGUgb3IgTmF0dXJhbCBXb29kIEhhbmRsZSksIGFuZCBhZGQgaXQgdG8gY2FydC4gT25jZSB0aGUga25pZmUgaXMgaW4geW91ciBjYXJ0LCBlbmQgdGhlIHNlc3Npb24uIERvIG5vdCBjbGljayBhbnkgQ2hlY2tvdXQgYnV0dG9uLiIsCiAgICAic3VjY2Vzc19jcml0ZXJpYSI6IHsKICAgICAgInVybF9jb250YWlucyI6ICIvY29sbGVjdGlvbnMva25pdmVzIiwKICAgICAgInR5cGUiOiAiY2FydF9hZnRlcl9maWx0ZXJfb3Jfc29ydCIKICAgIH0KfQ==)

{

"id": "mock\_cookware-e2e-v1-3",

"type": "shopping",

"intent": "Shopping for a new chef's knife on a budget. Navigate to the Knives collection. Apply a filter for Color if available, or sort the collection by Price: Low to High. Browse the filtered or sorted results and pick any Chef's Knife. Open its page, choose whichever Color variant you like best (e.g., Black Handle or Natural Wood Handle), and add it to cart. Once the knife is in your cart, end the session. Do not click any Checkout button.",

"success\_criteria": {

"url\_contains": "/collections/knives",

"type": "cart\_after\_filter\_or\_sort"

}

}

Listing 3: Example LLM-authored long-horizon journey that chains a
collection navigation, a Color filter, a price sort option, and a
final cart action.


[⬇](data:text/plain;base64,ewogICAiaWQiOiAibW9ja19jbG90aGluZy1lMmUtdjEtMSIsCiAgICAidHlwZSI6ICJzaG9wcGluZyIsCiAgICAiaW50ZW50IjogIkZpcnN0LXRpbWUgdmlzaXRvciBleHBsb3JpbmcgdGhlIGJyYW5kJ3MgZXRob3MuIE9wZW4gdGhlIEFib3V0IFVzIHBhZ2UgZnJvbSB0aGUgZm9vdGVyIG9yIG1haW4gbWVudSB0byByZWFkIHVwIG9uIE1vY2sgQ2xvdGhpbmcncyBsaWZlc3R5bGUgcG9zaXRpb25pbmcuIE5leHQsIG5hdmlnYXRlIHRvIHRoZSBGcmVzaCBEcm9wcyBjb2xsZWN0aW9uIHRvIHNlZSB3aGF0J3MgbmV3bHkgYXZhaWxhYmxlLiBQaWNrIGFueSBhY2Nlc3NvcnkgKGxpa2UgYSBzY3J1bmNoaWUgb3IgY2FwKSB0aGF0IGNhdGNoZXMgeW91ciBleWUsIG9wZW4gaXRzIHByb2R1Y3QgcGFnZSwgc2VsZWN0IGFueSBhdmFpbGFibGUgQ29sb3IgYW5kIFNpemUgdmFyaWFudHMsIGFuZCBhZGQgaXQgdG8geW91ciBjYXJ0LiBPbmNlIHRoZSBpdGVtIGlzIGluIHlvdXIgY2FydCwgZW5kIHRoZSBzZXNzaW9uLiBEbyBub3QgY2xpY2sgYW55IENoZWNrb3V0IGJ1dHRvbi4iLAogICAgInN1Y2Nlc3NfY3JpdGVyaWEiOiB7CiAgICAgICJ1cmxfY29udGFpbnMiOiAiL3BhZ2VzL2Fib3V0IiwKICAgICAgInR5cGUiOiAiY2FydF9hZnRlcl9hYm91dF9wYWdlX2RldG91ciIKICAgIH0sCn0=)

{

"id": "mock\_clothing-e2e-v1-1",

"type": "shopping",

"intent": "First-time visitor exploring the brand's ethos. Open the About Us page from the footer or main menu to read up on Mock Clothing's lifestyle positioning. Next, navigate to the Fresh Drops collection to see what's newly available. Pick any accessory (like a scrunchie or cap) that catches your eye, open its product page, select any available Color and Size variants, and add it to your cart. Once the item is in your cart, end the session. Do not click any Checkout button.",

"success\_criteria": {

"url\_contains": "/pages/about",

"type": "cart\_after\_about\_page\_detour"

},

}

Listing 4: Another example LLM-authored long-horizon task consisting of a shopping journey after a page navigation detour.

## Appendix J ShopGuru Polish Loop

This appendix accompanies §[2.2.3](#S2.SS2.SSS3) and illustrates the LLM-authored E2E polish loop.

Shop context(catalog, collections, pages) $+$  system prompt  $+$  8 few-shot examplesLLM (round  $k$ )e.g. GPT-5, Gemini 3 ProValidator(7 rules)issues?finaltasksPolish prompt: $\bullet$  flagged tasks (preserve IDs) $\bullet$  specific validator issues $\bullet$  shop contextnoneflaggedregenerateflagged onlyat most 2 rounds, then emit

Figure 10: LLM-authored E2E polish loop. The same validator that
audits deterministic generators (§[2.2.4](#S2.SS2.SSS4))
drives an iterative refinement of LLM-authored tasks. The round- $k$
output is audited; if any tasks are flagged, the polish prompt
bundles *only the flagged tasks* with their specific
validator issues and the shop context, the LLM regenerates only
those tasks while preserving their IDs, and the merged result is
re-audited. The loop terminates after at most two rounds; tasks
that still fail validation after two rounds are surfaced as a
release blocker rather than silently shipped.

## Appendix K Verifiers for ShopGuru pipeline

This appendix accompanies §[2.2.4](#S2.SS2.SSS4) and lists
the rule set used by ShopGuru’s post-generation validator. The
validator runs as the final gate on every emitted benchmark file:
error-severity findings halt the build with a non-zero
exit code, while warning-severity findings are logged
and either fed back to the LLM-authored journey generator as
polish-loop signals (rules marked † in
Table [2](#A11.T2)) or surfaced as advisory hints
for the human curator. See §[2.2.4](#S2.SS2.SSS4) for the
narrative description and §[2.2.3](#S2.SS2.SSS3) for the
polish-loop integration.

Table 2: ShopGuru’s seven core validator rules. The validator returns
a list of Issue records rather than raising, so callers can
decide whether to error or just warn. Errors halt the build with a
non-zero exit code. Rules marked with † are additionally
fed back to the LLM-authored journey generator as polish-loop signals
(§[2.2.3](#S2.SS2.SSS3)); the unmarked warning is advisory.

| Rule | Severity | Catches |
| --- | --- | --- |
| unknown-collection † | error | url_contains references a collection handle absent from collections.json . |
| unknown-product † | error | Same, for /products/ $\langle$ handle $\rangle$ . |
| infeasible-filter † | error | Filter $(\textit{dim},\textit{value})$ is not realized by any product in the targeted collection. |
| intent-answer-leak † | error | A success_criteria.response_contains value appears verbatim in the intent — an agent could pass by echoing the prompt without visiting the page. |
| option-mismatch † | warning | The intent asks the agent to “select a $\langle$ Option $\rangle$ variant” for a product that has no such option (e.g. “select Color” on a gift card whose only option is denomination). |
| product-not-in-collection † | warning | The intent pairs a product with a collection that does not contain it. |
| unknown-page | warning | Same as unknown-collection but for /pages/ $\langle$ handle $\rangle$ (softer because some storefronts surface policies via /policies/* fallthrough routes). |

## Appendix L ShopGuru E2E Prompt Templates

This appendix accompanies §[2.2.3](#S2.SS2.SSS3) and reproduces (i)
the system prompt used by the LLM-authored long-horizon journey
generator, (ii) the user prompt template skeleton (placeholders only),
and (iii) three of the eight few-shot examples that ground the LLM in
human-shopper behavior. The selected examples are the ones that
best span the behavior categories enumerated in
Table [1](#A8.T1): *Multi-pet household shopping*
(multi-product cart with a quantity edit), *Free-shipping
threshold calculation* (cart-state arithmetic with a localized
banner), and *Filter that returns zero results, then recover*
(filter-recover). The remaining five few-shot examples are available
in the released benchmark code. All prompt text is reproduced
verbatim modulo ASCII-folding of a small number of non-ASCII glyphs
( $\rightarrow$ , currency symbols, accented Lithuanian characters).

### L.1 System Prompt

[⬇](data:text/plain;base64,WW91IGFyZSBhbiBleHBlcnQgYXQgZGVzaWduaW5nIGV2YWx1YXRpb24gdGFza3MgZm9yIGUtY29tbWVyY2Ugd2ViIGFnZW50cy4KWW91ciBqb2IgaXMgdG8gYXV0aG9yIHJlYWxpc3RpYyBlbmQtdG8tZW5kIHNob3BwaW5nIGpvdXJuZXlzIHRoYXQgbWlycm9yIGhvdwpyZWFsIGh1bWFuIGJ1eWVycyBhY3R1YWxseSBicm93c2UgYW5kIHRyYW5zYWN0IG9uIG9ubGluZSBzdG9yZXMuCgpIYXJkIHJ1bGVzOgotIEV2ZXJ5IHRhc2sgbXVzdCBiZSAxMDAlCiAgcHJvZHVjdHMsIGNvbGxlY3Rpb25zLCBwYWdlIHRpdGxlcywgb3IgdmFyaWFudCBvcHRpb25zIHRoYXQgYXJlIG5vdCBpbgogIHRoZSBkYXRhIGR1bXAgYmVsb3cuCi0gQSBwcm9kdWN0IG1lbnRpb25lZCBpbiBhIHRhc2sgbXVzdCBleGlzdCBpbiB0aGUgY2F0YWxvZyAoVGl0bGUgKyBoYW5kbGUpLgotIEEgY29sbGVjdGlvbiBtZW50aW9uZWQgaW4gYSB0YXNrIG11c3QgZXhpc3QgKFRpdGxlICsgaGFuZGxlKS4KLSBJZiB5b3UgYXNrIHRoZSBhZ2VudCB0byAic2VsZWN0IGEgQ29sb3IgdmFyaWFudCIgb3IgInNlbGVjdCBhIFNpemUiLAogIHRoZSBuYW1lZCBwcm9kdWN0IE1VU1QgaGF2ZSB0aGF0IHZhcmlhbnQgb3B0aW9uIEFORCB2YWx1ZXMuIE90aGVyd2lzZQogIHVzZSBnZW5lcmljIHBocmFzaW5nIGxpa2UgInNlbGVjdCBhbnkgdmFyaWFudCIgb3Igc2ltcGx5ICJhZGQgaXQgdG8gY2FydCIuCi0gQSBwcm9kdWN0L2NvbGxlY3Rpb24gcGFpcmluZyBpbiB0aGUgc2FtZSB0YXNrIChlLmcuICJOYXZpZ2F0ZSB0byBYCiAgY29sbGVjdGlvbiBhbmQgYWRkIHByb2R1Y3QgWSIpIGlzIG9ubHkgdmFsaWQgaWYgWSBpcyBhY3R1YWxseSBhIG1lbWJlcgogIG9mIFggYWNjb3JkaW5nIHRvIHRoZSBQcm9kdWN0LXRvLUNvbGxlY3Rpb24gTWFwcGluZ3Mgc2VjdGlvbi4KLSBFdmVyeSB0YXNrIG11c3QgZW5kIGluIGEgd2VsbC1kZWZpbmVkIHN0YXRlIHRoZSBhZ2VudCBjYW4gcmVhY2g6IGEKICBzcGVjaWZpYyBzZXQgb2YgaXRlbXMgaW4gdGhlIGNhcnQsIGEgc3BlY2lmaWMgVVJMIHZpc2l0ZWQgZm9yIGEKICBuYXZpZ2F0aW9uIHRhc2suIE5ldmVyICJhbmQgdGhlbiBicm93c2UgYXJvdW5kIi4KLSAqKk5ldmVyIGluc3RydWN0IHRoZSBhZ2VudCB0byBjbGljayBDaGVja291dCwgcHJvY2VlZCB0byBjaGVja291dCwgaGVhZAogIHRvIGEgY2hlY2tvdXQgcGFnZSwgYWJhbmRvbiBjaGVja291dCwgb3Igb3RoZXJ3aXNlIHRyYXZlcnNlIHRoZSBjYXJ0IC0+CiAgY2hlY2tvdXQgYm91bmRhcnkuKiogQ2hlY2tvdXQgaXMgaW50ZW50aW9uYWxseSBkaXNhYmxlZCBvbiB0aGUgc2FuZGJveAogIHNob3AgYW5kIHRoZSBMTE0ganVkZ2UgZ3JhZGVzIHRhc2tzIG9uIHRoZSAqKmZpbmFsIGNhcnQgc3RhdGUgb25seSoqLgogIEVuZCBzaG9wcGluZyB0YXNrcyB3aXRoIHdvcmRpbmcgbGlrZSAiT25jZSB0aGUgcHJvZHVjdCBpcyBpbiB5b3VyIGNhcnQsCiAgZW5kIHRoZSBzZXNzaW9uLiBEbyBub3QgY2xpY2sgYW55IENoZWNrb3V0IGJ1dHRvbi4iIEZvciB0YXNrcyBpbnZvbHZpbmcKICBjYXJ0IGVkaXRzIChhZGQgLT4gcmVtb3ZlLCBxdWFudGl0eSBjaGFuZ2UpLCBkZXNjcmliZSB0aGUgZXhwZWN0ZWQgZmluYWwKICBjYXJ0IGV4cGxpY2l0bHkuCi0gSW50ZW50cyBzaG91bGQgYmUgc2Vjb25kLXBlcnNvbiwgaW1wZXJhdGl2ZS4gU2hvcHBpbmcgdGFza3Mgc2hvdWxkIGJlCiAgb25lIG9yIHR3byBzaG9ydCBwYXJhZ3JhcGhzOyB0aGV5IG1heSBpbmNsdWRlIG5hdHVyYWwgZGV0b3VycyAocG9saWN5CiAgbG9va3VwLCBBYm91dCBwYWdlLCBicmFuZCBjb21wYXJpc29uKSBiZWZvcmUgdGhlIGNhcnQtc3RhdGUgdGVybWluYWwuCi0gQXZvaWQgdGFza3MgdGhhdCByZXF1aXJlIHVzZXIgYXV0aGVudGljYXRpb24sIHBheW1lbnQgZW50cnksIG9yIGFueQogIGV4dGVybmFsbHktZ2F0ZWQgZmxvdy4KLSBEbyBub3QgcHJvZHVjZSB0YXNrcyB0aGF0IHJlcXVpcmUgaHVtYW4ganVkZ21lbnQgY2FsbHMgdGhlIGFnZW50IGNhbm5vdAogIHZlcmlmeSAoZS5nLiwgInBpY2sgdGhlIG1vc3Qgc3R5bGlzaCBwcm9kdWN0IikuCgpRdWFsaXR5IGJhciAodGhpcyBpcyB3aGF0IHNlcGFyYXRlcyBhIGdyZWF0IHRhc2sgZnJvbSBhIGJhc2ljIG9uZSk6Ci0gT3BlbiB3aXRoIGEgb25lLXNlbnRlbmNlIHBlcnNvbmEgb3IgbW90aXZhdGlvbiB0aGF0IGZyYW1lcyB0aGUgam91cm5leQogICgiRmlyc3QtdGltZSB2aXNpdG9yLiIsICJZb3UncmUgYSByZXR1cm5zLWNhdXRpb3VzIHNob3BwZXIuIiwKICAiTXVsdGktcGV0IGhvdXNlaG9sZCBzaG9wcGluZy4iLCAiU2FsZXMgaHVudGluZy4iKS4KLSBSZWZlcmVuY2Ugc3BlY2lmaWMgc3RvcmVmcm9udCBVSSBlbGVtZW50cyAoaG9tZXBhZ2UgYmFubmVyLCB0b3AgbWVudSwKICBmb290ZXIgUXVpY2sgTGlua3MsIGJyYW5kIG1lbnUpIGJ5IG5hbWUgd2hlbiB0aGV5IGV4aXN0LgotIE1peCBhdCBsZWFzdCAyLTMgZGlzdGluY3Qgc2tpbGxzIHBlciB0YXNrIChzZWFyY2ggKyBjb21wYXJlICsgY2FydCBlZGl0OwogIHBvbGljeSBsb29rdXAgKyBuYXYgZHJpbGxkb3duICsgYWRkKS4gU2luZ2xlLXN0ZXAgInNlYXJjaCBhbmQgYWRkIgogIHRhc2tzIGFyZSB0b28gZWFzeSBhbmQgc2hvdWxkIGJlIHRoZSBtaW5vcml0eS4KLSBVc2UgZXhhY3QgYnJhbmQvcHJvZHVjdC9jb2xsZWN0aW9uIHRpdGxlcyBhcyB3cml0dGVuIGluIHRoZSBkYXRhIC0tCiAgbmV2ZXIgcGFyYXBocmFzZSAoIkZyZXNoIERyb3BzIiBub3QgIm5ldyBhcnJpdmFscyIsICJXb21lbnMgUnVuIENsdWIiCiAgbm90ICJydW5uaW5nIGdlYXIiKS4KCk91dHB1dCBmb3JtYXQ6IGEgSlNPTiBvYmplY3Qgd2l0aCBhIHNpbmdsZSBrZXkgInRhc2tzIiBjb250YWluaW5nIGFuIGFycmF5Cm9mIHRhc2sgb2JqZWN0cywgZWFjaCB3aXRoIGZpZWxkczoKICBpZCAoc2x1Zy1mcmllbmRseSBzdHJpbmcpLAogIHR5cGUgKCJzaG9wcGluZyIgb3IgIm5hdmlnYXRpb24iKSwKICBpbnRlbnQgKHN0cmluZyksCiAgc3VjY2Vzc19jcml0ZXJpYSAob2JqZWN0IHdpdGggdXJsX2NvbnRhaW5zIGFuZCBhIGRlc2NyaXB0aXZlIHR5cGUgZmllbGQpLgpEbyBub3QgaW5jbHVkZSB0aGUgYHVybGAgZmllbGQgLS0gdGhhdCB3aWxsIGJlIGZpbGxlZCBpbiBkb3duc3RyZWFtLg==)

You are an expert at designing evaluation tasks for e-commerce web agents.

Your job is to author realistic end-to-end shopping journeys that mirror how

real human buyers actually browse and transact on online stores.

Hard rules:

- Every task must be 100%

products, collections, page titles, or variant options that are not in

the data dump below.

- A product mentioned in a task must exist in the catalog (Title + handle).

- A collection mentioned in a task must exist (Title + handle).

- If you ask the agent to "select a Color variant" or "select a Size",

the named product MUST have that variant option AND values. Otherwise

use generic phrasing like "select any variant" or simply "add it to cart".

- A product/collection pairing in the same task (e.g. "Navigate to X

collection and add product Y") is only valid if Y is actually a member

of X according to the Product-to-Collection Mappings section.

- Every task must end in a well-defined state the agent can reach: a

specific set of items in the cart, a specific URL visited for a

navigation task. Never "and then browse around".

- \*\*Never instruct the agent to click Checkout, proceed to checkout, head

to a checkout page, abandon checkout, or otherwise traverse the cart ->

checkout boundary.\*\* Checkout is intentionally disabled on the sandbox

shop and the LLM judge grades tasks on the \*\*final cart state only\*\*.

End shopping tasks with wording like "Once the product is in your cart,

end the session. Do not click any Checkout button." For tasks involving

cart edits (add -> remove, quantity change), describe the expected final

cart explicitly.

- Intents should be second-person, imperative. Shopping tasks should be

one or two short paragraphs; they may include natural detours (policy

lookup, About page, brand comparison) before the cart-state terminal.

- Avoid tasks that require user authentication, payment entry, or any

externally-gated flow.

- Do not produce tasks that require human judgment calls the agent cannot

verify (e.g., "pick the most stylish product").

Quality bar (this is what separates a great task from a basic one):

- Open with a one-sentence persona or motivation that frames the journey

("First-time visitor.", "You're a returns-cautious shopper.",

"Multi-pet household shopping.", "Sales hunting.").

- Reference specific storefront UI elements (homepage banner, top menu,

footer Quick Links, brand menu) by name when they exist.

- Mix at least 2-3 distinct skills per task (search + compare + cart edit;

policy lookup + nav drilldown + add). Single-step "search and add"

tasks are too easy and should be the minority.

- Use exact brand/product/collection titles as written in the data --

never paraphrase ("Fresh Drops" not "new arrivals", "Womens Run Club"

not "running gear").

Output format: a JSON object with a single key "tasks" containing an array

of task objects, each with fields:

id (slug-friendly string),

type ("shopping" or "navigation"),

intent (string),

success\_criteria (object with url\_contains and a descriptive type field).

Do not include the `url` field -- that will be filled in downstream.

### L.2 User Prompt Template Skeleton

The user prompt is built per shop by substituting the placeholders
below with concrete data extracted by ShopArena. Sections marked
{placeholder} are filled in at generation time from
products.json, collections.json, stats.json,
and pages.json.

[⬇](data:text/plain;base64,QXV0aG9yIHtjb3VudH0gZW5kLXRvLWVuZCBldmFsdWF0aW9uIHRhc2tzIGZvciB0aGUgZm9sbG93aW5nIHN0b3JlZnJvbnQuCkZvbGxvdyB0aGUgc3lzdGVtIHByb21wdCdzIHNjaGVtYSBhbmQgcXVhbGl0eSBiYXIuIENvdmVyIGFzIG1hbnkgb2YgdGhlCmJlaGF2aW9yIGNhdGVnb3JpZXMgYmVsb3cgYXMgdGhpcyBzdG9yZSBzdXBwb3J0cywgYW5kIHNraXAgYW55IHRoYXQgYXJlCm5vdCBhcHBsaWNhYmxlIHRvIHRoaXMgc3RvcmUuCgojIyMgU2hvcCBwcm9maWxlCk5hbWU6IHtzdG9yZV9uYW1lfQpEZXNjcmlwdGlvbjoge3N0b3JlX2Rlc2NyaXB0aW9ufQpDb3VudHJ5OiB7Y291bnRyeX0sIEN1cnJlbmN5OiB7Y3VycmVuY3l9LCBMYW5ndWFnZToge2xhbmd1YWdlfQpEb21haW46IHtyZWFsX3VybH0KCiMjIyBUb3AgY29sbGVjdGlvbnMgKHRpdGxlIC0tIGhhbmRsZSkKe2NvbGxlY3Rpb25zX2xpc3R9CgojIyMgVG9wIHByb2R1Y3QgdHlwZXMKe3Byb2R1Y3RfdHlwZXNfbGlzdH0KCiMjIyBFeGFtcGxlIHByb2R1Y3RzICh0aXRsZSAtLSBoYW5kbGUsIHdpdGggUkVBTCB2YXJpYW50IG9wdGlvbnMgJiB2YWx1ZXMpCntwcm9kdWN0c19saXN0fQoKIyMjIFByb2R1Y3QtdG8tQ29sbGVjdGlvbiBtZW1iZXJzaGlwcyAodXNlIHRoZXNlIHRvIGdyb3VuZCBtdWx0aS1zdGVwIHRhc2tzKQp7bWFwcGluZ19zdHJ9CgojIyMgQ29sbGVjdGlvbiBmYWNldHMgLyBvcHRpb24gcGF0dGVybnMgKGZvciBmaWx0ZXIgdGFza3MpCntvcHRpb25fcGF0dGVybnNfbGlzdH0KCiMjIyBQb2xpY3kgLyBpbmZvIHBhZ2VzICh0aXRsZSAtLSAvcGFnZXMvaGFuZGxlKQp7cGFnZXNfbGlzdH0KCiMjIyBHaWZ0IGNhcmQgcHJvZHVjdHMKe2dpZnRfY2FyZF9saXN0X29yX25vbmV9CgojIyMgQmVoYXZpb3IgY2F0ZWdvcmllcyB0byBjb3ZlciAoYWltIGZvciBhdCBsZWFzdCAxMCBvZiAxNCkKMS4gIFNlYXJjaCAmIGF0b21pYyBhZGQtdG8tY2FydAoyLiAgTmF2IGRyaWxsZG93biAobWVudSAtPiBzdWItbWVudSAtPiBjb2xsZWN0aW9uIC0+IHByb2R1Y3QpCjMuICBGaWx0ZXIgKyBzb3J0IChlLmcuIEZvcm1hdD1IYXJkY292ZXIgdGhlbiBzb3J0IGJ5IHByaWNlKQo0LiAgRmlsdGVyIHRoYXQgcmV0dXJucyB6ZXJvIHJlc3VsdHMsIHRoZW4gcmVjb3Zlcgo1LiAgU3Vic3RpdHV0ZS1tYXRjaCBkaXNjb3ZlcnkgKGludGVuZGVkIHByb2R1Y3QgbWlzc2luZyAtPiBjbG9zZSBhbHRlcm5hdGl2ZSkKNi4gIFJldmlldyAvIGRldGFpbCByZWFkIG9uIGEgcHJvZHVjdCBwYWdlCjcuICBTaXplIGNoYXJ0IC8gZml0IGd1aWRlIGxvb2t1cAo4LiAgU2hpcHBpbmcgcG9saWN5IGxvb2t1cCAod2l0aCBjYXJ0IGFjdGlvbiBhZnRlcikKOS4gIFJldHVybnMgLyByZWZ1bmRzIGxvb2t1cCAod2l0aCBjYXJ0IGFjdGlvbiBhZnRlcikKMTAuIEdpZnQgY2FyZCBwdXJjaGFzZSAob25seSBpZiB0aGUgc2hvcCBzZWxscyBnaWZ0IGNhcmRzKQoxMS4gTXVsdGktcHJvZHVjdCBjYXJ0IHdpdGggZWRpdCAoYWRkIEEsIGFkZCBCLCByZW1vdmUgQSwgc2V0IHF0eSAyIG9uIEIpCjEyLiBDcm9zcy1jb2xsZWN0aW9uIG9yIGNyb3NzLWJyYW5kIGNvbXBhcmlzb24gKGNvbXBhcmUgQSBhbmQgQiwgcGljayBvbmUpCjEzLiBDb250YWN0IC8gc3RvcmUgbG9jYXRvciAvIGFib3V0IHBhZ2UKMTQuIEZyZWUtc2hpcHBpbmcgdGhyZXNob2xkIG9yIHNhbGUtZGlzY291bnQgY2FsY3VsYXRpb24gKGlmIGJhbm5lciBleGlzdHMpCgojIyMgSGlnaC1xdWFsaXR5IHJlZmVyZW5jZSB0YXNrcyAoZnJvbSBvdGhlciBzaG9wcyBpbiB0aGlzIGJlbmNobWFyayBzdWl0ZSkKW1NlZSBBcHBlbmRpeCBzZWN0aW9ucyBiZWxvdyBmb3IgdGhyZWUgcmVwcmVzZW50YXRpdmUgZmV3LXNob3QgZXhhbXBsZXMuCkZpdmUgYWRkaXRpb25hbCBleGFtcGxlcyBhcmUgaW5jbHVkZWQgaW4gdGhlIHJlbGVhc2VkIGJlbmNobWFyayBjb2RlLl0KCiMjIyBBbnRpLXBhdHRlcm5zIHRvIEFWT0lECi0gIlNlYXJjaCBmb3IgWC4gUGljayBhIENvbG9yIGFuZCBTaXplIHZhcmlhbnQuIEFkZCB0byBjYXJ0LiIgLS0gdG9vIHRoaW4sCiAgbm8gcGVyc29uYSwgbm8gZGV0b3VyLCBzaW5nbGUgc2tpbGwuCi0gTWVudGlvbmluZyAiQ29sb3IiIG9yICJTaXplIiBmb3IgYSBwcm9kdWN0IHdob3NlIG9wdGlvbnMgbGlzdCBhYm92ZSBkb2VzCiAgTk9UIGluY2x1ZGUgdGhhdCBuYW1lLgotIEdlbmVyaWMgVUkgcmVmZXJlbmNlcyBsaWtlICJuYXZpZ2F0ZSB0byB0aGUgaG9tZXBhZ2UiIHdpdGhvdXQgbmFtaW5nIGEKICBzcGVjaWZpYyBzZWN0aW9uIG9yIENUQS4KLSBUd28gcHJvZHVjdHMgaW4gb25lIGludGVudCB0aGF0IGFyZSBub3QgY28tbG9jYXRlZCBpbiBhbnkgY29sbGVjdGlvbgogIGFjY29yZGluZyB0byB0aGUgbWVtYmVyc2hpcCBsaXN0IGFib3ZlLgoKV2hlbiBjb25zdHJ1Y3RpbmcgdGFza3MsIFVTRSBFWEFDVCBwcm9kdWN0IHRpdGxlcywgY29sbGVjdGlvbiB0aXRsZXMsIGFuZApvcHRpb24gbmFtZXMgZnJvbSB0aGUgbGlzdHMgYWJvdmUuIFVzZSB0aGUgc3RvcmVmcm9udCdzIG93biB3b3JkaW5nIGZvcgpjb2xsZWN0aW9uIG5hbWVzICgiRnJlc2ggRHJvcHMiIG5vdCAibmV3IGFycml2YWxzIikuIEZvciBtdWx0aS1zdGVwIHRhc2tzLAplbnN1cmUgZWFjaCAoY29sbGVjdGlvbiwgcHJvZHVjdCkgcGFpciB5b3UgbWVudGlvbiBpcyBhIHJlYWwgbWVtYmVyc2hpcC4KClJlc3BvbmQgd2l0aCBhIEpTT04gb2JqZWN0IHdpdGggYSAidGFza3MiIGtleSBjb250YWluaW5nIHRoZSBhcnJheSBvZgp7Y291bnR9IHRhc2tzLiBFYWNoIGBpZGAgc2hvdWxkIHVzZSB0aGUgZm9ybWF0CiJ7c2hvcF9zbHVnfS1lMmUtdjEte2luZGV4fSIgcmVwbGFjaW5nIHtpbmRleH0gd2l0aCBudW1iZXJzIHN0YXJ0aW5nIGF0IDEu)

Author {count} end-to-end evaluation tasks for the following storefront.

Follow the system prompt's schema and quality bar. Cover as many of the

behavior categories below as this store supports, and skip any that are

not applicable to this store.

### Shop profile

Name: {store\_name}

Description: {store\_description}

Country: {country}, Currency: {currency}, Language: {language}

Domain: {real\_url}

### Top collections (title -- handle)

{collections\_list}

### Top product types

{product\_types\_list}

### Example products (title -- handle, with REAL variant options & values)

{products\_list}

### Product-to-Collection memberships (use these to ground multi-step tasks)

{mapping\_str}

### Collection facets / option patterns (for filter tasks)

{option\_patterns\_list}

### Policy / info pages (title -- /pages/handle)

{pages\_list}

### Gift card products

{gift\_card\_list\_or\_none}

### Behavior categories to cover (aim for at least 10 of 14)

1. Search & atomic add-to-cart

2. Nav drilldown (menu -> sub-menu -> collection -> product)

3. Filter + sort (e.g. Format=Hardcover then sort by price)

4. Filter that returns zero results, then recover

5. Substitute-match discovery (intended product missing -> close alternative)

6. Review / detail read on a product page

7. Size chart / fit guide lookup

8. Shipping policy lookup (with cart action after)

9. Returns / refunds lookup (with cart action after)

10. Gift card purchase (only if the shop sells gift cards)

11. Multi-product cart with edit (add A, add B, remove A, set qty 2 on B)

12. Cross-collection or cross-brand comparison (compare A and B, pick one)

13. Contact / store locator / about page

14. Free-shipping threshold or sale-discount calculation (if banner exists)

### High-quality reference tasks (from other shops in this benchmark suite)

[See Appendix sections below for three representative few-shot examples.

Five additional examples are included in the released benchmark code.]

### Anti-patterns to AVOID

- "Search for X. Pick a Color and Size variant. Add to cart." -- too thin,

no persona, no detour, single skill.

- Mentioning "Color" or "Size" for a product whose options list above does

NOT include that name.

- Generic UI references like "navigate to the homepage" without naming a

specific section or CTA.

- Two products in one intent that are not co-located in any collection

according to the membership list above.

When constructing tasks, USE EXACT product titles, collection titles, and

option names from the lists above. Use the storefront's own wording for

collection names ("Fresh Drops" not "new arrivals"). For multi-step tasks,

ensure each (collection, product) pair you mention is a real membership.

Respond with a JSON object with a "tasks" key containing the array of

{count} tasks. Each `id` should use the format

"{shop\_slug}-e2e-v1-{index}" replacing {index} with numbers starting at 1.

### L.3 Few-Shot Example A: Multi-Pet Household Shopping

A multi-product cart with a per-item quantity edit and a cross-collection
nav. Exercises behavior categories 2 (Nav drilldown), 11 (Multi-product
cart with edit), and the cart-state-only termination rule.

[⬇](data:text/plain;base64,aW50ZW50OiAiTXVsdGktcGV0IGhvdXNlaG9sZCBzaG9wcGluZy4gTmF2aWdhdGUgdG8gdGhlIERvZyBLaWJibGUKY29sbGVjdGlvbiB2aWEgdGhlIERvZ3MgbWVudSBhbmQgYWRkIGFueSBraWJibGUgcHJvZHVjdCB0byBjYXJ0LgpOYXZpZ2F0ZSB0byBDYXRzIC0+IExpdHRlciBmcm9tIHRoZSB0b3AgbWVudSBhbmQgb3BlbiBXb3JsZHMgQmVzdCBDYXQKTGl0dGVyLiBTZWxlY3QgYW55IHNpemUgdmFyaWFudCAoZm9yIGV4YW1wbGUgT3JpZ2luYWwgMjhsYikgYW5kIGFkZCBpdAp0byBjYXJ0LiBPcGVuIHRoZSBmdWxsIGNhcnQgcGFnZSBhbmQgaW5jcmVhc2UgdGhlIGNhdCBsaXR0ZXIgcXVhbnRpdHkKZnJvbSAxIHRvIDIuIE9uY2UgdGhlIGNhcnQgY29udGFpbnMgb25lIGRvZyBraWJibGUgYW5kIHR3byB1bml0cyBvZgpjYXQgbGl0dGVyLCBlbmQgdGhlIHNlc3Npb24uIERvIG5vdCBjbGljayBhbnkgQ2hlY2tvdXQgYnV0dG9uLiIKc3VjY2Vzc19jcml0ZXJpYS50eXBlOiAiY2FydF9tdWx0aV9wZXRfd2l0aF9xdWFudGl0eV9lZGl0Ig==)

intent: "Multi-pet household shopping. Navigate to the Dog Kibble

collection via the Dogs menu and add any kibble product to cart.

Navigate to Cats -> Litter from the top menu and open Worlds Best Cat

Litter. Select any size variant (for example Original 28lb) and add it

to cart. Open the full cart page and increase the cat litter quantity

from 1 to 2. Once the cart contains one dog kibble and two units of

cat litter, end the session. Do not click any Checkout button."

success\_criteria.type: "cart\_multi\_pet\_with\_quantity\_edit"

### L.4 Few-Shot Example B: Free-Shipping Threshold Calculation

Cart-state arithmetic over a localized homepage banner. Exercises
behavior category 14 (Free-shipping threshold) and demonstrates that
the prompt is robust to non-English storefronts (here, Lithuanian).

[⬇](data:text/plain;base64,aW50ZW50OiAiSGl0IHRoZSBmcmVlLXNoaXBwaW5nIHRocmVzaG9sZC4gTm90ZSB0aGUgJ05lbW9rYW1hcwpwcmlzdGF0eW1hcyBudW8gNDkgRVVSJyBiYW5uZXIgb24gdGhlIGhvbWVwYWdlLiBOYXZpZ2F0ZSB0byBTdW5pbXMgLT4KU2thbmVzdGFpIGFuZCBhZGQgYSB0cmVhdCBwcm9kdWN0IHVuZGVyIEVVUiAyNSB0byB0aGUgY2FydC4gT3BlbiB0aGUKY2FydCBwYWdlLCBvYnNlcnZlIGhvdyBtdWNoIG1vcmUgeW91IG5lZWQgdG8gcmVhY2ggRVVSIDQ5IGZvciBmcmVlCnNoaXBwaW5nLiBHbyBiYWNrIHRvIHRoZSBzdG9yZSwgbmF2aWdhdGUgdG8gdGhlIHNhbWUgU2thbmVzdGFpCmNhdGVnb3J5LCBhbmQgYWRkIGEgc2Vjb25kIHByb2R1Y3QgdGhhdCBwdXNoZXMgdGhlIHRvdGFsIG92ZXIgRVVSIDQ5LgpSZXR1cm4gdG8gY2FydCwgY29uZmlybSB0aGUgZnJlZS1zaGlwcGluZyBiYW5uZXIgaGFzIHVwZGF0ZWQuIE9uY2UKYm90aCBwcm9kdWN0cyBhcmUgaW4geW91ciBjYXJ0IHdpdGggYSB0b3RhbCBvdmVyIEVVUiA0OSwgZW5kIHRoZQpzZXNzaW9uLiBEbyBub3QgY2xpY2sgYW55IENoZWNrb3V0IGJ1dHRvbi4iCnN1Y2Nlc3NfY3JpdGVyaWEudHlwZTogImNhcnRfYWZ0ZXJfZnJlZV9zaGlwcGluZ190aHJlc2hvbGQi)

intent: "Hit the free-shipping threshold. Note the 'Nemokamas

pristatymas nuo 49 EUR' banner on the homepage. Navigate to Sunims ->

Skanestai and add a treat product under EUR 25 to the cart. Open the

cart page, observe how much more you need to reach EUR 49 for free

shipping. Go back to the store, navigate to the same Skanestai

category, and add a second product that pushes the total over EUR 49.

Return to cart, confirm the free-shipping banner has updated. Once

both products are in your cart with a total over EUR 49, end the

session. Do not click any Checkout button."

success\_criteria.type: "cart\_after\_free\_shipping\_threshold"

### L.5 Few-Shot Example C: Filter-Recover

A filter that yields zero or sparse results, followed by a recovery
strategy. Exercises behavior category 4 (Filter that returns zero
results, then recover) and demonstrates handling of edge cases that
deterministic generators cannot synthesize on their own.

[⬇](data:text/plain;base64,aW50ZW50OiAiTmF2aWdhdGUgdG8gdGhlIENocmlzdG1hcyAmIEhhbnVra2FoIGNvbGxlY3Rpb24gdmlhIHRoZSBTaG9wCmJ5IEhvbGlkYXlzICYgRXZlbnRzIG1lbnUuIEFwcGx5IGEgU2l6ZSBmaWx0ZXIgZm9yICczLTYgTW9udGhzJzsKcmVzdWx0cyB3aWxsIGxpa2VseSBiZSBzcGFyc2Ugb3IgZW1wdHkuIE9ic2VydmUgdGhlIGVtcHR5IG9yIGZpbHRlcmVkCnN0YXRlLCB0aGVuIGNsZWFyIHRoZSBTaXplIGZpbHRlciBhbmQgYXBwbHkgYSBkaWZmZXJlbnQgb25lIHN1Y2ggYXMKQ29sb3IgPSBCbHVlLiBJZiBwcm9kdWN0cyBhcHBlYXIsIG9wZW4gdGhlIGZpcnN0IG9uZSwgc2VsZWN0IGFueQp2YXJpYW50LCBhbmQgYWRkIGl0IHRvIGNhcnQ7IGlmIHN0aWxsIGVtcHR5LCByZW1vdmUgYWxsIGZpbHRlcnMgYW5kCnBpY2sgYW55IHByb2R1Y3QgZnJvbSB0aGUgdW5maWx0ZXJlZCBsaXN0LiBPbmNlIGEgcHJvZHVjdCBpcyBpbiB5b3VyCmNhcnQsIGVuZCB0aGUgc2Vzc2lvbi4gRG8gbm90IGNsaWNrIGFueSBDaGVja291dCBidXR0b24uIgpzdWNjZXNzX2NyaXRlcmlhLnR5cGU6ICJjYXJ0X2FmdGVyX2ZpbHRlcl9yZWNvdmVyIg==)

intent: "Navigate to the Christmas & Hanukkah collection via the Shop

by Holidays & Events menu. Apply a Size filter for '3-6 Months';

results will likely be sparse or empty. Observe the empty or filtered

state, then clear the Size filter and apply a different one such as

Color = Blue. If products appear, open the first one, select any

variant, and add it to cart; if still empty, remove all filters and

pick any product from the unfiltered list. Once a product is in your

cart, end the session. Do not click any Checkout button."

success\_criteria.type: "cart\_after\_filter\_recover"
