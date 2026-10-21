# 历史归档：未收录的条目（programming/linux）

来源是旧 GitHub 仓库 `Linux`（ADR 0176）。以下内容**没有**进应用的「历史归档」章节；旧仓库只会被设为 archived，历史完整保留，需要时从那里取回。

| 旧路径 | 原因 |
|---|---|
| `Thread/01-ThreadCreate` | 与收录的 `Thread/T01-Create` 是同一练习的早一代（`sleep(5)` 等线程），差异在条目出处里说明 |
| `Thread/02-ThreadJoin` | 同一练习的早一代，**写法是对的**（两个变量分别接返回值）；收录的 `T02-Join` 是“整理”后引入回归的一代，批注里指出了这一点，所以收后者 |
| `Thread/03-ThreadMutex` | 与收录的 `Thread/T03-Mutex/main.c` 逐字节相同，只收一份 |
| `Thread/03-Thread` | 整个文件几乎全是被注释掉的 GTK 线程示例，没有可批注的实质 |
| `Thread/01-Thread` | GTK3 的线程与界面更新示例（`gdk_threads_add_idle`），属于 GTK 内容，归 `practice/c-gui-lab` 一侧的归档处理，不在 Linux 系统编程范围 |
| `CPlusPlus/33-cgi/*.cgi`、`Practice/CGI/*.cgi` | 编译产物（ELF 可执行文件）提交进了仓库，不是源码 |
| `Practice/CGI/*.cpp` | 与 `CPlusPlus/33-cgi` 源码相同 |
| 各目录的 `*.project`、`*.workspace`、`*.user`、`CMakeLists.txt.user`、`.codelite` 等 | IDE 工程与本机配置，无内容价值 |

## 来自旧仓库 `algorithm` 的 `21-basic`（C 语言基础）

「C 语言基础」组的 7 个条目来自 `algorithm/21-basic`，收了该目录下全部 9 个练习（`Goldbach`、`pi`、`callback`、`function_pointer`、`struct`、`volume`、`file`、`magic_square`、`check`）。未收的只有：

| 旧路径 | 原因 |
|---|---|
| `21-basic/function_pointer/main.bc`、`main.bc.s`、`main.ll`、`main.ll.s`、`main.o` | clang 的编译产物（LLVM 位码、汇编、目标文件）提交进了仓库，不是源码 |
| `21-basic/README.md` | 只有一行标题「数据结构和算法相关练习」，没有内容 |
| `Linux/Algorithm/21-basic/` | 与 `algorithm/21-basic/` 逐文件相同的拷贝（2023-02 为做 Qt 演示台素材而拷贝），只收规范版 |
