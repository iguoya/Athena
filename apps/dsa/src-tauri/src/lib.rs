// Athena DSA — 独立壳：内容路径、进度库、C++ 即时编译运行。
// 不依赖主程序头文件或 athena.json。

use serde::Serialize;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

struct AppState {
    content_root: PathBuf,
    /// 本应用自己的进度库：自建、自迁移，不依赖主程序是否跑过（ADR 0037）。
    store_path: PathBuf,
}

#[derive(Clone, Serialize)]
struct AppInfo {
    title: String,
    content_root: String,
    store_path: String,
    compiler: String,
}

#[derive(Serialize)]
struct RunResult {
    ok: bool,
    compile_log: String,
    stdout: String,
    stderr: String,
    duration_ms: u128,
}

fn content_root() -> PathBuf {
    if let Ok(root) = std::env::var("ATHENA_DSA_ROOT") {
        return PathBuf::from(root);
    }

    // 先按实际可执行文件找，避免发行包错误依赖编译机上由
    // CARGO_MANIFEST_DIR 烙进去的绝对源码路径。
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

    // 开发：src-tauri 的上一级就是 apps/dsa。
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let dev = manifest.join("..");
    dev.canonicalize().unwrap_or(dev)
}

fn own_store_path() -> PathBuf {
    let base = dirs_next::data_dir().unwrap_or_else(|| PathBuf::from("."));
    let dir = base.join("AthenaDSA");
    let _ = fs::create_dir_all(&dir);
    dir.join("learning.db")
}

fn parse_cli() {
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            // 进度库不再共享（ADR 0037）。老版本主程序仍会传这个参数，
            // 为它退出会让用户只看到"点了没反应"，所以吃掉并记一行。
            "--store" => {
                let ignored = args.next().unwrap_or_default();
                eprintln!("已忽略 --store {ignored}：本应用使用自己的进度库");
            }
            "--help" | "-h" => {
                eprintln!(
                    "用法：athena-dsa\n\n\
                     进度写入本应用自己的库，完全独立运行。\n\
                     --store <路径> 仅为兼容旧版主程序而接受，会被忽略。"
                );
                std::process::exit(0);
            }
            "--version" => {
                println!("athena-dsa {}", env!("CARGO_PKG_VERSION"));
                std::process::exit(0);
            }
            other => {
                eprintln!("无法识别的参数：{other}");
                std::process::exit(2);
            }
        }
    }
}

fn detect_compiler() -> String {
    for cand in ["c++", "clang++", "g++"] {
        if Command::new(cand)
            .arg("--version")
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false)
        {
            return cand.to_string();
        }
    }
    String::new()
}

