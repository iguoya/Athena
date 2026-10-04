import "dart:io";
import "dart:isolate";
import "dart:math";

import "package:file_selector/file_selector.dart";
import "package:flutter/material.dart";
import "package:image/image.dart" as img;
import "package:path/path.dart" as p;

import "glyphs.dart";
import "guide.dart";
import "look.dart";
import "progress.dart";

/// 个人点位卡（ADR 0037）：每一项的每一步，只写使用者自己验证过的点位——
/// 教练怎么说、自己在车里实测怎样。应用只给骨架，不给通用点位（ADR 0036）。

const pointTemplate = "看哪里：\n看到什么时：\n做什么：";

/// 照片长边缩到这么多像素，JPEG 质量 80：每张两三百 KB，随仓库走不至于太重。
const pointPhotoEdge = 1280;

/// 把一张照片缩图后存进 [dir]/<项目>/，返回相对 [dir] 的路径。解码和缩放在后台 isolate 里做。
Future<String> importPointPhoto(String source, String dir, String itemId, int step, {DateTime? now}) async {
  final bytes = await File(source).readAsBytes();
  final jpg = await Isolate.run(() {
    // 扩展名对、内容坏的文件，解码器会抛 RangeError 之类的底层错误，统一换成一句人话。
    img.Image? decoded;
    try {
      decoded = img.decodeImage(bytes);
    } catch (_) {
      decoded = null;
    }
    if (decoded == null) throw const FormatException("认不出这张图片的格式（支持 JPG、PNG、WebP、BMP、GIF）");
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
  final stamp = "${t.year}${_two(t.month)}${_two(t.day)}-${_two(t.hour)}${_two(t.minute)}${_two(t.second)}${t.millisecond.toString().padLeft(3, "0")}";
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
  });

  final GuideItem item;
  final ProgressStore store;
  final Map<(String, int), PointNote> notes;
  final List<PointPhoto> photos;
  final Future<void> Function() onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (var i = 0; i < item.steps.length; i++)
          PointCard(
            item: item,
            step: i,
            store: store,
            note: notes[(item.id, i)],
            photos: [for (final ph in photos) if (ph.itemId == item.id && ph.step == i) ph],
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
    final controller = TextEditingController(text: note == null || note!.text.trim().isEmpty ? pointTemplate : note!.text);
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
          TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text("取消")),
          FilledButton(onPressed: () => Navigator.of(context).pop(controller.text), child: const Text("保存")),
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
    const images = XTypeGroup(label: "图片", extensions: ["jpg", "jpeg", "png", "webp", "bmp", "gif"]);
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
          TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text("取消")),
          FilledButton(onPressed: () => Navigator.of(context).pop(controller.text), child: const Text("加进点位卡")),
        ],
      ),
    );
    if (caption == null) return;
    try {
      final file = await importPointPhoto(picked.path, ProgressStore.pointsDir, item.id, step);
      await store.addPointPhoto(item.id, step, file, caption.trim());
      await onChanged();
    } on Exception catch (error) {
      if (!context.mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text("照片没加上"),
          content: Text("$error"),
          actions: [FilledButton(onPressed: () => Navigator.of(context).pop(), child: const Text("知道了"))],
        ),
      );
    }
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
                constraints: const BoxConstraints(maxWidth: 1000, maxHeight: 640),
                child: Image.file(File(p.join(ProgressStore.pointsDir, photo.file)), errorBuilder: _missing),
              ),
              const SizedBox(height: 10),
              if (photo.caption.isNotEmpty) Text(photo.caption, style: Theme.of(context).textTheme.bodyLarge),
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
                  FilledButton(onPressed: () => Navigator.of(context).pop(false), child: const Text("关闭")),
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

  static Widget _missing(BuildContext context, Object error, StackTrace? stack) => Container(
        width: 160,
        height: 100,
        color: Bs.light,
        alignment: Alignment.center,
        padding: const EdgeInsets.all(8),
        child: const Text("照片文件不在这台机器上\n（用 launcher sync 同步仓库）", textAlign: TextAlign.center, style: TextStyle(fontSize: 12)),
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
                child: Text("第 ${step + 1} 步 · ${item.steps[step].title}", style: theme.textTheme.titleSmall),
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
            style: theme.textTheme.bodyLarge?.copyWith(color: text.isEmpty ? Bs.secondary : null),
          ),
          if (photos.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                for (final photo in photos)
                  InkWell(
                    onTap: () => _view(context, photo),
                    child: SizedBox(
                      width: 180,
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
                            Text(photo.caption, maxLines: 2, overflow: TextOverflow.ellipsis, style: theme.textTheme.bodySmall),
                        ],
                      ),
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
