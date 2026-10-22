# 算法领域清单摘要（T-002 · algo）

范围：`algorithm/`（22-recursion、23-divide_and_conconquer、backtracking、1-速学速用大辞典、21-basic、
DataStructure/recursion、docs 算法部分、markdown/vuepress 等杂项）、`Linux/Algorithm/`（Qt 演示台、任务类库、
qdarkstyle、镜像目录）。清单 [manifest-algorithms.json](manifest-algorithms.json)；
去重 [dedup2-report.txt](dedup2-report.txt)；编译 [build2-log.txt](build2-log.txt)；
零遗漏（两清单合并 931 文件、931/931 覆盖、退出码 0）见 [verify-algorithms.txt](verify-algorithms.txt)。

## 统计

单元 11（keep 8、drop 3：duplicate 1 + third-party 1 + junk 1）；keep 负责文件 169，drop 606（qdarkstyle 481 占大头）。

## 哈希去重与 qdarkstyle 判定

- `Linux/Algorithm` 的 {21-basic, 22-recursion, 23-divide, Backtrack, 1-速学速用大辞典} 与 algorithm 仓库
  逐文件一致（Backtrack ↔ backtracking 同内容异名），2023-02 拷入做 Qt 壳素材库 → drop-duplicate，规范版取 algorithm。
- **qdarkstyle（481 文件）= QDarkStyleSheet 官方库整套 vendored 拷贝**：`__init__.py` 文件头即官方自述
  （"The most complete dark/light style sheet for Qt applications (Qt4, Qt5, PySide…)"，指向
  qdarkstylesheet.readthedocs.io，上游 ColinDuquesnoy/QDarkStyleSheet），含 palette.py/qss/svg/example 完整包。
  演示台 main.cpp 从 qrc 加载其 darkstyle.qss——是暗色皮肤依赖。→ drop-third-party 不入库，批注记上游即可。

## 编译实测（44 目标：36 过、8 败、2 等输入）

亮点（详见 build2-log.txt）：
- **递归十题 10/10 编译过**；average_value 运行堆损坏（0xC0000374 越界写）——「编译过≠对」的活教材；
  hanoi 输出中文步骤、queen 输出棋盘解、fibonacci 输出数列，演示完成度高。
- **分治四题 4/4 过**；binary_search 运行退出码 3；gold 模板里 `int max1` 硬编码接 `tuple<T,T>`（double 窄化）。
- 大辞典六题 3 过 2 等输入 3 败（`../stack/stack.h`、`../list/list.h` 跨目录路径断×2；c_string 在 gcc 15 下
  隐式声明 atol 与 char** 不兼容为 error——2018 年旧编译器只警告）。
- 21-basic 11 目标 8 过 1 等 2 败：check 与 magic_square 的单测版依赖 **GNU Check** 框架（Linux 系统库，Windows 无）。
- Qt 演示台 toolchain（Qt5+qdarkstyle），未实测。

## topic_hint 核对（postgraduate/algorithms 现有章节）

现行只有四章：algo.complexity.measure / algo.paradigm.divide / algo.paradigm.dp / algo.paradigm.backtrack。
旧练习映射：23-divide→divide ✓；backtracking（笔记有、代码烂尾）→backtrack；大辞典 backpack→dp 引子；
1-算法常识笔记→measure。**递归无专章**——22-recursion 十题与笔记「减治法」是「新增·递归」的现成素材，
另「减治 vs 分治」是现行课程没有的分类视角。

## 笔记与杂项

- docs 算法笔记 7 章（常识/减治/分治/贪婪/回溯/枚举/动态规划）：提纲式，与代码单元一一配套（金块/赛程/子串互指）；
  「4-贪婪法」目录里错放着归并排序（属分治）。
- markdown/（vuepress 写作教程 10 篇）、vuepress/（Vue 语法笔记）、5-LineChart.md（chart.js 片段）
  是前端文档工具练习 → junk。
- function_pointer/ 提交了 clang -emit-llvm 的 main.ll 与 .bc/.s（学函数指针的编译器视角）——随单元保留，
  搬运时可给 machine（汇编）交叉引用。

## 待裁决（已按保守口径填，请 leader 定夺）

1. **21-basic 归属**：内容是 C 语言机制（函数指针/结构体/文件/GNU Check 单测）+数学小题（哥德巴赫/圆周率/幻方）。
   我按 ADR 0176 对照表填 `programming/linux`（C 编程、单元测试）；若认为数学题该留算法侧，可拆或整体改
   `postgraduate/algorithms` 的「新增·基础练习」。
2. **Qt 演示台归属**：内容是算法任务调度演示（Task 抽象+五类算法），技术栈是 Qt Widgets。我按内容填
   `postgraduate/algorithms`（archive 层）；按对照表「Qt Widgets → programming/qt」也成立。与 T-001 的
   qt-shell 同属一类裁决，建议一并定。
3. **algo-arch-cpp-recursion 是否并入 22-recursion**：DataStructure/recursion 是空壳（Hello World），
   可单独条目（批注「C++ 版计划未落地」）或并入递归专题条目当对照，倾向前者但由 leader 定。

## 产物清单

- `manifest-data-structures.json/.md`、`manifest-algorithms.json/.md`
- `dedup2.py` / `dedup2-report.txt`（902 文件→680 唯一、148 多份簇）
- `build-test2.py` / `build2-log.txt`（44 目标实测）
- `verify2.py` / `verify-data-structures.txt` / `verify-algorithms.txt`（931/931 零遗漏，退出码 0）
