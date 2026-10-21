# 历史归档：未收录的条目（programming/design-patterns）

来源是旧 GitHub 仓库 `DesignPattern`、`DesignPatterns`、`Practice`、`Linux`、`algorithm`（ADR 0176）。以下内容**没有**进应用的「历史归档」章节；旧仓库只会被设为 archived，历史完整保留，需要时从那里取回。清单与去重证据见 `comms/legacy-archive/artifacts/zcode/`（manifest-design-patterns、dedup-report）。

## 重复拷贝（内容逐字节相同，只收一份）

| 旧路径 | 说明 |
|---|---|
| `Linux/DesignPattern/**`（311 个文件） | `DesignPattern` 仓库的完整镜像 |
| `Practice/DesignPatterns/**`（71）、`DesignPatterns/workspace/**`（68） | 六个经典模式（SimpleFactory、Factory、AbstractFactory、Singleton、Observer、Adapter）与 `DesignPattern/` 内容一致；`workspace/TemplateMethod` 与 `workspace/Strategy` 是独有版本，已收 |
| `algorithm/design-patterns` 以外的各处 `docs/` 笔记副本 | 同一批 Markdown 在 `DesignPattern/docs`、`DesignPatterns/docs`、`Linux/DesignPattern/docs` 里各存了一份（含目录改名残留的 18 对同内容双份），只收 `algorithm/design-patterns` 里独有的三篇 |

## 第三方内容

| 旧路径 | 原因 |
|---|---|
| `DesignPatterns/docs/W设计模式课件`（58 个文件） | 某网课的官方配套代码包与讲义的整套拷贝，非自写 |
| `DesignPattern/docs/SampleModule`、`auto_gallery`、`sample_gallery`（45 个文件） | sphinx-gallery 官方文档示例模块原样拷贝，与设计模式无关 |

## 没有内容价值

| 旧路径 | 原因 |
|---|---|
| `DesignPattern/State/`（10 个文件） | 只有一份 `state.vpp` 与它的 8 份自动备份：当年只画了类图，没写代码 |
| `DesignPattern/*/*.vpp.bak_*`、`.lck`、`Debug/`、CodeLite/StarUML 工程产物、IDE `.user` 文件 | 工具自动备份与本机配置（约数 MB） |
| `DesignPattern/UML/`、`DesignPattern.mdj`、`Untitled.mdj` | StarUML 图档，仅服务于 Qt 壳的 UML 展示；Qt 壳作为 `qt` 应用的 `qt.arc.dpshell` 条目收录，图档随之 |
| `DesignPatterns/AAA`、`CCC`、`DesignPatterns`（Xcode 壳） | 2020-09-19 生成的 Hello World 模板，没改一行 |

## 归入其他应用

| 旧路径 | 去向 |
|---|---|
| `DesignPattern/main.cpp`、`mainwindow.*`、`resource.qrc`、`.pro`（Qt 壳） | `programming/qt`，条目 `qt.arc.dpshell` |
| `Linux/DesignEvolutionCpp` | gtkmm 跟练改造，归 `programming/gtkmm-lab` |
