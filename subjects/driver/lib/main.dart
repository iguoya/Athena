import "dart:async";
import "dart:convert";
import "dart:io";

import "package:flutter/foundation.dart";
import "package:flutter/material.dart";
import "package:flutter_localizations/flutter_localizations.dart";
import "package:http/http.dart" as http;
import "package:path/path.dart" as p;
import "package:window_manager/window_manager.dart";

import "content.dart";
import "glyphs.dart";
import "home.dart";
import "look.dart";
import "models.dart";
import "progress.dart";
import "sync.dart";
import "user_directory.dart";
import "users.dart";

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // 27 寸 4K 这类高分屏上，Flutter 默认给的窗口尺寸太小，每次都要手动最大化——
  // 桌面端（macOS/Windows/Linux）启动时直接最大化，不留这道手续。
  // 原生 runner 早就把窗口建好并显示出来了（见 windows/runner/main.cpp），
  // 这里不用再调 show()——那一步会把刚设好的最大化状态重置回原始大小。
  await windowManager.ensureInitialized();
  await windowManager.maximize();
  runApp(const BootstrapGate());
}

/// 启动门：本地进度库必开成功（ADR 0070，做题不以「连上中心」为前提）；先认出是谁
/// （ADR 0071、0075：输入名字登录，本机缓存里的人离线也能直接进）；API 没配置时可以先
/// 离线用——队列会等令牌配好后自然补发。
class BootstrapGate extends StatefulWidget {
  const BootstrapGate({super.key});

  @override
  State<BootstrapGate> createState() => _BootstrapGateState();
}

class _BootstrapGateState extends State<BootstrapGate> {
  String _stage = "loading";
  String _message = "";
  Bank? _bank;
  ProgressStore? _store;
  SyncEngine? _engine;
  UserProfile? _profile;
  UserRegistry? _registry;

  /// 应用内的导航器：启动门自己在 MaterialApp 之上，拿不到 Navigator，
  /// 侧栏触发的换人与配置页都经它 push。
  final _navigatorKey = GlobalKey<NavigatorState>();

  /// 本机还有单用户时代的 local.db 等着认领（登录后询问归到谁名下）。
  bool _legacyPending = false;

  @override
  void initState() {
    super.initState();
    _tryOpen();
  }

  Future<void> _tryOpen() async {
    setState(() => _stage = "loading");
    try {
      _bank ??= await ContentLoader.load();
      final registry = _registry ??= UserRegistry.load();
      if (registry.users.isEmpty) {
        setState(() {
          _legacyPending = File(p.join(ProgressStore.userDataDir(), "local.db")).existsSync();
          _stage = "first-user";
        });
        return;
      }
      // 缓存里只有一个人，不打扰直接进；多人记住上次用的（ADR 0071 决策 7）。
      if (registry.users.length == 1) {
        await _openAs(registry.users.first);
      } else if (registry.last != null && registry.byId(registry.last!) != null) {
        await _openAs(registry.byId(registry.last!)!);
      } else {
        setState(() => _stage = "pick");
      }
    } catch (error) {
      setState(() {
        _message = "$error";
        _stage = "error";
      });
    }
  }

  /// 登录页选定学习者后进入应用；[adoptLegacy] 为真时先把旧的单用户本地库归到他名下。
  Future<void> _enter(UserProfile profile, bool adoptLegacy) async {
    if (adoptLegacy) {
      ProgressStore.adoptLegacyFiles(profile.id);
      _legacyPending = false;
    }
    await _openAs(profile);
  }

  /// 以某个学习者身份打开应用：换人就是换一份空白历史（ADR 0071）。
  /// 身份认编号（ADR 0075）；侧栏显示的是名字。
  Future<void> _openAs(UserProfile profile) async {
    try {
      _engine?.stop();
      await _store?.close();
      final store = await ProgressStore.open(user: profile.id);
      _registry?.setLast(profile.id);
      final config = ApiConfig.load();
      _engine = config == null ? null : _startEngine(store, _bank!, config, profile.id);
      setState(() {
        _store = store;
        _profile = profile;
        _stage = "ready";
      });
    } catch (error) {
      setState(() {
        _message = "$error";
        _stage = "error";
      });
    }
  }

