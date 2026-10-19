# 证据 05-permute-2 · swap_adjacent 少 F'

## 环境
- 临时副本：`%TEMP%\pcs-t002-experiments\05-permute`（从 `programming/pocket-cube-solver/exercise/05-permute` 复制，不改仓库）
- PATH 前置 `C:\msys64\mingw64\bin`；`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`
- 命令：`meson setup build`（首次）→ `meson compile -C build` → `build\cube-test.exe`

## 改动
- 文件：`solver.cc`
- Diff 摘要：公式末尾去掉 F'

## 观察（原样）
- exit=1; FAIL line 158/159/160; 3 项失败
- 完整编译/运行日志：`evidence/_raw_logs/05-2.log`

## 对应草稿
- `experiments/05-permute.json` 第 2 条
