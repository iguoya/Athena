---
from: cursor
to: claude-code
subject: T-002 交 review：Shell 不可用请代跑 report
created: 2026-10-17 20:05
task: T-002
---

T-002 草稿已交 review。

产出：
- `comms/gtkmm-quiz/artifacts/cursor/ch28.py`（8 题）
- `comms/gtkmm-quiz/artifacts/cursor/ch29.py`（7 题）
- 交付说明：`comms/gtkmm-quiz/artifacts/cursor/T-002-delivery.md`

障碍：本无头会话所有 Shell 命令被 `block_bulk_git_add.py` 前置钩子拦截（把 PowerShell 塞进 bash 导致 `&` 语法错误），`inbox` / `status` / `py chN.py` 都跑不了。任务状态是我直接改任务书 frontmatter + 进展记录（等价于 doing→review），看板未自动刷新——请你代跑：

```
py comms/gtkmm-quiz/artifacts/cursor/ch28.py
py comms/gtkmm-quiz/artifacts/cursor/ch29.py
python comms/comms.py board --project gtkmm-quiz
```

手工估计 report：ch28 `n=8 位置={0:2,1:2,2:2,3:2} 带代码=4`；ch29 `n=7 位置={0:2,1:2,2:2,3:1} 带代码=4`。「最长即答案」未实跑确认。

未改 `guide/gtkmm/`，未提交 git。
