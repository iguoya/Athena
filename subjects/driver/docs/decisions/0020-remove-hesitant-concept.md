# ADR 0020：撤销「迟疑」概念，答对就算掌握

- 日期：2026-09-20
- 状态：已接受
- 影响：`lib/models.dart`、`lib/progress.dart`、`lib/session.dart`、`test/progress_test.dart`
- 关系：修订 ADR 0005/0007 里「迟疑答对的题练习里还会再出」那一条

## 背景

原来的设计：答对但用时明显超过自己平时节奏（`lingeredVsPace`）算「迟疑答对」，
`masteredQuestionIds()` 用 `WHERE correct = 1 AND hesitant = 0` 把这类作答排除在
「掌握」之外，指望 `appearsInPractice()` 把它们捞回练习队列再考一次。

这条规则本身有一个没堵上的缝：`appearsInPractice` 判断要不要出现在练习里，靠的是
`mastered`（掌握与否）和 `wrong`（最近一次是不是错的）这两个信号，从来不知道
「迟疑」这件事。一道 `regular`/`rare` 档位的题，只要迟疑答对过一次：
`mastered=false`（迟疑不算数）、`wrong=false`（毕竟答对了）、`attempts>=1`
（已经考过）——落进 `appearsInPractice` 判定的死角，永久卡住：界面上看不出
「掌握」也看不出「待练」，用户找不到入口重新回答它，phase 也因为这一道题
差一分永远到不了 100%，连带卡住下一阶段解锁。`hot`/`common` 档位的题因为
`appearsInPractice` 对它们有单独的「无条件出现」分支，不会中招，所以这个坑
只在 `regular`/`rare` 档位的题上炸，长期潜伏没被发现。

## 决策

**直接砍掉「迟疑」这个概念，不修补 `appearsInPractice` 的判断分支。**

1. `masteredQuestionIds()` 改回 `WHERE correct = 1`，不再管 `hesitant`——
   答对就是掌握，跟这道题花了多久没关系。
2. `recordAttempt` 不再计算或接收 `hesitant`，写库时固定存 `0`；
   `hesitant` 这一列留着（数据库不做迁移，历史数据不动），只是不再有任何
   代码去读它、去按它分支。
3. 删掉 `lingeredVsPace`、`recentDurations`（除了这一个用途没有别的调用方，
   一并清掉，不留只声明不使用的函数）。
4. 界面上「答对 · 迟疑」这行提示去掉，`_gradeLine` 只剩「答对/答错」两种。
5. `test/progress_test.dart` 里专门测「迟疑」行为的两个用例删掉。

## 后果

- 从设计上根治了这一类「规则本身留了逻辑死角」的问题——不是把 `appearsInPractice`
  加一个 `hesitant` 分支去接住迟疑答对的题（那样能解决已知的这一个缝，但引入
  「迟疑」信号本身就是给未来留更多这种缝的机会），而是让「答对」只有一种含义。
- 慢答对的题不会被特殊对待，也不会再重复出现——如果确实猜对了但没有真的搞懂，
  暴露的方式是下次遇到类似题答错，走「答错的题会再考」这条本来就有的路，不需要
  额外一层「按用时判断有没有真的掌握」的机制。
- 已经受这个缝卡住的历史数据（作答记录里 `hesitant=1` 但 `correct=1` 的题）
  这次改动之后立刻会被算作「已掌握」，可能让个别阶段的掌握度瞬间从「差一题」
  变成「100%」，进而解锁下一阶段——这是修复卡死状态的正常结果，不是 bug。
