# 课程内容

目录和格式见 [ADR 0010](../adr/0010-content-and-data-model.md)，来源和版权规则见 [ADR 0019](../adr/0019-open-content-sources.md)。每条内容都要能对应到 [sources.json](sources.json) 里的一个来源。

| 文件                           | 内容                                        | 怎么生成               |
| ------------------------------ | ------------------------------------------- | ---------------------- |
| `sources.json`                 | 来源登记：授权、署名、能不能打包            | 手写                   |
| `grammar.json`                 | 第一章句式单元与语法点清单（知识地图）      | 手写                   |
| `vocab/hs/words.json`          | 单词关词表草稿（ECDICT 高考词，约 3700 个） | `pnpm content:ecdict`  |
| `sentences/tatoeba.json`       | Tatoeba 真实句子和中文译文                  | `pnpm content:tatoeba` |
| `vocab/hs/sentence-index.json` | 每个词的候选例句编号                        | `pnpm content:tatoeba` |
| `vocab/hs/todo.json`           | 真实例句不足 3 条、先不入库的词             | `pnpm content:tatoeba` |
| `private/`                     | 真题、课本等只在本机用的资料（git 忽略）    | 手动放                 |

生成的 JSON 每条一行，方便在 git 里看改动。`words.json` 里的 `cnDraft`、`enRef` 都是草稿和参考：中文释义要精简，简单英文释义由 AI 起草、tiger 审核，例句只从句子库来。
