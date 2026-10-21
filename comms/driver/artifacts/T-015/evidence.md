# T-015 验证

2026-10-21，本机 Windows。

`python scripts/check.py --skip-build`（在 `certification/driver`）退出码 0：
内容 JSON、规范图、相关题覆盖、静态分析，以及 366 个测试全过。
其中 `test/point_feedback_test.dart` 覆盖：点位命中写入练车记录且不进同步队列、
旧照片清单无 marks 时读成空、复盘里点「偏早」后点位卡显示「最近点位：偏早」、
有标注的学员照片优先于通用素材（宽 1200 与窄 420 两档都画出「我的参照物：库角」）。

桌面 debug 构建没有跑（`--skip-build`）。
截图没有落盘：测试里用 `RenderRepaintBoundary.toImage` 抓图会把测试进程卡住，
功能断言改成不抓图之后才跑完。
