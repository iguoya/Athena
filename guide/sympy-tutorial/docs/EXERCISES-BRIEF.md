# 「试一试」写作须知

原教程没有习题。「试一试」是本应用自编的练习：让学习者**先预测、再在本机 SymPy 里运行、最后回来核对一个可机器判的结果**。
写好它是「学工具有成果」的关键；**答案必须由真 SymPy 算出**，不能凭心算。

## 你领到什么

几页教程。对每页写 3～6 道「试一试」，紧扣本页讲的函数，由易到难；每道换一个角度（调用形式、边界情形、与数学的联系、常见误区），
不要把同一题换个数重复。能连着高数或线代的优先（求导、积分、极限、矩阵运算、特征值）。

## 文件格式

`content/exercises/<页 id>.json`，一个数组，元素：

```json
{
  "id": "ex1",
  "stem": "先预测，再在 SymPy 里运行：\n\n```python\nfrom sympy import *\nx = symbols('x')\ndiff(x**3 * exp(x), x).subs(x, 0)\n```\n\n结果是多少？",
  "check": {"kind": "numbers", "ask": "写出一个数。", "answer": [0], "hint": "先求导再代入 $x=0$；乘积法则的两项在 $x=0$ 处各是多少？"},
  "verify": "result = diff(x**3*exp(x), x).subs(x, 0)",
  "sol": "乘积法则：$(x^3e^x)'=3x^2e^x+x^3e^x$，代入 $x=0$ 得 0。\n\n```python\n>>> diff(x**3*exp(x), x).subs(x, 0)\n0\n```",
  "source_refs": [{"relation": "authored", "locator": "calculus · 导数", "note": "自编，答案由 SymPy 1.14 复算"}]
}
```

- `stem`：中文题面。公式用 `$…$`，行内代码用反引号，代码块用三个反引号围栏；空行分段。题面里给出要运行的代码，学习者复制到自己的 Python 里。
- `check.kind`：
  - `numbers`：答案是一个数或一组数（矩阵按行展开成数列）；`ask` 说清写几个数、什么顺序；`answer` 是 float 全精度（`1/3` 写 `0.3333333333333333`）。
  - `choice`：`options` ≥ 2 个、**恰好一个** `ok: true`，每个都有 `why`；错误选项要对应真实误解（例如把 `**` 当成 `^`）。
  - 要写长证明、答案写法不唯一（如化简结果的形式有多种）的，不做核对点，换一个问法（例如改成问某个值、某个项数、某个是/否）。
- `verify`（numbers 必填）：一段 Python，已 `from sympy import *` 且已定义 `x, y, z, t`；把结果（数或数的列表）赋给 `result`。
  `check.py` 会复跑它并与 `answer` 比对（容差 1e-6）。choice 题没有 `verify` 的，在 `sol` 里给出真 SymPy 的运行结果。
  无法复算的写 `verify_note` 说明原因。
- `hint`：答错时显示，只说**回头复习什么、怎么下手**，不泄露答案。
- `sol`：参考做法：先思路，再给运行结果（`>>>` 会话要与真工具输出一致）。
- `source_refs`：固定 `relation: authored`，`locator` 写对应教程页与小节。

## 复核与汇报

写完用 `python3 scripts/lint_exercises.py <页 id> ...`（需要有 sympy 的 Python 才会复算；没有 SymPy 的 python3 只查结构）。
只改 `content/exercises/` 下属于你这几页的文件，不碰别的文件，不运行 git / sync_upstream.py / check.py。
汇报：每页写了几道、哪些用 choice、发现的教程笔误。
