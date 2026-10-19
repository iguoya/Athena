# release-next 舱：10.0.0 遗留的发版作业补齐

范围见 `docs/RELEASE-TODO.md`（不含九州、驾考）。分工同 `pocket-cube-solver` 舱：leader（claude-code）集成进 `.github/workflows/`、推送并触发 CI、看结果；
worker（cursor）**只在 `artifacts/cursor/` 写草稿与本地验证证据，不改 `.github/`、不提交、不推送**。
作业只能在 CI 上真跑，所以草稿必须先过本地 `actionlint`，并写清哪些步骤只在 CI 上才能验证。
