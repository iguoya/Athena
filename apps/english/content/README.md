# English 内容分级与来源

`curriculum.json` 是学习路线入口；练习材料按类型和等级放置，独立考核统一放在
`assessments/<等级>/`。当前仓库是一批可运行的自编样本，不是完整英语二词表，也不把
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

- 通用高频词优先参考 Browne、Culligan、Phillips 的
  [New General Service List](https://www.newgeneralservicelist.com/new-general-service-list)。
- 中高级跨学科说明和论证词参考 Victoria University of Wellington 的
  [Academic Word List](https://www.wgtn.ac.nz/lals/resources/academicwordlist/information)。
- 最终层能力方向参考中国研究生招生信息网公开的
  [英语（二）大纲解读](https://yz.chsi.com.cn/kyzx/en/201709/20170915/1628558459.html)，
  覆盖阅读理解、英译汉和写作，但不复制真题正文。

频率只决定“先学哪些更划算”，不能代替语境义项、搭配和理解难度。所有例句、短文、
题干、翻译与干扰项均为本项目自行编写。

## 练习与考核

- `vocab|sentences|passages|writing/<等级>/`：练习题，答后即时反馈，参与复习排期和
  错题本。
- `assessments/<等级>/`：与练习分离的平行题，整套交卷，只负责阶段资格；首次作答时材料未见，重考会复用当前题库版本。
- 独立考核可以测同一词义或同一种判断动作，但不得复用练习的原句、短文或题干。
- 写作练习保留开放输出；当前写作考核测任务回应、组织、衔接和语言选择，不把字数与
  连接词检查冒充人工作文评分。

运行 `npm run check:content` 可检查引用、ID、正确选项和练习/考核的材料隔离。
