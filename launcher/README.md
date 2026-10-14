# Athena 启动器

打开任何一个学习应用，都从这里走。三个前端，**同一条执行路径**：

| 目录 | 是什么 | 用在哪 |
| --- | --- | --- |
| [`core/`](core) | 编排器 `launcher`（Rust） | 所有前端的执行层，也能直接在终端用 |
| [`webui/`](webui) | 跨平台启动器（Tauri 2 + React + Three.js） | Windows 首发：3D 领域轨道环 + 2D 平铺，主线前端（ADR 0125） |
| [`gui/`](gui) | 旧前端（Rust + Slint），已退役 | ADR 0127：源码留档、不参与构建，运行入口是 webui |
| [`macos/`](macos) | 菜单栏启动器（Swift） | macOS 专用，⌃⌥A 唤出 |

"同一条执行路径"是字面意思：前端都不自己读 `app.json`、不自己判断状态、不自己拼
日志路径，一律向编排器要（`launcher list --json`）。菜单栏版是平台专属的，更要
守住这条——它为什么值得单独留着、另外两个平台少了什么，见
[ADR 0048](../docs/decisions/0048-menubar-launcher-stays-macos-only.md)。

背景与取舍见 [ADR 0044](../docs/decisions/0044-menubar-launcher.md)（常驻启动器）
和 [ADR 0046](../docs/decisions/0046-unified-dev-orchestrator.md)（统一编排器）。

## 应用怎么被启动

没有任何应用自己写启动脚本。每个应用在 `<分类目录>/<id>/app.json` 里**声明**：

```json
"dev": {
  "env": { "ATHENA_DATA_STRUCTURES_ROOT": "${dir}" },
  "prepare": [{ "when_missing": "node_modules", "run": ["npm", "install"] }],
  "run": ["npm", "run", "tauri:dev"],
  "ready": { "http": "http://localhost:1497" },
  "binary": "athena-data-structures"
}
```

- `prepare` 按顺序执行；带 `when_missing` 的只在那个路径不存在时跑（`npm install`、
  `meson setup`），不带的每次都跑（增量构建）。
- `ready` 区分"有 dev server"和"进程在就算就绪"。
- `binary` 是窗口进程的可执行文件名——共享 cargo 缓存之后，Tauri 应用的二进制不在
  应用目录里了，按文件名认最直接。
- `match`（可选）是判断进程归属的路径前缀，`programming/c-plus-plus` 用它指向 `build`。

窗口里的清单每 3 秒向编排器重读。托盘菜单在进程启动时生成，新增或删掉应用后要重启
启动器，菜单才会跟上。关窗口不退出，进程留在菜单栏托盘里；左键点图标把窗口叫回来，
退出走菜单里的「退出启动器」。

「开机自启」在托盘菜单里，默认关。勾选状态以系统实况为准，启动器不另记账：macOS 写
`~/Library/LaunchAgents/athena-launcher.plist`（LaunchAgent，指向当前这份可执行文件），
Windows 写 HKCU 的 Run 键，Linux 写 XDG autostart。登录拉起时窗口不弹出，点托盘或
Dock 再打开。开发调试版依赖 vite，勾了自启后下次登录会拉起这份 debug 二进制；日常
自启用带 `custom-protocol` 的 release。

窗口标题栏用**虎头**（Fluent Emoji 虎头，和各应用同一画风，ADR 0065）：SVG 原件
`gui/assets/tiger.svg` 随退役的 gui 留档（ADR 0127），窗口里用的是入库的
`webui/public/tiger-mark.png`，托盘用 `webui/src-tauri/icons/32x32.png`。Dock 和
Windows 任务栏用同一张 256px 的 `webui/src-tauri/icons/icon.png`。裸二进制没有
`.app`，macOS 的 Dock 读不到 Info.plist；Windows 任务栏认的是大图标，窗口创建时
只填了标题栏那张。这两处由 `webui/src-tauri/src/app_icon.rs` 在窗口建好后补上。

### 图标

