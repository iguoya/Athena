# T-002 · c-gui-lab 发布打包调研笔记

范围：`practice/c-gui-lab`。草稿 job：`c-gui-lab-release.yml`（Windows NSIS 一档）。
本文件只服务 leader 集成；不改 `.github/`、不改 `practice/`。

## 1. 本机怎么跑起来（照源码，不凭印象）

### Electron 母体

- `app.json`：`dev.prepare` 依次 `npm install` → `cmake --preset ucrt64` → `cmake --build --preset ucrt64`；`dev.run` 是 `npx electron .`。
- `package.json`：`main` = `launcher/main.js`，依赖只有 `electron`（^37.2.0），尚无打包器。
- `launcher/main.js` 做的事：
  - 开 BrowserWindow，加载 `launcher/index.html`（画廊 UI）。
  - `APPS` 表把键映射到 `build/apps/<name>/<name>.exe`（路径全部写死 `.exe`）。
  - `spawn` 成 **detached** 子进程，母体退出后原生窗口还在。
  - `childEnv()` 把 `C:\msys64\ucrt64\bin` 塞进 `PATH`（GTK/SDL DLL）。
  - `OFFICIAL` 表探测同目录下的 `gtk4-demo.exe` 等官方工具（随 MSYS2 包，探测不到就灰掉入口）。
  - 另有 `--shot=` 截图与 `--selftest` 无人值守探测。

### 谁编译 `apps/` 的 C/C++ 程序

- 顶层 `CMakeLists.txt` 挂七个子目录：`gtk-style`、`imgui-style`、`lvgl-style`、`raygui-demo`、`nuklear-demo`、`nuklear-gdi-demo`、`microui-demo`。
- **唯一** CMake preset 是 `ucrt64`：编译器 / `PKG_CONFIG_PATH` 钉死 `C:/msys64/ucrt64/...`（见 `CMakePresets.json`）。
- 依赖（AGENTS.md）：MSYS2 UCRT64 的 `gtk4`、`libadwaita`、`SDL2`；raygui 还要 `raylib`；链接器部分目标强制 `-fuse-ld=lld`。
- `third_party/` **gitignore**，不入库。本机目录里是 imgui、lvgl-9.2.2、microui、nuklear_gdi，以及就地改过 include 的 `nuklear_sdl2.c`、`raygui_controls_test.c`、一堆 `style_*.h` 等。没有「可复现的 fetch 脚本」。

### 安装包要不要带编译产物

- **要。** 画廊的价值就是一键 spawn 原生 exe；只发 Electron 壳等于半成品。
- 包里应含：`launcher/` + `package.json` + `build/apps/**` 下的 exe（及同目录资源如 `style.css`）+ 运行这些 exe 所需的 MinGW/GTK/SDL/raylib DLL（或等价运行时）。
- **不要**指望用户机器上已有 `C:\msys64`；也不要把「官方 gtk4-demo 等」打进包（母体本就按探测降级）。
- 当前 `main.js` 的 `MSYS2_BIN` 硬编码与相对 `PROJECT_ROOT/build/apps/...` 布局，**打进 asar/安装目录前必须改**（相对 `process.resourcesPath` 或旁路 `native-bin`）。这是集成时对 `practice/c-gui-lab` 的必要小改，不在本 worker 名下。

## 2. 打包器选型：electron-builder（不用 @electron/packager）

| 选项 | 结论 |
|---|---|
| **electron-builder** | **选用**。同一工具链原生出 Windows NSIS、macOS DMG、Linux DEB，与 ADR 0168 / Tauri 矩阵形态对齐；`executableName` / `artifactName` 可直接收成 `athena-c-gui-lab` 与 `athena-c-gui-lab-<ver>-windows-x64-setup.exe`。 |
| @electron/packager + 各平台工具 | 只出目录；NSIS/DMG/DEB 还要另接，维护面更大，且本应用短期只有 Windows 一档，收益更低。 |

`mainBinaryName` 风格（ADR 0168 第 4）：`executableName: athena-c-gui-lab`；窗口标题可用「C GUI Lab」作 `productName`。

## 3. 原生 C 在三个 runner 上能不能无头编（诚实结论）

