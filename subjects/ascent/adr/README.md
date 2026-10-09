# 架构决策记录（ADR）

这个目录记录 Lumi 英语学习软件的关键决策。每个文件一个决策，编号递增；决策改变时新增一条 ADR 并标注取代关系，不改写旧记录。

> 本目录是并入 Athena 时带来的历史档（仓库级 ADR 0066「两个英语应用各自独立发展，
> 不趋同」）：编号体系独立于仓库级 `docs/decisions/`，不改号、不迁移、不重排。

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
| [0020](0020-merged-into-athena.md)                 | 并入 Athena 仓库，作为独立应用 subjects/ascent（取代 0001） |
| [0021](0021-binary-rename-athena-ascent.md)        | 发布名与二进制名改用 athena-ascent，窗口品牌保持「拾阶」 |
| [0022](0022-stages-and-textbook-path.md)           | 词库分阶（先易后难子阶段）与教材导入路径 |
| [0023](0023-brand-name-zhaixing.md)                | 品牌名从「拾阶」改为「摘星」，工程命名不动 |
| [0024](0024-adopted-moyan-principles.md)           | 从磨砚吸收的掌握度三原则（考核分离、错题出库双条件、回合上限进校验） |

完整的第一版功能范围见：https://claude.ai/code/artifact/93687992-8596-41b3-9acf-87199ac80580
