// Athena English — 独立壳：内容路径、进度与复习。
// 不依赖主程序头文件或 athena.json。

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

struct AppState {
    content_root: PathBuf,
    store_path: PathBuf,
}

#[derive(Clone, Serialize)]
struct AppInfo {
    title: String,
    content_root: String,
    store_path: String,
}

#[derive(Serialize)]
struct ReviewState {
    item_id: String,
    reps: i64,
    ease: f64,
    interval_days: f64,
    due_at: String,
    last_rating: Option<i64>,
}

#[derive(Clone, Serialize)]
struct MasteryState {
    mastery: i64,
    last_correct: i64,
    last_total: i64,
}

#[derive(Serialize)]
struct AttemptStats {
    attempts: i64,
    correct: i64,
    active_days: i64,
    streak: i64,
}

fn is_leap(year: i32) -> bool {
    year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)
}

fn days_in_month(year: i32, month: u32) -> u32 {
    match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            if is_leap(year) {
                29
            } else {
                28
            }
        }
        _ => 31,
    }
}

fn prev_ymd(day: &str) -> Option<String> {
    let mut parts = day.split('-');
    let year: i32 = parts.next()?.parse().ok()?;
    let month: u32 = parts.next()?.parse().ok()?;
    let date: u32 = parts.next()?.parse().ok()?;
    if month == 0 || month > 12 || date == 0 {
        return None;
    }
    let (year, month, date) = if date > 1 {
        (year, month, date - 1)
    } else if month > 1 {
        let month = month - 1;
        (year, month, days_in_month(year, month))
    } else {
        (year - 1, 12, 31)
    };
    Some(format!("{year:04}-{month:02}-{date:02}"))
}

fn consecutive_streak(today: &str, days: &[String]) -> i64 {
    let set: HashSet<&str> = days.iter().map(String::as_str).collect();
    let yesterday = match prev_ymd(today) {
        Some(day) => day,
        None => return 0,
    };
    let mut cursor = if set.contains(today) {
        today.to_string()
    } else if set.contains(yesterday.as_str()) {
        yesterday
    } else {
        return 0;
    };
    let mut count = 0;
    loop {
        if !set.contains(cursor.as_str()) {
            break;
        }
        count += 1;
        match prev_ymd(&cursor) {
            Some(prev) => cursor = prev,
            None => break,
        }
    }
    count
}

#[derive(Clone, Serialize)]
struct MistakeState {
    item_id: String,
    topic_id: String,
    kind: String,
    error_tag: String,
    wrong_count: i64,
    correct_days: i64,
    variant_correct: bool,
    selected_answer: String,
    correct_answer: String,
    explanation: String,
}

fn content_root() -> PathBuf {
    if let Ok(root) = std::env::var("ATHENA_ENGLISH_ROOT") {
        return PathBuf::from(root);
    }

    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            let roots = [
                dir.to_path_buf(),
                dir.join(".."),
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

    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let dev = manifest.join("..");
    dev.canonicalize().unwrap_or(dev)
}

fn own_store_path() -> PathBuf {
    let base = dirs_next::data_dir().unwrap_or_else(|| PathBuf::from("."));
    let dir = base.join("AthenaEnglish");
    let _ = fs::create_dir_all(&dir);
    dir.join("learning.db")
}

fn parse_cli() {
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--store" => {
                let ignored = args.next().unwrap_or_default();
                eprintln!("已忽略 --store {ignored}：本应用使用自己的进度库");
            }
            "--help" | "-h" => {
                eprintln!(
                    "用法：athena-english\n\n\
                     进度写入本应用自己的库，完全独立运行。\n\
                     --store <路径> 仅为兼容旧版主程序而接受，会被忽略。"
                );
                std::process::exit(0);
            }
            "--version" => {
                println!("athena-english {}", env!("CARGO_PKG_VERSION"));
                std::process::exit(0);
            }
            other => {
                eprintln!("无法识别的参数：{other}");
                std::process::exit(2);
            }
        }
    }
}

