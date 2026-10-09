# 课程内容

目录和格式见 [ADR 0010](../adr/0010-content-and-data-model.md)，来源和版权规则见 [ADR 0019](../adr/0019-open-content-sources.md)。每条内容都要能对应到 [sources.json](sources.json) 里的一个来源。

| 文件                           | 内容                                                             | 怎么生成                         |
| ------------------------------ | ---------------------------------------------------------------- | -------------------------------- |
| `sources.json`                 | 来源登记：授权、署名、能不能打包                                 | 手写                             |
| `grammar.json`                 | 第一章句式单元与语法点清单（知识地图）                           | 手写                             |
| `vocab/hs/words.json`          | 高中词库：单词关词表草稿（ECDICT 高考词，3678 个）               | `pnpm content:ecdict`            |
| `vocab/cet4/words.json`        | 四级词库：比高中多出来的四级词（1654 个）                        | `pnpm content:ecdict`            |
| `vocab/cet6/words.json`        | 六级词库：比高中和四级多出来的六级词（1755 个）                  | `pnpm content:ecdict`            |
| `vocab/*/stages.json`          | 词库分阶：先易后难的子阶段（高中 8 阶、四六级各 4 阶，ADR 0022） | `pnpm content:stages`            |
| `sentences/tatoeba.json`       | Tatoeba 真实句子和中文译文                                       | `pnpm content:tatoeba`           |
| `vocab/hs/sentence-index.json` | 每个词的候选例句编号                                             | `pnpm content:tatoeba`           |
| `vocab/hs/todo.json`           | 真实例句不足 3 条、先不入库的词                                  | `pnpm content:tatoeba`           |
| `vocab/*/exam-frequency.json`  | 每个词在四级真题里出现的次数（只有数字）                         | `pnpm content:cet4`              |
| `private/exam/cet4.json`       | 四级真题句子（本机，git 忽略）                                   | `pnpm content:cet4`              |
| `private/textbook/`            | 教材资料（本机，git 忽略），见下面「教材导入」                   | 手动放 + `pnpm content:textbook` |
| `private/`                     | 真题、课本等只在本机用的资料（git 忽略）                         | 手动放                           |

## 教材导入（ADR 0022）

教材（大学英语、高中英语）的课文和单元词表只在本机使用：把文件放进
`content/private/textbook/<教材名>/`，再跑 `pnpm content:textbook`，解析结果写在同一目录的
`parsed.json`，永远不进 git、不进安装包。目前支持：

- `words.txt`：单元生词表，每行一个词（`word`、`word<TAB>音标`、`word<TAB>音标<TAB>释义`
  或 `word<TAB>释义`，`#` 开头是注释）。
- 课文和音频的解析在后面的里程碑接入，格式会在这里更新。

分阶数据（`stages.json`）是 `pnpm content:stages` 的产物：按 ECDICT 真实语料词频、Collins
星级、Oxford 3000 和四级真题词频排序（公式见 ADR 0022），不手改。

每条内容的 `source` 字段对应 `sources.json` 里的来源，`pnpm content:check` 会检查。生成的 JSON 每条一行，方便在 git 里看改动。`words.json` 里的 `cnDraft`、`enRef` 都是草稿和参考：中文释义要精简，简单英文释义由 AI 起草、tiger 审核，例句只从句子库来。
