# T-008 俯视图画布

新文件，没有改 `subject2.dart`、`guide.dart`、`home.dart`、`content/subject2.json`。
没有做 `step_flow.dart`，也没有做侧方、曲线、直角的草表（T-009）。

## 落地

- `lib/subject2/field_map.dart`：`FieldMapStep`、`FieldMapPainter`、`FieldMap`。
  画库位线框、控制线虚线、带朝向的车身矩形、方向盘圆盘、参照点高亮。不写步骤文字。
- `reverseParkSketch`：倒车入库 7 步。右倒车尾先进库，入库后车头朝路、方向盘回正；
  第 7 步是左倒的镜像（方向盘向左）。位姿是相对关系，量级对齐现有倒库场地。
- 测试 `test/field_map_test.dart`：7 步数据、七步都能画完、换步 `shouldRepaint`。

## 截图

- `reverse-step-0.png` 起点，车在右侧控制线内、车头朝右
- `reverse-step-2.png` 右倒中，车尾朝库角，两个库角高亮
- `reverse-step-4.png` 入库停住，车头朝路，库后点高亮
- `reverse-step-6.png` 左倒中，方向与右倒相反

## 验证

`python scripts/check.py driver` 退出码 0：343 个测试通过，`Built build\windows\x64\runner\Debug\athena-driver.exe`。