  SyncEngine _startEngine(ProgressStore store, Bank bank, ApiConfig config, String user) {
    return SyncEngine(
      store: store,
      config: config,
      user: user,
      draftKeys: [for (final subject in bank.curriculum.subjects) "${subject.id}.exam"],
    )..start();
  }

  /// 登录页每次动作时现取：配置页保存令牌后，同一个页面立刻就能用。
  UserDirectory? _directory() {
    final config = ApiConfig.load();
    return config == null ? null : HttpUserDirectory(config);
  }

  /// 名字被改后同步侧栏显示（只能改当前登录的人，ADR 0075 决策 5）。
  void _onRenamed(UserProfile profile) {
    if (_profile?.id != profile.id) return;
    setState(() => _profile = profile);
  }

  /// 侧栏用户行点进来：换人，或改当前学习者自己的名字。
  Future<void> _switchUser() async {
    final registry = _registry;
    final navigator = _navigatorKey.currentState;
    if (registry == null || navigator == null) return;
    final picked = await navigator.push<UserProfile>(
      MaterialPageRoute(
        builder: (context) => UserGateScreen(
          registry: registry,
          directoryFactory: _directory,
          currentUser: _profile,
          allowCancel: true,
          onPicked: (profile, _) => Navigator.of(context).pop(profile),
          onRenamed: _onRenamed,
        ),
        fullscreenDialog: true,
      ),
    );
    if (picked == null || picked.id == _profile?.id || !mounted) return;
    await _openAs(picked);
  }

  /// 侧栏同步行点进来重新配置：保存后换引擎重启同步，跳过则维持现状。
  Future<void> _openConfig() async {
    final navigator = _navigatorKey.currentState;
    if (navigator == null) return;
    final config = await navigator.push<ApiConfigScreenResult>(
      MaterialPageRoute(
        builder: (context) => const ApiConfigScreen(allowSkip: true),
        fullscreenDialog: true,
      ),
    );
    if (config == null || !mounted) return;
    final bank = _bank;
    final store = _store;
    final profile = _profile;
    if (bank == null || store == null || profile == null) return;
    _engine?.stop();
    _engine = _startEngine(store, bank, config.config, profile.id);
    setState(() {});
  }

  @override
  void dispose() {
    _engine?.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return switch (_stage) {
      "first-user" || "pick" => MaterialApp(
          title: "驾考学习",
          debugShowCheckedModeBanner: false,
          locale: const Locale("zh", "CN"),
          supportedLocales: const [Locale("zh", "CN")],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: UserGateScreen(
            registry: _registry!,
            directoryFactory: _directory,
            legacyPending: _legacyPending,
            onPicked: _enter,
          ),
        ),
      "config" => MaterialApp(
          title: "驾考学习",
          debugShowCheckedModeBanner: false,
          home: ApiConfigScreen(
            onSavedDirect: (config) {
              final bank = _bank;
              final store = _store;
              final profile = _profile;
              if (bank == null || store == null || profile == null) return;
              _engine = _startEngine(store, bank, config, profile.id);
              setState(() => _stage = "ready");
            },
          ),
        ),
      "error" => BootstrapErrorApp(message: _message),
      "ready" => DriverApp(
          bank: _bank!,
          store: _store!,
          currentUser: _profile!.name,
          navigatorKey: _navigatorKey,
          onSwitchUser: _switchUser,
          syncStatus: _engine?.status,
          onOpenConfig: _openConfig,
        ),
      _ => const MaterialApp(
          title: "驾考学习",
          home: Scaffold(body: Center(child: CircularProgressIndicator())),
        ),
    };
  }
}

