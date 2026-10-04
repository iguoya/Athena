import "package:flutter/material.dart";

/// 一个语义色的四件套（ADR 0069 决策 4，阶段 2）：实心色与实心色上的字、浅底与浅底上的字。
/// Material 3 没有成功、警示、信息这类角色，做法是给每个语义一枚固定种子，经与皮肤相同的
/// [ColorScheme.fromSeed]（`fidelity`）生成——取它的 primary 四件套，所以色值与对比度由
/// 方案保证，不是手选的十六进制。
class Semantic {
  const Semantic({
    required this.color,
    required this.onColor,
    required this.container,
    required this.onContainer,
  });

  /// 实心色：图标、文字、进度条、徽章底。白字（[onColor]）在它上面够对比度。
  final Color color;
  final Color onColor;

  /// 浅底：提示条、成片的底色。上面的字用 [onContainer]。
  final Color container;
  final Color onContainer;

  factory Semantic.fromSeed(Color seed, {DynamicSchemeVariant variant = DynamicSchemeVariant.fidelity}) {
    final scheme = ColorScheme.fromSeed(seedColor: seed, dynamicSchemeVariant: variant);
    return Semantic(
      color: scheme.primary,
      onColor: scheme.onPrimary,
      container: scheme.primaryContainer,
      onContainer: scheme.onPrimaryContainer,
    );
  }
}

/// 全局语义色：含义人人认得，不随皮肤变（0058 决策 1），所以是进程内一份、不进 `Skin`。
/// 将来做暗色，只改这一层（给每个语义多生成一份 `Brightness.dark`）。
class Sem {
  Sem._();

  static final success = Semantic.fromSeed(const Color(0xFF198754));
  static final warning = Semantic.fromSeed(const Color(0xFFFFC107));
  static final info = Semantic.fromSeed(const Color(0xFF0DCAF0));

  /// 危险直接取 Material 3 的 error 角色，与组件主题里的 `error` 同一个值。
  static final danger = _danger();

  static final purple = Semantic.fromSeed(const Color(0xFF6F42C1));
  static final teal = Semantic.fromSeed(const Color(0xFF20C997));
  static final orange = Semantic.fromSeed(const Color(0xFFFD7E14));
  static final pink = Semantic.fromSeed(const Color(0xFFD63384));

  /// 次要文字、分隔性的灰：取 neutral 变体，不带色相。
  static final neutral = Semantic.fromSeed(const Color(0xFF6C757D), variant: DynamicSchemeVariant.neutral);

  /// 深色文字与线条（图表字、关闭图标）：方案的 onSurface。
  static final ink = ColorScheme.fromSeed(
    seedColor: const Color(0xFF6C757D),
    dynamicSchemeVariant: DynamicSchemeVariant.neutral,
  ).onSurface;

  static Semantic _danger() {
    final scheme = ColorScheme.fromSeed(seedColor: const Color(0xFFDC3545));
    return Semantic(
      color: scheme.error,
      onColor: scheme.onError,
      container: scheme.errorContainer,
      onContainer: scheme.onErrorContainer,
    );
  }
}
