// Athena 陈怀琛《实用大众线性代数（MATLAB 版）》精读 — 独立壳：内容路径、进度库。壳要薄：课树与题目都在 content/，不进 Rust。

use serde::Serialize;
use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::State;

struct AppState {
    content_root: PathBuf,
    /// 本应用自己的进度库：自建、自迁移，不依赖别的应用（主仓库 ADR 0037）。
    store_path: PathBuf,
}

#[derive(Clone, Serialize)]
struct AttemptRow {
    knowledge_id: String,
    item_id: String,
    correct: bool,
    answered_at: u64,
}

fn content_root() -> PathBuf {
    if let Ok(root) = std::env::var("ATHENA_CHEN_LINEAR_ALGEBRA_ROOT") {
        return PathBuf::from(root).join("content");
    }
    // 发行包：按实际可执行文件找，不依赖编译机上烙进去的绝对路径。
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            let roots = [
                dir.to_path_buf(),
                dir.join(".."),
                // macOS .app：Tauri 把 ../content 打包到 Resources/_up_/content。
                dir.join("../Resources/_up_"),
            ];
            for root in roots {
                let candidate = root.join("content");
                if candidate.join("curriculum.json").is_file() {
                    return candidate;
                }
            }
        }
    }
    PathBuf::from("content")
}

fn store_path() -> PathBuf {
    // 进度库放用户数据目录，不进仓库（主仓库 ADR 0155）；目录名登记在 app.json 的 progress.dir，两处必须一致。
    let base = dirs_next::data_dir().unwrap_or_else(|| PathBuf::from("."));
    base.join("AthenaChenLinearAlgebra").join("learning.db")
}

/// 内容 id 只允许字母数字与 . - _，防止界面传来的 id 钻出内容目录。
fn is_safe_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 128
        && !id.contains("..")
        && id.chars().all(|c| c.is_ascii_alphanumeric() || c == '.' || c == '-' || c == '_')
}

fn read_json(path: &Path) -> Result<Value, String> {
    let text = fs::read_to_string(path).map_err(|e| format!("读 {} 失败：{}", path.display(), e))?;
    serde_json::from_str(&text).map_err(|e| format!("{} 不是合法 JSON：{}", path.display(), e))
}

fn open_store(path: &Path) -> Result<rusqlite::Connection, String> {
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    // 与同步代理约定的事件表：只增不改，key = (knowledge_id, item_id, answered_at)（app.json 的 progress）。
    conn.execute(
        "CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            correct INTEGER NOT NULL,
            answered_at INTEGER NOT NULL
        )",
        [],
    )
    .map_err(|e| e.to_string())?;
    Ok(conn)
}

#[tauri::command]
fn get_curriculum(state: State<AppState>) -> Result<Value, String> {
    read_json(&state.content_root.join("curriculum.json"))
}

/// 一节的段落快照（content/sections/<id>.json）。
#[tauri::command]
fn get_section(state: State<AppState>, section_id: String) -> Result<Value, String> {
    if !is_safe_id(&section_id) {
        return Err(format!("非法节引用：{section_id}"));
    }
    read_json(&state.content_root.join("sections").join(format!("{section_id}.json")))
}

/// 一节的练习题（content/exercises/<id>.json，题源为原书例题与习题）；没有就返回 null。
#[tauri::command]
fn get_exercises(state: State<AppState>, section_id: String) -> Result<Value, String> {
    if !is_safe_id(&section_id) {
        return Err(format!("非法节引用：{section_id}"));
    }
    let path = state.content_root.join("exercises").join(format!("{section_id}.json"));
    if !path.is_file() {
        return Ok(Value::Null);
    }
    read_json(&path)
}

/// 一幅图的 SVG（content/figures/<图名>.svg，由 scripts/render_figures.py 渲染）；还没有就返回 null。
#[tauri::command]
fn get_figure(state: State<AppState>, fig_id: String) -> Result<Option<String>, String> {
    if !is_safe_id(&fig_id) {
        return Err(format!("非法图引用：{fig_id}"));
    }
    let path = state.content_root.join("figures").join(format!("{fig_id}.svg"));
    if !path.is_file() {
        return Ok(None);
    }
    fs::read_to_string(&path).map(Some).map_err(|e| format!("读 {} 失败：{}", path.display(), e))
}

#[tauri::command]
fn record_attempt(state: State<AppState>, knowledge_id: String, item_id: String, correct: bool) -> Result<(), String> {
    let conn = open_store(&state.store_path)?;
    let now = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    conn.execute(
        "INSERT INTO attempts (knowledge_id, item_id, correct, answered_at) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![knowledge_id, item_id, correct as i64, now],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_attempts(state: State<AppState>) -> Result<Vec<AttemptRow>, String> {
    let conn = open_store(&state.store_path)?;
    let mut stmt = conn
        .prepare("SELECT knowledge_id, item_id, correct, answered_at FROM attempts ORDER BY answered_at, id")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok(AttemptRow {
                knowledge_id: row.get(0)?,
                item_id: row.get(1)?,
                correct: row.get::<_, i64>(2)? != 0,
                answered_at: row.get(3)?,
            })
        })
        .map_err(|e| e.to_string())?;
    rows.collect::<Result<Vec<_>, _>>().map_err(|e| e.to_string())
}

pub fn run() {
    let state = AppState { content_root: content_root(), store_path: store_path() };
    let _ = open_store(&state.store_path);
    tauri::Builder::default()
    .plugin(tauri_plugin_updater::Builder::new().build())
    .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_opener::init())
        .manage(state)
        .invoke_handler(tauri::generate_handler![get_curriculum, get_section, get_exercises, get_figure, record_attempt, get_attempts])
        .run(tauri::generate_context!())
        .expect("error while running athena-chen-linear-algebra");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn content_ids_reject_path_tricks() {
        for ok in ["basic_operations", "calculus", "a.b_c-1"] {
            assert!(is_safe_id(ok), "{ok} 应当合法");
        }
        for bad in ["", "..", "../x", "a/b", "a\\b", "/etc/passwd", "C:x", "a..b", "x y"] {
            assert!(!is_safe_id(bad), "{bad} 应当被拒绝");
        }
        assert!(!is_safe_id(&"a".repeat(129)), "过长的 id 应当被拒绝");
    }

    #[test]
    fn attempts_roundtrip_in_answer_order() {
        let dir = std::env::temp_dir().join(format!("athena-cla-test-{}", std::process::id()));
        let path = dir.join("learning.db");
        let conn = open_store(&path).unwrap();
        // 后入库但答题时间更早的记录（同步拉回的旧记录）必须排在前面：「最近一次」按 answered_at 认。
        conn.execute("INSERT INTO attempts (knowledge_id,item_id,correct,answered_at) VALUES ('k','i',1,200)", []).unwrap();
        conn.execute("INSERT INTO attempts (knowledge_id,item_id,correct,answered_at) VALUES ('k','i',0,100)", []).unwrap();
        let mut stmt = conn.prepare("SELECT answered_at FROM attempts ORDER BY answered_at, id").unwrap();
        let got: Vec<u64> = stmt.query_map([], |r| r.get(0)).unwrap().map(|x| x.unwrap()).collect();
        assert_eq!(got, vec![100, 200]);
        let _ = std::fs::remove_dir_all(&dir);
    }
}
