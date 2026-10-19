# T-003 交付说明（返工）

## 返工点

按 leader 消息「T-003 返工」：

1. **删除** `build_patches.py` 里一切填充尾巴逻辑（`_expand_claim` / `equalize_distractors` / `re_equalize` 整段）。
2. 干扰项过短时：缩短正确项（断言不变）或**手写**等长/更长干扰项；禁止机械拼接。
3. 原文已合格的题（`KEEP_VERBATIM`）选项**一字不动**，只洗牌。
4. `check_patch.py` 新增：任意 ≥6 字从句（按 `，；：` 切）出现在 ≥3 个不同选项 → FAIL。
5. 「正确项独占最长」按严格最长计（并列不算），目标 20%~35%。

## 产物

| 文件 | 说明 |
|---|---|
| `snake.json` | 44 题选项重写补丁 |
| `chinese-chess.json` | 21 题选项重写补丁 |
| `c-plus-plus.json` | 18 题选项重写补丁 |
| `check_patch.py` | 自检（含从句重复 / 独占最长） |
| `build_patches.py` | 可复现生成脚本（无填充尾巴） |
| `check_patch.out.txt` | 自检全文 |

未改 `programming/`，未提交 git。

## 自检摘要

```
snake          44 题  位置 25/25/25/25  独占最长 30%  中文括号 0  重复从句 0
chinese-chess  21 题  位置 24/24/29/24  独占最长 29%  中文括号 0  重复从句 0
c-plus-plus    18 题  位置 28/22/28/22  独占最长 28%  中文括号 0  重复从句 0
PASS
```

复跑：

```sh
python comms/pocket-cube-solver/artifacts/cursor/bias-fix/build_patches.py
python comms/pocket-cube-solver/artifacts/cursor/bias-fix/check_patch.py
```

## 合格题（只洗牌）

`snake.window.redraw` / `snake.window.fps` / `snake.grid.cell` / `snake.grid.hz` /
`snake.body.deque` / `snake.food.grow` /
`chess.window.identity` / `chess.board.vector` / `chess.piece.general` /
`chess.piece.axis` / `chess.piece.click` / `chess.move.end` /
`cpp.TypeSemantics.object_lifetime#1` / `cpp.ValueSemantics.copy_control#1`

## 正确项措辞改写

多数改写是为了与手写干扰项等长而缩短从句（断言不变）；另有去括号：

- `snake.input.verify` — 去掉中文括号注释
- `snake.design.tail` — `（D-3）` → `D-3`
- `snake.score.event` — 「吃到食物」扩成完整断言句
- `cpp.RAII.basic#0` — 「析构函数」→「放在类的析构函数里」
- 若干象棋题缩短正确项以对齐长度（见 `CORRECT_REWRITES` 与自检 diff）

完整前后文见 `check_patch.out.txt`。
