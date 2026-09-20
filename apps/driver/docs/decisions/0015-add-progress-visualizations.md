# ADR 0015：补三种进度可视化——每日练习柱状图、章节正确率横向对比、掌握度环

- 日期：2026-09-20
- 状态：已接受
- 影响：`lib/progress.dart`、`lib/look.dart`、`lib/home.dart`
- 关系：落实主仓库 ADR 0056「可视化与交互是内容本身，不是装饰」；跟本应用
  ADR 0014（把已记录的成就展示出来）是同一批「记了要给人看」的收尾工作

## 背景

科目一/科目四概览页原来只有一个模拟考战绩柱状图（`ExamTrend`）和一排数字统计块
（`StatTile`）。三类现成的数据从来没画出来过：

- 每天练了多少题——`attempts` 表按天聚合，能看出有没有断更，但没人查过。
- 各章节正确率——`topicStats()` 早就能按 `topic_id` 分组算出来，界面上只有练习
  时的题目徽章带章节名，没有一个把全部章节摆在一起比的地方。
- 整体掌握度的分布（已掌握 / 练过没掌握 / 还没见过）——只有一句「已开放掌握
  N/M」的文字统计，没有图。

顺带发现 `look.dart` 里已经有一个 `RateRing`（单一进度环）从来没被用过——不是
这次要补的三色掌握度环能直接复用的（`RateRing` 只画一段弧，掌握度环要三段），
但说明这类「写了没接上」的情况在这个应用里不是第一次出现。

## 决策

1. **`ProgressStore.dailyAttempts(days: 14)`**：按天聚合最近 14 天的作答量与正确率，
   没练的天数补 0（不是不返回），这样柱状图连续、断更一眼看出来。
2. **`DailyActivityChart`**（`look.dart`）：柱状图，颜色按当天正确率分三档；
   `DailyActivityChart.dayStreak()` 顺带算出「从今天往前数，连续有练习的天数」，
   在标题栏写成「连续练习 N 天」——这是 AGENTS.md 提到的「连续日」激励要素目前
   唯一落地的一小步，严格说只是可视化，不是正式的连续日徽章系统。
3. **`TopicAccuracyChart`**（`look.dart`）：横向条形图，一章一条，按正确率从低到
   高排——排在最上面的就是最该补的章节。用现成的 `LinearProgressIndicator`
   实现，不额外画布自绘，跟 `BsProgress` 风格一致。
4. **`MasteryRing`**（`look.dart`）：三色环形图（已掌握绿、练过没掌握蓝、还没见过
   黄），中心写百分比。跟 `_examTrend`、`_recentNotices` 一样的卡片样式，摆在
   科目一、科目四概览页里，紧跟在模拟考战绩后面。

## 后果

- `home.dart` 新增 `_daily`、`_topicStats` 两个状态字段，`_reload()` 多两次查询；
  数据量是本机单人的作答记录，量级不大，没有分页或缓存的必要。
- `look.dart` 因为要用 `DailyCount`/`TopicStats` 类型，新增了对 `progress.dart`
  的依赖——`progress.dart` 不反向依赖 `look.dart`，没有循环引用。
- `RateRing` 依然没人用；它跟这次的 `MasteryRing` 定位不同（单值 vs 三段），
  暂不处理，不在这次范围内展开。
