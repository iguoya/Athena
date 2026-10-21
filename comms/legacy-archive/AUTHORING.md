# 历史归档条目写作规范（第二阶段）

依据 [ADR 0176](../../docs/decisions/0176-legacy-github-repos-archive-merge.md)。清单阶段结束后，把各自领域的 `keep` 单元写成目标应用里的**历史归档章节**条目。
**活样板**：`programming/design-patterns/content/archive.json` 里的 `dp.arc.observer`，以及它的案例目录 `content/cases/arc_dp_observer/`——先把它在应用里点开看一遍（或读 JSON），再动手。

## 一、选取：宁缺毋滥（根 AGENTS.md ADR 0129）

清单里的 `keep` 不等于都要进应用。一个条目必须有**可批注的实质**：手写逻辑有一定规模（大致 30 行以上的有效代码），或完整展示一个概念/结构/小项目。下列情况记 `drop-trivial`，**不进应用**，只记入该应用的 `content/archive-dropped.md`（一行一条：旧路径、原因；原仓库归档后仍可取回，所以删得起）：

- IDE 向导生成的模板、Hello World 级、只改了几行向导代码；
- 与已收条目内容几乎相同的重复变体（合并成一个条目，在 `origin.duplicates` 里列出被合并的路径）；
- 你读完代码**写不出 3 条具体的批注**——写不出，说明它没有可教的东西。

同一主题的多代演进（如 Strategy 两个版本）各自成条，批注里互相对照。

## 二、产物位置（每个应用只有一个负责人，独占以下文件）

| 文件 | 内容 |
|---|---|
| `<应用>/content/archive.json` | `{"tracks":[…], "chapters":[ 唯一一章 ]}`，章 `id:"archive"`、`layer:"archive"`；启动时由共用壳接在主课表末尾，**不要改 `curriculum.json`** |
| `<应用>/content/cases/arc_<前缀>_<slug>/` | 该条目的**原样**文件（见第三节） |
| `<应用>/content/archive-dropped.md` | 被 `drop-trivial` 的清单 |

## 三、案例目录：原样

- 把规范版的文件**逐字节拷贝**进 `arc_*` 目录，保持原文件名与子目录；不整理格式、不改行尾、不修错别字、不重命名。
- 不带：`*.user`、`*.pro.user*`、`*.depend`、`*.layout`、编译产物（`.o`、`a.out`、`.exe`）、IDE 工作区文件、大于 256 KB 的文件、图片以外的二进制。依赖的小图片/资源可以带（Qt/GTK 条目常见）。
- **能编译就不动它**。只有“本机编译器因为纯粹的环境差异过不去”才允许最小改动，改动处必须写成 `// [ARCHIVE] 原为：……` 的注释并在批注里交代。代码本身有语法错误（如 `#include vector`）则**不修**：`run` 标 `read-only`，`run_note` 写清“原代码从未编译通过：<文件:行>”——这本身就是批注的第一条。
- 案例目录名 `arc_` 开头、全小写字母数字下划线，且不得与已有案例重名。
- `run` 的取值：`cli`（本机 g++/gcc 直接编译，**必须由你真编译真运行过**）、`linux-only`（POSIX/内核，Windows 上预期失败）、`toolchain`（需 Qt/GTK/SDL 等，应用里只读）、`read-only`。`sources` 是参与编译的源文件相对路径清单，`std` 写能通过的最低标准（`c++11`/`c++14`/`c++17`/`c++20`，C 代码写 `c11` 等），**以实测为准**。

## 四、条目 JSON（照 `dp.arc.observer`）