fn ensure_own_schema(path: &Path) -> Result<(), String> {
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    conn.execute_batch(
        "PRAGMA journal_mode=WAL;
         CREATE TABLE IF NOT EXISTS knowledge_progress (
           function_id TEXT PRIMARY KEY,
           mastery INTEGER NOT NULL DEFAULT 0,
           last_correct INTEGER NOT NULL DEFAULT 0,
           last_total INTEGER NOT NULL DEFAULT 0,
           updated_at TEXT
         );
         CREATE TABLE IF NOT EXISTS review_items (
           item_id TEXT PRIMARY KEY,
           topic_id TEXT NOT NULL,
           kind TEXT NOT NULL,
           reps INTEGER NOT NULL DEFAULT 0,
           ease REAL NOT NULL DEFAULT 2.5,
           interval_days REAL NOT NULL DEFAULT 0,
           due_at TEXT NOT NULL,
           last_rating INTEGER,
           updated_at TEXT
         );
         CREATE TABLE IF NOT EXISTS answer_attempts (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           item_id TEXT NOT NULL,
           topic_id TEXT NOT NULL,
           kind TEXT NOT NULL,
           correct INTEGER NOT NULL,
           is_variant INTEGER NOT NULL DEFAULT 0,
           answered_at TEXT NOT NULL DEFAULT (datetime('now'))
         );
         CREATE TABLE IF NOT EXISTS assessment_attempts (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           assessment_id TEXT NOT NULL,
           topic_id TEXT NOT NULL,
           correct INTEGER NOT NULL,
           total INTEGER NOT NULL,
           passed INTEGER NOT NULL,
           answered_at TEXT NOT NULL DEFAULT (datetime('now'))
         );
         CREATE TABLE IF NOT EXISTS assessment_progress (
           topic_id TEXT PRIMARY KEY,
           mastery INTEGER NOT NULL DEFAULT 0,
           last_correct INTEGER NOT NULL DEFAULT 0,
           last_total INTEGER NOT NULL DEFAULT 0,
           best_score INTEGER NOT NULL DEFAULT 0,
           passed_at TEXT,
           updated_at TEXT NOT NULL DEFAULT (datetime('now'))
         );
         CREATE TABLE IF NOT EXISTS mistake_items (
           item_id TEXT PRIMARY KEY,
           topic_id TEXT NOT NULL,
           kind TEXT NOT NULL,
           error_tag TEXT NOT NULL,
           wrong_count INTEGER NOT NULL DEFAULT 1,
           correct_days INTEGER NOT NULL DEFAULT 0,
           last_correct_day TEXT,
           variant_correct INTEGER NOT NULL DEFAULT 0,
           selected_answer TEXT NOT NULL,
           correct_answer TEXT NOT NULL,
           explanation TEXT NOT NULL,
           active INTEGER NOT NULL DEFAULT 1,
           updated_at TEXT NOT NULL DEFAULT (datetime('now'))
         );",
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

fn resolve_content(root: &Path, relative: &str) -> Result<PathBuf, String> {
    if relative.is_empty() || relative.contains("..") {
        return Err("非法内容路径".into());
    }
    let path = root.join("content").join(relative);
    if !path.starts_with(root.join("content")) {
        return Err("内容路径越界".into());
    }
    Ok(path)
}

fn unix_now() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as i64
}

fn iso_from_unix(ts: i64) -> String {
    // 存 unix 秒的十进制即可，前端用 Number 解析。
    ts.to_string()
}

#[tauri::command]
fn get_app_info(state: tauri::State<'_, Mutex<AppState>>) -> AppInfo {
    let s = state.lock().unwrap();
    AppInfo {
        title: "英语学习".into(),
        content_root: s.content_root.display().to_string(),
        store_path: s.store_path.display().to_string(),
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
fn load_content_text(
    state: tauri::State<'_, Mutex<AppState>>,
    relative: String,
) -> Result<String, String> {
    let s = state.lock().unwrap();
    let path = resolve_content(&s.content_root, &relative)?;
    fs::read_to_string(&path).map_err(|e| format!("无法读取 {}: {e}", path.display()))
}

#[tauri::command]
fn load_content_json(
    state: tauri::State<'_, Mutex<AppState>>,
    relative: String,
) -> Result<serde_json::Value, String> {
    let text = load_content_text(state, relative)?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

#[tauri::command]
fn load_all_review(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<HashMap<String, ReviewState>, String> {
    let s = state.lock().unwrap();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT item_id, reps, ease, interval_days, due_at, last_rating
             FROM review_items",
        )
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok(ReviewState {
                item_id: row.get(0)?,
                reps: row.get(1)?,
                ease: row.get(2)?,
                interval_days: row.get(3)?,
                due_at: row.get(4)?,
                last_rating: row.get(5)?,
            })
        })
        .map_err(|e| e.to_string())?;
    let mut map = HashMap::new();
    for row in rows.flatten() {
        map.insert(row.item_id.clone(), row);
    }
    Ok(map)
}

#[tauri::command]
fn load_attempt_stats(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<AttemptStats, String> {
    let s = state.lock().unwrap();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    let attempts: i64 = conn
        .query_row("SELECT COUNT(*) FROM answer_attempts", [], |row| row.get(0))
        .unwrap_or(0);
    let correct: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM answer_attempts WHERE correct = 1",
            [],
            |row| row.get(0),
        )
        .unwrap_or(0);
    let mut stmt = conn
        .prepare(
            "SELECT DISTINCT date(answered_at, 'localtime') FROM answer_attempts ORDER BY 1 DESC",
        )
        .map_err(|e| e.to_string())?;
    let days: Vec<String> = stmt
        .query_map([], |row| row.get(0))
        .map_err(|e| e.to_string())?
        .flatten()
        .collect();
    let today: String = conn
        .query_row("SELECT date('now', 'localtime')", [], |row| row.get(0))
        .unwrap_or_default();
    Ok(AttemptStats {
        attempts,
        correct,
        active_days: days.len() as i64,
        streak: consecutive_streak(&today, &days),
    })
}

#[derive(Deserialize)]
struct ReviewInput {
    item_id: String,
    topic_id: String,
    kind: String,
    correct: bool,
    deck_total: i64,
    selected_answer: String,
    correct_answer: String,
    explanation: String,
    error_tag: String,
    is_variant: bool,
}

#[derive(Deserialize)]
struct AssessmentInput {
    assessment_id: String,
    topic_id: String,
    correct: i64,
    total: i64,
}

fn schedule(reps: i64, correct: bool) -> (i64, f64) {
    // 间隔效应只支持“逐步拉开复习”这一方向，不存在适用于所有人的神奇天数。
    // 这里使用可审计的保守阶梯；答错十分钟后到期，答对后按成功次数扩展。
    if !correct {
        return (0, 10.0 / 1440.0);
    }
    let next_reps = reps + 1;
    let interval = match next_reps {
        1 => 1.0,
        2 => 3.0,
        3 => 7.0,
        4 => 14.0,
        5 => 30.0,
        _ => 60.0,
    };
    (next_reps, interval)
}

#[tauri::command]
fn save_answer(
    state: tauri::State<'_, Mutex<AppState>>,
    input: ReviewInput,
) -> Result<ReviewState, String> {
    if !input.item_id.starts_with("en.") || !input.topic_id.starts_with("en.") {
        return Err("练习项 id 必须以 en. 开头".into());
    }
    if input.deck_total <= 0 {
        return Err("deck_total 必须大于 0".into());
    }

    let s = state.lock().unwrap();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;

    let existing_reps = conn
        .query_row(
            "SELECT reps FROM review_items WHERE item_id = ?1",
            [&input.item_id],
            |row| row.get::<_, i64>(0),
        )
        .unwrap_or(0);
    let (next_reps, next_interval) = schedule(existing_reps, input.correct);
    let next_ease = 2.5;
    let stored_rating = if input.correct { 4 } else { 1 };
    let due = unix_now() + (next_interval * 86400.0).round() as i64;
    let due_at = iso_from_unix(due);

    conn.execute(
        "INSERT INTO answer_attempts(item_id, topic_id, kind, correct, is_variant)
         VALUES(?1, ?2, ?3, ?4, ?5)",
        rusqlite::params![
            input.item_id,
            input.topic_id,
            input.kind,
            input.correct as i64,
            input.is_variant as i64
        ],
    )
    .map_err(|e| e.to_string())?;

    conn.execute(
        "INSERT INTO review_items(
            item_id, topic_id, kind, reps, ease, interval_days, due_at, last_rating, updated_at
         ) VALUES(?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, datetime('now'))
         ON CONFLICT(item_id) DO UPDATE SET
           topic_id = excluded.topic_id,
           kind = excluded.kind,
           reps = excluded.reps,
           ease = excluded.ease,
           interval_days = excluded.interval_days,
           due_at = excluded.due_at,
           last_rating = excluded.last_rating,
           updated_at = excluded.updated_at",
        rusqlite::params![
            input.item_id,
            input.topic_id,
            input.kind,
            next_reps,
            next_ease,
            next_interval,
            due_at,
            stored_rating
        ],
    )
    .map_err(|e| e.to_string())?;

    update_mistake(&conn, &input)?;

    Ok(ReviewState {
        item_id: input.item_id,
        reps: next_reps,
        ease: next_ease,
        interval_days: next_interval,
        due_at,
        last_rating: Some(stored_rating),
    })
}

fn update_mistake(conn: &rusqlite::Connection, input: &ReviewInput) -> Result<(), String> {
    if !input.correct {
        conn.execute(
            "INSERT INTO mistake_items(
               item_id, topic_id, kind, error_tag, wrong_count, correct_days,
               last_correct_day, variant_correct, selected_answer, correct_answer,
               explanation, active, updated_at
             ) VALUES(?1, ?2, ?3, ?4, 1, 0, NULL, 0, ?5, ?6, ?7, 1, datetime('now'))
             ON CONFLICT(item_id) DO UPDATE SET
               topic_id = excluded.topic_id,
               kind = excluded.kind,
               error_tag = excluded.error_tag,
               wrong_count = mistake_items.wrong_count + 1,
               correct_days = 0,
               last_correct_day = NULL,
               variant_correct = 0,
               selected_answer = excluded.selected_answer,
               correct_answer = excluded.correct_answer,
               explanation = excluded.explanation,
               active = 1,
               updated_at = excluded.updated_at",
            rusqlite::params![
                input.item_id,
                input.topic_id,
                input.kind,
                input.error_tag,
                input.selected_answer,
                input.correct_answer,
                input.explanation
            ],
        )
        .map_err(|e| e.to_string())?;
        return Ok(());
    }

    let existing = conn
        .query_row(
            "SELECT correct_days, last_correct_day, variant_correct
             FROM mistake_items WHERE item_id = ?1 AND active = 1",
            [&input.item_id],
            |row| {
                Ok((
                    row.get::<_, i64>(0)?,
                    row.get::<_, Option<String>>(1)?,
                    row.get::<_, i64>(2)? != 0,
                ))
            },
        )
        .ok();
    let Some((correct_days, last_day, variant_correct)) = existing else {
        return Ok(());
    };
    let today: String = conn
        .query_row("SELECT date('now')", [], |row| row.get(0))
        .map_err(|e| e.to_string())?;
    let next_days = if last_day.as_deref() == Some(today.as_str()) {
        correct_days
    } else {
        correct_days + 1
    };
    let next_variant = variant_correct || input.is_variant;
    let active = !(next_days >= 2 && next_variant);
    conn.execute(
        "UPDATE mistake_items SET
           correct_days = ?2,
           last_correct_day = ?3,
           variant_correct = ?4,
           active = ?5,
           updated_at = datetime('now')
         WHERE item_id = ?1",
        rusqlite::params![
            input.item_id,
            next_days,
            today,
            next_variant as i64,
            active as i64
        ],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

fn persist_assessment_result(
    conn: &mut rusqlite::Connection,
    input: &AssessmentInput,
) -> Result<MasteryState, String> {
    let passed_now = input.correct * 100 >= input.total * 80;
    let transaction = conn.transaction().map_err(|e| e.to_string())?;
    transaction
        .execute(
            "INSERT INTO assessment_attempts(
                assessment_id, topic_id, correct, total, passed
             ) VALUES(?1, ?2, ?3, ?4, ?5)",
            rusqlite::params![
                input.assessment_id,
                input.topic_id,
                input.correct,
                input.total,
                passed_now as i64
            ],
        )
        .map_err(|e| e.to_string())?;
    transaction
        .execute(
            "INSERT INTO assessment_progress(
                topic_id, mastery, last_correct, last_total, best_score, passed_at, updated_at
             ) VALUES(
                ?1, ?2, ?3, ?4, ?5,
                CASE WHEN ?2 = 1 THEN datetime('now') ELSE NULL END,
                datetime('now')
             )
             ON CONFLICT(topic_id) DO UPDATE SET
               mastery = MAX(assessment_progress.mastery, excluded.mastery),
               last_correct = excluded.last_correct,
               last_total = excluded.last_total,
               best_score = MAX(assessment_progress.best_score, excluded.best_score),
               passed_at = CASE
                 WHEN assessment_progress.passed_at IS NOT NULL THEN assessment_progress.passed_at
                 WHEN excluded.mastery = 1 THEN datetime('now')
                 ELSE NULL
               END,
               updated_at = excluded.updated_at",
            rusqlite::params![
                input.topic_id,
                passed_now as i64,
                input.correct,
                input.total,
                input.correct * 100 / input.total
            ],
        )
        .map_err(|e| e.to_string())?;
    transaction.commit().map_err(|e| e.to_string())?;

    conn.query_row(
        "SELECT mastery, last_correct, last_total
         FROM assessment_progress WHERE topic_id = ?1",
        [&input.topic_id],
        |row| {
            Ok(MasteryState {
                mastery: row.get(0)?,
                last_correct: row.get(1)?,
                last_total: row.get(2)?,
            })
        },
    )
    .map_err(|e| e.to_string())
}

