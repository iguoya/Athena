// Athena 九州 — 图谱/参考类薄壳：编年与地点数据在构建期打进前端，Rust 侧只开窗口
//（ADR 0156）。疆域与 3D 高潮都在前端，不进 Rust。

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
    .plugin(tauri_plugin_updater::Builder::new().build())
    .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_opener::init())
        .run(tauri::generate_context!())
        .expect("error while running athena-jiuzhou");
}
