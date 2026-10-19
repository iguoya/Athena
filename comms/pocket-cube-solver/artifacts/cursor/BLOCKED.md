# T-001 blocked · 第三轮 spawn 复测：Shell 仍全挂

- **时间**：2026-10-19（本会话；spawn 无头 cursor · T-001）
- **舱**：pocket-cube-solver
- **任务书磁盘状态（开工时）**：`status: todo`，BOARD `doing 0`，**无他人认领冲突**

## 本轮命令探测

按补充说明先跑：

```
echo "shell-ok" && python --version && pwd
```

被钩子拦死，命令未启动。立刻再试：

```
echo shell-ok
```

同样拒。错误与 08:20 轮一致（不是 08:05 的 bash/PowerShell 混用）：

```
C:\Users\tiger\AppData\Local\Python\pythoncore-3.14-64\python.exe:
can't open file 'C:\\.claude\hooks\block_bulk_git_add.py': [Errno 2] No such file or directory
```

## 根因（相对仓库事实）

- 仓库内钩子真实路径：`C:\Users\tiger\Athena\.claude\hooks\block_bulk_git_add.py`（存在）
- 钩子实际去找：`C:\.claude\hooks\block_bulk_git_add.py`（不存在）
- 推断：`CLAUDE_PROJECT_DIR`（或等价解析）落成 `C:\`，而不是仓库根 `C:\Users\tiger\Athena`
- `.cursor/hooks.json` 无 `beforeShellExecution`；这条线来自 Claude Code PreToolUse（`.claude/settings.json`）被 Cursor Shell 侧误挂/错位环境

因此 **inbox / status / Node 实算 / json.tool / 完成提示音** 全部无法执行。

## 因此做不到的验收步骤

| 步骤 | 命令 | 结果 |
|---|---|---|
| 确认 Shell | `echo shell-ok` | 未执行 |
| 收件箱 | `python comms/comms.py inbox cursor --project pocket-cube-solver` | 未执行 |
| 认领 | `… status T-001 doing --by cursor …` | 未执行 |
| 预测题实算 | Node / `tsx` 调 `src/cube.ts` | 未执行 |
| JSON 校验 | `python -m json.tool` | 未执行 |
| 交 review | `… status T-001 review …` | 未执行 |
| 正规 blocked | `… status T-001 blocked …` | 未执行 → 手改任务书 + 本文件 |

## 已做的协议动作（Shell 不可用时的等价物）

1. 任务书 `status: blocked` + 进展记录一行（本应走 `status`；tasks 归属 leader，仅因命令通道全挂）。
2. 正式消息：`msgs/` 下本轮「请回」给 claude-code。
3. 本文件（覆盖同名证据；保留完整复测结论）。

## 未做

- 未写 `artifacts/cursor/questions/*.json`（无 Node 实算则无法满足「预测题不得口算」）。
- 未改 `programming/`，未提交 git。

## 请 leader / 使用者

修好 Cursor Shell 侧对 `block_bulk_git_add.py` 的调用：

1. 不要把 Claude Code PreToolUse 挂进 Cursor `beforeShellExecution`；或
2. 让 `CLAUDE_PROJECT_DIR`（或等价变量）指向 `C:\Users\tiger\Athena`，而不是 `C:\`。

修好后请把 T-001 拨回 `todo` 再 `spawn` 新会话。本会话无命令通道，不空等、不口算题库。
