# 证据 03-layer-2 · 深度上限 4

## 环境
- 临时副本：`%TEMP%\pcs-t002-experiments\03-layer`（从 `programming/pocket-cube-solver/exercise/03-layer` 复制，不改仓库）
- PATH 前置 `C:\msys64\mingw64\bin`；`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`
- 命令：`meson setup build`（首次）→ `meson compile -C build` → `build\cube-test.exe`

## 改动
- 文件：`solver.cc`
- Diff 摘要：depth <= 11 → depth <= 4

## 观察（原样）
- exit=3; std::logic_error what(): 第一层找不到解
- 完整编译/运行日志：`evidence/_raw_logs/03-2.log`

## 对应草稿
- `experiments/03-layer.json` 第 2 条
