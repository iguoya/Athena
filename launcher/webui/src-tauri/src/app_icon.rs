//! 任务栏 / Dock 上的启动器图标。
//!
//! 图片是 `icons/icon.png`（与 `webui/public/tiger-mark.png` 同一张虎头）。
//! 各平台认的路不一样，Tauri 的窗口图标盖不住：
//!
//! - **macOS**：裸二进制没有 `.app`，Dock 不读 Info.plist。Tauri 只在 dev
//!   构建（没开 `custom-protocol`）里调 `setApplicationIconImage`，release
//!   会落成通用图标。这里两种构建都设。
//! - **Windows**：任务栏用 `ICON_BIG`，标题栏用 `ICON_SMALL`。tao 创建窗口时
//!   只填了小图标，大图标传的是 `None`，等于把任务栏那一格清掉。这里从
//!   tauri-build 写进 exe 的 `.ico`（资源号 32512）再装回去，系统按 DPI 挑帧。
//! - **Linux**：X11 的 `_NET_WM_ICON` 由 Tauri 的默认窗口图标覆盖。Wayland
//!   不收窗口图标，只认 app-id 对应的 `.desktop`；没有那份文件时图标缺失是
//!   平台限制。

/// 窗口已经建好之后调用。
pub fn install(window: &tauri::WebviewWindow) {
    #[cfg(target_os = "macos")]
    {
        let _ = window;
        macos::install();
    }
    #[cfg(windows)]
    windows::install(window);
    #[cfg(not(any(target_os = "macos", windows)))]
    let _ = window;
}

#[cfg(target_os = "macos")]
mod macos {
    use objc2::AnyThread;
    use objc2_app_kit::{NSApplication, NSImage};
    use objc2_foundation::{MainThreadMarker, NSData};

    /// 256px，和窗口里的虎头是同一份像素。
    static PNG: &[u8] = include_bytes!("../icons/icon.png");

    pub fn install() {
        let Some(marker) = MainThreadMarker::new() else {
            eprintln!("Dock 图标没设上：不在主线程，Dock 会显示通用图标。");
            return;
        };
        let data = NSData::with_bytes(PNG);
        let Some(image) = NSImage::initWithData(NSImage::alloc(), &data) else {
            eprintln!("Dock 图标的 PNG 解码失败，Dock 会显示通用图标。");
            return;
        };
        // SAFETY: NSImage 有效，且 MainThreadMarker 保证在主线程。
        unsafe { NSApplication::sharedApplication(marker).setApplicationIconImage(Some(&image)) };
    }
}

#[cfg(windows)]
mod windows {
    use std::ffi::c_void;

    const WM_SETICON: u32 = 0x0080;
    const ICON_BIG: usize = 1;
    const IMAGE_ICON: u32 = 1;
    const SM_CXICON: i32 = 11;
    const SM_CYICON: i32 = 12;
    /// tauri-build 用 `set_icon_with_id(..., "32512")` 写进 exe 的资源号。
    const ICON_RESOURCE_ID: usize = 32512;

    #[link(name = "kernel32")]
    unsafe extern "system" {
        fn GetModuleHandleW(name: *const u16) -> *mut c_void;
    }

    #[link(name = "user32")]
    unsafe extern "system" {
        fn GetSystemMetrics(index: i32) -> i32;
        fn LoadImageW(
            hinst: *mut c_void,
            name: *const u16,
            typ: u32,
            cx: i32,
            cy: i32,
            flags: u32,
        ) -> *mut c_void;
        fn SendMessageW(hwnd: *mut c_void, msg: u32, wparam: usize, lparam: isize) -> isize;
    }

    pub fn install(window: &tauri::WebviewWindow) {
        let hwnd = match window.hwnd() {
            Ok(hwnd) => hwnd.0,
            Err(err) => {
                eprintln!("任务栏图标没设上，拿不到窗口句柄：{err}");
                return;
            }
        };
        unsafe {
            let cx = GetSystemMetrics(SM_CXICON).max(32);
            let cy = GetSystemMetrics(SM_CYICON).max(32);
            // MAKEINTRESOURCE：低字是资源号，不是字符串指针。
            let hicon = LoadImageW(
                GetModuleHandleW(std::ptr::null()),
                ICON_RESOURCE_ID as *const u16,
                IMAGE_ICON,
                cx,
                cy,
                0,
            );
            if hicon.is_null() {
                eprintln!("任务栏图标没设上，exe 资源段里没有虎头。");
                return;
            }
            SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon as isize);
        }
    }
}
