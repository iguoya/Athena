# ADR 0105：algorithm 复名 dsa——DSA 是数据结构与算法的领域知名缩写

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10 问：「dsa 算不算数据结构和算法的知名公认
  缩写，如果算的话可以采用」；查证后采用）
- 关系：依 [ADR 0104](0104-os-rename.md) 决策 4 的口径（禁自造缩写，领域知名
  缩写可用）对 0097/0100 时代改名的复评；进度库与内容零变动

## 背景

1. 该应用原名 `dsa`，在 ADR 0097「不用缩写」口径时代改名为 `algorithm`
   （当时 dsa 被当作待展开的缩写处理）。
2. 0104 校准口径后重评：**DSA 是 Data Structures and Algorithms 的领域通行
   缩写**——Tutorialspoint 明确「Data Structures and Algorithms is abbreviated
   as DSA」，IBM、GeeksforGeeks、W3Schools、Codecademy 等平台的教学内容都把
   DSA 作为标准术语（2026-10-10 查证）。`dsa` 不是自造缩写，按新口径合规。
3. 应用内部本来满是 dsa：知识点前缀 `dsa.`、环境变量 `ATHENA_DSA_ROOT`——
   复名后 id、前缀、环境变量全套对齐。`docs/REPOSITORY.md` 的登记也从始至终
   写的是 `dsa`（当时改名漏了同步，此次一并归位）。

## 决策

1. **`subjects/algorithm` → `subjects/dsa`**：app.json id、进程/二进制
   `athena-dsa`、identifier `cn.athena.dsa`、Cargo 包名与 lib 名、文档与命令
   示例同步；显示名「数据结构与算法」、group「算法」、端口 1420、
   `ATHENA_DSA_ROOT`、知识点前缀 `dsa.`、内容与 `progress/learning.db`
   全部不动。
2. 内容层文件 `algorithm_trace.hpp` 等不是应用 id，不改（改了会破坏 content
   引用）。
3. 0102/0103 等历史 ADR 原文里的 algorithm 指称不回改（只增不改），由本条
   承载新旧对应。

## 后果

- `docs/LEARNING-METHODS.md`、software `docs/content-plan.md` 的活文档引用
  同步为 dsa；历史 ADR 不动。
- 启动器条目、进程名变为 `athena-dsa`；Cargo 增量缓存重编一次。
