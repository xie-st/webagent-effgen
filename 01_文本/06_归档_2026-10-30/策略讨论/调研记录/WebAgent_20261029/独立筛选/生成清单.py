from pathlib import Path
import json,re
ROOT=Path(__file__).parent
# id, short name, research judgment / experimental support, repository, impact, project judgment, evidence / gap
ROWS=[
('2606.01533v1','MACU',9,8.5,'kohjingyu/multi-agent-computer-use','27 stars；Koh 团队延续 WebArena、VisualWebArena 的交互式评测研究。','把任务拆为可动态修订的 DAG，执行就绪节点；最贴近多 Tab 调度主线。','四项桌面与网页基准、并行数和管理器消融；保留无法再次观察的信息，向下游传递。'),
('2605.21470v2','Agent JIT Compilation',9,8,None,'预印本；未核实正式录用，不把 ICML 关键词视为录用证据。','把模型调用、工具动作与并发写进执行计划；用前后置条件和延迟估计优化调度。','五个应用、同工具缓存对照和统计附录支持编译调度机制；论文所引 blast 是基础设施，不能算本论文代码。'),
('2607.22689v1','ParaGUIBench',8.5,8,'pkgunboat/ParaGUIBench','6 stars；专门研究并行 GUI 的新基准。','区分串行、独立并行和需要协调的任务；帮助定义并行收益及共享状态评测。','233 项任务，成功率、关键路径步数、并行度及 token 成本；有规划器和工作器消融。'),
('2607.24167v1','FCPAgent',9,7.5,None,'预印本；以明确的验证和修复机制入选。','每个子目标附确认与否定证据；廉价检查失败后再诊断，局部修复。','621 项测试与模块消融支持整体收益；漂移检测仅抽查 50 条轨迹、13 个漂移样本，机制验证偏弱。'),
('2511.21398v1','Prune4Web',8.5,8,None,'AAAI 2026 主会：出版页已核实。','让模型生成元素评分规则，再由程序裁剪；适合作为页面观察压缩的设计参考。','候选元素压缩、定位和组件消融齐全；完整系统包含训练，比赛中借鉴过滤机制。'),
('2605.07134v1','Region4Web',8.5,8,'kwondu/region4web','0 stars；尚无明显社区传播证据，按适配性入选。','将可访问性树组织成功能区域，维护跨步骤页面摘要；与平台观察形式相近。','完整 WebArena、多模型与代理基线；仓库包含区域分解、摘要、选择与状态转移。完整方案带训练组件和辅助模型。'),
('2605.29397v1','Revisiting Observation Reduction',8.5,8,None,'预印本；系统比较观察压缩方法的直接证据。','用关键元素保留情况筛选压缩策略，并计入压缩本身的时间；适合选择观察预算。','11 种方法、32 配置，两项基准；WorkArena 33 个任务各一 seed，另有单步 WebLinx；论文同时报告成功率与总延迟。'),
('2602.20502v1','ActionEngine',8.5,7.5,None,'Georgia Tech / Microsoft 连续 GUI 系统研究；传播影响尚未核实。','用页面状态机和参数化动作生成程序；论坛场景特别贴近比赛。','主要深入评估 Reddit 子集，缺少相同深度的跨站验证；95% 是该子集结果，不能当作整个 WebArena 成绩。'),
('2603.20340v3','ContractSkill',8.5,8,'underfitting-lu/contractskill','8 stars；核心实现已公开。','把动作流程写成带前提和成功条件的技能；检查失败后仅修补出错步骤。','VisualWebArena 100 项三次运行、MiniWoB 20 类受控实验与局部修复消融；仓库有两个运行入口和 skill_utils。'),
('2610.03036v2','WebFovea',8.5,7.5,'jianganghan/WebFovea','0 stars；作者报告 WebRetriever 2026 第二名，57/100。','检查动作解析、实际执行、反馈、观察四个环节；真实网页演示的直接工程参考。','固定模型的四次竞赛提交和定向案例；活站变化与多项联合修改未被完全隔离，不能将总分变化归于单个补丁。'),
('2605.16565v2','Skim',8.5,8,None,'Princeton / Microsoft 的低延迟网页代理研究。','常见任务走可验证的快速路径，失败后从已到达页面接回通用代理；借鉴快慢路径调度。','三种底层代理、成本与延迟分布、回退分析；含离线模板和小模型，其接入须按赛题约束转换。'),
('2601.21123v2','CUA-Skill',8.5,8,'microsoft/cua_skill','50 stars；微软公开技能库与执行框架。','参数化技能与组合图减少细粒度动作决策；适合参考技能结构和复用单位。','技能级和 WindowsAgentArena 端到端评估、规划器及恢复消融；57.5% 是 best-of-three，单次平均另列。'),
('2603.00503v1','M²',8.5,8,None,'预印本；按网页任务证据和 Qwen 结果入选。','当前任务轨迹摘要加历史经验检索；直接用于长任务上下文与调用成本设计。','WebVoyager、OnlineMind2Web，多模型和记忆组件消融；有 Qwen3-VL-32B 结果。'),
('2610.01415v1','PoS / Beyond Memory',8.5,8,'luoyu100/PoS','34 stars；10 月新稿，已有运行框架。','显式维护当前状态、未解决要求与进度；检测无进展循环，组织恢复后的上下文。','四项执行/诊断基准、三种底层模型和一致性/恢复消融；这些基准不是网页专用基准。'),
('2512.10371v2','AgentProg',8.5,8,'MobileLLM/AgentProg','33 stars；公开程序化上下文框架。','按变量和控制流维护上下文，保留当前程序仍会用到的信息。','AndroidWorld 加 19 个长任务、对照与消融；作为移动 GUI 向网页迁移的结构参考。'),
('2606.15017v2','Budget-Constrained Web Agents',9,8.5,'ServiceNow/budget-constrained-web-agents','作者项目页标注 EMNLP 2026；2 stars。','把规划、记忆、技能生成与主代理的 token 一并计费，决定额外模块是否值得保留。','四个 WebArena 域、三种模型，含 Qwen3.6-27B；额外 WorkArena 和更高步数预算对照，并报告运行方差。'),
('2603.15473v2','ALTK',8.5,8,'AgentToolkit/altk-boost','CAIS 2026 系统演示论文；已有可安装组件。','执行前检查参数，执行后识别静默错误；适合搭建统一 hooks 与恢复入口。','SPARC、JSON 处理和 Silent Error Review 分组件评测；不是整套 WebAgent 的端到端成功率证明。'),
('2512.15374v2','SCOPE',8.5,8,'JarvisPei/SCOPE','85 stars；有独立优化包。','把执行失败归纳为短期修正和长期提示规则；用于离线迭代提示词。','HLE、GAIA、DeepSearch 和组件消融，附单代理 SWE-bench；主表 Pass@2，不能等同单次验收通过率。'),
('2609.05736v1','Beyond Prompts / PRISM',8.5,8,'airbnb/agent-harness-optimizer','11 stars；Airbnb 发布优化框架。','区分该改提示词还是工具边界代码；固定模型下优化 harness，与统一模型要求相合。','BFCL 和两项 τ² 基准、留出评价、预算控制及编辑面消融；用于离线设计，不照搬论文外部提案模型。'),
('2608.02643v2','CUADebug',8.5,7.5,'AgentDebugX/AgentDebugX','作者项目页标注 EMNLP 2026；关联框架 71 stars。','从日志中定位最早因果错误，形成带证据的诊断，再指导重试。','204 条人工标注失败；部分主表使用人工给定重启位置，不可把全部恢复增益理解为自动定位效果。代码在关联框架的 GUI 模块。'),
('2610.27954v1','Lost in Recovery / ReTrace',8.5,8,'PENDING:BangProx/ReTRACE','3 stars；10 月新稿。','恢复标准是后续动作能否继续正确执行，而非页面看起来回去了；适合定义恢复验收。','受控扰动、目标导向重放及端到端恢复评估；仓库仅 readme 和素材，写明 Code will be released soon。'),
('2604.06240v1','The Art of Building Verifiers',9,8.5,'microsoft/fara','Fara 仓库 6236 stars，属于整个模型/工具项目，不能归于本篇论文。','拆分过程与最终结果，设计不重叠的验证条件；避免 Agent 自报成功。','两套人工标注数据、一致性分析和消融；代码入口 webeval/scripts/verify_trajectories.py。'),
('2511.20067v1','Are We Done Yet?',8,8,'martasumyk/vision-based-judge','AAAI 2026 TrustAgent Workshop；4 stars。','用任务要求与最终截图判定完成，再将未完成证据反馈给执行器。','42 个 macOS 应用、1260 个标注任务、多种 judge 与执行器；适合真实站点的完成检查思路。'),
('2605.16116v1','ShopGym',8,7.5,None,'Shopify / NC State 新预印本；未定位公开实现。','参考电商任务类别、长任务组合及完成判定条件，补充比赛电商用例。','六个商店、224 项任务、结构和行为比较；对合成商店与真实商店的一致性验证规模仍较小。'),
('2604.16385v1','StressWeb',8.5,8,'inclusionAI/AWorld-RL/tree/main/StressWeb','AWorld-RL 仓库 128 stars，属于整个项目。','系统注入布局变化、交互语义变化与执行故障；直接服务容错测试。','干净/扰动成对比较，确定性检查点、多个模型；核实独立网站、执行器、评测器代码目录。'),
]
GROUPS=[
('任务规划','planning',['2606.01533v1','2607.24167v1','2602.20502v1']),
('页面观察与信息提取','observation',['2605.07134v1','2511.21398v1','2605.29397v1']),
('动作执行','actions',['2603.20340v3','2610.03036v2','2602.20502v1']),
('动作效率与技能复用','action-efficiency',['2605.21470v2','2605.16565v2','2601.21123v2']),
('上下文管理','context',['2603.00503v1','2512.10371v2','2610.01415v1']),
('模型调用效率','inference',['2606.15017v2','2605.29397v1','2605.16565v2']),
('并发调度与等待','concurrency',['2606.01533v1','2605.21470v2','2607.22689v1']),
('提示词与钩子','prompt-hooks',['2603.15473v2','2609.05736v1','2512.15374v2']),
('失败处理与恢复','recovery',['2607.24167v1','2608.02643v2','2610.27954v1']),
('结果检验','verification',['2604.06240v1','2607.24167v1','2511.20067v1']),
('Benchmark','benchmark',['2607.22689v1','2604.16385v1','2605.16116v1']),
]

