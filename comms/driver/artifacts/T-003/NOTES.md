# T-003 验收证据

四项每一步都有 `inside`（look / wrong / do）、`outside`（focus / risk）、`done`。讲解稿先念车外，再念车内。直角开灯步的参照是「视线保持在车道上，手摸开关」。侧方开灯步的错参照保留「低头找开关」。倒库第二次入库的参照是「和第一次同一对关系，从另一侧」。

场地图上理想走线用灰虚线铺全程，实走余迹用琥珀色虚线叠到当前时刻。车内格和场地图用同一种青色写同一句参照。步骤条数没变。考前分区没改。

验证：

- `certification/driver/test/subject2_test.dart`：四项字段齐全、讲解顺序、上面三句措辞、理想轨迹是实走的延长。
- `certification/driver/test/subject2_page_test.dart`：1600×2600 打开曲线行驶和倒车入库，车内格与当前步参照同屏，单步播放后步骤高亮跟着走，无布局异常。
- `python scripts/check.py driver` 退出码 0：334 项测试全过，Windows debug 构建成功（athena-driver.exe）。