/// 登录页（ADR 0075）：输入名字进入，不设口令。
///
/// - 名字在本机缓存里唯一命中 → 直接进，不联网（离线可用）。
/// - 否则问中心目录：找到一个就进；没有就提示可以新建；不止一个同名就再问**学习者编号**。
/// - 新建是单独的动作：名字已有人用时先确认，新建后显著展示分到的编号。
/// - 从侧栏进来时（[currentUser] 非空）可以改**当前这位**学习者自己的名字，改不了别人的。
///
/// 目录是权威，新建与异地首次登录要联网（ADR 0074 决策 3）；[directoryFactory] 返回 null
/// 表示还没配设备令牌，页面给出配置入口。
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
  final UserDirectory? Function() directoryFactory;

  /// 选定学习者。第二个参数为真表示使用者同意把旧的单用户本地记录归到他名下。
  final void Function(UserProfile profile, bool adoptLegacy) onPicked;
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

  static const _needSetup = "现在连不上学习者目录：还没有配置同步设备令牌。新建学习者和在新电脑上登录都要联网，请先配置同步。";

  Future<void> _guarded(Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _error = "";
    });
    try {
      await action();
    } on FormatException catch (error) {
      _fail(error.message);
    } on DirectoryUnavailable catch (error) {
      _fail("现在连不上学习者目录（${error.detail}）。已在这台电脑上用过的学习者可以直接点上面的名字。");
    } on DirectoryRejected catch (error) {
      _fail(error.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _fail(String message) {
    if (mounted) setState(() => _error = message);
  }

  /// 登录：先看本机缓存，再问中心。
  Future<void> _enter() async {
    await _guarded(() async {
      UserRegistry.validateName(_name.text);
      final cached = widget.registry.matching(_name.text);
      final typedId = _askId ? _id.text.trim() : "";
      if (_askId) UserRegistry.validateId(typedId);
      if (cached.isNotEmpty) {
        final hit = cached.length == 1 && typedId.isEmpty
            ? cached.first
            : cached.where((profile) => profile.id == typedId).firstOrNull;
        if (hit != null) return _finish(hit);
        if (typedId.isEmpty) {
          // 本机就有重名的人：只能靠编号区分。
          setState(() {
            _askId = true;
            _error = "这台电脑上有重名的学习者，请输入你的学习者编号。";
          });
          return;
        }
        // 缓存里没有这一对：交给中心判断（也许是在别的电脑上建的同名者）。
      }
      final directory = widget.directoryFactory();
      if (directory == null) return _fail(_needSetup);
      try {
        await _finish(await directory.login(_name.text, id: typedId));
      } on DirectoryNotFound {
        _fail(_askId
            ? "名字和编号对不上。编号是第一次新建时告诉你的那个数字。"
            : "没有叫「${_name.text.trim()}」的学习者。第一次来的话，点「新建学习者」。");
      } on DirectoryAmbiguous {
        setState(() {
          _askId = true;
          _error = "有重名的学习者，请输入你的学习者编号。";
        });
      }
    });
  }

  /// 新建：名字已有人用时先确认，成功后展示编号。
  Future<void> _create() async {
    await _guarded(() async {
      UserRegistry.validateName(_name.text);
      final directory = widget.directoryFactory();
      if (directory == null) return _fail(_needSetup);
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
        if (!go) return;
      }
      final created = await directory.register(_name.text);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          title: Text("你的学习者编号是 ${created.id}"),
          content: const SizedBox(
            width: 420,
            child: Text("在别的电脑上用名字登录时，如果遇到同名的人，会问你这个编号。记一下就行。"),
          ),
          actions: [
            FilledButton(onPressed: () => Navigator.of(context).pop(), child: const Text("知道了")),
          ],
        ),
      );
      await _finish(created);
    });
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
  Future<void> _finish(UserProfile profile) async {
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
    widget.onPicked(stored, adopt);
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
      final directory = widget.directoryFactory();
      if (directory == null) return _fail("改名要联网，先配置同步设备令牌。");
      final renamed = await directory.rename(profile.id, saved);
      widget.registry.renamed(renamed.id, renamed.name);
      widget.onRenamed?.call(renamed);
      if (mounted) setState(() => _current = renamed);
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final configured = widget.directoryFactory() != null;
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
                    "输入你的名字进入。各人的做题记录、成就和解锁进度完全分开，互不打扰。",
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
                            onPressed: _busy ? null : () => _guarded(() => _finish(profile)),
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
                        labelText: "学习者编号（1～999）",
                        helperText: "有重名的学习者：输入你第一次新建时分到的编号。",
                      ),
                      onSubmitted: (_) => _enter(),
                    ),
                  ],
                  if (!configured) ...[
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            "还没有配置同步设备令牌：新建学习者和在新电脑上登录要联网查家里的目录。",
                            style: TextStyle(fontSize: 13, color: theme.colorScheme.primary, height: 1.4),
                          ),
                        ),
                        TextButton(onPressed: _configure, child: const Text("配置同步")),
                      ],
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
                      OutlinedButton(onPressed: _busy ? null : _create, child: const Text("新建学习者")),
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

