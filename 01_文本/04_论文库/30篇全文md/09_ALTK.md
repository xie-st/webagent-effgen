---
title: "Agent Lifecycle Toolkit (ALTK): Reusable Middleware Components for Robust AI Agents"
arxiv_html: https://arxiv.org/html/2603.15473v2
downloaded: 2026-10-29
converted: arxiv LaTeXML HTML -> Markdown（本地图片 + alttext 公式还原）
---

# Agent Lifecycle Toolkit (ALTK): Reusable Middleware Components for Robust AI Agents

Conference: Proceedings of the 1st ACM Conference on Agentic and AI Systems; May 26, 2026; San Jose, CA, USAProceedings of the 1st ACM Conference on Agentic and AI Systems (CAIS ’26), May 26, 2026, San Jose, CA, USADOI: [10.1145/3786335.3813206](https://doi.org/10.1145/3786335.3813206)ISBN: 979-8-4007-2415-2/26/05CCS: Computing methodologies Intelligent agentsCCS: Software and its engineering Software libraries and repositories

- **Zidane Wright** · IBM Research , New York , NY , USA
- **Jason Tsay** · IBM Research , New York , NY , USA; Corresponding author. · jason.tsay@ibm.com
- **Anupama Murthi** · IBM Research , New York , NY , USA
- **Osher Elhadad** · IBM Research , Haifa , Israel
- **Diego Del Rio** · IBM , Argentina
- **Saurabh Goyal** · IBM Research , New York , NY , USA
- **Kiran Kate** · IBM Research , New York , NY , USA
- **Jim Laredo** · IBM Research , New York , NY , USA
- **Koren Lazar** · IBM Research , Haifa , Israel
- **Vinod Muthusamy** · IBM Research , New York , NY , USA
- **Yara Rizk** · IBM Research , New York , NY , USA

Received  13 March 2026

###### Abstract.

As AI agents move from demos into enterprise deployments, their failure modes become consequential: a misinterpreted tool argument can corrupt production data, a silent reasoning error can go undetected until damage is done, and outputs that violate organizational policy can create legal or compliance risk. Yet, most agent frameworks leave builders to handle these failure modes ad hoc, resulting in brittle, one-off safeguards that are hard to reuse or maintain. We present the Agent Lifecycle Toolkit (ALTK), an open-source collection of modular middleware components that systematically address these gaps across the full agent lifecycle.

Across the agent lifecycle, we identify opportunities to intervene and improve, namely, post-user-request, pre-LLM prompt conditioning, post-LLM output processing, pre-tool validation, post-tool result checking, and pre-response assembly. ALTK provides modular middleware that detects, repairs, and mitigates common failure modes. It offers consistent interfaces that fit naturally into existing pipelines. It is compatible with low-code and no-code tools such as the ContextForge MCP Gateway and Langflow. Finally, it significantly reduces the effort of building reliable, production-grade agents.

###### Keywords:

AI Systems, AI Agents, Agentic Middleware

## 1. Introduction

The agentic paradigm has accelerated rapidly as developers build increasingly capable LLM-powered agents that can reason, call tools, and produce structured outputs. Yet, these systems remain fundamentally brittle: as complexity grows, so do issues like hallucinated tool calls, silent failures, inconsistent outputs, and reasoning errors that break workflows. To address these challenges, we introduce ALTK, an open-source, framework-agnostic package that improves agent reliability, predictability, and production readiness. Agent Lifecycle Toolkit (ALTK) can integrate into any agent pipeline and add deterministic safeguards and recovery mechanisms that elevate agents from “cool demos” to dependable, enterprise-grade systems.

Early agents often rely on a simple loop of repeated LLM tool calls, useful for prototypes but insufficient for enterprise reliability. Production agents need additional logic to ensure robustness, especially in domains like sales where a single misinterpreted field can trigger incorrect APIs and distort downstream forecasts. Agent orchestration frameworks such as
LangChain ([Chase, 2022](#bib.bib11)), LangGraph ([LangChain, 2024b](#bib.bib12)), CrewAI ([Moura, 2023](#bib.bib16)) offer building blocks such as tools, memory, and popular agent architectures. However, they expect the developers to write custom code handling tool call errors or checking for policy conformance.

ALTK is a modular toolkit that comes with pre-built, hardened drop-in components to strengthen reasoning, tool execution, and output validation in agents. Rather than enforcing a particular agent framework (such as LangChain, LangGraph, or AutoGPT), its framework-agnostic design allows teams to introduce targeted reliability improvements without re-architecting their agents.

ALTK currently includes 10 components, each addressing a distinct failure mode in the agent lifecycle, as summarized in Figure [1](#S2.F1). For example, the lifecycle stage of "Pre-Tool" indicates a step in the agent’s execution when the LLM has generated a tool call but the tool call is yet to be executed. A "Pre-Tool" ALTK component such as SPARC takes the generated tool call, tool specifications, and agent context as input and performs different checks on the tool call to check for correctness. SPARC flags an invalid tool call with reasoning and suggestions for correcting it so the agent skips executing the wrong tool call and asks the LLM to take this feedback and generate a correct call.

What distinguishes ALTK is its flexibility through precise, surgical improvements rather than all-in-one orchestration. This allows for multiple paths of integration into existing agentic systems, including existing low-code and no-code systems such as LangFlow and the ContextForge MCP Gateway. All ALTK components have been rigorously evaluated on public benchmarks and show clear gains over baseline settings.

## 2. Toolkit Approach

ALTK is organized around key stages in the agent lifecycle, as shown in Figure [1](#S2.F1): build-time, pre-LLM prompt preparation, post-LLM, pre-tool call, post-tool call, and pre-final response. The main design goals are *separation of concerns* and *modularity*: each component targets one dominant error mode and can be enabled independently or in combination with others.

![Refer to caption](images/09_ALTK/altk_component_diagram.png)


Figure 1. Agent lifecycle and corresponding ALTK components

ALTK is currently implemented as an open source Python library called *altk-boost* that provides a simple interface into these lifecycle components. We intend for this library and its components to be plug-and-play and as framework-agnostic as possible. Integrating an ALTK component into an agent during runtime has three phases which can be done in three lines of code: 1) defining the input to the component, 2) instantiating and configuring the component, and 3) processing the given input and reviewing the result. Concretely, for the code example in Figure [2](#acmlabel1), we use the Silent Error Review component in the ALTK as a post-tool hook to check for silent errors in a problematic tool. This component expects the current log of messages and tool response as input and then after instantiating the Silent Error Review component, these messages are processed and a result is given whether or not a silent error was detected. This result can be given back to the agent to prevent unintended behavior. Each component in the ALTK library follows the same basic interface and phases. The library is available on GitHub11
1
https://github.com/AgentToolkit/altk-boost and PyPi22
2
https://pypi.org/project/altk-boost/. For more code examples, please see the *examples* folder in repository. A video walkthrough33
3
https://www.youtube.com/watch?v=FsTuf9fmgM4 is available with additional demonstration videos on the ALTK YouTube channel44
4
https://www.youtube.com/@AgentToolkit.

[⬇](data:text/plain;base64,ZGVmIHBvc3RfdG9vbF9ob29rKHN0YXRlOiBBZ2VudFN0YXRlKSAtPiBkaWN0OgogICAgIyBQb3N0LXRvb2wgbm9kZSB0byBjaGVjayB0aGUgb3V0cHV0IG9mIGEgcHJvYmxlbWF0aWMgdG9vbAogICAgdG9vbF9yZXNwb25zZSA9IHN0YXRlWyJtZXNzYWdlcyJdWy0xXS50b29sX291dHB1dHMKICAgIHJldmlld19pbnB1dCA9IFNpbGVudFJldmlld1J1bklucHV0KG1lc3NhZ2VzPXN0YXRlWyJtZXNzYWdlcyJdLCB0b29sX3Jlc3BvbnNlPXRvb2xfcmVzcG9uc2UpCiAgICByZXZpZXdlciA9IFNpbGVudFJldmlld0ZvckpTT05EYXRhQ29tcG9uZW50KCkKICAgIHJldmlld19yZXN1bHQgPSByZXZpZXdlci5wcm9jZXNzKGRhdGE9cmV2aWV3X2lucHV0LCBwaGFzZT1BZ2VudFBoYXNlLlJVTlRJTUUpCiAgICBpZiByZXZpZXdfcmVzdWx0Lm91dGNvbWUgPT0gT3V0Y29tZS5OT1RfQUNDT01QTElTSEVEOgogICAgICAgIHJldHVybiAiU2lsZW50IGVycm9yIGRldGVjdGVkLCByZXRyeSB0aGUgdG9vbCEiCiAgICBlbHNlOgogICAgICAgICMgKGFsbG93IHRvb2wgY2FsbCB0byBnbyB0aHJvdWdoKQoKYWdlbnRfZ3JhcGguYWRkX2VkZ2UoImZsYWt5X3Rvb2wiLCAicG9zdF90b29sX2hvb2siKQ==)

def post\_tool\_hook(state: AgentState) -> dict:

# Post-tool node to check the output of a problematic tool

tool\_response = state["messages"][-1].tool\_outputs

review\_input = SilentReviewRunInput(messages=state["messages"], tool\_response=tool\_response)

reviewer = SilentReviewForJSONDataComponent()

review\_result = reviewer.process(data=review\_input, phase=AgentPhase.RUNTIME)

if review\_result.outcome == Outcome.NOT\_ACCOMPLISHED:

return "Silent␣error␣detected,␣retry␣the␣tool!"

else:

# (allow tool call to go through)

agent\_graph.add\_edge("flaky\_tool", "post\_tool\_hook")

Figure 2. Code example in Python integrating the Silent Error Review component from ALTK to a LangGraph agent as a post-tool hook.Code example for integrating the Silent Error Review component from ALTK to a LangGraph agent as a post-tool hook.

At the time of writing, ALTK has 10 components (see Figure [3](#S2.F3)), spanning lifecycle stages from build-time to right before the response is given to the user. For this demonstration, we focus on three components: SPARC as a *pre-tool* call validator, JSON Processor as a *post-tool* processor of long responses, and a *post-tool* Silent Error Review.

![Refer to caption](images/09_ALTK/components_table.png)


Figure 3. List of components in ALTK

### 2.1. Pre-tool: SPARC - pre-execution validation

In enterprise settings, semantically incorrect tool calls may waste API quota, corrupt external state, or trigger irreversible actions. Production agents need an inline runtime mechanism that decides whether a specific call should even be allowed to execute.
SPARC is a component that works at the pre-tool lifecycle stage. Based on the message history, the provided tool specifications and any candidate tool calls, SPARC performs syntactic validation, semantic validation, and transformation validation.
Syntactic validation is rule-based and catches non-existent tools, unknown arguments, missing required parameters, type mismatches, and JSON-schema violations. Semantic validation uses one or more LLM judges to assess function-selection appropriateness, parameter grounding, hallucinated values, value-format alignment, and unmet prerequisites. Transformation validation handles format or unit mismatches (for example, date, currency formats) and performs automatic conversions as demanded by the tool specifications.
The output of the component identifies whether tool call is invalid. If the tool call is not valid, SPARC identifies issues and suggests remediation.

### 2.2. Post-tool: JSON Processor

In a tool-augmented agentic pipeline, the JSON processor acts as a critical middleware layer between raw API output and downstream reasoning. Passing voluminous, deeply nested JSON directly into the agent’s context competes for attention with the task prompt and has been shown to degrade accuracy as responses grow longer ([Kate et al., 2025](#bib.bib10)). Instead, this component delegates the parsing to a code generation step: the LLM is prompted to write a short Python function that navigates the JSON structure, applies any necessary filtering or aggregation logic, and returns only the extracted answer. This approach treats the LLM as a programmer rather than a reader, playing to its strength in producing structured code. When augmented with the API’s JSON response schema, the generated parser becomes even more reliable; the model can reason about field names, data types, and nesting relationships without needing to infer them from the raw data. The resulting agent architecture is both more token efficient, since the code output is far smaller than the full response it processes, and more composable, as the deterministic output of an executed script slots cleanly into the next stage of an agent loop without any formatting noise and verbosity.

### 2.3. Post-tool: Silent Error Review

A common scenario for agentic tool usage is "soft failures" where an API may return responses that seem correct by returning a HTTP status code of "200 OK" but the body of the response may contain text like "Service under maintenance" or "No results found." Traditional agents often interpret this tool response as a correct final answer and this may cause unintended behavior. The Silent Error Review component works at the post-tool stage to identify these failures using a prompt-based approach. The component takes as input the user query, the tool response, and optionally the tool specification, to review the response as “ACCOMPLISHED”, “PARTIALLY ACCOMPLISHED”, or “NOT ACCOMPLISHED”.

## 3. Evaluations

As ALTK is comprised of many components, each component is individually evaluated for effectiveness in their particular task. We present evaluations for the subset of ALTK components we focus on for this demonstration.

### 3.1. Pre-tool: SPARC Evaluation

We evaluate SPARC on the airline API subset of the $\tau$ -bench dataset ([Yao et al., 2024](#bib.bib1)) in a ReAct loop. If the candidate call is approved, it executes. If rejected, the reflection artifact (issue type, evidence, and correction suggestion) is fed back to the agent, which retries.
Figure [4](#S3.F4) reports the experimental results. The main pattern is that gains grow with $k$ . For GPT-4o self-reflection, pass1 moves from 0.470 to 0.485, while pass4 improves from 0.260 to 0.300.
SPARC is most helpful for near-miss trajectories: it turns many incorrect first proposals into recoverable tool decisions on subsequent retries.

![Refer to caption](images/09_ALTK/gpt4o_passk_gemini.png)


Figure 4.  $\tau$ -bench airline passk with and without SPARC. “With reflection” inserts SPARC before each tool call and returns critique and/or corrections to the agent when a call is rejected.

### 3.2. Post-tool: JSON Processor

We evaluate the JSON processor component on 15 models from various families and sizes on a dataset of approximately 1,300 JSON responses queries of varying complexity. Using the JSON processor leads to improvements over directly prompting a model to retrieve the answers without using the JSON processor component.
Figure [5](#S3.F5) shows 16% improvement on average across models when using the JSON processor ([Kate et al., 2025](#bib.bib10)).

![Refer to caption](images/09_ALTK/json_proc_res_gemini.png)


Figure 5. Model performance with and w/o JSON Processor([Kate et al., 2025](#bib.bib10))

### 3.3. Post-tool: Silent Error Review Evaluation

We evaluate the Silent Error Review component on the LiveAPIBench dataset for SQL queries in a ReAct loop ([Elder et al., 2026](#bib.bib22)). We evaluate using two metrics: Micro Win Rate and Macro Win Rate. The Micro Win Rate is the average performance across individual data subsets and the Macro Win Rate is the overall performance across all samples in all subsets. As seen in figure  [6](#S3.F6), adding Silent Error Review to the ReAct loop nearly doubles the micro win rate, indicating more queries are fully or partially accomplished. Additionally, the average loop counts decrease showing that fewer iterations are needed to reach success.

![Refer to caption](images/09_ALTK/silent_error_res.png)


Figure 6. ReAct agent performance comparison with and without Silent Error Review on LiveAPIBench ([Elder et al., 2026](#bib.bib22)); WR: Win Rate

## 4. Usage and Integrations

To maximize accessibility and facilitate adoption across diverse enterprise environments, ALTK is architected to support multiple deployment approaches. Rather than forcing a single integration pattern, the toolkit targets three distinct developer profiles: pro-code, low-code, and no-code.

In the pro-code case, for software engineers and AI researchers requiring fine-grained control over the execution flow, ALTK is distributed as a modular set of open-source Python libraries hosted on GitHub.
Developers install the core packages and directly modify their existing agent source code, embedding ALTK’s lifecycle hooks (Pre-Tool, Post-Tool, Pre-Response) natively within their logic. There are several Jupyter notebooks with examples of how to use the various components55
5
https://agenttoolkit.github.io/altk-boost/examples/.

For rapid prototyping and visual workflow builders, ALTK provides deep integration with the Langflow66
6
https://www.langflow.org/blog/langflow-1-7 low-code tool.
ALTK capabilities are exposed via a custom agent within Langflow’s visual authoring environment. The ToolGuard
, JSON Processor
, and SPARC
components are available in Langflow with demos on our YouTube channel77
7
https://www.youtube.com/@AgentToolkit.

For system administrators, platform engineers, and operations teams who need to secure and enhance legacy or third-party agents without altering their underlying code (no-code), ALTK integrates seamlessly as a middleware layer via the ContextForge MCP Gateway88
8
https://ibm.github.io/mcp-context-forge/.
Administrators configure the ALTK integrations in the gateway to intercept outbound tool calls and inbound responses, applying ALTK’s SPARC
or JSON Processor
dynamically. Tool enrichment and testing are available at the gateway for more effective agent tool use.
See our YouTube channel[7](#footnote7) for demos of these integrations.

## 5. Related Work

A wide ecosystem of agent orchestration frameworks, such as LangChain ([Chase, 2022](#bib.bib11)), LangGraph ([LangChain, 2024b](#bib.bib12)), LlamaStack ([AI, 2024](#bib.bib14)), LlamaIndex ([Liu, 2022](#bib.bib13)), CrewAI ([Moura, 2023](#bib.bib16)), AutoGen ([Wu et al., 2023](#bib.bib15)), Claude’s Agent SDK ([Anthropic, 2024](#bib.bib17)), Bee ([IBM Research, 2024](#bib.bib20)), Smolagents ([HuggingFace, 2024](#bib.bib19)), and Haystack ([Möller et al., 2020](#bib.bib18)), provides tooling to build LLM-based agents. These frameworks largely focus on workflow composition, infrastructure, or developer-side robustness. They offer hooks and middleware ([LangChain, 2024a](#bib.bib21)) for retries, fallbacks, and tool routing, but they generally do not detect or prevent semantic errors in agent reasoning or tool use.

ALTK fills this gap by acting as a framework-agnostic reliability layer that integrates at lifecycle hook points within any agent system.
For example, ALTK can plug into LangChain middleware or be exposed as skills or MCP components within Claude’s SDK.

Compared to data and model-centric approaches (e.g., APIGen ([Liu et al., 2024b](#bib.bib7)), ToolACE ([Liu et al., 2024a](#bib.bib6)), Granite function-calling models ([Abdelaziz et al., 2024](#bib.bib8))), which improve average tool-calling quality through better training, ALTK provides an inference-time gate to determine whether a specific call should run.

Compared to reflection- and repair-based methods (e.g., Reflexion ([Shinn et al., 2023](#bib.bib2)), REBACT ([Zeng et al., 2025](#bib.bib9)), ToolReflection ([Polyakov et al., 2025](#bib.bib3)), Failure Makes the Agent Stronger ([Su et al., 2025](#bib.bib4)), and Tool-MVR ([Ma et al., 2025](#bib.bib5))), ALTK’s SPARC module is similar in spirit but differs by operating before execution, producing structured outputs rather than free-form critiques, and combining semantic reflection with deterministic schema and execution- verification checks.

Overall, ALTK complements rather than replaces existing agent frameworks, providing systematic runtime safeguards that enhance correctness and reliability.

## 6. Conclusion

ALTK is motivated by a simple observation: robust agents need more than a capable base LLM; they need to address the dominant failure modes that occur at various points in the agent lifecycle. ALTK provides a flexible toolkit of components to address common problems at these lifecycle stages. This flexibility is open-ended, as we invite agent builders to extend the toolkit with their own solutions to problems as well as integrate components into agentic systems. We believe lifecycle-based components are key to building agents that are intelligent, reliable, and adaptable.

Beyond runtime reliability, ALTK can also support analytics and evaluation workflows by applying its lifecycle checks to agent trajectories, enabling fine-grained analysis of failure modes and model behavior. These same components can provide structured signals for reward model training or tuning, turning ALTK’s reflectors into supervision signals that improve tool-use fidelity and policy adherence.

## References

- Abdelaziz et al. (2024)
  I. Abdelaziz, K. Basu, M. Agarwal, S. Kumaravel, M. Stallone, R. Panda, Y. Rizk, G. S. Bhargav, M. Crouse, C. Gunasekara, et al.
  Granite-function calling model: introducing function calling abilities via multi-task learning of granular tasks.
  In Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing: Industry Track,
  pp. 1131–1139.
  Cited by: [§5](#S5.p3.1).
- AI (2024)
  M. AI
  Llama stack.
   GitHub.
  Note: <https://github.com/meta-llama/llama-stack>
  Cited by: [§5](#S5.p1.1).
- Anthropic (2024)
  Anthropic
  Claude Agent SDK.
  Note: <https://docs.anthropic.com>
  Cited by: [§5](#S5.p1.1).
- Chase (2022)
  H. Chase
  LangChain.
  Note: <https://github.com/langchain-ai/langchain>
  Cited by: [§1](#S1.p2.1),
  [§5](#S5.p1.1).
- Elder et al. (2026)
  B. Elder, A. Murthi, J. Kang, A. R. Naik, K. Kate, K. Basu, and D. Contractor
  Live api-bench: 2500+ live apis for testing multi-step tool calling.
  External Links: 2506.11266,
  [Link](https://arxiv.org/abs/2506.11266)
  Cited by: [Figure 6](#S3.F6),
  [§3.3](#S3.SS3.p1.1).
- HuggingFace (2024)
  HuggingFace
  Smolagents.
  Note: <https://github.com/huggingface/smolagents>
  Cited by: [§5](#S5.p1.1).
- IBM Research (2024)
  IBM Research
  Bee Agent Framework.
  Note: <https://github.com/i-am-bee/bee-agent-framework>
  Cited by: [§5](#S5.p1.1).
- Kate et al. (2025)
  K. Kate, Y. Rizk, P. Ghosh, A. Gulati, T. Chakraborti, Z. Wright, and M. Agarwal
  How good are llms at processing tool outputs?.
  arXiv preprint arXiv:2510.15955.
  Cited by: [§2.2](#S2.SS2.p1.1),
  [Figure 5](#S3.F5),
  [§3.2](#S3.SS2.p1.1).
- LangChain (2024a)
  LangChain
  LangChain Built-in Middleware.
  Note: <https://docs.langchain.com/oss/python/langchain/middleware/built-in>
  Cited by: [§5](#S5.p1.1).
- LangChain (2024b)
  LangChain
  LangGraph.
  Note: <https://github.com/langchain-ai/langgraph>
  Cited by: [§1](#S1.p2.1),
  [§5](#S5.p1.1).
- Liu (2022)
  J. Liu
  LlamaIndex.
  Note: <https://github.com/run-llama/llama_index>
  Cited by: [§5](#S5.p1.1).
- Liu et al. (2024a)
  W. Liu, X. Huang, X. Zeng, X. Hao, S. Yu, D. Li, S. Wang, W. Gan, Z. Liu, Y. Yu, et al.
  Toolace: winning the points of llm function calling.
  arXiv preprint arXiv:2409.00920.
  Cited by: [§5](#S5.p3.1).
- Liu et al. (2024b)
  Z. Liu, T. Hoang, J. Zhang, M. Zhu, T. Lan, S. Kokane, J. Tan, W. Yao, Z. Liu, Y. Feng, et al.
  Apigen: automated pipeline for generating verifiable and diverse function-calling datasets.
  Advances in Neural Information Processing Systems 37, pp. 54463–54482.
  Cited by: [§5](#S5.p3.1).
- Ma et al. (2025)
  Z. Ma, J. Liu, X. Luo, Z. Huang, Q. Zhu, and W. Che
  Advancing tool-augmented large language models via meta-verification and reflection learning.
  In Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V. 2,
  pp. 2078–2089.
  Cited by: [§5](#S5.p4.1).
- Möller et al. (2020)
  M. Möller, M. Mosbach, T. Ruas, S. Severini, and I. Gurevych
  Haystack: an end-to-end NLP framework.
  In Proc. EMNLP (Demos),
  Cited by: [§5](#S5.p1.1).
- Moura (2023)
  J. Moura
  CrewAI.
  Note: <https://github.com/crewAIInc/crewAI>
  Cited by: [§1](#S1.p2.1),
  [§5](#S5.p1.1).
- Polyakov et al. (2025)
  G. Polyakov, I. Alimova, D. Abulkhanov, I. Sedykh, A. Bout, S. Nikolenko, and I. Piontkovskaya
  ToolReflection: improving large language models for real-world api calls with self-generated data.
  In Proceedings of the 1st Workshop for Research on Agent Language Models (REALM 2025),
  pp. 184–199.
  Cited by: [§5](#S5.p4.1).
- Shinn et al. (2023)
  N. Shinn, F. Cassano, A. Gopinath, K. Narasimhan, and S. Yao
  Reflexion: language agents with verbal reinforcement learning.
  Advances in neural information processing systems 36, pp. 8634–8652.
  Cited by: [§5](#S5.p4.1).
- Su et al. (2025)
  J. Su, Y. Wan, J. Yang, H. Shi, T. Han, J. Luo, and Y. Qiu
  Failure makes the agent stronger: enhancing accuracy through structured reflection for reliable tool interactions.
  arXiv preprint arXiv:2509.18847.
  Cited by: [§5](#S5.p4.1).
- Wu et al. (2023)
  Q. Wu, G. Bansal, J. Zhang, Y. Wu, B. Li, E. Zhu, L. Jiang, X. Zhang, S. Zhang, and C. Wang
  AutoGen: enabling next-gen LLM applications via multi-agent conversation.
  arXiv preprint arXiv:2308.08155.
  Cited by: [§5](#S5.p1.1).
- Yao et al. (2024)
  S. Yao, N. Shinn, P. Razavi, and K. Narasimhan
  Tau-bench: a benchmark for tool-agent-user interaction in real-world domains.
  arXiv preprint arXiv:2406.12045.
  Cited by: [§3.1](#S3.SS1.p1.1).
- Zeng et al. (2025)
  Q. Zeng, S. Rajkumar, D. Wang, N. Gyanchandani, and W. Yan
  Reflect before act: proactive error correction in language models.
  arXiv preprint arXiv:2509.18607.
  Cited by: [§5](#S5.p4.1).
