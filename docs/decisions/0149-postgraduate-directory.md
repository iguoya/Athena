# ADR 0149：新增顶层目录 postgraduate/（考研应用）

- 日期：2026-10-12
- 状态：已接受（使用者要求：「把 cs408 的都放入考研目录，这样就是一回事了」；目录名、搬迁范围、
  group 取值经使用者确认：`postgraduate/`、408 家族加 mathematics 与 ascent、group 统一为「考研」）
- 关系：局部修订 [ADR 0148](0148-regroup-domain-circles.md)（该条把分组留在 `group` 字段、不做成目录；
  本条是其中「目录与分组天然一致」的一个特例）；延续 [ADR 0116](0116-reference-attach-and-cs408.md)、
  [ADR 0118](0118-heavier-exam-owns-course-body.md) 的挂靠安排；沿用 ADR 0142、0147 新增顶层目录的做法

## 背景

`cs408` 是考研 408 的主应用，`algorithms`、`data-structures`、`organization`、`os`、`network`
五门科目课的 `parent` 都是 `cs408`；`mathematics` 与 `ascent` 是考研数学与英语。它们在 ADR 0148
之后的 `group` 是「考研」或「计算机基础」，目录却都在 `course/` 下：挂靠关系、分组、目录三者对不上，
启动器思维导图里还出现「group 写计算机基础、却画在考研一团里」的错位。

ADR 0148 没有把分组做成目录，理由是 `group` 横跨目录、会变。但「考研」这一圈不跨目录：圈里的
应用都是自编教学设计的课程、同属一个考试目标、挂靠关系也已经把五门课绑在 `cs408` 上，目录和
分组可以合成一回事。

## 决策

1. **新增顶层目录 `postgraduate/`**，装考研应用。目录名用完整英文单词，不用拼音（仓库命名规则）。
2. **搬入 8 个应用**：`cs408`、`data-structures`、`algorithms`、`organization`、`os`、`network`、
   `mathematics`、`ascent`，用 `git mv`，保留重命名历史。
3. **应用层面零改动**：id、目录名、进程名 `athena-<id>`、知识点前缀、`progress/learning.db`、
   `parent` 全部不变；`launcher open <id>` 不变。`parent` 仍是 `cs408`，本条不新增也不撤销任何挂靠。
4. **`group` 统一为「考研」**：`algorithms`、`data-structures`、`organization`、`os`、`network`
   由「计算机基础」改为「考研」（`cs408`、`mathematics`、`ascent`、`math-tools` 已是「考研」）。
   `math-tools` 留在 `tools/`，它是配套工具，类别由目录决定。
5. **登记**：启动器 `discover_all` 与 GUI 目录加扫 `postgraduate/`；根 `scripts/check.py` 的
   `APP_ROOTS`、各处对账与根目录白名单、`check-app-sources.mjs`、`pnpm-workspace.yaml`
   （`postgraduate/*`）、根 `Cargo.toml` 成员路径、`pnpm-lock.yaml` importers 键、
   CI 与发版里 `ascent` 的路径，以及三处文档（REPOSITORY.md 结构树、根 README、根 AGENTS.md）。
6. **学习应用的出处分档、教学规范不变**：这些应用仍是考试类（`cs408`、`mathematics`、`ascent`）
   或随主应用的科目课，原有规则按应用生效，不因目录改变。

## 后果

- `course/` 里剩下的是不属于考试的课程：C++、C 与机器、Linux、设计模式、Python、人工智能四门，
  以及软考实践子课程 `database`、`firmware`、`microcontroller`、`rtos`。
- 思维导图上五门科目课与 `cs408` 同属「考研」，不再错位。
- `.cache/cargo-target` 的编译缓存按路径隔离，这 8 个应用的 Rust 部分下次构建会重新编译。
- 历史 ADR、STRUCTURE-PROPOSALS、CHANGELOG 里的 `course/<id>` 或 `subjects/<id>` 不回改，
  现行位置以本文与 `docs/REPOSITORY.md` 为准。
