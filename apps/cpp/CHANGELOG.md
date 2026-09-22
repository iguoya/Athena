# 更新日志

本文件记录每个发行版本的显著变化。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循语义化版本，以 `meson.build` 为单一来源。

## [7.0.0] - 2026-09-23

### 变更

- **优化启动器统一管理**：跨平台托盘启动器统一发现、构建与打开各学习 /
  实践应用（含 `apps/practice` 实践分区）；Windows 上按应用构建系统注入
  MSYS2 UCRT64 或 Qt 路径，避免 Meson / CMake 工具链互相踩脚。

### 新增

- **Windows 进入正式发行**：标签 Release 现在除了 macOS DMG 和 Ubuntu DEB / AppImage，
  还产出 `athena-cpp-VERSION-windows-x64.msi` 与同内容的便携 zip。打包入口是
  `scripts/package_windows.py`，从 Meson 的 `athena-cpp.exe` 收集 UCRT64
  GTK 运行时，换机不需要再装 MSYS2。
- 驾考学习在 Windows 上按 UTF-8 编译源文件（MSVC `/utf-8`），窗口标题「驾考学习」
  不再被系统代码页 936 读成非法字符。

### 修复

- 启动器在 Windows 上点名微软雅黑 UI（以及各平台带简体字形的 UI 字体）。
  Slint 缺字回退在英文 Windows 上会先命中 Yu Gothic，简体独有的「语」「习」「结」
  会画成空白。

## [6.0.0] - 2026-09-14

### 变更

- **跨平台优先升为仓库级强约束（ADR 0047）**，管技术选型、代码编写和构建过程三段。
  按这条原则把 `apps/cpp` 的平台分支清零：教学内容只从 GResource 读（删掉两套取
  可执行文件路径的实现和编译期绝对路径）；菜单栏改问 GTK 的 `gtk-shell-shows-menubar`
  设置项；删掉运行时设 Dock 图标的 Objective-C++ 实现；打开 URI 交给系统默认处理器。
  现在生产代码里没有 `#ifdef`、没有 `.mm`，Meson 里只剩一条 macOS 依赖。
- **验证入口从 shell 迁到 Python**（`scripts/check.py`）：验证每天都要跑，不该要求
  Windows 上先装 Git Bash 或 WSL。步骤、参数、输出与原来一致。
- 连测试代码也不再依赖 POSIX：`chmod`/`S_IRUSR` 换成 `g_chmod` + 八进制权限位，
  `setenv`/`unsetenv` 换成 GLib 版本，写死的 `/tmp` 换成 `Glib::get_tmp_dir()`。
- 三个 Tauri 应用的 `rusqlite` 开 `bundled`，不再要求目标机器上有 libsqlite3；
  `apps/mathematics` 的 venv 解释器按存在与否在 `bin/python` 和 `Scripts/python.exe`
  之间挑。

### 新增

- **CI 扩到三个平台**：C++ 教程在 macOS / Ubuntu / Windows（MSYS2 UCRT64）各跑一遍
  同一条 Python 入口，启动器在三平台矩阵里构建。启动器三平台全绿；C++ 教程的
  Windows job 标为实验性——它卡在上游（MSYS2 现行 giomm 与 glib 头文件冲突），
  本仓库这边已无障碍，保留 job 持续探测。

### 修复

- Blueprint 编译在 Windows 上按 UTF-8 读 `.blp`（`PYTHONUTF8=1`），否则遇到中文
  会按系统代码页解码后崩溃。

## [5.0.0] - 2026-09-14

### 变更

- **仓库结构重排：C++ 教程降级为 `apps/cpp`，所有学习应用平级（ADR 0045）。**
  仓库根不再有任何 C++ 源码、构建文件、脚本或文档；`AGENTS.md` 分层为仓库级与
  应用级，ADR 按影响面分家（编号不重排，两处各自延续）。
- **各应用只声明怎么启动，执行统一由编排器负责（ADR 0046）。** `app.json` 的 `dev`
  块写环境变量、准备步骤、长驻命令和就绪判据；五份 `scripts/dev.sh` 全部退役。
  编排器统一注入 PATH 补全与共享的 `CARGO_TARGET_DIR`，三个 Tauri 应用不再各编
  一份依赖。
- 构建目录统一叫 `build`（原 `builddir`）；`apps/cpp` 根上散落的源文件按语义归入
  `platform/`、`ui/`、`packaging/`。
- 实验窗口改为纵向"当前目标 → 真实源码 → 运行验证 → 观察结果"证据链，减少阅读与
  实验之间的横向视线跳跃。
- Linux CI / Release 安装依赖与 Meson 对齐：去掉已不再链接的 WebKitGTK、md4c-html；
  DEB 运行时依赖补上 `libmd4c0`。

### 新增

- **启动器（ADR 0044、0046）**：`launcher/` 下三个前端共用一个编排器——跨平台的
  托盘常驻窗口（Rust + Slint）、macOS 菜单栏常驻应用（Swift，⌃⌥A 唤出）、
  终端的 `athena-dev`。列表是图块网格，每个应用自带图标，有历史演进关系的学科
  之间画连线（目前 C → C++）。

### 移除

- 移除运行历史、双记录比较、git 快照及"AI 讲解差异"，让执行链路只负责当前实验；
  旧数据库中的 `run_history` 表和记录保留原样，不做破坏性删除。
