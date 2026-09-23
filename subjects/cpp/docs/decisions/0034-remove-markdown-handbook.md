# ADR 0034：删除 Markdown 参考手册，大纲只有原生一份

- 日期：2026-09-12
- 状态：已接受；`resources/articles/` 下手册正文、相关配置字段与页面已全部移除
- 取代：ADR 0026（分类手册作为体系化解释的收纳处）中"手册正文统一放在
  `resources/articles/`"的部分
- 收尾：ADR 0033 只把 `type_semantics` 一章的 Markdown 副本删掉，本 ADR 把同一处置
  推广到全部章节，并移除承载它的机制

## 背景

ADR 0024 退出 WebView 之后，学习内容改由 GTK 控件承载，Markdown 被降级为"衍生物"；
ADR 0033 进一步确立大纲也用 `.blp` 控件树表达。但两次决策都保留了 Markdown 手册作为
"体系化解释的收纳处"，于是同一章可以同时存在两份大纲：一份原生、一份 Markdown。

2026-09-12 处理 `type_semantics` 时暴露了第一个问题：**两份内容会漂移**。原生大纲改成
五节范式、补了难度与掌握目标之后，Markdown 副本没有同步，两边表意已经不一致，读者
从不同入口进来看到的是不同的说法。当时的处置是只删这一章的副本。

更要紧的是第二个问题：**旧手册会成为写新大纲时的锚**。给一章写大纲，本该从知识点
本身出发决定教什么、讲到什么边界；但只要目录里躺着一份现成的 `*_overview.md`，实际
发生的是先读它、再在它的框架里增删。这正是 `AGENTS.md` 明令禁止的"从现有实现反向
决定应教授哪些知识"，只不过反推的来源从源码换成了旧文档。用户因此要求把所有 Markdown
参考手册一次性删掉。

## 决策

1. **删除全部 Markdown 手册正文。** `resources/articles/cpp/` 与
   `resources/articles/practice/` 下的 `*.md` 全部移除。`resources/articles/cpp/images/`
   保留——那些 SVG 是原生 `.blp` 页面在引用的，从来不属于 Markdown。
2. **从配置 schema 移除三个字段**：`category.handbook_documents`、
   `chapter.overview_document`、`subchapter.teaches`。三者一律登记为 deprecated，
   生成器遇到就报错，避免以后又悄悄加回来。
3. **删除只为渲染这些文档存在的页面**：`HandbookPage`（手册页）与 `WorkbenchPage`
   （旧式 Markdown 分节工作台，配置早已不启用，失去 `overview_document` 后无法工作）。
4. **章节大纲只有一个来源**：`resources/ui/chapters/<chapter>_lesson.blp` 里的
   「教学大纲」标签，按 ADR 0028 的五节范式组织。写新章节大纲不得先起草 Markdown。
5. **「说明文档」按钮保留本机 AI 退路**（`ui/chapter_overview.h`）。它不是手册，是另一条
   独立能力：按章节上下文唤起 AI 讲解，删手册不牵连它。

## 保留的不是手册

`DocumentView`、`DocModel` 和 MD4C 依赖继续存在，但服务对象只剩
`ui/ai_markdown_dialog`——AI 返回的讲解是运行时产生的 Markdown，仍需要解析和渲染。
把它们误读成"手册路线还在"是本 ADR 之后最可能的误解，故在此写明。

## 后果

- 每一章的大纲从此只有一份，不会再出现两边表意不一致。
- 写新章节大纲时目录里没有可抄的旧稿，只能从知识点重新设计，符合"内容自上而下"的原则。
- 尚未写原生大纲的章节（`Reference`、`RAII`、`PocketCube`）在补齐 `.blp` 大纲之前
  暂时没有大纲页，「说明文档」按钮走 AI 退路。这是明知的空窗，不用 Markdown 填补。
- 体系化解释不再有独立收纳处。它应当直接进入对应章节的原生大纲或教学过程；确实跨章
  的通用内容，等出现第二个实例时再按需求设计承载形式，不预先复活手册。
