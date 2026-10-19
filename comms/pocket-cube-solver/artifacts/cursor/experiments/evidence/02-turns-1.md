# 证据 02-turns-1 · rotate_cw 去负号

## 环境
- 临时副本：`%TEMP%\pcs-t002-experiments\02-turns`（从 `programming/pocket-cube-solver/exercise/02-turns` 复制，不改仓库）
- PATH 前置 `C:\msys64\mingw64\bin`；`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`
- 命令：`meson setup build`（首次）→ `meson compile -C build` → `build\cube-test.exe`

## 改动
- 文件：`cube.cc`
- Diff 摘要：Vec rotate_cw(... (-cross ...)) → (+ cross ...)

## 观察（原样）
- exit=1; FAIL line 55/57/59/116×10; 13 项失败
- 完整编译/运行日志：`evidence/_raw_logs/02-1.log`

## 对应草稿
- `experiments/02-turns.json` 第 1 条
