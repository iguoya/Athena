// 教程壳只做三件事：读某一章的源码、按白名单编译并启动那一章、把作答写入进度库。
// 贪吃蛇本体在 exercise/ 的 raylib 程序里，不在这个壳里。

use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use rusqlite::{params, Connection};

const CHAPTERS: &[(&str, &str)] = &[
    ("01-window", "snake-01"),
    ("02-grid", "snake-02"),
    ("03-body", "snake-03"),
    ("04-input", "snake-04"),
    ("05-food", "snake-05"),
    ("06-state", "snake-06"),
    ("07-score", "snake-07"),
    ("08-logic", "snake-08"),
    ("09-test", "snake-09"),
    ("10-polish", "snake-10"),
];

fn app_root() -> Result<PathBuf, String> {
    if let Ok(root) = std::env::var("ATHENA_SNAKE_ROOT") {
        let path = PathBuf::from(root);
        if path.join("app.json").is_file() {
            return Ok(path);
        }
    }
    let mut cursor = std::env::current_dir().map_err(|e| e.to_string())?;
    for _ in 0..6 {
        if cursor.join("app.json").is_file() && cursor.join("content").is_dir() {
            return Ok(cursor);
        }
        if !cursor.pop() {
            break;
        }
    }
    Err("找不到应用根目录（需要 app.json 和 content/）".into())
}

fn database_path() -> Result<PathBuf, String> {
    // 进度库放用户数据目录，不进仓库（ADR 0155）：启动器的同步代理在能连上路由器时
    // 把它与中心库互推。目录名登记在 app.json 的 progress.dir，两处必须一致。
    let dir = dirs_next::data_dir()
        .ok_or("找不到用户数据目录")?
        .join("AthenaSnake");
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    Ok(dir.join("learning.db"))
}

fn open_db() -> Result<Connection, String> {
    let conn = Connection::open(database_path()?).map_err(|e| e.to_string())?;
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_id TEXT NOT NULL,
            correct INTEGER NOT NULL,
            answered_at INTEGER NOT NULL
        );",
    )
    .map_err(|e| e.to_string())?;
    Ok(conn)
}

fn mingw_bin() -> Option<PathBuf> {
    let candidate = PathBuf::from(r"C:\msys64\mingw64\bin");
    if candidate.is_dir() {
        Some(candidate)
    } else {
        None
    }
}

fn with_toolchain(cmd: &mut Command) {
    if let Some(bin) = mingw_bin() {
        let old = std::env::var_os("PATH").unwrap_or_default();
        let mut paths = vec![bin.clone()];
        paths.extend(std::env::split_paths(&old));
        if let Ok(joined) = std::env::join_paths(paths) {
            cmd.env("PATH", joined);
        }
        cmd.env(
            "PKG_CONFIG_PATH",
            bin.parent()
                .unwrap_or(Path::new("."))
                .join("lib")
                .join("pkgconfig"),
        );
    }
}

fn run_tool(dir: &Path, program: &str, args: &[&str]) -> Result<String, String> {
    let mut cmd = Command::new(program);
    cmd.args(args).current_dir(dir);
    with_toolchain(&mut cmd);
    let output = cmd
        .output()
        .map_err(|e| format!("无法启动 {program}：{e}。需要 CMake（Windows 用 Visual Studio 或 MSYS2 的都可以）；raylib 不用预装，首次配置会自动联网拉取源码"))?;
    let mut text = String::new();
    text.push_str(&String::from_utf8_lossy(&output.stdout));
    text.push_str(&String::from_utf8_lossy(&output.stderr));
    if !output.status.success() {
        let tail = text.chars().rev().take(2400).collect::<String>();
        let tail = tail.chars().rev().collect::<String>();
        return Err(format!("{program} 失败\n{tail}"));
    }
    Ok(text)
}

fn allowed_source(path: &Path) -> bool {
    match path.file_name().and_then(|name| name.to_str()) {
        Some("CMakeLists.txt") => true,
        _ => matches!(
            path.extension().and_then(|ext| ext.to_str()),
            Some("cc" | "hh" | "h")
        ),
    }
}

