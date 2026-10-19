# T-003 · machine（Qt）三平台发布打包 — 调研笔记

起草日期：2026-10-19。只读仓库现状；不改 `programming/machine` / `.github/`。

## 1. 应用怎么跑起来（现状）

| 项 | 事实 |
|---|---|
| 壳 | Qt 6 Quick/QML，`CMakeLists.txt` 目标名 `athena-machine`（`WIN32` 子系统） |
| 本机启动 | `launcher open machine` → `app.json` 的 `prepare`（cmake + build）再跑 `build/athena-machine` |
| Qt 路径 | `app.json` 的 `CMAKE_PREFIX_PATH.first_existing`：Homebrew `qt@6` / `C:/Qt/6.8.1/msvc2022_64` |
| 内容根 | `src/main.cpp` 的 `resolve_root()`：**优先**环境变量 `ATHENA_MACHINE_ROOT`；否则编译期宏 `ATHENA_C_SOURCE_ROOT`（= `CMAKE_SOURCE_DIR`） |
| 运行时读盘 | `root/qml/Main.qml`、`root/content/curriculum.json`、`root/content/exercises.json`、`root/icon.svg`；`engine.addImportPath(root + "/qml")` |
| 不进 GUI 包 | `labs/`（`scripts/lab.py` 命令行）、`playground/`（独立 LVGL）、`content/sources/reference/`（约 28 MB 教材副本，壳不读） |

安装包里若仍依赖编译期 `ATHENA_C_SOURCE_ROOT`，用户机器上路径必错。草稿强制：

1. 把 `qml/`、`content/curriculum.json`、`content/exercises.json`、`content/sources/catalog.json`（若存在）、`icon.svg` 与二进制同树 staged；
2. 启动时设 `ATHENA_MACHINE_ROOT=<安装根>`（Windows NSIS 快捷方式 / macOS wrapper / Linux `/usr/bin` 包装脚本）。

`content/asm/` 若后续教案引用观察层再加；当前 GUI 不读它，首版可省略以控体积。

## 2. CI 上怎么装 Qt（跟已验证装法，不另起炉灶）

对照 `.github/workflows/ci.yml` 的 `qt-quick` / `qt-quick-windows`：

| 平台 | 已验证做法 | 版本对齐 |
|---|---|---|
| Windows | `pip install aqtinstall` → `aqt install-qt windows desktop 6.8.1 win64_msvc2022_64`；**不传** `-m qtdeclarative`（Qt 6 里 Quick 在基础包；传了会 XML 解析失败） | 与 `app.json` / job `QT_VERSION=6.8.1` 一致；`CMAKE_PREFIX_PATH=$GITHUB_WORKSPACE/Qt/6.8.1/msvc2022_64`；先手写 `vcvars64.bat` 再 cmake，避免 PATH 里 MinGW 抢 `g++` |
| macOS | `brew install qt@6 cmake ninja`；`CMAKE_PREFIX_PATH=/opt/homebrew/opt/qt@6`（intel runner 则为 `/usr/local/opt/qt@6`） | Homebrew 滚动版，**不一定**是 6.8.1；CI 已用此法编过，发布跟它 |
| Linux | `apt`：`qt6-base-dev qt6-declarative-dev libgl1-mesa-dev` + cmake/ninja | 发行版包，与 Windows 精确小版本不对齐；CI 对该 job `continue-on-error`（ADR 0051） |

### 关于 `jurplel/install-qt-action`

任务书点名调研。结论：**本草稿不用它**。

- 它底层仍是 aqt；Windows 上装 6.8.1 可行，但本仓 CI **已经**用裸 `aqtinstall` 修过两处坑（modules 误传、MSVC vs MinGW），再包一层第三方 action 无收益。
- 若将来 leader 想换成 action：`version: 6.8.1`、`arch: win64_msvc2022_64`，**不要**把 `qtdeclarative` 放进 `modules:`（那是 addon 列表）；若裁剪安装才用 `archives: qtbase qtsvg qtdeclarative`。
- macOS/Linux 继续 brew/apt 与 `qt-quick` 一致即可。

打包额外需要：`windeployqt` / `macdeployqt`（随 Qt 工具包；aqt 默认带 `qttools`）。Windows runner 再 `choco install nsis`（或等价）出 `*-setup.exe`。

## 3. 产物命名（对齐 `publish` 收集）

`publish` 用 `actions/download-artifact` pattern `athena-*`，checksum 扫 `athena-*`。上传 artifact 的 **name** 与 **path 内文件名** 都必须 `athena-` 开头。

照 Tauri 矩阵改名惯例（`release.yml` Collect and rename）：

| 平台 | 文件名 | upload `name` |
|---|---|---|
| Windows | `athena-machine-<version>-windows-x64-setup.exe` | `athena-machine-windows-x64` |
| macOS arm64 | `athena-machine-<version>-macos-arm64.dmg` | `athena-machine-macos-arm64` |
| Linux | `athena-machine_<version>_amd64.deb`（下划线） | `athena-machine-linux-x86_64` |

`mainBinaryName` 风格：包内可执行文件 **`athena-machine`**（已是 CMake 目标名）；窗口标题仍可中文「C 与机器」。

