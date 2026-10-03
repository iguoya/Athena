// windows_subsystem:release 构建下不弹控制台窗口,调试构建保留 stdout 便于排错
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("athena-math-tools 启动失败");
}