| 平台 | 能否按现状编出完整实验室 | 是否进本版包 |
|---|---|---|
| **Windows (MSYS2 UCRT64)** | 本机路径已验证可编；CI 上前提是 **可复现的 third_party** + UCRT64 包齐（gtk4、libadwaita、SDL2、raylib、lld、cmake/ninja/pkgconf）。 | **进**：NSIS。 |
| **macOS** | **不能**按现状：仅有 ucrt64 preset；`imgui-style` 绑 Win32+DX11；`nuklear-gdi-demo` 纯 Win32 GDI；`nuklear-demo`/`microui-demo` 链 `opengl32`；`main.js` 全是 `.exe` + 硬编码 MSYS2。要进包需换后端、改 launcher、加 CMake preset，成本超过「补发布作业」。 | **不进包**（ADR 0049：成本过高，写明排除）。 |
| **Linux** | 同上：GTK/SDL 虽可装，但 Win32/DX11/GDI/`opengl32` 目标与 launcher 路径仍挡完整产品；不是「装齐 apt 就能编」。 | **不进包**（同上）。 |

草稿 job 因此是 **单平台 windows-x64**，不是三平台空矩阵。将来若有人移植完后端与 launcher，再扩 DMG/DEB 行。

## 4. 与 `release.yml` 的 `publish` 对齐

`publish` 现状（勿改文件，只记口径）：

- `needs: [macos, linux, windows, driver, ascent, tauri-apps]` —— 粘贴后 **leader 必须把 `c-gui-lab` 加进 needs**，否则永远不参与合流转正。
- 下载：`pattern: athena-*`，`merge-multiple: true`。
- 校验和：`dist` 下所有 `athena-*`。
- 上传：`dist/athena-*` + `SHA256SUMS.txt`。

草稿约定（与 tauri-apps 同形）：

- artifact **name**：`athena-c-gui-lab-windows-x64`
- 文件：`practice/c-gui-lab/dist/athena-c-gui-lab-<version>-windows-x64-setup.exe`
- 因此会被 `athena-*` 通配收走；**不要**用 Electron 默认的 `C GUI Lab Setup 1.2.3.exe` 这类名字上送。

## 5. 只能在 CI 上验证的步骤

1. `msys2/setup-msys2` UCRT64 装齐依赖后，无头 `cmake --preset ucrt64 && cmake --build --preset ucrt64`（本机有 GUI/杀软差异，不能代替）。
2. `electron-builder --win nsis` 在 GitHub-hosted windows-latest 上出安装包（含下载 Electron/winCodeSign 缓存行为）。
3. 安装包内原生 exe 在**干净 runner**（无本机 `C:\msys64`）上能否被母体 spawn 起来（验证 DLL 是否收齐、launcher PATH 是否已改）。
4. 整段 job 挂进 `release.yml` 后，`publish` 的 `needs` 与 tag 触发合流转正（本机 actionlint 只能验语法）。

## 6. 最可能红的三处

1. **`third_party/` 不在 git**：CI checkout 后没有 imgui/lvgl/就地补丁文件 → CMake 直接失败。集成前必须先定：提交 vendor 快照 / 可复现 fetch+patch 脚本 / 或 CI 专用 tarball 缓存；否则作业不可用。
2. **运行时 DLL 没收全**：GTK4/Adwaita/SDL2/raylib 传递依赖多；漏 DLL 时安装包能出、画廊能开，一点按钮就「启动失败」或闪退。干净机验证是硬门槛。
3. **launcher 路径未适配安装布局**：现网 `MSYS2_BIN` 与 `build/apps/...exe` 假设开发树；不改就打包，probe 全红或 spawn 找不到文件。

## 7. leader 集成 checklist（worker 不执行）

- [ ] 解决 `third_party` 可复现来源。
- [ ] 小改 `launcher/main.js`：打包后找旁路 native + DLL PATH（保留开发树行为）。
- [ ] 把 `c-gui-lab-release.yml` 整段粘进 `.github/workflows/release.yml`，并把 `publish.needs` 加上 `c-gui-lab`。
- [ ] `package.json` 增加 `electron-builder`（或 CI 里 `npm i -D`）；版本由 tag 写入（与 driver/tauri 同法）。
- [ ] 可选：CI 增加「含原生编译」档，与 `--skip-build` 的现网检查分开。
