# ADR 0150：取消 course/，课程类应用按领域圈分目录

- 日期：2026-10-12
- 状态：已接受（使用者要求：「按照分组，彻底将 course 虚化，不确定划分的项目问我」；
  不确定的软考实践子课程经使用者确认「按分组各建一个目录」，目录名确认用 `programming/` 与
  `artificial-intelligence/`）
- 关系：取代 [ADR 0145](0145-subjects-rename-to-course.md)（`course/` 作为课程类容器不再存在）；
  推进 [ADR 0149](0149-postgraduate-directory.md) 的做法到全部课程类应用；
  修订 [ADR 0148](0148-regroup-domain-circles.md) 决策 1（分组不做成目录）——课程类应用的
  目录现在与领域圈一致，`group` 仍保留为软约束

## 背景

ADR 0149 把「考研」圈做成了目录 `postgraduate/` 之后，`course/` 里只剩 13 个应用，
都有明确的领域圈。继续留着 `course/` 当「其余课程」的容器，就多一层没有含义的分类。

## 决策

1. **取消 `course/`**，课程类学习应用按领域圈分到四个新目录（加上已有的 `postgraduate/`）：

   | 目录 | 应用 |
   |---|---|
   | `programming/` | `c-plus-plus`、`machine`、`linux`、`python`、`design-patterns` |
   | `artificial-intelligence/` | `machine-learning`、`deep-learning`、`llm-app`、`llm-finetune` |
   | `computer-fundamentals/` | `database` |
   | `electronics/` | `firmware`、`microcontroller`、`rtos` |
   | `postgraduate/` | （ADR 0149）`cs408` 及 7 个应用 |

   目录名用完整英文单词，不用拼音。`git mv` 保留重命名历史。
2. **应用层面零改动**：id、目录名、进程名、知识点前缀、进度库、`parent`、`group` 全部不变。
3. **类别目录与分组目录并存**：`guide/`、`practice/`、`certification/`、`mentor/`、`tools/` 仍按应用
   的类别分（建法、判分、检查规则不同）；课程类学习应用按领域圈分。两种划分在顶层并列，
   `group` 字段仍是软约束（ADR 0148 补记）。
4. **启动器不再靠 `course/` 认仓库根**：改为根 `AGENTS.md` 加 `launcher/` 目录；扫描课程类应用
   用 `LEARNING_ROOTS`（`launcher/core/src/manifest.rs`），合起来仍按应用目录名排序。
   根 `scripts/check.py` 由 `GROUP_ROOTS` / `APP_ROOTS` 统一派生，各处不再各写一份目录清单。
5. **进度库的 git 规则不再写具体目录名**：`.gitattributes` 与 `.gitignore`、`.zcodeignore` 里的
   `course/*/progress/*.db…` 改为 `*/*/progress/*.db…`。此前 ADR 0149 搬迁时漏改，是它造成
   `postgraduate/` 下 SQLite 临时文件显示为未跟踪。
6. **新增课程类应用**：先看它属于哪个领域圈；已有对应分组目录就放进去，没有同类、归属不明时
   先问使用者，不自己造目录（`new-app` skill 同步）。

## 后果

- 顶层多了 4 个目录，`course/` 消失；`certification/` 的软考主应用与它们的实践子课程
  （`software` 与 `database`、`embedded` 与 `firmware` 等）分在不同目录，靠 `group` 和文档关联。
- `computer-fundamentals/` 目前只有 `database` 一个应用；是否并入别处另议。
- 本地脚本、笔记里写死的 `course/…` 路径失效；`launcher open <id>` 不受影响。
- `practice/cpp` 不需要知道其他应用的存在（使用者原则）：删去它的 `external_apps_root()`、对应的三个测试，
  以及 `programming/c-plus-plus/app.json` 里传给它的 `ATHENA_APPS_ROOT`。该函数此前没有任何真实调用方。
- 历史 ADR、STRUCTURE-PROPOSALS、CHANGELOG 里的 `subjects/<id>`、`course/<id>` 不回改，
  现行位置以本文与 `docs/REPOSITORY.md` 为准。
