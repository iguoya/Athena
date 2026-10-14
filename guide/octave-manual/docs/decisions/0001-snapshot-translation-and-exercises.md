# ADR 0001：Texinfo 段落快照 + 逐段译文 + 自编「试一试」

- 日期：2026-10-14
- 状态：已接受
- 依赖：主仓库 ADR 0163（选源）、0043/0089（出处，open 档）、0052（掌握度只由作答写入）、0155（进度同步）

## 决策

1. **快照是中间层**：`sync_upstream.py` 把上游 Texinfo 解析成块流（段落、列表、定义列表、表格、提示框、展示公式、代码块、函数说明卡片），
   每个可译单元带 `en`（Texinfo 行内命令规整成 `$公式$`、`` `代码` ``、`*斜体*`、`**粗体**`）、`sha`、`zh`（手写）。
2. **函数说明用本机 Octave 展开**：`@DOCSTRING(名字)` 的正文在源码注释里，同步时用同版本 Octave 的 `get_help_text` 取出，
   与手册正文一起解析。函数签名（`@deftypefn`）与 `@example` 块逐字保留，不译。
3. **只收列出的函数**：`scope.json` 每页给 `sections` 与 `functions`；函数列表里有而手册节里没有的，同步直接报错，免得名单悄悄失效。
4. **练习自编**：手册没有习题；`content/exercises/<页>.json` 手写，答案由 `verify` 里的 Octave 代码用真 Octave 复算，标 `authored`。
5. **掌握度**只由核对点作答写入；不做自评。
6. 译文不得改公式与行内代码（导入时校验）。

## 后果

- 同步（不是使用）需要装有钉点同版本的 Octave。
- 手册里对被裁掉章节的交叉引用会成为悬空文字，照译不补。
- 手册里的图（`@float` 与 `@image`）收成 `figure` 块，只收 `scope.json` 里 `figures`（基础）与 `figures_more`（进阶）列出的；
  SVG 由 `scripts/render_figures.py` 生成：数据由真 Octave 算，图形由 matplotlib 重绘（云环境 Octave 无显示、图形后端创建坐标轴就失败）。
  有图形能力的机器上应改用 Octave 原生渲染覆盖同名文件，见仓库 `docs/HANDOFF.md`。
7. **厚度分档**（主仓库 ADR 0164）：`scope.json` 每页的 `functions` 是基础、`functions_more` 是进阶，快照里进阶的函数卡片与图带 `stage: 2`，
   界面默认折叠。译文与练习不受影响。