class ApiConfigScreenResult {
  const ApiConfigScreenResult(this.config);
  final ApiConfig config;
}

/// 设备同步配置（ADR 0068 决策 1、ADR 0070）：只持设备令牌，不持数据库口令。
/// 存用户数据目录 api.json（POSIX 600），环境变量 ATHENA_DRIVER_API 可代替。
class ApiConfigScreen extends StatefulWidget {
  const ApiConfigScreen({super.key, this.onSavedDirect, this.allowSkip = false});

  /// 启动门直接挂载时走这里（保存后直接进应用）；从侧栏 push 进来时
  /// pop 带回结果由调用方处理。
  final void Function(ApiConfig)? onSavedDirect;

  /// true：从应用内进来，允许不改直接返回；启动门挂载时给「先离线用」。
  final bool allowSkip;

  @override
  State<ApiConfigScreen> createState() => _ApiConfigScreenState();
}

class _ApiConfigScreenState extends State<ApiConfigScreen> {
  final _lanBase = TextEditingController(text: "http://192.168.6.1:5000");
  final _wanBase = TextEditingController();
  final _token = TextEditingController();
  final _cfClientId = TextEditingController();
  final _cfClientSecret = TextEditingController();
  String _pingResult = "";
  bool _pinging = false;

  @override
  void initState() {
    super.initState();
    final existing = ApiConfig.load();
    if (existing != null) {
      _lanBase.text = existing.lanBase;
      _wanBase.text = existing.wanBase ?? "";
      _token.text = existing.token;
      _cfClientId.text = existing.cfClientId ?? "";
      _cfClientSecret.text = existing.cfClientSecret ?? "";
    }
  }

  @override
  void dispose() {
    _lanBase.dispose();
    _wanBase.dispose();
    _token.dispose();
    _cfClientId.dispose();
    _cfClientSecret.dispose();
    super.dispose();
  }

  ApiConfig? _compose() {
    final lan = _lanBase.text.trim();
    final token = _token.text.trim();
    if (lan.isEmpty || token.isEmpty) return null;
    return ApiConfig(
      lanBase: lan,
      token: token,
      wanBase: _wanBase.text.trim().isEmpty ? null : _wanBase.text.trim(),
      cfClientId: _cfClientId.text.trim().isEmpty ? null : _cfClientId.text.trim(),
      cfClientSecret: _cfClientSecret.text.trim().isEmpty ? null : _cfClientSecret.text.trim(),
    );
  }

  Future<void> _ping() async {
    final config = _compose();
    if (config == null) {
      setState(() => _pingResult = "先填内网端点和设备令牌");
      return;
    }
    setState(() {
      _pinging = true;
      _pingResult = "";
    });
    String result = "两个端点都连不上";
    for (final base in [config.lanBase, if (config.wanBase != null) config.wanBase!]) {
      try {
        final response = await http
            .get(
              Uri.parse("$base/api/driver/v1/ping"),
              headers: {
                "Authorization": "Bearer ${config.token}",
                if (config.cfClientId != null && config.cfClientSecret != null) ...{
                  "CF-Access-Client-Id": config.cfClientId!,
                  "CF-Access-Client-Secret": config.cfClientSecret!,
                },
              },
            )
            .timeout(const Duration(seconds: 10));
        if (response.statusCode == 200) {
          final map = jsonDecode(response.body) as Map;
          result = "已连上（$base，设备名：${map["device"]}，使用者：${map["user"]}）";
          break;
        }
        if (response.statusCode == 401) {
          result = "端点通了，但令牌无效或已撤销（$base）";
          break;
        }
        result = "$base 返回 ${response.statusCode}";
      } on TimeoutException {
        result = "$base 超时";
      } catch (_) {
        // 换下一个端点再试。
      }
    }
    if (mounted) {
      setState(() {
        _pingResult = result;
        _pinging = false;
      });
    }
  }

  void _save() {
    final config = _compose();
    if (config == null) return;
    config.save();
    final direct = widget.onSavedDirect;
    if (direct != null) {
      direct(config);
    } else {
      Navigator.of(context).pop(ApiConfigScreenResult(config));
    }
  }

