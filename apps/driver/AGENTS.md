# Athena Driving — 项目协作规则

本文档是 **`apps/driving` 独立应用** 的项目级指令。本应用与仓库里其他学习应用
**平级、可脱离**：不读别人的配置、不链接别人的代码，不依赖别的进程即可完成
开发、构建与练习。

改本应用时以本文为准。启动器通过 `app.json` 发现并拉起它（主仓库 ADR 0032 /
0046），那不是运行本应用的前提。

## 定位

- 目标：把中国机动车理论考里的 **科目一** 和 **科目四** 练到考场规则够用。
- 科目四在法规里的名字是 **科目三安全文明驾驶常识**；界面用学习者口头称呼，
  出处写法规名。
- 不做科目二场地、科目三上路，也不做手机 App。
- 题目必须能指到法律、行政法规、部门规章或国家标准（ADR 0003）。不收录商业
  驾考题库原题。
- 掌握度只由作答写入，禁止手动标记熟练。

## 技术栈

- **壳**：Flutter 桌面（macOS / Windows / Linux）
- **界面**：Dart + Material 3；标志用 `CustomPaint` 自绘，不嵌 WebView
- **内容**：`content/curriculum.json` + `content/questions/*.json`
- **进度**：SQLite，用户数据目录 `AthenaDriving/learning.db`，知识点 ID 前缀
  `drive.`（主仓库 ADR 0037）

不引入 GTK、Qt、Tauri。开发时内容从 `ATHENA_DRIVING_ROOT` 读磁盘，改 JSON
热重启即可看到；发行包才走 Flutter assets。

## 目录

| 路径 | 职责 |
|---|---|
| `content/` | 课表、题库、出处 catalog；**唯一内容源** |
| `lib/` | 界面、组卷、进度 |
| `app.json` | 怎么构建、怎么启动、怎么算就绪 |
| `docs/decisions/` | 本应用 ADR |
| `scripts/check.py` | 本应用验证入口 |
| `scripts/run_dev.py` | 按平台调用 `flutter run` |

## 开发与验证

需要 Flutter SDK（stable）。没有放进 PATH 时，脚本会再找 `~/flutter`。

```sh
cd apps/driving
athena-dev open driving
```

不要启动打包副本。改题库后在运行中的窗口热重启一次。

```sh
python3 scripts/check.py              # JSON + analyze + test + 当前桌面 debug 构建
python3 scripts/check.py --skip-build # 只改了题库时
```

仓库根 `python3 scripts/check.py driving` 会转到这里。

## 出题

1. 打开 `content/sources/catalog.json` 里的来源，核对照条文或标准分类。
2. 每题带 `prompt`、恰好能判分的 `choices`、`explain`、`source_refs`。
3. `relation` 用 `quoted` / `adapted` / `authored`；自造要写 `note`，同一文件
   不得超过一半。
4. 标志题只描述形状颜色，界面自绘示意，不扫描 GB 5768 图样。
5. 模拟考按 GA 1026 的题量与时长组卷；题库不够考场题量时折合百分制，并在结果
   页说明。
