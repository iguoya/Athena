# 仓库级 ADR 索引

这里收**影响仓库结构或多个应用**的架构决策记录。只管某一个应用的决策记在该应用自己的
`docs/decisions/` 下，例如 [`subjects/c-plus-plus/docs/decisions/`](../../subjects/c-plus-plus/docs/decisions/README.md)。
两处各自延续编号，所以两边都有跳号（ADR 0045）。仓库级侧的缺号（0001–0006、
0008–0027、0033–0036、0038–0039 等）产生于本目录按 ADR 0045/0061 建立之前：当时的
决策或散见各应用文档，或未落成文。2026-10-11 多代理并行写 ADR 还撞过一回号：两方各持
**0131**，共享层试点先落库占号，异构准入改号 0133 顺延。编号按「只增不改」保留空位，
不回填、不重排；选号到落库要一次完成，缩短撞号窗口。

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
| [0109](0109-linux-subapp.md) | 新增「Linux 程序设计」子应用 linux 挂 software（承接软设第 4 章 Linux 命令实验与 Linux 学科，通用 OS 语义归 os）；端口 1499、前缀 linux.；图标归属：Tux 归 linux，os 用 Unix 专有图标 | 已接受；沿 0103 判据与 0106 追加模式 |
| [0110](0110-computer-networks-rename.md) | network 更名 computer-networks（计算机网络，title/group 同步；端口 1493 不变，前缀 network.→net. 零成本新起）；图标换 Cisco 标志（品牌蓝） | 已接受；修订 0103 决策 2 表格 network 行的名字与领域圈 |
| [0111](0111-programming-group.md) | 「编程」领域圈改名「程序设计」（gtkmm、c-gui-lab 的 group 同步）；linux 去挂靠入圈与 gtkmm 并肩，软设第 4 章承接降为文字指引 | 已接受；修订 0109 决策 1 的 parent:software |
| [0112](0112-network-rename-back.md) | computer-networks 复名 network（单词优先重新成立）；title「计算机网络」、Cisco 图标、端口/前缀/承接不变 | 已接受；修订 0110 决策 1 的英文代号 |
| [0113](0113-method-archetypes-per-course.md) | 按课程性质分配主导学习方法：七种方法原型（检索强化/预测–运行/机制模拟/真做校验/辨析决策/问题解决/语言习得）决定学习单元骨架与题型优先级，按章节选型；补前测、专长反转、不设自评；专注落成会话原则 P6–P8（有界一轮、作答零打扰、可选自由回忆） | 已接受；在 0096 之上新增一层，不修订其条款；不设自动门禁；初编 0111 与程序设计圈撞号重编 |
| [0114](0114-competitions-group.md) | 新增「大赛」领域圈，首个成员赛历参考应用 competitions（图谱/参考类，端口 1502）：赛事资格分在校生/社会人士，条目必带来源等级与核对日期，超一年标可能过期；训练应用按一个赛事一个应用另立 | 已接受 |
| [0117](0117-merge-english-into-ascent-and-group-reference.md) | 磨砚并入摘星后退役（先迁移后退役，打 pre-english-merge 标签兜底，参考资料分流规则迁移前先定）；引用挂靠扩展到领域圈：app.json 新增 also_in，数学学习与磨砚引用到「考研」圈 | 已接受；修订 0066、0095 在英语上的适用 |
| [0116](0116-reference-attach-and-cs408.md) | 引用挂靠：app.json 新增 also_under，一个应用可在多处出现（同图标同进程）；新增 408 考试主应用 cs408（「考研」圈，考试档）；目标考试更正为 22408，英语二、数学二已有承载，缺口只剩政治；思维导图扇区改按角度需求分配 | 已接受；修订 0115 的 organization 挂靠与缺口清单 |
| [0121](0121-design-patterns-to-programming-group.md) | design-patterns 去挂靠入「程序设计」圈；定位改为以设计模式与程序组织为主（讲解取材 GoF → 软设教程 §7.3 → Refactoring.Guru），软考降为专题（真题原题 verbatim）；批判课与出圈两章降为延伸层；出处档位改 open | 已接受；修订 0103 决策 2 表格 design-patterns 行 |
| [0115](0115-organization-app.md) | 新增计算机组成原理学习应用 organization（group 计算机、不设 parent，端口 1501，前缀 org.，主原型机制模拟）；记录 11408/0854 课程缺口，其余缺口与 408 主应用挂靠另立 | 已接受 |
| [0118](0118-heavier-exam-owns-course-body.md) | 课程本体归权重更高的考试——408 夺走软设手里的四门课（数据结构、组成原理、操作系统、计算机网络本体挂 cs408，软设降为文字指引） | 已接受 |
| [0119](0119-detach-is-exclusive.md) | 夺走即独占——启动器画布上一个节点只出现一次，被夺走方不再保留该节点 | 已接受 |
| [0120](0120-ai-group-and-llm-curriculum.md) | 新增「人工智能」领域圈与 LLM 应用开发课程路线；首门课 python 立项 | 已接受；由 0152 修订 |
| [0122](0122-ai-skeletons-in-one-pass.md) | 人工智能五门课（python、machine-learning、deep-learning、llm-app、llm-finetune）骨架一次落齐 | 已接受 |

