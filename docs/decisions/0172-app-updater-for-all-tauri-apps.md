# ADR 0172：应用内自动更新器推广到全部 Tauri 发布应用

- 日期：2026-10-20
- 状态：已接受（使用者逐条确认；实现随 10.1.0 走增量发版）
- 延伸：[ADR 0081](0081-unified-release.md) 决策 4——拾阶的更新器机制保留，但不再由拾阶独占，
  推广为全矩阵策略；延伸 [ADR 0171](0171-incremental-release-per-app-versions.md)——Release
  的 publish 侧为本次构建的应用推送各自的更新通道。0081、0171 原文不改。
- 关系：拾阶应用内更新的原始决策是应用级 [ADR 0018](../../postgraduate/ascent/adr/0018-auto-update.md)，
  本篇把它的模式定为全矩阵策略；平台取舍沿 [ADR 0051](0051-platform-priority-macos-windows-first.md)。

## 背景

拾阶自独立仓库迁入即带应用内更新器（0018），0081 统一发版时作为「先进机制」保留，但仅此
一例。其余二十多个 Tauri 发布应用没有更新器，装过的副本要用新功能只能手动下载安装包逐个
覆盖。使用者的判断：这套机制应该所有应用都有。

调研结论（2026-10）：Tauri 官方 updater 插件（拾阶在用的 `tauri-plugin-updater`）就是
Tauri 桌面生态的标准方案，官方没有更先进的替代；社区有差分更新插件，但本仓库安装包只有
几 MB 到几十 MB，全量下载以秒计，差分收益趋近于零，按 [ADR 0049](0049-portability-is-a-cost-benefit-call.md)
的成本收益判据不引入。真正可调的只有更新策略参数（检查时机、打断程度、手动入口），
「启动即静默更」在三者中对单用户自用软件最优。

## 决策

1. **机制**：发布矩阵内的全部 Tauri 应用接入 `tauri-plugin-updater`（配合
   `tauri-plugin-process` 的重启），全仓库共用一把签名密钥（CI 现有
   `TAURI_SIGNING_PRIVATE_KEY`），公钥一致。
2. **范围**：Tauri 矩阵全进。`practice/c-gui-lab`（Electron，同级别方案 electron-updater
   属另一套）、`certification/driver`（Flutter 桌面无一等公民更新器）、`practice/cpp`
   （GTK 原生，无现成方案）不进本期，需要时单独立项。启动器不在发布矩阵（0170），不涉及。
3. **策略照抄拾阶（0018 模式）**：应用启动时静默检查（15 秒超时，离线或失败一律静默，
   应用必须能离线使用）；发现新版本即下载安装，右下角进度条提示，装完自动重启；不设
   「检查更新」手动入口。三平台行为一致：Windows 上「下载完不重启、下次启动生效」做不到
   真无感（NSIS 安装器必须先结束运行中的应用），不采用。
4. **通道**：GitHub Release 固定标签 `app-updates`（仿 `ascent-updates`），每应用一个
   `<id>.json`（latest.json 格式），publish 时为本次构建的应用逐个上传（clobber）。比
   每应用一个标签少开二十多个假 Release。
5. **平台面**：更新工件 Windows 走 NSIS（矩阵现状），macOS 走 `.app.tar.gz`（updater
   标准工件，dmg 照旧产出）；Linux 不打 AppImage，通道 json 不写 Linux 平台条目——Linux
   上检查结果就是无更新，更新走手动下载 deb。这是 0051 优先级下的明确降级，不是缺陷。
6. **组件**：更新提示抽成仓库根共用件 `packages/app-update`（`@athena/app-update`，纯
   TypeScript 源码不预编译，0137 同款），各应用前端挂一行。
7. **拾阶迁移**：endpoint 改指 `app-updates/ascent.json`，UI 换用共用组件；过渡期
   publish 对拾阶双写（旧 `ascent-updates` 标签照常更新），等本机已装副本换到新通道后
   停写旧标签。停写无硬时限，停之前旧副本的更新不断供。
8. **不做**：启动器「统一更新中心」（读各应用通道显示可更新）是自研一摊，单用户收益
   趋近于零，明确不做。

## 后果

- 应用更新零手动：发版后打开应用即自动更到新版。
- 落地 = 全矩阵加依赖（两个插件进仓库根与 launcher 两个工作区的公共依赖表），10.1.0
  的增量计算自然得出「所有 Tauri 应用都有改动」，全量重构建、全部升版本（0171 决策 3
  的「凡被重新构建必须升版本」）。这次发版同时是所有已装副本换装「带公钥新包」的一次性
  时机：手动换装这轮之后，更新全走应用内通道。
- Release 页每应用多 updater 工件：`.sig` 签名文件与 macOS 的 `.app.tar.gz`。
- 新增故障面：签名不匹配、下载失败——失败一律静默，不影响使用；排查走 Release 页。
- 需要改动：各应用 `tauri.conf.json`（updater 配置与 `createUpdaterArtifacts`）、
  `capabilities`（`updater:default`、`process:allow-restart`）、Cargo 依赖与插件注册、
  前端挂组件；`release.yml` 的 publish 作业按 0171 的发版计划为本次构建的应用推通道
  （该文件在 release-next 舱 leader 名下，随增量机制一并落地）。
