// Athena GTKMM — 独立壳：内容路径、进度库、演示进程 spawn 与 JSON-RPC 转发。
// 不依赖主程序或其他应用。壳要薄：业务文案与课树不进 Rust（应用 ADR 0001）。

use serde::Serialize;
use serde_json::{json, Value};
use base64::Engine as _;
use std::collections::HashMap;
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::{AppHandle, Emitter, State};

struct AppState {
    content_root: PathBuf,
    /// 本应用自己的进度库：自建、自迁移，不依赖别的应用（ADR 0037、0053）。
    store_path: PathBuf,
    demos: Mutex<HashMap<String, Child>>,
}

#[derive(Clone, Serialize)]
struct LaunchResult {
    ok: bool,
    message: String,
}

#[derive(Clone, Serialize)]
struct AttemptRow {
    knowledge_id: String,
    item_id: String,
    correct: bool,
    answered_at: u64,
}

fn content_root() -> PathBuf {
    if let Ok(root) = std::env::var("ATHENA_GTKMM_ROOT") {
        return PathBuf::from(root).join("content");
    }

    // 先按实际可执行文件找，避免发行包错误依赖编译机上烙进去的绝对路径。
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
    // 开发模式（app.json dev.env 给了应用根）进度随仓库走；发行副本退回用户目录。
    if let Ok(root) = std::env::var("ATHENA_GTKMM_ROOT") {
        return PathBuf::from(root).join("progress").join("learning.db");
    }
    let base = dirs_next::data_dir().unwrap_or_else(|| PathBuf::from("."));
    base.join("AthenaGTKMM").join("learning.db")
}

fn read_content(root: &Path, name: &str) -> Result<Value, String> {
    let path = root.join(name);
    let text = fs::read_to_string(&path)
        .map_err(|error| format!("读 {} 失败：{}", path.display(), error))?;
    serde_json::from_str(&text).map_err(|error| format!("{} 不是合法 JSON：{}", name, error))
}

/// 演示产物命名规则与 scripts/check.py 的 check_native 一致：id 中的 `.` 换成 `-`。
fn demo_binary(app_root: &Path, demo_id: &str) -> PathBuf {
    let stem = demo_id.replace('.', "-");
    let base = app_root.join("build-native").join(&stem);
    if cfg!(windows) {
        let exe = base.with_extension("exe");
        if exe.is_file() {
            return exe;
        }
    }
    base
}

/// 从清单里找实体（演示与实验同表），返回 (id, source_dir)。
fn find_entity(manifest: &Value, demo_id: &str) -> Option<Value> {
    for kind in ["demos", "experiments"] {
        if let Some(items) = manifest.get(kind).and_then(|v| v.as_array()) {
            for entity in items {
                if entity.get("id").and_then(|v| v.as_str()) == Some(demo_id) {
                    return Some(entity.clone());
                }
            }
        }
    }
    None
}

fn init_store(path: &Path) -> rusqlite::Connection {
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let connection = rusqlite::Connection::open(path)
        .unwrap_or_else(|error| panic!("打开进度库 {} 失败：{}", path.display(), error));
    connection
        .execute(
            "CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                correct INTEGER NOT NULL,
                answered_at INTEGER NOT NULL
            )",
            [],
        )
        .expect("建 attempts 表失败");
    connection
}

#[tauri::command]
fn get_curriculum(state: State<AppState>) -> Result<Value, String> {
    read_content(&state.content_root, "curriculum.json")
}

#[tauri::command]
fn get_manifest(state: State<AppState>) -> Result<Value, String> {
    read_content(&state.content_root, "demos.json")
}

/// 英译训练标注数据（content/vocab.json：难词表 + 句型表）。
#[tauri::command]
fn get_vocab(state: State<AppState>) -> Result<Value, String> {
    read_content(&state.content_root, "vocab.json")
}

/// 官方节页的段落快照（content/chapters/<章>/<节>.json，原文+逐段中文，
/// 由 scripts/sync_upstream.py 生成——应用 ADR 0002 的段落级追踪）。
#[tauri::command]
fn get_page_content(state: State<AppState>, chapter_id: String, page_id: String) -> Result<String, String> {
    let path = state
        .content_root
        .join("chapters")
        .join(&chapter_id)
        .join(format!("{page_id}.json"));
    fs::read_to_string(&path).map_err(|error| format!("读 {} 失败：{}", path.display(), error))
}

/// 官方教程插图：读 content/ 下的图片文件，返回 data URL。
/// 图片与快照 JSON 走同一条 command 通道——开发模式不赌 vite 对仓库根的
/// 静态服务，发行包也不受资源目录在 webview HTTP 空间里的布局影响；
/// 这条链路在任何启动形态下（dev / build / 打包）行为都一致。
#[tauri::command]
fn get_figure(state: State<AppState>, image_ref: String) -> Result<String, String> {
    // 路径安全：只接受 content/ 内的相对引用，拒绝目录穿越、绝对路径与盘符
    if image_ref.is_empty()
        || image_ref.contains("..")
        || image_ref.contains('\\')
        || image_ref.starts_with('/')
        || image_ref.contains(':')
    {
        return Err(format!("非法图片引用：{image_ref}"));
    }
    let path = state.content_root.join(&image_ref);
    let bytes = fs::read(&path)
        .map_err(|error| format!("读 {} 失败：{}", path.display(), error))?;
    let mime = match path
        .extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.to_ascii_lowercase())
        .as_deref()
    {
        Some("png") => "image/png",
        Some("jpg" | "jpeg") => "image/jpeg",
        Some("gif") => "image/gif",
        Some("svg") => "image/svg+xml",
        Some("webp") => "image/webp",
        _ => return Err(format!("不支持的图片格式：{}", path.display())),
    };
    Ok(format!(
        "data:{mime};base64,{}",
        base64::engine::general_purpose::STANDARD.encode(bytes)
    ))
}