集成时 leader 必须把 `publish.needs` 加上本 job id（草稿里叫 `machine`），否则产物上传了也不会进 Release。

## 4. 打包策略摘要

- **Windows**：Release 编 `athena-machine.exe` → 拷到 `stage/` → `windeployqt --qmldir qml --release` → 叠课程树 → NSIS 生成 `*-setup.exe`，快捷方式带 `ATHENA_MACHINE_ROOT=$INSTDIR`。
- **macOS**：组 `athena-machine.app`（`Contents/MacOS` 包装脚本设 `ATHENA_MACHINE_ROOT` 指向 `Contents/Resources`，真二进制同目录或 Resources）→ `macdeployqt … -qmldir=…` → `hdiutil` UDZO DMG。
- **Linux**：deb 装到 `/usr/lib/athena-machine/`（二进制 + 课程树），`/usr/bin/athena-machine` 为包装脚本 export `ATHENA_MACHINE_ROOT`；`Depends` 写系统 Qt6（与 ci apt 同源），**不**走 linuxdeploy/AppImage（`release.yml` 已注明无头 CI 的 fuse 坑；Tauri 也只发 DEB）。

版本号：文件名用 `GITHUB_REF_NAME` 去 `v`。CMake `project(… VERSION 0.1.0)` 目前与发版 tag **不一致**；草稿**不**做 cpp 那种硬校验，避免首跑必红。建议 leader 集成前要么抬 `PROJECT_VERSION`，要么单独写入 Windows `app.rc` 用的版本。

## 5. 平台取舍（诚实排除）

| 目标 | 结论 |
|---|---|
| windows-x64 | **做**。CI `qt-quick-windows` 已是正式门槛；有 `packaging/windows/app.rc.in`。 |
| macos-arm64（`macos-15`） | **做**。CI `qt-quick` 已编过。 |
| macos-x86_64（`macos-15-intel`） | **首版不做**。machine 的 CI 从未在 intel runner 上跑；Homebrew Qt 路径与部署差异要单独验。等 `qt-quick` 矩阵加 intel 或专开一档再补。 |
| linux-x86_64 | **做（deb + 系统 Qt）**。CI 上 verify 是 `continue-on-error`，发布仍发包（与 Tauri 同策）；首跑若链接/依赖名不对，改 `Depends` 即可。 |
| 把 `labs/` / `playground/` / 教材 reference 打进包 | **不做**。GUI 不依赖；reference 28 MB；实验仍是本机 `lab.py`。 |

另：应用内 ADR 0008 已定迁 Tauri 2 + React，**尚未执行**。本作业是 Qt 壳的过渡发布通道；迁完后应删本 job、改走 `tauri-apps` 矩阵，勿双轨长期并行。

## 6. 只能在 CI 上验证的步骤

1. `windeployqt` / `macdeployqt` 完整依赖闭包（本机 Qt 布局≠runner）。
2. NSIS 打出的 `*-setup.exe` 静默安装后，无开发环境能否靠 `ATHENA_MACHINE_ROOT` 打开首页。
3. `macdeployqt` 后的 `.app` 在干净 macOS 上缺不缺 QML 插件 / 签名公证（草稿只做 ad-hoc/`hdiutil verify`，不做 Apple 公证）。
4. deb 的 `Depends` 包名在 `ubuntu-26.04` 上是否仍叫草稿里写的那些。
5. 把本 job 挂进 `publish.needs` 后，`download-artifact` 是否收到三个 `athena-machine-*`。

## 7. 最可能红的三处（CI 首跑先看）

1. **Windows：`windeployqt` 找不到或 QML 模块漏拷** — 症状：安装后白屏 / `QQmlApplicationEngine` 空 root。先看 job 日志里 `windeployqt` 命令与 `stage/qml` 是否进包；确认 aqt 装的是 `win64_msvc2022_64` 且 vcvars 已生效。
2. **`ATHENA_MACHINE_ROOT` 未生效** — 症状：进程起得来但立刻退（找不到 `Main.qml`）。查 NSIS 快捷方式 / macOS wrapper / Linux `/usr/bin` 脚本是否 export；勿只依赖编译期 `ATHENA_C_SOURCE_ROOT`。
3. **Linux deb 依赖名或 RPATH** — 症状：`dpkg -i` 解依赖失败，或包装脚本指向的目录无 `qml/`。对照 `apt-cache search qt6` 修正 `Depends`；确认 staged 树在 `/usr/lib/athena-machine/`。

## 8. 草稿未做 / 停在哪

- 本机未实机跑 `windeployqt`/`macdeployqt`/NSIS（无头会话；且不得改应用树加脚本）。
- 未写可复用的 `scripts/package_*.py`（那会动 `programming/machine`）；步骤内联在 workflow 里，leader 集成时可再抽。
- 未做代码签名 / Apple 公证 / Windows SmartScreen。
- `macos-x86_64` 明确排除（见上）。
- actionlint：在临时副本里把 `machine` job 并入 `release.yml` 后跑；证据见同目录 `machine-actionlint.out.txt`。
