mod compiler;
mod legacy;

use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::process::Command;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use rusqlite::{params, Connection};
use serde::Serialize;

const MAX_MASTERY: i64 = 5;
const MAX_SOURCE_BYTES: usize = 256 * 1024;

#[derive(Serialize)]
struct ProgressRow {
    function_id: String,
    mastery: i64,
    last_correct: i64,
    last_total: i64,
}

#[derive(Serialize)]
struct RunOutput {
    ok: bool,
    compiler: String,
    output: String,
}

/// 正确数 * 5 / 题数，与原来的 mastery_from_score 同一条整数除法。
fn mastery_from_score(correct: i64, total: i64) -> i64 {
    if total <= 0 {
        return 0;
    }
    let bounded = correct.clamp(0, total);
    bounded * MAX_MASTERY / total
}

fn app_root() -> Option<PathBuf> {
    if let Ok(root) = std::env::var("ATHENA_CPP_ROOT") {
        let path = PathBuf::from(root);
        if path.join("app.json").is_file() {
            return Some(path);
        }
    }
    let mut cursor = std::env::current_dir().ok()?;
    for _ in 0..6 {
        if cursor.join("app.json").is_file() && cursor.join("content").is_dir() {
            return Some(cursor);
        }
        if !cursor.pop() {
            break;
        }
    }
    None
}

fn database_path() -> Result<PathBuf, String> {
    // 进度库放用户数据目录，不进仓库（ADR 0155）：启动器的同步代理在能连上路由器时
    // 把它与中心库互推。目录名登记在 app.json 的 progress.dir，两处必须一致。
    let dir = dirs_next::data_dir()
        .ok_or("找不到用户数据目录")?
        .join("athena-cpp");
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    Ok(dir.join("learning.db"))
}

fn open_db() -> Result<Connection, String> {
    let path = database_path()?;
    let conn = Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS knowledge_progress (
            function_id TEXT PRIMARY KEY,
            mastery INTEGER NOT NULL DEFAULT 0,
            updated_at INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS assessment_attempt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_id TEXT NOT NULL,
            mastery INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            total INTEGER NOT NULL,
            answered_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS assessment_attempt_time
            ON assessment_attempt(answered_at);",
    )
    .map_err(|e| e.to_string())?;
    ensure_column(&conn, "last_correct")?;
    ensure_column(&conn, "last_total")?;
    Ok(conn)
}

fn ensure_column(conn: &Connection, name: &str) -> Result<(), String> {
    let mut stmt = conn
        .prepare("PRAGMA table_info(knowledge_progress)")
        .map_err(|e| e.to_string())?;
    let exists = stmt
        .query_map([], |row| row.get::<_, String>(1))
        .map_err(|e| e.to_string())?
        .filter_map(|r| r.ok())
        .any(|col| col == name);
    if !exists {
        conn.execute(
            &format!(
                "ALTER TABLE knowledge_progress ADD COLUMN {name} INTEGER NOT NULL DEFAULT 0"
            ),
            [],
        )
        .map_err(|e| e.to_string())?;
    }
    Ok(())
}

fn unix_now() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0)
}

#[tauri::command]
fn load_progress() -> Result<Vec<ProgressRow>, String> {
    let conn = open_db()?;
    let mut stmt = conn
        .prepare(
            "SELECT function_id, mastery, last_correct, last_total
             FROM knowledge_progress",
        )
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok(ProgressRow {
                function_id: row.get(0)?,
                mastery: row.get(1)?,
                last_correct: row.get(2)?,
                last_total: row.get(3)?,
            })
        })
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;
    Ok(rows)
}

#[tauri::command]
fn record_attempt(function_id: String, correct: i64, total: i64) -> Result<ProgressRow, String> {
    if !function_id.starts_with("cpp.") || function_id.len() > 160 {
        return Err("知识点 id 不合法".into());
    }
    if total <= 0 || total > 50 || correct < 0 || correct > total {
        return Err("作答数量不合法".into());
    }
    let mastery = mastery_from_score(correct, total);
    let now = unix_now();
    let conn = open_db()?;
    conn.execute(
        "INSERT INTO knowledge_progress
            (function_id, mastery, last_correct, last_total, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5)
         ON CONFLICT(function_id) DO UPDATE SET
            mastery = excluded.mastery,
            last_correct = excluded.last_correct,
            last_total = excluded.last_total,
            updated_at = excluded.updated_at",
        params![function_id, mastery, correct, total, now],
    )
    .map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO assessment_attempt
            (function_id, mastery, correct, total, answered_at)
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![function_id, mastery, correct, total, now],
    )
    .map_err(|e| e.to_string())?;
    Ok(ProgressRow {
        function_id,
        mastery,
        last_correct: correct,
        last_total: total,
    })
}

