import "dart:io";
import "dart:isolate";
import "dart:math";

import "package:file_selector/file_selector.dart";
import "package:flutter/material.dart";
import "package:image/image.dart" as img;
import "package:path/path.dart" as p;

import "../ui/glyphs.dart";
import "guide.dart";
import "../ui/look.dart";
import "../core/progress.dart";
import "step_media.dart";

/// 个人点位卡（ADR 0037）：每一项的每一步，只写使用者自己验证过的点位——
/// 教练怎么说、自己在车里实测怎样。应用只给骨架，不给通用点位（ADR 0036）。

const pointTemplate = "看哪里：\n看到什么时：\n做什么：";

/// 这一项最近几次标过的点位，新的在前，最多 [limit] 次。没标的把不算。
List<String> recentPointHits(Iterable<DrillRun> runs, String itemId, {int limit = 3}) {
  final out = <String>[];
  for (final run in runs) {
    if (run.itemId != itemId) continue;
    final label = pointHitLabel(run.pointHit);
    if (label == null) continue;
    out.add(label);
    if (out.length >= limit) break;
  }
  return out;
}

/// 一项一条标定引导：停在哪、看哪里、拍什么、写什么。不给通用点位（ADR 0036）。
String calibrationGuide(String itemId) => switch (itemId) {
  "reverse" => "停在起点，座椅固定。看后视镜里库口和车尾，拍下这一眼。按三行骨架写下你自己的点。",
  "parallel" => "停在库的左前方。看右后视镜里车身和库线的缝，拍下这一眼。只写这辆车、这个座位下成立的关系。",
  "curve" => "进弯前把车停稳。看挡风玻璃里车头角和边线，拍下这一眼。只写你实测过的。",
  "corner" => "转弯前停住。看后视镜或车头和内角，拍下这一眼。按「看哪里 / 看到什么时 / 做什么」写下你自己的点。",
  _ => "停稳，看这一步的参照，拍下这一眼，按三行骨架写下你验证过的点。",
};

/// 照片长边缩到这么多像素，JPEG 质量 80：每张两三百 KB，随仓库走不至于太重。
const pointPhotoEdge = 1280;

/// 把一张照片缩图后存进 [dir]/<项目>/，返回相对 [dir] 的路径。解码和缩放在后台 isolate 里做。
Future<String> importPointPhoto(
  String source,
  String dir,
  String itemId,
  int step, {
  DateTime? now,
}) async {
  final bytes = await File(source).readAsBytes();
  final jpg = await Isolate.run(() {
    // 扩展名对、内容坏的文件，解码器会抛 RangeError 之类的底层错误，统一换成一句人话。
    img.Image? decoded;
    try {
      decoded = img.decodeImage(bytes);
    } catch (_) {
      decoded = null;
    }
    if (decoded == null) {
      throw const FormatException("认不出这张图片的格式（支持 JPG、PNG、WebP、BMP、GIF）");
    }
    final upright = img.bakeOrientation(decoded);
    final longest = max(upright.width, upright.height);
    final resized = longest <= pointPhotoEdge
        ? upright
        : img.copyResize(
            upright,
            width: upright.width >= upright.height ? pointPhotoEdge : null,
            height: upright.height > upright.width ? pointPhotoEdge : null,
            interpolation: img.Interpolation.average,
          );
    return img.encodeJpg(resized, quality: 80);
  });
  final t = now ?? DateTime.now();
  final stamp =
      "${t.year}${_two(t.month)}${_two(t.day)}-${_two(t.hour)}${_two(t.minute)}${_two(t.second)}${t.millisecond.toString().padLeft(3, "0")}";
  final relative = "$itemId/${step + 1}-$stamp.jpg";
  final file = File(p.join(dir, relative));
  await file.parent.create(recursive: true);
  await file.writeAsBytes(jpg);
  return relative;
}

String _two(int v) => v.toString().padLeft(2, "0");

/// 单项页里的「我的点位卡」：每一步一张卡。
class PointCards extends StatelessWidget {
  const PointCards({
    super.key,
    required this.item,
    required this.store,
    required this.notes,
    required this.photos,
    required this.onChanged,
    this.stepKeys,
    this.recentHits = const [],
  });

  final GuideItem item;
  final ProgressStore store;
  final Map<(String, int), PointNote> notes;
  final List<PointPhoto> photos;
  final Future<void> Function() onChanged;

