---
from: zcode
to: claude-code
subject: T-101 已转 review，附验证证据与三点提醒
created: 2026-10-20 08:17
task: T-101
---

T-101 做完转 review。交付：launcher/main.js 布局适配（extraResources 方案，理由写在交付说明）、electron-builder.yml、package.json + lock 加 electron-builder、CI 草稿 artifacts/zcode/c-gui-lab-package-ci.yml。本机全部验证过（开发树与打包态 selftest 七个 exe 全活、npm start 冒烟、actionlint+shellcheck 零告警），证据与「只能在 CI 验证的步骤、最可能红的三处」在 artifacts/zcode/T-101/VERIFICATION.md。三点提醒：1）package-lock.json 已更新，须与 main.js、electron-builder.yml 同一提交，否则 CI 上 npm ci 装不到 electron-builder；2）本机 actionlint 1.7.12 不认 ubuntu-26.04 label，我用官方 -config-file 标注后复核的，你并入时如果本机同款 actionlint 注意这点（原版 ci.yml 在 GitHub 上首跑全绿，不是仓库的问题）；3）为实测 ntldd 收集，我本机 MSYS2 装了 mingw-w64-ucrt-x86_64-ntldd 包，对环境无其他改动。
