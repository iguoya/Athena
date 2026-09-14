# ADR 0046：统一开发编排器，各应用只声明怎么启动

- 日期：2026-09-14
- 状态：已接受
- 影响：新增 `launcher/core`（`athena-dev`）与 `launcher/gui`（Slint）；
  `apps/*/app.json` 增加 `dev` 声明；各应用 `scripts/dev.sh` 退役；
  `launcher/macos` 改为调用同一核心

## 背景

五个学习应用各有一份启动脚本——`apps/{c,dsa,english,mathematics}/scripts/dev.sh`
和 `apps/cpp/scripts/dev-run.sh`。它们做的是同一套事：补 PATH、设环境变量、
探测是否已在运行、前置已有窗口、按需装依赖或增量构建、最后 exec。**差异只有三处**：
构建命令、启动命令、就绪判据。

五份重复会各自漂移：改一次行为要改五遍，新增一个应用先抄一份别人的脚本。ADR 0044
的菜单栏启动器也只是"调用这些脚本"，没有解决重复本身。

同时还有两个问题：

- 这些脚本全是 bash + osascript，**只在 macOS 成立**，Ubuntu 上用不了。
- 三个 Tauri 应用依赖版本完全相同（`tauri 2`、`serde 1`、`rusqlite 0.32`、
  `vite 6`、`typescript 5.8.3`），却各编一份 `src-tauri/target`：4.2 GB + 2.1 GB
  + 2.1 GB，编的是同一批依赖。

## 决策

1. **各应用只在 `app.json` 里声明怎么启动**，不再写脚本：

   ```json
   "dev": {
     "env": { "ATHENA_DSA_ROOT": "${dir}" },
     "prepare": [{ "when_missing": "node_modules", "run": ["npm", "install"] }],
     "run": ["npm", "run", "tauri:dev"],
     "ready": { "http": "http://127.0.0.1:1420" },
     "match": "src-tauri/target"
   }
   ```

   `when_missing` 表达一次性步骤（`npm install`、`meson setup`），没有它就每次都跑
   （增量构建属于这一类）；`ready` 区分"有 dev server"和"进程在就算就绪"；
   `match` 指明判断进程归属时用的路径前缀。

2. **执行逻辑只写一份**：`launcher/core`（crate `athena-dev`），Rust，三平台通用。
   它负责补 PATH、注入环境变量、按顺序跑 prepare、spawn 长驻命令、写日志、
   探测状态、停止、把窗口叫到前面。**各应用的 `scripts/dev.sh` 全部退役。**

3. **状态从系统实况读，不自己记账**（沿用 ADR 0044）：窗口进程按可执行文件路径
   前缀匹配，构建期的那一串按命令行里的应用目录识别，有 dev server 的再加一次
   TCP 连通性探测。注意路径前缀必须带分隔符——`apps/c` 是 `apps/cpp` 的前缀，
   少了它两个应用会互相误判。

4. **跨平台界面用 Rust + Slint**（`launcher/gui`）：声明式 `.slint` 和项目里的
   `.blp`、`.qml` 是同一种写法；原生渲染不经 WebView；单二进制无运行时依赖；
   用系统字体，中文界面不必内嵌字体。**macOS 菜单栏版保留**（ADR 0044），
   改为调用同一个核心——两个前端，一条执行路径。

5. **编排器统一注入共享的 `CARGO_TARGET_DIR`**（`<repo>/.cache/cargo-target`）。
   相同版本的依赖只编一次，第二、三个 Tauri 应用的首次构建几乎是白拿的。
   这条不需要任何应用改代码，正是"统一执行"的顺带好处。

6. **平台能力差异如实记录，不假装一致**：把已运行的窗口叫到前面，macOS 有正经
   办法，X11 靠 `wmctrl`/`xdotool`，而 **Wayland 出于安全根本不允许别的进程抢
   焦点**——那种情况下编排器明说"请自己切过去"，而不是假装成功。长远的解法是
   各应用自己响应"再启动一次"来 present 窗口（Tauri 有 single-instance 插件）。

## 后果

- 新增一个学习应用 = 放一份带 `dev` 声明的 `app.json`，终端、跨平台窗口、
  macOS 菜单栏三个入口同时生效，一行代码都不用改。
- 磁盘：三份 8.4 GB 的 Rust 构建缓存收敛成一份（约 2.5–3 GB）。代价是 cargo 对
  target 目录加文件锁，**同时构建两个 Tauri 应用会串行等待**；预热本来就该串行，
  影响可以接受。切换到共享目录后第一次构建是全量的，之后才享受复用。
- 各应用 `bin/`、`src-tauri/target` 下的旧缓存不再使用，可以删。
- 代价是多了一层间接：出问题要看 `app.json` 的声明加编排器的日志，而不是读一份
  自己的 shell 脚本。日志集中在系统惯例位置（macOS `~/Library/Logs/Athena/`，
  Linux `$XDG_STATE_HOME/athena/logs`），界面上也会显示当前卡在哪一步。
