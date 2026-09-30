# ADR 0049：界面图标对照表——一个概念一个图标，统一实心风格

- 日期：2026-09-30
- 状态：已接受
- 影响：新增 `lib/glyphs.dart`（`Glyph`）与 `test/glyphs_test.dart`；`lib/` 下所有界面文件
  改用 `Glyph.xxx`
- 关系：ADR 0048（小汽车是应用标志，不当功能图标）

## 背景

2026-09-30 盘点时，界面里直接写了 90 种 Material 图标，没有任何约定：

- 同一个字形实心、描边混着用：科目二「规则自测」小节标题是 `quiz_outlined`，紧挨着的
  按钮是 `quiz`；另有 timer、play_circle、article、error、warning_amber 五组。
- 一个图标身兼数职：旗子同时是「科目一掌握进度」「结束本轮」「科目二考前」；
  打开的书同时是「解析」「出处」「项目手册」「说明」；`fact_check` 同时是「考前复习」
  和「复盘今天」；`record_voice_over` 同时是「默演」和「朗读开关」；小汽车同时是
  侧栏标志和「练了几把」。
- 反过来，同一个意思用了不同图标：「错」有时是 `close`（叉）有时是 `cancel`，
  而 `close` 本来是「关闭」。

看图标认不出意思，图标就只剩装饰。

## 决策

1. **一个概念只用一个图标，一个图标只表示一个意思。** 对照表写成代码：
   `lib/glyphs.dart` 的 `Glyph` 一个概念一个常量，界面代码只写 `Glyph.xxx`，不直接写
   `Icons.xxx`。加新图标先在表里加一行，挑一个表里没用过的字形。
2. **统一 Material 实心（Filled）风格**，不用 `_outlined`、`_outline`、`_rounded`、
   `_sharp` 变体。
3. **小汽车 `directions_car` 留给应用标志**（ADR 0048），不进表。
4. `test/glyphs_test.dart` 读源码守住：表里没有重复字形、没有描边变体、没有小汽车，
   `lib/` 别的文件里没有 `Icons.`。
5. 「对」和「错」各是一个概念：`check_circle` 表示答对、已掌握、操作成功，
   `cancel` 表示答错、还错着、默演漏了；`close` 只表示关闭 / 退出。

## 对照表

以 `lib/glyphs.dart` 为准，改表时两处一起改。

