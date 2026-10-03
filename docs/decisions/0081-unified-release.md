# ADR 0081：统一发版——一个 v* tag 全量构建所有应用，发一个 Athena Release

- 日期：2026-10-03
- 状态：已接受；修订 subjects/ascent 应用级 [ADR 0018](../../subjects/ascent/adr/0018-auto-update.md)
  中「每次推送即发版」「发布入口独立」的描述（0018 原文不改，更新器机制原样保留）；
  取代提交 `c115dd4` 引入的 driver 独立发版工作流（该做法未立 ADR，随本条一并回退）
- 范围：仓库发布机制，涉及 subjects/cpp、subjects/driver、subjects/ascent 三个应用

## 背景

发版入口一度有三个：`release.yml`（`v*`，发 cpp）、`driver-release.yml`（`driver-v*`）、
`ascent-release.yml`（`ascent-v*`）。三套触发、三个 Release 页、三种发版节奏。

查这段历史，拾阶独立 tag 不是偏好，是迁入时的技术约束：Tauri 更新器要读一个**固定地址**的
`latest.json`，在原独立仓库靠 `releases/latest` 就行；并入 Athena 后 `releases/latest` 被所有
应用共用，不能再指望它，才改用固定标签 `ascent-updates` 存放（ascent ADR 0018、0020 与工作流
注释都有记录）。这个约束由 `ascent-updates` 解决之后，与「发布由谁触发」已经无关。

根 `CHANGELOG.md` 本来就是一个版本号、多应用小节的结构（v8.0.0 下分驾考、启动器等小节）。
使用者的决定：**所有应用一次性随 Athena 版本号发布，更统一**；拾阶工作流的先进机制（签名
构建、`latest.json` 更新通道）保留，融入统一流程。

## 决策

1. **唯一发版入口**：推 `v*.*.*` tag，`release.yml` 全量构建 cpp（macOS 双架构、Windows、
   Linux）、driver（Windows zip、macOS dmg×2、Linux tar.gz）、拾阶（Windows 签名安装包），
   发**一个** Athena Release。删除 `ascent-release.yml` 与 `driver-release.yml`。
2. **版本号一个体系**。拾阶自下一个 `v*` 起并入（8.0.0 起）。Tauri 更新器按 semver 比较，
   8.0.0 > 0.1.9，已安装的旧版能正常收到更新；ADR 0020 锁定的 `productName`、`identifier`、
   Cargo 包名不动（它们决定安装目录、数据目录与更新识别）。
3. **版本号来源**：cpp 保持「预提交 meson 版本 + tag 校验」（既有约定不动）；driver 由 CI 把
   tag 版本写入 `pubspec.yaml`（沿用 driver-release.yml 的做法，发版免预提交）；拾阶由 CI
   把 tag 版本写入 `tauri.conf.json`（现状即如此，仓库里不维护实时版本）。
4. **拾阶更新器机制原样保留**：安装包用 `TAURI_SIGNING_PRIVATE_KEY` 签名；`latest.json`
   同步到固定标签 `ascent-updates`。签名 key 未配置时拾阶 job 跳过并 notice，不阻塞
   cpp、driver 照常发布。
5. **合流方式**：拾阶的 tauri-action 以 draft 方式创建统一 Release（tagName 用 `v*` 本尊）
   并产出 `latest.json`；publish job 在其上补齐 cpp、driver 资产与 SHA256SUMS、按 CHANGELOG
   生成说明后正式发布。key 缺失、拾阶 job 被跳过时，publish 退回现有的「不存在则创建」路径。

## 后果

- 给拾阶推急修也要全量发版。接受：个人仓库发版频率低，急修频率更低，全量构建时长可容忍。
- 发版前 CHANGELOG 各应用小节要写全，统一 Release 的说明才完整。
- `release.yml` 变长，但发版心智只剩一条：打 `v*` tag。
- 发版操作入口是 `scripts/release.py`：`prepare` 校验前提、bump meson 版本、按提交预生成
  CHANGELOG 节并打 tag；`push` 推送并触发 CI。两阶段之间留人工润色 CHANGELOG 的位置；
  meson 版本必须预提交（CI 用 tag 校验它），driver、拾阶的版本由 CI 写入，不进仓库。
- 已发布的历史 Release 与 `ascent-updates` 标签不动，历史提交不改写；`c115dd4` 的行为由
  后续提交回退，git 历史保留。