#[tauri::command]
fn read_case(case_id: String) -> Result<String, String> {
    let path = case_file(&case_id)?;
    fs::read_to_string(path).map_err(|e| e.to_string())
}

fn case_file(case_id: &str) -> Result<PathBuf, String> {
    if case_id.is_empty()
        || !case_id
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
    {
        return Err("案例名不合法".into());
    }
    let root = app_root().ok_or("不在应用目录里，读不到案例")?;
    let path = root
        .join("resources")
        .join("cases")
        .join(case_id)
        .join("main.cpp");
    if !path.is_file() {
        return Err(format!("找不到案例 {case_id}"));
    }
    Ok(path)
}

#[tauri::command]
fn compile_and_run(source: String) -> Result<RunOutput, String> {
    if source.len() > MAX_SOURCE_BYTES {
        return Err("源码过长".into());
    }
    let compiler = compiler::detect().ok_or_else(compiler::install_hint)?;
    let dir = std::env::temp_dir().join(format!("athena-cpp-lab-{}", std::process::id()));
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    let src = dir.join("main.cpp");
    let mut file = fs::File::create(&src).map_err(|e| e.to_string())?;
    file.write_all(source.as_bytes()).map_err(|e| e.to_string())?;
    let out = dir.join(compiler.artifact_name());

    let compile = run_bounded(compiler.compile_command(&src, &out), Duration::from_secs(30))?;
    if !compile.status.success() {
        return Ok(RunOutput {
            ok: false,
            compiler: compiler.label(),
            output: decode_output(&compile),
        });
    }

    let run = run_bounded(Command::new(&out), Duration::from_secs(8))?;
    let mut text = decode_output(&run);
    if !run.status.success() {
        text.push_str(&format!("\n进程退出码 {:?}\n", run.status.code()));
    }
    Ok(RunOutput {
        ok: run.status.success(),
        compiler: compiler.label(),
        output: text,
    })
}

fn decode_output(output: &std::process::Output) -> String {
    let mut text = String::new();
    text.push_str(&String::from_utf8_lossy(&output.stdout));
    text.push_str(&String::from_utf8_lossy(&output.stderr));
    text
}

#[tauri::command]
fn open_legacy_window() -> Result<String, String> {
    let root = app_root().ok_or("不在应用目录里，打不开旧版窗口")?;
    legacy::open(&root)
}

fn run_bounded(mut cmd: Command, limit: Duration) -> Result<std::process::Output, String> {
    let mut child = cmd
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;
    let started = Instant::now();
    loop {
        if let Some(_status) = child.try_wait().map_err(|e| e.to_string())? {
            return child.wait_with_output().map_err(|e| e.to_string());
        }
        if started.elapsed() > limit {
            let _ = child.kill();
            let _ = child.wait();
            return Err("超时".into());
        }
        std::thread::sleep(Duration::from_millis(40));
    }
}

/// 历史归档（ADR 0176）：读出案例目录里的全部文本文件。
#[tauri::command]
fn load_case_files(case_id: String) -> Result<Vec<athena_course_shell::archive::CaseFile>, String> {
    let root = app_root().ok_or("找不到应用根目录")?;
    athena_course_shell::archive::load_files(&root, &case_id)
}

/// 历史归档：编译并运行案例里指定的源文件（多文件、10 秒超时、只读）。
#[tauri::command]
fn run_archive_case(
    case_id: String,
    sources: Vec<String>,
    std: Option<String>,
    stdin: Option<String>,
) -> Result<athena_course_shell::archive::ArchiveRun, String> {
    let root = app_root().ok_or("找不到应用根目录")?;
    athena_course_shell::archive::run(&root, "athena-c-plus-plus", &case_id, &sources, std.as_deref(), stdin.as_deref())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
    .plugin(tauri_plugin_updater::Builder::new().build())
    .plugin(tauri_plugin_process::init())
        .invoke_handler(tauri::generate_handler![
            load_progress,
            record_attempt,
            read_case,
            compile_and_run,
            load_case_files,
            run_archive_case,
            open_legacy_window
        ])
        .run(tauri::generate_context!())
        .expect("启动 C++ 教程失败");
}

#[cfg(test)]
mod tests {
    use super::mastery_from_score;

    #[test]
    fn mastery_matches_the_old_integer_scale() {
        assert_eq!(mastery_from_score(2, 2), 5);
        assert_eq!(mastery_from_score(1, 2), 2);
        assert_eq!(mastery_from_score(0, 2), 0);
        assert_eq!(mastery_from_score(0, 0), 0);
    }
}
