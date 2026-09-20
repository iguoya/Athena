# ADR 0016：模拟考边答边存草稿，中途重启能续上

- 日期：2026-09-20
- 状态：已接受
- 影响：`lib/progress.dart`（新表 `exam_drafts`，数据库版本 4→5）、`lib/session.dart`、
  `lib/home.dart`

## 背景

模拟考期间选的答案只存在 `_SessionStageState._picked` 这个内存里的 Map，只有点
「交卷」才会一次性写进 `attempts` 表——这是刻意的设计，跟考场「交卷才判分」一致
（ADR 0007）。但这意味着交卷前如果 Windows 端进程崩溃、被系统重启、或者应用被
不小心关掉，整场模拟考的作答**全部丢失**，包括几十道题都白答了，屏幕上也不会有
任何提示——用户发现之前是先问出来的，不是应用自己说的。

练习模式不受影响：练习模式每答一题 `_commit()` 立刻落盘，这条 ADR 只管模拟考。

## 决策

1. **新表 `exam_drafts`**（`draft_key` 主键），记录一份「进行中的模拟考」需要
   重建现场的全部信息：题目 id 顺序、`ExamRules` 的几个字段、`fullBank`、已选
   答案（题号 -> 选项 id 集合）、开考时刻。一个 `draft_key` 同时只留一份。
2. **`draft_key` 按「科目 + 哪一种考」区分**：全库模拟考是 `<subjectId>.exam`，
   阶段测试是 `<subjectId>.phase<N>`——同一科目的全库模拟考和某阶段测试互不
   覆盖对方的草稿。
3. **每次选择答案就存一次草稿**（`_pick()` 里 `_isExam` 分支，`unawaited`，
   不阻塞点选手感），交卷成功后立刻清掉草稿；用户主动放弃续答时也清掉。
4. **入口在 `_startExam`/`_startPhaseTest`**：抽新卷之前先查一次有没有同
   `draft_key` 的草稿，有就弹窗问「继续上次」还是「放弃重新开始」；继续则
   按草稿重建 `Paper`（题目 id 找不到题库里对应题目的情况——比如题库改动过——
   直接放弃草稿，不强凑）。
5. **倒计时按「原始开考时刻」算，不是「续上的时刻」**：`SessionLaunch.resumeStartedAt`
   传的是草稿里存的开考时间，`_SessionStageState.initState()` 用它跟当前时间的
   差算出还剩多少分钟；挂起太久已经超时的，续上后直接按超时自动交卷处理，不能
   靠「续上」白嫖额外时间。
6. **续上后跳到第一道没答的题**，不用从头翻一遍已经答过的。

## 后果

- 数据库版本升到 5；新库直接带这张表，旧库走 `_createV5` 升级，不影响已有的
  `attempts`/`exams`/`notices`/`achievements` 数据。
- 练习模式完全不受影响，`draftKey`/`resumePicked`/`resumeStartedAt` 都是
  `SessionLaunch` 上的可选字段，练习场景不传就是 `null`。
- 草稿只解决「进程没了」这一类中断，不是多设备同步的机制——`exam_drafts`
  不参与 ADR 0010/文件夹同步的事件流导出，只在本机起作用。
