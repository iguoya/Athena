# ADR 0069：令牌层改接 Material 3 ColorScheme——不再沿用 Bootstrap 5 色板

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
| 2 | 语义色改为 `ThemeExtension` 四件套，迁移 `Bs.success` 等使用点（决策 4） | 待办 |
| 3 | 自绘组件按 Material 3 收编：卡片、侧栏、状态徽章（决策 5 的其余部分） | 待办 |

## 后果

- 看得见的变化：四套皮肤的主色变成方案生成的 `primary`（比旧手选色略深，白字对比度
  更好）；页面底、卡片底、分隔线、环境色斑都改读方案角色；侧栏底色与主按钮同色
  （旧版侧栏比主色再深一档）；悬停提示条由深灰改为反色面。
- 不变：题库、进度库、同步、字号基准、圆角与动效令牌、四套皮肤的名字与持久化。
- 第一阶段结束后，语义色仍是旧的 Bootstrap 色值，与新的氛围色并存；这是已知的中间
  状态，到第二阶段收口。
- `Skin` 不再是 `const` 对象，`Skins.all` 随之由 `const` 改 `final`；用到的位置只有
  侧栏皮肤切换器，已一并改。
