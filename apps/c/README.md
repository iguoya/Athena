# Athena · C 语言编程

和主程序（C++ / GTK / Meson）**平级的独立学习应用**：自己的构建系统、
自己的界面技术、自己的内容体系。主程序只做一件事——把它当作一个进程启动。

## 为什么独立

C 语言教学最值钱的部分是"看见内存里发生了什么"，适合用一套面向嵌入式风格的
图形库自己画；把它塞进 GTK 主程序会让两边互相牵制。做成独立进程之后，这边
崩了不影响主程序，换掉窗口库主程序也一行都不用改。

## 边界

- 不 include 主程序的任何头文件，主程序的 Meson 也不引用这里的任何路径。
- 不读 `resources/athena.json`；章节和文档都在 `content/` 下自己管。
- 唯一共享的基础设施是**学习库**：同一个 SQLite 文件，路径由主程序通过
  `--store` 传入，表结构的 owner 是主程序，这边只读写 `knowledge_progress`
  的约定两列。知识点 ID 以 `c.` 开头。

## 构建

```sh
cmake -S apps/c -B apps/c/build
cmake --build apps/c/build
```

窗口后端需要 `vendor/lvgl/` 和 SDL2，见 [vendor/README.md](vendor/README.md)。
两者任一缺失时会编译成占位实现——能启动、能连学习库、不开窗口，用来验证
链路是否打通。

## 中文显示

界面中文由 `src/cjk_font.c` 在运行时加载系统字体渲染（LVGL 的 tiny_ttf，内置
stb_truetype，不需要额外依赖）。候选路径覆盖 macOS 的冬青黑体/苹方/华文黑体和
Ubuntu 的 Noto Sans CJK、文泉驿，找不到时用 `ATHENA_C_FONT` 指定：

```sh
ATHENA_C_FONT=/path/to/font.ttf ./build/athena-c
```

**不要改用 LVGL 内置的 `lv_font_simsun_16_cjk`**。它不是"CJK 全集"，而是生成时用
`--symbols` 写死的约一千个字，且明显偏日文与繁体——有「應」「經」没有「应」「经」，
显示简体中文会大面积缺字变方框。它只作为系统字体加载失败时的兜底。

另外 `lv_conf.h` 把内存分配改成了系统 `malloc`：LVGL 默认是 64KB 固定内存池，那是
给单片机的，光栅化汉字字形时会直接耗尽并让 stb 断言失败退出。

## 运行

```sh
apps/c/build/athena-c --store ~/Library/Application\ Support/Athena/learning.db
```

主程序首页的「C 语言编程」块就是这么把它启动起来的。直接不带参数运行也可以，
只是不记录进度。

## 目录

| 路径 | 内容 |
|---|---|
| `src/main.c` | 参数解析与启动 |
| `src/progress.{h,c}` | 共用学习库的读写，只碰约定的两列 |
| `src/app_window.h` | 窗口接口；两个实现由 CMake 择一编译 |
| `src/ui/window_placeholder.c` | 依赖未就位时的占位实现 |
| `content/` | 章节、文档、实验源码 |
| `vendor/` | 第三方源码（LVGL），不进仓库历史 |
| `app.json` | 给主程序读的清单：标题、图标、可执行文件位置 |
