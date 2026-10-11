# ADR 0133：异构技术栈准入——栈是教学内容才允许异构，纯内容应用默认 Tauri 2 + React

- 日期：2026-10-11
- 状态：已接受（tiger 2026-10-11：批准评审建议落地——「异构技术栈需要一条准入规则，而不是『不趋同』一刀切」）
- 关系：补充 [ADR 0047](0047-cross-platform-first.md)、[ADR 0049](0049-cost-benefit-cross-platform.md)（跨平台是成本收益判断）；
  与 [ADR 0130](0130-shared-build-and-schema.md)（构建共享、schema 共享）正交——共享层管公共代码放哪，本篇管每个应用选什么栈；
  应用级先例：ascent ADR 0066（本应用不趋同）

## 背景

1. 仓库现有 7 种以上技术栈并存：Flutter（driver）、Tauri 2 + React（多数）、Tauri 2 + Vue
   （math-tools）、GTK4/gtkmm + Meson + Blueprint（c-plus-plus、pocket_cube）、Qt6/QML + CMake
   （machine）、Electron（c-gui-lab）、Swift（launcher/macos）。
2. 「不趋同」此前只是各应用的自选（如 ascent ADR 0066），仓库级没有立过边界。结果有两个：
   合理的异构（gtkmm 教 GTK4、c-gui-lab 对比 GUI 框架——栈即内容）与无教学收益的异构
   （machine 教 C 语言，Qt 不是教学内容，却让仓库多养一套 Qt6/QML + CMake 构建与检查体系）
   在规则层面无法区分。
3. 新应用（OS 系列、AI 系列）已经全部用 Tauri 2 + React 的壳复制起步，事实上的默认栈已经形成，
   但「什么时候允许不跟默认」没有成文，下一个应用仍可能凭感觉带进新栈。

## 决策

1. **准入规则：满足下列任一条，应用才允许采用 Tauri 2 + React 之外的技术栈**——
   - **（a）栈是教学内容或教学实验对象**：gtkmm（教 GTK4/gtkmm）、machine（C 与机器，汇编与
     内存布局的实验需要贴近裸机的工具链）、c-gui-lab（GUI 框架对比本身就是实验内容）。
   - **（b）栈是教学内容生态的原生载体**：c-plus-plus（教 C++，GTK 是 C++ 生态的原生 GUI）、
     pocket_cube（C++ 实践）。
   - **（c）存量成熟投入，不追溯**：driver（Flutter，功能与内容已深，迁移成本远超收益，
     按 0049 的成本收益判断留在 Flutter）。
2. **其余应用默认 Tauri 2 + React**（TypeScript + Vite，壳从现有应用复制）；0130 的共享层
   机制落地后，壳的公共部分从共享层取。
3. **machine 的 Qt6 记为历史例外**：按本规则它不属于任何准入条目（教 C，Qt 既非内容也非
   C 生态载体），但不强制迁移——重建一套 Tauri 壳的收益抵不上停摆成本。此例外**不得作为
   新应用效仿的先例**。
4. **新增应用立栈时，准入判断写进该应用的立项 ADR**：走哪条准入、或为什么跟默认，一句话
   说清；说不清就默认。

## 后果

- 「不趋同」从「各自随意」变成「有边界的自由」：异构的每一处都有教学理由可查，
  新应用不再可能凭感觉带入第五种前端框架。
- machine 若未来大改（实验台重做等），迁移 Tauri 壳可一并评估；在那之前 Qt 构建链照常维护。
- 对 0130 共享层的期望随之明确：共享层服务的默认栈只有一个形态（Tauri 2 + React），
  不需要为每种栈各留一套公共件。
