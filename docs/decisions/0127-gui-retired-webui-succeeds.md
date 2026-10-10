# ADR 0127：gui（Slint）退役——webui 转正为唯一图形前端

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「如果3D版稳定 彻底退出卸载先前的版本」）
- 关系：执行 [ADR 0125](0125-launcher-webui-tauri-threejs.md) 决策 6 预告的 gui
  退役；执行路径约定（ADR 0046）与 macos 菜单栏版（ADR 0048）不变

## 背景

1. ADR 0125 落地后，webui 经过若干轮修复（capabilities 授权、custom-protocol
   生产构建开关、3D 相机参数）已能稳定渲染与启动应用，tiger 判定稳定、要求
   彻底退出先前的 Slint 版。
2. ADR 0125 决策 5 原定「gui 冻结、代码留档、不删除」。本 ADR 把冻结推进为
   退役：不参与构建、不再运行、可执行产物清理；**源码目录按 0125 继续留档**
   （git 历史亦可恢复），要物理删除另行决定。

## 决策

1. `athena-launcher.exe` 停止运行；`gui` 从 workspace members 移出——CI 与本地
   的 `cargo build --manifest-path launcher/Cargo.toml --all-targets` 不再触及它。
2. target 里的旧版可执行产物（`athena-launcher.exe`、`athena-dev.exe` 及其调试
   版）删除，即「卸载」的落地。
3. **CLI `launcher.exe` 与 core 不受影响**：它是 macos 菜单栏版与脚本的执行路径。
4. webui 的功能缺口如实记录：**托盘常驻与开机自启动尚未迁移**（gui 版有），
   在补齐前，启动器的图形入口是 webui 窗口本体（手动启动）；迁移完成后本条
   后果作废。

## 后果

- 「Athena 启动器」窗口只有一个：webui；托盘图标暂时消失，待 webui 接入
  tauri 托盘插件后恢复。
- CI 的 launcher 段调整：Windows/macOS 先 `npm ci && npm run build` 构建页面
  资产再 cargo 全量编译；Linux 只编 `launcher-core`（Tauri 2 需要 webkit2gtk
  全套，Linux 支持未承诺，ADR 0051 降级约定）。
- launcher 的 Slint 相关依赖（slint、slint-build）随 gui 移出构建不再编译；
  Cargo.lock 中的存量条目待下次依赖刷新自然收敛。
