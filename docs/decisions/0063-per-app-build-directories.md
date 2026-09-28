# ADR 0063：同类可共享构建缓存，异构必须隔离

- 日期：2026-09-25
- 状态：已接受
- 修订：ADR 0046 第 5 条（共享 `CARGO_TARGET_DIR` 的范围）

## 背景

ADR 0046 让编排器给**每一次**启动都注入仓库级 `.cache/cargo-target`。三个 Tauri
应用（dsa / english / mathematics）依赖版本相同，共享能少编几 GB，首次打开第二个
应用几乎白拿——这仍然成立。

但「一律注入」越界了：Flutter、GTK/Meson、Qt/CMake 与 Tauri **不是同一类构建**。
给驾考学习也设 `CARGO_TARGET_DIR` 无意义；更糟的是 Windows 上把 MinGW、MSVC、Qt
DLL 目录塞进无关应用的 PATH，会让 CMake/Meson 捡错编译器，一份坏缓存拖垮别的项目。

判据不是「省不省磁盘」，而是**是不是同一类构建、共享会不会更快且不串味**。

## 决策

1. **同类、且共享能加快开发 → 可以共享一份构建缓存。** 当前实现：目录下有
   `src-tauri/` 的应用（三个 Tauri 学习应用）继续共用
   `<repo>/.cache/cargo-target`。外层已 export `CARGO_TARGET_DIR` 时编排器不覆盖。
2. **异构项目不得共享构建目录，也不得共用会污染对方的工具链 PATH。**
   各用自己目录下的 `build/`、`target/`、Flutter `build/` 等；Windows 上：
   - 只有 `dev.prepare` 调用 `meson` 的才加 MSYS2 UCRT64；
   - 只有声明了 `CMAKE_PREFIX_PATH` 的才加 Qt 运行库目录；
   - 只有带 `pubspec.yaml` 的才把 `~/flutter/bin` 补进 PATH。
3. **以后出现第二组「同类」**（例如又一批同版依赖的 Tauri，或明确同工具链的
   小项目），可以再开一组共享缓存；**不要**把不同族塞进同一目录。

## 后果

- Tauri 三应用仍享受共享 cargo 缓存；彼此编的时候仍可能抢同一把文件锁——这是
  同类共享的已知代价，可接受。
- 驾考 / C++ / 北极星 / C 语言不再被塞进 Tauri 的 cargo target，也不再误看见
  对方的编译器前缀。
- ADR 0046 其余条款不变；第 5 条收窄为「仅对同类 Tauri 注入」，不再写成全局默认。
