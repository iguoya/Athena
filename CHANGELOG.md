# 更新日志

本文件记录每个发行版本的显著变化。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循语义化版本，以 `meson.build` 为单一来源。

## [Unreleased]

### 新增

- GitHub Release 新增 Ubuntu x86_64 的 `.deb` 与 AppImage 资产；`.deb` 为推荐的
  APT 原生安装方式，AppImage 面向 Ubuntu 24.04 及以上相近环境的便携下载。

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
