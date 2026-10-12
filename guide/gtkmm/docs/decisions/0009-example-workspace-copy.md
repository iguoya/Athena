# ADR 0009：官方示例的工作区副本——VS Code 打开真实工程

- 日期：2026-10-12
- 状态：已接受
- 延续：应用 ADR 0006（exercise/ 镜像禁止就地修改）、主仓库 ADR 0059
  （骨架实验：骨架只读、学习者副本在工作区、可重置）

## 背景

官方示例卡（ADR 0006）提供「编译并运行」与页内源码查看，但都是只读
体验：exercise/ 是上游镜像，不允许就地修改。学习者想「从真实工程项目的
角度」查看、编辑、运行示例——改代码、设断点、看编译错误——需要另一个
落点。workspace/ 的既有约定（一集一独立 CMake 工程、副本可改可删、
构建产物不入库）就是为此而设。

## 决策

1. **副本在 `workspace/<示例 id>/`**（id 的 `.` 换 `-`，如
   `workspace/example-buttons-button/`，与 `exp.*` 骨架副本同一落点约定）。
   由壳的 `open_example_workspace` 生成：官方源文件从 exercise/ 镜像原样
   复制，另生成壳写的工程文件——独立 `CMakeLists.txt`（target 与清单
   `build_target` 一致）、`README.md`（来源、构建命令、重置方式）。
   副本已存在则原样复用，**不覆盖个人改动**；重置 = 删掉目录重新打开。

2. **VS Code 配置按当前平台生成**：`.vscode/tasks.json`（configure / build
   默认任务 / run 三任务；run 以工程根为 cwd——button 示例从工作目录读
   `info.xpm`）、`launch.json`（cppdbg 调试，Windows 用 MSYS2 的 gdb，
   需要 ms-vscode.cpptools 扩展）、`c_cpp_properties.json`（IntelliSense，
   Windows 指向 MSYS2 g++）。Windows 的任务 env 前置 MSYS2 mingw64 的
   bin 与 PKG_CONFIG_PATH（与 check.py 同源探测）；macOS/Linux 走系统
   路径不需要覆盖。副本是本机个人区不入库，按本机平台生成即完备。

3. **绑定 VS Code 靠探测不靠配置**：PATH 里的 `code`，Windows 兜底
   LOCALAPPDATA 与 Program Files 的 `bin/code.cmd`，macOS 兜底应用包内
   CLI；找不到时返回副本路径与安装指引（勾选「添加到 PATH」），不弹
   对话框、不加配置项。

4. **镜像纪律不变**：exercise/ 不被壳写入；课程壳的编译运行
   （`launch_example`）仍走 `build-exercise/`，与副本的 `workspace/<id>/build`
   互不相干。清单不登记 workspace 副本（workspace 不进清单是既有约定）。

## 后果

- 每张示例卡三个动作各司其职：「编译并运行」看原样行为、「查看源码」
  页内读、「打开工作区」进真实工程改与调。
- 副本里的源文件是生成时的镜像拷贝：上游同步后副本不会自动跟进——
  想对齐新版本删掉副本重开；README 写明。个人改动与官方更新的合并
  是学习者的功课，壳不代劳。
- VS Code 配置生成在壳里（Rust 字符串模板），与 `demos/`、`exercise/`
  的 CMake 约定（gtkmm-4.0、C++17、Ninja）保持同档；工具链路径变化
  （如 MSYS2 挪位置）由探测兜住，写死值只出现在探测失败的兜底串里。
