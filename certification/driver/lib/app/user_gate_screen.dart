import "dart:async";

import "package:flutter/material.dart";

import "../ui/glyphs.dart";
import "../core/users.dart";

/// 登录页（ADR 0075、0127）：输入名字进入，不设口令；界面里没有「同步」「服务器」这类概念。
///
/// - 名字在本机缓存里唯一命中 → 直接进。
/// - 缓存没有的名字 → 在这台电脑上新建学习者（本机段编号，1000 起）。和中心目录对上号是
///   之后检测到路由器时后台自己做的事（`LearnerBinder`），登录页不碰网络。
/// - 本机已有重名的人时要靠编号区分；「我是另一个同名的人，新建」先确认一次。
/// - 从侧栏进来时（[currentUser] 非空）可以改**当前这位**学习者自己的名字，只写本机缓存。
class UserGateScreen extends StatefulWidget {
  const UserGateScreen({
    super.key,
    required this.registry,
    required this.onPicked,
    this.onRenamed,
    this.currentUser,
    this.allowCancel = false,
    this.legacyPending = false,
  });

  final UserRegistry registry;

  /// 选定学习者。第二个参数为真表示使用者同意把旧的单用户本地记录归到他名下。
  final void Function(UserProfile profile, bool adoptLegacy, bool created) onPicked;
  final void Function(UserProfile profile)? onRenamed;
  final UserProfile? currentUser;
  final bool allowCancel;
  final bool legacyPending;

  @override
  State<UserGateScreen> createState() => _UserGateScreenState();
}

class _UserGateScreenState extends State<UserGateScreen> {
  final _name = TextEditingController();
  final _id = TextEditingController();
  late UserProfile? _current = widget.currentUser;
  bool _askId = false;
  bool _busy = false;
  String _error = "";

  @override
  void dispose() {
    _name.dispose();
    _id.dispose();
    super.dispose();
  }

