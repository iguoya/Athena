# chen-linear-algebra 舱：陈怀琛《实用大众线性代数（MATLAB版）》精读应用

应用：`guide/chen-linear-algebra`（ADR 0177）。leader（zcode）建壳、定格式、验收、提交；
worker（cursor）做习题数字化采集，直接写 `guide/chen-linear-algebra/content/exercises/`
（不走 artifacts 中转，`check.py` 的出处门禁是硬闸）。

## 文件归属

| 路径 | 谁 |
|---|---|
| `comms/chen-linear-algebra/tasks`、`msgs`、`artifacts/zcode` | zcode |
| `comms/chen-linear-algebra/artifacts/cursor`、`chat/cursor.log`、`read/cursor.txt` | cursor |
| `guide/chen-linear-algebra/content/exercises/` | cursor（按任务书） |
| `guide/chen-linear-algebra/` 其余一切、git 提交 | zcode |

## 规矩

- 题目格式与出处规则以 `guide/chen-linear-algebra/AGENTS.md` 为准；格式范本看
  `content/exercises/ch7.json`（leader 写的两道示范）。
- **authored 不入库**：只收 verbatim / adapted，locator 必须给到页码与题号。
- worker 不提交 git；做完 `status <任务> review --note "…"` 附 `python scripts/check.py --skip-rust`
  输出摘要与逐题 locator 核对记录（放 `artifacts/cursor/`）。
- 底本：第 7 章用 `upstream/第7章-…doc` + `upstream/programs/pla7xx.m`（已在仓库）；
  1–6 章等书 PDF（T-901 拿到后 leader 广播）。
