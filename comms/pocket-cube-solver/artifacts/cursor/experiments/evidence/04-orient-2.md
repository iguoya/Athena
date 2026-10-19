# 证据 04-orient-2 · top_oriented 看 D

## 环境
- 临时副本：`%TEMP%\pcs-t002-experiments\04-orient`（从 `programming/pocket-cube-solver/exercise/04-orient` 复制，不改仓库）
- PATH 前置 `C:\msys64\mingw64\bin`；`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`
- 命令：`meson setup build`（首次）→ `meson compile -C build` → `build\cube-test.exe`

## 改动
- 文件：`solver.cc`
- Diff 摘要：Face::U → Face::D

## 观察（原样）
- exit=3; std::logic_error what(): 宏步骤找不到解：状态不在这个阶段的范围里
- 完整编译/运行日志：`evidence/_raw_logs/04-2.log`

## 对应草稿
- `experiments/04-orient.json` 第 2 条