  void _skip() {
    final direct = widget.onSavedDirect;
    if (direct != null) {
      // 启动门跳过：不开同步器直接进应用，侧栏会提示「未配置同步」。
      final state = context.findAncestorStateOfType<_BootstrapGateState>();
      state?.setState(() => state._stage = "ready");
    } else {
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "驾考学习",
      debugShowCheckedModeBanner: false,
      locale: const Locale("zh", "CN"),
      supportedLocales: const [Locale("zh", "CN")],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: Scaffold(
        body: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: Padding(
              padding: const EdgeInsets.all(28),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("学习记录同步", style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 10),
                  const Text(
                    "做题记录先存在本机，后台自动和家里的软路由保持同一份；断网也能照常做题，"
                    "联网后自动补上。每台电脑一个设备令牌（dapi_ 开头），丢了哪台就撤销哪个。",
                    style: TextStyle(height: 1.5),
                  ),
                  const SizedBox(height: 20),
                  TextField(
                    controller: _lanBase,
                    decoration: const InputDecoration(labelText: "内网端点（在家时用）"),
                  ),
                  TextField(
                    controller: _wanBase,
                    decoration: const InputDecoration(
                      labelText: "外网端点（可选，离开内网时用）",
                      hintText: "https://www.yatiger.cn",
                    ),
                  ),
                  TextField(
                    controller: _token,
                    decoration: const InputDecoration(labelText: "设备令牌"),
                  ),
                  TextField(
                    controller: _cfClientId,
                    decoration: const InputDecoration(labelText: "Cloudflare Client ID（可选，外网时用）"),
                  ),
                  TextField(
                    controller: _cfClientSecret,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: "Cloudflare Client Secret（可选）"),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      OutlinedButton(
                        onPressed: _pinging ? null : _ping,
                        child: const Text("测试连接"),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          _pinging ? "正在连接…" : _pingResult,
                          style: const TextStyle(fontSize: 13, height: 1.4),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      FilledButton(onPressed: _save, child: const Text("保存并开始同步")),
                      const SizedBox(width: 12),
                      TextButton(onPressed: _skip, child: Text(widget.allowSkip ? "返回" : "先离线用，稍后配置")),
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

class BootstrapErrorApp extends StatelessWidget {
  const BootstrapErrorApp({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "驾考学习",
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        body: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(
                    "启动失败\n\n$message",
                    style: const TextStyle(fontSize: Bs.bodySize, height: 1.45),
                  ),
                ),
          ),
        ),
      ),
    );
  }
}

class DriverApp extends StatelessWidget {
  const DriverApp({
    super.key,
    required this.bank,
    required this.store,
    required this.currentUser,
    this.navigatorKey,
    this.syncStatus,
    this.onOpenConfig,
    this.onSwitchUser,
  });

  final Bank bank;
  final ProgressStore store;

  /// 当前学习者（ADR 0071）：侧栏常驻显示，点击换人。
  final String currentUser;

  /// 应用内导航器：启动门在 MaterialApp 之上，侧栏换人、配置页经它 push。
  final GlobalKey<NavigatorState>? navigatorKey;
  final ValueListenable<SyncStatus>? syncStatus;
  final VoidCallback? onOpenConfig;
  final VoidCallback? onSwitchUser;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      navigatorKey: navigatorKey,
      title: "驾考学习",
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.light(
          primary: Bs.primary,
          error: Bs.danger,
          surface: Bs.light,
        ),
        useMaterial3: true,
        textTheme: Bs.textTheme(ThemeData(useMaterial3: true).textTheme),
        iconTheme: const IconThemeData(size: Bs.bodySize),
        visualDensity: VisualDensity.standard,
        splashFactory: NoSplash.splashFactory,
        scaffoldBackgroundColor: Bs.light,
        dividerColor: Bs.border,
        filledButtonTheme: FilledButtonThemeData(
          // 主按钮用主行动色，不再是一片深灰
          style: FilledButton.styleFrom(
            backgroundColor: Bs.primary,
            foregroundColor: Colors.white,
            textStyle: const TextStyle(fontSize: Bs.bodySize, fontWeight: FontWeight.w600),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          ),
        ),
      ),
      locale: const Locale("zh", "CN"),
      supportedLocales: const [Locale("zh", "CN")],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: HomePage(
        bank: bank,
        store: store,
        currentUser: currentUser,
        syncStatus: syncStatus,
        onOpenConfig: onOpenConfig,
        onSwitchUser: onSwitchUser,
      ),
    );
  }
}
