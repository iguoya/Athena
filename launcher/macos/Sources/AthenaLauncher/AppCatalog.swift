import Foundation

// apps/<id>/app.json 的启动器视角子集。主程序读的是同一份清单（ADR 0032），
// 这里只多读 icon.symbol 和 dev 两处；未知字段两边都忽略，互不牵制。
struct LearningApp: Identifiable, Sendable {
    /// 怎么构建、怎么启动、怎么算就绪都写在 app.json 的 dev 声明里，由编排器
    /// 执行（ADR 0046）；菜单栏版不需要理解这些字段。
    struct Dev: Sendable {}

    var id: String
    var title: String
    var summary: String
    var symbol: String
    var directory: URL
    // 判断"这个应用在不在跑"时看的路径前缀。默认就是应用目录；主程序这种
    // 进程落在子目录（builddir/）里的，用 match 指明，免得把仓库里任何
    // 进程都算成它自己。
    var matchPrefix: String
    /// 窗口进程的可执行文件名，来自 app.json 的 dev.binary。
    var binary: String
    var dev: Dev
}

enum AppCatalog {
    // 所有学习应用都在 apps/ 下，C++ 教程（apps/cpp）也不例外——它没有特权，
    // 这里没有任何针对某个应用的分支（ADR 0045）。顺序按目录名排，
    // 菜单里的次序才不会随文件系统变。
    static func discover(in repository: URL) -> [LearningApp] {
        var apps: [LearningApp] = []
        let appsRoot = repository.appendingPathComponent("apps")
        let entries = (try? FileManager.default.contentsOfDirectory(
            at: appsRoot,
            includingPropertiesForKeys: [.isDirectoryKey],
            options: [.skipsHiddenFiles]
        )) ?? []

        apps.append(contentsOf: entries
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
            .compactMap { parse(directory: $0) })
        return apps
    }

    private static func parse(directory: URL) -> LearningApp? {
        let manifest = directory.appendingPathComponent("app.json")
        guard let data = try? Data(contentsOf: manifest),
              let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let id = root["id"] as? String,
              let title = root["title"] as? String else {
            return nil
        }

        let icon = root["icon"] as? [String: Any]
        let dev = root["dev"] as? [String: Any]
        let match = (dev?["match"] as? String) ?? (root["match"] as? String)
        return LearningApp(
            id: id,
            title: title,
            summary: root["description"] as? String ?? "",
            symbol: icon?["symbol"] as? String ?? "book.closed",
            directory: directory,
            matchPrefix: match.map { directory.appendingPathComponent($0).path }
                ?? directory.path,
            binary: dev?["binary"] as? String ?? "",
            dev: LearningApp.Dev()
        )
    }
}
