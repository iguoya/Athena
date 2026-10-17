//! 托盘常驻与开机自启（ADR 0125；0127 的缺口在此补上）。
//!
//! 窗口是可选的详细视图。关掉窗口只是藏起来，进程留在托盘；
//! 退出走托盘菜单「退出启动器」，或系统自己的退出（macOS 的 Cmd+Q）。
//! 托盘建不起来时不拦截关窗，否则进程会变成没有入口的后台残留。
//!
//! 开机自启默认关。勾选状态从系统实况读，启动器不另记账：
//! macOS 是 `~/Library/LaunchAgents/athena-launcher.plist`（LaunchAgent，
//! 开发二进制不是 .app，不能走登录项），Windows 是 HKCU 的 Run 键，
//! Linux 是 XDG autostart。登录拉起时带 `--autostart`，窗口不弹出。

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};

use launcher_core::{discover_all, runner};
use tauri::menu::{CheckMenuItem, Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{AppHandle, Emitter, Manager, WebviewWindow};
use tauri_plugin_autostart::ManagerExt;

/// 登录拉起时附加的参数。平时手动打开不带它，窗口照常出现。
pub const AUTOSTART_ARG: &str = "--autostart";

pub fn launched_hidden() -> bool {
    std::env::args().any(|arg| arg == AUTOSTART_ARG)
}

/// 主窗口是否正显示着。状态探测靠它决定要不要扫进程表。
pub struct Shown(pub Arc<AtomicBool>);

/// 托盘图标句柄。清单变化时整份菜单换上，不重建图标。
pub struct TraySlot(pub Mutex<Option<tauri::tray::TrayIcon>>);

/// 窗口可见性翻转：记下标志，并叫醒状态探测线程。
pub fn note_visibility(app: &AppHandle, on: bool) {
    if let Some(shown) = app.try_state::<Shown>() {
        shown.0.store(on, Ordering::SeqCst);
    }
    crate::watch::poke();
}

/// 按当前清单做一份托盘菜单。应用条目的 id 是契约（`open:` / `stop:`），
/// 换菜单时点击处理不用跟着换。
fn build_menu(app: &AppHandle, repo: &std::path::Path) -> Result<Menu<tauri::Wry>, String> {
    let autostart_on = app.autolaunch().is_enabled().unwrap_or(false);
    let menu = Menu::new(app).map_err(|e| e.to_string())?;
    for entry in discover_all(repo).iter().filter(|entry| !entry.hidden) {
        let sub = Submenu::with_id(app, format!("app:{}", entry.id), &entry.title, true)
            .map_err(|e| e.to_string())?;
        let open = MenuItem::with_id(
            app,
            format!("open:{}", entry.id),
            "打开",
            true,
            None::<&str>,
        )
        .map_err(|e| e.to_string())?;
        let stop = MenuItem::with_id(
            app,
            format!("stop:{}", entry.id),
            "停止",
            true,
            None::<&str>,
        )
        .map_err(|e| e.to_string())?;
        sub.append(&open).map_err(|e| e.to_string())?;
        sub.append(&stop).map_err(|e| e.to_string())?;
        menu.append(&sub).map_err(|e| e.to_string())?;
    }
    menu.append(&PredefinedMenuItem::separator(app).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;

    let rescan = MenuItem::with_id(app, "rescan", "扫描应用目录", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    menu.append(&rescan).map_err(|e| e.to_string())?;

    let autostart = CheckMenuItem::with_id(
        app,
        "autostart",
        "开机自启",
        true,
        autostart_on,
        None::<&str>,
    )
    .map_err(|e| e.to_string())?;
    menu.append(&autostart).map_err(|e| e.to_string())?;

    let show = MenuItem::with_id(app, "show", "显示启动器", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    menu.append(&show).map_err(|e| e.to_string())?;
    let quit = MenuItem::with_id(app, "quit", "退出启动器", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    menu.append(&quit).map_err(|e| e.to_string())?;
    Ok(menu)
}

/// 清单或开机自启勾选变了，整份菜单换上。从后台线程调用：`set_menu` 会
/// 把活派回主线程再等它完成，调用方若已在主线程上就会自己等自己。
pub fn refresh_menu(app: &AppHandle) -> Result<(), String> {
    let Some(slot) = app.try_state::<TraySlot>() else {
        return Ok(());
    };
    let guard = slot.0.lock().unwrap_or_else(|p| p.into_inner());
    let Some(icon) = guard.as_ref() else {
        return Ok(());
    };
    let repo = app.state::<crate::Repo>().0.clone();
    let menu = build_menu(app, &repo)?;
    icon.set_menu(Some(menu)).map_err(|e| e.to_string())
}

/// 建托盘并拦住关窗。失败时调用方继续显示窗口，关窗即退出。
pub fn install(
    app: &AppHandle,
    window: &WebviewWindow,
    quitting: Arc<AtomicBool>,
) -> Result<tauri::tray::TrayIcon, String> {
    let repo = app.state::<crate::Repo>().0.clone();
    let menu = build_menu(app, &repo)?;
    let quitting_for_menu = Arc::clone(&quitting);
    let image = tauri::image::Image::from_bytes(include_bytes!("../icons/32x32.png"))
        .map_err(|e| format!("托盘图标读不出来：{e}"))?;

    // 句柄留给 refresh_menu 换菜单。丢掉最后一份 TrayIcon 会把托盘卸掉。
    let tray = TrayIconBuilder::with_id("main-tray")
        .icon(image)
        .tooltip("Athena 启动器")
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(move |app, event| {
            handle_menu(app, event.id().as_ref(), &quitting_for_menu);
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                show_main(tray.app_handle());
            }
        })
        .build(app)
        .map_err(|e| e.to_string())?;

    let window_for_event = window.clone();
    window.on_window_event(move |event| {
        if let tauri::WindowEvent::CloseRequested { api, .. } = event {
            if quitting.load(Ordering::SeqCst) {
                return;
            }
            api.prevent_close();
            let _ = window_for_event.hide();
            // 前端靠这个事件停 3D 帧循环；状态探测同时停掉，托盘里不再扫进程表。
            note_visibility(window_for_event.app_handle(), false);
            let _ = window_for_event.app_handle().emit("launcher://visibility", false);
        }
    });
    Ok(tray)
}

pub fn show_main(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.unminimize();
        let _ = window.set_focus();
    }
    note_visibility(app, true);
    let _ = app.emit("launcher://visibility", true);
}

fn handle_menu(app: &AppHandle, id: &str, quitting: &AtomicBool) {
    if id == "autostart" {
        toggle_autostart(app);
        // 菜单回调多半在主线程。refresh_menu 要等主线程把新菜单装上，
        // 不能在这里同步等，否则自己等自己。
        let app = app.clone();
        std::thread::spawn(move || {
            if let Err(error) = refresh_menu(&app) {
                eprintln!("托盘菜单没能按开机自启状态重建：{error}");
            }
        });
        return;
    }
    if id == "rescan" {
        let app = app.clone();
        std::thread::spawn(move || {
            if let Err(error) = crate::watch::rescan(&app) {
                eprintln!("扫描应用目录失败：{error}");
            }
        });
        return;
    }
    if id == "show" {
        show_main(app);
        return;
    }
    if id == "quit" {
        quitting.store(true, Ordering::SeqCst);
        app.exit(0);
        return;
    }
    let (action, target) = if let Some(target) = id.strip_prefix("open:") {
        ("open", target.to_string())
    } else if let Some(target) = id.strip_prefix("stop:") {
        ("stop", target.to_string())
    } else {
        return;
    };
    let repo = app.state::<crate::Repo>().0.clone();
    // launch 会跑完整构建链（数十秒），不能堵在菜单回调上。
    tauri::async_runtime::spawn_blocking(move || {
        let apps = discover_all(&repo);
        let Some(app_cfg) = apps.iter().find(|entry| entry.id == target) else {
            return;
        };
        let result = match action {
            "open" => runner::launch(app_cfg, &repo, |_| {}).map(|_| ()),
            _ => runner::stop(app_cfg),
        };
        if let Err(error) = result {
            eprintln!("托盘动作 {action} {target} 失败：{error}");
        }
    });
}

fn toggle_autostart(app: &AppHandle) {
    let auto = app.autolaunch();
    let currently = auto.is_enabled().unwrap_or(false);
    let result = if currently { auto.disable() } else { auto.enable() };
    if let Err(error) = result {
        eprintln!("开机自启切换失败：{error}");
    }
}
