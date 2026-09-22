import Foundation

// 应用清单来自编排器的 `launcher list --json`（ADR 0046、0048）。
//
// 菜单栏版不自己读 app.json。清单里哪些字段可选、默认值是什么，只保留编排器
// 那一份；两边各解析一遍就会各自漂移——symbol 的兜底曾经一边是 "book"、
// 一边是 "book.closed"，只是碰巧每个 app.json 都写了才没暴露。
struct LearningApp: Identifiable, Sendable {
    var id: String
    var title: String
    var summary: String
    /// 菜单里显示的 SF Symbol。
    var symbol: String
    var directory: URL
    /// 判断「这个应用在不在跑」时看的路径前缀，编排器算好了交过来。
    var matchPrefix: String
    /// 窗口进程的可执行文件名。
    var binary: String
    /// 启动日志的位置，同样由编排器决定，菜单栏版不再自己拼。
    var logURL: URL
}

enum AppCatalog {
    /// 解析 `launcher list --json` 的输出。
    ///
    /// 少字段的行跳过而不是整张表作废：新增一个还没写全 app.json 的应用时，
    /// 其余应用照常能打开。
    static func parse(_ data: Data) -> [LearningApp] {
        rows(data).compactMap { row in
            guard let id = row["id"] as? String,
                  let title = row["title"] as? String,
                  let directory = row["dir"] as? String else {
                return nil
            }
            return LearningApp(
                id: id,
                title: title,
                summary: row["summary"] as? String ?? "",
                symbol: row["symbol"] as? String ?? "book",
                directory: URL(fileURLWithPath: directory),
                matchPrefix: row["matchPrefix"] as? String ?? directory,
                binary: row["binary"] as? String ?? "",
                logURL: URL(fileURLWithPath: row["log"] as? String ?? "")
            )
        }
    }

    /// 每个应用此刻的状态，按稳定标识读。
    ///
    /// 以前这里解析的是给人看的中文（"运行中"/"启动中…"）：编排器改一个字，
    /// 菜单栏就会静默把所有应用显示成"未运行"，而且没有任何报错（ADR 0048）。
    static func states(_ data: Data) -> [String: RunState] {
        var result: [String: RunState] = [:]
        for row in rows(data) {
            guard let id = row["id"] as? String, let key = row["state"] as? String else {
                continue
            }
            result[id] = RunState(key: key)
        }
        return result
    }

    private static func rows(_ data: Data) -> [[String: Any]] {
        (try? JSONSerialization.jsonObject(with: data)) as? [[String: Any]] ?? []
    }
}
