---
id: T-007
title: scripts/release_plan.py：应用清单、版本读写、plan 与 matrix（ADR 0171）
owner: cursor
status: todo
priority: P1
depends: 
created: 2026-10-20 17:14
updated: 2026-10-20 17:14
---
## 背景
ADR 0171（docs/decisions/0171-incremental-release-per-app-versions.md，必读）把发版改成：应用各有自己的真实版本号，只构建有改动的应用。本任务做**计划脚本**，是后面 prepare、readiness、CI 的共同底座。名下新文件：`scripts/release_plan.py`、`scripts/release_apps.json`、`scripts/tests/test_release_plan.py`。不改 `release.py` / `release_readiness.py`（那是 T-008，等本任务 review 后再做）。

## 要做的事
1. **`scripts/release_apps.json`**：发布应用清单（数据，不是代码）。每项：`id`、`root`（顶层目录）、`kind`（`tauri` / `cpp` / `driver` / `ascent` / `electron`）、`manifest`（版本所在文件）、`manifest_format`（`tauri_conf` / `pubspec` / `meson` / `package_json`）。名单来源：`.github/workflows/release.yml` 的 `tauri-apps` 矩阵（22 个应用）加 `ascent`（postgraduate/ascent）、`driver`（certification/driver）、`cpp`（practice/cpp）、`c-gui-lab`（practice/c-gui-lab，Electron）。ascent 的 kind 单独标，因为它有更新器。
2. **版本读写**：按 `manifest_format` 读出和写入版本；写入只改版本那一行，**保留文件其余字节不变**（不要 JSON 整体重新序列化）。`pubspec.yaml` 的版本形如 `10.0.0+3`，写入时保留 `+构建号`部分（升版本时构建号规则：沿用，不自增）。
3. **`plan` 子命令**：`python scripts/release_plan.py plan [--base TAG]`（默认 base 是最近的 `v*.*.*` tag），算出每个应用「有没有改动、为什么、建议升到几」：
   - 路径比对：应用目录自己有改动。
   - 依赖图：pnpm 工作区用 `pnpm ls --filter "...[<base>]" --depth -1 --json`（或等价办法）取变更包及其下游；Rust 用 `cargo metadata` 的工作区依赖，取变更 crate 及其下游。`packages/`（`@athena/viz`、`athena-course-shell`、`maps`）变了，下游应用算有改动。非工作区应用（driver、cpp）只按路径。
   - 全局触发：**只有**锁定的工具链版本变了才算所有 Tauri 应用都有改动：`.github/workflows/release.yml` 里 `pnpm/action-setup` 的 `version`、`actions/setup-node` 的 `node-version`、tauri CLI 的版本（如果有锁定）。改 `release.yml` 的其它内容不算。
   - 忽略项：`practice/cpp/meson.build` 里 `version` 那一行单独变动不算 cpp 有改动（它是发版时写的）；`comms/`、`docs/`、`scripts/`、`.github/`（除上面的工具链版本）不触发任何应用。
   - **凡是被判为有改动（包括只是依赖变了）的应用必须升版本**。
   - 升多少：看「只动了该应用及其依赖路径」的提交（`git log base..HEAD -- <路径>`）：提交标题里有 `feat` 升 minor，有 `⚠️` 或标题里 `!:` 升 major，其余 patch。输出里给出每个应用的当前版本、建议版本、判断依据（哪几个提交、哪条路径）。
   - 输出：默认人读的表格；`--json` 给机器读。
4. **`matrix` 子命令**（CI 用，不算依赖图）：`python scripts/release_plan.py matrix --base TAG --head REF`，**只比较各应用清单里的版本**：和 base 相比版本不同的应用，就是这次要构建的。输出一行 JSON：
   ```json
   {"tauri": {"include": [{"app":"snake","root":"programming","os":"windows-latest","platform":"windows-x64","bundles":"nsis"}, ...]},
    "cpp": false, "driver": false, "ascent": true, "c-gui-lab": false}
   ```
   `tauri.include` 的条目必须与 `release.yml` 现在 `tauri-apps` 矩阵每项的字段一模一样（`app root os platform bundles`；四个平台：windows-latest/windows-x64/nsis、macos-15/macos-arm64/app,dmg、macos-15-intel/macos-x86_64/app,dmg、ubuntu-26.04/linux-x86_64/deb）。平台表写成脚本里的常量。没有 Tauri 应用要构建时，`include` 给空数组，CI 会据此跳过。base 里应用还不存在（新应用）算有改动。
5. 应用在 base 版本里没有清单版本（占位 0.1.0 之类）的情况：照常比较，不特殊处理。

## 验收口径
- `plan` 在当前仓库上跑一次：对照 `git diff --stat v10.0.0..HEAD`，被判有改动的应用应当是 pocket-cube-solver、snake、chinese-chess、jiuzhou、c-plus-plus、earth、gtkmm 这几个，加上 `packages/maps` 或锁文件变化牵连出的下游；把输出和你的核对贴进交付说明，**核对每个判断是不是说得对**，说不对的要解释。
- `matrix` 对造出来的两份清单（临时目录里的假仓库或桩）验证：版本没变→不出现；变了→四个平台条目齐；新应用→出现。
- 自测覆盖：四种清单格式的读写（含 pubspec 的 `+构建号`、写入后其余字节不变）、升版本级别推断（feat / ⚠️ / `!:` / 其余）、忽略项、工具链版本变动触发全量。不引测试框架，风格同 `scripts/tests/test_release_readiness.py`。
- 只读：`plan`、`matrix` 不写任何文件、不改 git 状态。写版本是 T-008 的事，这里只提供写入函数并自测。
- 注释写为什么，中文，不解释语言基础。Windows 下输出强制 UTF-8（同 `release.py` 的 `force_utf8_output`）。

## 做完
`status T-007 review`，`--note` 附输出摘要与证据路径（放 `comms/release-next/artifacts/cursor/T-007/`）。不提交 git。

## 进展记录
