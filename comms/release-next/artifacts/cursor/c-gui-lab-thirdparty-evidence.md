# T-004 · c-gui-lab third_party 可复现实施证据（A 路线）

日期：2026-10-19。leader 拍板走 A：取回脚本 + `patches/` + `third_party.lock.json`，不动 `.gitignore`、不入库 `third_party/`，不碰 `launcher/main.js`。

## 交付物（cursor 名下）

| 路径 | 说明 |
|---|---|
| `practice/c-gui-lab/third_party.lock.json` | 每项含 `url`、`version`（tag 或完整 commit）、`sha256` |
| `practice/c-gui-lab/scripts/fetch-third-party.py` | 下载、校验 sha256（失败即退出）、只解构建子集、打补丁、建 `lvgl` 别名 |
| `practice/c-gui-lab/patches/*.patch`（6 个） | include 平铺 / 窗口标题等就地改动；相对钉死上游幂等（先清空目标再解压再 `git apply`） |

未改：`.gitignore`、`launcher/main.js`、`third_party/`（仍 gitignore）、未 `git commit`。

## 锁文件钉点

| id | version | 备注 |
|---|---|---|
| imgui | `v1.92.9` | 只解 16 个构建文件 |
| lvgl | `v9.2.2` | 只解 `src/` + `demos/` + `lvgl.h`/`lv_version.h`；脚本建 `lvgl`→`lvgl-9.2.2` junction（非 Windows 为 symlink） |
| microui | commit `0850aba…` | 核心 + demo；两份 SDL include 补丁 |
| nuklear | commit `9f775029…`（**钉 commit，非浮动 master**） | 本机原 `nuklear.h`/`overview.c` 与该 tip 一致；评估稿写「等于 v4.13.3」不准确，实施时改正。补丁仅 SDL 平铺 + 窗口标题 |
| raygui | commit `ca17a68d…`（**钉 commit**） | 用上游 `raygui.h`（含 GuiTabBar 空指针防护）；controls_test + 19 个 `style_*.h` |

## 验证步骤（任务书第二步）

工作目录：`%TEMP%\athena-t004-verify\c-gui-lab`  
（从仓库 `practice/c-gui-lab` robocopy，排除 `third_party/` 与 `build/`）。

```text
python scripts/fetch-third-party.py --dest third_party --cache %TEMP%\athena-t004-fetch-cache
# → EXIT 0；二次再跑仍 EXIT 0（不叠补丁）

set PATH=C:\msys64\ucrt64\bin;C:\Program Files\CMake\bin;%PATH%
set PKG_CONFIG_PATH=C:/msys64/ucrt64/lib/pkgconfig;C:/msys64/ucrt64/share/pkgconfig
cmake --preset ucrt64
cmake --build --preset ucrt64
# → EXIT 0
```

完整日志：`%TEMP%\athena-t004-verify\cmake-configure.log`、`cmake-build2.log`。

### 七个原生程序（文件在 + 能起）

| 程序 | 验证树大小 | 本机原 build 大小 | 冒烟（起 1.5s 后杀） |
|---|---:|---:|---|
| gtk-style.exe | 64591 | 64591 | running |
| imgui-style.exe | 1513601 | 1513601 | running |
| lvgl-style.exe | 1112426 | 1112426 | running |
| raygui-demo.exe | 409662 | 409662 | running |
| nuklear-demo.exe | 584955 | 584443 | running（差 512 B：上游 tip 相对旧本机快照的正常漂移） |
| nuklear-gdi-demo.exe | 354304 | 354304 | running |
| microui-demo.exe | 89600 | 89600 | running |

冒烟记录：`%TEMP%\athena-t004-verify\smoke.txt`。

### 别名

```text
dir /AL third_party
# lvgl [JUNCTION] → ...\third_party\lvgl-9.2.2
# 且 third_party\lvgl\lvgl.h 可读（满足 font include "lvgl/lvgl.h"）
```

## 未验证到

- CI / GitHub Actions 外网取回（本机已用同一 URL 校验 sha256；CI 集成归 leader）。
- 非 Windows 上的 symlink 路径（脚本已写 `os.name != "nt"` 分支，本机未跑）。
- 未把取回结果写回仓库内 `third_party/`（按设计不入库）。

## 使用方式（给后续 CI / 本机）

```sh
python practice/c-gui-lab/scripts/fetch-third-party.py
cmake --preset ucrt64 && cmake --build --preset ucrt64
```
