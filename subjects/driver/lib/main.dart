import "dart:async";
import "dart:convert";

import "package:flutter/foundation.dart";
import "package:flutter/material.dart";
import "package:flutter_localizations/flutter_localizations.dart";
import "package:http/http.dart" as http;
import "package:window_manager/window_manager.dart";

import "content.dart";
import "home.dart";
import "look.dart";
import "models.dart";
import "progress.dart";
import "sync.dart";

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

/// 启动门：本地进度库必开成功（ADR 0070，做题不以「连上中心」为前提）；API
/// 没配置时进配置屏，但可以跳过先离线用——队列会等令牌配好后自然补发。
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

  @override
  void initState() {
    super.initState();
    _tryOpen();
  }

  Future<void> _tryOpen() async {
    setState(() => _stage = "loading");
    try {
      final bank = await ContentLoader.load();
      final store = await ProgressStore.open();
      final config = ApiConfig.load();
      _engine?.stop();
      _engine = null;
      if (config != null) _engine = _startEngine(store, bank, config);
      setState(() {
        _bank = bank;
        _store = store;
        _stage = config == null ? "config" : "ready";
      });
    } catch (error) {
      setState(() {
        _message = "$error";
        _stage = "error";
      });
    }
  }

  SyncEngine _startEngine(ProgressStore store, Bank bank, ApiConfig config) {
    return SyncEngine(
      store: store,
      config: config,
      draftKeys: [for (final subject in bank.curriculum.subjects) "${subject.id}.exam"],
    )..start();
  }

  /// 侧栏同步行点进来重新配置：保存后换引擎重启同步，跳过则维持现状。
  Future<void> _openConfig() async {
    final config = await Navigator.of(context).push<ApiConfigScreenResult>(
      MaterialPageRoute(
        builder: (context) => const ApiConfigScreen(allowSkip: true),
        fullscreenDialog: true,
      ),
    );
    if (config == null || !mounted) return;
    final bank = _bank;
    final store = _store;
    if (bank == null || store == null) return;
    _engine?.stop();
    _engine = _startEngine(store, bank, config.config);
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
      "config" => MaterialApp(
          title: "驾考学习",
          debugShowCheckedModeBanner: false,
          home: ApiConfigScreen(
            onSavedDirect: (config) {
              final bank = _bank;
              final store = _store;
              if (bank == null || store == null) return;
              _engine = _startEngine(store, bank, config);
              setState(() => _stage = "ready");
            },
          ),
        ),
      "error" => BootstrapErrorApp(message: _message),
      "ready" => DriverApp(
          bank: _bank!,
          store: _store!,
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
          final device = (jsonDecode(response.body) as Map)["device"];
          result = "已连上（$base，设备名：$device）";
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
    this.syncStatus,
    this.onOpenConfig,
  });

  final Bank bank;
  final ProgressStore store;

  /// null 表示还没配置同步（先离线用）：侧栏显示「未配置同步」。
  final ValueListenable<SyncStatus>? syncStatus;
  final VoidCallback? onOpenConfig;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
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
        syncStatus: syncStatus,
        onOpenConfig: onOpenConfig,
      ),
    );
  }
}
