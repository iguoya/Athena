import AppKit
import Foundation

// 一个应用此刻在哪个状态。判据只有两条，都从系统实况来，不从启动器自己的记账来：
// 窗口进程在不在（NSRunningApplication），以及有没有属于这个目录的进程在忙。
enum RunState: Equatable {
    case stopped     // 没起来
    case starting    // 有进程在跑（cargo / vite / cmake），但窗口还没出来
    case hidden      // 已预热：窗口在，但被藏起来了，点一下就现身
    case ready       // 窗口在，且可见

    var label: String {
        switch self {
        case .stopped: return "未运行"
        case .starting: return "启动中…"
        case .hidden: return "已预热"
        case .ready: return "运行中"
        }
    }
}

@MainActor
final class AppSupervisor: ObservableObject {
    @Published private(set) var apps: [LearningApp] = []
    @Published private(set) var states: [String: RunState] = [:]
    @Published private(set) var repositoryProblem: String?

    // 预热名单存在 UserDefaults：登录后启动器自己起来，就把它们悄悄拉起来。
    @Published var prewarmIDs: Set<String> {
        didSet { defaults.set(Array(prewarmIDs).sorted(), forKey: Self.prewarmKey) }
    }

    private static let prewarmKey = "PrewarmAppIDs"
    private let defaults = UserDefaults.standard
    private var repository: URL?
    private var children: [String: Process] = [:]
    private var pollTimer: Timer?
    // 预热启动的应用，窗口一出现就藏起来，免得抢走正在做别的事的人的焦点。
    private var pendingHide: Set<String> = []

    init() {
        prewarmIDs = Set(defaults.stringArray(forKey: Self.prewarmKey) ?? [])
        reloadCatalog()
    }

    func reloadCatalog() {
        guard let root = Repository.locate() else {
            repositoryProblem = "找不到 Athena 仓库：请设置 ATHENA_ROOT 环境变量，"
                + "或用 launcher/scripts/install.sh 重新安装一次启动器。"
            apps = []
            return
        }
        repository = root
        repositoryProblem = nil
        apps = AppCatalog.discover(in: root)
    }

    // MARK: - 轮询

    func startPolling(interval: TimeInterval = 2) {
        pollTimer?.invalidate()
        let timer = Timer(timeInterval: interval, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.refresh() }
        }
        RunLoop.main.add(timer, forMode: .common)
        pollTimer = timer
        refresh()
    }

    func refresh() {
        let busy = busyDirectories()
        for app in apps {
            let state: RunState
            if let running = runningApplication(for: app) {
                if pendingHide.contains(app.id) {
                    // 预热刚起来的窗口：藏起来，状态随下一轮探测自然变成 .hidden。
                    running.hide()
                    pendingHide.remove(app.id)
                }
                state = running.isHidden ? .hidden : .ready
            } else if children[app.id]?.isRunning == true || busy.contains(app.matchPrefix) {
                state = .starting
            } else {
                state = .stopped
            }
            states[app.id] = state
        }
    }

    // MARK: - 动作

    // 点一下的语义只有一个：把这个应用放到我面前。已经在跑就前置，没跑才拉起来。
    func open(_ app: LearningApp) {
        if let running = runningApplication(for: app) {
            running.unhide()
            running.activate(options: [.activateAllWindows])
            states[app.id] = .ready
            return
        }
        spawnDevScript(for: app, hideWhenReady: false)
    }

    // 预热：同样是 dev.sh，只是窗口一出来就藏起来。
    func prewarm(_ app: LearningApp) {
        guard runningApplication(for: app) == nil,
              children[app.id]?.isRunning != true,
              !busyDirectories().contains(app.matchPrefix) else {
            return
        }
        spawnDevScript(for: app, hideWhenReady: true)
    }

    func prewarmAllMarked() {
        for app in apps where prewarmIDs.contains(app.id) {
            prewarm(app)
        }
    }

    // 停止要连同 dev.sh 拉起的那一串（vite、cargo、tauri 壳）一起收拾干净，
    // 否则下次探测会看见半棵进程树，状态就说不清了。
    func stop(_ app: LearningApp) {
        children[app.id]?.terminate()
        children[app.id] = nil
        // 窗口进程先按系统给的真实路径关掉——它的命令行可能是相对路径，
        // 只靠 pkill 的文本匹配会漏掉。pkill 再补一刀，收掉构建期的那一串。
        runningApplication(for: app)?.terminate()
        runCommand("/usr/bin/pkill", ["-f", app.matchPrefix + "/"])
        states[app.id] = .stopped
    }

    func restart(_ app: LearningApp) {
        stop(app)
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) { [weak self] in
            self?.open(app)
        }
    }

    func logURL(for app: LearningApp) -> URL {
        Self.logDirectory.appendingPathComponent("\(app.id).log")
    }

    func revealLog(for app: LearningApp) {
        NSWorkspace.shared.open(logURL(for: app))
    }

    // MARK: - 进程

    private static let logDirectory: URL = {
        let url = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Logs/AthenaLauncher")
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }()

    private func spawnDevScript(for app: LearningApp, hideWhenReady: Bool) {
        guard app.executableExists else {
            states[app.id] = .stopped
            return
        }

        let log = logURL(for: app)
        if !FileManager.default.fileExists(atPath: log.path) {
            FileManager.default.createFile(atPath: log.path, contents: nil)
        }
        let handle = try? FileHandle(forWritingTo: log)
        handle?.seekToEndOfFile()
        let stamp = ISO8601DateFormatter().string(from: Date())
        handle?.write(Data("\n===== \(stamp) 启动 \(app.id) =====\n".utf8))

        let process = Process()
        process.executableURL = app.executable
        process.currentDirectoryURL = app.directory
        if let handle {
            process.standardOutput = handle
            process.standardError = handle
        }

        do {
            try process.run()
            children[app.id] = process
            states[app.id] = .starting
            if hideWhenReady {
                pendingHide.insert(app.id)
            }
        } catch {
            handle?.write(Data("启动失败：\(error.localizedDescription)\n".utf8))
            states[app.id] = .stopped
        }
    }

    // 一个应用的窗口进程，是可执行文件落在它自己目录下的那个进程。
    // 不靠名字匹配：路径是应用自己的，改产品名也不会认错。
    private func runningApplication(for app: LearningApp) -> NSRunningApplication? {
        let prefix = app.matchPrefix + "/"
        return NSWorkspace.shared.runningApplications.first { running in
            guard let path = running.executableURL?.resolvingSymlinksInPath().path else {
                return false
            }
            return path.hasPrefix(prefix)
        }
    }

    // 一次 ps 看完所有应用：构建期的 cargo / vite / npm 都带着应用目录的路径。
    private func busyDirectories() -> Set<String> {
        let listing = runCommand("/bin/ps", ["-axo", "command="]) ?? ""
        var busy: Set<String> = []
        for app in apps where listing.contains(app.matchPrefix + "/") {
            busy.insert(app.matchPrefix)
        }
        return busy
    }

    @discardableResult
    private func runCommand(_ path: String, _ arguments: [String]) -> String? {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: path)
        process.arguments = arguments
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = FileHandle.nullDevice
        do {
            try process.run()
        } catch {
            return nil
        }
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        return String(data: data, encoding: .utf8)
    }
}
