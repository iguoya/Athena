/// 科目二项目页的「操作过程」主视图（T-009，承接 T-007 骨架）。
///
/// 一个项目一个过程：步骤条选步，当前步一屏讲完——车外/车内双视角两栏（车外 =
/// 位置与要防的结果，车内 = 视线与手脚），方向盘与参照是主角行，「偏了怎么修」
/// 是警示区。项目页不出题，题目归「注意事项」章节。
///
/// 受控组件：当前步序号由页面持有，俯视图（T-008 FieldMap）与文字随同一序号联动。
library;

import "package:flutter/material.dart";

import "guide.dart";

/// 双视角并排的最小宽度；以下堆叠为纵向。
const _kDualViewBreakpoint = 680.0;

class StepFlow extends StatelessWidget {
  const StepFlow({
    super.key,
    required this.steps,
    required this.current,
    required this.onStepChanged,
  });

  final List<GuideStep> steps;

  /// 当前步下标，由页面持有（俯视图共用）。
  final int current;
  final ValueChanged<int> onStepChanged;

  GuideStep get _step => steps[current];

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _StepBar(
          count: steps.length,
          current: current,
          onSelected: onStepChanged,
        ),
        const SizedBox(height: 12),
        Text(
          "第 ${current + 1} 步 · ${_step.title}",
          style: theme.textTheme.titleMedium,
        ),
        if (_step.body.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(_step.body),
          ),
        const SizedBox(height: 12),
        _DualView(step: _step),
        _Primary(label: "方向盘", text: _step.steer, emphasis: true),
        _Primary(label: "参照", text: _step.reference),
        if (_step.skill.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              "技巧：${_step.skill}",
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
        _FixBlock(fixes: _step.fix),
        if (_step.done.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text("做完：${_step.done}"),
          ),
        _CautionBar(step: _step),
      ],
    );
  }
}

class _StepBar extends StatelessWidget {
  const _StepBar({
    required this.count,
    required this.current,
    required this.onSelected,
  });

  final int count;
  final int current;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 40,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: SegmentedButton<int>(
          segments: [
            for (var i = 0; i < count; i++)
              ButtonSegment(value: i, label: Text("${i + 1}")),
          ],
          selected: {current},
          onSelectionChanged: (selection) => onSelected(selection.first),
          showSelectedIcon: false,
        ),
      ),
    );
  }
}

/// 车外/车内双视角：宽屏并排、窄屏堆叠。不出屏是硬要求（T-005 口径）。
class _DualView extends StatelessWidget {
  const _DualView({required this.step});

  final GuideStep step;

  @override
  Widget build(BuildContext context) {
    final inside = step.inside;
    final outside = step.outside;
    if (inside == null && outside == null) return const SizedBox.shrink();
    return LayoutBuilder(
      builder: (context, constraints) {
        final wide = constraints.maxWidth >= _kDualViewBreakpoint;
        final cards = [
          if (outside != null) _OutsideCard(outside: outside),
          if (inside != null) _InsideCard(inside: inside),
        ];
        if (wide) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (var i = 0; i < cards.length; i++) ...[
                if (i > 0) const SizedBox(width: 12),
                Expanded(child: cards[i]),
              ],
            ],
          );
        }
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            for (var i = 0; i < cards.length; i++) ...[
              if (i > 0) const SizedBox(height: 12),
              cards[i],
            ],
          ],
        );
      },
    );
  }
}

class _OutsideCard extends StatelessWidget {
  const _OutsideCard({required this.outside});

  final StepOutside outside;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("车外 · 盯哪", style: theme.textTheme.labelLarge),
            const SizedBox(height: 6),
            Text(outside.focus),
            if (outside.risk.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  "要防：${outside.risk}",
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// 车内一格用深色面板，与 drill 的 CabinPanel 同一语言：人在车里看的是暗的。
class _InsideCard extends StatelessWidget {
  const _InsideCard({required this.inside});

  final StepInside inside;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF263238),
        borderRadius: BorderRadius.circular(10),
      ),
      child: DefaultTextStyle.merge(
        style: const TextStyle(color: Colors.white),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "车内 · 手脚",
              style: theme.textTheme.labelLarge?.copyWith(
                color: Colors.white70,
              ),
            ),
            const SizedBox(height: 6),
            Text("盯：${inside.look}"),
            Text("做：${inside.action}"),
            if (inside.wrong.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  "别按这个来：${inside.wrong}",
                  style: const TextStyle(color: Color(0xFFFFAB91)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// 主角行：方向盘与参照（T-006 口径，页面上的主角）。没写的字段不占版面。
class _Primary extends StatelessWidget {
  const _Primary({
    required this.label,
    required this.text,
    this.emphasis = false,
  });

  final String label;
  final String text;
  final bool emphasis;

  @override
  Widget build(BuildContext context) {
    if (text.isEmpty) return const SizedBox.shrink();
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: emphasis
                  ? theme.colorScheme.primaryContainer
                  : theme.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(label),
          ),
          const SizedBox(width: 8),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}

/// 「偏了怎么修」：迹象 → 动作，警示色（可救），与「别按这个来」的 danger 红区分。
class _FixBlock extends StatelessWidget {
  const _FixBlock({required this.fixes});

  final List<StepFix> fixes;

  @override
  Widget build(BuildContext context) {
    if (fixes.isEmpty) return const SizedBox.shrink();
    final theme = Theme.of(context);
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: theme.colorScheme.tertiaryContainer,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("偏了怎么修", style: theme.textTheme.labelLarge),
          for (final f in fixes)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text("迹象：${f.sign} → ${f.action}"),
            ),
        ],
      ),
    );
  }
}

/// 实战注意红条；条款号以角标随行，不展开成条款列表（评判归「注意事项」章节）。
class _CautionBar extends StatelessWidget {
  const _CautionBar({required this.step});

  final GuideStep step;

  @override
  Widget build(BuildContext context) {
    if (step.caution.isEmpty) return const SizedBox.shrink();
    final theme = Theme.of(context);
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: theme.colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(10),
      ),
      child: DefaultTextStyle.merge(
        style: TextStyle(color: theme.colorScheme.onErrorContainer),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("注意", style: theme.textTheme.labelLarge),
            const SizedBox(height: 4),
            Text(step.caution),
            if (step.cautionLocators.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  step.cautionLocators.join(" · "),
                  style: theme.textTheme.bodySmall,
                ),
              ),
          ],
        ),
      ),
    );
  }
}
