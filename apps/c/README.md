# Athena · C 语言编程（独立应用）

与主程序平级。教学用 **Qt Quick / QML** 写教案（ADR 0042）。

首页是**章**的知识图谱，章序跟 Beej 教程卷：内存与变量、指针、数组、字符串、
结构体、动态分配（ADR 0002）。对齐主程序 C++ 分类页的分层，不是把几个知识点
直接铺在首页。点一章进入该章大纲；教案只能从章内知识点路线图点进来。

教材副本在 `content/sources/reference/`。写课、出题必须能对上节号（ADR 0003）；
语义以 C23 为准（ADR 0004）。

首页图谱点「C 语言编程」会 spawn `app.json` 的 dev 声明。LVGL 小程序仍在
[`playground/`](playground/README.md)，实验台在已构建时把它拉起来。

## 运行

```sh
cd apps/c
athena-dev open c
```

依赖：CMake 与 Qt 6。改 `qml/` 或 `content/` 保存即热加载。

| 平台 | 装 Qt 6 | 找得到吗 |
|---|---|---|
| macOS | `brew install qt@6` | `app.json` 的 `CMAKE_PREFIX_PATH` 已列好 Homebrew 的几个位置 |
| Linux | `apt install qt6-base-dev qt6-declarative-dev` | 装在标准路径，CMake 自己找得到 |
| Windows | Qt 官方安装器 | 路径带版本号，无法预先枚举，自己设 `CMAKE_PREFIX_PATH` 环境变量 |

`app.json` 里的候选路径一个都不存在时不会注入这个变量，所以自己设的那份不会
被覆盖。

刷新本地教材：

```sh
python3 scripts/fetch-sources.py
```

## 目录

| 路径 | 内容 |
|---|---|
| `qml/pages/GraphPage.qml` | 章知识图谱 |
| `qml/lessons/` | 每一节课（QML） |
| `qml/components/` | 共用教学块（含随堂考核） |
| `content/curriculum.json` | 章与知识点 |
| `content/exercises.json` | 随堂与课后题 |
| `content/sources/` | 教材目录与本地副本 |
| `src/` | Qt 壳 |
| `playground/` | 保留的 LVGL 小程序 |
| `app.json` | 声明怎么构建、怎么启动、怎么算就绪；由 `athena-dev` 执行（ADR 0046） |
