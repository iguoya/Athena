# launcher 协作规则（启动器）

仓库级通用规则在 [`../AGENTS.md`](../AGENTS.md)，这里只写启动器自己的。启动器不是学习
应用，「跨应用教学规范」对它不生效。用法、`app.json` 字段和平台差异的完整说明见
[`README.md`](README.md)。

## 是什么

| 目录 | 是什么 |
|---|---|
| `core/` | 编排器 `launcher`（Rust）：发现应用、准备、启动、判断状态、日志、`sync` |
| `gui/` | 跨平台启动器（Rust + Slint）：托盘常驻 + 列表窗口，另有「实践」分区 |
| `macos/` | 菜单栏启动器（Swift），macOS 专属（ADR 0048） |

背景与取舍：ADR 0044（常驻启动器）、0046（统一编排器）、0048（菜单栏版只在 macOS）。

## 规则

- **三个前端同一条执行路径。** 前端不自己读 `app.json`、不自己判断状态、不自己拼日志
  路径，一律向编排器要（`launcher list --json`）。菜单栏版是平台专属的，更要守住这条。
- **启动器里没有按应用写的分支。** 新增应用只放一份带 `dev` 声明的 `app.json`，启动器
  不改代码（ADR 0046）。发现逻辑扫 `<root>/*/app.json`：默认 `subjects/`，
  `--root practice` 扫项目应用，GUI 的实践分区用同一套 `discover_in`。
- **状态从系统实况读，不自己记账。** 窗口进程在 = 运行中；有属于它的构建进程 = 启动中；
  都没有 = 未运行。dev server 端口通了不算就绪。
- **`list --json` 的 `state` 是契约。** `stopped` / `starting` / `ready` 是固定标识符，
  前端和脚本都认它；改它等于破坏所有前端。
- **`sync` 只碰 `progress` 路径**（ADR 0053）：不连带代码改动，待推送里有非进度提交就
  列出来交回使用者，不替人 push。
- **平台降级要如实说**（ADR 0047、0049、0051）：做不到就明说（例如 Wayland 不允许抢
  焦点时提示使用者自己切过去），不假装成功。
- **换标志只换 `gui/assets/tiger.svg`。** 标题栏、任务栏、托盘都从这一份派生，裁切在
  `gui/build.rs` 里。

## 验证

```sh
cargo build --manifest-path launcher/Cargo.toml --all-targets   # CI 三平台跑的就是这条
cargo test  --manifest-path launcher/Cargo.toml
```

macOS 菜单栏版：`swift build --package-path launcher/macos`。启动器不在
`subjects/`、`practice/` 下，根 `scripts/check.py` 不会带上它，改完要自己跑上面两条。
