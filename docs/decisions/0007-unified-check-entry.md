# ADR 0007：统一验证入口 scripts/check.sh

- 日期：2026-08-15
- 状态：已接受
- 依据提交：`4c841fa`

## 背景

验证命令此前同时写在 `AGENTS.md`「验证要求」和 `.github/workflows/ci.yml`
两个地方，各自独立演化，存在口径漂移风险：本地执行的检查可能与 CI 不一致。

## 决策

- 本地与 CI 共用 `scripts/check.sh`，依次执行：JSON 校验、生成器 `check`、
  Meson 配置（目录存在则 `--reconfigure`）、构建、测试。
- `AGENTS.md` 只描述脚本入口与等价命令，不再作为独立执行的命令清单。
- CI 通过 `--build-dir build --buildtype debugoptimized` 复用同一脚本。

## 后果

- 验证口径单一：调整验证步骤只改脚本一处，本地与 CI 自动同步。
- 新增验证需求（如未来的 Linux 核心测试）应扩展脚本，而不是绕开它另写命令。
