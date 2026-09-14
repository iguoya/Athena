import AppKit
import Carbon.HIToolbox

// 全局快捷键：不需要辅助功能权限，Carbon 这套老 API 至今是最省事的做法。
// 回调是 C 函数指针，捕获不了上下文，所以处理动作只能放在文件级变量里。
nonisolated(unsafe) private var hotKeyAction: (() -> Void)?

enum HotKey {
    // 默认 ⌃⌥A：⌘Space 是聚焦搜索、⌥Space 常被 Raycast 占着，避开它们。
    static func register(keyCode: UInt32 = UInt32(kVK_ANSI_A),
                         modifiers: UInt32 = UInt32(controlKey | optionKey),
                         action: @escaping () -> Void) {
        hotKeyAction = action

        var eventType = EventTypeSpec(
            eventClass: OSType(kEventClassKeyboard),
            eventKind: UInt32(kEventHotKeyPressed)
        )
        InstallEventHandler(
            GetApplicationEventTarget(),
            { _, _, _ in
                DispatchQueue.main.async { hotKeyAction?() }
                return noErr
            },
            1,
            &eventType,
            nil,
            nil
        )

        let id = EventHotKeyID(signature: OSType(0x41544845), id: 1) // 'ATHE'
        var reference: EventHotKeyRef?
        RegisterEventHotKey(keyCode, modifiers, id, GetApplicationEventTarget(), 0, &reference)
    }
}
