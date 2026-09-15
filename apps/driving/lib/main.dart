import "package:flutter/material.dart";
import "package:flutter_localizations/flutter_localizations.dart";

import "content.dart";
import "home.dart";
import "models.dart";
import "progress.dart";

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final bank = await ContentLoader.load();
  final store = await ProgressStore.open();
  runApp(DrivingApp(bank: bank, store: store));
}

class DrivingApp extends StatelessWidget {
  const DrivingApp({super.key, required this.bank, required this.store});

  final Bank bank;
  final ProgressStore store;

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(seedColor: const Color(0xFF1565C0));
    return MaterialApp(
      title: "驾驶学习",
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorScheme: scheme, useMaterial3: true),
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
