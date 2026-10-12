# ADR 0007：正文快照复刻官方构建期的示例代码注入

- 日期：2026-10-12
- 状态：已接受
- 延续：应用 ADR 0002（官方教程全量翻译是内容基准；代码与代码语句永远原样）、
  0006（exercise/ 官方示例镜像）

## 背景

官网教程的 Example 小节内嵌完整示例源码（「File: buttons.h (For use with
gtkmm 4)」+ 代码框），但 DocBook **源**里没有这些代码——只有一行
`<link>Source Code</link>` 外链。代码是官方构建期由
`docs/tutorial/insert_example_code.py` 注入的：扫描 Source Code 链接段，
把链接指向 `examples/book/` 下的目录内容展开为 File 段 + CDATA 程序清单。

快照管线跟随 DocBook 源（ADR 0002），没有复刻这一步——正文里 Example
处只剩截图，官网有的代码我们没有。以官网最终呈现为呈现基准，这是缺失。

## 决策

`sync_upstream.py` 在提取前复刻官方注入（与上游脚本逐项同口径）：

1. **触发与展开**：同一正则匹配 Source Code 链接段（含 `<!-- Insert … -->`
   点名的额外文件），链接段原样保留；*.h 排序在前、*.cc 在后；.h/.cc 跳过
   开头的版权注释（直到首个 `#\w` 行）；Insert 点名的文件不跳；目录不存在
   时空注入（官方同款行为，如指向 examples 根的 base 链接）。
2. **File 段不带 `<filename>` 标签**：提取后由既有的 strip_meta_labels
   消化为代码块的 `file` 属性（渲染为代码块标题），与官网视觉等价，且不给
   翻译层制造 267 条「File: xxx」假段落——这些行是构建脚手架文本，不在
   官方 PO 里，永远无官方译文可对。
3. **删注释换成 CDATA 感知**：注入必须发生在删注释之前（Insert 注释是
   额外文件的传递通道），而注入的 UI 文件（.ui/.gresource.xml）代码里真有
   XML 注释——删注释时 CDATA 区间原样保留，不碰代码原文（ADR 0002）。
4. **对齐语义不变**：注入块是 code 块（`zh` 恒空、不标待译、不进 PO
   对齐），指纹 = 代码文本指纹。上游 examples 文件变化 → 指纹变 → 走既有
   的 replace 通道（code 块无译文可失效，仅内容更新）；Source Code 链接的
   URL 仍由 strip_meta_labels 挂给节内首个代码块（「完整源码 ↗」）。

## 后果

- 全书 93 处 Source Code 链接展开为 259+ 个文件块（按钮章 3 个文件、
  buildapp 章含全部 .ui 等），正文与官网最终呈现对齐；「官方示例」卡
  （ADR 0006）与正文内嵌代码自此同源同版本（exercise/ 与注入同出于
  upstream 钉点）。
- 快照 diff 一次性膨胀（+367 段），全部是注入代码块：既有段指纹不变，
  1969 段译文零损失（实测）。
- sync_upstream 从此依赖 upstream 克隆里的 examples/ 目录（本就依赖
  克隆，无新增前提）；examples 变化会以代码块更新的形态出现在同步 diff 里，
  纳入既有「同步上游」流程，无新流程。