#[tauri::command]
fn save_assessment_result(
    state: tauri::State<'_, Mutex<AppState>>,
    input: AssessmentInput,
) -> Result<MasteryState, String> {
    if !input.assessment_id.starts_with("en.assessment.") || !input.topic_id.starts_with("en.") {
        return Err("考核 id 必须使用 en.assessment. 前缀，轨道 id 必须使用 en. 前缀".into());
    }
    if input.total <= 0 || input.correct < 0 || input.correct > input.total {
        return Err("考核分数范围非法".into());
    }
    let s = state.lock().unwrap();
    ensure_own_schema(&s.store_path)?;
    let mut conn = rusqlite::Connection::open(&s.store_path).map_err(|e| e.to_string())?;
    persist_assessment_result(&mut conn, &input)
}

#[tauri::command]
fn load_mistakes(state: tauri::State<'_, Mutex<AppState>>) -> Result<Vec<MistakeState>, String> {
    let s = state.lock().unwrap();
    ensure_own_schema(&s.store_path)?;
    let conn = rusqlite::Connection::open(&s.store_path).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT item_id, topic_id, kind, error_tag, wrong_count, correct_days,
                    variant_correct, selected_answer, correct_answer, explanation
             FROM mistake_items
             WHERE active = 1
             ORDER BY updated_at DESC, item_id",
        )
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok(MistakeState {
                item_id: row.get(0)?,
                topic_id: row.get(1)?,
                kind: row.get(2)?,
                error_tag: row.get(3)?,
                wrong_count: row.get(4)?,
                correct_days: row.get(5)?,
                variant_correct: row.get::<_, i64>(6)? != 0,
                selected_answer: row.get(7)?,
                correct_answer: row.get(8)?,
                explanation: row.get(9)?,
            })
        })
        .map_err(|e| e.to_string())?;
    Ok(rows.flatten().collect())
}

