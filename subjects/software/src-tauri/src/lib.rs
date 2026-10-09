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

#[derive(serde::Serialize)]
struct SqlLabOutcome {
    columns: Vec<String>,
    rows: Vec<Vec<String>>,
    passed: bool,
    detail: String,
}

/// SQL 实验：内存库跑 setup → 执行学习者查询 → 执行参考查询，行集（无序）与
/// 列名都一致才判通过。内存库不落盘，写坏什么都没关系；命令只碰 SQL，无文件
/// 与进程访问（softcert ADR 0002）。
#[tauri::command]
fn run_sql_lab(setup: Vec<String>, user_sql: String, answer_sql: String) -> Result<SqlLabOutcome, String> {
    let conn = rusqlite::Connection::open_in_memory().map_err(|e| e.to_string())?;
    for (i, batch) in setup.iter().enumerate() {
        conn.execute_batch(batch).map_err(|e| format!("建表脚本第 {} 段出错：{e}", i + 1))?;
    }
    let (user_cols, mut user_rows) = query_rows(&conn, &user_sql)?;
    let (answer_cols, mut answer_rows) = query_rows(&conn, &answer_sql)?;
    // 行序不作判定点（教学场景允许无 ORDER BY 的行序差异），列名严格：SELECT *
    // 过不了关。
    user_rows.sort();
    answer_rows.sort();
    let passed = user_cols == answer_cols && user_rows == answer_rows;
    let detail = if passed {
        "通过：结果集与参考查询一致。".to_string()
    } else if user_cols != answer_cols {
        format!("列不匹配：期望 {answer_cols:?}，你的查询是 {user_cols:?}。检查 SELECT 的目标列。")
    } else {
        format!(
            "行数 {} 对 {}，内容有出入。再对照题目检查 WHERE 条件。",
            user_rows.len(),
            answer_rows.len()
        )
    };
    Ok(SqlLabOutcome { columns: user_cols, rows: user_rows, passed, detail })
}

fn query_rows(conn: &rusqlite::Connection, sql: &str) -> Result<(Vec<String>, Vec<Vec<String>>), String> {
    let mut stmt = conn.prepare(sql).map_err(|e| format!("SQL 错误：{e}"))?;
    let col_count = stmt.column_count();
    let columns: Vec<String> = stmt.column_names().into_iter().map(String::from).collect();
    let mut rows = stmt.query([]).map_err(|e| format!("SQL 错误：{e}"))?;
    let mut out: Vec<Vec<String>> = Vec::new();
    while let Some(row) = rows.next().map_err(|e| format!("SQL 错误：{e}"))? {
        let mut r = Vec::with_capacity(col_count);
        for i in 0..col_count {
            let v = match row.get_ref(i).map_err(|e| format!("SQL 错误：{e}"))? {
                rusqlite::types::ValueRef::Null => String::new(),
                rusqlite::types::ValueRef::Integer(n) => n.to_string(),
                rusqlite::types::ValueRef::Real(f) => f.to_string(),
                rusqlite::types::ValueRef::Text(t) | rusqlite::types::ValueRef::Blob(t) => {
                    String::from_utf8_lossy(t).into_owned()
                }
            };
            r.push(v);
        }
        out.push(r);
    }
    Ok((columns, out))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            record_attempt,
            attempts_summary,
            today_stats,
            load_setting,
            save_setting,
            run_sql_lab
        ])
        .run(tauri::generate_context!())
        .expect("error while running athena-software-designer");
}
