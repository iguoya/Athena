# ADR 0047：跨平台优先——技术选型与代码编写的默认原则

- 日期：2026-09-14
- 状态：已接受
- 范围：**整个仓库**，所有学习应用与启动器
- 影响：`apps/cpp` 的 `platform/`、`content/content_loader`、`meson.build`、
  `scripts/package_macos.py`；`apps/cpp/app.json` 的 dev 声明；今后所有选型决定

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

## 原则：跨平台优先

这条原则管两件事——**选什么技术**和**怎么写代码**，适用于仓库里每一个应用。

### 技术选型

1. **跨平台是选型的硬指标，不是加分项。** 引入一个库、框架或工具之前，先确认它在
   macOS、Linux、Windows 上都能用；只在部分平台可用的，要么找等价替代，要么在 ADR
   里写明为什么值得，以及另外那些平台怎么降级。
2. **优先选把平台差异自己吃掉的抽象。** GIO 的 `launch_default_for_uri` 胜过拼
   `open` / `xdg-open`；GTK 的 `gtk-shell-shows-menubar` 设置项胜过判断"是不是
   macOS"；Rust 标准库和 Slint 胜过各写一份原生界面。这类抽象往往还更正确——
   按平台判断会漏掉同一平台上的例外（Linux 也有全局菜单栏的桌面环境）。
3. **能在构建期解决的，不要留到运行期。** 应用图标、包元数据、依赖收集都属于打包
   工作，不该变成代码里的分支。GTK4 在 Windows 要收集一批 DLL，那是构建期一次性的
   事（GIMP、Inkscape 都这么发），不构成技术选型的减分项。
4. **构建过程本身也跨平台。** 构建系统、检查入口、开发脚本都要能在三个平台上跑
   （Meson、CMake、Cargo、npm 都满足，`.sh` 不满足——Windows 上要靠 Git Bash 或
   WSL）。只有**产出安装包的那一步**允许是平台专用的，因为产物本就不同
   （`.dmg` / `.deb` / `.msi`）；验证、生成、启动这些每天都要跑的环节不允许。
   CI 也一样：支持哪个平台，就在 CI 里跑哪个平台，否则支持会悄悄退化。

### 代码编写

想写 `#ifdef`、`.mm`、或按平台挑源文件之前，先回答三个问题：

1. 这条分支服务的业务是什么？
2. 有没有一条所有平台都走得通的路，能达到同样效果？
3. 如果有，那条平台特有的路还剩下多少价值？

**一段平台特有代码要留下来，必须是这个平台真的提供了别处没有的能力，而不是为了
某个可有可无的便利。** 留下来的也必须：关在单独一个模块里、不外泄到调用方、
其他平台有明确的降级行为（返回空、提示改用别的入口），而不是编不过或崩溃。

目前全仓库确认必须保留的平台代码只有一类：**进程与窗口管理**——启动器要把已运行的
窗口叫到前面，各平台的能力本就不同（Wayland 出于安全根本不允许），ADR 0046 已如实
记录差异并让它降级提示。除此之外，默认不写平台分支。

### 已知的待清理项

这份清单立在 2026-09-14。2026-09-15 逐条复核的结果记在下面——**判据在
[ADR 0049](0049-portability-is-a-cost-benefit-call.md) 之后不再是「有没有做到
三平台对称」，而是成本收益**，所以有几条的结局是「明确排除」而不是「修好」。

已经做掉的：

- ~~`apps/mathematics` 的 `engine.rs` 写死 `engine/.venv/bin/python`~~ —— 已按
  POSIX 与 Windows 两种布局各留一个候选；建环境的 `setup-engine.sh` 也改写成
  Python，改用标准库 `venv.EnvBuilder` 拿解释器路径。
- ~~三个 Tauri 应用的 `rusqlite` 没开 `bundled`~~ —— 已经是 `bundled`，SQLite
  源码跟着一起编，不再需要目标机器上有 libsqlite3。
- ~~验证入口和各应用检查脚本是 `.sh`~~ —— 根入口与五个应用的检查脚本全部是
  Python，`apps/c` 的 `fetch-sources.sh` 也一并改写。仓库里只剩
  `launcher/macos/scripts/` 下两个 macOS 专用安装脚本。

明确排除，不再当欠账（ADR 0049）：

- **`apps/cpp` 在 Windows 上编不过**：MSYS2 现行的 giomm 2.86 与 glib 2.90 头文件
  冲突（`GDBusActionGroupClass` 重复声明）。本仓库这边没有障碍，倒在 gtkmm 自己的
  头文件上——**上游问题，成本不由我们控制**。`apps/cpp` 支持 macOS 与 Ubuntu，
  CI 里不再保留探测 job。
- **`apps/dsa` 的实验编译不认 MSVC 的 `cl.exe`**：它的命令行参数是另一套，要为它
  单独写一份编译调用。Windows 上装 MSYS2/MinGW 或 LLVM 即可，`g++` / `clang++`
  都认得。

仍然是欠账：

- 启动器的窗口前置在 Windows 上未实现（`runner.rs` 里预留了位置）。目前的降级是
  如实返回「已经在运行」，不崩溃也不假装成功。

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
