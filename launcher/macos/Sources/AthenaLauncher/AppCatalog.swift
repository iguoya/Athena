import Foundation

// apps/<id>/app.json 的启动器视角子集。主程序读的是同一份清单（ADR 0032），
// 这里只多读 icon.symbol 和 dev 两处；未知字段两边都忽略，互不牵制。
struct LearningApp: Identifiable, Sendable {
    struct Dev: Sendable {
        // Tauri 应用的 dev server 地址：能连上就说明这个应用已经就绪。
        var url: URL?
        // 没有 dev server 的应用（如 Qt 写的 apps/c）靠进程名判断在不在。
        var process: String?
    }

    var id: String
    var title: String
    var summary: String
    var symbol: String
    var directory: URL
    var executable: URL
    // 判断"这个应用在不在跑"时看的路径前缀。默认就是应用目录；主程序这种
    // 进程落在子目录（builddir/）里的，用 match 指明，免得把仓库里任何
    // 进程都算成它自己。
    var matchPrefix: String
    var dev: Dev

    var executableExists: Bool {
        FileManager.default.isExecutableFile(atPath: executable.path)
    }
}

enum AppCatalog {
    // 仓库根的 app.json 是主程序（C++ 教程）自己那一条，排在最前；
    // 其余按目录名排序，菜单里的次序才不会随文件系统变。
    static func discover(in repository: URL) -> [LearningApp] {
        var apps: [LearningApp] = []
        if let host = parse(directory: repository) {
            apps.append(host)
        }
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
              let title = root["title"] as? String,
              let executable = root["executable"] as? String else {
            return nil
        }

        let icon = root["icon"] as? [String: Any]
        let match = root["match"] as? String
        let dev = root["dev"] as? [String: Any]
        let urlText = dev?["url"] as? String

        return LearningApp(
            id: id,
            title: title,
            summary: root["description"] as? String ?? "",
            symbol: icon?["symbol"] as? String ?? "book.closed",
            directory: directory,
            executable: directory.appendingPathComponent(executable),
            matchPrefix: match.map { directory.appendingPathComponent($0).path }
                ?? directory.path,
            dev: LearningApp.Dev(
                url: urlText.flatMap(URL.init(string:)),
                process: dev?["process"] as? String
            )
        )
    }
}
