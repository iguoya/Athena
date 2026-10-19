# T-004 · c-gui-lab `third_party/` 可复现评估（第一步，未实施）

评估日：2026-10-19。上游已下载到本机临时目录 `%TEMP%\athena-t004-vendor\`（下载物与解压目录各自独立），与 `practice/c-gui-lab/third_party/` 做了内容比对（文本按 CRLF→LF 归一后再 hash；`git diff --ignore-cr-at-eol` 核对就地改动）。

本机 `third_party/` 合计约 **292 MB**；构建真正需要的子集约 **67 MB**。其余是死重（见下表「构建？」列）。

## 总表

| 项 | 上游（URL + 固定版本/commit） | 本地有没有改动（和上游 diff 多大） | 取回方式 | 构建？ | 体积（本机） |
|---|---|---|---|---|---|
| `imgui/` | https://github.com/ocornut/imgui `v1.92.9`（`IMGUI_VERSION` 1.92.9 / 19290） | **无内容改动**。构建用到的 16 个源/头与 tag 逐文件 SHA256 全同。本机是瘦身树（无 examples/docs/misc/fonts），相对完整 zip 少 ~265 文件 | A：按 tag 拉 zip，只解出构建文件；B：直接入库瘦身树 | 是（`imgui-style`） | 3.73 MB |
| `lvgl-9.2.2/` | https://github.com/lvgl/lvgl `v9.2.2` | **无内容改动**。`src/`（787）+ `demos/`（258）+ `lvgl.h`/`lv_version.h` 归一化后与 tag 全同；hash 差只来自 CRLF。`lv_conf.h` 在 `apps/lvgl-style/`（已入库），不在 third_party | A：按 tag 拉 zip，只留 `src/`+`demos/`+头；B：入库该子集 | 是（`lvgl-style`） | 全树 129.9 MB；构建子集 ≈ **61.1 MB** |
| `lvgl/`（9.3.0） | https://gitee.com/mirrors/lvgl.git @ `v9.3.0`（`c033a98`），整仓含 `.git` | 不参与编译；CMake 钉的是 `lvgl-9.2.2`。唯一「用处」：生成字体 `#include "lvgl/lvgl.h"`，靠 `target_include_directories(... third_party)` 解析到 `third_party/lvgl/` | **不要入库**。取回后做 `lvgl` → `lvgl-9.2.2` 的 junction/symlink（或改 include，但 `apps/` 不在 cursor 名下） | 否（死重；仅路径别名） | 149.7 MB |
| `cimgui/` | https://github.com/cimgui/cimgui @ `125f397` | 不参与构建（AGENTS.md：对照用） | 不取回 | 否 | 4.0 MB |
| `libui-ng/` | https://gitee.com/mirrors/libui-ng.git（空壳，候选未收编） | 无内容 | 不取回 | 否 | ≈0 |
| `imgui.tgz` / `lvgl.tgz` | 本机下载残留 | — | 不取回 | 否 | 2.7 MB |
| `microui/` | https://github.com/rxi/microui @ `0850aba`（`MU_VERSION` 2.02；无 release tag，用 commit） | **小补丁**：`demo/main.c`（`#define SDL_MAIN_HANDLED` + `#include <SDL.h>` 替代 SDL2/）；`demo/renderer.c`（窗口标题 `"microui demo"`）。`src/microui.{c,h}`、`atlas.inl`、`renderer.h` 与上游同。另有未参与编译的根目录副本 `microui.c/h`、本地多出的 `demo/demo.c`、缺 docs/LICENSE | A：commit zip + `patches/microui-*.patch`；B：入库瘦身目录 | 是（`microui-demo`） | 0.13 MB |
| `nuklear.h` | https://github.com/Immediate-Mode-UI/Nuklear `v4.13.3`（与当前 `master` 头文件内容同） | **无改动**（对 tag/master `--ignore-cr-at-eol` 退出码 0） | A/B 均可 | 是 | 1.13 MB |
| `nuklear_sdl2.c` | 同上仓库 `demo/sdl_opengl2/main.c` @ v4.13.3 | **小补丁**（约 5 行）：`SDL.h`/`SDL_opengl.h` 平铺；`#include "nuklear.h"`；`#include "demo/common/overview.c"`；窗口标题 | A：官方文件 + patch；B：入库已改文件 | 是（`nuklear-demo`） | 7 KB |
| `nuklear_sdl_gl2.h` | 同上 `demo/sdl_opengl2/nuklear_sdl_gl2.h` | **小补丁**：`#include <SDL.h>`；增 Alt/F1–F12 键映射（约 +15 行） | 同上 | 是 | 15 KB |
| `nuklear_gdi/` | 同上 `demo/gdi_native_nuklear/` | `main.c`：include 平铺 + 窗口标题；`nuklear_gdi.h`：增 Alt/F1–F12（约 +41 行）；`window.h` **与上游同** | 同上 | 是（`nuklear-gdi-demo`） | 0.05 MB |
| `demo/common/` | 同上 `demo/common/`（概览 demo 被 sdl2 主程序 `#include`） | `overview.c` 相对 v4.13.3 tag 有功能增量（link/chevron 等），与本地 `nuklear.h` v4.13.3/master 能力对齐；本地另有 tag 树里没有的 `overview.h`/`window.c`/`window.h`（sdl2 构建路径未直接编它们） | A：从同 commit 取 `overview.c` + 保留本地旁路头/源或写进 patch；B：整目录入库 | 是（被 include） | 0.07 MB |
| `raygui.h` | https://github.com/raysan5/raygui；本机为 **5.1-dev**，接近 `master` @ `ca17a68`（评估时 tip） | 对 **5.0 tag** 差一截（5.0→5.1-dev）；对 **master tip** 仅 `GuiTabBar` 空指针防护等约 6–10 行落后。**无 Athena 自有语义改动**，是上游时间点快照 | A：钉 commit（建议评估当日 `ca17a68` 或更新后重钉）拉 `src/raygui.h`；B：入库当前文件 | 是（`raygui-demo`） | 0.30 MB |
| `raygui_controls_test.c` | 同上 `examples/controls_test_suite/controls_test_suite.c` | **几乎只有 include 平铺**：`raygui.h` / `style_*.h` 改为同目录；相对 master 多几个 style include 行（与本机 style 文件集一致） | A：官方文件 + path patch；B：入库 | 是 | 17 KB |
| `style_*.h`（19 个） | 同上 `examples/styles/style_*.h`（`styles/<name>/` 下也有同名） | **与 master `examples/styles` 全同**（19/19） | 随 raygui 同 commit 取回 | 是 | ≈0.5 MB |