每个应用的 `icon.svg` 就是它的图标本身：透明底、自带颜色。启动器图块原样显示它，
不垫底色，也不随运行状态变样（运行态只看状态点）；应用自己的窗口 / 任务栏 / Dock
和界面里的标志也都从它来（ADR 0065）。平台图标位要位图，在 `icon.renders` 里声明：

```json
"icon": {
  "file": "icon.svg",
  "renders": {
    "icon.png": 256,
    "icon.ico": "ico",
    "src-tauri/icons/icon.icns": "icns"
  }
}
```

值是 PNG 边长，或 `"ico"`（16–256 共 9 帧）/ `"icns"`（16–1024）。改了 `icon.svg` 跑：

```sh
.cache/cargo-target/release/launcher icons          # 各分组目录、practice/、certification/、mentor/ 与 tools/ 一起重新生成
.cache/cargo-target/release/launcher icons --check  # 只核对，过期时退出码非零
```

生成的文件提交进各应用目录，应用构建不依赖启动器。没有 `icon.svg` 的新应用，图块退回
`icon.accent` 色块加 `icon.letter`。

### 分组与关系（学习应用面板的思维导图）

学习应用面板是放射状思维导图（ADR 0083）：中心是虎头，向外是领域分组，应用挂在各自领域外面。
同心轨道是椭圆（launcher ADR 0002：长轴沿横向，贴屏幕形态；子节点多的组占内层），
位置、分组和连线全部由 `launcher-core` 的 `mindmap::layout` 从清单算出来，不存坐标；
`app.json` 里这几个可选字段决定画什么：

| 字段 | 含义 |
|---|---|
| `group` | 领域名，如 `"编程语言"`、`"英语"`。同名的归一组；省略归「其他」。**软约束**：只在同领域有多个同类应用时才需要，一个应用不必非有组名；目录才是硬约束（ADR 0148）。分组名是自由文本，写错一个字就多出一个分组 |
| `evolves_from` | 另一个应用的 id：谁从谁长出来。画成带箭头的实线 |
| `related` | 相关应用的 id 数组。**无向**，只在一边写就行；找不到的 id 忽略；已经有演进线的两个应用不再画相关线 |
| `parent` | 主挂靠的应用 id（ADR 0092）：本应用是它底下的子课程，画在它外一圈、有向连线，不占领域扇区。只能写一个；挂靠深度一层 |
| `also_in` | 引用到领域圈的领域名数组（ADR 0117）：在这些领域圈里各多一个引用节点，和圈内成员同圈排布、由领域胶囊连线。领域名不存在或与本体所在领域相同的条目忽略 |
| `also_under` | 引用挂靠的应用 id 数组（ADR 0116）：在这些应用底下各多一个引用节点——同一个应用、同一个图标，点开是同一个进程，连线比主挂靠淡。解析不到、指向自己、与 `parent` 重复、目标自己也是挂靠节点的条目忽略 |

```json
"group": "数理",
"related": ["cpp"]
```

实践面板仍是网格：那些小项目彼此没有关系可画。

编排器统一注入：按应用需要补 PATH（node / cargo / meson / Qt / flutter——异构
工具链不混用）、同类 Tauri 共享的 `CARGO_TARGET_DIR`（ADR 0063：同类可共享，
异构各用自己的 `build/`），以及日志重定向。

## 用

Rust 构建产物不进 `launcher/target/`：仓库根 `.cargo/config.toml` 把本仓库所有
Rust 构建指到共享缓存 `.cache/cargo-target/`（ADR 0140、0063），下面所有命令的
产物都在 `.cache/cargo-target/release/` 里。

```sh
cargo build --release --features custom-protocol --manifest-path launcher/Cargo.toml
```

`custom-protocol` 把前端页面嵌进二进制（`tauri build` 自动带，直接 `cargo build`
要手动加）；不带它是开发版，运行时去连 vite 开发服务器（`pnpm dev`），改前端时用。

**跨平台启动器**（托盘常驻，关掉窗口不退出）：

```sh
.cache/cargo-target/release/athena-launcher-webui
```

