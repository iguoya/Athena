# ADR 0003：文章章节统一 WebView 渲染，不保留 GTK 文章回退

- 日期：2026-08-14（2026-08-15 补记）
- 状态：已接受
- 依据提交：`daacc94` Markdown 文章章节、`f4c6a17` WKWebView、`7fd39ef` 合并
  目录与正文、`e64d00b` 简化为 WebView 单一路径

## 背景

文章章节引入时同时存在 GTK 正文控件与 WebView 两条路径。字号调节、明暗主题、
锚点跳转等排版能力需要在两个后端重复实现，维护成本高且观感不一致。

## 决策

- 共享层（`render/markdown_renderer`）生成完整 HTML：文章目录、标题锚点、
  字号与明暗主题；平台 ArticleView 后端只负责加载 HTML 和管理原生控件生命周期。
- macOS 使用系统 WKWebView。
- 永不提供 GtkTextView/GTK 文章回退。
- Linux 的接入路径是 WebKitGTK 6.0（经同一 ArticleView 接口）；尚未实现，
  当前非 macOS 平台为 `article_view_unavailable` 存根。

## 后果

- 非 macOS 平台文章阅读暂缺，这是被接受的现状，不是待修复缺陷
  （`ARCHITECTURE.md` 渐进式改造第 9 项）。
- HTML/CSS/JS 排版权威集中在 `markdown_renderer`，新增平台只需实现 ArticleView。
