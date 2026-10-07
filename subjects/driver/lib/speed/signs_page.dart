import "package:flutter/material.dart";

import "recall_status.dart";
import "cheat_image.dart";
import "../ui/glyphs.dart";
import "../ui/look.dart";
import "../core/models.dart";
import "recall.dart";
import "../study/reinforce.dart";
import "recall_cards.dart";
import "sign.dart";
/// 标志速记页（ADR 0059）：标志按「禁令 / 警告 / 指示 / 指路」四组摊开，
/// 每条配一句「看到之后怎么开」，每组能直接练相关的题。内容源是
/// `content/signs.json`（文件级出处 GB 5768.2），页面只负责呈现与起练习。
/// 图用 Wikimedia Commons 上的国标标志规范图（ADR 0080），手绘 `SignView`
/// 只在图读不出来时兜底。
class SignsPage extends StatelessWidget {
  const SignsPage({
    super.key,
    required this.signs,
    required this.histories,
    required this.questions,
    required this.mastered,
    required this.onRecallAnswer,
    this.recallPage = "s1.signs",
    this.subjectLabel = "科目一",
    required this.onStartPractice,
  });

  final List<RoadSign> signs;

  /// 作答历史：格子微点由它现算——只看这一条自己的自测卡（ADR 0077 决策 3、0112）。
  final HistorySet histories;

  /// 本科目的全部题（含偏难，ADR 0112 一视同仁）：「练这组」从这里按 `Question.sign` 取题。
  final List<Question> questions;
  final Set<String> mastered;

  /// 每次自测作答记一条作答记录（ADR 0094）：首页接上，写进进度库。
  final RecallAnswerRecorder onRecallAnswer;

  /// 本专题的页键（`s1.signs` 这样，作答记录里的题号带它）与所属科目的名称（ADR 0096）。
  final String recallPage;
  final String subjectLabel;
  final void Function(List<Question> questions, String title, bool again) onStartPractice;

