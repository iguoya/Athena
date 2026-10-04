# 驾考学习 · ADR 索引

本目录只记录 **`subjects/driver` 独立应用** 的产品与技术决策。主仓库
`docs/decisions/` 管跨应用规则；精神可对齐，编号互不混用。

| 编号 | 决策 | 状态 |
|---|---|---|
| [0001](0001-subject-one-and-four-only.md) | 只做科目一与科目四理论 | 已接受（第 1、3、4 条由 0054 对齐现状） |
| [0002](0002-flutter-desktop.md) | 桌面壳用 Flutter | 已接受 |
| [0003](0003-sourced-theory-questions.md) | 题目必须能指到法条或标准 | 已接受（第 3 条由 0024 修订） |
| [0004](0004-desktop-workspace.md) | 桌面工作台，不用手机题库的控件妥协 | 已接受 |
| [0005](0005-native-tts-for-explain.md) | 答题解释用系统 TTS 朗读 | 已接受 |
| [0006](0006-phased-subject-one-unlocks-four.md) | 科目一分阶段，过关后才开科目四 | 已接受（第 2、3 条由 0044 撤销） |
| [0007](0007-four-questions-per-page.md) | 练习一页四题，答错才朗读，解析按需回看 | 已接受（第 1 条由 0022 修订） |
| [0008](0008-adopt-public-question-banks.md) | 自用软件不受版权束缚，公开题库可以直接收录 | 已接受 |
| [0009](0009-rebalance-subject-one-phases.md) | 科目一四阶段按题量重划 | 已接受（题量区间由 0026 取消） |
| [0010](0010-sync-progress-through-a-github-jsonl.md) | 跨机器同步走 GitHub 私有仓库里的一个 JSONL 事件流 | 已接受 |
| [0011](0011-luoyang-local-questions-in-scope.md) | 考试地在河南洛阳，河南地方性题目照收 | 已接受 |
| [0012](0012-adaptive-group-size-and-side-panel-layout.md) | 分组题量按内容自适应，翻页条挪到左栏底部，右栏顶部加统计方块 | 已接受（第 1 条由 0022 修订） |
| [0013](0013-periodic-auto-sync.md) | 启动时同步一次，之后每 15 分钟自动同步一次 | 已接受 |
| [0014](0014-surface-recorded-achievements.md) | 把已经记录的成就实际展示出来 | 已接受 |
| [0015](0015-add-progress-visualizations.md) | 补三种进度可视化——每日练习柱状图、章节正确率横向对比、掌握度环 | 已接受 |
| [0016](0016-resumable-exam-drafts.md) | 模拟考边答边存草稿，中途重启能续上 | 已接受（第 5 条「超时续上即交卷」由 0042 撤销；第 4、5 条由 0043 修订） |
| [0017](0017-scope-to-c1-c2-license-category.md) | 题库按小型汽车（C1/C2）准驾车型精确裁剪，不收其他车型专属内容 | 已接受 |
| [0018](0018-topic-test-and-chart-navigation.md) | 补一个章节测试入口，图表点一下能跳转 | 部分撤销（第 1、2 条） |
| [0019](0019-confirm-before-timed-test-and-exit-without-submit.md) | 开考前先确认一次，考试中途能退出不用交卷 | 已接受 |
| [0020](0020-remove-hesitant-concept.md) | 撤销「迟疑」概念，答对就算掌握 | 已接受 |
| [0021](0021-launch-window-maximized.md) | 桌面窗口启动时直接最大化 | 已接受 |
| [0022](0022-ten-per-page-auto-advance-when-clean.md) | 一页十题，全对自动翻页 | 已接受（第 2、3 条由 0025 修订） |
| [0023](0023-exam-follows-test-centre.md) | 模拟考按考场的判分方式和内容比例走 | 已接受（修订 0007、0016 第 3 条；「提前结束」由 0041 撤销） |
| [0024](0024-sign-meaning-questions.md) | 标志、标线、交警手势收「认含义」题，不收「认类别」题 | 已接受（修订 0003 第 3 条） |
| [0025](0025-auto-advance-when-page-done.md) | 一页十题答完就自动翻页，不看对错 | 已接受（修订 0022 第 2、3 条） |
| [0026](0026-phase-size-follows-content.md) | 阶段题量随内容走，不设上下限 | 已接受（修订 0009） |
| [0027](0027-practice-by-national-error-rate.md) | 练习按全国错误率排序，易错题标出来 | 已接受 |
| [0028](0028-confusable-numbers-page.md) | 易混数字对照页 | 已接受 |
| [0029](0029-subject4-trim-other-vehicle-duties.md) | 科目四里其他车型驾驶人的专属知识标偏难 | 已接受（修订 0017 第 4 条） |
| [0030](0030-find-working-tree-from-executable.md) | 直接点开调试包也认得出工作树，一台机器只有一份进度库 | 已接受 |
| [0031](0031-each-question-once-per-round.md) | 一轮练习里每道题只出一次 | 已接受 |
| [0032](0032-rare-questions-capped-in-exams.md) | 模拟考可以抽到偏难怪，每卷封顶 2% | 已接受（修订 0026、0029 的「不考」；回到 0003 原意） |
| [0033](0033-pre-exam-review.md) | 考前复习——累计错 2 次以上的题单独成页 | 已接受（第 2 条由 0034 修订） |
| [0034](0034-review-exit-by-correct-streak.md) | 考前复习动态进出——错几次就要连对几次才移出 | 已接受（修订 0033 第 2 条；第 2 条由 0035 修订） |
| [0035](0035-review-exit-by-correct-margin.md) | 退出考前复习——答对次数至少比答错多 1～2 次 | 已接受（修订 0034 第 2 条） |
| [0036](0036-subject2-c2-rules-drills-and-animations.md) | 科目二（C2）：评判规则题、操作动画讲解、练车错因记录 | 已接受（修订 AGENTS.md「不做科目二场地」） |
| [0037](0037-subject2-brief-reference-points-rehearsal.md) | 科目二配合线下练车：练车前简报、个人点位卡、默演模式 | 已接受 |
| [0038](0038-page-dwell-at-least-five-seconds.md) | 自动翻页前至少停留 5 秒 | 已接受（修订 0025 的停顿时长） |
| [0039](0039-subject2-organized-around-practice-days.md) | 科目二围绕「练车日」组织，不沿用科目一的练习形式 | 已接受 |
| [0040](0040-subject2-narration-cautions-marks.md) | 科目二动画加语音讲解、注意事项与画面标注 | 已接受 |
| [0041](0041-exam-continues-after-failing.md) | 模拟考错到不可能及格也继续答完 | 已接受（撤销 0023 的提前结束） |
| [0042](0042-exam-timer-without-deadline.md) | 模拟考只计时，到点不收卷 | 已接受（撤销 0016 第 5 条的超时交卷） |
| [0043](0043-always-resume-exam-draft.md) | 开始模拟考总是接着上次没交的那一卷 | 已接受（修订 0016 第 4、5 条） |
| [0044](0044-subject1-no-unlocking.md) | 科目一不设解锁，四个阶段和模拟考全部开放 | 已接受（撤销 0006 第 2、3 条） |
| [0045](0045-collect-remaining-public-bank-questions.md) | 补收公开题库剩余题目，同考点换问法也收，逐道核对现行规定 | 已接受 |
| [0046](0046-low-trust-source-questions.md) | 低可信来源的题量不大时也收，答案逐道按条文重核 | 已接受 |
| [0047](0047-subject2-unlocks-at-steady-95.md) | 科目二要等科目一模拟考稳定在 95 分以上才开放 | 已接受 |
| [0048](0048-car-app-icon.md) | 应用图标改用上色的小汽车，界面标志用同一份 | 已接受 |
| [0049](0049-icon-glossary.md) | 界面图标对照表：一个概念一个图标，统一实心风格 | 已接受 |
| [0050](0050-sidebar-subject-tree.md) | 侧栏按科目分目录，章节挂在所属科目底下 | 已接受（修订 0004 侧栏排列） |
| [0051](0051-pin-cross-subject-entries.md) | 错题本、考前复习等跨科目入口钉在侧栏底部 | 已接受（修订 0050 第 4 条） |
| [0052](0052-exam-explains-wrong-answers.md) | 模拟考答错也当场讲、自动朗读 | 已接受（修订 0023、0005 第 4 条） |
| [0053](0053-quick-turn-when-last-correct.md) | 一页最后一题答对，1 秒就翻页 | 已接受（修订 0038） |
| [0054](0054-align-scope-docs-with-current-state.md) | 范围说明对齐现状：ADR 0001 几条已被后续决定取代 | 已接受（修订 0001 第 1、3、4 条） |
| [0055](0055-explanations-carry-content-and-term-rule.md) | 解释必须讲内容；解释里「科目三」「科目四」的写法 | 已接受（第 2 条由 0056 取代） |
| [0056](0056-subject3-is-road-test-subject4-is-theory.md) | 叫法统一：科目三 = 路考，科目四 = 安全文明驾驶常识 | 已接受（取代 0055 第 2 条，修订 0001 第 1 条的写法） |
| [0057](0057-attempt-kind-and-duration-cap.md) | 作答记录带场合标记（practice/exam），单题用时封顶 5 分钟；历史按交卷时间窗回填 | 已接受 |
| [0058](0058-skin-token-system.md) | 皮肤令牌系统：一套组件换氛围，只做明色 | 已接受 |
| [0059](0059-sign-gallery-page.md) | 标志速记页——手绘标志成为可浏览的内容 | 已接受 |
| [0060](0060-page-fade-and-number-slide.md) | 换页淡入与数值滑入，动效收窄到两处 | 已接受 |
| [0061](0061-chart-hover-and-empty-actions.md) | 图表悬停取值与空态行动入口 | 已接受 |
| [0062](0062-sync-pull-parallel-and-trigger-upload-only.md) | 同步在外网环境提速：拉取并行、写入触发只上传 | 已接受 |
| [0063](0063-default-skin-meadow.md) | 默认皮肤改为青野 | 已接受 |
| [0064](0064-keypoints-notes-page.md) | 考点速记页——情景要点对照，条目挂出处 | 已接受 |
| [0065](0065-markings-gallery-page.md) | 标线速记页——路面读法成为可浏览的内容 | 已接受 |
| [0066](0066-split-rules-topic.md) | 拆分 drive.s1.rules：一个知识点装三分之一的题，薄弱点看不细 | 已接受 |
| [0067](0067-gauge-gallery-page.md) | 仪表速记页——车内符号成为可浏览的内容 | 已接受 |
| [0068](0068-henan-notes-page.md) | 河南速记页——地方条例的差异成为可浏览的内容 | 已接受 |
| [0069](0069-reinforce-round-size-and-stubborn-list.md) | 强化练习：轮量可调与反复错题清单 | 已接受 |
| [0070](0070-fresh-questions-under-topic.md) | 章节下的「练新题」入口 | 已接受 |
| [0071](0071-material3-color-scheme-tokens.md) | 令牌层改接 Material 3 ColorScheme——不再沿用 Bootstrap 5 色板 | 已接受 |
| [0072](0072-withdraw-doubtful-questions.md) | 下架答案存疑或题面有问题的题 | 已接受 |
| [0073](0073-gesture-gallery-page.md) | 手势速记页——修订 0064 决策 4 的「手势不做图」 | 已接受 |
| [0074](0074-crime-penalty-cheatsheet.md) | 易混数字加「刑罚档位」组——罪名与刑期的对照 | 已接受 |
| [0075](0075-stubborn-questions-pinned-in-reinforce.md) | 累计答错 3 次以上的题常驻强化练习 | 已接受 |
