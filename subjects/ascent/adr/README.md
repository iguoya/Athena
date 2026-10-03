# 架构决策记录（ADR）

这个目录记录 Lumi 英语学习软件的关键决策。每个文件一个决策，编号递增；决策改变时新增一条 ADR 并标注取代关系，不改写旧记录。

| 编号                                               | 决策                                   |
| -------------------------------------------------- | -------------------------------------- |
| [0001](0001-separate-repo.md)                      | 独立仓库，不与 Athena 合并             |
| [0002](0002-offline-desktop-app.md)                | 做离线优先的桌面应用，只有 AI 批改上云 |
| [0003](0003-tech-stack.md)                         | 技术栈：Tauri 2 + React                |
| [0004](0004-visual-first-three-themes.md)          | 视觉优先，三套皮肤定版                 |
| [0005](0005-real-sentences-no-isolated-words.md)   | 单词不孤立，只用现实中的真实句子       |
| [0006](0006-integrated-four-skills.md)             | 读写听说结合，每天一组真实句子         |
| [0007](0007-implicit-grammar.md)                   | 语法融入真实句子，隐性习得             |
| [0008](0008-proven-learning-methods.md)            | 借鉴公认有效的学习理论                 |
| [0009](0009-visible-progress-and-motivation.md)    | 见效快、看得见的进步和成就感           |
| [0010](0010-content-and-data-model.md)             | 内容与数据结构                         |
| [0011](0011-output-first-learn-to-use.md)          | 学有所用：写是必修，说是鼓励项         |
| [0012](0012-vocabulary-gate.md)                    | 单词关：以高中词汇量为上限             |
| [0013](0013-sentences-first-gradual-difficulty.md) | 句子为主，难度缓慢增加                 |
| [0014](0014-memory-and-learning-science.md)        | 系统融入记忆理论和高效学习方法         |
| [0015](0015-exam-weighted-priorities.md)           | 按考试分值分布定学习重点               |
| [0016](0016-archive-old-site.md)                   | 归档 2020 年的旧作文站                 |
| [0017](0017-chapter-roadmap-high-school-first.md)  | 章节路线：先夯实高中英语，再逐级备考   |
| [0018](0018-auto-update.md)                        | 启动时自动更新；发版触发与入口由仓库级 ADR 0081 修订 |
| [0019](0019-open-content-sources.md)               | 开放内容来源和版权规则                 |
| [0020](0020-merged-into-athena.md)                 | 并入 Athena 仓库，作为独立应用 subjects/lumi（取代 0001） |

完整的第一版功能范围见：https://claude.ai/code/artifact/93687992-8596-41b3-9acf-87199ac80580
