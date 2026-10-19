# 证据 06-solver-2 · normalize 不要求 DBL

## 环境
- 临时副本：`%TEMP%\pcs-t002-experiments\06-solver`（从 `programming/pocket-cube-solver/exercise/06-solver` 复制，不改仓库）
- PATH 前置 `C:\msys64\mingw64\bin`；`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`
- 命令：`meson setup build`（首次）→ `meson compile -C build` → `build\cube-test.exe`

## 改动
- 文件：`cube.cc`
- Diff 摘要：去掉 corner_solved(moved, kDBL) 条件，首个旋转即 return

## 观察（原样）
- exit=3; FAIL line 208; std::invalid_argument what(): 要先摆正：DBL 角块必须在左下后
- 完整编译/运行日志：`evidence/_raw_logs/06-2.log`

## 对应草稿
- `experiments/06-solver.json` 第 2 条
