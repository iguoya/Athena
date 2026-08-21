# Athena

为快速渐进学习和掌握 C++ 而开发的自用软件平台，突出学练合一：把零散的代码知识点学习整合到统一框架中，方便运行验证和自我修正。基于 GTK4（gtkmm4）、GtkSourceView 5、MD4C、Meson 和 Blueprint。

GtkSourceView 5 用于源码框的 C++ 语法高亮与行号显示，MD4C 用于把文章章节的
Markdown 转换为 HTML。macOS 使用系统自带的 WKWebView 和统一的文章 CSS，
文章目录、正文和阅读设置由同一个 HTML 页面原生控制；当前不保留 GTK 文章
阅读回退，Linux 后端将来可以在同一 ArticleView 接口下接入 WebKitGTK 6.0。
macOS 可通过 Homebrew 安装
`gtksourceview5 md4c nlohmann-json googletest`；Ubuntu 使用开发包
`libgtksourceview-5-dev libmd4c-dev nlohmann-json3-dev libgtest-dev`。

统一校验、构建并运行测试：

```sh
scripts/check.sh
```

该脚本依次执行 JSON 校验、项目生成器检查、Meson 配置、构建和测试；可用
`--build-dir` 与 `--buildtype` 覆盖默认构建目录和构建类型。

测试包括：`athena-core` 独立验证章节 JSON、Markdown 转换和演示注册表；
`athena-gtk-resources` 只构造 Blueprint/GResource 中的关键控件，不启动完整窗口；
两个项目生成器测试分别校验真实配置和四个生成子命令。

只检查项目配置而不构建：

```sh
python3 scripts/generate_project.py \
  --project-root . --config resources/athena.json check
```

统一生成器还提供 `resources`、`registry` 和只创建缺失文件的 `scaffold` 子命令，
具体用法见 `docs/CODE_GENERATION.md`。

教学源码由 `athena.json` 驱动并随 GResource 打包：开发运行优先显示仓库中的实时
源码，发行版在没有源码目录时读取应用内置副本。

生成当前 Mac 架构的未公证 `.app` 和 DMG：

```sh
meson setup build-release --buildtype=release -Dstrip=true
meson compile -C build-release
meson test -C build-release --print-errorlogs
python3 scripts/package_macos.py \
  --project-root . --binary build-release/Athena \
  --output-dir dist
```

版本号默认读取 `meson.build`，显式传入不一致的 `--version` 会被拒绝。

发行包会携带 GTK 和其他非系统动态库，但当前只使用 ad-hoc 签名，尚未完成 Apple
Developer ID 签名和公证。完整流程见 `docs/RELEASE.md`。
