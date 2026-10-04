# ADR 0071：令牌层改接 Material 3 ColorScheme——不再沿用 Bootstrap 5 色板

- 日期：2026-10-04
- 状态：已接受
- 影响：`lib/skin.dart`（`Skin` 只存种子色，色彩由 `ColorScheme.fromSeed` 生成）、
  `lib/look.dart`（`buildTheme` 直接用皮肤的 `ColorScheme`，删掉与方案默认值重复的手写
  按钮色与提示条色）、`docs/decisions/0058-skin-token-system.md` 的色板来源说明
- 修订：0058 决策 1 中「皮肤色值手选」与决策 3 中「语义色为 Bootstrap 5 原板」；
  不修订 0058 其余条款（明色、圆角分级、动效令牌）与 0063（默认青野）
- 关系：落实仓库级 ADR 0056 的界面方向；使用者明确取消「Bootstrap 5 观感」这一历史
  约束，界面按 Flutter 统一的 Material 3 样式基因走

## 背景

0058 为迁移当天界面不变，沿用了 Bootstrap 5 的色值（成功绿 `198754`、危险红
`DC3545`……），皮肤色也是逐套手选十六进制。这有三个问题：

1. 仓库里没有任何规则要求 Bootstrap；它只是历史来源，却一直在制约新界面的取色。
2. Flutter 的组件（按钮、输入框、对话框、滚动条、导航）默认都读 `ColorScheme` 的角色。
   我们用 `ColorScheme.light(...)` 只填四个字段，其余角色落回基线默认，再靠手写颜色
   去覆盖，组件每多一种就多一处手写。
3. 手选的色值没有对比度保证，换皮肤要逐个调。

## 决策

1. **色彩来源：每套皮肤只存一个种子色，其余由 Material 3 生成。** `Skin.scheme =
   ColorScheme.fromSeed(seedColor: seed, dynamicSchemeVariant: DynamicSchemeVariant.fidelity)`。
   选 `fidelity` 而不是默认的 `tonalSpot`：实测 `tonalSpot` 把晴空的蓝压成灰蓝
   （`#485D92`）、曙途的橙压成棕（`#8E4D31`），四套皮肤认不出来；`fidelity` 的
   `primaryContainer` 就是种子色本身，`primary` 是它压暗的一档，白字对比度够。
2. **只用现行角色名。** 用 `surface`、`surfaceContainerLowest..Highest`、
   `onSurfaceVariant`、`outlineVariant`、`primaryContainer`、`inverseSurface` 这一组；
   不用 SDK 已标注弃用的 `background`、`onBackground`、`surfaceVariant`，也不以
   `ColorScheme.light()` 的基线默认值为底。`scripts/check.py` 里的 `flutter analyze`
   已经会把弃用成员报出来，不另加检查。
3. **`Bs` 门面保留，getter 改指角色。** 150 多处引用的名字不动：
   `Bs.primary / paper` → `scheme.primary`；`Bs.nav` → `scheme.primary`（侧栏白字）；
   `Bs.light` → `scheme.surface`；`Bs.body` → `scheme.surfaceContainerLowest`；
   `Bs.border` → `scheme.outlineVariant`；环境色斑 → `primaryContainer`、
   `primaryFixedDim`、`secondaryContainer`（不用 `tertiary*`：`fidelity` 下它是种子色的
   互补色，铺到整窗底下偏艳）。
4. **成功、警示、信息、题型、频次这类语义色：分阶段迁。** Material 3 没有对应角色，
   做法是用 `ThemeExtension` 承载，每个语义色由一枚固定种子经同一个 `fromSeed` 生成
   「实心色 / 实心色上的字 / 浅底 / 浅底上的字」四件套，不随皮肤变（含义不变，将来
   若做暗色也只改这一层）。这一步要动 150 多处 `Bs.success` 等常量的使用点，其中不少
   在 `const` 表达式里，**本 ADR 的第一阶段不做**：`Bs.success / warning / info / danger`
   等仍是常量，只有主题层的 `error` 角色已是 Material 3 的值。
5. **组件：第一阶段只让主题层吃方案默认值。** 按钮前景背景、文字按钮、悬停提示条
   （`inverseSurface`）不再手写颜色。`BsCard` 的双层软阴影（0058 决策 5）、自绘图表与
   手写侧栏保持原样，等第三阶段再评估是否换成 `Card.filled` 与 `NavigationDrawer`。
6. **不引入 `dynamic_color` 与系统取色。** 桌面三个平台支持不齐，且「一台机器一个
   口味」由 0058 决策 7 持久化，不跟系统走。
7. **0058 决策 2 不变：只做明色，不做暗色。** 本 ADR 让将来加暗色只需给每套皮肤多
   生成一份 `Brightness.dark` 的方案，不再是逐个色值重调。

## 阶段

