# 证据 07-optimal-1 · 729→728

## 环境
- 临时副本：`%TEMP%\pcs-t002-experiments\07-optimal`（从 `programming/pocket-cube-solver/exercise/07-optimal` 复制，不改仓库）
- PATH 前置 `C:\msys64\mingw64\bin`；`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`
- 命令：`meson setup build`（首次）→ `meson compile -C build` → `build\cube-test.exe`

## 改动
- 文件：`optimal.cc`
- Diff 摘要：to_index/from_index 中 729 全改 728

## 观察（原样）
- exit=1; FAIL line 261/268/269; 9 项失败
- 完整编译/运行日志：`evidence/_raw_logs/07-1.log`

## 对应草稿
- `experiments/07-optimal.json` 第 1 条