  /// 每一步一张卡的键，供「去标定」滚到这一步。
  final List<GlobalKey>? stepKeys;

  /// 这一项最近几次点位命中（准 / 偏早 / 偏晚），新的在前。
  final List<String> recentHits;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (recentHits.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text("最近点位：${recentHits.join(" · ")}"),
          ),
        for (var i = 0; i < item.steps.length; i++)
          PointCard(
            key: stepKeys != null && i < stepKeys!.length ? stepKeys![i] : null,
            item: item,
            step: i,
            store: store,
            note: notes[(item.id, i)],
            photos: [
              for (final ph in photos)
                if (ph.itemId == item.id && ph.step == i) ph,
            ],
            onChanged: onChanged,
          ),
      ],
    );
  }
}

class PointCard extends StatelessWidget {
  const PointCard({
    super.key,
    required this.item,
    required this.step,
    required this.store,
    required this.note,
    required this.photos,
    required this.onChanged,
    this.compact = false,
  });

  final GuideItem item;
  final int step;
  final ProgressStore store;
  final PointNote? note;
  final List<PointPhoto> photos;
  final Future<void> Function() onChanged;

  /// 默演对照时只读展示，不给编辑按钮。
  final bool compact;

  bool get empty => (note?.text.trim().isEmpty ?? true) && photos.isEmpty;

  Future<void> _edit(BuildContext context) async {
    final controller = TextEditingController(
      text: note == null || note!.text.trim().isEmpty
          ? pointTemplate
          : note!.text,
    );
    final saved = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("第 ${step + 1} 步 · ${item.steps[step].title}"),
        content: SizedBox(
          width: 640,
          child: TextField(
            controller: controller,
            autofocus: true,
            minLines: 5,
            maxLines: 12,
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              helperText: "只写你自己验证过的：教练怎么说、你在车里实测怎样。点位跟车型、座椅、考场绑定。",
              helperMaxLines: 2,
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text("取消"),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(controller.text),
            child: const Text("保存"),
          ),
        ],
      ),
    );
    if (saved == null) return;
    final text = saved.trim() == pointTemplate.trim() ? "" : saved.trim();
    if (text == (note?.text ?? "")) return;
    await store.savePointNote(item.id, step, text);
    await onChanged();
  }

  Future<void> _addPhoto(BuildContext context) async {
    const images = XTypeGroup(
      label: "图片",
      extensions: ["jpg", "jpeg", "png", "webp", "bmp", "gif"],
    );
    final picked = await openFile(acceptedTypeGroups: const [images]);
    if (picked == null || !context.mounted) return;
    final controller = TextEditingController();
    final caption = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("给这张照片写一句说明"),
        content: SizedBox(
          width: 520,
          child: TextField(
            controller: controller,
            autofocus: true,
            decoration: const InputDecoration(hintText: "例如：右后视镜下沿刚碰到库角时打满方向"),
            onSubmitted: (v) => Navigator.of(context).pop(v),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text("取消"),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(controller.text),
            child: const Text("加进点位卡"),
          ),
        ],
      ),
    );
    if (caption == null) return;
    try {
      final file = await importPointPhoto(
        picked.path,
        ProgressStore.pointsDir,
        item.id,
        step,
      );
      await store.addPointPhoto(item.id, step, file, caption.trim());
      await onChanged();
    } on Exception catch (error) {
      if (!context.mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text("照片没加上"),
          content: Text("$error"),
          actions: [
            FilledButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text("知道了"),
            ),
          ],
        ),
      );
    }
  }

  Future<void> _annotate(BuildContext context, PointPhoto photo) async {
    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => Dialog(
        child: PointMarkEditor(
          photo: photo,
          onSave: (marks) => store.savePointPhotoMarks(photo.file, marks),
        ),
      ),
    );
    if (saved == true) await onChanged();
  }

  Future<void> _view(BuildContext context, PointPhoto photo) async {
    final remove = await showDialog<bool>(
      context: context,
      builder: (context) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ConstrainedBox(
                constraints: const BoxConstraints(
                  maxWidth: 1000,
                  maxHeight: 640,
                ),
                child: Image.file(
                  File(p.join(ProgressStore.pointsDir, photo.file)),
                  errorBuilder: _missing,
                ),
              ),
              const SizedBox(height: 10),
              if (photo.caption.isNotEmpty)
                Text(
                  photo.caption,
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (!compact)
                    TextButton.icon(
                      onPressed: () => Navigator.of(context).pop(true),
                      icon: Icon(Glyph.delete, color: Bs.danger),
                      label: Text("删掉这张", style: TextStyle(color: Bs.danger)),
                    ),
                  const SizedBox(width: 8),
                  FilledButton(
                    onPressed: () => Navigator.of(context).pop(false),
                    child: const Text("关闭"),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
    if (remove != true) return;
    await store.removePointPhoto(photo);
    await onChanged();
  }

  static Widget _missing(
    BuildContext context,
    Object error,
    StackTrace? stack,
  ) => Container(
    width: 160,
    height: 100,
    color: Bs.light,
    alignment: Alignment.center,
    padding: const EdgeInsets.all(8),
    child: const Text(
      "照片文件不在这台机器上\n（用 launcher sync 同步仓库）",
      textAlign: TextAlign.center,
      style: TextStyle(fontSize: 12),
    ),
  );

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final text = note?.text.trim() ?? "";
    return BsCard(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.fromLTRB(14, 10, 10, 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  "第 ${step + 1} 步 · ${item.steps[step].title}",
                  style: theme.textTheme.titleSmall,
                ),
              ),
              if (!compact) ...[
                TextButton.icon(
                  onPressed: () => _edit(context),
                  icon: const Icon(Glyph.edit, size: 18),
                  label: Text(text.isEmpty ? "写点位" : "改"),
                ),
                TextButton.icon(
                  onPressed: () => _addPhoto(context),
                  icon: const Icon(Glyph.addPhoto, size: 18),
                  label: const Text("加照片"),
                ),
              ],
            ],
          ),
          Text(
            text.isEmpty ? "还没写。看哪里？看到什么时？做什么？" : text,
            style: theme.textTheme.bodyLarge?.copyWith(
              color: text.isEmpty ? Bs.secondary : null,
            ),
          ),
          if (photos.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                for (final photo in photos)
                  SizedBox(
                    width: 180,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        InkWell(
                          onTap: () => _view(context, photo),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(4),
                                child: Image.file(
                                  File(p.join(ProgressStore.pointsDir, photo.file)),
                                  height: 110,
                                  width: 180,
                                  fit: BoxFit.cover,
                                  cacheWidth: 360,
                                  errorBuilder: _missing,
                                ),
                              ),
                              if (photo.caption.isNotEmpty)
                                Text(
                                  photo.caption,
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: theme.textTheme.bodySmall,
                                ),
                            ],
                          ),
                        ),
                        if (!compact)
                          TextButton(
                            onPressed: () => _annotate(context, photo),
                            child: Text(photo.marks.isEmpty ? "标注参照物" : "改标注"),
                          ),
                      ],
                    ),
                  ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

