import "package:flutter/material.dart";

import "look.dart";
import "recall.dart";
import "reinforce.dart";

/// 速记组右上角「练这组」按钮的颜色（ADR 0109）：随这一组相关题的作答结果变——
/// 有答错过且还没掌握的 → 红；全部掌握 → 绿；其余（没做过、只做了一部分）→ 灰。
ButtonStyle practiceButtonStyle(SymbolStatus status) {
  final color = switch (status) {
    SymbolStatus.wrong => Bs.danger,
    SymbolStatus.mastered => const Color(0xFF2ECC71),
    SymbolStatus.partial || SymbolStatus.fresh => const Color(0xFF8A939B),
  };
  return FilledButton.styleFrom(backgroundColor: color, foregroundColor: Colors.white);
}

/// 侧栏里专题与专题分组左边的状态圆（ADR 0109）：样式同 [StatusDot]（实心圆加黑心、三态色），
/// 只是小一号。红 = 答错过未掌握，绿 = 答对过，灰 = 没做过。
class TopicDot extends StatelessWidget {
  const TopicDot({super.key, required this.status, required this.tooltip, this.size = 16});

  final SymbolStatus status;
  final String tooltip;
  final double size;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      SymbolStatus.wrong => Bs.danger,
      SymbolStatus.mastered || SymbolStatus.partial => const Color(0xFF2ECC71),
      SymbolStatus.fresh => const Color(0xFFADB5BD),
    };
    return Tooltip(
      message: tooltip,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        alignment: Alignment.center,
        child: Container(
          width: size * 10 / 28,
          height: size * 10 / 28,
          decoration: const BoxDecoration(color: Colors.black, shape: BoxShape.circle),
        ),
      ),
    );
  }
}

/// 一组的「练这组」按钮状态：相关真题与这一组的自测卡**一起**看（ADR 0110）。
/// 任何一道有答错过且最近还没答对 → 红；全部最近答对 → 绿；一道没碰过 → 灰；其余（做了一部分）→ 灰。
SymbolStatus groupStatus({
  required Iterable<String> ids,
  required Set<String> mastered,
  required HistorySet histories,
}) {
  final all = ids.toList();
  if (all.isEmpty) return SymbolStatus.fresh;
  final touched = [for (final id in all) if (histories.byQuestion.containsKey(id)) id];
  if (touched.isEmpty) return SymbolStatus.fresh;
  if (touched.any((id) => (histories.byQuestion[id]?.wrong ?? 0) > 0 && !mastered.contains(id))) {
    return SymbolStatus.wrong;
  }
  return all.every(mastered.contains) ? SymbolStatus.mastered : SymbolStatus.partial;
}
