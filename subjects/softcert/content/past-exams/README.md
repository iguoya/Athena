# 历年真题演练 · 导入格式

真题是判分内容的最高出处(ADR 0043),但**整卷真题在取得授权前不进仓库**——
目录为空是预期状态。取得官方真题集后按下面的格式导入,应用自动按年份成卷。

## 一卷一文件

```
content/past-exams/papers/2021a.json
```

```json
{
  "id": "past-exam-2021a",
  "title": "2021 年上半年 综合知识",
  "year": 2021,
  "session": "上半年",
  "subject": "综合知识",
  "source_note": "全国软考办《嵌入式系统设计师 2017–2021 试题分析与解答》",
  "questions": [
    {
      "id": "past-exam-2021a.q12",
      "stem": "(整段题干原样录入)",
      "options": ["A. ……", "B. ……", "C. ……", "D. ……"],
      "answer": 2,
      "explanation": "(官方解析摘录或自写讲评)",
      "source": { "relation": "verbatim", "sourceId": "past-exam-2021a", "locator": "第 12 题" }
    }
  ]
}
```

## 规则

1. **年份、题号必须与试卷原样一致**,严禁凭记忆补录——记不清的题不录。
2. `relation` 一律 `verbatim`;讲解性文字放 `explanation`,不要混进 `stem`。
3. 每导入一卷,在 `papers.json` 的 `papers` 数组里登记一行。
4. 导入后跑 `python3 scripts/check.py`:出处检查会把每道题对到
   `content/sources.json` 的来源登记上。

## papers.json

`papers` 数组按年份倒序列出已导入的卷,首页真题演练页读它成卷。
`content/past-exams/papers.json` 当前登记为空数组,是预期状态。
