# T-002 验收证据

手册顶部有「C2 怎么开科目二」，四项卡片按先易后难：直角转弯 → 曲线行驶 → 侧方停车 → 倒车入库。

顺序断言在 `certification/driver/test/subject2_page_test.dart`（比较四张卡的屏幕位置）和 `test/subject2_test.dart`（`c2.order` 与条款在摘录里存在）。考试顺序仍是 `items` 数组：倒库 → 侧方 → 曲线 → 直角，考前默演文案未改。

`python scripts/check.py driver` 退出码 0：330 项测试全过，Windows debug 构建成功。
