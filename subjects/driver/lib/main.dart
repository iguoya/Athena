import "dart:async";
import "dart:io";

import "package:flutter/foundation.dart";
import "package:flutter/material.dart";
import "package:flutter_localizations/flutter_localizations.dart";
import "package:path/path.dart" as p;
import "package:window_manager/window_manager.dart";

import "app/api_config_screen.dart";
import "core/content.dart";
import "home.dart";
import "ui/look.dart";
import "core/models.dart";
import "core/progress.dart";
import "ui/skin.dart";
import "core/sync.dart";
import "core/user_directory.dart";
import "app/user_gate_screen.dart";
import "core/users.dart";
/// 各 MaterialApp 共用的皮肤主题与整窗环境背景（ADR 0058）：皮肤令牌挂在
/// [SkinStore.notifier] 上，切换器改值后这里重建 MaterialApp 整树换装；
/// 环境背景垫在 builder 里，页面 Scaffold 全透明，铺满启动到做题的每个场景。
Widget withSkins(
  WidgetBuilder builder, {
  GlobalKey<NavigatorState>? navigatorKey,
  GlobalKey<ScaffoldMessengerState>? scaffoldMessengerKey,
}) {
  return ValueListenableBuilder<Skin>(
    valueListenable: SkinStore.notifier,
    builder: (context, skin, _) => MaterialApp(
      title: "驾考学习",
      debugShowCheckedModeBanner: false,
      theme: buildTheme(skin),
      navigatorKey: navigatorKey,
      scaffoldMessengerKey: scaffoldMessengerKey,
      locale: const Locale("zh", "CN"),
      supportedLocales: const [Locale("zh", "CN")],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      builder: (context, child) => Stack(
        children: [
          Positioned.fill(child: AmbientBackdrop(skin: skin)),
          if (child != null) Positioned.fill(child: child),
        ],
      ),
      home: builder(context),
    ),
  );
}

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
/// （ADR 0071、0075：输入名字登录，本机缓存里的人离线也能直接进）；同步总是尝试，连不上
/// 就是「暂不同步」，队列等连上后自然补发（ADR 0077：没有令牌可配）。
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

  /// 应用内的提示条：新建学习者后告诉使用者分到的编号，不弹窗拦人（ADR 0078）。
  final _messengerKey = GlobalKey<ScaffoldMessengerState>();

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
  Future<void> _enter(UserProfile profile, bool adoptLegacy, bool created) async {
    if (adoptLegacy) {
      ProgressStore.adoptLegacyFiles(profile.id);
      _legacyPending = false;
    }
    await _openAs(profile);
    if (created) _showWelcome(profile);
  }

  /// 新建学习者后的提示：编号用一条不挡路的提示条告诉他（ADR 0078 决策 2）。
  /// 本地学习者的提示另说清楚「不同步」（ADR 0123）。
  /// 等进入应用的那一帧画完再弹，提示条才挂得上。
  void _showWelcome(UserProfile profile) {
    final content = profile.isLocal
        ? "已在这台电脑上新建本地学习者「${profile.name}」，编号 ${profile.id}。"
            "记录只保存在这台电脑上，不会同步到其他设备。"
        : "已新建学习者「${profile.name}」，编号 ${profile.id}。在别的电脑登录时如果遇到同名，会问这个编号。";
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _messengerKey.currentState?.showSnackBar(
        SnackBar(
          content: Text(content),
          duration: const Duration(seconds: 15),
          showCloseIcon: true,
        ),
      );
    });
  }

  /// 以某个学习者身份打开应用：换人就是换一份空白历史（ADR 0071）。
  /// 身份认编号（ADR 0075）；侧栏显示的是名字。本地学习者（ADR 0123，编号 1000 起）
  /// 不启动同步引擎——它只存这台电脑，永不出站。
  Future<void> _openAs(UserProfile profile) async {
    try {
      _engine?.stop();
      await _store?.close();
      final store = await ProgressStore.open(user: profile.id);
      _registry?.setLast(profile.id);
      _engine = profile.isLocal ? null : _startEngine(store, _bank!, ApiConfig.load(), profile.id);
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

  /// 登录页每次动作时现取：配置页改了端点，同一个页面立刻生效。
  UserDirectory _directory() => HttpUserDirectory(ApiConfig.load());

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
    String? createdId; // 这次是不是在登录页顺手新建的
    final picked = await navigator.push<UserProfile>(
      MaterialPageRoute(
        builder: (context) => UserGateScreen(
          registry: registry,
          directoryFactory: _directory,
          configLoader: ApiConfig.load,
          currentUser: _profile,
          allowCancel: true,
          onPicked: (profile, _, created) {
            if (created) createdId = profile.id;
            Navigator.of(context).pop(profile);
          },
          onRenamed: _onRenamed,
        ),
        fullscreenDialog: true,
      ),
    );
    if (picked == null || picked.id == _profile?.id || !mounted) return;
    // 换人是唯一没有二次确认的破坏性操作（批次 7）：整库切换，误触一次就进错库。
    final confirmed = await showDialog<bool>(
      context: navigator.context,
      builder: (context) => AlertDialog(
        title: Text("换到「${picked.name}」？"),
        content: const Text("当前学习者的进度都保存在这台机器上，随时可以换回来。"),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text("不换了")),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text("换人")),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    await _openAs(picked);
    if (createdId == picked.id) _showWelcome(picked);
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
      "first-user" || "pick" => withSkins(
          (context) => UserGateScreen(
            registry: _registry!,
            directoryFactory: _directory,
            configLoader: ApiConfig.load,
            legacyPending: _legacyPending,
            onPicked: _enter,
          ),
        ),
      "config" => withSkins(
          (context) => ApiConfigScreen(
            onSavedDirect: (config) {
              final bank = _bank;
              final store = _store;
              final profile = _profile;
              if (bank == null || store == null || profile == null) return;
              _engine = _startEngine(store, bank, config, profile.id);
              setState(() => _stage = "ready");
            },
            onSkipDirect: () => setState(() => _stage = "ready"),
          ),
        ),
      "error" => withSkins((context) => BootstrapErrorApp(message: _message)),
      "ready" => withSkins(
          (context) => DriverApp(
            bank: _bank!,
            store: _store!,
            currentUser: _profile!.name,
            navigatorKey: _navigatorKey,
            messengerKey: _messengerKey,
            onSwitchUser: _switchUser,
            syncStatus: _engine?.status,
            localOnly: _profile!.isLocal,
            onOpenConfig: _openConfig,
          ),
          navigatorKey: _navigatorKey,
          scaffoldMessengerKey: _messengerKey,
        ),
      _ => withSkins(
          (context) => Scaffold(body: Center(child: CircularProgressIndicator())),
        ),
    };
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
                    style: TextStyle(fontSize: Bs.bodySize, height: 1.45),
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
    this.messengerKey,
    this.syncStatus,
    this.localOnly = false,
    this.onOpenConfig,
    this.onSwitchUser,
  });

  final Bank bank;
  final ProgressStore store;

  /// 当前学习者（ADR 0071）：侧栏常驻显示，点击换人。
  final String currentUser;

  /// 应用内导航器：启动门在 MaterialApp 之上，侧栏换人、配置页经它 push。
  final GlobalKey<NavigatorState>? navigatorKey;

  /// 应用内的提示条（新建学习者后告诉编号等）。
  final GlobalKey<ScaffoldMessengerState>? messengerKey;
  final ValueListenable<SyncStatus>? syncStatus;

  /// 本地学习者（ADR 0123）：没有同步引擎，侧栏如实写「本地模式」。
  final bool localOnly;

  final VoidCallback? onOpenConfig;
  final VoidCallback? onSwitchUser;

  @override
  Widget build(BuildContext context) {
    // 主题、导航器与提示条壳由 withSkins 统一提供（ADR 0058），这里只挂主页。
    return HomePage(
      bank: bank,
      store: store,
      currentUser: currentUser,
      syncStatus: syncStatus,
      localOnly: localOnly,
      onOpenConfig: onOpenConfig,
      onSwitchUser: onSwitchUser,
    );
  }
}
