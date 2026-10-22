# 历史 GTK 条目相对 practice/c-gui-lab 的落点建议

## 现状（只读 AGENTS.md）

- `practice/c-gui-lab` 是 **practice** 应用：Electron 母体 + `apps/gtk-style`（**GTK4 + libadwaita**）、imgui、lvgl 等并排对比。
- **不建进度库**；目标是「能跑的对比」，不是课程章节。

## 旧 Linux/GTK 代码

- 静态判断以 **GTK2 / GTK3 + Anjuta/Glade 脚手架** 为主（`gtk_main` / `GtkHBox` / `.glade` / `callbacks.c` 样板）。
- 与现网 `apps/gtk-style`（GTK4）**不能直接并入可运行画廊**。

## 建议

1. 若 c-gui-lab 增加「历史归档」区：条目一律 `run: read-only` 或 `toolchain`（需自备 GTK3），不要挂进母体一键 spawn。
2. 脚手架重复（内容哈希相同的 g17/g19/…）只留一份规范版，其余 duplicates。
3. 真正有手写逻辑的（如 `GtkApp`、少量非空 callbacks）优先 keep；纯 Anjuta 空壳可考虑 leader 裁决批量 drop。
4. `Linux/SDL` 不在本任务范围；leader 已划给 c-gui-lab，与 GTK 清单分开。
