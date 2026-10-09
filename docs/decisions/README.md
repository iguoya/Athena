# 仓库级 ADR 索引

这里收**影响仓库结构或多个应用**的架构决策记录。只管某一个应用的决策记在该应用自己的
`docs/decisions/` 下，例如 [`subjects/cpp/docs/decisions/`](../../subjects/cpp/docs/decisions/README.md)。
两处各自延续编号，所以两边都有跳号（ADR 0045）。仓库级侧的缺号（0001–0006、
0008–0027、0033–0036、0038–0039 等）产生于本目录按 ADR 0045/0061 建立之前：当时的
决策或散见各应用文档，或未落成文；编号按「只增不改」保留空位，不回填、不重排。

架构决策记录保存重要取舍的背景、决策与后果，**不是实时功能清单**：一条 ADR 说明当时
为什么这样选，后来的修订以 [`AGENTS.md`](../../AGENTS.md) 等当前规范为准。影响架构边界
或不可逆方向的新决定，先新增 ADR 再动代码；编号只增不改，被取代的记录保留原文。

## 跨应用教学规范

| 编号 | 决策 | 状态 |
|---|---|---|
| [0028](0028-outline-process-experiment-layering.md) | 大纲、教学过程、教学实验三层分工 | 已接受，`type_semantics` 已跟进 |
| [0029](0029-difficulty-and-mastery-goal.md) | 知识点按难度与掌握目标两个维度评级 | 已接受 |
| [0030](0030-knowledge-point-prerequisites.md) | 知识点级前置依赖与依赖方向校验 | 已接受，`type_semantics` 已声明 |
| [0031](0031-knowledge-type-drives-teaching-actions.md) | 知识类型（概念/技能/策略）决定教学动作 | 已接受，`type_semantics` 已标注 |
| [0040](0040-lesson-length-matches-mastery-goal.md) | 学习内容拒绝八股，篇幅与掌握目标匹配 | 已接受，第一章已按此精简 |
| [0043](0043-sourced-content-across-apps.md) | 「内容必须有出处」跨应用统一规范 | 已接受（统一 mathematics 0019、c 0003、english 0007–0009；第 7 节补充 cpp AI 出题反例） |
| [0052](0052-incentives-and-records-cooperate.md) | 激励与统计是同一条回路，必须互相配合 | 已接受（裁定 mathematics 0011 待定项；对齐 english 0009） |
| [0058](0058-content-driven-block-based-ui.md) | 内容驱动 UI：有限块类型胜过按章手写整页 | 已接受（统一 dsa 块架构与 cpp 反面案例） |
| [0059](0059-experiments-ship-skeletons-not-blank-slates.md) | 教学实验给骨架，不给白板 | 已接受（统一 dsa 0003、cpp 0053、mathematics 0014） |
| [0096](0096-retrieval-spacing-interleaving-lead-curriculum.md) | 检索练习、间隔重复、交错练习定为课程设计的主导学习策略，自我解释与双重编码为辅；界面与内容取舍判据化，按成本五档改造；学习风格适配明确不做 | 已接受；不设自动门禁 |
| [0107](0107-chapter-three-dimension-rating.md) | 软考章节三维评级（应用性/实践性/实验性）恢复为内容建设正式维度，与「实践路径 A/B」并存分工；2026-10-09 两张评级表收录为基线 | 已接受；评级表原文在本 ADR |
| [0108](0108-dsa-split.md) | dsa 拆分为 data-structures（数据结构，承接软设第 3 章）与 algorithms（算法设计，承接第 8 章），内容按教材章硬切，dsa 退役；端口 1497/1498，前缀 ds./algo.，旧进度库不迁 | 已接受；修订 0103 决策 2 表格 dsa 行与决策 6 承接表述、0099 承接表述 |

## 应用边界与启动