## A vs B（体积 / 改动面 / 可复现性）

| | A：取回脚本 + `patches/*.patch` + `third_party.lock.json` | B：`third_party/` 入库（建议 **瘦身子集**，非整棵 292 MB） |
|---|---|---|
| 体积进 git | 脚本+补丁+锁文件，**≪ 1 MB** | 构建必需 ≈ **67 MB**（去掉 9.3/cimgui/tarball/空壳后） |
| 改动面（cursor 名下） | `practice/c-gui-lab/scripts/fetch-third-party.py`（或同类）、`patches/*.patch`、`third_party.lock.json`（url/版本/sha256） | 同上可不写；但 **要改 `.gitignore` 去掉 `third_party/`**——任务书规定这步 **停下来由 leader 改**；`git add` 具体路径也需 leader 点头 |
| CI 可复现 | 依赖外网（GitHub）；锁文件校验 sha256；补丁必须幂等 | checkout 即有源码，**不依赖外网**；最稳 |
| 风险 | GitHub 限流/镜像挂；补丁与上游漂移要重钉 | 仓库变大；误把死重（尤其 9.3 全仓）加进去会冲到 ~200 MB+ |

## 建议（给 leader 拍板）

**值得做。**

- **首选 B-slim**：只入库构建子集（≈67 MB），死重一律不进；取回/开发机用 junction 满足 `lvgl/lvgl.h` 别名。理由：发版作业卡在 CI checkout，B 零外网、补丁面小（多数是 include 平铺），ADR 0159 允许。**动 `.gitignore` 与是否 `git add third_party/...` 等你回「做」并改 ignore。**
- **次选 A**：若你不想涨仓库体积，我按锁文件写取回脚本 + 把上表「小补丁」收成 `patches/`，CI 步骤先 fetch 再 cmake。预计改动面仍只在名下三处路径；验证按任务书第二步（临时目录无 third_party 复制 → fetch → UCRT64 七个原生程序）。

预计实施工作量（你回「做」之后）：半日级——补丁整理 +（A）脚本/sha256 或（B）瘦身拷贝清单与证据构建；不改 `launcher/main.js`，不提交。

## 证据位置

- 上游下载/解压：`%TEMP%\athena-t004-vendor\upstream\`、`extract\`
- LVGL 归一化比对脚本：`%TEMP%\athena-t004-vendor\cmp_lvgl.py`（`src`/`demos` contentDiff=0）
- 本计划：`comms/release-next/artifacts/cursor/c-gui-lab-thirdparty-plan.md`
