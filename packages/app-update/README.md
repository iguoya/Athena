# @athena/app-update

Tauri 应用的应用内自动更新组件（ADR 0172）。启动时静默检查更新通道，发现新版本就下载
安装，右下角进度条提示，装完自动重启；离线或失败一律静默。模式与摘星一致（摘星
ADR 0018 的全矩阵推广）。

纯 TypeScript 源码不预编译（ADR 0137 同款），依赖由使用方提供。

## 应用接入清单

1. `tauri.conf.json`：`bundle` 加 `"createUpdaterArtifacts": true`；顶层加
   `plugins.updater`（公钥与端点 `https://github.com/iguoya/Athena/releases/download/app-updates/<id>.json`，
   `windows.installMode: "passive"`）。公钥与摘星一致，抄任意已接入应用。
2. `src-tauri/capabilities/*.json`：`permissions` 加 `updater:default`、
   `process:allow-restart`。
3. `src-tauri/Cargo.toml`：`tauri-plugin-updater`、`tauri-plugin-process`（workspace 依赖，
   两个工作区的公共依赖表已含，ADR 0172 落地起）。
4. Rust 入口的 `Builder` 注册两个插件（参照摘星 `lib.rs`）。
5. `package.json`：加 `@athena/app-update`（workspace）、`@tauri-apps/plugin-updater`
   与 `@tauri-apps/plugin-process`（catalog）。
6. 前端入口挂 `<AppUpdate />` 一行。
