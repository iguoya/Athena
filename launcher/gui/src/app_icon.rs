//! 任务栏 / Dock / 窗口管理器里的应用图标。
//!
//! 图片本身仍是 `assets/tiger.svg`（build.rs 渲染），这里只解决「各平台各自认哪条路」：
//!
//! - **Windows**：任务栏用 `ICON_BIG`，标题栏用 `ICON_SMALL`。Slint 在窗口创建前只把
//!   `Window.icon` 塞进 winit 的 `window_icon`（只设小图标），大图标没人设，任务栏
//!   就成了空白。这里窗口显示后直接从 exe 资源段加载多尺寸 `.ico`，让系统按 DPI
//!   挑最合适的一帧，比把 256px 位图缩下来清楚。
//! - **macOS**：裸二进制没有 `.app` bundle，Dock 读不到图标；`Window.icon` 在 macOS
//!   上也不生效。运行时给 `NSApplication` 设 `applicationIconImage`。
//! - **Linux**：X11 读 `_NET_WM_ICON`（Slint 已按 `Window.icon` 设好）；Wayland 不收
//!   窗口图标，只认 app-id 对应的 `.desktop` 文件里的 `Icon=`。app-id 在这里设，
//!   `.desktop` 文件见 README「图标」一节。没有这个文件时 Wayland 下图标缺失是平台限制。

/// 与 `.desktop` 文件名、macOS bundle id 的最后一段保持一致。
#[cfg(target_os = "linux")]
const XDG_APP_ID: &str = "athena-launcher";

/// 窗口创建之前调用：Linux 的 app-id 只能在创建窗口前设。
pub fn prepare() {
    #[cfg(target_os = "linux")]
    if let Err(err) = slint::set_xdg_app_id(XDG_APP_ID) {
        eprintln!("设置 xdg app-id 失败：{err}（Wayland 下任务栏可能认不出图标）");
    }
}

/// 窗口 `show()` 之后调用：底层窗口此刻才存在。
#[cfg(target_os = "windows")]
pub fn install(window: &slint::Window) {
    use slint::winit_030::winit::platform::windows::{IconExtWindows, WindowExtWindows};
    use slint::winit_030::winit::window::Icon;
    use slint::winit_030::WinitWindowAccessor;

    /// `winresource::set_icon` 把图标登记成 1 号资源（build.rs）。
    const RESOURCE_ID: u16 = 1;

    let applied = window.with_winit_window(|winit| match Icon::from_resource(RESOURCE_ID, None) {
        Ok(icon) => {
            winit.set_taskbar_icon(Some(icon));
            true
        }
        Err(err) => {
            eprintln!("从 exe 资源段读不到任务栏图标：{err}");
            false
        }
    });
    if applied != Some(true) {
        eprintln!("任务栏图标没有设上，系统会退回通用图标。");
    }
}

#[cfg(target_os = "macos")]
pub fn install(_window: &slint::Window) {
    use objc2::AnyThread;
    use objc2_app_kit::{NSApplication, NSImage};
    use objc2_foundation::{MainThreadMarker, NSData};

    static PNG: &[u8] = include_bytes!(concat!(env!("OUT_DIR"), "/dock-icon.png"));

    let Some(marker) = MainThreadMarker::new() else {
        return;
    };
    let data = NSData::with_bytes(PNG);
    let Some(image) = NSImage::initWithData(NSImage::alloc(), &data) else {
        eprintln!("Dock 图标的 PNG 解码失败，Dock 会显示通用图标。");
        return;
    };
    // SAFETY: 传入的是有效的 NSImage，且在主线程调用。
    unsafe { NSApplication::sharedApplication(marker).setApplicationIconImage(Some(&image)) };
}

#[cfg(not(any(target_os = "windows", target_os = "macos")))]
pub fn install(_window: &slint::Window) {}
