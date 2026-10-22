# 算法领域已核实的事实（leader 逐个编译运行后得出，给 T-004 的 algorithms 部分用）

环境：本机 Windows，gcc/g++ 15.2（MinGW）。以下“实测”都是我在临时目录里编译运行的结果；批注里用到请保留“实测”二字并只写这里有的事实。

## 22-recursion（递归）
- `fibonacci/main.c`：朴素递归 `fibonacci(i)` 与迭代 `fibonacci_normal` 在同一个 main 里各跑 i=1..40，**总耗时约 1.1 s**；main 没有计时，两种复杂度的差别没有被演示；`int` 在 fib(47) 溢出，上限 40 恰好掩盖了。
- `fibnonacciv2/main.cpp`：目录名拼错（fibnonacci）；递归把结果累积进 `vector`，线性时间，读 `result[size-1]` 与 `result[size-2]`（写得好）；main 里 `for (const auto it : result)` 按值拷贝，有 Hello World 残留。
- `footstep/main.c`：`static int total_method` 等状态跨调用累积——**实测** `step(4)` 打印 1–7 号走法，随后 `step(10)` 的编号接着从 8 开始；`step_queue[20]` 定长，n>20 越界；函数声明 `int` 但末尾没有 return（`-Wreturn-type` 实测）。
- `footstepv2/main.cpp`：`route` 按值传参（每层拷贝），其后的 `push_back/pop_back` 配对因此多余；`result` 用引用收集（对）；空的 else 分支。
- `hanoi/main.c`：第 20 行的“整体结束”打印写在 `if(n)` 外面，n=0 也会打印“移动0（含）编号以上盘子整体结束”；**实测** n=2 时计划文字写“从A通过B移动到C”，下一行实际移动打印的却是“将编号1圆盘从A移动到B”——日志里的起点/经由/终点标签和真实移动不一致；没有计数 2^n−1。
- `integer_factorization/main.c`：同样用 static 状态；它枚举的是**有序的组合**（1+2 与 2+1 算两种，n=10 共 2^9=512 种），不是整数分拆（p(10)=42），名字与行为不符。
- `numeral_system/main.c`：`number_representation` 返回的是**最高位的下标**，main 只打印这三个下标，**实测输出 `6, 2, 3`**，数字本身从未被打印；隐藏的 static `index`；有一条路径没有 return（`-Wreturn-type`）；`dec_to_bin` 的调用全被注释掉。
- `average_value/main.cpp`：文件叫平均值，实际是 `summation`/`factorial`，没有平均；`list::erase(it)` 循环里 `auto tmp = it; ++it; sample.erase(it);`（第 45–47 行）擦掉的是“下一个”而不是 tmp，`it` 随后失效，且 `i != sample.size()` 的上界在变——**实测以 0xC0000374（堆损坏）退出**；`summation(0)` 因为只处理 n==1 而无限递归。
- `max_value/main.cpp`：函数会 `pop_back` 掉调用者的 vector（破坏输入）；变量 `min` 实际存的是候选最大值，名字误导；`<vector>` 靠 `<random>` 间接带入。
- `permutation/main.cpp`：`se_sample.remove(*it)` 会删掉**所有**等值元素——**实测**对 `{1,2,1}` 得到的“排列”只有 2 个元素；每层按值拷贝 list 并 remove 是 O(n) 的。无重复元素时是对的。
- `queen/main.c`（递归目录里的第一版）：`queen(int n)` 完全不用 n，只打印一个 4×4 的全 0 棋盘（**实测**），`check()` 恒返回 true，前 50 行是被注释掉的第一次尝试（还 `#include "../stack/stack.h"`）——一个烂尾的墓碑文件。

