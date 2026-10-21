# 历年真题整卷库

整卷存放目录：一份试卷一个 JSON 文件，命名 `YYYY-MM.json`（如 `2019-04.json`）。
节内容（`content/sections/*.json`）里的判分题通过 `source_refs.locator` 指向这里的题号，
如「全国 2019 年 4 月 第 3 题」。

## 整卷格式

```json
{
  "course": "linear-algebra",
  "code": "02198",
  "year": 2019,
  "month": 4,
  "title": "全国 2019 年 4 月高等教育自学考试 线性代数 试题",
  "transcript_sources": ["转录来源 URL，多个都列"],
  "sections": [
    {
      "name": "一、单项选择题",
      "scoring": "本大题共 5 小题，每小题 2 分，共 10 分",
      "items": [
        {
          "no": 1,
          "stem": "题干原文（公式用 LaTeX，$...$ 行内）",
          "options": ["A. …", "B. …", "C. …", "D. …"],
          "answer": "B",
          "solution_note": "评分参考或解析（有则录）"
        }
      ]
    }
  ]
}
```

## 录入规则

1. **如实转录**：行列式与矩阵用 LaTeX（`\\begin{vmatrix}…` / `\\begin{pmatrix}…`）；
   扫描件转录后必须做数值验算核对答案，算不通的题在 `solution_note` 里标「待核」，不猜。
2. **出处照记**：`transcript_sources` 记下转录页面 URL；纸质/扫描件来源记文件名与页码。
3. **不带答案的卷子也收**：答案后补，`answer` 可为 `null`。
4. 节内容里的题改挂真题时，`relation` 从 `authored` 换成 `verbatim`，`authored` 数量只减不增。
