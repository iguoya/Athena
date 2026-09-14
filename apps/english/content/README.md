# English 内容分级与来源

`curriculum.json` 是学习路线入口；练习材料按类型和等级放置，独立考核统一放在
`assessments/<等级>/`。当前仓库是一批可运行样本：例句、短文、写作任务和考核情境
必须绑定可核对的现实教材或开放原文，项目只把它们转成解释、受控变式和干扰项；
它不是完整英语二词表，也不把
三级名称换算成外部证书等级。

## 分级原则

| 等级 | 词与语境 | 句子、短文与翻译 | 输出 |
|---|---|---|---|
| beginner | 生活、学习、工作中的高频通用义和固定搭配 | 熟悉场景中的条件、因果、转折、指代；短句英译汉 | 完整句、理由、转折和简短实用消息 |
| intermediate | 常见抽象义、一词多义、跨场景搭配 | 一到两层从句、让步、证据与段落主旨；信息完整的句子翻译 | 观点、支持、让步、衔接与收束 |
| advanced | 熟词生义、立场、前提、证据边界 | 论证短文、复杂主干、作者态度、较长句英译汉 | 应用文任务回应、图表概括与有边界的论证 |

分级坡度参考 Council of Europe 的
[CEFR Companion Volume](https://www.coe.int/en/web/common-european-framework-reference-languages/cefr-companion-volume-and-its-language-versions)：
初级从高频、熟悉、具体的短文本起步，中级处理直接的事实和观点文本，高级提高文本
复杂度、抽象度和独立处理要求。这里只借用能力描述校准坡度，不声称获得 CEFR 认证。

## 词汇选材

- 通用高频词用 Browne、Culligan、Phillips 的 NGSL 1.2 全表
  （`sources/reference/lemmas.json`）。
- 中高级论证词用同一文件里的 NAWL 1.2 和 Coxhead 的 AWL。
- 任务类型对照研招网公开的英语二说明（`sources/reference/yz-english-2-outline.md`）。
  附录词形已用 NETEM 词表灌进 `exam-outline-lemmas.txt`。
- 已用来源引用的 VOA 课文在 `sources/reference/voa/`。
- 考研词频、四六级/考研句库、Oxford、AVL 和英语二词书副本在
  `sources/reference/github/`，只作作者侧离线对照；没有明确内容许可证的副本不能在
  学习者界面冒充正式教材来源。

频率只决定“先学哪些更划算”，不能代替语境义项、搭配和理解难度。每个条目的
`source_refs` 必须能在 `sources/catalog.json` 对上号，并绑定具体原句、篇目或习题。
自编只用于解释、受控变式和干扰项。教辅摘录放进 `sources/reference/textbooks/`，
与词频、公开大纲一起权衡，但正式投放仍须核对可靠性与授权。
`sources/reference/working-mix.json` 是当前综合选词表；
`sources/ngsl-1.2-used-words.json` 记录已上课表词在 NGSL 里的排名。

写题先打开 `sources/reference/README.md`。

## 练习与考核

- `vocab|sentences|passages|writing/<等级>/`：练习题，答后即时反馈，参与复习排期和
  错题本。
- `assessments/<等级>/`：与练习分离的平行题，整套交卷，只负责阶段资格；首次作答时材料未见，重考会复用当前题库版本。
- 独立考核可以测同一词义或同一种判断动作，但不得复用练习的原句、短文或题干。
- 写作练习保留开放输出；当前写作考核测任务回应、组织、衔接和语言选择，不把字数与
  连接词检查冒充人工作文评分。
- **单词题的有效记法**：题干是带标记的原句，不是「provide —」这种词形标题；选项
  先测本句义项（提取，不是看词对中文）；答后才出示词形和义项；练习里紧接着用新句
  挖空提取词形。间隔重复和错题变式仍由进度库负责。

运行 `npm run check:content` 可检查引用、ID、正确选项、练习/考核隔离、来源与媒体授权、
NGSL 词项、词汇义项，以及每个阶段是否真正覆盖听说读写。
