import "package:flutter/material.dart";
import "package:flutter_localizations/flutter_localizations.dart";

import "content.dart";
import "home.dart";
import "look.dart";
import "models.dart";
import "progress.dart";

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
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
          style: FilledButton.styleFrom(
            backgroundColor: Bs.dark,
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
