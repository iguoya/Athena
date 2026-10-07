# 结构规范化提案（未拍板，不实施）

> 本文是 2026-10-08 发版 v9.0.0 时对仓库做的一次全量结构侦查的**提案清单**。
> 状态：等使用者拍板。任何一条要落地，先按 [AGENTS.md](../AGENTS.md) 的规矩立 ADR
> （影响仓库结构或多个应用的放仓库级 `docs/decisions/`），再动代码；涉及目录改名或
> 归档内容的，实施前先打基线提交。

## 背景

v9.0.0 周期仓库从 8 个目录涨到 14 个应用（subjects 11 + practice 3），发版矩阵
从 2 个应用扩到 6 个。这次侦查（CI 覆盖、文档同步、根目录杂物、应用一致性矩阵、
规模分布）发现的问题里，能直接修的已随手修掉，剩下的是**需要拍板的结构性决定**。

## 已直接修复（本次发版窗口，均已提交）

- `docs/REPOSITORY.md` 与实际同步：结构树补 `gtkmm/`、`nas_admin/`、`c-gui-lab/`，
  `c/` 改 `machine/`，北极星技术栈随 ADR 0015 更新；名字表补 `math-tools`、`gtkmm`，
  拾阶进程名如实写 `lumi`。
- 根 `README.md` 应用表从 6 个补全到 14 个，注明分类判据出处。
- ADR 索引补上缺失的 0082 / 0087 / 0088，0081 行补记发布矩阵扩容。
- `gtkmm`、`mathematics` 补此前缺失的 `README.md`；`archive/computer/README.md`
  从 0 字节补成一段说明。
- 根目录清理：`__pycache__/`（源文件从未入库的孤儿 .pyc）、空目录 `dist-driver/`。
- CI 覆盖缺口（六个应用无任何 CI job）：由并行会话在 `fe30cf7` 补齐，含 pnpm 分支。

## 提案（等拍板）

### P1 目录名与 id 的连字符统一

`practice/nas_admin` → id `nas-admin`、`practice/pocket_cube` → id `pocket-cube`，
目录用下划线、id 用连字符，两套写法并存。目录名是 Python 模块/包名不友好历史造成的
（`nas_admin` 里有 Flask 工程），但仓库内引用（文档、CI 缓存 key、脚本）已经各自
写死。**选项**：a) 维持现状，在 REPOSITORY.md 名字表加一句「目录名允许下划线历史
遗留，id 一律连字符」把例外写明；b) 一次性改名目录并对齐全部引用。
**建议 a**，成本最低，把例外写进文档就不再是「不一致」。

### P2 ascent 的 ADR 位置

`subjects/ascent/adr/`（21 篇，自成体系）是全仓唯一不用 `docs/decisions/` 的应用。
它是并入的外来应用（ADR 0066），历史编号独立。**选项**：a) 迁入 `docs/decisions/`
并改写全部内部交叉引用（工作量大，收益是结构一致）；b) 保留现状，在 `adr/README`
写明「本目录是并入时带来的历史档，编号独立，不改号」。
**建议 b**——ADR 0066 的原则本来就是「两个英语应用各自独立发展，不趋同」。

### P3 拾阶的 Lumi 命名

binary/productName 是 `lumi` / `Lumi`，不在 `athena-<id>` 约定内，且
`src-tauri` 的更新通道（ascent-updates tag、latest.json）、NSIS 产物名
（`Lumi_*.exe`）全部绑定此名。**选项**：a) 维持品牌现状（文档已如实记录）；
b) 大版本时一次性切回 `athena-ascent` 并同步更新器地址（需要停机窗口与版本
协商）。**建议 a**，品牌名是产品决定，不是仓库规范问题；名字表已写明例外。

### P4 driver 迁移前的本地残留进度库

`subjects/driver/progress/learning.db`（495KB）与 `progress/points/` 在磁盘上
仍未删（ADR 0067/0070 之后客户端不再有 learning.db，`.gitignore` 挡住了误提交）。
这是迁 PG 前的最后一个本地快照。**选项**：a) 确认中心 PG 数据完整后本地删除；
b) 移入 `archive/`；c) 留着。**需要拍板**——数据处置不擅自动手。

### P5 ascent 根目录的中文启动脚本

`subjects/ascent/启动 Lumi（开发版）.cmd` 是唯一被跟踪的、绕过 launcher 的启动
入口，与 ADR 0046「应用只声明怎么启动」的精神相悖。**建议**：删除（它的全部功能
就是 `app.json` 的 `dev` 块已有的内容），或至少改名为 ASCII 并注明仅作过渡。

### P6 仓库级 ADR 编号缺失段的出处说明

`docs/decisions/` 实存 0007 起跳号，README 只有一句「两边都有跳号」；0001–0006、
0008–0027、0033–0036、0038–0039 的去向（散在各应用、随旧仓库流失、还是作废）
没有任何说明。**建议**：在索引头部补两行，写明这些编号的归属或「已不可考」，
免得后人误以为文件丢了。

### P7 归档双轨制的边界

全局 `archive/`（前身仓库整体归档）与 `subjects/ascent/archive/`（应用内历史档）
并存。现行判断其实一致——「不参与构建的历史都进自己最近的归档位」——只是没有写
下来。**建议**：在 REPOSITORY.md 或本文转正时补一句规则，不强制迁移。
