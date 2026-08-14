# Athena

C++ 学习指南桌面应用，基于 GTK4（gtkmm4）、GtkSourceView 5、MD4C、Meson 和 Blueprint。

GtkSourceView 5 用于源码框的 C++ 语法高亮与行号显示，MD4C 用于把文章章节的
Markdown 转换为 HTML。macOS 使用系统自带的 WKWebView 和统一的文章 CSS，
文章目录、正文和阅读设置由同一个 HTML 页面原生控制；当前不保留 GTK 文章
阅读回退，Linux 后端将来可以在同一 ArticleView 接口下接入 WebKitGTK 6.0。
macOS 可通过 Homebrew 安装
`gtksourceview5 md4c`；Ubuntu 使用开发包
`libgtksourceview-5-dev libmd4c-dev`。
