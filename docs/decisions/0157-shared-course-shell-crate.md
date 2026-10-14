# ADR 0157：课程应用的 Tauri 壳收成一个共用 crate

- 日期：2026-10-14
- 状态：已接受（使用者 2026-10-14：「抽共用的小 crate」）
- 关系：局部修订 ADR 0132（「schema、内容块、通用应用代码的抽象待成熟再议」）——对 Rust 壳这一件事，
  成熟的证据已经够了；其余抽象照旧不做。延续 ADR 0137（`packages/` 放共用件）、0135/0140（同栈共用
  工作区），不改 0062（约束各守各的）：共用的是**代码**，不是约束来源

## 背景

数据结构、算法、408、组成原理、Linux、设计模式六个应用的 `src-tauri` 是同一个模板各抄一份：
`compiler.rs` 逐字相同，`lib.rs` 之间只差 18～20 行（应用名、环境变量名、数据目录名、课程标题）。
共约 4800 行，抄出来的问题要修六遍，漏一遍就是潜伏的不一致。已经出现的：

1. `algorithms` 与 `linux` 的 `get_app_info` 一直返回「数据结构与算法」，标题没改。
2. 只有 `design-patterns` 给编译命令加了 `-pthread`，其余五个应用的并发实验在旧 glibc 上会链接失败。
3. `load_case_source` / `save_case_source` 把前端传来的 `case_id`、`entrypoint` 直接拼进路径，
   后者是**写**文件，`entrypoint` 传 `../../..` 就能写到任意位置——六份里各有一份。
4. 同类问题在别的壳里已发生过：「最近一次作答」按自增 id 认，在四个应用里各抄各踩（见 0155、0156 相关修复）。

## 决策

1. **新增 `packages/athena-course-shell`**（Rust crate，根工作区成员）：承载整个课程壳——内容根探测、
   本地进度库（掌握度、实验状态、草稿、随堂选项）、C++ 探测与即时编译运行、clang-format、命令行入口、
   16 个 Tauri 命令。命令名与参数不变，前端无须改动。
2. **应用只传配置**：`ShellConfig { binary, title, root_env, data_dir, version, manifest_dir }`，
   外加自己的 `tauri::generate_context!()`（它读应用自己的 `tauri.conf.json` 与前端产物，必须在应用
   crate 里展开）。`lib.rs` 缩到约 20 行。`data_dir` 必须与 `app.json` 的 `progress.dir` 一致。
3. **应用仍直接依赖 `tauri-plugin-opener`**：插件在共用 crate 里注册，但 `tauri-build` 只从应用的
   直接依赖里收集插件权限，不留这条依赖，`capabilities/default.json` 里的 `opener:default` 就找不到。
   应用的 `Cargo.toml` 里写了注释，防止被当成多余依赖删掉。
4. **顺手收紧**：案例 id 与入口文件名必须是单段名字（字母、数字、`._-`，不是 `.` / `..`），
   否则拒绝；编译命令统一带 `-pthread`；`algorithms`、`linux` 的课程标题改成各自真实的名字。
5. **进度读写拆成不依赖 Tauri 的纯函数**（`store.rs`），可脱离窗口单测；命令只是薄封装。
6. **范围只到这六个应用。** `c-plus-plus`（更早一代的壳，自己的接口、编译器探测已分叉）、
   `software` / `embedded` / `gtkmm` / `snake` / `chinese-chess`（功能不同的壳）、`mathematics`（带符号引擎）、
   骨架应用（没有命令的 15 行壳）不动。将来某个应用的壳需要共用 crate 没有的命令，就离开它，
   不在共用 crate 里为单个应用加分支（延续 0046「启动器里没有按应用写的分支」的精神）。

## 后果

- 改壳的行为只改一处；新增同类课程应用的壳是一份约 20 行的配置，不再复制 800 行。
- 六个应用共享同一份命令表面：一个应用要独有的命令，就得离开共用 crate。
- 应用的 `src-tauri/src/compiler.rs` 删除；`packages/` 现在除了 `@athena/viz`（前端呈现件）还有一个
  Rust crate，REPOSITORY.md 与根 `AGENTS.md` 已同步。
- 验证：crate 自带 7 个单元测试（进度读写、旧库升级、路径校验）；六个应用的 `check.py` 全部通过；
  在虚拟显示器里启动 `athena-cs408`，确认进度库建在配置的数据目录。
- 未做：`c-plus-plus` 的编译器探测与这份仍有重复，等它的壳与共用 crate 对齐时再并。