```jsonc
{
  "id": "<前缀>.arc.<slug>",        // 前缀同应用的知识点前缀（dp. / ds. / algo. …见该应用 curriculum），id 一经写出永不改嫁
  "title": "观察者模式（早期练习）",
  "difficulty": 2, "mastery_goal": "understand", "knowledge_type": "skill",   // 归档条目一律 understand；类型 skill/concept/strategy
  "requires": ["dp.observer"],      // 指向主课表里已有的知识点，没有就 []
  "track": "archive", "guide_line": "一句话：这份旧代码是什么、批注要抓什么", "weight": "了解",
  "outline": { "promise": "…", "pain": "…", "model": "…", "scope": "…", "judgment": "…", "landing": "…" },  // 六项各一两句，写实不写套话
  "lesson": { "blocks": [
    { "type": "lead", "text": "…它对在哪、错在哪；运行后看什么" },
    { "type": "archive", "case": "arc_dp_observer", "sources": ["main.cpp","observer.cpp","subject.cpp"], "std": "c++17", "run": "cli",
      "summary": "……", "origin": { "repo": "DesignPattern", "path": "Observer", "first_commit": "2022-05-02", "duplicates": ["…"] },
      "notes": [ { "file": "subject.cpp", "line": 11, "end": 12, "kind": "ownership", "text": "…" } ] },
    { "type": "callout", "tone": "info", "title": "对照现行讲解", "text": "指向本应用主线里对应的章节/知识点，不要写不存在的东西" }
  ]}
}
```

`origin.first_commit` 用 `git log` 取，**不凭印象**。`kind` 取值：`naming` `ownership` `coupling` `testing` `portability` `style` `design` `other`。

## 五、批注的标准（这是整件事的价值所在）

1. **具体**：说出哪个文件第几行、是什么问题、会造成什么后果、该怎么改。禁止“命名不规范”“可读性差”“建议重构”这类空话。
2. **真实**：你必须**读过并（可运行的）运行过**代码；结论要是你能复现的事实。说“双重释放”，就要能指出触发它的调用序列；不确定的写“可能”并说明条件。**批注行号逐条核对**（`archive_check.py` 会检查越界，但行号指没指对要你自己对）。
3. **公平**：这是当年的练习代码。指出的是写法和程序组织上的不足，对照的是**本应用现行主线的做法**；写得好的地方也可以用一条批注点出来（`kind` 用 `design`/`style`），不要只挑刺。
4. 每个条目 **≥3 条**批注，覆盖 **≥2 种** `kind`；批注正文里用 `反引号` 包标识符；一条批注一个问题，不超过约 150 字。
5. 不凭印象写出处、不编造书名页码；不确定出处就不写。写“与某某教材一致”之前核对。

## 六、章与知识点的约束

- 章 `summary` 可沿用 design-patterns 的写法（说明“从旧仓库去重整理、原样保留、批注、留待人工审视”）。
- 章内条目按主题分组排序（组内按难度/演进先后）；组名写进条目 `guide_line` 开头，如“[线性表] …”。
- 条目数量按“精选”走，不设下限。**宁可 15 条扎实也不要 60 条敷衍。**

## 七、验证（交 review 前全部做完）

```sh
# 单应用快速自检（根检查 scripts/check.py 也会跑同一套）
python -c "import sys; sys.path.insert(0,'scripts'); import archive_check as a; from pathlib import Path; print(a.check_app(Path('<应用目录>')))"
python <应用目录>/scripts/check.py --skip-rust   # 前端类型检查与构建（design-patterns 的 check.py 不带这个参数，直接跑）
```

两者都必须通过。再自己抽 3 个 `cli` 条目，用 `g++ -std=<std> <sources>`（C 用 gcc）在**系统临时目录**里重新编译运行一次，确认和你写进 `summary`/批注里的输出一致。转 `review` 时 `--note` 写：条目数、drop-trivial 数、`cli` 条目实测通过数、检查命令输出摘要。

## 八、边界

- 只写本任务书指明的应用目录里的上述三个位置，**不改** `src/`、`curriculum.json`、`scripts/`、`packages/`；前端或校验要改的地方发消息给 claude-code。
- `git add` 写明确文件路径（仓库有钩子会拦整目录添加）；提交由 leader 验收后统一做，worker 不提交。
- 不要碰 `.cache/legacy-src`（只读）。需要编译就拷到系统临时目录。