  /// 组的顺序与每组的形状口诀；分组本身由 json 的 `kind` 决定。
  static const _groups = [
    (kind: "prohibit", hint: "红圈在说「不许」——红圈、红杠都是禁令。"),
    (kind: "warning", hint: "黄三角在提醒「当心」——见到先减速。"),
    (kind: "indicate", hint: "蓝盘告诉你「该怎么走」——照它走不违规。"),
    (kind: "guide", hint: "蓝底白字报路名、方向和距离，提前看、提前变道。"),
    (kind: "highway", hint: "绿底白字是高速公路：出入口、服务设施、救援电话都在这一类。"),
    (kind: "tourist", hint: "棕底白字指向旅游区：看方向、看距离。"),
    (kind: "marker", hint: "红白斜杠提示障碍物：按斜杠走向从对应一侧通过。"),
  ];

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).textTheme.bodyMedium?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.45,
    );
    return ListView(
      padding: const EdgeInsets.fromLTRB(36, 28, 36, 32),
      children: [
        Row(
          children: [
            Icon(Glyph.signs, color: Bs.paper),
            SizedBox(width: 8),
            Text("标志速记", style: TextStyle(fontSize: 32, fontWeight: FontWeight.w600)),
            const SizedBox(width: 12),
            BsBadge(text: subjectLabel, color: Bs.primary),
            const Spacer(),
            FilledButton.tonalIcon(
              onPressed: () => _startRecall(context),
              icon: const Icon(Glyph.question, size: 18),
              label: const Text("自测"),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          "标志是路上的语言：先认形状，再记含义。红圈禁、黄三角警、蓝盘指、绿牌路；"
          "每张卡都写着「看到之后怎么开」，每组都能直接练相关的题。",
          style: Theme.of(context).textTheme.bodyLarge,
        ),
        for (final group in _groups)
          _signGroup(context, group.kind, group.hint, muted),
        const SizedBox(height: 24),
        Text(
          "分类与含义依据 GB 5768.2—2022《道路交通标志和标线 第 2 部分：道路交通标志》；"
          "图取自 Wikimedia Commons 的国标标志图形（公有领域），认标志以路上实物为准。",
          style: muted,
        ),
      ],
    );
  }

  RecallEntry _recallEntryOf(RoadSign sign, RecallCard card) {
    final other = sign.confuseWith == null
        ? null
        : signs.where((x) => x.id == sign.confuseWith).firstOrNull;
    return RecallEntry.fromCard(
      card,
      front: _signImage(sign, 288),
      related: [for (final q in questions) if (q.signId == sign.id) q],
      confuseView: other == null ? null : _signImage(other, 144),
    );
  }

  /// 标志规范图（ADR 0080）；文件读不出来时退回手绘标志。
  static Widget _signImage(RoadSign sign, double size) => CheatImage(
    path: sign.image,
    width: size,
    fallback: (side) => SignView(id: sign.id, size: side),
  );

  /// 自测：把没认得的标志逐张过完，收尾深链练相关题（ADR 0077、0090）。
  void _startRecall(BuildContext context) {
    final cards = {for (final c in recallCardsOfSigns(recallPage, signs)) c.id: c};
    RecallSession.show(
      context,
      onAnswer: onRecallAnswer,
      histories: histories,
      mastered: mastered,
      entries: [for (final s in signs) _recallEntryOf(s, cards[s.id]!)],
      onStartPractice: (questions) => onStartPractice(questions, "标志速记 · 自测", false),
    );
  }

  Widget _signGroup(BuildContext context, String kind, String hint, TextStyle? muted) {
    final inGroup = [for (final sign in signs) if (sign.kind == kind) sign];
    if (inGroup.isEmpty) return const SizedBox.shrink();
    final label = inGroup.first.kindLabel;
    final related = [
      for (final sign in inGroup)
        for (final q in questions)
          if (q.signId == sign.id) q,
    ];
    final pending = [for (final q in related) if (!mastered.contains(q.id)) q];
    // 组状态只看这一组的自测卡（ADR 0112）：红 = 有答错未掌握、绿 = 自测卡全部答对过、灰 = 没测完。
    final status = statusOfIds(
      ids: [for (final sign in inGroup) recallQuestionId(recallPage, sign.id)],
      histories: histories,
    );
    return Padding(
      padding: const EdgeInsets.only(top: 28),
      child: BsCard(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TopicDot(
                  status: status,
                  size: 20,
                  tooltip: switch (status) {
                    SymbolStatus.wrong => "这一组的自测卡有答错过，还没掌握",
                    SymbolStatus.mastered => "这一组的自测卡全部答对过",
                    SymbolStatus.fresh => "这一组还没测完",
                  },
                ),
                const SizedBox(width: 10),
                Text(label, style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(width: 10),
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text("${inGroup.length} 种", style: muted),
                ),
                const Spacer(),
                FilledButton.icon(
                  style: practiceButtonStyle(status),
                  onPressed: () => onStartPractice(related, "标志速记 · $label", status == SymbolStatus.mastered),
                  icon: const Icon(Glyph.practice, size: 20),
                  label: Text(
                    status == SymbolStatus.mastered
                        ? "这组已掌握 · 再练一遍"
                        : pending.isEmpty
                        ? "练这组"
                        : "练这组 ${pending.length} 题",
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(hint, style: muted),
            const SizedBox(height: 14),
            Wrap(
              spacing: 14,
              runSpacing: 14,
              children: [
                for (final sign in inGroup)
                  _SignCell(
                    sign: sign,
                    other: sign.confuseWith == null
                        ? null
                        : signs.where((s) => s.id == sign.confuseWith).firstOrNull,
                    status: statusOfIds(
                      ids: [recallQuestionId(recallPage, sign.id)],
                      histories: histories,
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// 标志速记的一个格子：手绘图 + 名称 + 「怎么开」。悬停上浮是唯一的动效，
/// 复用 BsCard 的语言与令牌（ADR 0059 决策 5）。
class _SignCell extends StatefulWidget {
  const _SignCell({required this.sign, required this.status, this.other});

  final RoadSign sign;
  final SymbolStatus status;

  /// 易混对（ADR 0077 决策 2）：浮层里双图对照。
  final RoadSign? other;

  @override
  State<_SignCell> createState() => _SignCellState();
}

class _SignCellState extends State<_SignCell> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).textTheme.bodySmall?.copyWith(
      color: Theme.of(context).colorScheme.onSurfaceVariant,
      height: 1.35,
    );
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: GestureDetector(
        onTap: () => _zoom(context),
        child: AnimatedContainer(
          duration: Bs.durFast,
          curve: Curves.easeOut,
          width: 232,
          transform: Matrix4.translationValues(0, _hover ? -2 : 0, 0),
          padding: const EdgeInsets.fromLTRB(12, 14, 12, 12),
          decoration: BoxDecoration(
            color: Bs.light,
            borderRadius: BorderRadius.circular(Bs.radius),
            boxShadow: _hover ? Bs.hoverShadow : Bs.cardShadow,
          ),
          child: Column(
            children: [
              SignsPage._signImage(widget.sign, 192),
              const SizedBox(height: 10),
              // 状态点在图标下方、条目文字左侧（ADR 0101：与行点同一套样式）。
              Row(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  StatusDot(status: widget.status),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Text(
                      widget.sign.name,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.2),
                    ),
                  ),
                ],
              ),
              if (widget.sign.band == QuestionBandColors.hot) ...[
                const SizedBox(height: 6),
                BsBadge(
                  text: "高频",
                  color: Bs.bandColor(QuestionBandColors.hot),
                  icon: Glyph.hot,
                ),
              ],
              const SizedBox(height: 6),
              Text(widget.sign.meaning, textAlign: TextAlign.center, style: muted),
            ],
          ),
        ),
      ),
    );
  }

  /// 点开看大图（ADR 0059）：速记格子里 96px 的图看细节不够，放大用玻璃浮层——
  /// 它本来就是「小面积浮层」的既定用途（ADR 0058），遮罩不遮暗，速记页还在身后。
  void _zoom(BuildContext context) {
    showDialog<void>(
      context: context,
      barrierColor: Colors.transparent,
      builder: (dialogContext) => Dialog(
        insetPadding: const EdgeInsets.all(32),
        backgroundColor: Colors.transparent,
        child: GlassPanel(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SignsPage._signImage(widget.sign, 320),
              const SizedBox(height: 14),
              Text(
                widget.sign.name,
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Text(
                widget.sign.meaning,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 16,
                  height: 1.45,
                  color: Theme.of(dialogContext).colorScheme.onSurfaceVariant,
                ),
              ),
              if (widget.other != null) ...[
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Bs.light,
                    borderRadius: BorderRadius.circular(Bs.radius),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      SignsPage._signImage(widget.other!, 144),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text("容易混：${widget.other!.name}", style: Theme.of(dialogContext).textTheme.titleSmall),
                            const SizedBox(height: 4),
                            Text(widget.sign.confuseNote ?? "", style: TextStyle(
                              fontSize: 14,
                              height: 1.45,
                              color: Theme.of(dialogContext).colorScheme.onSurfaceVariant,
                            )),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
