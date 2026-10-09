# ADR 0097：应用 id 全称化——softcert 改名 software-designer，esd 改名 embedded-system-designer

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10：「名字缩写太多、词不达意」「不要轻易用缩写」）；
  注记：决策 1、2 的名字已由 [ADR 0100](0100-single-word-app-ids.md) 收窄为单词
  形式——`software`、`embedded`；「不用缩写」口径与解耦原则不变
- 关系：修订 [ADR 0092](0092-launcher-tree-attach-and-softcert-rename.md) 决策 3 的
  「id 不动」（其理由是丢进度、断更新——两应用均无发行包、无进度数据，此刻改名
  零损失，理由不成立）；[ADR 0090](0090-softcert-splits-esd.md)、[ADR 0095](0095-one-exam-one-app.md)
  等历史文献中的 `softcert` / `esd` 指当时的 id，不回改

## 背景

`softcert`、`esd` 都是缩写 id：前者「软考证书」的生造词，与「软件设计师」对不上；
后者是「嵌入式系统设计师」的英文首字母缩写。tiger 明确不要轻易用缩写。
两应用当前都没有 `learning.db`、没有发行包，目录名、进程名、identifier、
包名一次改清是零成本窗口；一旦有了作答数据或分发版，再改就要付迁移代价。

## 决策

1. **`subjects/softcert` → `subjects/software-designer`**（软件设计师）：
   app.json id、进程/二进制 `athena-software-designer`、identifier
   `cn.athena.software-designer`、Cargo 包名与 lib 名、发行包数据目录名、
   localStorage 键同步改名；显示名「软件设计师」不变（0092 已定），
   tauri.conf 窗口标题「软考」顺带对齐为「软件设计师」（0092 决策 3 漏改项）。
2. **`subjects/esd` → `subjects/embedded-system-designer`**（嵌入式系统设计师）：
   同上全套。显示名不变。
3. **内容层短名与 id 解耦，保留不动**：知识点前缀 `sc.*`、`esd.*`，课程目录
   `content/esd`，章节 id `esd-*`，真题卷 id `past-exam-esd-*`。它们是界面
   不可见的内部命名空间短名，全称做 namespace 冗长无益；`esd.` 对嵌入式系统
   设计师是通行短名，刚在 0090 决策 4 改写到位，不再折腾。将来若产生跨应用
   误导再议。
4. **其余一切不动**：端口 1450 / 1480、进度库 schema、内容与教学结构、两套
   界面体系；启动器零改动（按 app.json 自动发现，目录改名后条目自动更新）。
5. 历史文献（ADR、tag `pre-softcert-reorg`、提交信息）中的旧 id 不回改；
   `AGENTS.md`、`README`、`docs/REPOSITORY.md`、根 `README.md` 等现状文档
   同步为新 id。

## 后果

- 启动器、思维导图中的应用条目与进程名变为全称；目录名与 id 恢复一致。
- 两应用的 Cargo 增量缓存按新包名重编一次（一次性成本）。
- `docs/REPOSITORY.md` 结构树与名字表、根 `README.md` 应用表随改名更新。
- 今后新增应用起名同样遵循「不用缩写」：id 用完整的英文词或词组
  （连字符连接），如 `math-tools`、`software-designer`。
