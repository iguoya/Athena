# ADR 0060：`apps/` 拆成 `subjects/` 与 `practice/`，按意图分

- 日期：2026-09-23
- 状态：已接受
- 修订：ADR 0045（所有应用平级住在 `apps/` 下）——平级不变，住处按意图分两处

## 背景

`apps/` 这个名字只说了「这里是应用」，没说是干什么的应用。实际上里面装着两种
意图完全不同的东西：

- 课程学科学习：`cpp`、`c`、`dsa`、`english`、`mathematics`、`driver`，以及
  同属学科体系的 `polaris`（图谱）和 `design-patterns`（素材）。
- 项目应用：`apps/practice/` 下的独立小项目（目前是 `pocket_cube`），做的是
  「动手做出一个能跑的东西」，不追求知识点覆盖、不接掌握度体系。

后者被嵌在 `apps/practice/` 这一层容器里，启动器要用 `--root apps/practice`
这样的特殊路径才找得到它，读目录的人也会误以为它是某个学科应用的附属。

## 决策

1. `apps/` 更名为 `subjects/`：负责**课程学科学习**。其中各目录的三类划分
   （学习应用 / 图谱参考类 / 素材坑）不变，仍以根 `AGENTS.md` 的判据为准。
2. `apps/practice/` 上移为仓库根的 `practice/`，与 `subjects/` 平级：专注**项目
   应用**。每个子目录一个独立小项目、各自一份 `app.json`；`practice/` 本身不是应用。
3. 启动器的发现根随之改为 `subjects/*` 与 `practice/*` 两处，界面分区不变；
   仓库根的识别标志从 `apps/` 目录改为 `subjects/` 目录。
4. 标识不跟着改：进程名 `athena-<id>`、知识点前缀、环境变量 `ATHENA_APPS_ROOT`、
   代码里泛指「应用」的变量名都保持原样——它们指的是「应用」这个概念，不是目录名。

## 后果

- 历史 ADR 与 CHANGELOG 保留 `apps/...` 的原文，不回改；读到时按
  `apps/practice/ → practice/`、`apps/ → subjects/` 对照即可。
- 现行规范（`AGENTS.md`、各应用 `AGENTS.md` / README / 文档）、代码、CI 与检查脚本
  已全部改用新路径。
- 已有的本地构建目录（Meson `build/`、CMake、Cargo `target/`、Flutter 生成文件）
  里记着旧的绝对路径，搬家后需要清掉重新配置。
