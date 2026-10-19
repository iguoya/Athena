# 证据 04-orient-1 · Sune 多撇

## 环境
- 临时副本：`%TEMP%\pcs-t002-experiments\04-orient`（从 `programming/pocket-cube-solver/exercise/04-orient` 复制，不改仓库）
- PATH 前置 `C:\msys64\mingw64\bin`；`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`
- 命令：`meson setup build`（首次）→ `meson compile -C build` → `build\cube-test.exe`

## 改动
- 文件：`solver.cc`
- Diff 摘要：R U R' U R U2 R' → R U R' U' R U2 R'

## 观察（原样）
- exit=1; FAIL line 137/139/140/142; 4 项失败
- 完整编译/运行日志：`evidence/_raw_logs/04-1.log`

## 对应草稿
- `experiments/04-orient.json` 第 1 条