| 编号 | 决策 | 状态 |
|---|---|---|
| [0032](0032-independent-apps-launched-as-processes.md) | 异构学习应用作为独立进程共处一个仓库 | 已接受；启动路径见 0041 |
| [0037](0037-independent-apps-own-their-progress-store.md) | 每个独立应用自建自管自己的进度库 | 已接受；库位置由 0053 修订 |
| [0041](0041-independent-apps-launch-in-dev-mode.md) | 独立应用从源码以开发模式启动，不经打包副本 | 已接受 |
| [0042](0042-c-language-qt-qml-lessons.md) | C 语言学习应用用 Qt Quick / QML 写教案 | 已接受 |
| [0044](0044-menubar-launcher.md) | 常驻菜单栏的启动器，主程序也只是其中一项 | 已接受 |
| [0045](0045-apps-are-peers.md) | C++ 教程降级为 `subjects/cpp`，所有学习应用平级 | 已接受；目录由 0060 拆分 |
| [0060](0060-subjects-and-practice.md) | `apps/` 拆成 `subjects/`（课程学科）与 `practice/`（项目应用） | 已接受 |
| [0062](0062-apps-own-their-constraints.md) | 每个应用只守自己的约束，不从别的应用继承 | 已接受 |

## 仓库工程

| 编号 | 决策 | 状态 |
|---|---|---|
| [0007](0007-unified-check-entry.md) | 统一验证入口（现为 `scripts/check.py`） | 已接受；各应用均已接入 |
| [0046](0046-unified-dev-orchestrator.md) | 统一开发编排器，各应用只声明怎么启动 | 已接受；第 5 条范围由 0063 收窄 |
| [0063](0063-per-app-build-directories.md) | 同类可共享构建缓存，异构必须隔离 | 已接受；修订 0046 第 5 条 |
| [0065](0065-one-colour-icon-per-app.md) | 每个应用一份彩色图标，启动器、任务栏、应用界面三处同源 | 已接受 |
| [0047](0047-portable-by-default.md) | 跨平台优先：选型、代码与构建过程的默认原则 | 已接受 |
| [0048](0048-menubar-launcher-stays-macos-only.md) | 菜单栏启动器保留为 macOS 专属，只消费编排器结论 | 已接受 |
| [0049](0049-portability-is-a-cost-benefit-call.md) | 跨平台是成本收益判断，成本过高的整体排除 | 已接受；限定 0047 的边界 |
| [0050](0050-ci-runs-on-release-not-every-push.md) | 跨平台稳定之前，CI 推送即跑 | 已被 0064 取代 |
| [0064](0064-ci-explicit-trigger.md) | CI 改为显式触发，不再推送即跑 | 已接受；取代 0050 |
| [0081](0081-unified-release.md) | 统一发版：一个 v* tag 全量构建 cpp、driver、拾阶，发一个 Athena Release | 已接受；修订 ascent 应用级 0018 的发版入口描述；回退 `c115dd4` 的 driver 独立发版；北极星、磨砚、数学工具随后加入同台矩阵（v9.0.0 起） |
| [0083](0083-launcher-mind-map.md) | 启动器的学习应用面板改为放射状思维导图，关系由 app.json 的 group / related 声明 | 已接受 |
| [0084](0084-math-tools-joins-subjects.md) | math-tools 从 practice/ 迁入 subjects/，作为数学学习的配套工具 | 已接受；修订 0060 对 math-tools 的归类 |
| [0085](0085-reinforce-draws-from-all-wrong.md) | 强化练习从历史上全部错题里按权重抽取，每轮重抽并可「换一批」 | 已接受；修订 0076 第 7 条的选题规则；决策 2 由 0086 修订 |
| [0086](0086-reinforce-coverage-then-fade.md) | 错题必须在强化练习里测过且没出错才能移出备选库，没测过的优先覆盖 | 已接受；修订 0085 决策 2 |
| [0087](0087-reinforce-round-size-50.md) | 强化练习一轮默认 50 题，页面把备选库总题数摆在最前 | 已接受；修订 0076 决策 7 |
| [0088](0088-reinforce-variant-pass-counts.md) | 同考点变式在强化练习里答对，同簇错题也算验收 | 已接受；修订 0086 决策 1 |
| [0051](0051-platform-priority-macos-windows-first.md) | 平台优先级：macOS 与 Windows 优先，Linux 降级 | 已接受；`subjects/cpp` 的选型冲突已解决 |
| [0053](0053-progress-travels-with-the-repository.md) | 进度库随仓库走，换机器 clone 下来进度还在 | 已接受；修订 0037 第 1 条；对已迁移中心 PG 的应用由 0067 修订 |
| [0054](0054-prefer-adding-over-deleting.md) | 内容工作宁增勿删，参考不得用来重划结构 | 已接受；推翻 polaris ADR 0004、0005 的主干重划；第 2、3 条由 0080 限定 |
| [0080](0080-reorg-exemption-when-intent-changes.md) | 应用意图整体改变时，可由应用级 ADR 声明重组豁免 | 已接受；限定 0054 第 2、3 条；首例 `subjects/machine` |
| [0055](0055-no-institute-names-in-product-content.md) | 软件内容不出现具体院所名，一律用「某所」 | 已被 0082 撤销，相关内容与条款已清除 |
| [0082](0082-drop-institute-redaction.md) | 撤销 0055 的院所名脱敏规则，清除全部相关痕迹 | 已接受；0055 原文保留仅作历史记录 |
| [0056](0056-visualization-and-interaction-first.md) | 可视化与交互是学习内容本身，不是装饰 | 已接受（强制方针） |
| [0057](0057-assume-a-developer-machine.md) | 基线是一台开发机——依赖自行安装，不写兜底 | 已接受 |
| [0061](0061-agent-instructions-single-source.md) | 代理指令以 AGENTS.md 为唯一真源，且只放规则 | 已接受；`subjects/cpp` 应用级已同日瘦身到预算内 |
| [0066](0066-two-english-apps-evolve-independently.md) | 并入 ascent（拾阶），两个英语应用（磨砚 / 拾阶）各自独立发展，不趋同 | 已接受 |
| [0067](0067-progress-data-goes-to-central-postgresql.md) | 进度数据直连中心 PostgreSQL（driver 先行），个人数据与项目数据区隔 | 已接受；修订 0053 的适用范围；第 4、5 条由 0068 修订 |
| [0068](0068-three-layer-storage-credentials-and-rest-channel.md) | 个人数据三层存储（JSON 内容 / 本地 SQLite 队列 / 中心 PG）、凭据不进仓库、外网走 REST API | 已接受；修订 0067 第 4、5 条；服务端与迁移已落地，客户端本地层由 0070 落地 |
| [0069](0069-driver-progress-readonly-dashboard.md) | 驾考进度的网页只读仪表盘挂在 nas_admin：外网过 Access、内网免登录、服务端聚合口径对齐客户端 | 已接受；已落地部署 |
| [0070](0070-driver-client-local-first-rest-only.md) | 驾考客户端本地优先、统一走 REST API：内网直连 PG 通道退役，本地 SQLite 是唯一数据面、队列幂等补发，测试脱离 PG | 已接受；落地 0068 决策 2、4 |
| [0071](0071-driver-multi-user.md) | 驾考引入用户维度：同一份题库，多个学习者各一份历史，无口令、本地按用户分库、中心表加 `user` 列 | 已接受；决策 2 由 0072 修订、决策 4 由 0074 修订 |
| [0072](0072-user-id-display-name.md) | 学习者 ID 与显示名分离，允许改名 | 已接受；修订 0071 决策 2；决策 2、3、4 由 0073、0074 修订 |
| [0073](0073-global-user-directory.md) | 学习者目录全局化（`Athena/users.json`、中心 `athena_users`），tiger 以规范 ID 收编 | 已接受；修订 0072 决策 3；决策 2、4 由 0074 修订 |
| [0074](0074-central-learner-directory.md) | 中心学习者目录是权威，ID 由后台登记时生成，名字不要求唯一、谁都能改 | 已接受；修订 0071 决策 4、0072 决策 2/4、0073 决策 2/4；尚未实现 |
| [0075](0075-login-by-name-numeric-id.md) | 按名字登录，学习者 ID 改为服务端分配的短数字（≤999），重名才问编号；只能改自己的名字 | 已接受；修订 0074 决策 1/4/5/6；代码已落地，未部署 |
| [0076](0076-attempt-attribution-and-reinforcement-practice.md) | 作答记录补充归因字段（所选选项、会话、考试关联、解析停留），新增独立的「强化练习」，考点簇与派生统计分阶段做 | 已接受；阶段 1～4 均已落地（阶段 4 的实现方式见 0079）；服务端已部署；第 7 条的选题规则由 0085 修订 |
| [0077](0077-no-device-token-gate-at-cloudflare.md) | 取消设备令牌，外网的门放在 Cloudflare 访问规则上，应用里不认证；限流改按来源地址 | 已接受；修订 0068 决策 3、0070 令牌各条 |
| [0078](0078-login-in-one-step.md) | 登录合并为一步：输入名字点进入，没有就直接新建；编号用提示条告知，不弹窗 | 已接受；修订 0075 决策 3 |
| [0079](0079-clusters-computed-at-runtime.md) | 考点簇运行时现算（不落盘），强化练习出「同考点变式」，学习诊断给出变式差距 | 已接受；修订 0076 决策 9 的实现方式 |
| [0089](0089-source-tiers-by-app-nature.md) | 出处要求按应用性质分档：考试/考证考级类阻断（exam），技术学习类降为习惯不做门禁（open），不判分类不适用（reference） | 已接受；修订 0043 的适用范围；english 本轮收紧，machine/gtkmm 降档，softcert 记为考试档已知欠账 |
| [0091](0091-experiments-inside-subject-apps.md) | 实验能力长在学科应用内：编码实验是 softcert 的 lab 块（软设 8 实践章），硬件实验是 esd 的实验视图（嵌入式第 2、4 章），不另建独立实验应用 | 已接受；试点 SQL 实验 |
| [0092](0092-launcher-tree-attach-and-softcert-rename.md) | 启动器思维导图支持树状挂靠（app.json 新增 parent 单父字段、第三层布局、面板归属随 parent）；softcert 显示名改「软件设计师」；dsa、c-gui-lab 挂靠软设（dsa 承接第 3、8 章编码实验），cpp 预留挂靠 | 已接受；修订 0090 决策 1 定位表述、0091 决策 1 承接范围；启动器三层布局待实现 |
| [0093](0093-drop-practice-panel.md) | 取消实践面板（展示全由 group/parent 声明驱动）；app.json 新增 hidden 字段；nas-admin 隐藏（软路由 Web 服务非桌面应用，仪表盘宿主服务照常）；pocket-cube 挂靠 cpp | 已接受；废止 0083 的实践面板分区；启动器实现归启动器开发线 |
| [0094](0094-no-category-labels-in-launcher.md) | 课程性/实验性区分留在内容与目录层，启动器界面不设类别标签/徽章/分区，只表达领域圈与挂靠连线 | 已接受；约束 0092/0093 的启动器实现 |
| [0098](0098-minimal-links.md) | 连线最小化：非必要不特意连线——删 esd↔softcert、磨砚↔摘星 related、C与机器→C++ 演进线、dsa 挂靠（承接软设 3/8 章实验改内容指引）；挂靠深度一层 | 已接受；修订 0092 决策 4 承接表达 |
| [0099](0099-dsa-reattach.md) | dsa 恢复挂靠软件设计师——0095 决策 3 系误读,树形分支保留,承接第 3、8 章编码实验分工不变 | 已接受;原占 0096 号与检索练习版撞号,重编 0099 |
| [0100](0100-single-word-app-ids.md) | 应用 id 再收窄为单词:software-designer→software、embedded-system-designer→embedded(进程/identifier/包名同步);内容层短名继续保留 | 已接受;修订 0097 决策 1、2 的具体名字,「不用缩写」口径不变 |
| [0101](0101-domain-circle-siblings-no-links.md) | 领域圈成员即兄弟:同领域应用之间不画任何特意连线;删 math-tools↔mathematics related(圈内兄弟由 group 表达) | 已接受;修订 0098 决策 4 保留例外、0084 决策 3 声明要求 |
| [0102](0102-exam-apps-as-top-level-groups.md) | 软件设计师、嵌入式系统设计师各为启动器一级大类(group 为领域名「计算机」「电子信息」,「软考」分组退役);挂靠关系不变,id/进度库/内容不动 | 已接受;修订 0090 决策 2 的「group 同为软考」 |
| [0095](0095-one-exam-one-app.md) | 一个考试一个应用:新考试方向一律独立成新应用,不再并入已有考试应用;softcert 多课程注册表为历史结构不再扩 | 已接受;修订 0092 决策 3 的「届时再议」,关闭 0090 决策 1 扩位预留 |
| [0097](0097-spell-out-app-ids.md) | 应用 id 全称化:softcert→software-designer、esd→embedded-system-designer(进程/identifier/包名同步);知识点前缀与课程层短名解耦保留;今后新增应用不用缩写 | 已接受;修订 0092 决策 3 的「id 不动」(无进度无发行,改名零损失) |
