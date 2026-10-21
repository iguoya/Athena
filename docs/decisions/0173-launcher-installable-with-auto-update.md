# ADR 0173：启动器做成安装包，并接入应用内自动更新

- 日期：2026-10-21
- 状态：已接受（使用者要求；ZCode 会话里曾建议不做，使用者明确改判；设计细节由 leader 按总方向定）
- 修订：[ADR 0170](0170-release-exclusions-launcher-and-legacy-pocket-cube.md) 第 1 条「启动器不做安装包」；[ADR 0172](0172-app-updater-for-all-tauri-apps.md) 第 2 条末句「启动器不在发布矩阵」。两篇原文不改。
- 关系：延伸 0172（更新机制）与 [ADR 0171](0171-incremental-release-per-app-versions.md)（增量发版）；0172 第 8 条「启动器统一更新中心不做」不变。启动器的编排规则仍是 [ADR 0044](0044-menubar-launcher.md)、[0046](0046-unified-dev-orchestrator.md)，进度同步是 [ADR 0155](0155-progress-local-first-sync-to-router.md)。

## 背景

0170 把启动器挡在发布矩阵外，理由是它依赖仓库：靠 `ATHENA_ROOT` 或当前目录找到仓库，扫各分类目录的 `app.json`，执行 `dev` 块里的命令，装到没有仓库的机器上找不到任何东西。ZCode 会话据此建议「启动器不做自动更新」。

使用者的判断不同：已装的二十多个应用都有安装包和应用内更新（0172），入口——启动器——却只能在开发机上从源码跑，这是缺口。另有一条实质理由：进度同步代理（0155）住在启动器里，没有可安装的启动器，没有仓库的机器上已装应用的进度就推不到中心库。

## 决策

1. **启动器（`launcher/webui`，id `launcher`）进发布矩阵**：Tauri 2 应用，NSIS / DMG / DEB，与其它 Tauri 应用同一标准，走 0171 的增量发版与 0172 的更新器（通道 `app-updates/launcher.json`，接入清单见 `packages/app-update/README.md`）。macOS 菜单栏 Swift 版（0048）不动，不打包。
2. **两种运行模式，由 `locate_repo()` 决定**：
   - **仓库模式**：找到仓库（`ATHENA_ROOT`、可执行文件上溯或当前目录上溯命中）——行为与现在一字不改，开发机照旧。
   - **安装模式**：找不到仓库——用内嵌清单工作（下条）。装了启动器的开发机上，安装版开机自启走安装模式；要用仓库模式就设 `ATHENA_ROOT` 或从仓库里启动。
3. **安装模式的应用清单是编译期内嵌的 `catalog.json`**：由编排器新增的 `launcher catalog` 子命令从仓库的 `app.json` 与各 Tauri 应用的 `tauri.conf.json` 生成，提交入库（`launcher/core/catalog.json`），`scripts/check.py` 校验它没有过期。只含发布清单（`scripts/release_apps.json`）里的应用；字段取展示与定位所需的（id、名称、分组、`related`、`evolves_from`、图标、`productName`、`mainBinaryName`、`identifier`、`progress` 声明），不含 `dev` 块。启动器里仍然没有按应用写的分支（`launcher/AGENTS.md` 规则不变）。
4. **安装模式下状态与动作按平台约定**：
   - 已安装 = 在约定位置找到可执行文件：Windows 为 NSIS 每用户安装目录 `%LOCALAPPDATA%\<productName>\<mainBinaryName>.exe`（再查注册表卸载项）；macOS 为 `/Applications` 与 `~/Applications` 下的 `<productName>.app`；Linux 为 PATH 里的 `<mainBinaryName>`。
   - 运行中 = 进程在（现有判据不变）；`starting` 状态（构建进程）在安装模式下不存在。
   - 打开 = 直接启动可执行文件；未安装 = 灰态，点击打开仓库的 Releases 页指路，**启动器不代装**。
   - 异构应用（驾考 Flutter、旧 cpp 窗口、c-gui-lab Electron）的安装位置没有统一约定：清单里显示，标「未支持安装模式启动」，点击同样指路 Releases。以后哪个有了稳定的安装约定再补。
   - 仓库专属功能（构建日志、dev server、图标位图生成、`sync` 的 git 推送）在安装模式下不出现在界面里；不假装成功（ADR 0047 的降级原则）。
5. **进度同步在安装模式照常工作**：同步代理读内嵌清单里的 `progress` 声明，读写各应用在用户数据目录里的本地库（0155 本来就在那里），与中心库互推；它从来不碰 git，安装模式没有影响。
6. **更新**：按 0172 的清单接入；启动器常驻托盘并开机自启，更新装完重启后必须仍是常驻状态（自启项指向安装路径，更新不换路径）。不做「统一更新中心」（0172 第 8 条）。
7. **发布清单与增量计算**：`scripts/release_apps.json` 的 `launcher` 条目用新增的 `dir` 字段声明应用目录 `launcher/webui`（其它应用 `dir` 缺省为 `<root>/<id>`）；`release_plan.py` 按 `dir` 比路径，清单、依赖图与 `matrix` 其余逻辑不变。

## 后果

- 没有仓库的机器上，装一个启动器就能看到全部应用、点开已装的、对未装的被指路，进度同步也在；之后所有应用与启动器自己都靠应用内更新。
- 启动器的 `tauri.conf.json` 由 `bundle.active: false` 改为出安装包，加 updater 配置与公钥；`beforeBuildCommand` 与 `custom-protocol` 约定不变。
- 新增维护面：`catalog.json` 随应用清单变化要重新生成（`check.py` 拦过期）；安装路径约定写死在 core 的一个模块里，Tauri 以后改安装目录要同步。
- 表现层冻结（`launcher/AGENTS.md`，2026-10-11）不被打破：不新增视图、不做视觉打磨，安装模式只是隐藏仓库专属元素、加一个灰态与指路。
- 旧 0170 第 1 条的论证（依赖仓库与开发工具链）对仓库模式依然成立，本篇是在它旁边加安装模式，而不是推翻它。
