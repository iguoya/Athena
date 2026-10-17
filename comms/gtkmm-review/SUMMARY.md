# gtkmm 前十章审查 · 汇总（leader）

三份原始报告：[claude-code（教学设计）](artifacts/claude-code/report.md) ·
[zcode（译文忠实度）](artifacts/zcode/report.md) · [cursor（工程一致性）](artifacts/cursor/report.md)。
leader 已抽样核实 zcode 的 P0/P1、cursor 的 F1，并自跑 `check.py`（全绿）与 exercise↔upstream 整树 diff
（28 个目录仅 `treeview` 少一个 `meson.build`，在前十章之外）。

## 一句话结论

**底座忠于初衷，上层偏离初衷。** 官方全量翻译、段落级上游追踪、66 个官方示例原样可编译，都扎实；
但「理论为主体、实践具象化、预测–运行、完成度反映真实掌握」这条主线在前十章只有第 6 章落地，
译文有若干会误导学习的硬伤，测验的设计让「通过」不代表学会。

## 必须先处理（P0）

| 来源 | 问题 |
|---|---|
| 译文 | `changes-gtkmm4/sec-deprecations-4-10` 块 0 **整句译反**：原文说「这些改动在保持二进制兼容下做不到」，译成「保持了二进制兼容」 |
| 译文 | `sec-text-entry` 块 4（焦点离开/leave 信号被替换为原文没有的断言）、`sec-scrollbar-widgets` 块 0（trough/slider 交互整段被自造概括替换） |
| 测验 | **答案位置偏置**：112 题里 68% 是 B，第 8、9 章全是 B；**80% 的题正确项最长**——不读也能过 |

## 应当尽快处理（P1，择要）

- 译文：`clicked` 译成「按下**或**释放」（应为按下**并**释放）、toggle 页把 clicked 说成 toggled、
  依赖包 `gtk4` 译成 `gtkmm4`、`make_window_and_run()` 残留 gtkmm3 的 `run()`、
  行/列颠倒（`set_text_column`）、装填方向译反、`command_line` 信号句漏译、鼠标键 2/3 注反。
  这些集中在**第 6 章（信号语义）**，与「预测–运行」主原型直接冲突。
- 工具链：`extract_source.py` 的 `strip_tags` 把 `&lt;…&gt;` 当标签吞掉，**全书 31 段英文快照已损坏**
  （`sigc::slot<R(Args...)>`、Pango `<b>` 标签），译文无从忠实。
- 术语：widget 一词四种译法（部件 54 / 控件 26 / 小部件 6 / 组件 1），packing 三种译法同页并存，无统一约定。
- 译文丢外链（「可以从 中下载」式残句）。
- 清单：`example.frame` 的 `translation_ref.chapter=8` 但 `page_ref` 属第 9 章，**界面上永远不显示**
  （全清单仅此一条错位；Frame 在上游 DocBook 属第 9 章，应改章号）。`check.py` 只验 page_ref 存在、不验归属，漏网。
- 教学：测验答错立刻可重试（4 选 1 逐个排除）、全部无解析；知识点被「一章一个 quizset」取代，先修/分级形同虚设；
  题型几乎全是事实回忆；第 7–10 章只有测验 + 官方示例，第 1–3 章连运行锚都没有。

## 更好的开发布局（不动官方章序，ADR 0003）

1. **先修质量，再往后译。** 第 11 章以后复制同样的测验缺陷与译文标准，成本会翻倍。
2. **一次性返修批（按收益排序）**：①修 `strip_tags` 并重跑 sync；②改 P0/P1 误译（约 20 处，都有精确位置）；
   ③定翻译约定（widget=控件等）并全书统一；④修 `example.frame`，给 `check.py` 加「example.page_ref 须属
   translation_ref.chapter」；⑤测验重做（均匀答案位、等长选项、加 `explanation`、读代码预测题≥1/3、
   错后不可立即同题重试）。
3. **演示投入顺序**：第 3 章基础（信号时序、`make_window_and_run` 生命周期）最值得做第一个「预测–运行」
   演示，其次第 9 章布局模拟；第 7–10 章若不做 sim+demo，应在章首明示「运行端 = 官方示例」，别让学习者
   期待与第 6 章同构。
4. **知识点拆分**：quizset 拆成按概念命名、带 `requires` 的知识点，题挂其上，复习调度（ADR 0096）才有依据。
5. **统一状态口径**：写明「translated = para/listitem 全有 zh；heading/figure 不要求（前端本就恒显英文）」，
   让 check 与 AGENTS.md 一致；随后把 misc/container/listmodel 转 translated。
6. **第 4、5 章**加「迁移者读」标记、不进进度分母，位置不动。

## 需要使用者拍板的事

1. 是否批准按上面「一次性返修批」动手（先提交一版原样，符合 ADR 0129 的删改纪律）？
2. 测验重做是否同时覆盖第 11–31 章（本次只看了前十章；偏置统计已覆盖全 31 章，问题是全书性的）？
3. heading/figure 是否要求中文？（决定状态口径怎么写）

## 流程备忘

- cursor 无头会话这次被 Cursor 注入的 Claude `PreToolUse` 钩子（`.claude/settings.json` →
  `block_bulk_git_add.py`，用 PowerShell 语法交给 bash）挡住了所有 shell 命令，只能做静态审查；
  上次测试却没出现，疑似不稳定。如果以后要靠 cursor 跑命令，需先查这条钩子的兼容性。
- 本舱全程只读，未改 `guide/gtkmm/` 任何文件。
