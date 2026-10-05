import "dart:async";

import "package:flutter/material.dart";
import "package:flutter_localizations/flutter_localizations.dart";
import "package:http/http.dart" as http;

import "../core/sync.dart";
class ApiConfigScreenResult {
  const ApiConfigScreenResult(this.config);
  final ApiConfig config;
}

/// 同步设置（ADR 0070、0077）：内网端点（默认就是路由器地址）、可选的外网端点与外网访问凭据。
/// 不持数据库口令。存用户数据目录 api.json（POSIX 600），
/// 环境变量 ATHENA_DRIVER_API 可代替。
class ApiConfigScreen extends StatefulWidget {
  const ApiConfigScreen({super.key, this.onSavedDirect, this.onSkipDirect, this.allowSkip = false});

  /// 启动门直接挂载时走这里（保存后直接进应用）；从侧栏 push 进来时
  /// pop 带回结果由调用方处理。
  final void Function(ApiConfig)? onSavedDirect;

  /// 启动门挂载时的「先离线用」：不开同步器直接进应用（侧栏会提示「未配置同步」）。
  final VoidCallback? onSkipDirect;

  /// true：从应用内进来，允许不改直接返回；启动门挂载时给「先离线用」。
  final bool allowSkip;

  @override
  State<ApiConfigScreen> createState() => _ApiConfigScreenState();
}

class _ApiConfigScreenState extends State<ApiConfigScreen> {
  final _lanBase = TextEditingController(text: "http://192.168.6.1:5000");
  final _wanBase = TextEditingController();
  final _cfClientId = TextEditingController();
  final _cfClientSecret = TextEditingController();
  String _pingResult = "";
  bool _pinging = false;

  @override
  void initState() {
    super.initState();
    final existing = ApiConfig.load();
    _lanBase.text = existing.lanBase;
    _wanBase.text = existing.wanBase ?? ApiConfig.defaultWanBase;
    _cfClientId.text = existing.cfClientId ?? "";
    _cfClientSecret.text = existing.cfClientSecret ?? "";
  }

  @override
  void dispose() {
    _lanBase.dispose();
    _wanBase.dispose();
    _cfClientId.dispose();
    _cfClientSecret.dispose();
    super.dispose();
  }

  ApiConfig _compose() {
    final lan = _lanBase.text.trim();
    return ApiConfig(
      lanBase: lan.isEmpty ? ApiConfig.defaultLanBase : lan,
      wanBase: _wanBase.text.trim().isEmpty ? ApiConfig.defaultWanBase : _wanBase.text.trim(),
      cfClientId: _cfClientId.text.trim().isEmpty ? null : _cfClientId.text.trim(),
      cfClientSecret: _cfClientSecret.text.trim().isEmpty ? null : _cfClientSecret.text.trim(),
    );
  }

  Future<void> _ping() async {
    if (_idLooksLikeEmail) {
      setState(() => _pingResult = emailAsCredentialHint);
      return;
    }
    final config = _compose();
    setState(() {
      _pinging = true;
      _pingResult = "";
    });
    // 内网和外网各测各的、逐行显示：以前内网通了就停，「已连上」只说明内网通，外网通不通
    // 看不出来，容易误以为外网也配好了。
    final lines = <String>[];
    final client = http.Client();
    final endpoints = [("内网", config.lanBase, false), if (config.wanBase != null) ("外网", config.wanBase!, true)];
    for (final (label, base, external) in endpoints) {
      String outcome;
      try {
        final request = http.Request("GET", Uri.parse("$base/api/driver/v1/ping"))
          ..followRedirects = false
          ..headers.addAll({
            // 外网访问凭据只发给外网端点，不发给内网地址。
            if (external && config.cfClientId != null && config.cfClientSecret != null) ...{
              "CF-Access-Client-Id": config.cfClientId!,
              "CF-Access-Client-Secret": config.cfClientSecret!,
            },
          });
        final response = await client.send(request).timeout(const Duration(seconds: 10));
        final body = await response.stream.bytesToString();
        if (blockedByCloudflare(response.statusCode, response.headers, body)) {
          outcome = (config.cfClientId == null)
              ? "被 Cloudflare 访问规则拦住了（没填外网访问凭据）"
              : "被 Cloudflare 访问规则拦住了：检查凭据，以及 Cloudflare 里是否给这个令牌加了 Service Auth 策略";
        } else if (response.statusCode == 401) {
          outcome = "后台是旧版本，要先部署新版";
        } else if (response.statusCode == 200) {
          outcome = "已连上";
        } else {
          outcome = "返回 ${response.statusCode}";
        }
      } on TimeoutException {
        outcome = "超时";
      } catch (_) {
        outcome = "连不上";
      }
      lines.add("$label（$base）：$outcome");
    }
    client.close();
    if (mounted) {
      setState(() {
        _pingResult = lines.join("\n");
        _pinging = false;
      });
    }
  }

  /// 外网访问凭据的 ID 不是邮箱：邮箱是给人在浏览器里收验证码用的，程序用不上；程序用的是
  /// Cloudflare 里新建「服务令牌」得到的一对 ID 和密钥。填了邮箱存下来也永远不会生效，
  /// 所以保存和测试连接前先拦住并说清楚（ADR 0077）。
  static const emailAsCredentialHint =
      "这里填的不是邮箱。邮箱是给人在浏览器里收验证码用的，桌面程序用不上；"
      "这里要的是在 Cloudflare 里新建「服务令牌」后得到的一对 ID（以 .access 结尾）和密钥。"
      "只在家里内网用的话，这几项留空就行。";

  bool get _idLooksLikeEmail => _cfClientId.text.contains("@");

  void _save() {
    if (_idLooksLikeEmail) {
      setState(() => _pingResult = emailAsCredentialHint);
      return;
    }
    final config = _compose();
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
      widget.onSkipDirect?.call();
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
                    "联网后自动补上。在家里内网用什么都不用改；离开内网时填外网端点，"
                    "以及 Cloudflare 给的外网访问凭据（一对 ID 和密钥，全家共用）。",
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
                      labelText: "外网端点（离开内网时用）",
                      helperText: "已内置，一般不用改",
                    ),
                  ),
                  TextField(
                    controller: _cfClientId,
                    decoration: const InputDecoration(
                      labelText: "外网访问凭据 · Client ID（可选）",
                      helperText: "不是邮箱；是 Cloudflare「服务令牌」的 ID，以 .access 结尾",
                    ),
                  ),
                  TextField(
                    controller: _cfClientSecret,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: "外网访问凭据 · Client Secret（可选）"),
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
