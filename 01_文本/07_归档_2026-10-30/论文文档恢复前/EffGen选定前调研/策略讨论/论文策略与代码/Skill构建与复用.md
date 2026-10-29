# Skill构建与复用：从轨迹到可验证执行

2026-10-30。覆盖现行清单22 CUA-Skill、23 SGDR、24 Trace2Skill、25 SkillsBench，并连接04 ContractSkill、06预算研究、13 Skim与18 ActionEngine。防限流不展开。

**采用一套技能接口：Trace2Skill离线改善内容，SGDR按当前状态选择，CUA-Skill组织参数和执行位置，ContractSkill验证与修补，SkillsBench检验是否值得保留。** 这些是互补机制，不必同时引入各论文的完整框架。

下文“论文方法”是作者原机制，“接入设计”是固定Qwen、AX树和单请求单动作下的项目方案。先给逐篇可用方法，再给统一接口与接入流程。

## 22 CUA-Skill：将技能做成有参数、有分支的执行单元

**问题与理论。** 同一个用户意图可以有不同的操作路径。技能不能只是一串固定点击；应把“做什么”“传入什么”“当前界面下怎么做”分开。作者以 `应用、意图、参数模式、执行图` 定义技能。技能内部执行图描述低层动作与分支；技能之间的组合图描述可衔接关系，不是预先固定的整任务计划。

**论文方法。** 检索少量候选后，规划器结合目标、当前画面、历史和参数适配度选择技能，低层动作始终作为回退候选。参数从定义域内配置；执行器遍历执行图，遇到具体交互再定位。结果记忆同时记录意图、真实效果及失败上下文，避免再次选择同一无效操作。

**接入设计。** 给基础 Agent 增加技能注册表与可暂停的执行游标。每项保存 `id、intent、page_type、args_schema、entry_checks、steps/branches、exit_checks、fallback`；其中前后条件及fallback接现有ContractSkill检查与恢复模块，是本项目组合设计。参数分为任务值和界面目标：任务值来自用户要求或已证实事实，界面目标保存语义定位条件，每轮从当前AX树重新绑定编号。缺参数、入口不成立或目标不唯一时，退回基础决策，不能猜值继续。

执行状态保存 `skill_id、version、bound_values、cursor、verified_steps、pending_effect`。一次 `decide()` 只返回当前步骤的一条平台动作；下次收到观察先核验上一动作，成立才推进游标。页面变化使剩余目标失效时，重新绑定或暂停技能；写入结果不明时先确认，不从技能首步重放。完成技能只更新其对应子目标，最终完成仍由全任务要求判断。

