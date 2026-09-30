# 0019 开放内容来源和版权规则

- 状态：提议（待 tiger 确认）
- 日期：2026-09-30
- 决策人：tiger

## 背景

tiger 想从 GitHub 和专业英语学习网站找开放资源来填充软件内容。ADR 0005 已经定了只用有出处的真实句子、AI 不生成例句，ADR 0010 定了内容目录。还缺两件事：哪些开放资源可以用，以及版权怎么守。

有两个事实决定了规则：

- 仓库 iguoya/English 是公开的，GitHub Releases 里的安装包也是公开的。放进仓库或安装包，就等于公开发布。
- 真题、课本、词典例句都有版权；GitHub 上常见的“四六级词库”多数是从词典网站抓的中文释义和例句，许可证写着 MIT 或 BSD，但内容本身出处不明。

## 决策

### 来源分四类，登记在 `content/sources.json`

| 类别         | 含义                                                | 例子                                                    |
| ------------ | --------------------------------------------------- | ------------------------------------------------------- |
| `bundle`     | 可以进公开仓库和安装包，按要求署名                  | Tatoeba 句子、ECDICT、WordNet、VOA、Gutenberg、LibriVox |
| `bundle-sa`  | 同上，但衍生数据沿用 CC BY-SA，单独放文件           | Wiktionary 引文例句、Simple English Wikipedia、NGSL     |
| `quote`      | 公开演讲、新闻只摘单句，登记链接                    | 乔布斯斯坦福演讲                                        |
| `local-only` | 只放本机 `content/private/`（git 忽略），不进安装包 | 高考、四六级、专四专八真题和音频，她的课本              |

### 各来源的用法

1. **Tatoeba**（CC BY 2.0 FR）：例句库主力。每条句子带作者用户名和链接，中文译文也来自 Tatoeba 并单独署名。朗读音频每条授权不同，多数禁止商用，打包前逐条核对，默认不打包。
2. **ECDICT**（MIT）：高中单词关词表（`gk` 标签，约 3700 词）、考试标签、词形变化和中文释义草稿。中文释义由 tiger 精简审核。
3. **WordNet / Open English WordNet**：英文释义只作 AI 起草“简单英文释义”的参考。WordNet 的例句是编者写的，不算真实例句，不用。
4. **VOA Learning English**（公有领域）：慢速新闻的文字和录音，做听力、听写和精读。文中标明来自美联社、路透社等的照片和外稿不用。
5. **Project Gutenberg + LibriVox**（公有领域）：后期泛读和听力，自己对齐文本和音频。
6. **CC BY-SA 来源**：Wiktionary 只取带出处的引文例句；Simple English Wikipedia 做句群和短文阶段的泛读；NGSL 辅助排难度。

### 不用的

- GitHub 上出处不明的词库里的中文释义和例句（例如 KyleBing/english-vocabulary、没有许可证的 mahavivo/english-wordlists）。这些词表的“哪些词属于哪门考试”可以参考，词条内容不用。
- 牛津、柯林斯、朗文等商业词典的释义和例句。
- TED 演讲字幕（CC BY-NC-ND，不许改编）。
- 专四专八考试大纲词表没找到授权清楚的开放版本；需要时只存“词 + 考试标签”，不抄释义。

### 导入流程

- 导入脚本在 `scripts/content/`，下载缓存放 `.cache/content/`（git 忽略）。
  - `pnpm content:ecdict`：生成 `content/vocab/hs/words.json`（单词关词表草稿）。
  - `pnpm content:tatoeba`：给词表里每个词挑最多 8 条带简体中文译文的 Tatoeba 句子，生成 `content/sentences/tatoeba.json`、`content/vocab/hs/sentence-index.json`，不足 3 条的词写进 `content/vocab/hs/todo.json`。
- 挑句按 i+1：4 到 20 个词，其余的词至少 80% 在高中词表里，短句优先，方便前期建立信心。
- 导入结果只是候选：义项划分、语法标签、结构标注和中文释义都要经过 tiger 审核后才进入今日句组。

## 后果

- 例句库一开始就有数千条可署名的真实句子，不用等真题整理。
- Tatoeba 的句子是真人写的日常句，但不全是“现实里出现过的原文”。真题和 VOA 原文进来以后，挑句时排在 Tatoeba 前面。
- 真题是来源优先级第一，但因为安装包公开，不能打包。以后在软件里做一个“导入本地资料”功能，让真题只存在她自己的电脑上。
- 用了 CC BY-SA 内容的文件必须单独存放并标明协议，不能和 `bundle` 文件混在一起。
