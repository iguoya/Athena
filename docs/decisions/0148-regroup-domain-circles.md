# ADR 0148：领域圈（group）重新归并

- 日期：2026-10-12
- 状态：已接受（使用者给出分组：计算机基础 / 程序设计 / 人工智能 / 电子信息 / 考试，并确认
  「考试改叫考研，driver 单独一个考证组」）
- 关系：调整 [ADR 0102](0102-exam-apps-as-top-level-groups.md)（`software`、`embedded`、`driver`
  的 group 取值）、[ADR 0111](0111-programming-group.md)（「编程语言」并入「程序设计」，
  `python` 入圈）、[ADR 0120](0120-ai-group-and-llm-curriculum.md)（`python` 不再属于「人工智能」圈，
  仍是该课程路线的入口）；沿用 [ADR 0145](0145-subjects-rename-to-course.md) 之后的目录布局

## 背景

`group` 是每个 `app.json` 里的自由字符串，启动器按它给应用分组显示（思维导图的领域胶囊、
列表分区）。它最初是因为 `subjects/` 下应用多了需要分类才产生的。长期叠加之后有 12 个取值，
其中「算法」「数据结构」「操作系统」「计算机网络」各只装一门课，「编程语言」与「程序设计」只差一个
名字，「考研」与「计算机」互相交叉。

使用者提出过一个替代方案：干脆把分组做成顶层目录，与 `practice/` 平级，取消 `course/`。

## 决策

1. **分组仍是 `app.json` 的 `group` 字段，不做成目录。** 目录说「这是哪一类东西」
   （课程 / 手册 / 项目 / 考证 / 导师 / 工具：建法、判分、检查规则各不相同，很少变），`group` 说
   「属于哪个学科圈」（会经常调整）。两个维度互相垂直：`certification/software` 的圈是
   「计算机基础」，`guide/gtkmm`、`practice/earth` 的圈是「程序设计」，一个目录装不下一个圈。
   做成目录还有两个代价：每次调整圈就是一次大规模搬迁（ADR 0145 的改名动了 1299 个文件），
   每多一个顶层目录要改 `APP_ROOTS`、根目录白名单、pnpm / Cargo 成员、CI 与启动器扫描列表。
2. **归并为 6 个圈：**

   | group | 应用 |
   |---|---|
   | 计算机基础 | `os`、`network`、`data-structures`、`algorithms`、`organization`、`database`、`software` |
   | 程序设计 | `c-plus-plus`、`machine`、`design-patterns`、`linux`、`python`、`gtkmm`、`c-gui-lab`、`earth`、`cpp`、`pocket-cube` |
   | 人工智能 | `machine-learning`、`deep-learning`、`llm-app`、`llm-finetune` |
   | 电子信息 | `firmware`、`microcontroller`、`rtos`、`embedded` |
   | 考研 | `cs408`、`mathematics`、`ascent`、`math-tools`（数学配套工具跟随 `mathematics`） |
   | 考证 | `driver` |

3. **不在本条范围内、保持原值：** `mentor/` 下的「大赛」（`competitions`）与「图谱」（`polaris`）
   是图谱/参考类，不是课程圈；`nas-admin` 没有 group。
4. **`python` 归「程序设计」，但仍是人工智能课程路线的入口**：它教的是会编程的人如何用 Python 与
   AI 工具链，先修关系和路线说明（`route` 文案、ADR 0120）不变，只是启动器里不再归进「人工智能」圈。
5. **`group` 取值不是写死的名单**：启动器按首次出现的顺序动态分组，改值不需要改启动器代码。
   应用自己的 `scripts/check.py` 与 `src/App.tsx` 里若硬编码了自己的 group，随本条同步
   （只有 `python` 有）。

## 后果

- 16 个应用的 `app.json` `group` 改值；应用 id、目录名、进程名、知识点前缀、进度库全部不动。
- 启动器思维导图里有 `parent` 的应用沿用挂靠者的圈：`algorithms`、`data-structures`、`os`、
  `network`、`organization` 的 `parent` 都是 `cs408`，所以导图上它们仍画在 `cs408`（考研）那一团，
  而它们自己的 `group` 是「计算机基础」。本条不改 `parent`；要让它们在导图上也归到「计算机基础」，
  需要另议挂靠关系。
- 「圈」的历史说法留在原 ADR 里不回改；现行取值以本文与 `docs/REPOSITORY.md` 为准。
- 若以后确实要把某个圈做成目录，先回答本条第 1 点的两个问题：跨目录的应用放哪，以及谁来承担
  每次调整的搬迁成本。
