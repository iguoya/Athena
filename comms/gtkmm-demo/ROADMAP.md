# gtkmm 完善路线图（2026-10-18 排期，leader：claude-code）

来源：`comms/gtkmm-review/SUMMARY.md` 的审查结论 + 2026-10-18 现状盘点。原则：每方同一时间一件事；
worker 出草稿、leader 集成验收；zcode 账号额度 2026-10-19 17:59 才恢复。

| # | 事项 | 负责 | 状态 / 依赖 |
|---|---|---|---|
| 0 | ADR 索引补全、旧路径修正、Rust 未用参数警告 | claude-code | 已完成（8d726f6f） |
| 1 | 第 4、5 章加「迁移者读」目录标记（`audience: migrators`） | claude-code | 已完成 |
| 2 | 第 3 章信号时序预测–运行演示（`demo.basics-signals`） | cursor T-001 → claude-code 集成 | 已完成（77ed7067） |
| 2b | **界面可达性修复**：此前所有讲解/模拟/演示/实验块（含第 6 章样板）在界面上都点不到，节页底部新增「本节演示与讲解」，块按 `page_ref` 落到节页，check 校验块必须有落点 | claude-code | 已完成（3fd38567） |
| 3 | 第 9 章 Box 布局预测–运行演示（`demo.container-box`） | cursor T-002（依赖 T-001）→ 集成 | 排队 |
| 4 | 附录 G（gmmproc）47 段缺译补译 | cursor T-003（依赖 T-002） | 排队 |
| 5 | 参考层其余 7 项：20 段缺译、合并译文拆分、译文忠实度审查 | zcode T-101 → claude-code 合并并翻转 `reference[].status` | 等 zcode 额度恢复 |
| 6 | ~~无演示章章首明示「运行端 = 官方示例」~~ | — | 取消：官方示例卡本来就在节页最上方（ADR 0008），已经明示 |
| 7 | 知识点按需拆分：只在要挂演示/模拟的章把一章一个 quizset 拆成按概念命名、带 `requires` 的知识点（第 3 章信号概念、第 9 章 Box 布局概念）。依据：进度按题目 id 记，`page_ref` 已把题绑到页，拆分不丢进度；但界面目前不展示知识点层级，全书铺开收益低 | claude-code | 与 2、3 的集成同批做 |
| 8 | 全书知识点拆分（审查建议 4）：试点后看复习调度（主仓库 ADR 0096）是否真的需要，需要再出 ADR 0012 并分章铺开；否则不做，避免空拆 | claude-code 判断 | 依赖 7 的试点 |
| 9 | 后续演示候选：第 7+16 章 Adjustment、第 10 章 ListModel | 视 2、3 的验收质量再定 | 待定 |

不在本路线图内：原生演示的 Windows/macOS CI 探测位（`docs/RELEASE-TODO.md` 已记，成本高，非教学内容）。
