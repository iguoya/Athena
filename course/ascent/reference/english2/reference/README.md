# 本地参考材料

本目录给**写题的人**离线对照，不是给学习者当课文背。练习和考核仍在
`content/vocab|sentences|writing|assessments/` 里自写或改写。

个人练习应用：写题用得上的材料就落到这里。公开词表、考试说明、公有领域课文、
教辅摘录和个人笔记都收。不因为出处不够「正统」就丢掉；多家对照，一定程度上
可靠即可。完整电子表不在公开页上的（英语二大纲附录 5500 词形），留下粘贴入口。

## 现在有什么

| 文件 | 用来干什么 |
|---|---|
| `lemmas.json` | NGSL 1.2、NAWL 1.2、AWL 中心词及屈折；选词和校验覆盖范围 |
| `raw/` | 上述三份词表的原始 JSON 快照 |
| `yz-english-2-outline.md` | 研招网公开的英语二试卷结构、能力要求和备考口径 |
| `exam-collocations.json` | 同一公开页附带的常用词组，写搭配题时先查这里 |
| `exam-outline-lemmas.txt` | 大纲附录词形；已用 NETEM 5530 词灌入，校验覆盖范围按此表 |
| `voa/` | 已经用来源引用的 VOA Learning English 课文（公有领域） |
| `academic-phrasebank.md` | 曼彻斯特 Academic Phrasebank 的功能分类，写作骨架对照 |
| `working-mix.json` | 当前课表、建议下一词、尚未覆盖的公开搭配；写题时的综合权衡表 |
| `github/` | 考研词频、四六级/考研句库、Oxford、AVL、英语二词书等原件 |
| `textbooks/` | 教辅摘录、词表和笔记投放区；不自动当作练习正文 |

## 怎么用

1. 打开 `working-mix.json`，看已覆盖和下一优先；词频、公开搭配、教辅摘录互相校正。
2. 初级词仍优先 NGSL 前 1000；中级看 NGSL 后段和 AWL；高级看熟词生义、NAWL
   和教辅里反复出现的任务词。不必只信一家。
3. 写搭配先查 `exam-collocations.json` 和 `textbooks/` 里的摘录，并在 `source_refs`
   里标明综合了哪些依据。
4. 词形覆盖已由 `exam-outline-lemmas.txt` 承担；补词时先查 `github/` 里的句库和英语二词表。
5. 教辅扫描件和整本真题不必进练习 JSON；摘录、词表、切句笔记放到 `textbooks/`。原件优先放 `github/`。
