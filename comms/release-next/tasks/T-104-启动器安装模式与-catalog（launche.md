---
id: T-104
title: 启动器安装模式与 catalog（launcher/core，ADR 0173）
owner: zcode
status: todo
priority: P1
depends: 
created: 2026-10-21 08:23
updated: 2026-10-21 08:23
---
## 背景
ADR 0173（docs/decisions/0173-launcher-installable-with-auto-update.md，必读）：启动器做成安装包。本任务做**编排器核心（launcher/core）的安装模式与 catalog**；webui 适配、打包配置、更新器接入是 T-105。

先读 `launcher/AGENTS.md`、`launcher/README.md` 和 `launcher/core/src/` 里的 `paths.rs`、`manifest.rs`、`runner.rs`、`main.rs`，理解现在「发现应用 → 状态 → 打开」的链路。**仓库模式一字不改**：所有现有 `cargo test -p launcher-core` 用例继续过。

## 要做的事
1. **`launcher catalog` 子命令**：扫仓库里 `scripts/release_apps.json` 列出的应用（用其中的 `dir` 字段，缺省 `<root>/<id>`；`dir` 字段由 T-009 加，你可以先按缺省规则和 `launcher` 特例处理，T-009 合入后再对齐），读各自 `app.json` 与 Tauri 应用的 `src-tauri/tauri.conf.json`，生成 `launcher/core/catalog.json`。字段按 ADR 0173 决策 3：id、名称、分组、`related`、`evolves_from`、图标（相对路径或内嵌 data URI，你定，写理由）、`productName`、`mainBinaryName`、`identifier`、`progress` 声明、`kind`；**不含 `dev` 块**。输出稳定（键序、换行固定），`launcher catalog --check` 只核对不写，过期退出码非 0。
2. **`scripts/check.py` 校验 catalog 不过期**：在结构卫生里调 `launcher catalog --check`（或等价的纯 Python 重算比对——哪个对三平台更稳你选，写理由）。check.py 是 leader 的文件，**这一处你直接改并告诉我**，只加这一项，不动别的。
3. **安装模式**（`locate_repo()` 为 `None` 时）：
   - 清单来源改为 `include_str!` 内嵌的 `catalog.json`；`list --json` 的契约保持（`state` 取值 `stopped` / `starting` / `ready` 不变——安装模式下没有 `starting`），新增字段（比如 `installed: bool`、`mode: "installed"`）只增不改。
   - 「已安装」按 ADR 0173 决策 4 的平台约定判断；这段路径逻辑**关进单独模块**（比如 `core/src/installed.rs`），其它地方不出现平台分支（根 AGENTS.md 跨平台规则）。Windows 先把 NSIS 每用户目录与注册表卸载项做实；macOS、Linux 按约定写，做不到验证的明说。
   - 「打开」：已安装直接启动可执行文件，未安装返回明确的「未安装」结果（前端据此指路 Releases）；异构应用（kind 不是 tauri）返回「未支持安装模式启动」。
   - 「运行中」判据沿用现有（进程名），不重新发明。
4. **进度同步在安装模式照常**：`progress_sync.rs` 读 `progress` 声明的来源在安装模式换成 catalog；本地库路径逻辑不变。`cargo test -p launcher-core progress_sync` 继续过。
5. 单元测试：catalog 生成的稳定性与 `--check`；安装模式下的清单加载、已安装判断（用临时目录造假安装位置）、打开未安装应用的返回、异构应用的返回。

## 验收口径
- `cargo build --manifest-path launcher/Cargo.toml --all-targets` 与 `cargo test --manifest-path launcher/Cargo.toml` 通过；贴输出摘要。
- 在本机真跑一次：`ATHENA_ROOT` 指向一个**没有仓库**的空目录、cwd 也不在仓库里，`launcher list --json` 能输出内嵌清单，里面本机确实装着的应用 `installed: true`、其余 false。贴输出。
- 仓库模式回归：不设环境变量在仓库里跑 `launcher list --json`，输出与改动前逐字段一致（新增字段除外）。
- **允许提交**（只提交你名下的 launcher/core 改动、`launcher/core/catalog.json` 与 check.py 那一处），提交前 `cargo test` 必须绿。转 `review` 并写提交号。

## 注意
- 表现层冻结（launcher/AGENTS.md）：这个任务不碰 webui 的视觉。
- `release_apps.json` / `release_plan.py` 归 cursor 的 T-009，别改；你需要 `dir` 字段而它还没到，先按缺省规则写并在交付说明里提一句。

## 进展记录
