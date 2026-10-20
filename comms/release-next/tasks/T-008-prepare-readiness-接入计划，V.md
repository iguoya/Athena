---
id: T-008
title: prepare/readiness 接入计划，VERSION 与发布说明两张表（ADR 0171）
owner: cursor
status: done
priority: P1
depends: T-007
created: 2026-10-20 17:14
updated: 2026-10-20 17:44
---
## 背景
ADR 0171（必读）。T-007 交付了 `scripts/release_plan.py`（`plan`、`matrix`、版本读写）。本任务把它接进发版流程：`prepare` 按计划升各应用版本、写发版号；`readiness` 多一条红灯；`notes` 产出发布说明里的两张表。名下路径：`scripts/release.py`、`scripts/release_readiness.py`、`scripts/release_plan.py`（可追加 `notes` 子命令）、`scripts/tests/`、仓库根 `VERSION` 文件。**不动** `.github/workflows`（leader 做）、各应用清单的回填（zcode 的 T-102）。

## 要做的事
1. **发版号放 `VERSION`**（仓库根，一行 `10.0.0`，当前值就是上一版）。`release.py` 里原来读 `practice/cpp/meson.build` 当「当前发版号」的地方（`current_meson_version`、`parse_target`、`check_prerequisites`）改读 `VERSION`；`prepare` 写 `VERSION`，不再 bump `practice/cpp/meson.build` 当发版号。tag 与 `VERSION` 必须一致。
2. **`prepare` 接入计划**：先跑 readiness（T-006 已接），再调 `release_plan` 算改动集与建议版本；对每个有改动的应用，把建议版本写进它的清单；命令行 `--bump <应用>=major|minor|patch|x.y.z` 手动覆盖（可多次）；`--dry-run` 只打印计划表（哪些应用、从什么版本到什么版本、判断依据），不写任何文件。写完后和 `VERSION`、CHANGELOG 节一起进同一个 `chore(release): x.y.z` 提交。没有任何应用有改动时拒绝发版并说明。
3. **发版号怎么定**：沿用现有规则（`--major/--minor/--patch` 或显式给版本，CHANGELOG 头部的 ⚠️ 规则不变），只是基数来自 `VERSION`。
4. **`readiness` 增加一条**：「有改动但没升版本」——对 `plan` 判为有改动、而清单版本与 base 相同的应用，红灯并点名（`prepare` 会自动升，所以这条主要是防手改清单或移 tag 之后漏升）。
5. **`notes` 子命令**：`python scripts/release_plan.py notes --base TAG --head REF` 输出发布说明里的两张 Markdown 表：①「本次发布」：应用、旧版本→新版本；②「未变化的应用」：应用、当前版本、最新安装包在哪个 tag（由「该应用清单版本最后一次变化的 tag」推出，没有 tag 对应时写「—」）。CI 的 publish 作业会把它拼进 Release 说明（leader 接 `release.yml`）。
6. 不兼容的老行为要有清晰报错：比如 `VERSION` 不存在时提示「先建 VERSION，内容写上一个发布的版本号」。

## 验收口径
- 自测：`VERSION` 读写、`--bump` 覆盖解析、`--dry-run` 不写文件、没有应用有改动时拒绝、readiness 新增红灯、`notes` 两张表（用桩 git 与桩清单，不真调 gh / 不真打 tag）。风格同 `scripts/tests/test_release_readiness.py`，`python scripts/tests/test_release_readiness.py` 与新增自测都要 exit 0。
- 实机：在当前仓库上 `python scripts/release.py prepare --minor --dry-run` 跑一次（`readiness` 若红，按 T-006 的约定 dry-run 只提示不拒绝），把输出贴进交付说明。**不要真的 prepare、不要打 tag、不要 push。**
- 只读边界：除 `--dry-run` 之外的路径，写入都限于 `VERSION`、各应用清单版本行、`CHANGELOG.md`（沿用现有逻辑）。

## 做完
`status T-008 review`，`--note` 附验证输出与证据路径（`comms/release-next/artifacts/cursor/T-008/`）。不提交 git。

## 进展记录
- [2026-10-20 17:43] claude-code：todo → doing · leader 接手：cursor 会话已结束
- [2026-10-20 17:44] claude-code：doing → review · 已提交 629cdaac：prepare 按计划升版本、VERSION、--bump、dry-run 计划表；readiness 加应用版本计划检查；notes 子命令已在 2bd69134；4 份自测全 exit 0；prepare --minor --dry-run 实机输出核对
- [2026-10-20 17:44] claude-code：review → done · leader 自验：dry-run 计划表与 plan 一致（8 个升 patch、2 个新应用不升）