**macOS 菜单栏版**（常驻状态栏，⌃⌥A 唤出，可登录自启）：

```sh
launcher/macos/scripts/install.sh
```

**终端**：

```sh
.cache/cargo-target/release/launcher list        # 谁在跑、谁没跑
.cache/cargo-target/release/launcher list --json # 同上，机器读的格式（前端用它）
.cache/cargo-target/release/launcher open dsa    # 打开；已在跑的只把窗口叫到前面
.cache/cargo-target/release/launcher stop dsa    # 连同构建期拉起的那一串一起收掉
.cache/cargo-target/release/launcher logs dsa    # 日志文件路径
.cache/cargo-target/release/launcher sync        # 提交并推送学习进度（只剩未迁走的应用）
.cache/cargo-target/release/launcher progress sync [id]   # 本地进度库与路由器对一遍
.cache/cargo-target/release/launcher progress status      # 每个应用的本地库、待推送条数、游标
.cache/cargo-target/release/launcher progress backup [dir]  # 本地库与中心库导出成 JSON 快照
```

**进度同步代理**（ADR 0155）：在 `app.json` 里声明了 `progress` 的应用，本地库放在用户数据目录
（`<dir>/learning.db`），**不进 git**；启动器在能连上路由器时把它与 `nas_admin` 的
`/api/progress/v1` 互推。打开应用前会先对一遍，常驻时每隔一段时间对没在跑的应用对一遍；
路由器不可达只写日志（`<用户数据目录>/AthenaSync/sync.log`），不弹任何提示。
配置在 `AthenaSync/config.json`（首次自动生成：端点列表、学习者编号、设备名）。
声明格式：

```json
"progress": {
  "dir": "athena-cpp",
  "tables": {
    "knowledge_progress": { "mode": "lww" },
    "run_history": { "mode": "append", "key": ["started_at", "lab_id"] }
  }
}
```

`mode` 是 `lww`（可变记录，更新时间新者胜）或 `append`（事件，同一键只记第一次；删除用墓碑，只标记不真删，ADR 0160）；
`key` 省略取表的主键，没有主键的表必须写。

`sync` 对应 ADR 0053：进度库跟着仓库走（`<分类目录>/<id>/progress/learning.db`），所以
同步就是一次提交加一次推送。**声明了 `progress` 的应用已改走上面的同步代理**（ADR 0155），
它们的库不再进 git，这里不收集；`driver` 的 `progress/` 目录只剩点位照片，仍按目录被收集。
它**只碰 `progress` 路径**，不会连带你手上的代码改动；
待推送的提交里有不是进度的，它会列出来交回你自己决定，不替你 push。顺带把
`git diff` 的 sqlite textconv 配好，这样进度库的 diff 不是一句 "Binary files differ"。

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
- **托盘**：macOS 在菜单栏，Windows 在通知区。关窗口隐藏，进程还在。GNOME 默认没有
  状态栏区域，需要 AppIndicator 扩展；装不上时托盘不显示，窗口照常能用，关窗口即退出。
  Ubuntu 上还需要 `libayatana-appindicator3-dev`。
- **开机自启**：托盘菜单勾选，三平台都写进系统自己的登录启动（见上）。Linux 上启动器
  图形界面本身仍按 ADR 0051 不作为承诺。
- **Windows** 上全部应用都有正式的 CI 门槛并且构建通过：启动器、三个 Tauri 应用、
  `programming/machine`（Qt）、`programming/c-plus-plus`（GTK4）。`programming/c-plus-plus` 的 Windows 支持 2026-09-15 打通，
  其中一处临时垫片绕开了 glib 2.90 与 MSYS2 现有 glibmm 2.86 的名字冲突
  （ADR 0049），MSYS2 跟上后可以删。

## 日志

macOS `~/Library/Logs/Athena/<id>.log`，Linux `$XDG_STATE_HOME/athena/logs/`，
Windows `%LOCALAPPDATA%\Athena\logs\`。准备步骤和长驻进程的输出都写在这里，
构建失败先看它。
