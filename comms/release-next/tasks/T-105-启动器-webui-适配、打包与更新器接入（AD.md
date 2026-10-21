---
id: T-105
title: 启动器 webui 适配、打包与更新器接入（ADR 0173）
owner: zcode
status: todo
priority: P1
depends: T-104
created: 2026-10-21 08:23
updated: 2026-10-21 08:23
---
## 背景
ADR 0173。T-104 交付了编排器的安装模式与 `catalog.json`。本任务把 **webui 适配安装模式、打开打包、接入更新器**。表现层冻结：不新增视图、不做视觉打磨，只做「隐藏仓库专属元素、加灰态与指路」。

## 要做的事
1. **webui 适配**：从后端拿到 `mode`（仓库 / 安装）后——安装模式下隐藏构建日志、dev server 状态、图标重生成等仓库专属入口；`installed: false` 的应用灰态，点击打开仓库的 Releases 页（`https://github.com/iguoya/Athena/releases`，用 Tauri 的 opener 能力，不要自己拼进程命令）；异构应用点击同样指路并带「未支持安装模式启动」的提示。仓库模式界面与行为不变。
2. **打包**：`launcher/webui/src-tauri/tauri.conf.json` 把 `bundle.active` 改为 `true`，`targets` 取 NSIS / DMG / DEB（对齐其它 Tauri 应用的 `release.yml` 取法：矩阵里 Windows 是 `nsis`、macOS 是 `app,dmg`、Linux 是 `deb`）；`productName` 保持 `athena-launcher`（别让安装目录和 ID 变化），图标沿用虎头。`beforeBuildCommand` 与 `custom-protocol` 的约定不变。
3. **更新器**：按 `packages/app-update/README.md` 的六处清单接入（conf 的 `createUpdaterArtifacts` 与 `plugins.updater`、capabilities、Cargo、插件注册、package.json、前端挂 `<AppUpdate />`）；端点是 `https://github.com/iguoya/Athena/releases/download/app-updates/launcher.json`，公钥抄 snake。**常驻要保住**：关窗口不退出、托盘与开机自启（tauri-plugin-autostart）保持；更新装完重启后仍是常驻状态，自启项指向安装路径、更新不换路径——在交付说明里写你怎么确认的。
4. 本机打一次安装包验证（Windows 先做）：`pnpm run tauri:build`（见 launcher/AGENTS.md），**静默安装到临时目录**（NSIS：`/S /D=<无空格路径>`，`/D=` 必须是最后一个参数），确认安装版能起来、`list` 走安装模式、托盘在、能退出；验完卸载或删临时目录。把过程和结果写进证据。

## 验收口径
- `cargo build/test` 通过；前端 `pnpm run build`（tsc + vite）通过。
- 证据：安装版启动的截图或日志（`launcher.log`/stdout）、安装模式 `list --json` 输出、灰态与指路的行为说明。
- **`release_apps.json` 加 `launcher` 条目由 cursor 的 T-009 / leader 做**，你不改；本任务不碰 `release.yml`。
- 允许提交（你名下的 launcher/webui 与 launcher 工作区改动），提交前 `cargo test` 与 webui 构建绿。转 `review` 并写提交号。

## 注意
- 依赖 T-104；T-104 没 `done` 前，你可以先做第 2、3 条（打包配置与更新器接入，两者不依赖安装模式）并提交，第 1、4 条等 T-104。

## 进展记录
