import "dart:io";

import "package:flutter/material.dart";

import "../core/content.dart";
import "../ui/look.dart";
/// 速记页的规范图（ADR 0080）：标志、手势用仓库内落库的规范图（GIF 会自己动），
/// 标线、仪表复用题库的官方题图。读取方式与 [QuestionImage] 一致——开发时读磁盘、
/// 发行包走 assets——但这里不带点开放大，放大由各页自己的玻璃浮层做。
///
/// [path] 为空或文件读不出来时退回 [fallback]（页面原有的自绘视图）：个别条目
/// （胎压、ESC 灯）题库里没有可用的图，不能留一块空白。
class CheatImage extends StatelessWidget {
  const CheatImage({
    super.key,
    required this.path,
    required this.width,
    double? height,
    this.fallback,
  }) : height = height ?? width;

  final String? path;
  final double width;
  final double height;

  /// 退回的自绘视图，收到的是可用的边长（宽高取小）。
  final Widget Function(double size)? fallback;

  Widget _fallback() {
    final build = fallback;
    if (build == null) return SizedBox(width: width, height: height);
    final side = width < height ? width : height;
    return SizedBox(width: width, height: height, child: Center(child: build(side)));
  }

  @override
  Widget build(BuildContext context) {
    final relative = path;
    if (relative == null) return _fallback();
    final resolved = ContentLoader.imagePath(relative);
    final provider = ContentLoader.imagesOnDisk
        ? FileImage(File(resolved)) as ImageProvider
        : AssetImage(resolved);
    return SizedBox(
      width: width,
      height: height,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(Bs.radius),
        child: Image(
          image: provider,
          fit: BoxFit.contain,
          filterQuality: FilterQuality.medium,
          gaplessPlayback: true,
          errorBuilder: (context, error, stack) => _fallback(),
        ),
      ),
    );
  }
}