/// 参照下面的个人点位。没写就给「去标定」，不弹窗。
class InlinePoint extends StatelessWidget {
  const InlinePoint({
    super.key,
    required this.note,
    required this.photos,
    required this.onCalibrate,
  });

  final PointNote? note;
  final List<PointPhoto> photos;
  final VoidCallback onCalibrate;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final text = note?.text.trim() ?? "";
    if (text.isEmpty && photos.isEmpty) {
      return Align(
        alignment: Alignment.centerLeft,
        child: TextButton.icon(
          onPressed: onCalibrate,
          icon: const Icon(Glyph.pointCard),
          label: const Text("去标定"),
        ),
      );
    }
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (text.isNotEmpty)
            Text("我的点位：$text", style: theme.textTheme.bodyMedium),
          if (photos.isNotEmpty) ...[
            const SizedBox(height: 8),
            SizedBox(
              height: 72,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: [
                  for (final photo in photos)
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: Image.file(
                          File(p.join(ProgressStore.pointsDir, photo.file)),
                          height: 72,
                          width: 96,
                          fit: BoxFit.cover,
                          cacheWidth: 192,
                          errorBuilder: PointCard._missing,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// 项目页这一步的图：有学员自己的标注照就用它，否则用通用素材。
class StepVisual extends StatelessWidget {
  const StepVisual({super.key, required this.media, required this.annotated});

  final List<StepShot> media;
  final List<PointPhoto> annotated;

  @override
  Widget build(BuildContext context) {
    final mine = [for (final photo in annotated) if (photo.marks.isNotEmpty) photo];
    if (mine.isNotEmpty) return AnnotatedPointPhoto(photo: mine.last);
    if (media.isEmpty) return const SizedBox.shrink();
    return StepMedia(shots: media);
  }
}

/// 学员照片叠上自己点的参照。优先于通用素材出现在项目页。
class AnnotatedPointPhoto extends StatelessWidget {
  const AnnotatedPointPhoto({super.key, required this.photo});

  final PointPhoto photo;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final labels = [for (final mark in photo.marks) mark.label].where((s) => s.isNotEmpty).join("、");
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text("我的参照物${labels.isEmpty ? "" : "：$labels"}", style: theme.textTheme.titleSmall),
        const SizedBox(height: 6),
        _MarkedFile(photo: photo, height: 240),
        if (photo.caption.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(photo.caption, style: theme.textTheme.bodyMedium),
          ),
      ],
    );
  }
}

/// 在自己的照片上点选位置并加标签。标签写在输入框里，再点画面落一个点。
class PointMarkEditor extends StatefulWidget {
  const PointMarkEditor({super.key, required this.photo, required this.onSave});

  final PointPhoto photo;
  final Future<void> Function(List<PhotoMark> marks) onSave;

  @override
  State<PointMarkEditor> createState() => _PointMarkEditorState();
}

class _PointMarkEditorState extends State<PointMarkEditor> {
  late final _label = TextEditingController();
  late var _marks = [...widget.photo.marks];
  var _saving = false;

  @override
  void dispose() {
    _label.dispose();
    super.dispose();
  }

  void _drop(Offset local, Size box) {
    final label = _label.text.trim();
    if (label.isEmpty) return;
    final fitted = fittedImageRect(box, box);
    if (!fitted.contains(local) || fitted.width == 0 || fitted.height == 0) return;
    final x = ((local.dx - fitted.left) / fitted.width).clamp(0.0, 1.0);
    final y = ((local.dy - fitted.top) / fitted.height).clamp(0.0, 1.0);
    setState(() {
      _marks = [
        ..._marks,
        PhotoMark(type: "point", label: label, x: x, y: y),
      ];
    });
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    await widget.onSave(_marks);
    if (mounted) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: SizedBox(
        width: 720,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text("点选参照物", style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text("先写标签，再点照片上的位置。点一次加一个。", style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 8),
            TextField(
              key: const ValueKey("photo-mark-label"),
              controller: _label,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: "标签",
                hintText: "例如：库角",
              ),
            ),
            const SizedBox(height: 8),
            _MarkedFile(
              photo: widget.photo,
              height: 360,
              marks: _marks,
              onTap: _drop,
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                if (_marks.isNotEmpty)
                  TextButton(
                    onPressed: _saving
                        ? null
                        : () => setState(() => _marks = _marks.sublist(0, _marks.length - 1)),
                    child: const Text("撤销上一个"),
                  ),
                TextButton(
                  onPressed: _saving ? null : () => Navigator.of(context).pop(false),
                  child: const Text("取消"),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  key: const ValueKey("photo-mark-save"),
                  onPressed: _saving ? null : _save,
                  child: const Text("保存标注"),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MarkedFile extends StatelessWidget {
  const _MarkedFile({
    required this.photo,
    required this.height,
    this.marks,
    this.onTap,
  });

  final PointPhoto photo;
  final double height;
  final List<PhotoMark>? marks;
  final void Function(Offset local, Size box)? onTap;

  @override
  Widget build(BuildContext context) {
    final shown = marks ?? photo.marks;
    final stepMarks = [
      for (final mark in shown) StepMark(type: mark.type, label: mark.label, x: mark.x, y: mark.y),
    ];
    return LayoutBuilder(
      builder: (context, constraints) {
        final box = Size(constraints.maxWidth, height);
        final fitted = fittedImageRect(box, box);
        return GestureDetector(
          key: const ValueKey("photo-mark-surface"),
          onTapUp: onTap == null ? null : (details) => onTap!(details.localPosition, box),
          child: SizedBox(
            width: box.width,
            height: box.height,
            child: Stack(
              children: [
                Positioned.fromRect(
                  rect: fitted,
                  child: Image.file(
                    File(p.join(ProgressStore.pointsDir, photo.file)),
                    fit: BoxFit.fill,
                    errorBuilder: PointCard._missing,
                  ),
                ),
                Positioned.fill(
                  child: CustomPaint(
                    painter: StepMarkPainter(
                      stepMarks,
                      fitted,
                      Theme.of(context).textTheme.bodyMedium?.fontFamily,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
