import "dart:async";

import "package:flutter/material.dart";

import "api_config_screen.dart";
import "../ui/glyphs.dart";
import "../core/user_directory.dart";
import "../core/users.dart";
/// 登录页（ADR 0075）：输入名字进入，不设口令。
///
/// - 名字在本机缓存里唯一命中 → 直接进，不联网（离线可用）。
/// - 否则问中心目录：找到一个就进；没有就直接新建并进入（ADR 0078，不再有单独的新建步骤）；
///   不止一个同名就再问**学习者编号**。
/// - 目录连不上（ADR 0123）：出现「在这台电脑上新建（不同步）」——建一个本地学习者
///   （编号 1000 起，只存本机、永不参与同步）；已在本机的人照常直接进。
/// - 从侧栏进来时（[currentUser] 非空）可以改**当前这位**学习者自己的名字，改不了别人的；
///   本地学习者改名只写本机缓存。
///
/// 中心目录是权威，新建与异地首次登录要联网（ADR 0074 决策 3）。离开内网时要先在「同步设置」
/// 里填外网访问凭据（ADR 0077），页面底部有入口。
class UserGateScreen extends StatefulWidget {
  const UserGateScreen({
    super.key,
    required this.registry,
    required this.directoryFactory,
    required this.onPicked,
    this.onRenamed,
    this.currentUser,
    this.allowCancel = false,
    this.legacyPending = false,
  });

  final UserRegistry registry;
  final UserDirectory Function() directoryFactory;

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

  /// 目录这次没连上（ADR 0123）：显示「在这台电脑上新建（不同步）」的出路，
  /// 直到有一步不再碰壁为止。
  bool _unavailable = false;

  @override
  void dispose() {
    _name.dispose();
    _id.dispose();
    super.dispose();
  }

