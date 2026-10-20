# T-101 交付说明与验证记录

日期：2026-10-20 · 执行：zcode（release-next 舱）

## 改动清单（均未提交 git，建议同一提交落地）

| 文件 | 改动 |
|---|---|
| `practice/c-gui-lab/launcher/main.js` | 布局适配：`NATIVE_ROOT` 按 `app.isPackaged` 二分（开发树 `build/apps`、打包态 `resources/native`）；`APPS` 表改存相对 `bin` 路径；`childEnv()` 打包态不再往 PATH 塞 MSYS2；`--selftest` 对七个唯一 exe 逐个「spawn → 4 秒存活判定 → 杀掉」，两种布局同一逻辑 |
| `practice/c-gui-lab/electron-builder.yml` | 新建。NSIS 一档 x64；`extraResources` 把 `build/apps` 按白名单（`**/*.exe`、`**/*.dll`、`**/*.css`）放 `resources/native`；CMake 中间产物（CMakeFiles/、`liblvgl_ext.a`、imgui.ini）不进包 |
| `practice/c-gui-lab/package.json` | devDependencies 加 `electron-builder ^26.0.0`；新增 `npm run dist` / `dist:dir` 脚本。**package-lock.json 已随之更新，须与上面两个文件同提交** |
| `comms/release-next/artifacts/zcode/c-gui-lab-package-ci.yml` | CI 作业草稿（一个 job），给 leader 并入 ci.yml |

## 关键选择与理由：extraResources 而非 asarUnpack

exe 不能从 asar 里 spawn。asarUnpack 的做法是把 `build/**` 连中间产物一起收进
asar 再解出（Cursor 草稿的路线），files 过滤规则要逐项排除；extraResources 直接
按白名单把干净的运行时子集放到 `resources/native`，目录结构自定，不受 asar 打包
规则与 node_modules 提升影响。开发树与打包态的差异收在 `main.js` 顶部一处判定。

## 本机验证（证据在本目录）

1. 开发树 `npx electron . --selftest`：七个 exe 全部 spawn 存活，`SELFTEST-OK`，
   exit 0 → `selftest-dev-tree.log`。
2. `npm start` 入口冒烟（`--shot` 自动截屏退出）：画廊 UI 正常、状态栏「就绪」、
   probe 全亮 → `smoke-dev-tree.png`。
3. 打包态：`ntldd -R` 收集 69 个 UCRT64 运行库 DLL 到各 exe 旁（本机为此装了
   `mingw-w64-ucrt-x86_64-ntldd`）→ `npx electron-builder --dir` 出
   `dist/win-unpacked/`（`resources/native/<名>/<名>.exe + style.css + DLL`，无
   CMake 垃圾）→ 以**滤掉全部 MSYS2 路径的 PATH** 启动
   `win-unpacked/athena-c-gui-lab.exe --selftest`：七个 exe 全部旁路加载 DLL 起
   进程，`SELFTEST-OK`，exit 0 → `selftest-packaged.log`。
4. actionlint（1.7.12 + shellcheck 集成）对「草稿拼进 ci.yml 的副本」与原版
   ci.yml 均零告警。注：本机 actionlint 数据不含 `ubuntu-26.04` runner label，
   用官方 `-config-file` 标注该 label 后复核（配置在 /tmp，不进仓库）。
5. 应用自身 `scripts/check.py`：结构 + Electron 语法 + 七程序增量编译全部通过
   （lvgl_style.c 的 const 警告为存量，非本次引入）。

## 只能在 CI 验证的步骤

1. 干净 runner（无 `C:\msys64`）上从锁文件 fetch third_party 并编译——本机
   third_party 是既有状态，fetch 脚本在 ci.yml 的 `c-gui-lab-native` 一档已验过；
2. NSIS 安装包在本机的产出（`--dir` 只出了免安装目录；NSIS 打包步骤要下载
   NSIS 工具链）；
3. 静默安装（`/S /D=`）与安装目录布局；
4. 安装态 selftest 在无 MSYS2 机器上的完整链路——本机第 3 条已用过滤 PATH 的
   方式近似，但本机系统仍装有 MSYS2，并非真·干净机。

## 最可能红的三处

1. **DLL 收集复查**：`ntldd` 报 `not found` 的除 `ext-ms-*`/`api-ms-*` 外若出现
   别的（新依赖引入的 API set 或误报），复查步骤会拦下打包——届时按报错的具体
   DLL 名加白或补包，不要直接放宽检查。
2. **NSIS 静默安装的 `/D=`**：参数含空格即解析失败。现用 `RUNNER_TEMP`
   （`D:\a\_temp`，无空格）；若有人改目录，别用含空格路径。
3. **electron-builder 下载**（NSIS 工具链 / icons bundle）：runner 网络抖动会
   超时，重跑即可；`timeout-minutes: 90` 已留余量。

另注：DLL 缺失时 Windows 可能弹「缺 DLL」对话框让进程挂着存活，selftest 的
「存活」判定对这种情形有误判可能——这正是 CI 草稿把 ntldd 复查放在打包时兜住
的原因（本机打出的包已过复查）。
