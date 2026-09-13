// Athena Mathematics — 独立壳：内容路径与进度库。
// 不依赖主程序头文件或 athena.json（主仓库 ADR 0032）。
// Rust 侧不做数学：符号计算全在前端（本应用 ADR 0001、0010）。

use serde::Serialize;
use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

struct AppState {
    content_root: PathBuf,
    /// 本应用自己的进度库：自建、自迁移，不共用主程序的库（主仓库 ADR 0037）。
    store_path: PathBuf,
}

#[derive(Clone, Serialize)]
struct AppInfo {
    title: String,
    subject: String,
    content_root: String,
    store_path: String,
}

/// 一条进度记录。按 (topic, depth) 二元组存，因为同一知识点分三层深度（ADR 0012）。
#[derive(Serialize)]
struct ProgressRow {
    topic_id: String,
    depth: String,
    status: String,
    updated_at: i64,
}

/// 一次预测的记录。存的是事实（选了什么、对不对），不是分数或奖励（ADR 0011 第 4 节）。
#[derive(Serialize)]
struct PredictionRow {
    topic_id: String,
    exp_id: String,
    picked: String,
    correct: bool,
    updated_at: i64,
}

fn content_root() -> PathBuf {
    if let Ok(root) = std::env::var("ATHENA_MATH_ROOT") {
        return PathBuf::from(root);
    }

    // 先按实际可执行文件找，避免发行包依赖编译机上烙进去的绝对源码路径。
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            let roots = [
                dir.to_path_buf(),
                dir.join(".."),
                // macOS .app：Tauri 把 ../content 打包到 Resources/_up_/content。
                dir.join("../Resources/_up_"),
                dir.join("../Resources"),
            ];
            for root in roots {
                if root.join("content/curriculum.json").is_file() {
                    return root.canonicalize().unwrap_or(root);
                }
            }
        }
    }

    // 开发：src-tauri 的上一级就是 apps/mathematics。
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let dev = manifest.join("..");
    dev.canonicalize().unwrap_or(dev)
}

fn own_store_path() -> PathBuf {
    let base = dirs_next::data_dir().unwrap_or_else(|| PathBuf::from("."));
    let dir = base.join("AthenaMath");
    let _ = fs::create_dir_all(&dir);
    dir.join("learning.db")
}

fn now() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0)
}

fn ensure_schema(path: &PathBuf) -> Result<(), String> {
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS progress (
            topic_id   TEXT NOT NULL,
            depth      TEXT NOT NULL,
            status     TEXT NOT NULL,
            updated_at INTEGER NOT NULL,
            PRIMARY KEY (topic_id, depth)
         );
         CREATE TABLE IF NOT EXISTS predictions (
            topic_id   TEXT NOT NULL,
            exp_id     TEXT NOT NULL,
            picked     TEXT NOT NULL,
            correct    INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            PRIMARY KEY (topic_id, exp_id)
         );",
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_app_info(state: tauri::State<'_, Mutex<AppState>>) -> Result<AppInfo, String> {
    let s = state.lock().unwrap();
    Ok(AppInfo {
        title: "数学自学".into(),
        subject: "math2".into(),
        content_root: s.content_root.display().to_string(),
        store_path: s.store_path.display().to_string(),
    })
}

#[tauri::command]
fn load_curriculum(state: tauri::State<'_, Mutex<AppState>>) -> Result<serde_json::Value, String> {
    let s = state.lock().unwrap();
    let path = s.content_root.join("content/curriculum.json");
    let text = fs::read_to_string(&path)
        .map_err(|e| format!("读取课表失败 {}：{e}", path.display()))?;
    serde_json::from_str(&text).map_err(|e| format!("课表 JSON 解析失败：{e}"))
}

#[tauri::command]
fn save_progress(
    state: tauri::State<'_, Mutex<AppState>>,
    topic_id: String,
    depth: String,
    status: String,
) -> Result<(), String> {
    let s = state.lock().unwrap();
    ensure_schema(&s.store_path)?;
    let conn = rusqlite::Connection::open(&s.store_path).map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO progress (topic_id, depth, status, updated_at) VALUES (?1, ?2, ?3, ?4)
         ON CONFLICT(topic_id, depth) DO UPDATE SET status = ?3, updated_at = ?4",
        rusqlite::params![topic_id, depth, status, now()],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn load_all_progress(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<Vec<ProgressRow>, String> {
    let s = state.lock().unwrap();
    ensure_schema(&s.store_path)?;
    let conn = rusqlite::Connection::open(&s.store_path).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT topic_id, depth, status, updated_at FROM progress")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |r| {
            Ok(ProgressRow {
                topic_id: r.get(0)?,
                depth: r.get(1)?,
                status: r.get(2)?,
                updated_at: r.get(3)?,
            })
        })
        .map_err(|e| e.to_string())?;
    Ok(rows.flatten().collect())
}

#[tauri::command]
fn save_prediction(
    state: tauri::State<'_, Mutex<AppState>>,
    topic_id: String,
    exp_id: String,
    picked: String,
    correct: bool,
) -> Result<(), String> {
    let s = state.lock().unwrap();
    ensure_schema(&s.store_path)?;
    let conn = rusqlite::Connection::open(&s.store_path).map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO predictions (topic_id, exp_id, picked, correct, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5)
         ON CONFLICT(topic_id, exp_id) DO UPDATE SET picked = ?3, correct = ?4, updated_at = ?5",
        rusqlite::params![topic_id, exp_id, picked, correct as i32, now()],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn load_all_predictions(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<Vec<PredictionRow>, String> {
    let s = state.lock().unwrap();
    ensure_schema(&s.store_path)?;
    let conn = rusqlite::Connection::open(&s.store_path).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT topic_id, exp_id, picked, correct, updated_at FROM predictions")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |r| {
            Ok(PredictionRow {
                topic_id: r.get(0)?,
                exp_id: r.get(1)?,
                picked: r.get(2)?,
                correct: r.get::<_, i32>(3)? != 0,
                updated_at: r.get(4)?,
            })
        })
        .map_err(|e| e.to_string())?;
    Ok(rows.flatten().collect())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let store_path = own_store_path();
    let _ = ensure_schema(&store_path);
    let _ = writeln!(std::io::stderr(), "进度写入 {}", store_path.display());

    let state = AppState {
        content_root: content_root(),
        store_path,
    };

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(Mutex::new(state))
        .invoke_handler(tauri::generate_handler![
            get_app_info,
            load_curriculum,
            save_progress,
            load_all_progress,
            save_prediction,
            load_all_predictions
        ])
        .run(tauri::generate_context!())
        .expect("error while running athena-math");
}
