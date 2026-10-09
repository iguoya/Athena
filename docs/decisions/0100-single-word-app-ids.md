# ADR 0100：应用 id 再收窄为单词——software-designer 改名 software，embedded-system-designer 改名 embedded

- 日期：2026-10-10
- 状态：已接受（tiger 2026-10-10 定名）
- 关系：修订 [ADR 0097](0097-spell-out-app-ids.md) 决策 1、2 的具体名字；「不用缩写」
  的口径不变——`software`、`embedded` 都是完整的英文单词，只是不再用词组

## 背景

0097 把 `softcert` / `esd` 全称化为 `software-designer` / `embedded-system-designer`。
tiger 复核后定：词组太长，改用单词——`software`（软件设计师）、`embedded`
（嵌入式系统设计师）。两应用依旧没有进度数据与发行包，改名仍是零成本窗口。

## 决策

1. **`subjects/software-designer` → `subjects/software`**：app.json id、进程/二进制
   `athena-software`、identifier `cn.athena.software`、Cargo 包名与 lib 名、
   发行包数据目录 `AthenaSoftware`、localStorage 键同步；显示名「软件设计师」、
   端口、进度库 schema、内容不动。
2. **`subjects/embedded-system-designer` → `subjects/embedded`**：同上全套
   （数据目录 `AthenaEmbedded`）。
3. **0097 决策 3 继续有效**：知识点前缀 `sc.*` / `esd.*`、课程目录 `content/esd`、
   章节 `esd-*` 等内容层短名解耦保留，不再改。
4. **名字规则的表述随之校准**：id 用完整的英文单词（`software`、`embedded`、
   `machine`），不用首字母缩写、不用拼音；既有连字符名（`math-tools`）不强制
   拆改，新增应用按单词取。

## 后果

- 启动器、思维导图条目与进程名变为单词形式；两应用 Cargo 增量缓存再重编一次。
- 根 `AGENTS.md` 名字规则、`docs/REPOSITORY.md`、根 `README.md` 同步；
  0097 状态栏补注记（名字由本条更新，原文不改）。
