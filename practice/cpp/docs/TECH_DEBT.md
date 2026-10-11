# 技术欠账

记录**已知不符合当前规则、但不集中改的存量**：改到哪个文件顺手还一笔，不照抄扩大。
规则本身在 `AGENTS.md` 与 `docs/ENGINEERING_RULES.md`；这里只放具体文件清单——
文件清单写在规则里迟早过时（ADR 0059），放在这里核对和更新都更方便。

清单最后核对日期：2026-09-26。

## 纯代码构建的视图（应往 `.blp` 收）

规则见 `AGENTS.md`「GTK 与 Blueprint 规则」：界面布局默认用 `.blp`，只有三种情况允许
用代码构建。下列文件是在这条规则之前写的：

- `render/chart_view`、`render/knowledge_graph_view`——外壳和图例可进 `.blp`，Cairo 自绘的
  图形区（第 3 条）留代码；
- `ui/chapter_index_page`——页面骨架 + 卡片可做成 `.blp` 模板；
- `ui/settings_dialog`、`ui/about_dialog`、`ui/ai_markdown_dialog`——对话框结构应写在
  `.blp`，代码只填内容和信号。

原清单里另有两项，文件已删除，欠账随之消失：`render/domain_graph_view`（ADR 0058 移除
学科图谱首页）、`ui/progress_page`（学习进度并入学习图谱）。

合规参考：`resources/ui/window.blp`、`resources/ui/chapters/*.blp`（章节页 = `.blp`
模板 + `code_chapter_page.cc` 只做协调）。

## 基础设施头文件里的 `using namespace std`

规则见 `AGENTS.md`「C++ 编码规则」（ADR 0059 修订 ADR 0005）：只有 `cplusplus/` 下的教学
代码保留 `using namespace std;`，基础设施头文件不再这样写。

2026-09-26 统计共 47 个头文件：`ui/` 25、`render/` 8、`content/` 4、`registry/` 4、
`services/` 4、`platform/` 1、`storage/` 1。去掉之后，头文件里用到的标准库名字要补
`std::`，依赖它间接引入的 `.cc` 要自己写 `using namespace std;`。查找：

```sh
git grep -l 'using namespace std' -- '*.h' '*.hpp' | grep -v -E '^cplusplus/|generated'
```