  /// 包一层「转圈 + 错误显示」。动作返回**是否成功**：只有成功才清掉「目录连不上」的
  /// 标志——取消、早退都不算成功，本地新建的出路保持可见，用户还能再点。
  Future<void> _guarded(Future<bool> Function() action) async {
    setState(() {
      _busy = true;
      _error = "";
    });
    var unavailable = _unavailable;
    try {
      if (await action()) unavailable = false;
    } on FormatException catch (error) {
      _fail(error.message);
    } on DirectoryUnavailable catch (error) {
      unavailable = true;
      _fail("现在连不上学习者目录（${error.detail}）。已在这台电脑上用过的学习者可以直接点上面的名字，"
          "或者点「在这台电脑上新建（不同步）」先用起来，记录只存在这台电脑上。");
    } on DirectoryRejected catch (error) {
      _fail(error.message);
    } on DirectoryNotFound {
      // 兜底：任何一步抛出没人处理的「找不到」，也要让人看见，不能静默。
      _fail("目录里没有找到这位学习者。");
    } on DirectoryAmbiguous {
      _fail("有重名的学习者，请再输入学习者编号。");
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _unavailable = unavailable;
        });
      }
    }
  }

  void _fail(String message) {
    if (mounted) setState(() => _error = message);
  }

  /// 登录：先看本机缓存，再问中心。返回是否进入了（或到了需要再问编号等中间状态——
  /// 中间状态不算成功，保持「目录连不上」标志原样）。
  Future<bool> _enter() async {
    var entered = false;
    await _guarded(() async {
      UserRegistry.validateName(_name.text);
      final cached = widget.registry.matching(_name.text);
      final typedId = _askId ? _id.text.trim() : "";
      if (_askId) UserRegistry.validateId(typedId);
      if (cached.isNotEmpty) {
        final hit = cached.length == 1 && typedId.isEmpty
            ? cached.first
            : cached.where((profile) => profile.id == typedId).firstOrNull;
        if (hit != null) {
          await _finish(hit);
          return entered = true;
        }
        if (typedId.isEmpty) {
          // 本机就有重名的人：只能靠编号区分。
          setState(() {
            _askId = true;
            _error = "这台电脑上有重名的学习者，请输入你的学习者编号。";
          });
          return false;
        }
        // 缓存里没有这一对：交给中心判断（也许是在别的电脑上建的同名者）。
      }
      final directory = widget.directoryFactory();
      try {
        await _finish(await directory.login(_name.text, id: typedId));
        return entered = true;
      } on DirectoryNotFound {
        if (_askId) {
          _fail("名字和编号对不上。编号是第一次新建时告诉你的那个数字。");
          return false;
        }
        // 一个都没有：直接新建并进入，不再让人另找「新建」按钮（ADR 0078）。输错了也无妨：
        // 换回正确的名字，或者在侧栏把这个名字改对。
        await _finish(await directory.register(_name.text), created: true);
        return entered = true;
      } on DirectoryAmbiguous {
        setState(() {
          _askId = true;
          _error = "有重名的学习者，请输入你的学习者编号。";
        });
        return false;
      }
    });
    return entered;
  }

  /// 显式新建：用于「另一个人和已有的人同名」这种少见情况；名字已有人用时先确认一次。
  /// 平时不用点它——输入没人用过的名字点「进入」就会自动新建（ADR 0078）。
  Future<bool> _create() async {
    var created = false;
    await _guarded(() async {
      UserRegistry.validateName(_name.text);
      final directory = widget.directoryFactory();
      var exists = widget.registry.matching(_name.text).isNotEmpty;
      if (!exists) {
        try {
          await directory.login(_name.text);
          exists = true;
        } on DirectoryAmbiguous {
          exists = true;
        } on DirectoryNotFound {
          // 没人叫这个名字，直接新建。
        }
      }
      if (exists) {
        final go = await _confirm(
          title: "已有同名的学习者",
          body: "已经有叫「${_name.text.trim()}」的学习者。如果你就是 ta，请点「取消」再点「进入」；"
              "如果是另一个人，仍可新建，之后在别的电脑登录会多问一次编号。",
          yes: "仍要新建",
          no: "取消",
        );
        if (!go) return false;
      }
      await _finish(await directory.register(_name.text), created: true);
      return created = true;
    });
    return created;
  }

  /// 目录连不上时的出路（ADR 0123）：在这台电脑上新建一个本地学习者——编号从 1000 起
  /// （中心目录只发 1～999，两个段永不重叠），只存本机、永不参与同步。以后想同步，
  /// 等连得上目录时用中心目录的学习者，两边不互迁。本机已有**本地段**同名时先确认：
  /// 服务器段的同名者编号不同，不构成歧义。取消不算成功，出路按钮保持可见。
  Future<bool> _createLocal() async {
    var created = false;
    await _guarded(() async {
      UserRegistry.validateName(_name.text);
      final name = _name.text.trim();
      if (widget.registry.matching(name).any((profile) => profile.isLocal)) {
        final go = await _confirm(
          title: "这台电脑上已有同名的本地学习者",
          body: "本机已经有一个叫「$name」的本地学习者。仍要新建的话，两个人靠编号区分。",
          yes: "仍要新建",
          no: "取消",
        );
        if (!go) return false;
      }
      await _finish(UserProfile(id: "${widget.registry.nextLocalId()}", name: name), created: true);
      return created = true;
    });
    return created;
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

  Future<void> _configure() async {
    await Navigator.of(context).push<ApiConfigScreenResult>(
      MaterialPageRoute(builder: (context) => const ApiConfigScreen(allowSkip: true), fullscreenDialog: true),
    );
    if (mounted) setState(() => _error = "");
  }

  /// 改当前登录者自己的名字：服务端也校验，改别人的会被拒（ADR 0075 决策 5）。
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
      // 本地学习者（ADR 0123）：权威就是本机缓存，改名不问中心目录；不算「目录可达」，
      // 不清那个标志。
      if (profile.isLocal) {
        widget.registry.renamed(profile.id, saved.trim());
        final renamedLocal = profile.withName(saved.trim());
        widget.onRenamed?.call(renamedLocal);
        if (mounted) setState(() => _current = renamedLocal);
        return false;
      }
      final directory = widget.directoryFactory();
      final renamed = await directory.rename(profile.id, saved);
      widget.registry.renamed(renamed.id, renamed.name);
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
                    "输入你的名字进入；第一次来的话，直接输入想用的名字，会自动新建。各人的做题记录、成就和解锁进度完全分开，互不打扰。",
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
                  if (_unavailable) ...[
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: _busy ? null : _createLocal,
                      child: const Text("在这台电脑上新建（不同步）"),
                    ),
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
                      const Spacer(),
                      TextButton(onPressed: _configure, child: const Text("同步设置")),
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
