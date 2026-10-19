# actionlint 证据（T-001）

- 时间：2026-10-19
- 命令：把 artifacts/cursor/gtkmm-native-macos.yml 的 job 段插入临时副本
  `comms/release-next/artifacts/cursor/_tmp-ci-with-macos.yml`（不改仓库 ci.yml），
  再 `actionlint` 该副本。
- 结果：exit=0
- 输出：
```
(no output — zero findings)
exit=0
```