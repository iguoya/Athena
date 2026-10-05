# ADR 0111：lib 按职责分子目录，拆开挤在一个文件里的东西

状态：已接受

## 背景

`lib/` 平铺 50 个文件，几个文件里装着不属于它的东西：`home.dart` 里有整个「易混数字页」（其余速记页都是独立文件），
`look.dart` 里除了设计令牌和基础组件还有一整套统计图表，`main.dart` 里塞着登录屏和同步设置屏，
`recall.dart` 里自测界面与作答状态判定、状态圆混在一起，同步设置屏还靠 `findAncestorStateOfType` 去够启动门的私有状态。
后台代理（ZCode）改动期间又陆续加了文件，位置没有统一考虑。

## 决定

1. **拆文件**：易混数字页 → `speed/numbers_page.dart`（`NumbersPage`，与各速记页同构，首页只接作答记录与练习队列）；
   统计图表 → `ui/charts.dart`；登录屏、同步设置屏 → `app/`；作答状态枚举与判定函数、状态圆、「练这组」按钮样式 →
   `speed/recall_status.dart`（`recall.dart` 只留自测的界面流程）。
2. **按职责分子目录**：`core/`（模型、内容加载、进度库、同步、学习者目录、朗读）、`ui/`（设计令牌与基础组件、图表、皮肤、语义色、图标表）、
   `app/`（启动门里的整屏）、`study/`（做题台、组卷、强化练习、学习诊断、考点簇）、`speed/`（速记专题与自测、各速记页、规范图绘制）、
   `subject2/`（科目二）；`main.dart`、`home.dart` 留在 `lib/` 根。目录说明写进 `AGENTS.md`。
3. **去掉隐式耦合**：同步设置屏的「先离线用」由 `onSkipDirect` 回调交给启动门，不再向上够私有状态。
4. 易混数字页里一段永远为 0 的「还有多少题在没解锁的阶段里」（组级题和已开放题是同一批）一并删掉。
5. 纯搬迁与拆分，不改行为；`test/` 的 import 同步改成新路径，读源码的 `test/glyphs_test.dart` 指向 `lib/ui/glyphs.dart`。

## 后果

- 历史 ADR 里写的旧路径（如 `lib/home.dart` 里的数字页、`lib/recall.dart` 里的状态点）按本 ADR 对照；ADR 只增不改，不回头订正。
- 加新文件前先看它属于哪个目录；跨目录的依赖方向是 `speed`、`study`、`subject2`、`app` → `ui`、`core`，不反过来。
