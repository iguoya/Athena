# 证据 03-layer-1 · search 不保护已装块

## 环境
- 临时副本：`%TEMP%\pcs-t002-experiments\03-layer`（从 `programming/pocket-cube-solver/exercise/03-layer` 复制，不改仓库）
- PATH 前置 `C:\msys64\mingw64\bin`；`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`
- 命令：`meson setup build`（首次）→ `meson compile -C build` → `build\cube-test.exe`

## 改动
- 文件：`solver.cc`
- Diff 摘要：for i=0..placed → for i=placed-1..placed

## 观察（原样）
- exit=1; FAIL line 142 ×多次; 904 项失败；stdout 仍有第一层统计
- 完整编译/运行日志：`evidence/_raw_logs/03-1.log`

## 对应草稿
- `experiments/03-layer.json` 第 1 条
