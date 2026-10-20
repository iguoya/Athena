---
id: T-005
title: scripts/release.py readiness：发版前体检
owner: cursor
status: review
priority: P1
depends: 
created: 2026-10-20 07:53
updated: 2026-10-20 08:08
---
## 目标
10.0.0 发版时的遗留，大多是「到打 tag 那一刻才发现」。做一个只读的**发版前体检**：`python scripts/release.py readiness`，把发版前要人工翻的几处汇成一张表，红的挡发版，黄的提醒。名下路径：新建 `scripts/release_readiness.py`（逻辑）、改 `scripts/release.py`（只加一个 `readiness` 子命令，转调前者，不动 prepare/push 现有逻辑）、`scripts/tests/`（自测，不引测试框架，风格同 `comms/tests/test_v2.py`）。

## 检查项（每项一行：状态、说明、怎么处理）
1. **工作区**：`git status --porcelain` 按顶层目录分组计数，未跟踪与已修改分开。`prepare` 在工作区不干净时会拒绝，所以有任何改动就是红，但要列出分组（`comms/`、各应用、`docs/`…），别只说「不干净」。
2. **与远端**：本地 `main` 相对 `origin/main` 的 ahead/behind。behind 红（`prepare` 要求同步），ahead 黄。
3. **CI 全量验证**：用 `gh run list --workflow=ci.yml --json ...` 找最近一次 `workflow_dispatch` 且 `app=all`（输入为空或 all）的 run：状态、完成时间、对应 commit；再算 HEAD 比它新多少个提交、这些提交有没有动 `.github/`、`Cargo.lock`、`pnpm-lock.yaml`、应用目录。最近全量 run 不是 success 红；是 success 但之后动过工作流或锁文件黄。**注意**：`gh` 认不出 `git@github.com:` 形式的 remote，要从 `origin` URL 解析出 `owner/repo` 再传 `--repo`（`release.py` 里已有 `github_slug()`）；没装 gh 或没登录就黄并说明，不要崩。
4. **遗留清单**：解析 `docs/RELEASE-TODO.md` 里 `- [ ]` 的条目，原样列出（这是人写的，只统计和列出，不判断）。
5. **CHANGELOG**：下一个版本号的节是否已有（按 `CHANGELOG.md` 现有格式）；没有只是黄（`prepare` 会补机械底稿）。
6. **结构检查**：`--with-checks` 才跑 `python scripts/check.py --sources-only`（慢，默认不跑）。

输出末尾给一行结论：「可以 prepare / 有 N 项红 / 有 M 项黄」，退出码：有红 1，否则 0。

## 验收口径
- 在当前仓库上跑一次，输出贴进交付说明；当前应该有红（工作区里有未提交的协作记录），逐项核对它说得对不对。
- 自测覆盖：分组解析、ahead/behind 解析、`owner/repo` 从 SSH/HTTPS 两种 URL 解析、RELEASE-TODO 解析；gh 不可用时降级。不真的调 gh，用桩。
- 只读：不 fetch、不写文件、不改 git 状态。（要 fetch 的话提示使用者先 `git fetch`。）
- 注释写为什么，中文，不解释语言基础。

## 做完
`status T-005 review`，附输出与测试结果。不提交 git。

## 进展记录
- [2026-10-20 07:54] cursor：todo → doing
- [2026-10-20 08:02] cursor：doing → review · 自测通过（scripts/tests/test_release_readiness.py exit 0）。实机 readiness 退出码 1：2 红（工作区脏：comms/practice/scripts 分组已列；CI 全量 run 39344238323 仍 queued 非 success）+ 2 黄（RELEASE-TODO 6 条未勾；CHANGELOG 无 10.0.1 节）。远端同步绿。证据：comms/release-next/artifacts/cursor/T-005-readiness-output.txt。未提交 git；未碰 practice/c-gui-lab。
- [2026-10-20 08:02] claude-code：review → doing · 返工：全量 CI 进行中不应算红；输出强制 utf-8，详见消息
- [2026-10-20 08:06] cursor：doing → review · 返工：进行中的全量 CI 改黄（实机 run 39344238323 为黄，已完成 96/133，不再算红）；作业有 failure 且 run 未结束时黄并点名。readiness 子命令入口重配 utf-8。自测 exit 0，含进行中/部分失败/完成成功/完成失败四例。实机 readiness exit 1 只因工作区脏。证据 comms/release-next/artifacts/cursor/T-005-rework-output.txt。未提交。
- [2026-10-20 08:07] claude-code：review → done · leader 验收：返工两处已改（进行中算黄并给作业进度、强制 utf-8），实机输出核对无误，自测通过
- [2026-10-20 08:08] cursor：done → review · 返工完成：1) CI 进行中改黄（已完成 x/共 y；部分失败点名仍黄）；红仅 completed 且非 success。2) readiness 入口 force_utf8_output（同 check.py）。自测 exit 0（含进行中/部分失败/成功/失败四例）。实机 readiness exit 1：1 红（工作区脏）+ 3 黄（CI 进行中 114/133 queued、RELEASE-TODO、CHANGELOG）。证据：comms/release-next/artifacts/cursor/T-005-readiness-output.txt。未提交。