fn ensure_own_schema(path: &Path) -> Result<(), String> {
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute_batch(
        "PRAGMA journal_mode=WAL;
         CREATE TABLE IF NOT EXISTS knowledge_progress (
           function_id TEXT PRIMARY KEY,
           mastery INTEGER NOT NULL DEFAULT 0,
           updated_at TEXT
         );",
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_app_info(state: tauri::State<'_, Mutex<AppState>>) -> AppInfo {
    let s = state.lock().unwrap();
    AppInfo {
        title: "数据结构与算法".into(),
        content_root: s.content_root.display().to_string(),
        store_path: s.store_path.display().to_string(),
        compiler: detect_compiler(),
    }
}

#[tauri::command]
fn load_curriculum(state: tauri::State<'_, Mutex<AppState>>) -> Result<serde_json::Value, String> {
    let s = state.lock().unwrap();
    let path = s.content_root.join("content/curriculum.json");
    let text =
        fs::read_to_string(&path).map_err(|e| format!("无法读取课表 {}: {e}", path.display()))?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

#[tauri::command]
fn load_case_source(
    state: tauri::State<'_, Mutex<AppState>>,
    case_id: String,
    entrypoint: String,
) -> Result<String, String> {
    let s = state.lock().unwrap();
    let path = s
        .content_root
        .join("content/cases")
        .join(&case_id)
        .join(&entrypoint);
    fs::read_to_string(&path).map_err(|e| format!("{}: {e}", path.display()))
}

#[tauri::command]
fn save_case_source(
    state: tauri::State<'_, Mutex<AppState>>,
    case_id: String,
    entrypoint: String,
    source: String,
) -> Result<(), String> {
    let s = state.lock().unwrap();
    let path = s
        .content_root
        .join("content/cases")
        .join(&case_id)
        .join(&entrypoint);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(&path, source).map_err(|e| e.to_string())
}

#[tauri::command]
fn compile_and_run(
    state: tauri::State<'_, Mutex<AppState>>,
    case_id: String,
    entrypoint: String,
) -> Result<RunResult, String> {
    let s = state.lock().unwrap();
    let src = s
        .content_root
        .join("content/cases")
        .join(&case_id)
        .join(&entrypoint);
    if !src.is_file() {
        return Err(format!("找不到源文件 {}", src.display()));
    }
    let compiler = detect_compiler();
    if compiler.is_empty() {
        return Err("未找到 c++ / clang++ / g++，请先安装本机 C++ 编译器。".into());
    }

    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    let work = std::env::temp_dir().join(format!("athena-dsa-{case_id}-{stamp}"));
    fs::create_dir_all(&work).map_err(|e| e.to_string())?;
    let obj = work.join("a.out");

    let started = SystemTime::now();
    let compile = Command::new(&compiler)
        .args([
            "-std=c++20",
            "-O0",
            "-Wall",
            "-Wextra",
            src.to_str().unwrap_or(""),
            "-o",
            obj.to_str().unwrap_or(""),
        ])
        .output()
        .map_err(|e| format!("启动编译器失败：{e}"))?;

    let mut compile_log = String::new();
    compile_log.push_str(&String::from_utf8_lossy(&compile.stderr));
    compile_log.push_str(&String::from_utf8_lossy(&compile.stdout));

    if !compile.status.success() {
        let _ = fs::remove_dir_all(&work);
        return Ok(RunResult {
            ok: false,
            compile_log,
            stdout: String::new(),
            stderr: String::new(),
            duration_ms: started.elapsed().unwrap_or_default().as_millis(),
        });
    }

    let run = Command::new(&obj)
        .current_dir(&work)
        .output()
        .map_err(|e| format!("运行失败：{e}"))?;
    let _ = fs::remove_dir_all(&work);

    let mut stdout = String::from_utf8_lossy(&run.stdout).to_string();
    let mut stderr = String::from_utf8_lossy(&run.stderr).to_string();
    // 限制输出体积，避免前端卡死
    const LIMIT: usize = 200_000;
    if stdout.len() > LIMIT {
        stdout.truncate(LIMIT);
        stdout.push_str("\n…（输出已截断）\n");
    }
    if stderr.len() > LIMIT {
        stderr.truncate(LIMIT);
        stderr.push_str("\n…（输出已截断）\n");
    }

    Ok(RunResult {
        ok: run.status.success(),
        compile_log,
        stdout,
        stderr,
        duration_ms: started.elapsed().unwrap_or_default().as_millis(),
    })
}

#[tauri::command]
fn load_mastery(state: tauri::State<'_, Mutex<AppState>>, topic_id: String) -> Result<i32, String> {
    let s = state.lock().unwrap();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT mastery FROM knowledge_progress WHERE function_id = ?1")
        .map_err(|e| e.to_string())?;
    let mastery = stmt.query_row([&topic_id], |row| row.get(0)).unwrap_or(0);
    Ok(mastery)
}

#[tauri::command]
fn save_mastery(
    state: tauri::State<'_, Mutex<AppState>>,
    topic_id: String,
    mastery: i32,
) -> Result<(), String> {
    let mastery = mastery.clamp(0, 5);
    let s = state.lock().unwrap();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO knowledge_progress(function_id, mastery, updated_at)
         VALUES(?1, ?2, datetime('now'))
         ON CONFLICT(function_id) DO UPDATE SET
           mastery = excluded.mastery,
           updated_at = excluded.updated_at",
        rusqlite::params![topic_id, mastery],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn load_all_mastery(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<std::collections::HashMap<String, i32>, String> {
    let s = state.lock().unwrap();
    let mut map = std::collections::HashMap::new();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT function_id, mastery FROM knowledge_progress")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, i32>(1)?))
        })
        .map_err(|e| e.to_string())?;
    for row in rows.flatten() {
        map.insert(row.0, row.1);
    }
    Ok(map)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    parse_cli();
    let store_path = own_store_path();
    let _ = ensure_own_schema(&store_path);
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
            load_case_source,
            save_case_source,
            compile_and_run,
            load_mastery,
            save_mastery,
            load_all_mastery
        ])
        .run(tauri::generate_context!())
        .expect("error while running athena-dsa");
}