**代码。** [agent/action/compose_action.py](https://github.com/microsoft/cua_skill/blob/main/agent/action/compose_action.py) 的 `BaseComposeAction.add_path()`、`append_graph()`、`step()` 可参考执行图组织与逐步展开；[argument.py](https://github.com/microsoft/cua_skill/blob/main/agent/action/argument.py) 的 `Argument` 可参考参数封装；[retrieval.py](https://github.com/microsoft/cua_skill/blob/main/agent/retrieval.py) 的 `BM25`、`ActionRetriever.retrieve_actions()` 提供候选检索入口。原仓库是Windows桌面执行框架；本题取数据结构和控制流程，动作层接官方协议，截图定位替换为当前AX编号绑定。

## 23 SGDR：根据目标和当前页面，动态找短流程

**问题与研究判断。** 开始任务时检索到的整段流程，不一定适用于任务中途。作者将复用单位定为可在中间页面调用的短流程，用“任务想做什么”和“当前页面允许做什么”共同检索，较单纯给更多技能更贴近网页交互。

**论文方法。** 从评估为成功的轨迹中用2–5步滑窗提取候选，参数化为“操作描述＋函数代码”；用技能替换原片段重放，仍成功才入库。每步把AX树压成页面类型和当前可用操作摘要，按 `α×任务相似度＋(1−α)×状态相似度` 粗排，再以MMR减去与已选技能的相似度，避免重叠滑窗占满候选。候选只支持当前决策，下一步重新检索。

**接入设计。**

1. **形成技能。** 开发阶段从已确认成功轨迹抽短流程，泛化任务值和目标控件；候选记录来源轨迹、适用页面、参数、预期效果。只在可复位的开发环境中做替换重放；通过后发布版本。原文成功判定是模型代理信号，项目入库另结合现有检查器的页面证据。
2. **组织检索。** 输入当前子目标、页面类型和可用语义操作，输出少量技能ID、版本、相关度与入口检查结果。程序先按站点/页面类型和必要控件过滤，检索阶段同时保留目标和状态两种信号，再去掉重复流程。小库首版可用BM25/关键词与规则，语义排序使用同一Qwen；这与原文embedding余弦评分不同，不额外默认启用辅助模型。
3. **控制调用成本。** 页面类型或子目标改变、技能失败、当前候选均不再适用时刷新候选；稳定表单内沿已验证执行游标继续，不必每个输入动作再调用一次摘要和检索。这是本项目在固定模型下的成本改造。
4. **执行与回退。** 通过CUA-Skill式统一执行接口展开，当前动作即时绑定编号。原文的复合函数不能直接返回给平台；跨页后才出现的控件必须在新观察中解析。前置条件不成立则选普通动作，后置条件失败则转局部修复并重新检索，保留已确认进度。

**代码。** [sgdr/retrieval/skill_store.py](https://github.com/plusnli/online-skill-learning/blob/main/sgdr/retrieval/skill_store.py) 已核实 `Skill`、`SkillStore.add()`、`save()`、`topk()`：保存来源任务和窗口，按双信号评分，再贪心MMR。`add()` 的语义去重由阈值配置控制，默认阈值为None，不能仅调用入库函数就认定完成语义去重。论文α=0.5，而所读源码 `topk()` 默认α=0.4，接入时显式配置。[state_summarizer.py](https://github.com/plusnli/online-skill-learning/blob/main/sgdr/retrieval/state_summarizer.py) 与 [induce目录](https://github.com/plusnli/online-skill-learning/tree/main/sgdr/induce) 是状态摘要和技能提取入口。

## 24 Trace2Skill：从多条执行轨迹归并成稳定流程

**问题与理论。** 一条失败就追加一条规则，会让技能受修改顺序影响；把每段经验独立存进记忆，又把重组负担留给在线检索。作者的判断是：先独立分析多条轨迹，再把反复出现的操作规律归并成一份技能，价值来自联合归纳，而非规则堆积。

**论文方法。** 冻结模型与初始技能，生成带正确性标签的成功、失败轨迹。成功分析器单次提炼有效行为；失败分析器读取日志与产物，定位原因、实施最小修复并核验，无法解释的失败不提补丁。各分析器针对同一初始技能快照独立写补丁，再分层归并：同义规则合并、冲突依据证据解决、独立经验保留、低频细节移入引用文件。最终补丁经确定性格式与编辑检查后应用。

**接入设计：放在开发阶段，在线只加载产物。**

1. 复用现有 trace，输入 `任务约束、动作前后AX树、动作与回执、最终校验、当时技能版本`。成功轨迹提取有效顺序与检查条件；失败轨迹提取首个因果错误、触发状态、已验证修正及恢复后的继续条件。只有本队合法开发轨迹进入提炼集。
2. 每条经验输出 `source_trace、适用条件、失败机制/有效模式、操作规则、检查条件、建议修改文件/段落`。失败原因必须能由回放与页面证据支持；有本地可重置环境时用最小修改重跑验证。无法验证原因的记录留作待分析，不立即写成强制规则。
3. 对同一技能原始版本独立生成候选补丁，再按“导航、参数绑定、结果确认、恢复”归并。根文件只留触发条件、短流程和必要检查；站点特有细节放引用文件，主文件链接与引用文件一起更新。规则描述对象类别和状态条件，不固化某次任务的答案、旧元素编号或最终用例参数。
4. 输出新技能目录、版本号、来源轨迹集合、diff与变更理由。格式/路径/引用校验后，在独立开发任务上比较旧版与新版，通过后再替换现行版本。执行中的任务固定技能版本，下一任务使用新版本，避免运行到一半改变流程含义。

Trace2Skill原实验将已知目标技能的 `SKILL.md` 预加载，并按需读取辅助资源；它不提供SGDR式状态检索。项目可用Trace2Skill离线改善技能内容，再由SGDR选择当前需要的短流程。轨迹生成、分析、归并均可接统一Qwen，不采用论文的模型切换或推理参数配置；其分析并行缩短的是离线技能生成时间。

**代码。** [并行归并核心](https://github.com/Qwen-Applications/Trace2Skill/blob/main/skill_evolver/parallel_evolving_agent.py) 中 `ParallelSkillEvolver.run_map_phase()`、`run_reduce_phase()`、`run_apply_phase_programmatic()`、`run_verification_phase()`；`PatchEdit/Patch` 给出文件、操作、目标段落、旧文本、新文本等结构，`_enforce_create_pairing()` 保证新增引用和主文件链接成对。[混合成功/失败实现](https://github.com/Qwen-Applications/Trace2Skill/blob/main/skill_evolver/parallel_success_evolving_agent.py) 中 `normalize_mixed_records()`、`CombinedParallelSkillEvolver`；[运行入口](https://github.com/Qwen-Applications/Trace2Skill/blob/main/skill_evolver/run_parallel_combined_skill_evolution.py) 组织分析记录到技能产物；[released_skills](https://github.com/Qwen-Applications/Trace2Skill/tree/main/released_skills) 可看主文件与引用文件的组织。

其中 `run_verification_phase()` 检查文件格式和资源一致性，技能是否改善任务完成仍须单独运行任务验证。

## 25 SkillsBench：独立测量技能是否改善了固定Agent

**问题与判断。** “加载了技能”不代表“技能被正确采用”，更不代表提高任务完成率。作者把技能作为独立实验变量：同一任务、环境、模型与执行框架，只改变技能访问条件，由同一程序验收器判定结果。

**可提取的方法。** 任务包分开保存指令、环境、参考解和验收器；技能提供一类任务的流程知识，不暴露实例答案。使用无技能/有技能的成对结果，而非比较两批不同任务的平均成绩。除完成率外记录技能发现、读取、调用、实际执行、token和耗时，区分内容质量与加载/执行链路问题。

**接入设计。** 保持基础Agent及统一Qwen固定，用同一组可重置开发任务比较：无技能、人工初稿、Trace2Skill修订稿；需要评估检索时，再在同一技能版本上比较任务级检索与状态级检索。每轮只改一个因素，重置页面与业务数据；人工接管时段单独记录。

每条运行保留 `task_id、agent_version、skill_version、loaded_skill_ids、检索/读取/执行步骤、最终整项通过、模型调用/token、页面访问、动作、耗时`。同时统计成功被修好与原本成功变失败的任务，检查是技能不适用、正文过重、参数绑定错，还是检查/回退缺失。最终以整项通过率为主，耗时比较双方均通过任务；检索、加载、校验和回退的成本全部计入。

**对技能内容的直接启发。** 技能优先写模型从页面上不易推断的顺序、约束、验证细节和确定性辅助逻辑；把可选重步骤标清，提供返回基础Agent的轻量路径。根文件保持聚焦，低频材料按需加载。原文按技能数量和篇幅分组观察收益差异，这支持“精简后实测”的选择，不把某个数量或字数视为赛题通用最优值。

**代码。** [成对配置：有技能](https://github.com/benchflow-ai/skillsbench/blob/main/experiments/configs/main-with-skills.yaml) / [无技能](https://github.com/benchflow-ai/skillsbench/blob/main/experiments/configs/main-without-skills.yaml) 可参考实验条件的组织；这些是仓库保留的配置样例，不直接当作论文最新版汇总配置。[任务实例](https://github.com/benchflow-ai/skillsbench/tree/main/tasks/offer-letter-generator) 展示指令、oracle、技能与verifier的分离；[verifier/test_outputs.py](https://github.com/benchflow-ai/skillsbench/blob/main/tasks/offer-letter-generator/verifier/test_outputs.py) 的参数化字段核验可参考多要求分别检查的组织。网页项目替换为页面/业务终态检查，不复制文档任务逻辑；官方验收口径继续沿用比赛要求。

## 把现有契约、恢复与预算接入Skill

### ContractSkill：把技能正文变成可验证对象

论文将技能表示为 `目标、前置条件、带断言的步骤、总后置条件、恢复规则、终止条件`。每步包含语义目标、动作、参数和结果断言；失败后返回步骤位置、错误类型和局部证据，只允许替换目标、纠正参数、插入前置/后置条件或恢复步骤。候选修补用同一验证器接受，不因“文本写得更合理”直接替换现行版本。

接入时保留两层产物：`SKILL.md`承载适用场景、规则和按需参考；结构化执行记录承载参数、语义定位、契约和游标。文本技能可先作为基础Agent的决策指导；只有已经明确参数、前后条件及逐步行为的部分才进入执行队列。每个技能明确自己的完成条件，全任务终止仍由总目标验证器决定。

代码从[env/skill_utils.py](https://github.com/underfitting-lu/contractskill/blob/main/env/skill_utils.py)的 `validate_skill_payload()`、`build_contract_repair_prompt()`、`observation_contract_status()` 与 `allowed_patch_types_for_failure()` 开始读。实际源码返回 `skill_id/task/preconditions/success_contract/steps/repair_history/patches`，步骤是 `action/target/value`，不完全等同论文概念字段；项目的逐步断言需由适配层补齐。`skill_to_action_string()`输出作者的语义文本动作格式，平台适配器还须把目标绑定成当前编号。步骤定位、最小修补与源码细节见[规划执行恢复](规划执行恢复.md)。

### 预算研究：验证技能自身有效，并完整计算额外成本

技能引入两类需要分别记录的结果：技能按契约完成；技能失败后基础Agent补救并完成。后者能证明整体恢复有效，不能据此将原技能记为验证通过。失败轨迹仍可提炼恢复经验，但成功标签要来自相应步骤和页面证据。

入库轨迹不保存旧编号和任务实例常量，保留当前页面如何识别目标、参数来自哪里、何时停止及如何确认。只写“搜索、点击、提交”的泛化流程缺少决定成败的操作信息；应补入分页、排序方向、对象身份或结果确认等实际决定行为的条件。

检索、技能生成、修订、加载、步骤验证和失败回退全部计入成本。离线提炼成本与单任务运行成本分开报，运行比较包括加载和回退；有技能与无技能使用同一模型、任务和验收器。成本计数与AX去重代码见[验证调用与钩子](验证调用与钩子.md)的06条目。

### Skim与ActionEngine：保留两种执行加速入口

Skim用于已验证的只读导航与提取快路径，验证失败就从当前页面交回基础Agent；ActionEngine用页面状态图与变量把重复决策改为图搜索和确定性计算。它们都通过同一语义定位、单动作输出与结果检查接口执行，无需另建技能库或另维护一套完成状态。具体方法见[规划执行恢复](规划执行恢复.md)的13、18条目。

## 统一接口：让基础Agent可以逐步采用

下表是本项目的组合规格，不是某一论文的原版schema。

| 对象 | 必需字段 | 用途 |
|---|---|---|
| 技能规格 `SkillSpec` | id、version、intent、适用页面/状态、args_schema、entry_checks、steps/branches、exit_checks、fallback、resource_refs | 检索、绑定、执行与验证共用一份定义 |
| 每步规格 | 语义目标、动作类型、参数来源、前置条件、预期证据、失败分支 | 解析当前动作与决定何时推进 |
| 执行状态 `SkillRun` | skill_id/version、任务值、cursor、已确认步骤、pending_effect、退出原因 | 跨平台请求续跑，任务内固定版本 |
| 来源与准入 | source_traces、修订diff、验证任务与结果、总成本、当前发布状态 | 提炼有据可查、更新可回退 |

**任务值和控件编号分开。** 商品、数量、目标论坛等任务值可保存；控件编号每次从当前观察取得。后续页面才出现的控件，不在技能开始时猜编号。

**参考文件按需加载。** 索引只放意图、适用状态、参数说明和资源位置；选中技能再加载根文件，只有步骤需要时才加载低频参考。资源加载成本与检索成本一起记录。

### 接到现有 `decide()` 的顺序

1. 收到当前观察，先验证上一技能动作的 `pending_effect`。有证据才推进cursor，结果不明则进入现有检查/恢复流程。
2. 技能正在执行且当前步骤条件成立时，解析语义目标并绑定当前编号，返回一条合法动作。参数或目标有歧义时让统一Qwen判定，不盲目继续队列。
3. 没有可继续技能，或子目标/页面状态变化时，检索候选、检查入口、绑定参数；不适用就沿用基础Agent普通决策。
4. 技能退出时保存步骤证据、实际成本与退出原因；成功只完成对应子目标，失败将当前页面、已确认状态和错误交回基础Agent。
5. 任务结束后把trace交给离线提炼，产出候选新版本；独立任务检验通过后发布，执行中的版本不变。

优先接“技能作为按需指导”，再把已验证且结构清楚的短流程接为带游标执行。这样可以分别评价内容、检索和执行器的贡献，而不一次替换基础Agent。