#[tauri::command]
fn read_source(relative: String) -> Result<String, String> {
    if relative.contains("..") || relative.contains(':') {
        return Err("只允许读 exercise/ 下面的源文件".into());
    }
    let root = app_root()?;
    let exercise = root.join("exercise");
    let path = root.join(&relative);
    if !allowed_source(&path) {
        return Err("只读源码和 CMakeLists.txt".into());
    }
    let canon = path.canonicalize().map_err(|e| e.to_string())?;
    let exercise = exercise.canonicalize().map_err(|e| e.to_string())?;
    if !canon.starts_with(&exercise) {
        return Err("只允许读 exercise/ 下面的源文件".into());
    }
    let bytes = fs::read(&canon).map_err(|e| e.to_string())?;
    if bytes.len() > 256 * 1024 {
        return Err("文件太大".into());
    }
    String::from_utf8(bytes).map_err(|e| e.to_string())
}

fn run_chapter_sync(id: String) -> Result<String, String> {
    let (dir_name, exe_name) = CHAPTERS
        .iter()
        .find(|(key, _)| *key == id)
        .copied()
        .ok_or("未知章节")?;
    let root = app_root()?;
    let dir = root.join("exercise").join(dir_name);
    if !dir.join("CMakeLists.txt").is_file() {
        return Err(format!("{dir_name} 没有 CMakeLists.txt"));
    }
    // 十章共享一份 raylib 下载缓存：FetchContent 只在第一次联网拉源码。
    let cache = root.join(".cache").join("fetchcontent");
    std::fs::create_dir_all(&cache).map_err(|e| e.to_string())?;
    let cache_arg = format!("-DFETCHCONTENT_BASE_DIR={}", cache.display());
    if !dir.join("build").join("CMakeCache.txt").is_file() {
        run_tool(&dir, "cmake", &["-B", "build", cache_arg.as_str()])?;
    }
    run_tool(&dir, "cmake", &["--build", "build"])?;
    let exe = if cfg!(windows) {
        dir.join("build").join(format!("{exe_name}.exe"))
    } else {
        dir.join("build").join(exe_name)
    };
    if !exe.is_file() {
        return Err(format!("编译过了，但没有找到 {}", exe.display()));
    }
    let mut cmd = Command::new(&exe);
    with_toolchain(&mut cmd);
    cmd.spawn()
        .map_err(|e| format!("编译过了，但启动 {} 失败：{e}", exe.display()))?;
    Ok(format!("已启动 {exe_name}"))
}

#[tauri::command]
async fn run_chapter(id: String) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || run_chapter_sync(id))
        .await
        .map_err(|e| e.to_string())?
}

/// 每道题只看最近一次作答。答对的 id 交给界面，用来把整章标绿。
#[tauri::command]
fn passed_questions() -> Result<Vec<String>, String> {
    let conn = open_db()?;
    let mut stmt = conn
        .prepare(
            // 「最近一次」按作答时间认，同一秒再按行号：同步拉回的旧记录入库晚、id 更大，
            // 按 id 认会把别的设备昨天的答错当成最近一次，盖掉本机刚答对的（ADR 0155）。
            "SELECT DISTINCT a.function_id FROM attempts a
             WHERE a.correct = 1
               AND NOT EXISTS (SELECT 1 FROM attempts b
                               WHERE b.function_id = a.function_id
                                 AND (b.answered_at > a.answered_at
                                      OR (b.answered_at = a.answered_at AND b.id > a.id)))",
        )
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| row.get(0))
        .map_err(|e| e.to_string())?;
    rows.collect::<Result<Vec<String>, _>>()
        .map_err(|e| e.to_string())
}

#[tauri::command]
fn record_attempt(function_id: String, correct: bool) -> Result<(), String> {
    if !function_id.starts_with("snake.") || function_id.len() > 80 {
        return Err("知识点 id 必须以 snake. 开头".into());
    }
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_secs() as i64;
    let conn = open_db()?;
    conn.execute(
        "INSERT INTO attempts (function_id, correct, answered_at) VALUES (?1, ?2, ?3)",
        params![function_id, correct as i64, now],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .invoke_handler(tauri::generate_handler![
            read_source,
            run_chapter,
            record_attempt,
            passed_questions
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
