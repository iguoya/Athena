# 「试一试」写作须知

手册没有习题。「试一试」是本应用自编的练习：让学习者**先预测、再在本机 Octave 里运行、最后回来核对一个可机器判的结果**。
**答案必须由真 Octave 算出**（本机已装 Octave 8.4.0，命令行 `octave --no-gui --eval '…'`），不能凭心算。

## 你领到什么

几页手册。对每页写 4～6 道「试一试」，紧扣本页收的函数，由易到难；每道换一个角度（调用形式、输出形状、边界情形、常见误区、与数学的联系），
不要把同一题换个数重复。能连着线代或高数的优先（解方程组、特征值、秩与零空间、积分、微分方程、多项式根）。

## 文件格式

`content/exercises/<页 id>.json`，一个数组，元素：

```json
{
  "id": "ex1",
  "stem": "先预测，再在 Octave 里运行：\n\n```octave\nA = [2 1; 1 3];\nlambda = eig (A)\n```\n\n两个特征值之和是多少？",
  "check": {"kind": "numbers", "ask": "写出一个数。", "answer": [5], "hint": "特征值之和等于矩阵的迹 $\\operatorname{tr}A$。"},
  "verify": "A = [2 1; 1 3]; result = sum (eig (A));",
  "sol": "特征值之和等于迹：$2+3=5$。\n\n```octave\n>> sum (eig (A))\nans = 5\n```",
  "source_refs": [{"relation": "authored", "locator": "linalg · eig", "note": "自编，答案由 Octave 8.4 复算"}]
}
```

- `stem`：中文题面。公式用 `$…$`，行内代码用反引号，代码块用三个反引号围栏；空行分段。题面里给出要运行的代码，学习者复制到自己的 Octave 里。
- `check.kind`：
  - `numbers`：答案是一个数或一组数（矩阵按**列**展开成数列，Octave 的惯例——`ask` 里说清顺序）；`answer` 是 float 全精度（`1/3` 写 `0.3333333333333333`）。
  - `choice`：`options` ≥ 2 个、**恰好一个** `ok: true`，每个选项都有 `text` 与 `why`；错误选项要对应真实误解（如把 `*` 当逐元素乘）。
    正确项的位置请打乱，不要总放第一个。
  - 要写长证明、答案写法不唯一的，不做核对点，换一个问法（问某个值、某个元素、个数、是/否）。
- `verify`（numbers 必填）：一段 Octave 代码，把结果（数或数组，按列展开）赋给变量 `result`；`check.py` 会复跑它并与 `answer` 比对（容差 1e-6）。
  涉及随机数的题不做。choice 题的对错也要用真 Octave 运行确认，并把运行结果写进 `sol`。
- `hint`：答错时显示，只说**回头复习什么、怎么下手**，不泄露答案。
- `sol`：参考做法：先思路，再给运行结果（`>>` 会话必须是你真跑出来的输出，不要凭记忆写）。
- `source_refs`：固定 `relation: authored`，`locator` 写对应页与函数。
- 绘图页的题：图本身无法机器判，改问可算的量（如某点的函数值、`ylim` 的返回值、句柄属性、`numel` 之类），并在 `sol` 里告诉学习者运行后应看到什么样的图。

## 复核与汇报

写完用 `python3 scripts/lint_exercises.py <页 id> ...` 检查（会用本机 Octave 复算 `verify`）。
只改 `content/exercises/` 下属于你这几页的文件，不碰别的文件，不运行 git / sync_upstream.py / check.py。
汇报：每页写了几道、哪些用 choice、发现的手册笔误或与手册描述不符的实际行为。
