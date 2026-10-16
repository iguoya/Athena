# T-006 前半：直角转弯数据层

只交数据，页面呈现按 2026-10-16 21:55 修订留给 T-007 / T-009。

## 落地

- `content/subject2.json` 直角转弯：4 步拆成 5 步（进弯靠外侧、转弯前开转向灯、内角到位再打满、打满后看内后轮、平行就回正）。每步有 `steer` / `reference`，第 4 步 `fix` 2 条。`caution` / `tips` / `outside.risk` 不再写扣分和不合格。`rules` 与 `requirement` 的原文和 locator 未改。
- `mistakes` 只改了说法，`id` / `level` / `locator` 未动，练车打分仍按 id。
- `lib/subject2/guide.dart` 只增加 `steer` / `reference` / `skill` / `fix` 的解析。讲解念稿仍是原来的「扣分点」句式，页面组件未改。
- `lib/subject2/drill.dart` 把进弯后的直道拆成两步，总距离仍是 `13 - 4 - _cornerTurnY`，车轮轨迹不变。讲解步数必须和动画步数一致。

## 口径

- 「门把手平齐」写在 `reference`。`inside.look` 仍不写门把手、厘米、转向灯开关（原有测试禁止把死点位写进这一格）。
- 曲线、侧方、倒库未改，等这一半验收后再写。

## 验证

`python scripts/check.py driver` 退出码 0：336 个测试通过，`Built build\windows\x64\runner\Debug\athena-driver.exe`。
数据断言在 `test/subject2_test.dart`「直角转弯五步都有方向盘和参照，注意事项不复述扣分」。
没有截图：本任务不验界面。
