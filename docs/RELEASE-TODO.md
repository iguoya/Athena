# 下一版再做

本文件记下 10.0.0 窗口里没收口的事。发版说明写进 `CHANGELOG.md` 的时候，这些不要写成已经完成。

## 发布

- [x] （2026-10-18 已发 v10.0.0）写 `CHANGELOG.md` 的 `[10.0.0]` 节（v9.0.0 以来的主线，不兼容项标 ⚠️），再 `python scripts/release.py prepare 10.0.0` 与 `push`。工作区还有未提交改动时 `prepare` 会拒绝。
- [x] 把本地超前 `origin/main` 的提交推上去。`prepare` 要求两边一致。
- [x] （2026-10-19）`pocket-cube-solver` 已加进 `release.yml` 的 Tauri 矩阵，下一版首发；本机 `--full` 与 `--native` 都绿，CI 的三平台检查也绿（run 39186902938）；安装包作业要等下一次打 tag 才会跑。
- [x] （2026-10-19，ADR 0170）启动器 `launcher/webui` 与旧版 `practice/pocket_cube` 不进发布矩阵：前者依赖仓库与开发工具链、不是可独立安装的应用，后者已定为供参考、不再做。
- [ ] `programming/machine`：等 ADR 0008 的 Tauri 迁移完成后走 `tauri-apps` 矩阵，不给 Qt 壳补作业（ADR 0170 第 3 条；Qt 三平台打包草稿已存档，未上 CI）。
- [x] （2026-10-20，ADR 0170 第 4 条）`practice/c-gui-lab` Windows 安装包：third_party 可复现、启动器适配安装布局、electron-builder 配置都已落地；ci.yml 的 `c-gui-lab-package` 一档首次完整通过（run 39349483787：编译、收 DLL、出 NSIS、静默安装到临时目录、安装态 selftest 七个原生程序都起得来）。已按同一套步骤加进 `release.yml`（job `c-gui-lab`，版本号从 tag 写入，`publish.needs` 已补），**release.yml 只在打 tag 时跑，这一档在 release 里还没跑过**，下一次发版先看它。
- [ ] `edge-ai` 和所有 `lifecycle: archived` 的空壳，等有真实内容再按同一标准加入。不要单独开名单。

## 驾考

zcode 2026-10-20 收口（本机 `check.py driver` 全绿：362 测试 + Windows 构建）：

- [x] T-008 done；T-011 前半（标定引导与就地显示）done，命中反馈与 ADR 0130 照片标注拆成 T-015（owner cursor）。
- [x] T-005 裁决关闭：诉求由 T-007 项目页整体承接，没有未覆盖项；状态机没有关闭态，任务书留在 blocked 归档，等同「已决定不做」。
- [ ] 队列：T-015 → T-013（P2）；T-012 暂缓，等真实使用情况再定；T-104 第一批已交 review（倒库 5/7 步有实拍），直角转弯 3/4 步与倒库 1/7 步缺合格实拍，缺口清单在 `comms/driver/artifacts/T-104/`，建议转使用者补拍。

## 九州

- [x] （2026-10-19，使用者决定）九州冻结：现状已提交（`d5c4579f`、`9a63bc58`），协作舱关闭，T-034 等未完成条目都不做了；仍留在启动器里（`5e747229`）。不再是发版遗留。

## 协作通讯

- [x] （2026-10-19，`ae773bf5`）`comms/comms.py`、`comms/tests/` 的未提交改动，以及各舱任务书、消息、已读游标已提交。九州舱的记录随九州一起处理，没动。
- [x] （2026-10-19）无头 Cursor 会话的 Shell 被 `.claude/settings.json` 的钩子挡死：钩子读 `$CLAUDE_PROJECT_DIR`，Cursor 里它是空的。钩子命令改成不依赖该变量，`comms/spawn.py` 起新会话时也不再继承宿主的 `CLAUDE*` / `SHELL`。

## gtkmm

- [x] （2026-10-19）原生演示的 Windows（MSYS2）与 macOS（Homebrew）两档补上，首跑都全绿（Windows run 39187469455，macOS run 39219054141）；Linux 本来就有。安装包打的是教程壳。

## 10.0.0 发版中顺手修掉的 CI 问题（已完成，留档）

- `ci.yml` 的 tauri 矩阵条件缺 `"all"`，全量跑时 36 个 Tauri 应用整组被跳过，此前从未验证。
- gtkmm 原生演示缺 pnpm/Node；Linux 启动器误编 Tauri 的 webui；驾考两处多余 import。
- `scripts/check.py` 在 Windows 上用裸名字启动 pnpm，找不到 `pnpm.CMD`。
- design-patterns 骨架的「未使用私有字段」警告被当成失败（填空骨架的正常状态）。
- `release.yml`：各应用共用 cargo 缓存，旧安装包被还原导致收集到多个产物；Linux 缺 `libspeechd-dev`。
- 第一次推 tag 后失败，移 tag 到修复提交重跑（与 v9 同法）；没有留下需要排出发版的疑难应用。

## 2026-10-19 加的防再发措施

- `scripts/check.py` 结构卫生新增两条：ci.yml 各作业的 `if` 名单必须含 `all` 且与矩阵一致；Tauri 构建钩子必须 `pnpm`（顺手修了启动器 webui 的 `npm run`）。这两类以前只有 CI 全量跑才暴露。
- `scripts/question_bias.py`：AI 起草的选择题常见「答案几乎都在第 2 位、正确项最长」的毛病，只报告不阻断。体检结果：snake、中国象棋、C++ 教程、魔方四个应用都中招，魔方已整改并加了门禁，其余三个已全部修完（T-003：中国象棋、C++ 教程、贪吃蛇）。
- `gh` 认不出 `git@github.com:` 这种 SSH 别名的 remote，手动触发要加 `--repo iguoya/Athena`；同一分支的两次 dispatch 共用 concurrency 组，后一个会取消前一个，要一个一个来。
- `python scripts/release.py readiness`（只读）：发版前体检，汇总工作区、与远端、最近一次全量 CI（进行中算黄，作业失败点名）、本文件的未勾条目、CHANGELOG；红的挡 `prepare`。发版前先跑它，再 `prepare`。
- 本机（Windows）跑全量 `check.py` 的坑（2026-10-20 实测，除 nas_admin 外 43 个应用全绿）：① `practice/cpp` 要 MSYS2 的 pkg-config，系统 PATH 里 Octave 自带的那个排前面会找不到 gtkmm，把 `C:/msys64/ucrt64/bin` 前置；但**调用 `check.py` 的 Python 要用原生解释器的绝对路径**，否则 `python` 变成 MSYS 版，数学应用的 `engine/.venv` 会被建成 POSIX 布局（`bin/` 而非 `Scripts/`），后面找不到解释器；② 旧 `practice/cpp/build` 的 meson 缓存可能还指着迁移前的 `subjects/` 路径（`ERROR: Unhandled python OSError`），`meson setup build --wipe` 重建；③ `practice/nas_admin` 的冒烟要连真实 PostgreSQL（`db-local.json` 指向路由器），路由器不在线就会 `ConnectionTimeout`，是环境问题，CI 里有 Postgres 服务容器；④ 脚本里 `subprocess.run(text=True)` 必须同时给 `encoding="utf-8"`，中文 Windows 默认 GBK（`practice/cpp` 的生成器测试因此红过，已修 8a560238）。
