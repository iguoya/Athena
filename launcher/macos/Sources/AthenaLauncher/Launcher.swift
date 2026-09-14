import AppKit
import SwiftUI

// 启动器只有两个要求：一直在，且点下去马上有反应。
// 所以它是一个常驻菜单栏的 accessory 应用——没有 Dock 图标、没有主窗口，
// 唯一的界面是一张随点随开的列表。
@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    private let supervisor = AppSupervisor()
    private var statusItem: NSStatusItem!
    private let popover = NSPopover()

    func applicationDidFinishLaunching(_ notification: Notification) {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.image = NSImage(
            systemSymbolName: "graduationcap",
            accessibilityDescription: "Athena 启动器"
        )
        statusItem.button?.target = self
        statusItem.button?.action = #selector(togglePopover)

        popover.behavior = .transient
        popover.animates = false
        popover.contentViewController = NSHostingController(
            rootView: LauncherView(supervisor: supervisor) { [weak self] in
                self?.popover.performClose(nil)
            }
        )

        supervisor.startPolling()
        HotKey.register { [weak self] in self?.togglePopover() }

        // 预热在启动器自己就位之后再开始，别和登录时的其他事情抢资源。
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
            self?.supervisor.prewarmAllMarked()
        }
    }

    @objc private func togglePopover() {
        guard let button = statusItem.button else { return }
        if popover.isShown {
            popover.performClose(nil)
            return
        }
        supervisor.refresh()
        popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
        // accessory 应用的 popover 不主动激活就收不到键盘事件。
        NSApp.activate(ignoringOtherApps: true)
    }
}

@main
enum Launcher {
    @MainActor
    static func main() {
        // 无界面自检：在终端里看一眼启动器都发现了什么、各自在什么状态。
        if CommandLine.arguments.contains("--list") {
            let supervisor = AppSupervisor()
            if let problem = supervisor.repositoryProblem {
                print(problem)
                exit(1)
            }
            supervisor.refresh()
            for app in supervisor.apps {
                let state = supervisor.states[app.id] ?? .stopped
                print("\(app.id)\t\(app.title)\t\(state.label)")
            }
            exit(0)
        }

        // 终端入口：`--open <id>` 等价于在菜单里点一下那一项，
        // 方便把某个应用挂到快捷键、Raycast 或别的脚本上。
        if let index = CommandLine.arguments.firstIndex(of: "--open"),
           index + 1 < CommandLine.arguments.count {
            let wanted = CommandLine.arguments[index + 1]
            let supervisor = AppSupervisor()
            guard let app = supervisor.apps.first(where: { $0.id == wanted }) else {
                print("没有这个应用：\(wanted)")
                exit(1)
            }
            supervisor.open(app)
            // 子进程交给 launchd 继续跑，这里只要确认已经发出去了。
            Thread.sleep(forTimeInterval: 0.5)
            exit(0)
        }

        // 离屏渲染一张菜单截图：不用真的点开菜单栏，也能检查这张列表长什么样。
        if let index = CommandLine.arguments.firstIndex(of: "--snapshot"),
           index + 1 < CommandLine.arguments.count {
            let application = NSApplication.shared
            application.setActivationPolicy(.accessory)
            let supervisor = AppSupervisor()
            supervisor.refresh()
            let view = NSHostingView(
                rootView: LauncherView(supervisor: supervisor, onOpen: {})
            )
            view.frame = NSRect(origin: .zero, size: view.fittingSize)
            guard let bitmap = view.bitmapImageRepForCachingDisplay(in: view.bounds) else {
                exit(1)
            }
            view.cacheDisplay(in: view.bounds, to: bitmap)
            let url = URL(fileURLWithPath: CommandLine.arguments[index + 1])
            try? bitmap.representation(using: .png, properties: [:])?.write(to: url)
            exit(0)
        }

        let application = NSApplication.shared
        let delegate = AppDelegate()
        application.delegate = delegate
        application.setActivationPolicy(.accessory)
        application.run()
    }
}
