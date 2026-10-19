# 预测题实算与验收统计（T-001 返工）

## 题数与分布

| 章 | 题数 | 正确项为唯一最长 |
|---|---:|---:|
| 01-net | 5 | 1/5 |
| 02-turns | 8 | 2/8 |
| 03-layer | 7 | 2/7 |
| 04-orient | 7 | 2/7 |
| 05-permute | 7 | 2/7 |
| 06-solver | 7 | 2/7 |
| 07-optimal | 7 | 1/7 |

全课共 **48** 题。正确项为唯一最长：**12/48 = 25.0%**（要求 20%–35%；每章 ≤1/3）。

`answer` 分布：位置 0/1/2/3 各 **12** 题（各 **25.0%**），落在 20%–30% 要求内。

返工要点：`choices` 中无「（」「(」；干扰项手写、长度差 ≤40%；已去掉批量括号后缀。

题型：每章至少 1 道预测题（带 `figure`/`reveal`）；02–07 各有辨析题、回溯题；01 按任务书可缺辨析/回溯。全部旧题 `id` 保留。

草稿路径：`comms/pocket-cube-solver/artifacts/cursor/questions/<章id>.json`  
生成脚本：`build_questions.py`（可复跑核对分布与括号/长度）

## 实算命令

```text
node --experimental-strip-types comms/pocket-cube-solver/artifacts/cursor/_run_verify.mjs
python comms/pocket-cube-solver/artifacts/cursor/build_questions.py
```

模型：`programming/pocket-cube-solver/src/cube.ts`（`run` / `parse` / `solved` / `layerDone` / `topOriented` / `isSolved`）

JSON 解析：

```text
python -m json.tool comms/pocket-cube-solver/artifacts/cursor/questions/<章id>.json
```

七个文件均通过（UTF-8 无 BOM）；`choices` 无括号。

## 预测题逐题

### cube.net.predict-ruprime
- 文件：`questions/01-net.json`
- 实算：`R U' R'` 后 `U[0]=绿色`
- 草稿 `answer=0` →「绿色」
- 结果：OK

### cube.turns.predict-ru
- 文件：`questions/02-turns.json`
- 实算：`R U` 后 F 右上 slot9=`橙色`
- 草稿 `answer=2` →「橙色」
- 结果：OK

### cube.layer.predict-rprime
- 文件：`questions/03-layer.json`
- 实算：`R'` 后 `layerDone=false` `isSolved=false`
- 草稿 `answer=1` →「layer_done 为假，is_solved 也为假」
- 结果：OK

### cube.orient.predict-sune
- 文件：`questions/04-orient.json`
- 实算：Sune 后 U 黄格=1，`layerDone=true`，`topOriented=false`
- 草稿 `answer=0` →「1 格黄，且 layer_done 为真」
- 结果：OK

### cube.permute.predict-r2
- 文件：`questions/05-permute.json`
- 实算：`R2` 后 `topOriented=false` `layerDone=false`
- 草稿 `answer=3` →「top_oriented 为假，layer_done 也为假」
- 结果：OK

### cube.solver.predict-f
- 文件：`questions/06-solver.json`
- 实算：`F` 后 R 面=`黄、橙、黄、橙`
- 草稿 `answer=2` →「黄、橙、黄、橙」
- 结果：OK

### cube.optimal.predict-ur
- 文件：`questions/07-optimal.json`
- 实算：`U R` 后 F 左上 slot8=`橙色`
- 草稿 `answer=1` →「橙色」
- 结果：OK

## 汇总

全部 7 道预测题实算与草稿 `answer` 一致。`build_questions.py` 输出 `ACCEPTANCE_STATS_OK`。
