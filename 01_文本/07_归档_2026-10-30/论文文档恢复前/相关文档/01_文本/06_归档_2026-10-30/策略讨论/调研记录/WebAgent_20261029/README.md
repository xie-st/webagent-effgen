# WebAgent 文献试跑

原版流水线筛选结果，按方向分开；每篇保留标题、日期、相关性分和原文链接。

近30天：2026-09-30 至 2026-10-29；近一年：2025-10-30 至 2026-10-29。

| 方向 | 近30天 | 近一年 |
| --- | --- | --- |
| 任务规划 | [1 篇](近30天/webagent-planning.md) | [93 篇](近一年/webagent-planning.md) |
| 页面观察与信息提取 | [2 篇](近30天/webagent-observation.md) | [100 篇](近一年/webagent-observation.md) |
| 网页行动与工具 | [4 篇](近30天/webagent-actions.md) | [100 篇](近一年/webagent-actions.md) |
| 并发调度与等待 | [1 篇](近30天/webagent-concurrency.md) | [59 篇](近一年/webagent-concurrency.md) |
| 限流控制 | 未运行 | [3 篇](近一年/webagent-rate-control.md) |
| 行动效率 | [0 篇](近30天/webagent-action-efficiency.md) | [100 篇](近一年/webagent-action-efficiency.md) |
| 模型调用效率 | [2 篇](近30天/webagent-inference.md) | [100 篇](近一年/webagent-inference.md) |
| 结果检验 | [3 篇](近30天/webagent-verification.md) | [96 篇](近一年/webagent-verification.md) |
| 失败处理与恢复 | [4 篇](近30天/webagent-recovery.md) | [100 篇](近一年/webagent-recovery.md) |
| 上下文管理 | [3 篇](近30天/webagent-context.md) | [100 篇](近一年/webagent-context.md) |
| 提示词与钩子 | [1 篇](近30天/webagent-prompt-hooks.md) | [75 篇](近一年/webagent-prompt-hooks.md) |
| Skill | 未运行 | [100 篇](近一年/webagent-skills.md) |

一年窗口每方向最多保留100篇；两条流程的筛选门槛不同，数量不直接比较。

本轮返回论文名单；一年窗口未生成逐篇精读内容。完整候选、评审缓存和日志保留在 `.local-runs/` 与 `archive/`。

2026-10-30：限流控制与 Skill 年度专题均已完成召回、相关性评分及名单导出，已合并至上表；每个专题评审300篇，分别保留3篇、100篇。新增专题仅运行一年窗口，未运行近30天调研。[任务记录](限流与Skill任务记录.md)

<!-- benchmark-topic:start -->

## Benchmark专题

本轮专题 100 篇，去重整合 126 篇，已完成。

[赛题选型](benchmark选型.md) · [年度整合名单](近一年/webagent-benchmark-integrated.md) · [任务记录](benchmark任务记录.md)

<!-- benchmark-topic:end -->

## 最终清单与保留参考

- [WebAgent 项目最终 33 篇论文](../../WebAgent项目最终30篇论文.md)：现行清单，保留 12 个大维度，按项目重要程度排序。
- [每维度三篇（主要参考）](独立筛选/每维度三篇.md)。
- [每维度三篇·言语独立筛选（辅助参考）](每维度三篇_言语独立筛选.html)。
- [Benchmark 选型](../03_Benchmark选型.md)。

2026-10-29：按用户要求删除其余 7 份旧版精选清单，原始候选与核查材料保留。

2026-10-30：补入 Skill 方向的 SGDR、Trace2Skill、SkillsBench，清单增至 33 篇；[筛选任务记录](Skill筛选任务记录.md)保留判断与核查依据。
