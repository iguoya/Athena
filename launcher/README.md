# Athena 启动器

打开任何一个学习应用，都从这里走。三个前端，**同一条执行路径**：

| 目录 | 是什么 | 用在哪 |
| --- | --- | --- |
| [`core/`](core) | 编排器 `athena-dev`（Rust） | 所有前端的执行层，也能直接在终端用 |
| [`gui/`](gui) | 跨平台启动器（Rust + Slint） | macOS / Ubuntu / Windows：托盘常驻 + 列表窗口 |
| [`macos/`](macos) | 菜单栏启动器（Swift） | macOS 专用，⌃⌥A 唤出 |

"同一条执行路径"是字面意思：前端都不自己读 `app.json`、不自己判断状态、不自己拼
日志路径，一律向编排器要（`athena-dev list --json`）。菜单栏版是平台专属的，更要
守住这条——它为什么值得单独留着、另外两个平台少了什么，见
[ADR 0048](../docs/decisions/0048-menubar-launcher-stays-macos-only.md)。

背景与取舍见 [ADR 0044](../docs/decisions/0044-menubar-launcher.md)（常驻启动器）
和 [ADR 0046](../docs/decisions/0046-unified-dev-orchestrator.md)（统一编排器）。

## 应用怎么被启动

没有任何应用自己写启动脚本。每个应用在 `apps/<id>/app.json` 里**声明**：

```json
"dev": {
  "env": { "ATHENA_DSA_ROOT": "${dir}" },
  "prepare": [{ "when_missing": "node_modules", "run": ["npm", "install"] }],
  "run": ["npm", "run", "tauri:dev"],
  "ready": { "http": "http://localhost:1420" },
  "binary": "athena-dsa"
}
```

- `prepare` 按顺序执行；带 `when_missing` 的只在那个路径不存在时跑（`npm install`、
  `meson setup`），不带的每次都跑（增量构建）。
- `ready` 区分"有 dev server"和"进程在就算就绪"。
- `binary` 是窗口进程的可执行文件名——共享 cargo 缓存之后，Tauri 应用的二进制不在
  应用目录里了，按文件名认最直接。
- `match`（可选）是判断进程归属的路径前缀，`apps/cpp` 用它指向 `build`。

托盘图标来自 `gui/assets/tiger.svg`——Athena 早期欢迎页的主视觉，2026-08-30 随
欢迎页一起删掉，现在从 git 历史里取回来了。菜单栏只有 22pt 高，整只老虎缩进去
只剩一条色块，所以 `gui/build.rs` 在构建期裁出虎头再渲染成位图；换图标就是换那份
SVG（连带调一下裁剪框）。

编排器统一注入：PATH 补全（node / cargo / meson / Qt 在桌面环境里往往不在 PATH）、
共享的 `CARGO_TARGET_DIR`（三个 Tauri 应用依赖相同，各编一份是白费 6 GB）、
以及日志重定向。

## 用

```sh
cargo build --release --manifest-path launcher/Cargo.toml
```

**跨平台启动器**（托盘常驻，关掉窗口不退出）：

```sh
launcher/target/release/athena-launcher
```

**macOS 菜单栏版**（常驻状态栏，⌃⌥A 唤出，可登录自启）：

```sh
launcher/macos/scripts/install.sh
```

**终端**：

```sh
launcher/target/release/athena-dev list        # 谁在跑、谁没跑
launcher/target/release/athena-dev list --json # 同上，机器读的格式（前端用它）
launcher/target/release/athena-dev open dsa    # 打开；已在跑的只把窗口叫到前面
launcher/target/release/athena-dev stop dsa    # 连同构建期拉起的那一串一起收掉
launcher/target/release/athena-dev logs dsa    # 日志文件路径
```

`list --json` 里的 `state` 是 `stopped` / `starting` / `ready` 这组固定标识符，
不是给人看的中文——写脚本认它，别去匹配 `list` 那一列的措辞。

`open` 可以挂到 Raycast、GNOME 自定义快捷键或 Windows 快捷方式上。

## 状态怎么判断

窗口进程在 = 运行中；有属于它的构建进程在跑 = 启动中；都没有 = 未运行。全部从系统
实况读（进程表 + 可选的 TCP 探测），不靠启动器自己记账——所以应用被别处启动、崩溃、
手动关掉，三个前端都跟得上。

**dev server 通不算就绪**：Tauri 的 vite 秒开，而 Rust 壳还要编几十秒，那段时间端口
是通的但屏幕上什么都没有。

## 平台差异

- **把已运行的窗口叫到前面**：macOS 有正经办法；X11 靠 `wmctrl` / `xdotool`；
  **Wayland 出于安全不允许别的进程抢焦点**，那种情况下编排器会明说"请自己切过去"，
  而不是假装成功。
- **托盘**：Windows 正常；GNOME 默认没有状态栏区域，需要 AppIndicator 扩展，
  装不上时托盘不显示，窗口照常能用。Ubuntu 上还需要 `libayatana-appindicator3-dev`。
- **Windows** 上启动器本身有 CI 保证编得过；被启动的应用则参差：三个 Tauri 应用
  已纳入三平台流水线，`apps/c`（Qt）与 `apps/cpp`（GTK4）的 Windows job 还是
  `continue-on-error` 的探测位，后者卡在 MSYS2 giomm 与 glib 的头文件冲突上。
  也就是说，Windows 上能不能真的打开某个应用，取决于那个应用自己。

## 日志

macOS `~/Library/Logs/Athena/<id>.log`，Linux `$XDG_STATE_HOME/athena/logs/`，
Windows `%LOCALAPPDATA%\Athena\logs\`。构建失败先看它。
