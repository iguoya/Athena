# 驾考学习 · ADR 索引

本目录只记录 **`subjects/driver` 独立应用** 的产品与技术决策。主仓库
`docs/decisions/` 管跨应用规则；精神可对齐，编号互不混用。

| 编号 | 决策 | 状态 |
|---|---|---|
| [0001](0001-subject-one-and-four-only.md) | 只做科目一与科目四理论 | 已接受 |
| [0002](0002-flutter-desktop.md) | 桌面壳用 Flutter | 已接受 |
| [0003](0003-sourced-theory-questions.md) | 题目必须能指到法条或标准 | 已接受 |
| [0004](0004-desktop-workspace.md) | 桌面工作台，不用手机题库的控件妥协 | 已接受 |
| [0005](0005-native-tts-for-explain.md) | 答题解释用系统 TTS 朗读 | 已接受 |
| [0006](0006-phased-subject-one-unlocks-four.md) | 科目一分阶段，过关后才开科目四 | 已接受 |
| [0007](0007-four-questions-per-page.md) | 练习一页四题，答错才朗读，解析按需回看 | 已接受（第 1 条由 0022 修订） |
| [0008](0008-adopt-public-question-banks.md) | 自用软件不受版权束缚，公开题库可以直接收录 | 已接受 |
| [0009](0009-rebalance-subject-one-phases.md) | 科目一四阶段按题量重划 | 已接受 |
| [0010](0010-sync-progress-through-a-github-jsonl.md) | 跨机器同步走 GitHub 私有仓库里的一个 JSONL 事件流 | 已接受 |
| [0011](0011-luoyang-local-questions-in-scope.md) | 考试地在河南洛阳，河南地方性题目照收 | 已接受 |
| [0012](0012-adaptive-group-size-and-side-panel-layout.md) | 分组题量按内容自适应，翻页条挪到左栏底部，右栏顶部加统计方块 | 已接受（第 1 条由 0022 修订） |
| [0013](0013-periodic-auto-sync.md) | 启动时同步一次，之后每 15 分钟自动同步一次 | 已接受 |
| [0014](0014-surface-recorded-achievements.md) | 把已经记录的成就实际展示出来 | 已接受 |
| [0015](0015-add-progress-visualizations.md) | 补三种进度可视化——每日练习柱状图、章节正确率横向对比、掌握度环 | 已接受 |
| [0016](0016-resumable-exam-drafts.md) | 模拟考边答边存草稿，中途重启能续上 | 已接受 |
| [0017](0017-scope-to-c1-c2-license-category.md) | 题库按小型汽车（C1/C2）准驾车型精确裁剪，不收其他车型专属内容 | 已接受 |
| [0018](0018-topic-test-and-chart-navigation.md) | 补一个章节测试入口，图表点一下能跳转 | 部分撤销（第 1、2 条） |
| [0019](0019-confirm-before-timed-test-and-exit-without-submit.md) | 开考前先确认一次，考试中途能退出不用交卷 | 已接受 |
| [0020](0020-remove-hesitant-concept.md) | 撤销「迟疑」概念，答对就算掌握 | 已接受 |
| [0021](0021-launch-window-maximized.md) | 桌面窗口启动时直接最大化 | 已接受 |
| [0022](0022-ten-per-page-auto-advance-when-clean.md) | 一页十题，全对自动翻页 | 已接受 |
