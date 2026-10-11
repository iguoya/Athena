// Athena 赛历 — 参考类应用的薄壳：赛事数据在构建期打进前端，Rust 侧只开窗口和
// 把官网交给系统浏览器（opener）。没有进度库，也没有自定义命令（ADR 0114）。

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .run(tauri::generate_context!())
        .expect("error while running athena-competitions");
}
