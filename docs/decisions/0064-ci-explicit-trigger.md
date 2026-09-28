# ADR 0064：CI 改为显式触发，不再推送即跑

- 日期：2026-09-28
- 状态：已接受
- 影响：`.github/workflows/ci.yml` 的触发条件
- 关系：取代 [ADR 0050](0050-ci-runs-on-release-not-every-push.md)（兑现它写好的
  退出条件）；「支持哪个平台就在 CI 里跑哪个」（[ADR 0047](0047-portable-by-default.md)）
  与降级档位（[ADR 0051](0051-platform-priority-macos-windows-first.md)）不变

## 背景

ADR 0050 让 CI 推送即跑，明确是阶段性安排：跨平台坑清得差不多、连续全绿且没有新增
平台特有修复时，就改成发布与手动驱动，并回来留记录。

到 2026-09-28，情况是：

- 最近 8 次失败全部是**同一个测试**（`subjects/driver/test/session_test.dart` 里交卷后
  固定等 100ms 真实时间），不是平台缺陷——测试自己的时序假设在慢的 Windows runner 上
  不成立。已改成等到结果真的出现再断言。
- 其余二十多个 job 连续多次全绿，这段时间没有新增平台特有修复。
- 日常提交里相当一部分是 `progress: 同步学习进度`——只动进度库，却每次拉起全部 runner。

退出条件已经满足。

## 决策

**1. CI 只在两种情况下跑：**

- **手动**：`gh workflow run ci.yml` 全量，`gh workflow run ci.yml -f app=<id>` 只跑一个
  应用（`cpp` / `c` / `polaris` / `dsa` / `english` / `mathematics` / `driver` /
  `launcher`），或在 Actions 页面点 Run workflow。跨应用的「内容出处」检查便宜，每次都跑。
- **推版本 tag**（`v*.*.*`）：全量。发布本身就是显式动作，发之前必须验完整矩阵。

去掉 `push: branches`、`paths-ignore` 与 `pull_request`：本仓库单人直推 main，PR
触发本质上也是「顺手就跑」。

**2. 什么时候该手动跑**：改了平台相关代码（路径、进程、工具链探测、构建脚本）、
动了依赖或 CI 本身、准备发布。只改内容 JSON、文档、进度库，本地
`python3 scripts/check.py <id>` 足够。

## 后果

- 本地统一入口（ADR 0007）从「提交前该走的一步」变成**唯一的日常门槛**；CI 是按需的
  跨平台确认，不是推上去看红不红的远程编译器（这一点 ADR 0050 就有，现在更要守）。
- 平台回归可能晚几天才被发现——代价换来的是日常提交零 runner 开销、红叉只在真要看的
  时候出现。回归积累到发布前才暴露，就是该更早手动跑一次的信号。
- 按应用过滤用 job 级 `if` 加动态矩阵实现：选一个应用时其他 job 显示为 skipped，
  不占 runner。新增应用时要把它的 id 加进 `workflow_dispatch.inputs.app.options`
  和对应 job 的过滤列表。
