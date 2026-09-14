import Foundation

// 启动器要知道 Athena 仓库在哪，才能扫到 apps/*/app.json。
// 三条线索按可靠性排序：显式环境变量 → 打包时写进 Info.plist 的路径 →
// 从可执行文件所在位置向上找。三条都落空时返回 nil，界面会说清楚缺什么。
enum Repository {
    static func locate() -> URL? {
        if let raw = ProcessInfo.processInfo.environment["ATHENA_ROOT"],
           let url = validated(URL(fileURLWithPath: raw)) {
            return url
        }
        if let raw = Bundle.main.object(forInfoDictionaryKey: "AthenaRepositoryRoot") as? String,
           !raw.hasPrefix("@"),
           let url = validated(URL(fileURLWithPath: raw)) {
            return url
        }
        var candidate = URL(fileURLWithPath: CommandLine.arguments[0])
            .resolvingSymlinksInPath()
            .deletingLastPathComponent()
        for _ in 0..<8 {
            if let url = validated(candidate) {
                return url
            }
            candidate = candidate.deletingLastPathComponent()
        }
        return nil
    }

    // 仓库的标志是 apps/ 目录：启动器只关心这一件事。
    private static func validated(_ url: URL) -> URL? {
        var isDirectory: ObjCBool = false
        let apps = url.appendingPathComponent("apps").path
        guard FileManager.default.fileExists(atPath: apps, isDirectory: &isDirectory),
              isDirectory.boolValue else {
            return nil
        }
        return url.standardizedFileURL
    }
}
