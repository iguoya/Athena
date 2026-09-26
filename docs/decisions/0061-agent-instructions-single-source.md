# ADR 0061：代理指令以 AGENTS.md 为唯一真源，且只放规则

- 日期：2026-09-26
- 状态：已接受
- 关联：ADR 0045（AGENTS.md 分仓库级与应用级两层）、ADR 0047（跨平台优先）、
  ADR 0054（宁增勿删，允许移到参考层）

## 背景

主力代理是 Claude Code 与 Codex，两者读指令文件的方式不同：

- **Claude Code** 默认二选一：工作目录或上层有 `CLAUDE.md` 就只读 `CLAUDE.md` 一类，
  否则才读 `AGENTS.md`。`CLAUDE.md` 里写 `@AGENTS.md` 导入，不会重复加载。
  项目 skill 只从 `.claude/skills/` 读。
- **Codex** 从仓库根走到当前目录，把沿途的 `AGENTS.md` 按顺序拼接，总量默认上限
  **32 KiB**（`project_doc_max_bytes`），到上限后不再加载后续文件。项目 skill 只从
  `.agents/skills/` 读。

盘点时发现：

- 根 `AGENTS.md` 22 KB，`subjects/cpp` 的 30 KB，合计 52 KB；`mathematics` 合计
  44 KB。在这两个应用里用 Codex，应用级规则大概率整份没加载，而且没有任何提示。
- `subjects/polaris` 有 `AGENTS.md` 没有 `CLAUDE.md`，它的规则 Claude 看不到。
- `launcher/`、`practice/pocket_cube/` 没有 `AGENTS.md`，规则只在 README 或代码里。
- 项目 skill（`grill`）只放在 `.claude/skills/`，Codex 看不到。

## 决策

1. **`AGENTS.md` 是唯一真源。** 每个有 `AGENTS.md` 的目录配一个 `CLAUDE.md`，只写
   `@AGENTS.md` 导入；Claude 特有的补充写在导入下方。不复制规则内容。
2. **`AGENTS.md` 只放规则，阐述下放 `docs/`。** 规则本身（要做什么、不做什么、以哪条
   ADR 为准）留在 `AGENTS.md`；来历、取舍、例子移到 `docs/`，`AGENTS.md` 里留一行链接。
   这是移动不是删除（ADR 0054）。体积预算：根 `AGENTS.md` 不超过 10 KB，应用级不超过
   20 KB，使「根 + 任一应用」落在 Codex 默认 32 KiB 以内。
3. **超预算时机器侧兜底。** 在 `~/.codex/config.toml` 设 `project_doc_max_bytes`
   （个人配置，不入库）。兜底不替代第 2 条：换一台没设的机器，规则照样会丢。
4. **项目 skill 两份，内容一致。** `.agents/skills/` 是源（Codex 与其他遵循同一约定的
   代理读这里），`.claude/skills/` 是副本。不用符号链接：Windows 上 git 默认把符号链接
   检出成普通文本文件（ADR 0047）。`scripts/check.py` 校验两份逐字一致。
5. **只为在用的代理维护需要维护成本的配置。** 会复制规则、会漂移的配置（例如 Copilot 的
   `.github/copilot-instructions.md`）只为 Claude Code 与 Codex 做。只做指向、不复制内容的
   配置对任何代理都可以加，例如 Gemini CLI 的 `.gemini/settings.json` 把
   `context.fileName` 指向 `AGENTS.md`。
6. **每个独立单元都有自己的 `AGENTS.md`。** `subjects/*`、`practice/*` 下的应用与
   `launcher/` 都有；素材坑（如 `subjects/design-patterns`）除外。

## 后果

- 根 `AGENTS.md` 按第 2 条瘦身，细节移入 `docs/`。
- `subjects/cpp/AGENTS.md`（30 KB）仍超出应用级预算，根瘦身后合计约 40 KB，
  暂靠第 3 条兜底；它的瘦身另行处理。
- 新增 skill 时两处都要放；只放一处会被检查器拦下。
- 新增应用时连同 `AGENTS.md` 与 `CLAUDE.md` 一起建。
