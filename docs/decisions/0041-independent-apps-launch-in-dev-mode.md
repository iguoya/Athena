# ADR 0041：独立应用从源码以开发模式启动，不经打包副本

- 日期：2026-09-14
- 状态：已接受；「从源码热启动」的结论不变，执行方式已由
  [ADR 0046](0046-unified-dev-orchestrator.md) 收敛到统一编排器——下文提到的
  `ui/external_app_launcher` 与各应用的入口脚本都已随之退役
- 影响：`apps/*/app.json`、`ui/external_app_launcher`、`apps/{dsa,english,mathematics}`
  的入口脚本；修正 ADR 0032 关于「启动打包产物」的后果

## 背景

ADR 0032 把 `apps/` 下的异构应用定为独立进程，发现靠 `app.json` 的 `executable`。
后来三个 Tauri 应用（数据结构、英语、数学）把这条路径落实成了：

1. `npm run build:app` 做一次 release 打包；
2. 把 `.app` 拷进 `apps/<id>/bin/`；
3. 数学应用还会把产物同步到 `/Applications/athena-math.app`；
4. 主程序图谱点击再 `spawn` 这份冻结的 Mach-O。

这是按 DMG / 已安装应用的方式在跑，和本仓库「自用、改完立刻看见」的定位相反：

- 同一应用在仓库 `bin/`、`target/release/bundle`、`/Applications` 里各有一份，
  改源码只动了其中一份时，表现为「改动完全没生效」；
- 日常验证要付一次两三分钟的 release 编译，前端热更新用不上；
- 主程序点图谱打开的不是正在编辑的那棵源码树。

Athena 是自用学习平台，日常入口应当对着源码，而不是对着一份已经打好的包。

## 决策

1. **Tauri 应用的启动路径是 `scripts/dev.sh`（内部 `npm run tauri:dev`）。**
   `app.json` 的 `executable` 指向这份脚本。主程序图谱点击、以及
   `./bin/athena-*` 别名，一律走这条路径。改前端即时热更新；改 Rust 才重编壳。
2. **不把打包 `.app` / DMG 当作运行方式。** 不为了「能点开」去 `tauri build`，
   不把产物拷进 `bin/`，不安装、不同步到 `/Applications`。`build:app` /
   `build:dmg` 只在真正要交付一份可分发的包时才跑，和日常启动无关。
3. **一份源码、一个进程。** 开发服务若已在对应 Vite 端口上，入口脚本直接
   把已有窗口提到前面，不再起第二份。进度库仍在各应用自己的用户数据目录
   （ADR 0037），清掉 `/Applications` 里的壳不会丢掉学习记录。
4. ~~**`apps/c` 仍启动 CMake 产物。**~~ **已由 ADR 0042 取代**：C 语言应用是
   Qt Quick，入口同样是 `scripts/dev.sh`（QML 热加载）；原 LVGL 小程序留在
   `apps/c/playground/`，不作为图谱启动目标。

## 后果

- 从主程序打开 DSA / 英语 / 数学，看到的就是仓库里正在改的那份；不再需要
  先猜自己点开的是 `/Applications` 还是 `bin/` 里哪一份旧包。
- 第一次（或清过 `target/` 之后）启动会编译 debug 壳，可能要等一两分钟；
  之后只有改 `src-tauri/` 才再编。机器上需要 Node、Rust 和系统 `sqlite3`，
  入口脚本会补常见 PATH（Homebrew、`~/.cargo/bin`）。
- ADR 0032 里「macOS 打包时把应用放进 `Contents/Resources/apps/<Name>/`」
  不再是启动路径。主程序发行包仍然可以不含这些独立应用；开发时靠源码树
  的 `apps/`（`external_apps_root()`）发现并拉起。
- 可选的 `tauri build` 仍可用来做一份真正要分发的包，但那是打包任务，
  不是「打开这个应用」的步骤。
