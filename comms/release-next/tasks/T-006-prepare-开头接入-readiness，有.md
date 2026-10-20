---
id: T-006
title: prepare 开头接入 readiness，有红即拒
owner: cursor
status: done
priority: P1
depends: 
created: 2026-10-20 08:17
updated: 2026-10-20 08:58
---
## 背景（采纳你的建议）
体检现在是可选的，打 tag 的人可能不跑。让 `prepare` 开头自己调 readiness，有红就拒绝，黄只打印。

## 要求
1. `prepare`（含 `--dry-run`）开头调用 `release_readiness` 里同一套检查，**以 readiness 为准，去掉 `check_prerequisites` 里重复的口径**（工作区干净、与远端同步）。`check_prerequisites` 里 readiness 没覆盖的检查（只能在 main、版本只增、tag 未占用）保留不动。两处不许各说各话：同一个事实只在一个地方判断。
2. 有红：打印体检表后拒绝，退出码非 0，信息里说明红在哪、怎么处理。黄：打印、继续。`--dry-run` 下红只提示、不拒绝（要预览改动）。
3. 提供 `--skip-readiness`（逃生口，要显式写，且打印一行醒目的警告「已跳过发版体检」），给紧急热修用。
4. gh 不可用或没登录：CI 项黄（降级，不挡），这点已经是现状，保持。
5. 自测补用例：红拒绝、黄放行、dry-run 红放行、skip 生效；不真的 prepare，用桩替掉 git 与 gh。别动 `push`。
6. 名下路径同 T-005。做完 `status T-006 review`，附证据。

## 不用做
安装包作业里的 fetch 片段不用写：它在 zcode 的 T-101 里，他会采纳你在即时消息里给的方向。

## 进展记录
- [2026-10-20 08:17] cursor：todo → doing
- [2026-10-20 08:19] cursor：doing → doing
- [2026-10-20 08:24] cursor：doing → review · prepare 开头接 readiness：有红拒绝，黄继续；dry-run 红只提示；--skip-readiness 打印已跳过发版体检。check_prerequisites 去掉工作区与远端同步。自测 test_release_prepare_gate.py 与 test_release_readiness.py 均 exit 0（含 git/gh 桩）。未真 prepare，未改 push，未提交。证据 artifacts/cursor/T-006-evidence.txt。
- [2026-10-20 08:25] cursor：review → review · prepare 开头接入 readiness：红拒/黄放/dry-run 红只提示/--skip-readiness 逃生口；check_prerequisites 去掉工作区与远端同步（归 readiness）。自测 test_release_readiness + test_release_prepare_gate 均 exit 0；实机 prepare --patch --dry-run exit 0（有红仅提示后继续预览）；无 skip 的 gate 拒绝。证据：comms/release-next/artifacts/cursor/T-006-prepare-gate-output.txt。未提交；未碰 practice/c-gui-lab / push。
- [2026-10-20 08:58] claude-code：review → done · leader 验收：prepare 与 dry-run 实机核对（有红拒绝、不改任何文件）、两份自测通过
