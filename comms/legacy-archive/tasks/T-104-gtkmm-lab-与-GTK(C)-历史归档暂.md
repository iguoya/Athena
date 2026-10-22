---
id: T-104
title: gtkmm-lab 与 GTK(C) 历史归档暂存包
owner: cursor
status: done
priority: P1
depends: 
created: 2026-10-21 16:00
updated: 2026-10-22 23:04
---
## 目标
为 **新建应用 `programming/gtkmm-lab`**（gtkmm / C++ 旧练习）与 **`practice/c-gui-lab` 的 GTK(C) 旧练习**准备「历史归档」条目的暂存包。**先读 `comms/legacy-archive/AUTHORING.md` 全文**，看活样板 `dp.arc.observer`。

## 暂存位置（你的文件）
- `comms/legacy-archive/artifacts/cursor/staging/gtkmm-lab/content/{archive.json,cases/arc_gtkmm_*/,archive-dropped.md}`，前缀 `gtkmmlab.`（`gtkmm.` 已被 guide/gtkmm 占用），id `gtkmmlab.arc.<slug>`
- `comms/legacy-archive/artifacts/cursor/staging/gtk-c/content/{archive.json,cases/arc_gtk_*/,archive-dropped.md}`，前缀 `gtk.`，id `gtk.arc.<slug>`
`requires` 一律 `[]`。

## 范围与裁决
- gtkmm-lab：你的 `manifest-gtkmm.json` 的 7 个 keep，**加上** `Linux/DesignEvolutionCpp`（gtkmm 官方示例跟练改造，含自有 Basic 类与 CMake，zcode 在 T-001 里标为 gtkmm-evolution）。
- gtk-c：你的 `manifest-gtk.json` 的 80 个 keep **严格按第一节筛**：Anjuta/Glade 向导样板、“手写源码少”的壳子 drop-trivial；有手写回调逻辑、能说明 GTK 编程结构的才收。预期 10–20 条，宁少勿滥；重复脚手架（g17/g19/…）整体合并成一个“Anjuta 工程骨架”类的条目最多一条，或全 drop。
- 版本问题是批注重点：GTK2/GTK3 的 `GtkHBox`、`gtk_main`、`gtk_widget_show_all`、Glade 回调名约定、`gtkmm3` vs 现行 gtkmm4（现有 `guide/gtkmm` 讲 gtkmm4，**不要引用它的内容**，只在批注里说“旧 API，4 中已改”这类事实）。
- `run` 全部 `toolchain` 或 `read-only`，`run_note` 写明需要的库与版本。

## 验收口径
AUTHORING.md 第七节，暂存目录当应用目录跑 `archive_check.check_app`（见 T-103 里的命令，换路径）。

## 边界
不提交 git；只写暂存目录。

## 进展记录
- [2026-10-21 16:14] cursor：todo → doing
- [2026-10-21 16:20] cursor：doing → review · gtkmm-lab 条目5（含 DesignEvolutionCpp）、drop/merge 3；gtk-c 条目17、drop-trivial/merge 63；全部 run=toolchain|read-only；requires=[]；前缀 gtkmmlab./gtk.。校验：archive_check 两目录均 OK([])。证据：comms/legacy-archive/artifacts/cursor/staging/verify-t104.txt；产物：…/staging/gtkmm-lab/content/ 与 …/staging/gtk-c/content/；构建脚本 _build_t104_staging.py
- [2026-10-22 23:04] claude-code：review → done · leader 验收：gtkmm-lab 5 条已入（87723347）；GTK(C) 暂存 17 条中精选 3 条并入 c-gui-lab 归档（d72d83d1），其余留 staging 不入；两应用 check.py 通过；cursor 无额度，按现有材料验收
