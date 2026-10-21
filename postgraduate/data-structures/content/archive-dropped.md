# 历史归档：未收录的条目（postgraduate/data-structures）

来源是旧 GitHub 仓库 `algorithm`、`Practice`、`Linux`（ADR 0176）。以下内容**没有**进应用的「历史归档」章节；旧仓库只会被设为 archived，历史完整保留，需要时从那里取回。清单与去重证据见 `comms/legacy-archive/artifacts/zcode/`（manifest-data-structures、dedup2-report）。

| 旧路径 | 处置 | 原因 |
|---|---|---|
| `algorithm/DataStructure/sort`（镜像同下） | 不收 | `sort.h` 全文只有包含守卫两行，`test_sort.cpp` 是 0 字节空文件，`main.cpp` 只打印 Hello World；写不出 3 条实质批注。排序类练习见 algorithms 应用的历史归档 |
| `algorithm/DataStructure/recursion` | 不收 | C++ 版递归计划没有落地（`main.cpp` 只有 Hello World），真正的递归练习在 `algorithm/22-recursion`，归 algorithms 应用 |
| `algorithm/docs` 里的数据结构笔记（总纲、线性表、树、排序算法 4 个目录共 9 篇） | 不收 | 提纲式笔记，全部加起来约 5 KB，大半是标题与 mermaid 流程图，没有可批注的实质；归档后仍可在旧仓库取回 |
| `Practice/DataStructure`（34 个文件）、`Linux/Algorithm/DataStructure`（59 个文件） | 重复 | 与 `algorithm/DataStructure`、`algorithm/11-linner`、`algorithm/12-tree` 逐文件内容哈希一致，三处镜像只收规范版 |
| `algorithm/11-linner/**/CMakeLists.txt.user`、`algorithm/DataStructure/**/.gitignore` 等 | 不收 | IDE 本机配置 |

`DataStructure/linear` 里的 `test_*.cpp`（GoogleTest 用例）随案例目录原样保留在 `arc_ds_cpp_linear`，不单独批注：本机没有 GoogleTest，无法验证它们。