#[tauri::command]
fn load_all_mastery(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<HashMap<String, serde_json::Value>, String> {
    let s = state.lock().unwrap();
    let path = &s.store_path;
    ensure_own_schema(path)?;
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    let mut stmt = conn
        .prepare(
            "SELECT topic_id, mastery, last_correct, last_total
             FROM assessment_progress",
        )
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, i64>(1)?,
                row.get::<_, i64>(2)?,
                row.get::<_, i64>(3)?,
            ))
        })
        .map_err(|e| e.to_string())?;
    let mut map = HashMap::new();
    for (id, mastery, correct, total) in rows.flatten() {
        map.insert(
            id,
            serde_json::json!({
                "mastery": mastery,
                "last_correct": correct,
                "last_total": total
            }),
        );
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
            load_content_text,
            load_content_json,
            load_all_review,
            load_attempt_stats,
            save_answer,
            save_assessment_result,
            load_mistakes,
            load_all_mastery
        ])
        .run(tauri::generate_context!())
        .expect("error while running athena-english");
}

#[cfg(test)]
mod tests {
    use super::{consecutive_streak, persist_assessment_result, schedule, AssessmentInput};

    #[test]
    fn streak_counts_today_and_yesterday() {
        let days = vec!["2026-09-14".into(), "2026-09-13".into(), "2026-09-12".into()];
        assert_eq!(consecutive_streak("2026-09-14", &days), 3);
    }

