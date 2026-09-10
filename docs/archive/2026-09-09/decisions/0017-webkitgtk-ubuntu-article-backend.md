# ADR 0017：Ubuntu 使用 WebKitGTK 渲染文章

- 日期：2026-08-28
- 状态：已接受

## 背景

`ArticleView` 已将 Markdown/HTML 生成与平台控件隔离。此前 macOS 使用 WKWebView，
Ubuntu 只有空实现，手册和 AI Markdown 对话框只能显示未排版的原文。

## 决策

- Ubuntu/Linux 构建要求 `webkitgtk-6.0`（Ubuntu 包名 `libwebkitgtk-6.0-dev`）。
- 新增 `render/article_view_webkitgtk.cc`，把 `WebKitWebView` 放进既有文章宿主，
  复用 `ArticleView::load_html()` 与 `scroll_to_anchor()` 契约。
- 保持与 WKWebView 一致的行为：等待页面完成加载后再执行锚点跳转；文章内锚点留在
  当前页面平滑滚动；HTTP(S) 链接交给系统默认浏览器打开。
- macOS 仍链接系统 WKWebView；未知平台保留空实现和纯文本降级，避免把未验证的
  平台假称为受支持。

## 后果

- macOS 与 Ubuntu 都以同一份受控 HTML、CSS 和 JavaScript 呈现文章，手册与 AI
  Markdown 的排版能力一致。
- Linux 开发与 CI 新增 WebKitGTK 开发依赖；Meson 会在 Ubuntu 上缺少该依赖时明确失败。