  /// 包一层「转圈 + 错误显示」。
  Future<void> _guarded(Future<bool> Function() action) async {
    setState(() {
      _busy = true;
      _error = "";
    });
    try {
      await action();
    } on FormatException catch (error) {
      _fail(error.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _fail(String message) {
    if (mounted) setState(() => _error = message);
  }

  /// 登录：先看本机缓存；缓存没有的名字就在本机新建。
  Future<void> _enter() => _guarded(() async {
        UserRegistry.validateName(_name.text);
        final cached = widget.registry.matching(_name.text);
        final typedId = _askId ? _id.text.trim() : "";
        if (_askId) UserRegistry.validateId(typedId);
        if (cached.isEmpty) return _createNamed(_name.text);
        final hit = cached.length == 1 && typedId.isEmpty
            ? cached.first
            : cached.where((profile) => profile.id == typedId).firstOrNull;
        if (hit != null) {
          await _finish(hit);
          return true;
        }
        setState(() {
          _askId = true;
          _error = typedId.isEmpty ? "这台电脑上有重名的学习者，请输入你的学习者编号。" : "名字和编号对不上。";
        });
        return false;
      });

  /// 显式新建：用于「另一个人和已有的人同名」这种少见情况，先确认一次，两个人靠编号区分。
  Future<void> _create() => _guarded(() async {
        UserRegistry.validateName(_name.text);
        final name = _name.text.trim();
        if (widget.registry.matching(name).isNotEmpty) {
          final go = await _confirm(
            title: "这台电脑上已有同名的学习者",
            body: "本机已经有叫「$name」的学习者。如果你就是 ta，请点「取消」再点「进入」；"
                "如果是另一个人，仍可新建，两个人靠编号区分。",
            yes: "仍要新建",
            no: "取消",
          );
          if (!go) return false;
        }
        return _createNamed(name);
      });

  /// 在这台电脑上新建学习者：编号从 1000 起，本机自己分配、永不复用（ADR 0123、0127）。
  Future<bool> _createNamed(String name) async {
    UserRegistry.validateName(name);
    await _finish(UserProfile(id: "${widget.registry.nextLocalId()}", name: name.trim()), created: true);
    return true;
  }

  Future<bool> _confirm({required String title, required String body, required String yes, required String no}) async {
    if (!mounted) return false;
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: SizedBox(width: 440, child: Text(body, style: const TextStyle(height: 1.5))),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text(no)),
          FilledButton(onPressed: () => Navigator.of(context).pop(true), child: Text(yes)),
        ],
      ),
    );
    return result ?? false;
  }

  /// 选定：记进本机缓存；本机还躺着单用户时代的旧记录就问一句归不归他。
  Future<void> _finish(UserProfile profile, {bool created = false}) async {
    var adopt = false;
    if (widget.legacyPending) {
      adopt = await _confirm(
        title: "这台电脑上有一份旧的本地记录",
        body: "是单用户时代留下的做题记录。要归到「${profile.name}」名下吗？",
        yes: "归到我名下",
        no: "不用",
      );
    }
    final stored = widget.registry.remember(profile);
    if (!mounted) return;
    widget.onPicked(stored, adopt, created);
  }

  /// 改当前登录者自己的名字：只写本机缓存，名字只是称呼，记录认编号。
  Future<void> _renameSelf() async {
    final profile = _current;
    if (profile == null) return;
    final controller = TextEditingController(text: profile.name);
    final saved = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("改我的名字"),
        content: SizedBox(
          width: 420,
          child: TextField(
            controller: controller,
            autofocus: true,
            decoration: InputDecoration(helperText: "只改称呼；学习记录认编号 ${profile.id}，改名不受影响。"),
            onSubmitted: (value) => Navigator.of(context).pop(value),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text("取消")),
          FilledButton(onPressed: () => Navigator.of(context).pop(controller.text), child: const Text("保存")),
        ],
      ),
    );
    if (saved == null) return;
    await _guarded(() async {
      UserRegistry.validateName(saved);
      widget.registry.renamed(profile.id, saved.trim());
      final renamed = profile.withName(saved.trim());
      widget.onRenamed?.call(renamed);
      if (mounted) setState(() => _current = renamed);
      return true;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Padding(
              padding: const EdgeInsets.all(28),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("谁在学车？", style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  const Text(
                    "输入你的名字进入；第一次来的话，直接输入想用的名字就会新建。"
                    "各人的做题记录、成就和解锁进度完全分开，互不打扰。",
                    style: TextStyle(height: 1.5),
                  ),
                  const SizedBox(height: 20),
                  if (_current != null) ...[
                    Row(
                      children: [
                        const Icon(Glyph.user),
                        const SizedBox(width: 8),
                        Expanded(child: Text("现在是：${_current!.name}（编号 ${_current!.id}）")),
                        TextButton.icon(
                          onPressed: _busy ? null : _renameSelf,
                          icon: const Icon(Glyph.edit, size: 18),
                          label: const Text("改我的名字"),
                        ),
                      ],
                    ),
                    const Divider(height: 28),
                  ],
                  if (widget.registry.users.isNotEmpty) ...[
                    const Text("这台电脑上用过的", style: TextStyle(fontSize: 13, color: Color(0xFF757575))),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (final profile in widget.registry.users)
                          OutlinedButton.icon(
                            onPressed: _busy
                                ? null
                                : () => _guarded(() async {
                                      await _finish(profile);
                                      return true;
                                    }),
                            icon: const Icon(Glyph.user, size: 18),
                            label: Text(profile.name),
                          ),
                      ],
                    ),
                    const Divider(height: 28),
                  ],
                  TextField(
                    controller: _name,
                    autofocus: widget.registry.users.isEmpty,
                    decoration: const InputDecoration(labelText: "你的名字"),
                    onSubmitted: (_) => _enter(),
                  ),
                  if (_askId) ...[
                    const SizedBox(height: 12),
                    TextField(
                      controller: _id,
                      autofocus: true,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: "学习者编号",
                        helperText: "有重名的学习者：输入你第一次新建时分到的编号。",
                      ),
                      onSubmitted: (_) => _enter(),
                    ),
                  ],
                  if (_error.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(_error, style: TextStyle(color: theme.colorScheme.error, height: 1.4)),
                  ],
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      FilledButton(onPressed: _busy ? null : _enter, child: const Text("进入")),
                      const SizedBox(width: 12),
                      TextButton(onPressed: _busy ? null : _create, child: const Text("我是另一个同名的人，新建")),
                      if (widget.allowCancel) ...[
                        const SizedBox(width: 12),
                        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text("返回")),
                      ],
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
