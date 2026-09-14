# Athena · C 语言编程（独立应用）

与主程序平级。教学用 **Qt Quick / QML** 写教案（ADR 0042）。

首页是**章**的知识图谱（对象与字节、指针、数组、结构体、函数与地址、堆与寿命、
字符串），对齐主程序 C++ 分类页，不是把几个知识点直接铺在首页。点一章进入该章
大纲；教案只能从章内知识点路线图点进来。

首页图谱点「C 语言编程」会 spawn `scripts/dev.sh`。LVGL 小程序仍在
[`playground/`](playground/README.md)，实验台在已构建时把它拉起来。

## 运行

```sh
cd apps/c
./scripts/dev.sh
```

依赖：CMake、Qt 6（`brew install qt@6`）。改 `qml/` 或 `content/` 保存即热加载。

## 目录

| 路径 | 内容 |
|---|---|
| `qml/pages/GraphPage.qml` | 章知识图谱 |
| `qml/lessons/` | 每一节课（QML） |
| `qml/components/` | 共用教学块 |
| `content/curriculum.json` | 章与知识点 |
| `src/` | Qt 壳 |
| `playground/` | 保留的 LVGL 小程序 |
| `app.json` | 主程序发现用 |
