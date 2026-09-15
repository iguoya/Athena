import AppKit
import ServiceManagement
import SwiftUI

struct LauncherView: View {
    @ObservedObject var supervisor: AppSupervisor
    var onOpen: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            header

            if let problem = supervisor.repositoryProblem {
                Text(problem)
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(12)
            } else {
                ForEach(supervisor.apps) { app in
                    AppRow(
                        app: app,
                        state: supervisor.states[app.id] ?? .stopped,
                        isPrewarmed: supervisor.prewarmIDs.contains(app.id),
                        supervisor: supervisor,
                        onOpen: onOpen
                    )
                }
            }

            Divider().padding(.vertical, 6)
            footer
        }
        .padding(.vertical, 8)
        .frame(width: 340)
    }

    private var header: some View {
        HStack {
            Text("Athena 学习应用")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(.secondary)
            Spacer()
            Text("⌃⌥A")
                .font(.system(size: 11, design: .monospaced))
                .foregroundStyle(.tertiary)
        }
        .padding(.horizontal, 14)
        // 上下都要留：只给 .bottom 的话，标题会贴着弹窗顶边，而底部有
        // MenuRow 自己的 .vertical padding 撑着，整块看起来就偏上了。
        .padding(.top, 4)
        .padding(.bottom, 6)
    }

    private var footer: some View {
        VStack(alignment: .leading, spacing: 2) {
            MenuRow(title: "登录时自动启动启动器", systemImage: "power") {
                toggleLoginItem()
            }
            MenuRow(title: "重新扫描应用清单", systemImage: "arrow.clockwise") {
                supervisor.reloadCatalog()
                supervisor.refresh()
            }
            MenuRow(title: "退出启动器", systemImage: "xmark.circle") {
                NSApp.terminate(nil)
            }
        }
    }

    private func toggleLoginItem() {
        do {
            if SMAppService.mainApp.status == .enabled {
                try SMAppService.mainApp.unregister()
            } else {
                try SMAppService.mainApp.register()
            }
        } catch {
            NSSound.beep()
        }
    }
}

private struct AppRow: View {
    let app: LearningApp
    let state: RunState
    let isPrewarmed: Bool
    @ObservedObject var supervisor: AppSupervisor
    var onOpen: () -> Void

    @State private var hovering = false

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: app.symbol)
                .font(.system(size: 15))
                .frame(width: 22)
                .foregroundStyle(.secondary)

            VStack(alignment: .leading, spacing: 1) {
                Text(app.title)
                    .font(.system(size: 14))
                HStack(spacing: 5) {
                    Circle()
                        .fill(statusColor)
                        .frame(width: 6, height: 6)
                    Text(state.label)
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                    if isPrewarmed {
                        Text("· 开机预热")
                            .font(.system(size: 11))
                            .foregroundStyle(.tertiary)
                    }
                }
            }

            Spacer()

            Menu {
                Button("重新启动") { supervisor.restart(app) }
                Button("停止") { supervisor.stop(app) }
                    .disabled(state == .stopped)
                Divider()
                Toggle("开机预热", isOn: Binding(
                    get: { isPrewarmed },
                    set: { on in
                        if on {
                            supervisor.prewarmIDs.insert(app.id)
                        } else {
                            supervisor.prewarmIDs.remove(app.id)
                        }
                    }
                ))
                Divider()
                Button("查看启动日志") { supervisor.revealLog(for: app) }
                Button("在访达中显示") {
                    NSWorkspace.shared.selectFile(
                        nil,
                        inFileViewerRootedAtPath: app.directory.path
                    )
                }
            } label: {
                Image(systemName: "ellipsis")
            }
            .menuStyle(.borderlessButton)
            .menuIndicator(.hidden)
            .frame(width: 22)
            .opacity(hovering ? 1 : 0)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 6)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(hovering ? Color.accentColor.opacity(0.14) : .clear)
                .padding(.horizontal, 8)
        )
        .contentShape(Rectangle())
        .onHover { hovering = $0 }
        .onTapGesture {
            supervisor.open(app)
            onOpen()
        }
    }

    // 状态用色按通行约定：绿=就绪、黄=进行中、蓝=待命、灰=停止。
    private var statusColor: Color {
        switch state {
        case .ready: return .green
        case .starting: return .orange
        case .hidden: return .blue
        case .stopped: return .secondary
        }
    }
}

private struct MenuRow: View {
    let title: String
    let systemImage: String
    let action: () -> Void

    @State private var hovering = false

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: systemImage)
                .font(.system(size: 12))
                .frame(width: 22)
                .foregroundStyle(.secondary)
            Text(title).font(.system(size: 13))
            Spacer()
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 5)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(hovering ? Color.accentColor.opacity(0.14) : .clear)
                .padding(.horizontal, 8)
        )
        .contentShape(Rectangle())
        .onHover { hovering = $0 }
        .onTapGesture(perform: action)
    }
}
