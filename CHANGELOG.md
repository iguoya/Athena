# 更新日志

本文件记录每个发行版本的显著变化。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循语义化版本，以 `meson.build` 为单一来源。

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
