mod private;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // Self-update from GitHub Releases on launch (ADR 0018).
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        // 「导入本地资料」选文件夹（ADR 0025）。
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            private::read_private_english2,
            private::private_status,
            private::import_private,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Lumi");
}