| 阶段 | 内容 | 状态 |
|---|---|---|
| 1 | 皮肤与主题层改接 `ColorScheme`（决策 1、2、3、5 的主题部分） | 随本 ADR 提交 |
| 2 | 语义色由 Material 3 方案生成四件套，`Bs.success` 等改接（决策 4，实施方式见下） | 已完成 |
| 3 | 自绘组件按 Material 3 收编：侧栏、徽章；卡片的取舍见下（决策 5 的其余部分） | 已完成 |

## 后果

- 看得见的变化：四套皮肤的主色变成方案生成的 `primary`（比旧手选色略深，白字对比度
  更好）；页面底、卡片底、分隔线、环境色斑都改读方案角色；侧栏底色与主按钮同色
  （旧版侧栏比主色再深一档）；悬停提示条由深灰改为反色面。
- 不变：题库、进度库、同步、字号基准、圆角与动效令牌、四套皮肤的名字与持久化。
- 第一阶段结束后，语义色仍是旧的 Bootstrap 色值，与新的氛围色并存；这是已知的中间
  状态，第二阶段已收口（见下）。
- `Skin` 不再是 `const` 对象，`Skins.all` 随之由 `const` 改 `final`；用到的位置只有
  侧栏皮肤切换器，已一并改。

## 阶段 2 实施记录

- **载体改为静态类，不用 `ThemeExtension`。** 决策 4 原定用 `ThemeExtension`，实施时
  放弃：语义色不随皮肤变、也没有暗色，`ThemeExtension` 的好处（随 `Theme` 变化）用不上，
  却要求 150 多处引用都改成 `Theme.of(context)...`。改为 `lib/semantic.dart` 的
  `Semantic` 四件套（实心色 / 实心色上的字 / 浅底 / 浅底上的字）与全局 `Sem`；将来做
  暗色，要给每个语义多生成一份 `Brightness.dark`，再升级成 `ThemeExtension`。
- **`Bs` 门面名字不变，改指实心色。** `Bs.success / warning / info / danger / purple /
  teal / orange / pink / secondary / dark / accent` 由 `static const` 改为 getter。
  `danger` 取 Material 3 的 `error` 角色，与组件主题同值；`secondary` 取 neutral 变体，
  `dark` 取方案的 `onSurface`。
- **色值整体变深**（对比度由方案保证，白字都能放在实心色上）：例如成功 `#198754` →
  `#006C40`，警示 `#FFC107` → `#785900`（琥珀偏棕），危险 `#DC3545` → `#BA1A1A`。图表里
  的亮黄条变成深琥珀，是已知的观感变化；要保留亮色的地方改用浅底（`container`）。
- **失去 `const` 的位置**约 20 处（`TextStyle(color: Bs.secondary)` 一类），已去掉；
  `BsAlert` 的默认参数 `color = Bs.info` 改为可空、在 `build` 里回退，同 `BsBadge`。
- **新增 `test/semantic_test.dart`**：每个语义色的实心色、浅底与各自的字，对比度不低于
  4.5；每套皮肤主色上能放白字、卡片底与页面底不同色。换种子色或变体后这条仍然守得住。
- **没做的**：把徽章、提示条、图表条改用浅底四件套（`container / onContainer`）——
  现在用得上的位置仍是「实心色 + 透明度」；这属于阶段 3 的组件收编。

## 阶段 3 实施记录

- **侧栏改成 Material 3 导航抽屉的样子。** 底是 `surfaceContainerLow`（仍叠 0.92 透明度透出
  环境色斑），文字与图标 `onSurfaceVariant`，禁用态 38% 透明度；选中行是药丸底
  （`Bs.radiusPill`）。旧版是整条主色底、白字、左侧黄条。同步状态行、皮肤切换器、分隔线
  一并改读方案角色，不再有 `Colors.white` 与写死的 `0xFFDCE9FF`。
- **选中行的底用「主色 14% 透明度铺在侧栏底上」，不用 `secondaryContainer`。** 渲染后
  对比：`fidelity` 方案里 `secondaryContainer` 偏艳，曙途的选中行像一条橙色药丸；主色
  低透明度与徽章是同一个办法（Material 3 状态层的做法），四套皮肤都克制。
- **徽章默认改成浅色调。** `BsBadge` 的底是 `color` 以 14% 透明度铺在卡片底上，字与图标用
  `color` 本身；传了 `foreground` 的才是实心。阶段 2 的一个副作用在这里一并解决：深琥珀
  的警示色放在主色底的侧栏徽章上，是棕底绿底，难看；现在是浅底深字。
- **卡片不改。** `BsCard` 的双层软阴影保留：整窗有环境色斑，卡片靠阴影从色斑上「浮」出来，
  Material 3 的 `Card.filled`（无阴影、靠色阶分层）在这个背景上分不出层。这条原样沿用
  0058 决策 5。
- **图表条、提示条不改。** 它们用实心语义色做条与描边，对比度已由阶段 2 的测试守住。
- **验证方式。** 用一份临时的渲染脚本（`flutter test` 里把页面画成 PNG，不提交）四套皮肤
  逐页目检：首页概览、做题页、标线速记、易混数字、强化练习、考点速记。
