# ADR 0154：文档站用 MkDocs Material 发布到 GitHub Pages

- 日期：2026-10-13
- 状态：已接受（使用者 2026-10-13：「做 Pages 文档站」，并要求弄清它与 wiki 的关系）
- 关系：与 ADR 0064（CI 显式触发）有一处有意例外，见决策 4；不改变 ADR 0061（规则单一来源）

## 背景

1. 仓库已有 120 多篇 ADR 和五份工程规范，读起来只能在 GitHub 的文件视图里点，没有
   搜索、没有导航、没有统一样式。
2. GitHub Wiki 是独立的 git 仓库，内容要另写一份，不跟提交和检查走，必然漂移，
   也与「同一组东西不写两遍」冲突，已关闭。
3. 文档里有大量裸的 `<id>` 之类尖括号，VitePress 会把它当 Vue 标签解析并报错；
   MkDocs 的 Python-Markdown 宽松得多。

## 决策

1. 站点**没有自己的内容**：源是 `docs/` 加根目录的 `README.md`、`AGENTS.md`、
   `CHANGELOG.md`，渲染结果即这几份文件的样子。不在站点上手写任何页面。
2. 生成器用 MkDocs Material，配置在 `scripts/docs-site/`，暂存与构建由
   `scripts/docs_site.py` 完成（暂存到 `.cache/docs-site`，不进版本库）。暂存时把指向
   应用目录、源码的相对链接改写成 GitHub 地址，把文字里的裸尖括号转义。
3. 依赖钉死精确版本（`scripts/docs-site/requirements.txt`），mkdocs 钉在 1.x。
4. 发布走 `.github/workflows/pages.yml`：文档相关路径推送到 `main` 或手动触发。
   这是 ADR 0064 的有意例外——它只读文档、一分钟内跑完、不开矩阵，路径过滤保证改代码
   不触发；而「文档一改站点就变」正是它防漂移的方式。
5. 构建时不开严格模式。文档里已有的坏链接（指向已不存在的 `subjects/`、`apps/`
   旧路径和几处错写的 ADR 文件名）只给警告，由内容侧另行修复，不在站点层掩盖。

## 后果

- 站点地址 `https://iguoya.github.io/Athena/`；仓库 Settings → Pages 的来源选
  GitHub Actions。
- 各应用自己的 `AGENTS.md` 与 `docs/` 暂未纳入，第一版只收仓库级文档；要纳入时在
  `scripts/docs_site.py` 的 `INCLUDE_*` 加路径。
- 本地预览：`python3 scripts/docs_site.py --serve`。
