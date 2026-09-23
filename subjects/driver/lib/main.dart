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
  try {
    final bank = await ContentLoader.load();
    final store = await ProgressStore.open();
    runApp(DriverApp(bank: bank, store: store));
  } catch (error) {
    runApp(BootstrapErrorApp(message: "$error"));
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
