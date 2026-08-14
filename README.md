# Athena

C++ 学习指南桌面应用，基于 GTK4（gtkmm4）、GtkSourceView 5、MD4C、Meson 和 Blueprint。

GtkSourceView 5 用于源码框的 C++ 语法高亮与行号显示，MD4C 用于把文章章节的
Markdown 转换为 HTML。macOS 使用系统自带的 WKWebView 和统一的文章 CSS，
文章目录、正文和阅读设置由同一个 HTML 页面原生控制；当前不保留 GTK 文章
阅读回退，Linux 后端将来可以在同一 ArticleView 接口下接入 WebKitGTK 6.0。
macOS 可通过 Homebrew 安装
`gtksourceview5 md4c googletest`；Ubuntu 使用开发包
`libgtksourceview-5-dev libmd4c-dev libgtest-dev`。

构建并运行测试：

```sh
meson setup builddir
meson compile -C builddir
meson test -C builddir --print-errorlogs
```

测试包括：`athena-core` 独立验证章节 JSON、Markdown 转换和演示注册表；
`athena-gtk-resources` 只构造 Blueprint/GResource 中的关键控件，不启动完整窗口；
两个项目生成器测试分别校验真实配置和四个生成子命令。

项目配置检查：

```sh
python3 scripts/generate_project.py \
  --project-root . --config resources/athena.json check
```

统一生成器还提供 `resources`、`registry` 和只创建缺失文件的 `scaffold` 子命令，
具体用法见 `docs/CODE_GENERATION.md`。

教学源码由 `athena.json` 驱动并随 GResource 打包：开发运行优先显示仓库中的实时
源码，发行版在没有源码目录时读取应用内置副本。
