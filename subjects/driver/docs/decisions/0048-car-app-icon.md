# ADR 0048：应用图标改用上色的小汽车，界面标志用同一份

- 日期：2026-09-30
- 状态：已接受
- 影响：`icon.svg` 及 `app.json` 里 `icon.renders` 声明的派生位图、`lib/look.dart`
  （`AppMark`）、`lib/home.dart` 侧栏标题、`pubspec.yaml` assets
- 关系：落实仓库 ADR 0065 第 1 条（启动器、任务栏、应用界面三处同源），
  替换其第 2 条选型表里驾考的「红绿灯」

## 背景

仓库 ADR 0065 给驾考挑的是 Fluent Emoji 红绿灯（身份概念取「科目一、四考交通法规」）。
但应用界面侧栏标题旁一直是 Material 的 `directions_car` 小汽车，没换成红绿灯——
界面和任务栏各是一个标志，违反 ADR 0065 第 1 条。

使用者看过之后的意见：小汽车更合适，就用侧栏左上角那个，能上色更好。
备考的是小型汽车驾照（C2 / C1，ADR 0017），科目二也在应用里，身份取「小汽车」
比取「交通法规」更贴。

## 决策

1. `icon.svg` 换成 Material Icons `directions_car`（Filled，Apache 2.0）上色版：
   红色车身，挡风玻璃和车灯是字形里的镂空、在车身下垫浅蓝和黄色透出来，
   轮胎盖一层深灰。出处、许可与改动写在 SVG 顶部注释里。
2. 侧栏标题的标志改用 `AppMark`：显示 `icon.svg` 派生的 `icon.png`，开发时读工作树、
   发行包走 assets，跟题图同一条路。不在界面里另画一个车。
3. 派生位图照 ADR 0065 由 `launcher icons` 生成并提交。

## 后果

- 启动器图块、任务栏、窗口、侧栏标志是同一辆车。Windows 的 exe 图标要重新构建才换。
- 以后换图标只改 `icon.svg`，跑 `launcher icons`，界面标志自动跟着变。
