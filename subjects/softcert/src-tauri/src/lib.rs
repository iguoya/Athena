mod store;

use store::{AttemptRecorded, KpSummary, Store, TodayStats};

#[tauri::command]
fn record_attempt(
    course: String,
    chapter_id: String,
    kp_id: String,
    question_id: String,
    correct: bool,
    mode: String,
) -> Result<AttemptRecorded, String> {
    Store::open()
        .map_err(|e| e.to_string())?
        .record_attempt(&course, &chapter_id, &kp_id, &question_id, correct, &mode)
        .map_err(|e| e.to_string())
}

#[tauri::command]
fn attempts_summary() -> Result<Vec<KpSummary>, String> {
    Store::open().map_err(|e| e.to_string())?.attempts_summary().map_err(|e| e.to_string())
}

#[tauri::command]
fn today_stats() -> Result<TodayStats, String> {
    Store::open().map_err(|e| e.to_string())?.today_stats().map_err(|e| e.to_string())
}

#[tauri::command]
fn load_setting(key: String) -> Result<Option<String>, String> {
    Store::open().map_err(|e| e.to_string())?.get_setting(&key).map_err(|e| e.to_string())
}

#[tauri::command]
fn save_setting(key: String, value: String) -> Result<(), String> {
    Store::open().map_err(|e| e.to_string())?.set_setting(&key, &value).map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            record_attempt,
            attempts_summary,
            today_stats,
            load_setting,
            save_setting
        ])
        .run(tauri::generate_context!())
        .expect("error while running athena-softcert");
}
