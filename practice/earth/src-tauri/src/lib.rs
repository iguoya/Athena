use tauri::Manager;

// 地球是只读的分层浏览：标准模型数据由前端直接导入，Rust 端只做壳——保证进程唯一、窗口前置。
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // 单实例插件必须最先注册。第二份启动时，请第一份把窗口举到前面，然后第二份自己退出。
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_opener::init())
        .run(tauri::generate_context!())
        .expect("地球启动失败");
}
