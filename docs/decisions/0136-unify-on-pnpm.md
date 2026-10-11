# ADR 0136：前端包管理器统一为 pnpm，去掉 ascent 的特殊

- 日期：2026-10-11
- 状态：已接受（tiger 2026-10-11：「要不然全用 pnpm 要不然全用 npm，如果有技术优劣之分的话」——授权按技术优劣择一；
  ascent 的 pnpm 豁免是特殊，要去掉）。**决定已定，迁移尚未执行**，执行条件见决策 4
- 延续：[ADR 0135](0135-share-low-cost-build-layer-first.md) A 档的版本对齐；本篇是它的下一步，也是 B 档（工作区）的前置
- 修订：0135 决策 3 里「`ascent` 用 pnpm，本批不动」的例外

## 背景

26 个 Tauri + Node 应用里，25 个用 npm，只有 `ascent` 用 pnpm（`pnpm-lock.yaml`、
`pnpm-workspace.yaml`、`app.json` 与 `tauri.conf.json` 里的 `pnpm`，CI 与 release 里各有一段
`ascent` 专用分支）。ADR 0135 为它开了版本检查豁免——这是不该留的特殊。要么全 pnpm，要么
全 npm，下面按技术优劣选。

## 比较

| 维度 | npm | pnpm |
|---|---|---|
| 磁盘 | 每个应用一份完整 `node_modules`。实测 24 个应用装完共 **3.3 GB** | 全局内容寻址存储 + 硬链接，同一版本的包整机只存一份；26 个应用共用 React、Vite、TypeScript 等同一套版本（ADR 0135 刚对齐），去重收益最大 |
| 依赖严格性 | 提升到顶层，代码能 import 到没声明的包（幽灵依赖） | 默认严格，没声明的包 import 不到，漏声明在本地就暴露 |
| 版本统一 | 靠 `check.py` 事后比对 | 工作区 `catalog:` 把版本写在一处，应用引用它（B 档的天然载体） |
| 供应链 | — | 原生 `minimumReleaseAge`（拒绝装发布不久的版本）；`ascent` 已在用 |
| 开箱即用 | Node 自带，无需安装 | **Node 25 起不再随带 corepack，pnpm 要单独装**（本机 Node 26.9、无 pnpm） |
| 迁移代价 | 只需改 `ascent` 一个应用 | 改 25 个应用 + CI + release + 文档 |

结论：**pnpm 更好**。迁移代价是一次性、机械的；磁盘去重、依赖严格、`catalog:` 与供应链防护
是持续的收益，且正好服务于 ADR 0135 的方向。基线「机器是完整的开发机」（ADR 0057）已假定
开发工具齐备，多装一个 pnpm 不违背它，按 0057 的做法在 `docs/ENGINEERING.md` 给一条安装指引。

## 决策

1. **所有 Tauri + Node 应用统一用 pnpm**；`package-lock.json` 退役，锁文件统一为
   `pnpm-lock.yaml`。每个 `package.json` 写 `packageManager` 字段钉住 pnpm 版本。
2. **迁移保持依赖版本不变**：用 `pnpm import` 从现有 `package-lock.json` 生成
   `pnpm-lock.yaml`，不借机升级任何包；升级仍走 ADR 0135 的整批升级。
3. **需要同步修改的位置**：各应用 `app.json` 的 `prepare`/`run`、`src-tauri/tauri.conf.json` 的
   `beforeDevCommand`/`beforeBuildCommand`、`.github/workflows/ci.yml` 与 `release.yml`
   （去掉 `ascent` 专用分支，统一 `pnpm/action-setup` + `cache: pnpm`）、
   `docs/ENGINEERING.md`（安装指引）、仍提到 `npm install/ci/run` 的应用文档。
4. **执行条件**（不满足就不开始，避免中途停在不一致状态）：
   - 本机已装 pnpm；
   - `.github/workflows/ci.yml`、`release.yml` 没有其他代理的未提交改动（并行规则）；
   - 先在一个应用上跑通 `pnpm import` → `pnpm install` → `pnpm build` → `tauri dev` 一遍，再批量。
5. **完成后**：删掉 `STACK_VERSION_EXEMPT` 里 `ascent` 一项，`ascent` 的 `motion`、`lucide-react`
   等对齐到 `STACK_VERSIONS`；`check.py` 新增一条：同栈应用不得出现 `package-lock.json`，
   且必须有 `packageManager`。
6. **ascent 的 `minimumReleaseAgeExclude` 白名单**随 `pnpm-workspace.yaml` 保留；是否把
   `minimumReleaseAge` 推广到全部应用，等 B 档工作区落地时再定。

## 后果

- 迁移前，`ascent` 仍是唯一用 pnpm 的应用，豁免暂时保留并标注"待 ADR 0136 迁移"。
- **实测（2026-10-11 迁移）**：24 个应用全部装好，npm 方案 `node_modules` 合计 3.3 GB；pnpm 的
  全局存储合计 **1.1 GB**，各应用 `node_modules` 是指向它的硬链接（约三分之一）。
  迁移中还遇到两处差异：pnpm 12 默认拦截依赖的安装脚本（`mathematics` 直接用 esbuild，需在
  `pnpm-workspace.yaml` 的 `allowBuilds` 里批准）；`packageManager` 字段会写进锁文件，先写字段
  再 `pnpm import` 的顺序会让 `--frozen-lockfile` 失败，应先 `pnpm install` 刷新一次锁。
- 多一个必装工具；缺 pnpm 时启动器的 `prepare` 会失败，需按决策 3 的安装指引提示。
