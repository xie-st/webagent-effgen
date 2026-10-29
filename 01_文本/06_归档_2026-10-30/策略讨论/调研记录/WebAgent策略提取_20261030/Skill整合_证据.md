# Skill补充：整合与代码核查

2026-10-30。用户补充后的现行清单共33篇：新增23 SGDR、24 Trace2Skill、25 SkillsBench，原23–30顺延为26–33；22 CUA-Skill解除暂缓。仅使用当前对话、根指导和指定项目资料；防限流不研究，比赛要求保持原文。

## 整合依据

新四篇逐篇阅读、实验评分和源码核查见 Skill检索执行_证据.md、Skill提炼评估_证据.md。原04 ContractSkill、06预算研究、13 Skim、18 ActionEngine沿用首轮完整阅读及评分；本轮重新细读ContractSkill §3.2–4.5、预算研究§3.2/3.3、§5.2、附录F.1–F.4，将技能结构、质量准入和成本核算补全。Skim只读快路径与ActionEngine状态图的具体接入已在规划执行恢复.md中保留，本轮只补链路定位，不冒充新的独立实现。

ContractSkill把纯文本草案改成可验证外部对象，继承程序修复的定位、小步编辑与验证接受；CUA-Skill侧重执行与组合图；SGDR侧重当前状态下的可调用性；Trace2Skill侧重多轨迹经验归并；SkillsBench与预算研究侧重技能贡献的隔离评价。此为方法之间的关系，不将它们称为同一团队连续研究。

## 本轮源码补核

GitHub连接器成功读取 https://github.com/underfitting-lu/contractskill/blob/main/env/skill_utils.py （71,388字符）。核实：

- validate_skill_payload：实际返回 skill_id、task、preconditions、success_contract、steps、repair_history、patches；步骤规范化为 action/target/value。源码schema与论文goal/P/U/Q/R/T概念模型不完全同名，正文分开写。
- normalize_contract：仅保留支持的契约键，并做列表去重；未知键不会自动成为有效检查。
- build_contract_repair_prompt：附失败定位、最近6步轨迹、当前可见目标及允许补丁；返回完整修订JSON；源码有特定基准提示，不作为比赛通用流程直接复制。
- skill_to_action_string：生成CLICK[语义文本]、TYPE[标签=值]等作者动作格式；不能直接用作官方click [编号]协议，必须经当前观察重新绑定并转换。

既有 observation_contract_status、localize_failure、allowed_patch_types_for_failure 等符号见规划执行恢复_证据.md。空契约的成功返回不作总目标完成证据。

## 迁移归属

正文的统一SkillSpec字段、每请求只执行一步的执行器、阶段状态、参数与当前编号分离、版本准入、带技能/无技能对照方案均为项目组合设计；不声称是任何一篇论文的原始完整实现。使用同一Qwen完成需要模型的生成/修复，未新增报备之外的辅助模型。没有安装或运行论文代码。

事实核查8.5/10，达标；原04与06实验评分沿用已核对记录，新四篇评分留对应证据文件。正文不堆叠论文结果数字。
