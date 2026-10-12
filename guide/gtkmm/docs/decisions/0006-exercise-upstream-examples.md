# ADR 0006：exercise/ 原样导入官方示例代码，壳内编译运行

- 日期：2026-10-12
- 状态：已接受
- 延续：应用 ADR 0001（演示/实验机制与清单）、0002（代码与代码语句永远原样）；
  主仓库 ADR 0059（骨架实验：不改一行也能编译运行）

## 背景

教程正文的 Example 小节链接官方仓库的示例代码（`examples/book/`，与正文同
仓库发布），学习者只能看网页或自己搭工程。按钮章（第 6 章）正文链接了
button、checkbutton、radiobutton 三个示例，官方 `examples/book/buttons/`
目录另有 togglebutton、scalebutton 两个同章示例。

这些代码官方仓库本来就有，不需要也不应该由本应用重写（ADR 0002 的原样
纪律对整份示例文件同样成立）；需要的是：进仓库、能编译、能从课程壳里
一键运行。demos/ 的演示工程做不了这件事——演示必须说 JSON-RPC 协议、
必须支持 `--self-check`（ADR 0001），而官方示例一个字都不能改。

## 决策

1. **`exercise/<官方示例集目录>/<示例名>/` 原样导入**：从 upstream 克隆
   （upstream.json 钉住的 commit）按官方目录结构复制，代码、注释、许可头
   一个字不改；来源与许可（GPL-2.0-or-later，文件头自带）随文件保留。
   示例集目录名 = 官方 `examples/book/` 下的目录名（首批 `buttons/`，5 个
   示例全收——目录即官方对该章示例集的划界，不自行取舍）。
   后续章节按同法扩目录；同步上游时以 git diff 整目录对照官方对应版本。

2. **构建脚本是我们提供的**（官方只有 meson 总构建）：`exercise/CMakeLists.txt`
   集中声明，每示例一个 target（gtkmm-4.0、C++17，与 demos 同档）；
   构建脚本一律不进官方目录，`exercise/<示例集>/<示例>/` 保持 100% 镜像，
   与上游对照用 `git diff --no-index` 整目录即得。产物统一落
   `build-exercise/`，target 名 = 清单 id 的 `.` 换 `-`。与 demos 的 `build-native/` 分开：演示带协议、
   自检归 check.py 管；示例是外部原样代码，编译通过即验证目标，运行是
   弹独立窗口。二者互不占用产物名空间，删一个不影响另一个。

3. **清单是唯一事实源**：`content/demos.json` 新增 `"examples"` 数组
   （id 前缀 `example.*`），实体带 `page_ref` 锚定教程节——正文有
   Source Code 链接的按链接锚定；官方目录有而正文未单独链接的
   （togglebutton）按同名小节锚定；正文完全没提的（scalebutton）不设
   `page_ref`，作为章级示例显示在本章每节尾部，`note` 写明来历。

4. **壳负责编译并运行**：`launch_example` command 对示例工程做增量
   configure + build（首次慢、之后秒级），产物以示例源目录为工作目录
   spawn（button 示例从工作目录读 `info.xpm`；Windows 下 PATH 前置
   MSYS2 mingw64 的 bin，与 check.py 的探测同源）。官方代码没有协议，
   壳只管拉起，不做 JSON-RPC 转发、不进程托管；`read_example_sources`
   command 返回示例源文件文本，供页内查看源码。

5. **入口在教程节页**：翻译正文之后、随堂测验之前渲染「官方示例」区块
   （清单驱动：锚定当前节 + 章级示例），每张卡有「编译并运行」与源码
   展开；不为某章手写页面（主仓库 ADR 0058）。演示–模拟配对与骨架实验
   机制（ADR 0001、主仓库 ADR 0059）不适用于官方示例，二者并存不互替。

6. **check.py 的验证强度**：examples 实体校验字段齐全性 + `exercise`
   工程全量编译 + 产物存在；不跑 `--self-check`（不能改官方代码加自检，
   headless 环境也不弹窗验证）。

## 后果

- 学习者在正文读完就能跑到官方原样代码，「预测–运行」的运行一端多了
  官方锚点；示例源码即教材，页内可读，不用出应用。
- exercise/ 是上游代码的镜像，禁止就地修改——发现要改的地方属于上游，
  走上游贡献；本应用的教学改造（加协议、拆 TODO）只发生在 demos/。
- 示例与 demos 的观察对象可能重叠（如 button 示例与 demo.buttons 都是
  三种按钮）：演示卡讲「信号时序模型」，示例卡给「官方完整写法」，
  卡面 purpose 已写明分工。
- 同步上游版本时 exercise/ 可能因官方改动而需要重新对照（整目录 diff），
  归入既有的「同步上游」流程，`sync_upstream.py` 不处理代码目录。
