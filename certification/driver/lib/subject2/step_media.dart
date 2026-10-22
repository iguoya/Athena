/// 真实图 / 动图上叠参照物标记（ADR 0130）。没有素材就什么都不画。
library;

import "dart:io";
import "dart:math" as math;

import "package:flutter/material.dart";

import "../core/content.dart";
import "guide.dart";

class StepMedia extends StatelessWidget {
  const StepMedia({super.key, required this.shots});

  final List<StepShot> shots;

  @override
  Widget build(BuildContext context) {
    if (shots.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final shot in shots) ...[
          _ShotFrame(shot: shot),
          const SizedBox(height: 12),
        ],
      ],
    );
  }
}

class _ShotFrame extends StatefulWidget {
  const _ShotFrame({required this.shot});

  final StepShot shot;

  @override
  State<_ShotFrame> createState() => _ShotFrameState();
}

class _ShotFrameState extends State<_ShotFrame> {
  ImageProvider? _provider;
  ImageStream? _stream;
  ImageStreamListener? _listener;
  Size? _imageSize;
  bool _missing = false;

  /// 第一帧 build 之前只改字段。监听在 didChangeDependencies 里可能同步回调，
  /// 那时 setState 会撞上正在进行的构建。
  bool _painted = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _listen();
  }

  @override
  void didUpdateWidget(_ShotFrame old) {
    super.didUpdateWidget(old);
    if (old.shot.file != widget.shot.file) _listen();
  }

  @override
  void dispose() {
    if (_listener != null) _stream?.removeListener(_listener!);
    super.dispose();
  }

  void _apply(VoidCallback change) {
    change();
    if (_painted && mounted) setState(() {});
  }

  void _listen() {
    final file = widget.shot.file;
    if (file.isEmpty) {
      _apply(() {
        _missing = true;
        _provider = null;
        _imageSize = null;
      });
      return;
    }
    final resolved = ContentLoader.imagePath(file);
    if (ContentLoader.imagesOnDisk && !File(resolved).existsSync()) {
      _apply(() {
        _missing = true;
        _provider = null;
        _imageSize = null;
      });
      return;
    }
    final ImageProvider provider = ContentLoader.imagesOnDisk
        ? FileImage(File(resolved))
        : AssetImage(resolved);
    if (provider == _provider) return;
    if (_listener != null) _stream?.removeListener(_listener!);
    _provider = provider;
    _imageSize = null;
    _missing = false;
    _listener = ImageStreamListener(
      (info, _) {
        if (!mounted) return;
        _apply(() {
          _imageSize = Size(
            info.image.width.toDouble(),
            info.image.height.toDouble(),
          );
          _missing = false;
        });
      },
      onError: (exception, stack) {
        if (!mounted) return;
        _apply(() => _missing = true);
      },
    );
    _stream = provider.resolve(createLocalImageConfiguration(context));
    _stream!.addListener(_listener!);
  }

  void _zoom() {
    final provider = _provider;
    if (provider == null || _missing) return;
    showDialog<void>(
      context: context,
      builder: (context) => Dialog(
        child: InteractiveViewer(
          child: Image(image: provider, fit: BoxFit.contain),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    _painted = true;
    final theme = Theme.of(context);
    final shot = widget.shot;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        GestureDetector(
          onTap: _zoom,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final box = Size(constraints.maxWidth, 240);
              final fitted = fittedImageRect(box, _imageSize ?? box);
              return SizedBox(
                width: box.width,
                height: box.height,
                child: Stack(
                  children: [
                    if (_provider != null && !_missing)
                      Positioned.fromRect(
                        rect: fitted,
                        child: Image(
                          image: _provider!,
                          fit: BoxFit.fill,
                          gaplessPlayback: true,
                          errorBuilder: (context, error, stack) =>
                              const SizedBox.shrink(),
                        ),
                      ),
                    if (_missing) const Center(child: Text("这张图读不到")),
                    Positioned.fill(
                      child: CustomPaint(
                        painter: StepMarkPainter(
                          shot.marks,
                          fitted,
                          theme.textTheme.bodyMedium?.fontFamily,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 6),
        Text(
          [
            if (shot.view.isNotEmpty) shot.view,
            if (shot.caption.isNotEmpty) shot.caption,
          ].join(" · "),
          style: theme.textTheme.bodyMedium,
        ),
        if (shot.note.isNotEmpty)
          Text(
            shot.note,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
      ],
    );
  }
}

class StepMarkPainter extends CustomPainter {
  StepMarkPainter(this.marks, this.image, this.fontFamily);

  final List<StepMark> marks;
  final Rect image;
  final String? fontFamily;

  @override
  void paint(Canvas canvas, Size size) {
    final line = Paint()
      ..color = const Color(0xFFFFF3B0)
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
    for (final mark in marks) {
      if (mark.type == "point") {
        final at = mark.at(image);
        canvas.drawCircle(at, 8, line);
        _label(canvas, mark.label, at + const Offset(12, -10));
      } else {
        final a = mark.from(image);
        final b = mark.to(image);
        canvas.drawLine(a, b, line);
        if (mark.type == "arrow") _arrow(canvas, a, b, line);
        _label(canvas, mark.label, (a + b) / 2 + const Offset(0, -14));
      }
    }
  }

  void _arrow(Canvas canvas, Offset a, Offset b, Paint paint) {
    final angle = math.atan2(b.dy - a.dy, b.dx - a.dx);
    const len = 10.0;
    final left = Offset(
      b.dx - len * math.cos(angle - 0.5),
      b.dy - len * math.sin(angle - 0.5),
    );
    final right = Offset(
      b.dx - len * math.cos(angle + 0.5),
      b.dy - len * math.sin(angle + 0.5),
    );
    canvas.drawLine(b, left, paint);
    canvas.drawLine(b, right, paint);
  }

  void _label(Canvas canvas, String text, Offset at) {
    if (text.isEmpty) return;
    final painter = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          color: Color(0xFF1A1A1A),
          fontSize: 13,
          fontWeight: FontWeight.w700,
          fontFamily: fontFamily,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    final rect = Rect.fromLTWH(
      at.dx - 4,
      at.dy - 2,
      painter.width + 8,
      painter.height + 4,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(rect, const Radius.circular(3)),
      Paint()..color = const Color(0xFFFFF3B0),
    );
    painter.paint(canvas, at);
  }

  @override
  bool shouldRepaint(StepMarkPainter old) =>
      old.image != image || old.marks != marks || old.fontFamily != fontFamily;
}
