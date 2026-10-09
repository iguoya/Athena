# ADR 0104：operating-system 改名 os

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「operating-system 是词组 改名 os」）
- 关系：修订 [ADR 0103](0103-practice-courses-as-attached-subapps.md) 决策 7 的命名；
  零成本改名窗口同 [ADR 0100](0100-single-word-app-ids.md)（本应用无进度数据、
  无发行包）

## 背景

0103 落地时该应用用了词组 id `operating-system`——当时的判断是单词候选
（kernel、process、simulator）无一能达课程全意，收完整词组作显式例外。tiger
复核后定：词组太长，直接叫 `os`。

tiger 同时校准了命名口径（2026-10-10）：**「不用缩写」禁的是自造缩写**
（`softcert` 改名 `software`、`esd` 改名 `embedded` 消灭的正是这类），
**本领域知名的缩写可以用**——`os` 是计算机领域的通行缩写，不在禁止之列。
ADR 0097/0100 原文「不用首字母缩写」按此口径理解，原文不改，由本条承载校准。

收益是 id 与知识点前缀 `os.`（0103 决策 6 的内容层短名）从此一致——目录、
进程、内容层短名收敛为一套名字。

## 决策

1. **`subjects/operating-system` → `subjects/os`**：app.json id、进程/二进制
   `athena-os`、identifier `cn.athena.os`、Cargo 包名与 lib 名、icon theme 名、
   `scripts/check.py` 的期望值同步；显示名「操作系统」、窗口标题、端口 1492、
   实验引擎、内容骨架全部不动。
2. **知识点前缀 `os.` 不变**——它本来就是 `os`（0103 决策 6），改名后 id 与
   前缀自然对齐，AGENTS.md 里「前缀与目录 id 解耦」一句相应改为「前缀与 id
   一致」。
3. 0103 决策 7 中「operating-system 词组例外」的表述由本条取代；0103 状态栏
   补注记，原文不改。
4. **命名口径表述校准**（根 `AGENTS.md`「名字」节与 `docs/REPOSITORY.md` 同步）：
   id 不用**自造**缩写、不用拼音；本领域知名缩写（如 `os`）可以用。

## 后果

- 启动器条目、进程名变为 `athena-os`；Cargo 缓存重编一次（骨架阶段无损失）。
- 其余应用取名仍按 0100「新增应用按单词取」执行；自造缩写与拼音照旧禁止。