## 23-divide_and_conconquer（分治）
- `binary_search/main.cpp`：main 里 `binary_search(sample, x, 0, sample.size())`，而函数把 `end` 当**闭区间**，所以会访问 `sample[size()]`——**实测**前两次查找打印 45、72，第三次（查 9999，大于所有元素）触发 `vector::operator[]` 断言 `__n < this->size()`，进程以 **exit code 3** 中止；函数名与 `std::binary_search` 同名（`using namespace std` + `<algorithm>`）。
- `merge_sort/main.cpp`：**名不副实，没有任何排序**。只是生成 100 个随机数并打印；第 14 行的 `for_each` 在填充之前就打印，所以**实测先输出 100 个 0**，然后才是随机数；还有一行 `//dddddddd`。
- `gold/main.cpp`：模板函数里写死 `int max1, min1, max2, min2`，T 不是 int 时（如 double）在 `tie(max1, min1) = find_max_min_gold(...)` 处被静默截断；`vector<T>` 按值传入并为两半各建新 vector，拷贝是 O(n log n)；两元素的基本情形一次比较（对）；`time(NULL)` 没有 `<ctime>`；没有拿 `std::minmax_element` 校验。
- `queen/main.cpp`：目录叫“分治”，做法是**生成全部 8!=40320 个排列再在叶子上检验**，没有剪枝（不是回溯）；`check_points` 每个候选都打印（**实测输出约 4 万行、0.7 s**），`map` 按值传参；对角线判定用行偏移，是对的，**实测共 92 种解，与已知的 8 皇后解数一致**。
- `backtracking/substring/main.cpp`：只有 Hello World，不收。

## 1-速学速用大辞典
- `iterative/`：**实测**输出把最小公倍数标成“最小公约数”（`common_multiple_divisor` 里的文字，100 和 20 得 100）；`factorization` 输出末尾多一个 `*`（`100 = 2*2*5*5*`），`factorization(0)` 会死循环，main 里重复调了两次 54；`x*y/dividend` 会溢出；头文件里用 `printf`/`fabs` 却不自己 include（靠 main.c 先包含）；`my_sqrt` 是 void、只打印不返回。
- `enum/main.c`：`char result[3]` 填满三个字符，没有结尾 `'\0'`，随后 `%s`/`atoi(result)` 读越界；`while(1)` + 不检查 `scanf`：**实测**输入结束后程序死循环（5 秒超时）。
- `backtrack/main.c`：号称“1–n 取 r 个数的所有组合”，**实测只输出 36 行，而 C(10,3)=120**：前 r−1 个元素被强制成连续的 `data[i..i+r-2]`，只有最后一个元素在变；代码也并不是回溯（没有递归），r 虽是变量但逻辑只对 r=3 成立。
- `sort/`：`#include "../list/list.h"` 指向不存在的目录（list 在 `11-linner/2-list`），无法编译；所谓 `bubble_sort` 是拿 `unsort[i]` 与后面每个 `unsort[j]` 比较交换（交换排序/选择式），不是冒泡；原地修改输入并每轮打印。
- `c_string/main.c`：用了 `atol` 却没有 `<stdlib.h>`（gcc 15 里隐式声明是**错误**）、`%d` 配 `long`、`fflush(stdin)`、`p_str = str`（`char(*)[11]` 赋给 `char**`）。
- `backpack/main.c`：不是背包，只打印一个 5×5 数组的各元素地址，且 `#include "../stack/stack.h"` 路径不存在；不收。

## 不收
- `algorithm/docs`（算法笔记约 8 KB，大半是标题与 mermaid 流程图）、`markdown/`、`vuepress/`、`5-LineChart.md`（前端文档工具练习）。
- `Linux/Algorithm/qdarkstyle`（481 个文件，QDarkStyleSheet 官方库整套拷贝）。

## 21-basic（C 基础）归属
我裁决归 `programming/linux`（C 编程与单元测试）。因为 `programming/linux/content/archive.json` 已有我写的 7 条，**你不要直接改它**：21-basic 的条目请按 AUTHORING.md 做成暂存包 `comms/legacy-archive/artifacts/zcode/staging/linux-c-basic/content/{archive.json,cases/arc_linux_cbasic_*,archive-dropped.md}`（id 前缀 `linux.arc.`，requires 一律 []），我来合并。
