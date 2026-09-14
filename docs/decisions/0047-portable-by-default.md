# ADR 0047：通用性优先，删掉为单一平台做的妥协

- 日期：2026-09-14
- 状态：已接受
- 影响：`apps/cpp` 的 `platform/app_paths`、`content/content_loader`、`meson.build`、
  `scripts/package_macos.py`；`apps/cpp/app.json` 的 dev 声明

## 背景

`apps/cpp/platform/app_paths.cc` 里有一段平台分支：取可执行文件路径时，macOS 用
`_NSGetExecutablePath`，其他平台读 `/proc/self/exe`。Windows 两条都不通，直接编不过。

审视它究竟在为什么业务服务，结论是：**为一条冗余的读取路径服务**。

教学源码（`cplusplus/` 下 15 个文件、44 KB）**已经全部打进 GResource** 的
`/app/sources` 前缀。`ContentLoader::load_project_file()` 的逻辑是"先按文件路径读，
读不到再从 GResource 读"——也就是说资源那条路本来就是完整可用的，文件那条只是
"开发时优先读源码树"。

为了这条可有可无的优先级，付出的是：

- 两套取可执行文件路径的平台代码，且没有 Windows 的那一套；
- 一个编译期绝对路径 `ATHENA_SOURCE_ROOT`（装到别的机器就失效，`AGENTS.md` 早已
  禁止生产代码用它，却仍留在这里当兜底）；
- 一段"同一份代码要在源码树、`.app`、Linux 安装前缀三种布局下都能找到内容根"的
  适配逻辑；
- `package_macos.py` 里一个 `copy_teaching_sources()`，把源码再拷一份进 bundle，
  它的注释还写着"这些不走 GResource"——那个说法已经过时了。

更要命的是它还有个隐患：开发时从源码树读，源码框会显示**还没编译进二进制的版本**，
而实验跑的是上次编译的代码。看到的和跑出来的不是同一份。GResource 随构建打包，
永远和二进制同版本。

## 决策

1. **教学内容只从 GResource 读。** `ContentLoader` 不再接受项目根路径，
   `load_project_file()` 直接走 `/app/sources`。源码框显示的内容从此和运行的实验
   保证同版本。
2. **删掉 `executable_directory()` 与 `content_root()`**，连同那段平台分支。
   `ATHENA_SOURCE_ROOT` 仅保留给测试目标（测试只在构建机上跑，编译期路径在那里
   是合理的），生产代码不再使用。
3. **`external_apps_root()` 只认环境变量 `ATHENA_APPS_ROOT`。** 谁要让主程序能从
   图谱打开别的学科，谁就告诉它 `apps/` 在哪——启动器在 `app.json` 的 dev 声明里
   传。主程序不再自己满世界找别人的目录，这也回到了"应用之间不互相引用路径"
   （ADR 0032）本来的边界。拿不到就提示用启动器打开，功能降级而不是崩溃。
4. **`package_macos.py` 不再拷教学源码进 bundle**：GResource 里已经有了。
5. **菜单栏不按平台编译两份实现。** "系统有没有接管应用菜单"不是平台问题，
   是桌面环境的能力问题（Unity、某些 KDE 配置也有全局菜单栏）。GTK 早把它
   抽象成设置项 `gtk-shell-shows-menubar`，运行时问一句就够，
   `menu_bar_platform_macos.cc` / `_other.cc` 两个文件合并成一个。
6. **删掉运行时设置 Dock 图标的 Objective-C++ 实现。** 它只服务"开发时直接跑
   二进制"这一种情形；正式 `.app` 的图标由 `Info.plist` 和 `.icns` 提供，
   Linux 由图标主题提供，两条正路都不需要代码。为此项目不再需要 objcpp 语言
   和 AppKit 框架依赖。
7. **打开 URI 交给系统默认处理器**（`Gio::AppInfo::launch_default_for_uri`），
   不再按平台拼 `open` / `xdg-open` 命令行。"用什么打开这个 URI"本就是系统的事。

## 原则

**通用性优先：一段平台特有代码要留下来，必须是这个平台真的提供了别处没有的能力，
而不是为了某个可有可无的便利。** 遇到"这里要分平台"时，先问三个问题：

1. 这条路径服务的业务是什么？
2. 有没有一条所有平台都走得通的路，能达到同样效果？
3. 如果有，那条平台特有的路还剩下多少价值？

本项目已经确认必须保留的平台代码只有两类：窗口系统的原生集成（macOS 的菜单栏、
应用图标），和进程/窗口管理（启动器里把窗口叫到前面——这件事各平台的能力本就不同，
ADR 0046 已如实记录差异）。除此之外，默认不写平台分支。

## 后果

- **`apps/cpp` 的生产代码里一个平台分支都不剩**：没有 `#ifdef`，没有 `.mm`，
  `platform/` 下只剩两个不含条件编译的小文件。Meson 里只剩一条 macOS 依赖
  （`gtk4-macos`）。Windows 移植从此不必先改代码——剩下的是 GTK4 在 Windows
  的构建与分发，那是构建期一次性的工作（GIMP、Inkscape 都这么发），
  不是代码里的持续负担。
- 开发时改教学源码要重新编译才能在源码框看到——但本来就要重新编译才能运行，
  这不是退步，是把"看到的"和"跑的"重新对齐。
- macOS bundle 少一份源码副本；打包脚本少一个函数。
- 代价：部署时不能再通过摆放目录来替换教学内容（`ATHENA_CONTENT_ROOT` 一并取消）。
  这个能力从来没被用过，教学内容本就该随二进制一起走。
