import "dart:async";

import "package:flutter/foundation.dart";

import "user_directory.dart";
import "users.dart";

/// 学习者与中心目录的静默绑定（ADR 0127）。
///
/// 学习者一律先在本机创建（本机段编号），同步所需的中心编号在检测到路由器之后才补上：
/// 按名字问目录——恰好一个同名者就认领它（同一个人换了台电脑），没有就登记一个新的。
/// 整个过程没有界面：成败都不告诉使用者，失败了下次再试，学习记录始终先存本机。
///
/// 不替使用者做判断：目录里有**不止一个**同名者时，无界面就无法知道是哪一个，宁可保持
/// 「只存本机」也不乱认，绝不把记录写到别人名下。
class LearnerBinder {
  LearnerBinder({required this.registry, required this.directoryFactory});

  final UserRegistry registry;
  final UserDirectory Function() directoryFactory;

  /// 返回学习者的中心编号；还绑定不了（路由器不在、同名不止一个、服务端拒绝）返回 null。
  /// 从不抛错：这是后台动作，调用方不该为它写错误处理。
  Future<String?> ensureBound(UserProfile profile) async {
    final known = profile.serverId;
    if (known != null) return known;
    try {
      final directory = directoryFactory();
      UserProfile found;
      try {
        found = await directory.login(profile.name);
      } on DirectoryNotFound {
        found = await directory.register(profile.name);
      }
      registry.bindServerId(profile.id, found.id);
      return found.id;
    } on DirectoryAmbiguous {
      debugPrint("学习者「${profile.name}」在中心目录里有重名者，保持仅本机");
    } on DirectoryUnavailable {
      // 路由器不在身边：常态，不是错误。
    } on DirectoryRejected catch (error) {
      debugPrint("中心目录拒绝绑定「${profile.name}」：${error.message}");
    } catch (error) {
      debugPrint("绑定「${profile.name}」时出错：$error");
    }
    return null;
  }
}
