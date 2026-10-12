# ADR 0140：同栈 Tauri 应用共用一份依赖与一个编译目录

- 日期：2026-10-11
- 状态：已接受（使用者要求：技术底层一样的应用共用底层依赖库、一样的版本、共用构建目录）
- 落实：[ADR 0135](0135-share-low-cost-build-layer-first.md) 决策 1 的 B 档
- 不改：[ADR 0132](0132-defer-shared-layer.md) 的 C 档——schema、内容块、进度库、应用代码仍不抽

## 背景

课程、讲解、演示类应用已经是 Tauri 2 + Node 前端（React，或 ADR 0138 尚未改完的原生
TypeScript）。仓库里没有还在用的 Tauri + Vue：`embedded` 已迁 React；`ascent/archive/vuepress-2020`
是历史站点，不参与构建。

0135 的 A 档把核心依赖版本对齐，并让启动器给 Tauri 应用注入同一个
`CARGO_TARGET_DIR`。手动 `cargo` / `tauri dev` 不经过启动器时仍各自写
`src-tauri/target`，前端锁文件也仍是每个应用一份。版本表写在 `check.py` 里，
`package.json` 再手抄一遍，两处会漂。

## 决策

1. **前端一个 pnpm 工作区。** 仓库根 `pnpm-workspace.yaml` 收 `subjects/*`、
   `practice/earth`、`launcher/webui`、`packages/*`。不收异构栈：`driver`（Flutter）、
   `machine`（Qt）、`practice/c-gui-lab`（Electron）、`practice/pocket_cube`（GTK）、
   `practice/nas_admin`（Python）。锁文件只留根上的 `pnpm-lock.yaml`。
2. **版本只写在 catalog。** 同栈核心依赖在 `package.json` 里写 `catalog:`，版本范围写在
   `pnpm-workspace.yaml` 的 `catalog`，与 `scripts/check.py` 的 `STACK_VERSIONS` 必须逐字相同。
   `packageManager` 统一 `pnpm@10.15.1`（与本机和 CI 的 pnpm 10 一致）。`@athena/viz` 用
   `workspace:*`。启动器 webui 一并跟上 React 19、Vite 8、TypeScript 6，以及 earth 已在用的
   `three` / `@react-three/fiber` / `@react-three/drei`。
3. **Rust 两个工作区，一个编译目录。** 课程与 `practice/earth` 的 `src-tauri` 进仓库根
   虚拟工作区，共享 `workspace.dependencies` 里的 `tauri`、`tauri-build`、`serde`、
   `serde_json`，锁文件是根 `Cargo.lock`。`launcher/` 自己的工作区保留（它还包含
   `launcher-core`，嵌套工作区 Cargo 不支持），但同一组 `workspace.dependencies` 必须与根上
   逐字相同，由检查脚本比对。编译产物一律
   `<repo>/.cache/cargo-target`：仓库根 `.cargo/config.toml` 的 `[build] target-dir`
   相对配置所在目录解析，手动 cargo 与启动器走同一目录（ADR 0063）。Flutter、Meson、CMake
   不读这个配置。
4. **应用仍然互不引用。** 共享的是工具链、锁文件和编译缓存，不是对方的源码、内容或进度库。
   不抽阅读器、测验或进度代码。

## 后果

- 装依赖在仓库根执行 `pnpm install`；某个应用的 `pnpm run build` 仍在该应用目录执行。
- 发行包从 `.cache/cargo-target/release/bundle` 取，不再从 `src-tauri/target` 取。
- 启动器界面按 ADR 0125 的表现层冻结只做版本对齐，不改视觉。fiber 8 不支持 React 19，
  因此 three 相关库跟 earth 的 9 / 10 / 0.182，而不是把 earth 降回 fiber 8。
