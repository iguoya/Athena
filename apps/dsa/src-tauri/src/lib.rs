// Athena DSA — 独立壳：内容路径、进度库、C++ 即时编译运行。
// 不依赖主程序头文件或 athena.json。

mod compiler;

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


fn detect_clang_format() -> String {
    for cand in ["clang-format", "clang-format-18", "clang-format-16", "clang-format-15"] {
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

/// 交给 clang-format 排版。没装它就报错说清楚装什么——不自己实现一个劣化版
/// 缩进器顶替（主仓库 AGENTS.md 的基线：使用者是开发者，工具视为已装）。
#[tauri::command]
fn format_cpp(source: String) -> Result<String, String> {
    let tool = detect_clang_format();
    if tool.is_empty() {
        return Err(if cfg!(windows) {
            "没找到 clang-format。装 LLVM，或 MSYS2 后 \
             pacman -S mingw-w64-ucrt-x86_64-clang-tools-extra。"
        } else if cfg!(target_os = "macos") {
            "没找到 clang-format。brew install clang-format"
        } else {
            "没找到 clang-format。apt install clang-format 或 dnf install clang-tools-extra。"
        }
        .to_string());
    }
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    let work = std::env::temp_dir().join(format!("athena-dsa-fmt-{stamp}"));
    fs::create_dir_all(&work).map_err(|e| e.to_string())?;
    let src = work.join("main.cpp");
    fs::write(&src, &source).map_err(|e| format!("写入待格式化源码失败：{e}"))?;
    let out = Command::new(&tool)
        .args([
            "-style={BasedOnStyle: LLVM, IndentWidth: 4, UseTab: Never, ColumnLimit: 100}",
            src.to_str().unwrap_or(""),
        ])
        .output();
    let _ = fs::remove_dir_all(&work);
    match out {
        Ok(o) if o.status.success() => {
            let formatted = String::from_utf8_lossy(&o.stdout).to_string();
            if formatted.trim().is_empty() {
                Ok(source)
            } else {
                Ok(formatted)
            }
        }
        _ => Ok(source),
    }
}

fn ensure_own_schema(path: &Path) -> Result<(), String> {
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute_batch(
        "PRAGMA journal_mode=WAL;
         CREATE TABLE IF NOT EXISTS knowledge_progress (
           function_id TEXT PRIMARY KEY,
           mastery INTEGER NOT NULL DEFAULT 0,
           updated_at TEXT
         );
         CREATE TABLE IF NOT EXISTS lab_progress (
           lab_key TEXT PRIMARY KEY,
           status TEXT NOT NULL DEFAULT 'tried',
           updated_at TEXT
         );
         CREATE TABLE IF NOT EXISTS lab_draft (
           lab_key TEXT PRIMARY KEY,
           source TEXT NOT NULL,
           updated_at TEXT
         );
         CREATE TABLE IF NOT EXISTS quiz_picks (
           quiz_key TEXT PRIMARY KEY,
           picks TEXT NOT NULL,
           updated_at TEXT
         );",
    )
    .map_err(|e| e.to_string())?;

    // 兼容早期只有 passed 列的库：补 status，并按 passed 回填。
    let has_status = {
        let mut stmt = conn
            .prepare("PRAGMA table_info(lab_progress)")
            .map_err(|e| e.to_string())?;
        let cols: Vec<String> = stmt
            .query_map([], |row| row.get::<_, String>(1))
            .map_err(|e| e.to_string())?
            .filter_map(|r| r.ok())
            .collect();
        cols.iter().any(|c| c == "status")
    };
    if !has_status {
        let _ = conn.execute("ALTER TABLE lab_progress ADD COLUMN status TEXT", []);
        let _ = conn.execute(
            "UPDATE lab_progress SET status = CASE WHEN IFNULL(passed, 0) = 1 THEN 'done' ELSE 'tried' END
             WHERE status IS NULL OR status = ''",
            [],
        );
    }
    Ok(())
}

#[tauri::command]
fn get_app_info(state: tauri::State<'_, Mutex<AppState>>) -> AppInfo {
    let s = state.lock().unwrap();
    AppInfo {
        title: "数据结构与算法".into(),
        content_root: s.content_root.display().to_string(),
        store_path: s.store_path.display().to_string(),
        compiler: compiler::detect().map(|c| c.label()).unwrap_or_default(),
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

fn safe_path_segment(raw: &str) -> String {
    let s: String = raw
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '_' || c == '-' || c == '.' {
                c
            } else {
                '_'
            }
        })
        .collect();
    if s.is_empty() || s == "." || s == ".." {
        "_".into()
    } else {
        s
    }
}

#[tauri::command]
fn compile_and_run(
    state: tauri::State<'_, Mutex<AppState>>,
    case_id: String,
    entrypoint: String,
    source: String,
) -> Result<RunResult, String> {
    // 用编辑器里的源码写到临时目录再编译，不要回写 content/cases/：
    // 开发时 Vite 会监视那些文件，一保存就整页刷新，看起来像「运行完跳回主页」。
    let compiler = compiler::detect().ok_or_else(|| compiler::install_hint().to_string())?;

    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    let case_seg = safe_path_segment(&case_id);
    let entry_seg = safe_path_segment(&entrypoint);
    let work = std::env::temp_dir().join(format!("athena-dsa-{case_seg}-{stamp}"));
    fs::create_dir_all(&work).map_err(|e| e.to_string())?;
    let src = work.join(&entry_seg);
    fs::write(&src, source).map_err(|e| format!("写入临时源码失败：{e}"))?;
    let obj = work.join(compiler.artifact_name());

    let started = SystemTime::now();
    // 案例共享头（如 dsa_trace.hpp）放 content/cases/_shared；挂上 include
    // 路径后案例 `#include "dsa_trace.hpp"` 即可用（ADR 0004）。
    let shared = {
        let s = state.lock().unwrap();
        s.content_root.join("content/cases/_shared")
    };
    let include = shared.is_dir().then_some(shared.as_path());
    let compile = compiler
        .compile_command(&src, &obj, include)
        .output()
        .map_err(|e| format!("启动 {} 失败：{e}", compiler.label()))?;

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

#[tauri::command]
fn save_lab_status(
    state: tauri::State<'_, Mutex<AppState>>,
    lab_key: String,
    status: String,
) -> Result<(), String> {
    let status = match status.as_str() {
        "done" | "tried" | "started" => status,
        _ => return Err(format!("非法实验状态：{status}")),
    };
    let s = state.lock().unwrap();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO lab_progress(lab_key, status, updated_at)
         VALUES(?1, ?2, datetime('now'))
         ON CONFLICT(lab_key) DO UPDATE SET
           status = excluded.status,
           updated_at = excluded.updated_at",
        rusqlite::params![lab_key, status],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn load_all_lab_status(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<std::collections::HashMap<String, String>, String> {
    let s = state.lock().unwrap();
    let mut map = std::collections::HashMap::new();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT lab_key, status FROM lab_progress")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            let key: String = row.get(0)?;
            let status: Option<String> = row.get(1)?;
            Ok((key, status.unwrap_or_else(|| "tried".into())))
        })
        .map_err(|e| e.to_string())?;
    for row in rows.flatten() {
        let st = match row.1.as_str() {
            "done" => "done",
            "started" => "started",
            _ => "tried",
        };
        map.insert(row.0, st.to_string());
    }
    Ok(map)
}

#[tauri::command]
fn save_lab_draft(
    state: tauri::State<'_, Mutex<AppState>>,
    lab_key: String,
    source: String,
) -> Result<(), String> {
    let s = state.lock().unwrap();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO lab_draft(lab_key, source, updated_at)
         VALUES(?1, ?2, datetime('now'))
         ON CONFLICT(lab_key) DO UPDATE SET
           source = excluded.source,
           updated_at = excluded.updated_at",
        rusqlite::params![lab_key, source],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn load_all_lab_drafts(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<std::collections::HashMap<String, String>, String> {
    let s = state.lock().unwrap();
    let mut map = std::collections::HashMap::new();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT lab_key, source FROM lab_draft")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)))
        .map_err(|e| e.to_string())?;
    for row in rows.flatten() {
        map.insert(row.0, row.1);
    }
    Ok(map)
}

#[tauri::command]
fn clear_lab_draft(
    state: tauri::State<'_, Mutex<AppState>>,
    lab_key: String,
) -> Result<(), String> {
    let s = state.lock().unwrap();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute("DELETE FROM lab_draft WHERE lab_key = ?1", [lab_key])
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn save_quiz_picks(
    state: tauri::State<'_, Mutex<AppState>>,
    quiz_key: String,
    picks: String,
) -> Result<(), String> {
    let s = state.lock().unwrap();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO quiz_picks(quiz_key, picks, updated_at)
         VALUES(?1, ?2, datetime('now'))
         ON CONFLICT(quiz_key) DO UPDATE SET
           picks = excluded.picks,
           updated_at = excluded.updated_at",
        rusqlite::params![quiz_key, picks],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn load_all_quiz_picks(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<std::collections::HashMap<String, String>, String> {
    let s = state.lock().unwrap();
    let mut map = std::collections::HashMap::new();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare("SELECT quiz_key, picks FROM quiz_picks")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)))
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
            format_cpp,
            load_mastery,
            save_mastery,
            load_all_mastery,
            save_lab_status,
            load_all_lab_status,
            save_lab_draft,
            load_all_lab_drafts,
            clear_lab_draft,
            save_quiz_picks,
            load_all_quiz_picks
        ])
        .run(tauri::generate_context!())
        .expect("error while running athena-dsa");
}
