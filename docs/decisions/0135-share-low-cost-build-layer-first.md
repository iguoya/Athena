# ADR 0135：共享分层推进——构建层低成本项先做，schema 与内容抽象待成熟

- 日期：2026-10-11
- 状态：已接受（tiger 2026-10-11：方向没错，暂缓只是因为多应用内容与结构还不成熟、难以抽象；
  显而易见可共享、代价低的，优先采取一定的共享策略；同技术体系构建隔离没必要）
- 收窄：[ADR 0132](0132-defer-shared-layer.md)——暂缓范围缩小为 schema 与内容抽象，构建层不再暂缓
- 恢复方向：[ADR 0130](0130-shared-build-and-schema.md) 的方向成立；其 `shared/` 位置与 gtkmm 试点
  （[ADR 0131](0131-shared-layer-location-and-pilot.md)）仍只在 schema 层启动时才用
- 修订：[ADR 0032](0032-independent-apps-launched-as-processes.md) 决策 2——同技术体系的应用
  不再要求构建隔离；异构栈（[ADR 0133](0133-heterogeneous-stack-admission.md) 准入的那几个）仍各自构建
- 不变：[ADR 0062](0062-apps-own-their-constraints.md)（约束不继承）、[ADR 0129](0129-prefer-quality-over-quantity.md)

## 背景

0132 把共享整体暂缓，理由是内容与结构未成熟、难以抽象。这个理由对 **schema、内容块、
进度表**成立，对**构建层**不成立：构建层的重复是机械的，不依赖课程内容长成什么样。

实测（26 个 Tauri 2 + Node 应用，2026-10-11）：

- **已经共享的**：Rust `target`。启动器给所有 Tauri 应用注入同一个
  `CARGO_TARGET_DIR=<repo>/.cache/cargo-target`（`launcher/core/src/runner.rs`，ADR 0046/0063）。
  （0130 背景里「每个应用独占 target」的说法不准确，本 ADR 更正。）
- **依赖版本已分叉**：`react` 13 个应用里 10 个 18.3、3 个 19.3；`vite` 三个版本
  （`^6`×14、`^6.0.3`×8、`^8.3.1`×4）；`typescript` 23 个 5.8、3 个 6.0；
  `@fontsource/noto-sans-sc`、`tailwindcss`、`@tauri-apps/*` 同样各有两种写法。
  同一台机器上因此要装并构建多套互不兼容的前端工具链。
- **配置是手抄的**：`vite.config.ts`、`tauri.conf.json`、`Cargo.toml` 26 份各不相同，
  `tsconfig.json` 7 个版本，`src-tauri/build.rs` 26 份逐字相同。
- **`node_modules` 现在只装了 1 个**（其余应用未安装依赖）。一旦逐个装起来，每份都是
  独立副本，磁盘和安装时间线性增长——这是**将要**发生的成本，不是已经发生的。

## 决策

1. **分三档推进，按成本从低到高：**
   - **A 档（现在做）**：不改应用结构、可逐项回退的共享——
     (a) 同栈应用的核心依赖版本对齐到同一组，并由 `scripts/check.py` 加一条跨应用检查，
     版本分叉直接报错；(b) 已有的共享 Cargo target 保持，并确认 `launcher open` 之外的
     手动 `tauri dev` 也走同一目录（文档写明环境变量）。
   - **B 档（A 档稳定后，另立 ADR 再做）**：npm workspaces 提升 `node_modules`、共享
     `Cargo.lock` / workspace 依赖表、共享 `tsconfig` / `vite` 基础配置。这一档会改动每个
     应用的 `package.json`、锁文件与 `prepare` 步骤，需要先在一个应用上验证。
   - **C 档（暂缓，维持 0132）**：内容块类型、`content-contract.json` 公共部分、进度库
     schema、阅读/测验/复习等应用代码。待内容与结构成熟、满足 0132 的重启条件再议。
2. **同栈不再要求构建隔离。** 「同栈」按 ADR 0133 的默认栈（Tauri 2 + React + TypeScript +
   Vite）界定；异构应用（gtkmm 的 CMake 实验、c-plus-plus、machine、driver、c-gui-lab 等）
   仍各自构建，不被拉进共享。应用之间依然**不互相引用路径与内容配置**——共享的是工具链
   与依赖，不是对方的文件。
3. **A 档版本对齐方向（tiger 2026-10-11 定）：技术选型统一用相对最新的**——取仓库里已有
   应用在用的最新组合，不取"多数派"，也不跳到尚无应用验证过的大版本：
   React 19.3、Vite 8.3.1、TypeScript 6.0.3、`@vitejs/plugin-react` 6.1.1、Tailwind 4.3.3、
   `@tauri-apps/*` 2.12。npm 上 TypeScript 已有 7.x，但没有任何应用验证过，A 档不采用；
   升级时整批升级（见决策 4），不让个别应用先走。
   - 例外：`ascent` 用 pnpm（本机默认工具链未装），本批不动，写进检查脚本的豁免表并附理由。
4. **版本检查的形状**：`scripts/check.py` 的 `run_stack_version_check` 对照 `STACK_VERSIONS`
   表逐项比较声明的版本范围，豁免写在 `STACK_VERSION_EXEMPT` 表里（附理由），不靠注释；
   新应用立项时按表里的版本起步。
5. **不做**：不建 `shared/`，不抽代码，不动进度库与内容契约；不因为"将来可能共享"提前
   对齐 schema 字段。

## 后果

- 根 `AGENTS.md`、`docs/REPOSITORY.md` 的措辞改为「同栈构建可共享，异构栈各自构建；
  schema / 内容抽象暂缓」；四个应用 `AGENTS.md` 里的「构建完全隔离」同步改。
- 0130 的磁盘膨胀论据降级为「将来 `node_modules` 全装后的预期」，不再当作现状。
- A 档本身不产出新目录，风险限于版本升级的回归；B 档才开始动结构，须单独立项。