def main():
    papers={}
    for aid,name,q,e,repo,impact,judgment,evidence in ROWS:
        d=json.loads((ROOT/'来源文本'/(aid+'.json')).read_text(encoding='utf-8'))
        papers[aid]=dict(id=aid,name=name,title=d['title'],quality=q,experiment=e,repo=repo,impact=impact,judgment=judgment,evidence=evidence,url=d['url'])
    lines=['# WebAgent：每维度三篇独立筛选','',
    '2026-10-29。合并近一年与近30天；11 个维度、33 个阅读位置，去重后 25 篇。每维度按本项目阅读优先级排列，跨维度重复保留。','',
    '筛选依据：先满足成功率与容错，再比较耗时、冗余动作和模型成本；结合统一 Qwen3.6-35B-A3B、可访问性树输入、单请求单动作及真实站点演示要求。优先可迁移的调度、状态、验证和执行机制。','',
    '候选仅取原始分类清单的题名与论文链接，不使用原相关性分数、benchmark选型、质量抽查、整合结果或他人评价。初筛题名后读取 31 篇论文正文，核查方法、实验、必要附录和代码，最终保留 25 篇。','',
    '研究质量与实验支撑分别采用 10 分制；8 分达标。评分为本次判断。影响力结合正式发表、可见开源传播及连续研究；stars 记录于核查日，不等于论文引用数。代码状态指核查到的实现，未进行安装复现。','',
    '**本项目最值得先读：MACU、FCPAgent、Agent JIT Compilation。** 三篇分别对应任务依赖与并行、验证与局部修复、调用与调度成本。','']
    for label,key,ids in GROUPS:
        lines += ['## '+label,'','| 顺序 | 论文 | 对本项目的价值 | 代码 |','|---|---|---|---|']
        for n,aid in enumerate(ids,1):
            p=papers[aid]; repo=p['repo']
            code=('未定位' if not repo else '[待发布](https://github.com/'+repo.removeprefix('PENDING:')+')' if repo.startswith('PENDING:') else '[有实现](https://github.com/'+repo+')')
            lines += [f"| {n} | [{p['name']}]({p['url']}) | {p['judgment']} | {code} |"]
        lines+=['']
    lines+=['## 质量、影响力与取舍记录','','实验达到 8 分的仅记录结论；未达标的写明影响判断的缺口。下列为选入依据，不把作者宣称的最高结果直接当作比赛预期。','',
    '| 论文 | 研究质量 / 实验支撑 | 影响力依据 | 核查要点 |','|---|---|---|---|']
    for p in papers.values():
        lines += [f"| {p['name']} | {p['quality']} / {p['experiment']} | {p['impact']} | {p['evidence']} |"]
    lines+=['','## 原始来源与适配记录','',
    '- 原始赛题：[WebAgent比赛要求.md](../../../../比赛要求/WebAgent比赛要求.md)。',
    '- [AAAI 出版页：Prune4Web](https://ojs.aaai.org/index.php/AAAI/article/view/40772)。',
    '- [CUADebug 作者项目页](https://cuadebug.github.io/)；[Budget-Constrained 作者项目页](https://sinahmr.github.io/budget-constrained-web-agents/)。',
    '- arXiv HTML 本次可直接访问；没有调用 AnySearch，也没有读取其凭据。',
    '- 调度和程序化执行须在现有动作接口内展开：每次返回一个当前观察中合法的动作；多 Tab 真并行需实际接口支持。',
    '- ActionEngine、JIT、Skim 的程序化思路迁移为可中断执行计划和参数化网页流程；不把网站内部 API 或预写答案当作捷径。',
    '- Region4Web 的学习组件、Skim 的小模型和其它方案的辅助模型均受报备要求约束；赛方平台不允许控制模型推理参数，未优先选服务端 KV cache、解码和 GPU 调度论文。',
    '- 频率控制、登录/二次验证接管仍按赛题独立设计；不把通用并发论文等同于已经解决这些能力。',
    '- 31 篇读取源文、抓取脚本、仓库核查与任务记录保留在本文件所在目录；未改动已有调研结论。','']
    (ROOT/'每维度三篇.md').write_text('\n'.join(lines),encoding='utf-8')
    (ROOT/'筛选数据.json').write_text(json.dumps({'date':'2026-10-29','groups':GROUPS,'papers':papers},ensure_ascii=False,indent=2),encoding='utf-8')
    # Check every selection really belongs to its original category, independently of old scores.
    base=ROOT.parent
    for label,key,ids in GROUPS:
        raw='\n'.join(p.read_text(encoding='utf-8') for p in base.glob('*/webagent-'+key+'.md'))
        assert len(ids)==3 and len(set(ids))==3
        for aid in ids: assert aid.split('v')[0] in raw,(label,aid)
    print(json.dumps({'dimensions':len(GROUPS),'slots':sum(len(g[2]) for g in GROUPS),'unique':len(papers),'implementation':sum(bool(p['repo']) and not p['repo'].startswith('PENDING:') for p in papers.values()),'pending':sum(bool(p['repo']) and p['repo'].startswith('PENDING:') for p in papers.values())},ensure_ascii=False))

if __name__=='__main__': main()