- 删除仅服务于旧 HTML/WebView 路径的 `cpp_syntax_highlighter`（内容已由 GTK
  `DocumentView` + GtkSourceView 承载，该模块无调用方）。
- 删除各应用 `bin/` 下转发到 dev 脚本的别名、`apps/c/playground` 的构建产物，
  以及一个遗留的 worktree 副本。

### 修复

- 取消启动时强制进入 macOS 原生全屏，主窗口改用 1440×900 的适中默认尺寸；
  同时缩小实验窗口，确保系统标题栏和关闭按钮在常见屏幕工作区内可见。
- 首页说明区块铺满页宽，消除 `gtk_widget_measure` 的尺寸协商告警。

## [3.0.0] - 2026-08-29

### 新增

- 加入 Ubuntu 与 macOS 的跨平台软件部署：GitHub Release 现提供 Ubuntu x86_64 的
  `.deb` 与 AppImage，以及 macOS Intel、Apple Silicon 的 DMG；`.deb` 为推荐的 APT
  原生安装方式，AppImage 面向 Ubuntu 24.04 及以上相近环境的便携下载。

## [2.0.1] - 2026-08-29

### 新增

- Ubuntu 文章阅读页接入 WebKitGTK 6，与 macOS 的 WKWebView 使用同一套 HTML
  渲染、目录跳转、主题和字号控制能力。

### 修复

- VS Code 的 Meson 构建、GDB 调试和 C++ IntelliSense 配置，修复 Ubuntu 下
  GTK 头文件路径导致的构建失败。

## [2.0.0] - 2026-08-21

### 新增

- AI 服务集成：接入火山方舟豆包（优先）与 DeepSeek（回退），支持 AI 自测
  （按知识点源码生成选择题，本地按正确率换算 0-5 星熟练度）、运行历史里
  两次记录的"AI 讲解差异"、章节"本章总纲"文档生成。
- SQLite 本地学习数据存储：知识点熟练度、运行历史（含源码快照、耗时、
  git 提交与工作区脏标记，可两两并排对比）、应用内 AI 服务商 Key 设置。
- 学习进度统计页：环形图看整体掌握占比、直方图看熟练度分布、按章节列出
  完成度，作为欢迎页之后的合成标签页。
- 手册系统：article 章节改为按分类聚合的 Markdown 阅读页（合成标签页），
  macOS WKWebView 统一渲染目录、正文、字号与明暗主题。
- 知识点五星评分体系：重要度（内容作者标注的客观难度，只读）与熟练度
  （AI 自测换算，只读）两套独立指标。
- 内容：TypeSemantics（初始化、auto/decltype 推导、值类别、类型转换、
  强类型枚举）与 RAII（RAII 思想、独占/共享/弱引用指针、右值引用、移动
  语义）共 12 个知识点全部实现并接入注册表。
- 桌面集成：应用图标 `cn.athena.icon`、Dock 图标、设置面板。
- 关于对话框；项目改用木兰宽松许可证第二版（Mulan PSL v2）授权。

### 变更

- 教学实现默认约定改为单文件 `.hpp`：TypeSemantics、RAII 从 `.hpp`+`.cpp`
  （RAII 曾是 `.hpp` + 3 个 `.cpp`）迁移为单文件，对齐 Reference 的既有
  模式，源码框展示的始终是完整、一致的整章代码。
- `MainWindow` 持续模块化：`AiService`、`ProgressPage`、`LearningDialogs`
  依次拆分为独立模块，非 GTK 部分可脱离窗口单独测试（ADR 0014）。
- 作者配置（`resources/athena.json`）改为唯一数据源并集中校验，
  `ChapterCatalog` 只解码生成器产出的规范化 Catalog，不再自行解释默认值。
- 本地与 CI 验证统一入口 `scripts/check.sh`。
- 移除笔记功能和知识点级"AI 讲解"按钮——体验验证后判定不如直接看手册和
  源码实用；旧数据库的 `note` 列保留不删，不影响历史数据。

### 修复

- 学习数据存储：旧库升级到新增列时的崩溃、异常处理加固。
- 熟练度直方图裁切与中文标签渲染。
- AI 请求临时文件：修复继承自父进程的过期临时目录、创建失败的处理。
- AI 自测评分后学习进度统计未及时刷新。
- 源码面板切换知识点后选中状态丢失。

## [1.0.0] - 2026-08-15

### 新增

- 文章章节：Markdown 阅读页由共享层生成 HTML，macOS WKWebView 统一渲染目录、
  正文、字号与明暗主题，不保留 GTK 文章回退。
- 源码显示：GtkSourceView 提供 C++ 语法高亮与行号，知识点选择与源码高亮联动。
- 代码闭环：`athena.json` 数据驱动章节目录，函数注册表由配置生成，知识点可
  独立运行并显示输出；教学源码随 GResource 打包，安装后仍可查看真实源文件。
- macOS 发行：`package_macos.py` 生成可携带 `.app` 与 DMG，`v*.*.*` 标签触发
  双架构 Release 自动构建（ad-hoc 签名，未公证）。

### 变更

- 项目版本号统一为 `meson.build` 单一来源，打包器拒绝不一致的 `--version`。
- 本地与 CI 验证统一入口 `scripts/check.sh`。

## [0.1.0] - 2026-08-15

- 首个打包发行版本：建立分类、章节、知识点三级导航与运行闭环，Reference 与
  RAII 知识点可运行；引入 macOS 可携带应用打包流程。
