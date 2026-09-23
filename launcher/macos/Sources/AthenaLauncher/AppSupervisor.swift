import AppKit
import Foundation

// 一个应用此刻在哪个状态。判定不在这里做——菜单栏版和跨平台窗口、终端入口
// 共用同一个编排器 `launcher`（ADR 0046），这里只是把它报的状态显示出来。
enum RunState: Equatable {
    case stopped
    case starting
    case hidden   // 已预热：窗口在，但藏着，点一下就现身
    case ready

    var label: String {
        switch self {
        case .stopped: return "未运行"
        case .starting: return "启动中…"
        case .hidden: return "已预热"
        case .ready: return "运行中"
        }
    }

    // 编排器只报三种状态，用的是不会变的标识符（ADR 0048）；"已预热"是菜单栏版
    // 自己的概念，靠窗口是否隐藏区分。
    init(key: String) {
        switch key {
        case "ready": self = .ready
        case "starting": self = .starting
        default: self = .stopped
        }
    }
}

@MainActor
final class AppSupervisor: ObservableObject {
    @Published private(set) var apps: [LearningApp] = []
    @Published private(set) var states: [String: RunState] = [:]
    @Published private(set) var repositoryProblem: String?

    @Published var prewarmIDs: Set<String> {
        didSet { defaults.set(Array(prewarmIDs).sorted(), forKey: Self.prewarmKey) }
    }

    private static let prewarmKey = "PrewarmAppIDs"
    private let defaults = UserDefaults.standard
    private var repository: URL?
    private var orchestrator: URL?
    private var pollTimer: Timer?
    private var pendingHide: Set<String> = []

    init() {
        prewarmIDs = Set(defaults.stringArray(forKey: Self.prewarmKey) ?? [])
        reloadCatalog()
    }

    func reloadCatalog() {
        guard let root = Repository.locate() else {
            repositoryProblem = "找不到 Athena 仓库：请设置 ATHENA_ROOT 环境变量，"
                + "或用 launcher/macos/scripts/install.sh 重新安装一次启动器。"
            apps = []
            return
        }
        repository = root
        orchestrator = Self.locateOrchestrator(in: root)
        guard orchestrator != nil, let listing = runOrchestrator(["list", "--json"]) else {
            repositoryProblem =
                "还没有编排器可用：先在 launcher/ 执行 cargo build -p launcher-core --release。"
            apps = []
            return
        }
        // 清单由编排器给，菜单栏版不自己读 app.json（ADR 0048）。
        apps = AppCatalog.parse(listing)
        repositoryProblem = apps.isEmpty ? "编排器没报出任何应用，检查 subjects/ 下的 app.json。" : nil
    }

    // 优先用 release 产物；开发时 debug 的也认。
    private static func locateOrchestrator(in repository: URL) -> URL? {
        let candidates = ["launcher/target/release/launcher", "launcher/target/debug/launcher"]
        return candidates
            .map { repository.appendingPathComponent($0) }
            .first { FileManager.default.isExecutableFile(atPath: $0.path) }
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
        guard let listing = runOrchestrator(["list", "--json"]) else { return }
        let parsed = AppCatalog.states(listing)

        for app in apps {
            var state = parsed[app.id] ?? .stopped
            // 预热起来的窗口藏起来，免得抢走正在做别的事的人的焦点。
            if let running = runningApplication(for: app) {
                if pendingHide.contains(app.id) {
                    running.hide()
                    pendingHide.remove(app.id)
                }
                if running.isHidden {
                    state = .hidden
                }
            }
            states[app.id] = state
        }
    }

    // MARK: - 动作

    func open(_ app: LearningApp) {
        if let running = runningApplication(for: app), running.isHidden {
            running.unhide()
            running.activate(options: [.activateAllWindows])
            states[app.id] = .ready
            return
        }
        // 已在跑就前置、没跑就构建启动——这套判断在编排器里，菜单栏版不重复一遍。
        states[app.id] = .starting
        runOrchestratorAsync(["open", app.id])
    }

    func prewarm(_ app: LearningApp) {
        guard states[app.id] ?? .stopped == .stopped else { return }
        pendingHide.insert(app.id)
        states[app.id] = .starting
        runOrchestratorAsync(["open", app.id])
    }

    func prewarmAllMarked() {
        for app in apps where prewarmIDs.contains(app.id) {
            prewarm(app)
        }
    }

    func stop(_ app: LearningApp) {
        runOrchestratorAsync(["stop", app.id])
        states[app.id] = .stopped
    }

    func restart(_ app: LearningApp) {
        stop(app)
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) { [weak self] in
            self?.open(app)
        }
    }

    // 位置是编排器算的（三个平台各不相同），这里不重复一遍那套规则。
    func logURL(for app: LearningApp) -> URL {
        app.logURL
    }

    func revealLog(for app: LearningApp) {
        NSWorkspace.shared.open(logURL(for: app))
    }

    // MARK: - 进程

    private func runningApplication(for app: LearningApp) -> NSRunningApplication? {
        let prefix = app.directory.path + "/"
        return NSWorkspace.shared.runningApplications.first { running in
            guard let path = running.executableURL?.resolvingSymlinksInPath().path else {
                return false
            }
            if path.hasPrefix(prefix) {
                return true
            }
            // 共享 cargo 缓存之后二进制不在应用目录里了，按可执行文件名认（ADR 0046）。
            return !app.binary.isEmpty
                && (path as NSString).lastPathComponent == app.binary
        }
    }

    @discardableResult
    private func runOrchestrator(_ arguments: [String]) -> Data? {
        guard let orchestrator else { return nil }
        let process = Process()
        process.executableURL = orchestrator
        process.arguments = arguments
        process.currentDirectoryURL = repository
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
        return data
    }

    // 构建可能要几十秒，绝不能卡住菜单。
    private func runOrchestratorAsync(_ arguments: [String]) {
        guard let orchestrator, let repository else { return }
        DispatchQueue.global(qos: .userInitiated).async {
            let process = Process()
            process.executableURL = orchestrator
            process.arguments = arguments
            process.currentDirectoryURL = repository
            process.standardOutput = FileHandle.nullDevice
            process.standardError = FileHandle.nullDevice
            try? process.run()
            process.waitUntilExit()
        }
    }
}
