# T-012 验证

2026-10-22，本机 Windows。cursor 无额度，leader（zcode）接手完成。

## 改动

1. **用时记录**：`drill_runs` 新增本地列 `seconds`（INTEGER，手动填的秒，可不填），
   `recordDrillRun(seconds:)` 入库，不进 outbox（与 T-015 的 point_hit 同一做法，不新开同步资源）。
2. **复盘录入**（`review.dart`）：每把在点位三选一后面加「用时秒」输入框（可不填）；
   该项有时限（content 的 `limit_text`）且填入超过时限时，行内出红色「超时」徽标并附评判条款
   （倒库 GA 1026—2022 6.2.3.1 d)、侧方 6.2.3.4 b)，与这两项最后一步 caution 引的一致；
   无时限项不判）。
3. **简报显示**（`brief.dart` + 项目简报卡）：`ItemBrief.times` 汇总窗口内填了用时的把（新的在前），
   项目页简报卡显示「最近用时 m:ss / m:ss · 限 3.5 分钟」，只展示事实不评价。
4. **默演计时**（`rehearsal.dart`）：AppBar 加可选计时按钮，开了每秒走格、只计时不催促、
   不自动结束（ADR 0042「只计时不收卷」）；停表读数留在原地可再计；做完结果页显示总用时。

时限秒数由 `limitSecondsOf` 从内容 `limit_text` 换算（「3.5 分钟」→210），内容是唯一事实源。

## 测试

`test/drill_time_test.dart`（新增，5 例）：用时入库且 outbox 不含该键、applyRemote 不冲掉本地用时、
简报 times 派生、录入页超时徽标随填入出现/消失（含无时限项不判）、保存链路、默演计时器开关与做完停表。

`python scripts/check.py --skip-build`（本目录）真实退出码 0：内容 JSON、静态分析、全部 371 个测试通过。

## 顺手修复（接手过程中发现的既有问题）

1. T-013 给 caution 加 GB/T 30341 出处后，`subject2_test` 的摘录核对还假定所有 locator 都是
   GA 1026—2022，GB/T 条目被按错误前缀解析导致红；已按标准前缀泛化断言，并在
   `content/sources/reference/excerpts.md` 补上 GB/T 30341—2013 的公式条目（注明转载来源与
   「不冒标 GA 1029」），让出处门禁真正走通。
2. 复盘页新增用时输入框后 `practice_day_test` 用 `find.byType(TextField)` 不再唯一；教练的话
   输入框加了 `review-note-<itemId>` key，测试改用。
（教训：先前两次检查的退出码被 `| tail` 管道吞掉，这次改为直接取 check.py 退出码。）