## 应用边界与启动

| 编号 | 决策 | 状态 |
|---|---|---|
| [0032](0032-independent-apps-launched-as-processes.md) | 异构学习应用作为独立进程共处一个仓库 | 已接受；启动路径见 0041 |
| [0037](0037-independent-apps-own-their-progress-store.md) | 每个独立应用自建自管自己的进度库 | 已接受；库位置由 0053 修订 |
| [0041](0041-independent-apps-launch-in-dev-mode.md) | 独立应用从源码以开发模式启动，不经打包副本 | 已接受 |
| [0042](0042-c-language-qt-qml-lessons.md) | C 语言学习应用用 Qt Quick / QML 写教案 | 已接受；决策 1、3 由 0138 取代（machine 迁 Tauri + React） |
| [0044](0044-menubar-launcher.md) | 常驻菜单栏的启动器，主程序也只是其中一项 | 已接受 |
| [0045](0045-apps-are-peers.md) | C++ 教程降级为 `subjects/cpp`，所有学习应用平级 | 已接受；目录由 0060 拆分 |
| [0060](0060-subjects-and-practice.md) | `apps/` 拆成 `subjects/`（课程学科）与 `practice/`（项目应用） | 已接受 |
| [0062](0062-apps-own-their-constraints.md) | 每个应用只守自己的约束，不从别的应用继承 | 已接受 |
| [0090](0090-softcert-splits-esd.md) | 软考拆成两个应用——软件设计师留 softcert、嵌入式系统设计师独立成 esd（id 后经 0097、0100 全称化为 software / embedded） | 已接受 |
| [0103](0103-practice-courses-as-attached-subapps.md) | 实践性课程按子课程单元独立成挂靠子应用——software 与 embedded 细分（database、os、network、firmware、microcontroller 等立项） | 已接受；database 挂靠由 0126 修订 |
| [0104](0104-os-rename.md) | operating-system 改名 os——单字领域词优先，长连字符名收窄 | 已接受 |
| [0105](0105-dsa-rename-back.md) | algorithm 复名 dsa——DSA 是数据结构与算法的领域知名缩写，禁自造缩写口径下知名缩写可用 | 已接受；后由 0108 拆分退役 |
| [0106](0106-rtos-subapp.md) | RTOS 从嵌入式侧独立成子应用 rtos | 已接受；0123 入电子信息圈 |
| [0123](0123-embedded-practice-subapps-to-electronic-info.md) | rtos、microcontroller、firmware 去挂靠入「电子信息」圈 | 已接受；沿 0111/0121 入圈即去挂靠先例 |
| [0124](0124-software-to-programming-group.md) | software 去挂靠入「程序设计」圈 | 已接受；领域圈由 0126 改回「计算机」 |
| [0126](0126-software-database-to-computing-group.md) | software 与 database 入「计算机」圈，软考系聚回一处；database 去挂靠 | 已接受；修订 0124 的圈归属与 0103 的 database 行 |
| [0127](0127-gui-retired-webui-succeeds.md) | gui（Slint）退役——webui 转正为唯一图形前端；旧版可执行产物删除，托盘与自启动待 webui 迁移 | 已接受 |
| [0128](0128-earth-app.md) | 新增图谱/参考类应用 earth（「地球」，「程序设计」圈暂存归属，端口 1511）：真实比例的地球分层 3D 可视化——WGS84 椭球、PREM、US Standard Atmosphere 1976 标准模型驱动，不建进度库，壳复制自 polaris | 已接受；2026-10-11 补记：目录改为 practice/earth |
| [0139](0139-app-lifecycle-states.md) | 应用生命周期状态：`app.json` 新增可选 `lifecycle`（active 活跃学习 / built 建成待学 / archived 冻结归档，默认 active），启动器按档分层呈现——built 淡显、archived 默认不呈现且思维导图可开关显示；`hidden`（0093）语义不变，两者独立；首批标注 13 壳 archived、3 个建成待学 built | 已接受；给 0129「宁缺毋滥」提供比删除温和的中间态 |
| [0143](0143-guide-directory.md) | 新增顶层目录 `guide/`（手册类教程）：顶层语义三分 course（课程类，自编教学设计，现 `subjects/`）/ guide（手册类，跟随一本外部手册精读）/ practice（项目类）；gtkmm 迁入为首批唯一成员，id/前缀/进度库/领域圈不动；`subjects`→`course` 改名另行 ADR | 已接受；草拟于 STRUCTURE-PROPOSALS.md V3（0134 流程） |
| [0144](0144-mentor-directory.md) | 新增顶层目录 `mentor/`（导师类，图谱/参考类）：北极星、赛历迁入，只搬目录，id/进程名/端口/group 不动；math-tools 因与 mathematics 关联留 `subjects/`；发版矩阵加 `root` 字段 | 已接受，已执行；修订首版（`reference/`、三应用并入）；决策 3 由 0146 修订 |
| [0145](0145-subjects-rename-to-course.md) | `subjects/` 整体改名 `course/`（0143 决策 2 的落实）：应用 id/目录名/进程名/知识点前缀/进度库全不动，只改顶层容器名；牵动面清单见 STRUCTURE-PROPOSALS V5，等并行重组落库后与 gtkmm→guide 迁移一批执行 | 已接受；草拟于 STRUCTURE-PROPOSALS.md V5（0134 流程） |
| [0146](0146-tools-directory-for-math-tools.md) | 新建 `tools/`，math-tools 迁入；id、进程名、端口不动 | 已接受；修订 0144 决策 3 |
| [0147](0147-exam-apps-into-certification.md) | 软件设计师与嵌入式系统设计师迁入 `certification/`；id、进程名、知识点前缀不动，实践子课程留在 `subjects/` | 已接受 |
| [0148](0148-regroup-domain-circles.md) | 领域圈（`group`）归并为 6 个：计算机基础 / 程序设计 / 人工智能 / 电子信息 / 考研 / 考证；分组仍是 `app.json` 字段，不做成目录；`python` 归程序设计 | 已接受；调整 0102、0111、0120；由 0156 增补「兴趣」圈 |
| [0149](0149-postgraduate-directory.md) | 新增顶层目录 `postgraduate/`，搬入 cs408、五门科目课、mathematics、ascent；group 统一「考研」，挂靠与 id 不变 | 已接受；局部修订 0148 |
| [0150](0150-dissolve-course-by-group.md) | 取消 `course/`：课程类应用按领域圈分到 `programming/`、`artificial-intelligence/`、`computer-fundamentals/`、`electronics/`（加 `postgraduate/`）；启动器认根改用 AGENTS.md + launcher/ | 已接受；取代 0145，修订 0148 决策 1 |
| [0151](0151-chinese-chess-app.md) | 新增 `programming/chinese-chess`：教程壳 Tauri + React，棋盘按五章独立 gtkmm 程序放在 `exercise/` | 已接受；发版排除由 0168 取代 |
| [0152](0152-edge-ai-course.md) | 新增 AI 路线第 6 门 `edge-ai`（端侧 AI 推理与部署），放 `artificial-intelligence/edge-ai/`；运行时 ONNX Runtime 加 llama.cpp，主线板 RK3588；第一批做第 1–5 章，上板章后写；量化边界与 `llm-finetune` 划清 | 已接受；修订 0120 |
| [0153](0153-snake-app.md) | 新增 `programming/snake`：教程壳 Tauri + React，贪吃蛇按五章独立 raylib 程序放在 `exercise/`，第 5 章规则抽 `logic.hh` 配测试 | 已接受；发版排除由 0168 取代 |
| [0156](0156-jiuzhou-history-atlas.md) | 新增图谱/参考类应用 jiuzhou（「九州 / Jiuzhou」，端口 1516）：中国历史地理图鉴；政治秩序主轴（2026-10-13 起七段，蒙元并入唐宋）；MapLibre + `@athena/maps`；新开领域圈「兴趣」；earth 预期后期迁入 | 已接受；修订 0148；地理呈现见 0157 |
| [0157](0157-athena-maps-shared-package.md) | 历史地理纯呈现抽成 `packages/maps`（`@athena/maps`）：纸本墨线底图、自研水系/岸线/走廊；CHGIS 本机可选不入库；jiuzhou 首接 | 已接受；由 0158 修订学术层优先级，CHGIS 不入库一条由 0159 取代；沿 0137 例外；衔接 0156 |
| [0158](0158-jiuzhou-local-academic-maps-expressiveness.md) | 九州本机学术地理层优先（CHGIS/自备谭图系进 `.cache` 不进 git）；采纳史图馆色块年轴、谭图系古今对照、杨利辉提亮/路线/前后对照 | 已接受；修订 0157；衔接 0156；决策 1、2 由 0159 取代 |
| [0159](0159-jiuzhou-academic-layer-in-repo.md) | 互联网上能找到的数据一律默认公域，不为授权设计分流；九州学术层（CHGIS / Hartwell / 谭图数字化）据此直接入库 `packages/maps/geo/academic/`，取消 `prepare_local_maps.py` 等本机可选机制；出处照记 | 已接受；取代 0158 决策 1、2，取代 0156/0157 中「禁止再分发、不入库」的表述 |

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
| [0081](0081-unified-release.md) | 统一发版：一个 v* tag 全量构建 cpp、driver、拾阶，发一个 Athena Release | 已接受；修订 ascent 应用级 0018 的发版入口描述；回退 `c115dd4` 的 driver 独立发版；北极星、磨砚、数学工具随后加入同台矩阵（v9.0.0 起）；决策 1~3 的全量构建与统一版本号由 0171 修订 |
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
| [0125](0125-launcher-webui-tauri-threejs.md) | 启动器 UI 层重选 Tauri 2 + Three.js，学习应用面板改「领域轨道环」3D 构图 | 已接受 |
| [0129](0129-prefer-quality-over-quantity.md) | 内容工作宁缺毋滥：取舍标尺是质量而非数量，空骨架与被取代的旧内容不留占位；参考不得悄悄重划结构、`id` 不改嫁、先入库、显式删除的安全网保留 | 已接受；取代 0054 总原则与第 2 条；0080 适用面收窄为 `id` 不改嫁；不自动清理存量 |
| [0130](0130-shared-build-and-schema.md) | 构建共享、schema 共享：仓库级共享层放通用代码、依赖与公共 schema，应用仍独立进程且互不引用；数据与约束不合并 | 暂缓（见 0132）；原拟取代 0032 决策 2、0043 §1 |
| [0131](0131-shared-layer-location-and-pilot.md) | 共享层放仓库根 `shared/`（不是应用）；以 gtkmm 试点，只换进度层并无损迁移 69 条作答；公共进度 schema 起步为草案，冻结前对照 software/embedded/design-patterns | 不执行（见 0132）；作为重启时的备选保留 |
| [0133](0133-heterogeneous-stack-admission.md) | 异构技术栈准入：栈是教学内容/教学对象、或教学内容生态的原生载体、或存量成熟投入，三者之一才允许非 Tauri 2 + React；machine 的 Qt6 记为历史例外不得效仿；立栈判断写进各应用立项 ADR | 已接受；为「不趋同」（ascent ADR 0066 等应用级自选）立仓库级边界；与 0130 共享层正交 |
| [0134](0134-structural-decisions-cold-down.md) | 结构稳定性：`id` 与目录名一经入库不改名（实质错误须新 ADR 并按牵动面清单一次改齐）；新增/退役/合并、挂靠、圈归属等结构性决定先在 STRUCTURE-PROPOSALS.md 草拟、落 ADR 前重读草稿；使用者显式豁免与紧急修订不受限 | 已接受；与 0129 互补（0129 管要不要留，本篇管定下来不折腾）；反转移到草稿层 |
| [0132](0132-defer-shared-layer.md) | 共享层暂缓：问题存在但课程结构未充实，不值得抽象；0130、0131 不执行，构建隔离与各自进度库照旧，列出重启条件 | 已接受；范围由 0135 收窄为只暂缓 schema 与内容抽象；0043 §1、0037 恢复为现行 |
| [0135](0135-share-low-cost-build-layer-first.md) | 共享分层推进：A 档（同栈核心依赖版本对齐+跨应用版本检查，Rust target 已由启动器共享）现在做，B 档（npm/Cargo workspace）另立 ADR，C 档（schema/内容/通用代码）仍暂缓；同栈不再要求构建隔离，异构栈各自构建 | 已接受；收窄 0132，修订 0032 决策 2；B 档由 0140 落地 |
| [0136](0136-unify-on-pnpm.md) | 前端包管理器统一为 pnpm，去掉 ascent 的特殊：磁盘去重、依赖严格、catalog 与供应链防护优于 npm；迁移保持版本不变 | 已接受；迁移已执行；锁文件由 0140 收到仓库根一份；c-gui-lab 不在此列；修订 0135 决策 3 的 ascent 例外 |
| [0137](0137-viz-shared-package.md) | 可视化呈现件抽成仓库根 `packages/viz`（`@athena/viz`，纯 TS 源码不预编译）：同类功能只留一份实现，六份拷贝的 trace-player 收敛为一份（解析前缀参数化、渲染器按 kind 注册）；不触及 schema/内容/进度库，是 C 档的明示例外；data-structures 先试点，其余使用方逐个迁移，防回流检查跟进 | 已接受；例外于 0135 决策 5 与 C 档；满足 0132 决策 5 第二条重启条件；按 0134 先草拟、复看后落 |
| [0138](0138-course-apps-unify-tauri-react.md) | 课程/讲解/演示类应用统一 Tauri 2 + React（Vue、原生 TS 壳、Qt 壳逐波改造），页面渲染以摘星为基线，schema 不动；共享配置按课程属性四要素准入；machine 改造、c-plus-plus 与 driver 暂缓 | 已接受；修订 0133（默认→强制），取代 0042 决策 1、3；迁移待使用者逐波指派 |
| [0140](0140-shared-tauri-workspace.md) | 同栈 Tauri 应用共用一份 pnpm 工作区与 catalog 版本、一个 `.cache/cargo-target`；课程壳进根 Cargo 工作区，启动器保留自己的工作区但依赖表必须相同 | 已接受；落实 0135 的 B 档；不抽 schema 与应用代码 |
| [0141](0141-split-gtk-cpp-into-practice.md) | 旧 gtkmm 窗口从 C++ 教程拆出，独立为 `practice/cpp`（id `cpp`）；新壳只启动它已经编好的程序 | 已接受 |
| [0142](0142-certification-root-for-driver.md) | 驾考迁到仓库根 `certification/driver`，与 `exercise` 平级；id 仍是 `driver` | 已接受 |
| [0154](0154-docs-site-on-github-pages.md) | 文档站用 MkDocs Material 发布到 GitHub Pages：站点无自有内容，源是 `docs/` 与根文档，暂存时改写链接；`pages.yml` 在文档路径推送时触发，是 0064 的有意例外 | 已接受 |
| [0155](0155-progress-local-first-sync-to-router.md) | 学习进度本地优先、不进 git：本地库放用户数据目录，启动器外置同步代理在能连路由器时推拉到 PG（通用 JSONB 接口、按表声明合并规则），同步对使用者透明；一次全迁，确认中心收到前不撤库出 git | 已接受；修订 0053、0067 决策 2；推广 0067~0070 |
| [0160](0160-append-tombstones.md) | 事件表用墓碑表达删除：只标记、不实质删除，原数据保留；墓碑单向幂等，事件表整张为空时不推断全删 | 已接受（补充 0155 决策 5） |
| [0161](0161-shared-course-shell-crate.md) | 课程应用的 Tauri 壳收成一个共用 crate `athena-course-shell`：六个应用只传名字配置，顺手收紧案例路径校验与 -pthread | 已接受（局部修订 0132） |
| [0162](0162-linear-algebra-books-in-guide.md) | 线性代数手册类教程：Selinger、Siefken 两本书各一个 `guide/` 应用，按考纲裁剪、互不干扰便于对比；跟随原书、内容与习题并存；新开「数学」圈 | 已接受（沿用 0143，增补 0148 的 group 取值） |
| [0163](0163-math-tool-tutorials-in-guide.md) | 数学工具教程：一本书或一门课对应一个 `guide/` 应用；只做 GitHub 上能逐字入库的源，首批 Octave 官方手册（裁剪）与 SymPy 官方教程；示例用真工具复跑、练习自编并经工具核对；GeoGebra 与 Lachniet 小册拿不到，如实写明 | 已接受（沿用 0143、0162） |
| [0164](0164-cloud-limits-handoff-and-content-thickness.md) | 云会话做不到的事统一记进 docs/HANDOFF.md（现状、原因、接手步骤、验收）；新应用内容前期要薄（基础/进阶两层，默认折叠进阶）；数学工具多本好书就一本一个应用；阶段性成果及时合并主分支 | 已接受（补充 0162、0163） |
| [0165](0165-agent-comms-service.md) | 多代理协作通讯抽取为仓库公共服务 comms/（按舱协作：一个主题一个舱、config.json 声明 leader/worker；leader 拆任务与验收、worker 交 review 附证据；正式任务沟通与即时消息双通道）；九州舱暂不迁移照旧运行 | 已接受 |
| [0166](0166-comms-console-and-projection.md) | 协作观察台 comms-console（tools/，Tauri 2 + React，端口 1521）：文件是唯一权威、PG 是投影、观察台只读；看任务泳道、任务流转与裁决时间线、统一对话流；comms.py 加固原子写与 status 乐观锁 | 已接受 |
| [0167](0167-multi-session-task-routing.md) | 多会话并行按任务分箱：任务是路由单位（doing 即绑定声明）、inbox/ack/notify 支持 --mine 与 --task、已读游标按箱分文件、认领冲突防护、可选 --as 会话标记 | 已接受；实现派 comms-console 舱 T-102 |
| [0168](0168-release-mature-apps-uniformly.md) | 相对成熟的应用按同一标准进入发布：取消 0151、0153 对贪吃蛇和中国象棋的发版排除；archived 空壳与仍是 planned 占位的应用不进 | 已接受 |
| [0169](0169-pocket-cube-solver-app.md) | 新增 `programming/pocket-cube-solver`：象棋同款壳 + 七章独立 gtkmm 程序，按初学者层先法的阶段切章，终点是能解任意状态的程序；旧版 `practice/pocket_cube` 原地保留作参考 | 已接受 |
| [0170](0170-release-exclusions-launcher-and-legacy-pocket-cube.md) | 启动器（依赖仓库与开发工具链，不是可独立安装的应用）与旧版 pocket_cube（已定为供参考、不再做）不进发布矩阵，理由写明；machine 等迁到 Tauri 后再进，c-gui-lab 先解决 third_party 可复现 | 已接受 |
| [0171](0171-incremental-release-per-app-versions.md) | 增量发版：应用各有自己的真实版本号（写在各栈清单），只构建有改动的应用；Release 页只放本次构建的；不做逐应用 tag | 已接受；修订 0081 决策 1~3，落地后第一次发版是 10.1.0 |
| [0172](0172-app-updater-for-all-tauri-apps.md) | 应用内自动更新器推广到全部 Tauri 发布应用：官方 updater 全矩阵接入，启动即静默更、失败静默、无手动入口；集中 `app-updates` 标签每应用一个 json；c-gui-lab、driver、practice/cpp 排除；启动器统一更新中心不做 | 已接受；延伸 0081 决策 4 与 0171 |
| [0173](0173-launcher-installable-with-auto-update.md) | 启动器做成安装包并接入应用内自动更新：进发布矩阵；找不到仓库时进安装模式（编译期内嵌 catalog.json，按平台约定判断已安装、启动、指路 Releases）；仓库模式不变 | 已接受；修订 0170 第 1 条与 0172 第 2 条末句 |
| [0174](0174-mathematics-compass-in-mentor.md) | 数学学习导引：`mentor/` 新增 `mathematics-compass`（数学罗盘，图谱/参考类），给数学五个学习应用排唯一推荐路径、写学习目的与掌握要点；如实写明高数缺口；薄壳阅读为主 + 一张可点顺序图 | 已接受 |