| 概念（用在哪） | 图标 | 常量 |
|---|---|---|
| **导航与科目** | | |
| 科目一 | `gavel` | `Glyph.subject1` |
| 科目二 | `local_parking` | `Glyph.subject2` |
| 科目四 | `health_and_safety` | `Glyph.subject4` |
| 未解锁 | `lock` | `Glyph.locked` |
| 已解锁（科目一已过关） | `lock_open` | `Glyph.unlocked` |
| 错题本、错题数 | `bookmark` | `Glyph.wrongBook` |
| 提醒：错题本清空 | `bookmark_remove` | `Glyph.wrongBookCleared` |
| 考前复习、复习题数 | `fact_check` | `Glyph.review` |
| 易混数字 | `pin` | `Glyph.numbers` |
| **科目一 / 科目四：练习、考试与题目** | | |
| 开始一轮练题（待练 N 题、练这组、规则自测、练评判题） | `list_alt` | `Glyph.practice` |
| 章节 | `article` | `Glyph.topic` |
| 题目数、题库、规则自测小节 | `quiz` | `Glyph.question` |
| 待练 | `pending_actions` | `Glyph.pending` |
| 模拟考试入口、考场题量与时长 | `assignment` | `Glyph.mockExam` |
| 交卷 | `assignment_turned_in` | `Glyph.submit` |
| 提醒：模拟考未及格 | `assignment_late` | `Glyph.examFailed` |
| 模拟考战绩 | `timeline` | `Glyph.examHistory` |
| 限时 | `timer` | `Glyph.duration` |
| 各章节正确率 | `bar_chart` | `Glyph.topicAccuracy` |
| 最近 N 天 | `date_range` | `Glyph.recentDays` |
| 离目标还差多少（掌握进度、未解锁时要做的事） | `flag` | `Glyph.goal` |
| 结束本轮、准备好了去练车 | `done_all` | `Glyph.finish` |
| 第几题（本轮位置） | `format_list_numbered` | `Glyph.position` |
| 稳定编号 | `tag` | `Glyph.serial` |
| 高频 | `local_fire_department` | `Glyph.hot` |
| 其他出题档（常考、常规、偏难） | `signal_cellular_alt` | `Glyph.band` |
| 易错（全国错误率高） | `warning_amber` | `Glyph.errorProne` |
| 判断题 | `thumbs_up_down` | `Glyph.kindJudge` |
| 单选题 | `radio_button_checked` | `Glyph.kindSingle` |
| 多选题 | `library_add_check` | `Glyph.kindMulti` |
| 解析 | `lightbulb` | `Glyph.explain` |
| 出处、标准原文 | `menu_book` | `Glyph.source` |
| 朗读 | `volume_up` | `Glyph.readAloud` |
| 关掉朗读 | `volume_off` | `Glyph.readAloudOff` |
| 均速 | `speed` | `Glyph.speed` |
| **对错与订正** | | |
| 对：答对、已掌握、操作成功 | `check_circle` | `Glyph.correct` |
| 错：答错、错了几次、还错着、默演漏了 | `cancel` | `Glyph.wrong` |
| 顽固（错 3 次以上） | `priority_high` | `Glyph.stubborn` |
| 订正中 | `trending_up` | `Glyph.improving` |
| 薄弱项 | `trending_down` | `Glyph.weak` |
| 已移出考前复习 | `playlist_remove` | `Glyph.graduated` |
| 按科目分 | `category` | `Glyph.bySubject` |
| **激励与提醒** | | |
| 最近提醒 | `notifications` | `Glyph.notice` |
| 连对 | `bolt` | `Glyph.streak` |
| 章节全部掌握 | `verified` | `Glyph.topicDone` |
| 及格、新成就 | `emoji_events` | `Glyph.achievement` |
| **科目二：练车日与项目手册** | | |
| 练车日 | `today` | `Glyph.practiceDay` |
| 项目手册 | `library_books` | `Glyph.handbook` |
| 练车日志 | `history` | `Glyph.log` |
| 科目二考前 | `sports_score` | `Glyph.examReady` |
| 练车前 | `wb_sunny` | `Glyph.beforeDrill` |
| 练车后 | `nights_stay` | `Glyph.afterDrill` |
| 练车前简报、今天练车的重点 | `checklist` | `Glyph.brief` |
| 复盘今天 | `rate_review` | `Glyph.reviewDay` |
| 记一把练车 | `edit_note` | `Glyph.record` |
| 练车记录 | `insights` | `Glyph.runs` |
| 练了几把 | `repeat` | `Glyph.runCount` |
| 按考场规则能过 | `task_alt` | `Glyph.passable` |
| 按练车日看趋势 | `show_chart` | `Glyph.trend` |
| 每一项最近的表现 | `table_chart` | `Glyph.formTable` |
| 练车失分 | `error` | `Glyph.mistake` |
| 还没练过 | `fiber_new` | `Glyph.untried` |
| 评判规则 | `rule` | `Glyph.rules` |
| 注意事项 | `report` | `Glyph.caution` |
| 经验要点 | `tips_and_updates` | `Glyph.tips` |
| 点位卡 | `push_pin` | `Glyph.pointCard` |
| 教练说过 | `campaign` | `Glyph.coach` |
| 默演 | `record_voice_over` | `Glyph.rehearse` |
| 说完了，对照 | `visibility` | `Glyph.compare` |
| 有动画示意 | `animation` | `Glyph.animation` |
| 多一把 | `add_circle` | `Glyph.more` |
| 少一把 | `remove_circle` | `Glyph.less` |
| 加照片 | `add_photo_alternate` | `Glyph.addPhoto` |
| **动画播放** | | |
| 播放、开始 | `play_arrow` | `Glyph.play` |
| 暂停 | `pause` | `Glyph.pause` |
| 只播这一步 | `play_circle` | `Glyph.playStep` |
| 上一步 | `skip_previous` | `Glyph.stepBack` |
| 下一步 | `skip_next` | `Glyph.stepNext` |
| 从头 | `replay` | `Glyph.restart` |
| **同步** | | |
| 跨机器同步、立即同步 | `cloud_sync` | `Glyph.sync` |
| 同步失败 | `sync_problem` | `Glyph.syncFailed` |
| 云盘文件夹 | `cloud` | `Glyph.cloudFolder` |
| GitHub 备份 | `backup` | `Glyph.backup` |
| 仓库与令牌 | `key` | `Glyph.credentials` |
| 选择目录 | `folder_open` | `Glyph.chooseFolder` |
| **通用操作** | | |
| 下一组、下一项 | `arrow_forward` | `Glyph.next` |
| 返回 | `arrow_back` | `Glyph.back` |
| 进入、去练 | `chevron_right` | `Glyph.goTo` |
| 关闭、退出 | `close` | `Glyph.close` |
| 说明 | `info` | `Glyph.info` |
| 编辑 | `edit` | `Glyph.edit` |
| 删除 | `delete` | `Glyph.delete` |
| 保存 | `save` | `Glyph.save` |
| 列表圆点（装饰） | `circle` | `Glyph.bullet` |

## 后果

- 同一个意思在侧栏、概览、答题页、科目二各页长得一样；看到一个图标能反推它的意思。
- 旧写法里几处换了图标：「结束本轮」改为双勾，科目二「考前」改为终点旗，「解析」改为
  灯泡，「项目手册」改为书架，「复盘今天」改为评注，朗读开关改为喇叭，「练了几把」改为
  重复，「错」统一为带圈的叉。
