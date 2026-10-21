---
id: T-103
title: 更新器批量接入剩余 Tauri 应用并迁移拾阶（ADR 0172）
owner: claude-code
status: doing
priority: P1
depends: 
created: 2026-10-21 08:23
updated: 2026-10-21 08:24
---
## 背景
ADR 0172（docs/decisions/0172-app-updater-for-all-tauri-apps.md，你写的）已落地机制与 snake 样板。本任务把更新器**批量接入剩余的 Tauri 发布应用**。接入清单就是你写在 `packages/app-update/README.md` 里的六处，snake 的提交 29096047 是样板。

## 范围
`scripts/release_apps.json` 里 `kind` 为 `tauri` 的应用，除去：
- `snake`（样板，已接入）；
- `ascent`（kind 是 `ascent`，单独走迁移，见下）。
共 20 个应用。启动器不在本任务（T-104 / T-105）。

## 要做的事
1. 逐个应用做六处接入（conf / capabilities / Cargo / 插件注册 / package.json / 前端挂载）。可以写一个**幂等**的一次性脚本批量改，脚本放你的 artifacts 目录（`comms/release-next/artifacts/zcode/T-103/`），不进仓库；每个应用改完必须能被 `git diff` 看清楚，改动都在接入清单列出的文件里。
2. **拾阶迁移**（ADR 0172 决策 7，只做应用侧）：endpoint 改指 `https://github.com/iguoya/Athena/releases/download/app-updates/ascent.json`，前端换用共用组件 `@athena/app-update`。**不要**动 `release.yml`（双写过渡归 leader）。旧通道 `ascent-updates` 不动。
3. 两个工作区的 Cargo.lock / pnpm-lock.yaml 照常更新；**提交前用 `git worktree` 或其它办法确认 `pnpm install --frozen-lockfile` 在提交后的 HEAD 上通过**（上次有人的 lockfile 被别人的提交带走过）。
4. 同一个 `identifier` / 公钥一致：公钥抄 snake 已有的字符串，不要新生成密钥。

## 验收口径
- `git diff --stat` 每个应用只动接入清单里的文件；`pnpm install --frozen-lockfile`、`cargo check --workspace`（仓库根和 launcher 两个工作区各一次）通过。
- 抽查至少 5 个应用 `python scripts/check.py <应用>` 全绿（含 gtkmm、jiuzhou、mathematics、cs408、polaris）。本机 Windows 的环境坑见 `docs/RELEASE-TODO.md` 末尾那条（别让 MSYS 的 python 抢到 PATH 最前）。
- 交付说明里附一张表：应用 × 六处是否完成；以及一句话说明没接入的应用与原因（预期没有）。
- **允许提交**，分组提交（每提交一类应用，信息写清列了哪些应用），`git add` 写明确路径。提交后转 `review`，写上提交号。
- 发版号和各应用版本**不要动**：全矩阵加依赖本来就会让 10.1.0 的计划得出「所有应用都有改动」，版本由 `prepare` 统一升。

## 注意
- `release.yml` / `ci.yml` / `scripts/release*.py` 归 leader 和 cursor，别碰。
- 撞到别人的未提交改动先停，发消息给 leader。

## 进展记录
- [2026-10-21 08:24] zcode：todo → doing
- [2026-10-21 09:10] claude-code：leader 接手收尾（zcode 因使用者当面指派新任务暂停；二十多个应用的接入改动已在工作区，剩验证与提交；owner 改为 claude-code）
