# 0016 归档 2020 年的旧作文站

- 状态：已采纳
- 日期：2026-09-30
- 决策人：tiger

## 背景

仓库里原有一个 2020 年的 VuePress 英语作文站（`docs/`、`package.json`、`yarn.lock`、Travis 和 GitHub Actions 部署脚本）。tiger 决定把现有代码归档，不体现在全新的软件设计中。

## 决策

- 旧站点的全部文件原样移到 `archive/vuepress-2020/`，保留 git 历史。
- 部署脚本一起移进归档目录，不再在仓库根目录触发构建。
- 新软件不引用、不迁移旧站的代码和范文；此前计划把旧范文放进 `content/archive/` 的做法取消。
- gh-pages 分支上已发布的旧站点不动。

## 后果

- 仓库根目录留给新软件。
- 以后如需恢复旧站，从 `archive/vuepress-2020/` 移回即可。
