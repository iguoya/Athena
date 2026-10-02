import "package:flutter/material.dart";
import "package:flutter_localizations/flutter_localizations.dart";
import "package:window_manager/window_manager.dart";

import "content.dart";
import "home.dart";
import "look.dart";
import "models.dart";
import "progress.dart";

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

/// 启动门：先试开库。没配置过就弹配置对话框（凭据存本机，不写默认值，
/// ADR 0068）；连不上给诚实的错误页（ADR 0067 第 5 条）；都过了才进应用。
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
      setState(() {
        _bank = bank;
        _store = store;
        _stage = "ready";
      });
    } on ProgressNotConfigured {
      setState(() => _stage = "config");
    } catch (error) {
      setState(() {
        _message = "$error";
        _stage = "error";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return switch (_stage) {
      "config" => MaterialApp(
          title: "驾考学习",
          debugShowCheckedModeBanner: false,
          home: DbConfigScreen(onSaved: _tryOpen),
        ),
      "error" => BootstrapErrorApp(message: _message),
      "ready" => DriverApp(bank: _bank!, store: _store!),
      _ => const MaterialApp(
          title: "驾考学习",
          home: Scaffold(body: Center(child: CircularProgressIndicator())),
        ),
    };
  }
}

/// 第一次启动（或配置丢失）时的连接配置：存进用户数据目录的 db.json
/// （POSIX 上 600），环境变量 ATHENA_DRIVER_DB 可以代替它（CI / 脚本）。
class DbConfigScreen extends StatefulWidget {
  const DbConfigScreen({super.key, required this.onSaved});

  final Future<void> Function() onSaved;

  @override
  State<DbConfigScreen> createState() => _DbConfigScreenState();
}

class _DbConfigScreenState extends State<DbConfigScreen> {
  final _host = TextEditingController(text: "192.168.6.1");
  final _port = TextEditingController(text: "5432");
  final _database = TextEditingController(text: "athena_driver");
  final _username = TextEditingController(text: "athena_driver");
  final _password = TextEditingController();

  @override
  void dispose() {
    _host.dispose();
    _port.dispose();
    _database.dispose();
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  void _save() {
    for (final controller in [_host, _database, _username, _password]) {
      if (controller.text.trim().isEmpty) return;
    }
    DbConfig(
      host: _host.text.trim(),
      port: int.tryParse(_port.text.trim()) ?? 5432,
      database: _database.text.trim(),
      username: _username.text.trim(),
      password: _password.text,
    ).save();
    widget.onSaved();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("第一次使用：填写学习记录服务的连接信息",
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
                const SizedBox(height: 10),
                const Text(
                  "学习进度存在家里的软路由数据库里，两台电脑填同一份即可。"
                  "密码只保存在这台机器上。",
                  style: TextStyle(height: 1.5),
                ),
                const SizedBox(height: 20),
                TextField(
                  controller: _host,
                  decoration: const InputDecoration(labelText: "主机"),
                ),
                TextField(
                  controller: _port,
                  decoration: const InputDecoration(labelText: "端口"),
                ),
                TextField(
                  controller: _database,
                  decoration: const InputDecoration(labelText: "数据库"),
                ),
                TextField(
                  controller: _username,
                  decoration: const InputDecoration(labelText: "用户名"),
                ),
                TextField(
                  controller: _password,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: "密码"),
                ),
                const SizedBox(height: 22),
                FilledButton(onPressed: _save, child: const Text("保存并连接")),
              ],
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
  const DriverApp({super.key, required this.bank, required this.store});

  final Bank bank;
  final ProgressStore store;

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
      home: HomePage(bank: bank, store: store),
    );
  }
}