#[tauri::command]
fn record_attempt(
    state: State<AppState>,
    knowledge_id: String,
    item_id: String,
    correct: bool,
) -> Result<(), String> {
    let connection = rusqlite::Connection::open(&state.store_path)
        .map_err(|error| error.to_string())?;
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    connection
        .execute(
            "INSERT INTO attempts (knowledge_id, item_id, correct, answered_at) VALUES (?1, ?2, ?3, ?4)",
            rusqlite::params![knowledge_id, item_id, correct as i64, now],
        )
        .map_err(|error| error.to_string())?;
    Ok(())
}

/// 补正机制：按 item_id 列表清除作答记录（重置某章/节的测验与自评）。
#[tauri::command]
fn reset_attempts(state: State<AppState>, item_ids: Vec<String>) -> Result<(), String> {
    let connection = rusqlite::Connection::open(&state.store_path)
        .map_err(|error| error.to_string())?;
    for item_id in &item_ids {
        connection
            .execute("DELETE FROM attempts WHERE item_id = ?1", rusqlite::params![item_id])
            .map_err(|error| error.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn get_attempts(state: State<AppState>) -> Result<Vec<AttemptRow>, String> {
    if !state.store_path.exists() {
        return Ok(vec![]);
    }
    let connection = rusqlite::Connection::open(&state.store_path)
        .map_err(|error| error.to_string())?;
    let mut statement = connection
        .prepare("SELECT knowledge_id, item_id, correct, answered_at FROM attempts ORDER BY id")
        .map_err(|error| error.to_string())?;
    let rows = statement
        .query_map([], |row| {
            Ok(AttemptRow {
                knowledge_id: row.get(0)?,
                item_id: row.get(1)?,
                correct: row.get::<_, i64>(2)? != 0,
                answered_at: row.get(3)?,
            })
        })
        .map_err(|error| error.to_string())?;
    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|error| error.to_string())
}

#[tauri::command]
fn launch_demo(app: AppHandle, state: State<AppState>, demo_id: String) -> LaunchResult {
    let Ok(manifest) = read_content(&state.content_root, "demos.json") else {
        return LaunchResult { ok: false, message: "读 demos.json 失败".into() };
    };
    if find_entity(&manifest, &demo_id).is_none() {
        return LaunchResult { ok: false, message: format!("清单里没有 {}", demo_id) };
    }
    // build-native 在应用根（check.py 的 CMake 输出目录）。
    let app_root = state
        .content_root
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_default();
    let binary = demo_binary(&app_root, &demo_id);
    if !binary.is_file() {
        return LaunchResult {
            ok: false,
            message: format!(
                "演示尚未编译：{} 不存在。先运行 python3 scripts/check.py 完成编译。",
                binary.display()
            ),
        };
    }

    let mut child = match Command::new(&binary)
        .arg("--demo-id")
        .arg(&demo_id)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
    {
        Ok(child) => child,
        Err(error) => {
            return LaunchResult { ok: false, message: format!("启动失败：{}", error) };
        }
    };

    // initialize：协议握手（应用 ADR 0001 决策 5）。
    if let Some(stdin) = child.stdin.as_mut() {
        let request = json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": { "demo_id": demo_id, "protocol_version": 1 }
        });
        let _ = writeln!(stdin, "{}", request);
    }

    // 上行事件转发给前端：每行一个 JSON-RPC 消息（NDJSON）。
    if let Some(stdout) = child.stdout.take() {
        let emitter = app.clone();
        let demo_id = demo_id.clone();
        thread::spawn(move || {
            for line in BufReader::new(stdout).lines() {
                let Ok(line) = line else { break };
                let Ok(message) = serde_json::from_str::<Value>(&line) else { continue };
                let method = message.get("method").and_then(|v| v.as_str()).unwrap_or("");
                let params = message.get("params").cloned().unwrap_or(json!({}));
                let _ = emitter.emit(
                    "demo-event",
                    serde_json::json!({ "demo_id": demo_id, "method": method, "params": params }),
                );
            }
        });
    }

    state.demos.lock().unwrap().insert(demo_id.clone(), child);
    LaunchResult { ok: true, message: format!("{} 已启动", demo_id) }
}

#[tauri::command]
fn stop_demo(state: State<AppState>, demo_id: String) -> Result<(), String> {
    if let Some(mut child) = state.demos.lock().unwrap().remove(&demo_id) {
        if let Some(stdin) = child.stdin.as_mut() {
            let _ = writeln!(stdin, r#"{{"jsonrpc":"2.0","id":2,"method":"shutdown"}}"#);
        }
        thread::spawn(move || {
            thread::sleep(std::time::Duration::from_millis(500));
            let _ = child.kill();
        });
    }
    Ok(())
}

pub fn run() {
    let content_root = content_root();
    let store = store_path();
    let state = AppState {
        content_root: content_root.clone(),
        store_path: store.clone(),
        demos: Mutex::new(HashMap::new()),
    };
    let _ = init_store(&store);

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(state)
        .invoke_handler(tauri::generate_handler![
            get_curriculum,
            get_manifest,
            get_page_content,
            get_figure,
            get_vocab,
            record_attempt,
            reset_attempts,
            get_attempts,
            launch_demo,
            stop_demo
        ])
        .run(tauri::generate_context!())
        .expect("error while running athena-gtkmm");
}
