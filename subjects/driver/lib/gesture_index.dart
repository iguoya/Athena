import "models.dart";

/// 手势题 → 手势动作的反向索引（ADR 0078）：`ContentLoader` 读 `gestures.json` 时填。
/// 做题台答完手势题后，据此在右栏放上这个动作的动画——静态题图只有两个姿势，
/// 看不出完整的动作流程。
class GestureIndex {
  GestureIndex._();

  static Map<String, (String id, String name)> _byQuestion = const {};

  static void load(Iterable<TrafficGesture> gestures) {
    _byQuestion = {
      for (final g in gestures)
        for (final q in g.questions) q: (g.id, g.name),
    };
  }

  /// 这道题对应的手势动作；不是手势题返回 null。
  static (String id, String name)? of(String questionId) => _byQuestion[questionId];
}
