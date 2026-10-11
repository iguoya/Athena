# ADR 0060：学习壳改为 Tauri 2 + React，GTK 不再承载教案

- 日期：2026-10-11
- 状态：已接受（tiger 2026-10-11：把现有 C++ 学习改成 Tauri + React，不要 gtkmm 当底层，按现在的课程模式重写，内容和练习成果保留一部分）
- 依据：仓库 [ADR 0138](../../../../docs/decisions/0138-course-apps-unify-tauri-react.md) 决策 8 的重启条件（使用者另行指派）。重评结论：GTK 控件是旧教案的载体，不是 C++ 这门课的内容；实验仍然是本机 C++ 编译运行。
- 修订：本应用 ADR 0024、0035、0038 里「学习页由 GTK 控件承载」的现行效力。那些 ADR 保留原文，说明当时为什么用 GTK。
- 不变：`id`、目录名、知识点前缀 `cpp.`、`progress/learning.db` 的 `function_id` 与掌握度 0–5、出处档位 open。

## 背景

仓库把课程类应用统一到 Tauri 2 + React。0138 把本应用暂缓，理由是当时的教案写在 GTK 控件上。使用者现在指定改底层，并要求吸取原课的精华、按现行课程模式重写，进度不要整库作废。

现行课程模式是：大纲指向知识点，讲解用块（导语、对照、代码、先预测再揭示），随堂题写入掌握度，实验给骨架、本机编译。这与本应用原来的学习闭环一致，换的是呈现层。

## 决策

1. **打开应用的壳是 Tauri 2 + React + TypeScript + Vite**，样式用 Tailwind 4。`app.json` 的 `dev` 块改为 `pnpm run tauri:dev`，端口 **1512**。进程名仍是 `athena-c-plus-plus`。
2. **课表改到 `content/curriculum.json`。** 知识点 id 仍是 `cpp.<章>.<节>`，与进度库 `function_id` 相同，已有掌握度还能对上。章名、节名、难度、先修、出处从 `resources/athena.json` 接过来。
3. **重写的是讲解，不是再铺一层 GTK。** 值类别、初始化、引用、拷贝与移动、RAII 这些 C++ 特有的节写成对照、代码和随堂题。其余节先保留原来的题注与出处，不编造新的规则。
4. **实验仍在本机编译运行**（C++20）。现有 `resources/cases/` 可在应用里打开并运行。不提供任意 shell。
5. **进度库沿用 `progress/learning.db`。** 表仍是 `knowledge_progress` 与 `assessment_attempt`。掌握度换算仍是 `正确数 * 5 / 题数`。新的随堂题写入同一张表。
6. **GTK / Meson 源码本轮留在目录里，但不再是启动和 `scripts/check.py` 的路径。** 删除那棵树要单独一次提交，写清删了什么、从哪能取回。发行工作流（`.github/workflows/release.yml`）仍按旧的 Meson 包走，本次不改 tag 发布。

## 后续

决策 6 由仓库 [ADR 0141](../../../../docs/decisions/0141-split-gtk-cpp-into-practice.md) 取代：GTK / Meson 源码迁到 `practice/cpp`，不是从本目录删掉。课表以 `content/curriculum.json` 为准，不再与 `athena.json` 对账。

## 后果

- 日常开发不再需要 GTK、Blueprint、Meson。检查改为课表 id 对齐、前端构建和 `cargo check`。
- CI 里本应用从 GTK 矩阵改到 Tauri 矩阵；`pocket_cube` 仍走 GTK。
- `resources/athena.json` 在 GTK 树删除前仍是旧壳的配置。运行中的课以 `content/curriculum.json` 为准。两份 id 必须一致，`scripts/check.py` 守这个不变量。
