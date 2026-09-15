# 内容来源与查证规则

**本应用的教学内容一律有据可依，不得凭记忆发挥**（ADR 0054）。这份文档说明依据
哪些材料、怎么标注、怎么核对。

> 这一条在 2026-09-16 之前是反的：本文曾规定参考站点「仅作对照参考，**不作为章节
> 结构、目录顺序或措辞的来源**」。那句话的本意是防止把教程抄一遍，实际效果却是把
> 写作推向凭记忆发挥——而 C++ 的语义细节（值类别、生命周期延长的条件、特殊成员
> 函数的生成规则、窄化的判定）恰恰最不能凭记忆写，写错了也没有任何机制能发现。
> 该防的是**抄**，不是**查**。

## 要防的是抄，要求的是查

- **禁止**：整段复制正文、照搬目录结构、把某个教程的组织方式当作自己的章节顺序。
- **要求**：写之前查、写之后对。概念的定义、规则的条件、边界的例外，以规范性材料
  为准；讲法、顺序、例子、图示仍然自己组织。
- 引用按各来源的许可标注，不整段复制。

## 来源分级

登记表在 [`../resources/sources/catalog.json`](../resources/sources/catalog.json)，
每条带许可与实地核对日期。**凭印象写出处比自造更糟**——使用者按图索骥扑一次空，
之后所有出处都不可信了。

### 一级：规范性来源（定义、条件、边界、术语以它们为准）

| id | 来源 | 什么时候用它 |
|---|---|---|
| `cppreference` | [cppreference.com](https://en.cppreference.com/) | 语言与标准库语义的第一顺位。`locator` 写条目路径，如 `cpp/language/value_category` |
| `iso-cpp-draft` | [ISO C++ 标准草案](https://github.com/cplusplus/draft) | 需要逐字精确的条件时。`locator` 写条款号，如 `[dcl.init.list]/7` |
| `cpp-core-guidelines` | [C++ Core Guidelines](https://github.com/isocpp/CppCoreGuidelines) | 「该怎么写、为什么」这类取舍。`locator` 写规则编号，如 `ES.23`、`R.1` |
| `ms-learn-cpp` | [Microsoft Learn C++ 文档](https://github.com/MicrosoftDocs/cpp-docs) | 现代 C++ 的理念性说明，有中文版 |

### 二级：讲法对照（不作为语义判定的依据）

中文教程站（菜鸟教程、C 语言中文网、StudyC++、W3Cschool 等）登记为
`cn-cpp-tutorials`。**只用来看「别人怎么讲得明白」「初学者常卡在哪」**。
一级与二级冲突时一律以一级为准，不得用二级材料为一个说法背书。

## 怎么标

知识点和骨架案例都可以带 `source_refs`，字段名用跨应用统一的那套
（仓库 ADR 0043）：

```json
"source_refs": [
  {
    "source_id": "cppreference",
    "relation": "adapted",
    "locator": "cpp/language/copy_initialization",
    "url": "https://en.cppreference.com/cpp/language/copy_initialization",
    "note": "拷贝初始化只考虑非 explicit 构造函数——两种写法的分界以此条为准"
  }
]
```

- `relation` 取 `verbatim` / `quoted` / `adapted` / `authored` 之一（内容来源），
  或 `selection_basis` / `see_also`（补充说明，顶替不了内容来源）。
- `locator` 与 `url` 至少给一个，否则这条出处没法核对。
- `authored`（自造）必须在 `note` 里写明为什么一级材料覆盖不到，且同一节内不得过半。

生成器会校验 `source_id` 在登记表里、`relation` 合法、`authored` 给了理由；仓库的
`scripts/check-app-sources.mjs` 会统计覆盖率。存量未标注的知识点列在
[`../content-contract.json`](../content-contract.json) 的豁免名单里，**那份名单
只能变短**——新写或重写的一律当场标出处。

## 覆盖范围的参考

该讲哪些知识点、常见误区在哪里，仍可对照上面两级材料；与 C 语言高度重叠的基础内容
只在理解 C++ 语义确实需要时才纳入（ADR 0002）。
