// Athena 自考专业调查 — 导引类应用的薄壳：导引内容在构建期打进前端，Rust 侧只开窗口。
// 没有进度库，也没有自定义命令（主仓库 ADR 0174）。

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_opener::init())
        .run(tauri::generate_context!())
        .expect("error while running athena-selfstudy-survey");
}
