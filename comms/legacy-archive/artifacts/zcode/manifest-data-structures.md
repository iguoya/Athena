# 数据结构领域清单摘要（T-002 · ds）

范围：`algorithm/DataStructure/`（C++ 版五目录）、`algorithm/11-linner/`、`algorithm/12-tree/`（C 版）、
`algorithm/docs/` 数据结构部分（10-总纲/11-线性表/13-树/15-排序，从 T-001 转来）、`Practice/DataStructure/`、
`Linux/Algorithm/DataStructure/`。清单 [manifest-data-structures.json](manifest-data-structures.json)；
去重证据 [dedup2-report.txt](dedup2-report.txt)；编译证据 [build2-log.txt](build2-log.txt)；
零遗漏（与算法清单合并 931 文件）见 [verify-data-structures.txt](verify-data-structures.txt)。

## 统计

单元 9（keep 7、drop-duplicate 2）；keep 负责文件 63，drop 93。

## 哈希去重结论

- **C++ 版五目录（linear/search/sort/tree/recursion）三处重复**：`algorithm/DataStructure` ≡
  `Practice/DataStructure`（最早，2020-02-22）≡ `Linux/Algorithm/DataStructure`（2023-02 拷贝），
  逐文件内容哈希一致；规范版取 algorithm 仓库。
- **C 版 11-linner/12-tree 两处重复**：algorithm ≡ Linux/Algorithm/DataStructure/{11-linner,12-tree}。
- 注意：`Linux/Algorithm/DataStructure` 目录混装 C++ 五目录与 C 版两章，drop 单元整体覆盖，无遗漏。
- `DataStructure/README.md`（「# 数据结构与算法设计」导言）三仓同文，归 ds-arch-notes。

## 编译实测（gcc 15.2.0；C++ 用 -std=c++20，C 用 -std=c17）

| 单元 | 结果 |
|---|---|
| ds-arch-cpp-linear | **失败**：linear.cpp 用小写 `linear::`、linear.h 类名是 `Linear`，大小写不一致，从未编译通过 |
| ds-arch-cpp-search / sort / tree | 编译过、main 均为 Hello World（search.h 的递归二分调用了不存在的三参重载 `binary(e, m, n)`，没被调用所以没暴露） |
| ds-arch-c-linear | 1-array/3-stack/4-queue/5-string 过且输出正常（查找前 N 个最大、单链表逆置、舞伴问题）；**2-list 失败**：`init_List` vs `init_list` 大小写笔误 |
| ds-arch-c-tree | **失败**：btree.h `#include "../stack/stack.h"` 跨章相对路径断裂（stack 在 11-linner/3-stack） |

「从未编译通过」的三个目录（linear、2-list、12-tree）是批注的主要素材：大小写敏感、相对路径 include 依赖目录布局。

## topic_hint 核对（postgraduate/data-structures 现有章节）

ds.linear.array / ds.linear.list / ds.linear.stack_queue / ds.hash.table / ds.tree.basics / ds.tree.bst /
ds.tree.heap / ds.sort.basic / ds.sort.advanced / ds.graph.basics / ds.graph.traversal。
旧练习覆盖线性表、栈队列、串、树，**没有图与堆的练习**（现行章节反而更全）；笔记 15-排序算法 里有散列查找一篇，
对应 ds.hash.table。BST 旧练习仅 btree 模板的骨架，无插入查找实现。

## 待裁决

无本领域独有的争议；跨领域的见 [manifest-algorithms.md](manifest-algorithms.md)（21-basic 归属、Qt 演示台归属）。
