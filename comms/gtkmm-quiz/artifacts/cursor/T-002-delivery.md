# T-002 交付说明（cursor）

## 产出
- `comms/gtkmm-quiz/artifacts/cursor/ch28.py`：第 28 章 6 随堂 + 2 章末 = 8 题（前缀 `cw28`）
- `comms/gtkmm-quiz/artifacts/cursor/ch29.py`：第 29 章 5 随堂 + 2 章末 = 7 题（前缀 `mt29`）

## report() 状态
本无头会话 **Shell 全部被钩子拦住**（`block_bulk_git_add.py` 被包进一段 PowerShell，bash `eval` 遇 `&` 语法失败），`inbox` / `status` / `py chN.py` 均未能执行。

手工按 `quizlib.report` 口径核对：

| 章 | 预期一行 | 位置分布 | 带代码 |
|---|---|---|---|
| ch28 | `n=8 位置={0:2,1:2,2:2,3:2} 上限=4 最长即答案≈≤4 带代码=4(需≥3)` | 均衡 | cc-2/cw-1/css-1/cp-2 |
| ch29 | `n=7 位置={0:2,1:2,2:2,3:1} 上限=3 最长即答案≈≤3 带代码=4(需≥3)` | 均衡 | tc-2/ex-1/gd-1/cp-1 |

请 leader 在本机跑：

```sh
py comms/gtkmm-quiz/artifacts/cursor/ch28.py
py comms/gtkmm-quiz/artifacts/cursor/ch29.py
```

## 验证过的代码题预期
均来自章节快照英文原文与内嵌官方示例，未本机编译：
- ch28：unparent/`signal_destroy` 警告原文；`append_cairo` 示例；CSS 三选法与 `ExtraClassInit`
- ch29：规则 2 emit 归属；Dispatcher 接收者线程执行；示例 `notify`→`emit`→GUI `update_widgets` + mutex

## 不确定
- 原文 listitem 写 `add_class_name()`，示例用 `add_css_class()`——题面按「三种引用方式」出，CSS 题 why 里两者并提
- 未能实跑 `report()`，「最长即答案」个数是目测拉平后的估计，以 leader 实跑为准

## 通讯
因 Shell 不可用，任务状态与给 leader 的消息改为直接写任务书进展 + `msgs/` 新文件（未走 `comms.py status/send`）。请 leader 代跑 `board` 或 `status` 校准看板。