    #[test]
    fn streak_still_counts_if_today_is_empty_but_yesterday_is_not() {
        let days = vec!["2026-09-13".into(), "2026-09-12".into()];
        assert_eq!(consecutive_streak("2026-09-14", &days), 2);
    }

    #[test]
    fn streak_breaks_on_a_gap() {
        let days = vec!["2026-09-10".into(), "2026-09-08".into()];
        assert_eq!(consecutive_streak("2026-09-14", &days), 0);
        assert_eq!(consecutive_streak("2026-09-10", &days), 1);
    }

    #[test]
    fn correct_answers_expand_the_interval() {
        assert_eq!(schedule(0, true), (1, 1.0));
        assert_eq!(schedule(1, true), (2, 3.0));
        assert_eq!(schedule(4, true), (5, 30.0));
        assert_eq!(schedule(20, true), (21, 60.0));
    }

    #[test]
    fn an_error_resets_successes_and_returns_soon() {
        let (reps, interval) = schedule(4, false);
        assert_eq!(reps, 0);
        assert!((interval - 10.0 / 1440.0).abs() < f64::EPSILON);
    }

    #[test]
    fn assessment_pass_is_not_revoked_by_a_later_failure() {
        let mut conn = rusqlite::Connection::open_in_memory().unwrap();
        ensure_own_schema_for_connection(&conn);
        let passed = persist_assessment_result(
            &mut conn,
            &AssessmentInput {
                assessment_id: "en.assessment.beginner.vocab.v1".into(),
                topic_id: "en.beginner.vocab.core".into(),
                correct: 4,
                total: 5,
            },
        )
        .unwrap();
        assert_eq!(passed.mastery, 1);

        let later = persist_assessment_result(
            &mut conn,
            &AssessmentInput {
                assessment_id: "en.assessment.beginner.vocab.v1".into(),
                topic_id: "en.beginner.vocab.core".into(),
                correct: 2,
                total: 5,
            },
        )
        .unwrap();
        assert_eq!(later.mastery, 1);
        assert_eq!(later.last_correct, 2);
    }

    fn ensure_own_schema_for_connection(conn: &rusqlite::Connection) {
        conn.execute_batch(
            "CREATE TABLE assessment_attempts (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               assessment_id TEXT NOT NULL,
               topic_id TEXT NOT NULL,
               correct INTEGER NOT NULL,
               total INTEGER NOT NULL,
               passed INTEGER NOT NULL,
               answered_at TEXT NOT NULL DEFAULT (datetime('now'))
             );
             CREATE TABLE assessment_progress (
               topic_id TEXT PRIMARY KEY,
               mastery INTEGER NOT NULL DEFAULT 0,
               last_correct INTEGER NOT NULL DEFAULT 0,
               last_total INTEGER NOT NULL DEFAULT 0,
               best_score INTEGER NOT NULL DEFAULT 0,
               passed_at TEXT,
               updated_at TEXT NOT NULL DEFAULT (datetime('now'))
             );",
        )
        .unwrap();
    }
}
