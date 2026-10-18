//! 课程应用的本地进度库（ADR 0037、0155）：知识点掌握度、实验状态、实验草稿、随堂选项。
//!
//! 全部是接收库路径的普通函数，不碰 Tauri——命令只是 `lib.rs` 里的薄封装。这样这些读写
//! 可以脱离窗口直接单测，六个应用共用同一份实现，改一处就够。
//!
//! 每次读写前都先 `ensure_schema`：库是应用自建、自迁移的，不依赖它之前跑没跑过。
//! 表都是 `lww`（可变记录）；启动器的同步代理按各应用 `app.json` 的 `progress.tables`
//! 声明推拉，表结构变了要同步改那里。

use rusqlite::{params, Connection};
use std::collections::HashMap;
use std::path::Path;

fn open(path: &Path) -> Result<Connection, String> {
    ensure_schema(path)?;
    Connection::open(path).map_err(|e| e.to_string())
}

/// 建表并兼容早期的库。幂等。
pub fn ensure_schema(path: &Path) -> Result<(), String> {
    let conn = Connection::open(path).map_err(|e| e.to_string())?;
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

pub fn load_mastery(path: &Path, topic_id: &str) -> Result<i32, String> {
    let conn = open(path)?;
    let mut stmt = conn
        .prepare("SELECT mastery FROM knowledge_progress WHERE function_id = ?1")
        .map_err(|e| e.to_string())?;
    Ok(stmt.query_row([topic_id], |row| row.get(0)).unwrap_or(0))
}

/// 掌握度夹在 0～5；界面传什么都不会写出越界值。
pub fn save_mastery(path: &Path, topic_id: &str, mastery: i32) -> Result<(), String> {
    let conn = open(path)?;
    conn.execute(
        "INSERT INTO knowledge_progress(function_id, mastery, updated_at)
         VALUES(?1, ?2, datetime('now'))
         ON CONFLICT(function_id) DO UPDATE SET
           mastery = excluded.mastery,
           updated_at = excluded.updated_at",
        params![topic_id, mastery.clamp(0, 5)],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn load_all_mastery(path: &Path) -> Result<HashMap<String, i32>, String> {
    let conn = open(path)?;
    let mut stmt = conn
        .prepare("SELECT function_id, mastery FROM knowledge_progress")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, i32>(1)?))
        })
        .map_err(|e| e.to_string())?;
    Ok(rows.flatten().collect())
}

/// 实验状态只认三种；别的值是前端出了错，不静默写进库。
pub fn save_lab_status(path: &Path, lab_key: &str, status: &str) -> Result<(), String> {
    if !matches!(status, "done" | "tried" | "started") {
        return Err(format!("非法实验状态：{status}"));
    }
    let conn = open(path)?;
    conn.execute(
        "INSERT INTO lab_progress(lab_key, status, updated_at)
         VALUES(?1, ?2, datetime('now'))
         ON CONFLICT(lab_key) DO UPDATE SET
           status = excluded.status,
           updated_at = excluded.updated_at",
        params![lab_key, status],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn load_all_lab_status(path: &Path) -> Result<HashMap<String, String>, String> {
    let conn = open(path)?;
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
    Ok(rows
        .flatten()
        .map(|(key, status)| {
            // 库里的旧值或脏值一律归到 tried，不把未知字符串交给界面。
            let known = match status.as_str() {
                "done" => "done",
                "started" => "started",
                _ => "tried",
            };
            (key, known.to_string())
        })
        .collect())
}

pub fn save_lab_draft(path: &Path, lab_key: &str, source: &str) -> Result<(), String> {
    let conn = open(path)?;
    conn.execute(
        "INSERT INTO lab_draft(lab_key, source, updated_at)
         VALUES(?1, ?2, datetime('now'))
         ON CONFLICT(lab_key) DO UPDATE SET
           source = excluded.source,
           updated_at = excluded.updated_at",
        params![lab_key, source],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn load_all_lab_drafts(path: &Path) -> Result<HashMap<String, String>, String> {
    let conn = open(path)?;
    let mut stmt = conn
        .prepare("SELECT lab_key, source FROM lab_draft")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
        })
        .map_err(|e| e.to_string())?;
    Ok(rows.flatten().collect())
}

pub fn clear_lab_draft(path: &Path, lab_key: &str) -> Result<(), String> {
    let conn = open(path)?;
    conn.execute("DELETE FROM lab_draft WHERE lab_key = ?1", [lab_key])
        .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn save_quiz_picks(path: &Path, quiz_key: &str, picks: &str) -> Result<(), String> {
    let conn = open(path)?;
    conn.execute(
        "INSERT INTO quiz_picks(quiz_key, picks, updated_at)
         VALUES(?1, ?2, datetime('now'))
         ON CONFLICT(quiz_key) DO UPDATE SET
           picks = excluded.picks,
           updated_at = excluded.updated_at",
        params![quiz_key, picks],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn load_all_quiz_picks(path: &Path) -> Result<HashMap<String, String>, String> {
    let conn = open(path)?;
    let mut stmt = conn
        .prepare("SELECT quiz_key, picks FROM quiz_picks")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
        })
        .map_err(|e| e.to_string())?;
    Ok(rows.flatten().collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    /// 每个测试一份独立的临时库，结束时清掉；并发互不踩。
    struct TempDb(PathBuf);

    impl TempDb {
        fn new(name: &str) -> Self {
            let stamp = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            let dir = std::env::temp_dir().join(format!("athena-shell-test-{name}-{stamp}"));
            std::fs::create_dir_all(&dir).unwrap();
            Self(dir.join("learning.db"))
        }
    }

    impl Drop for TempDb {
        fn drop(&mut self) {
            if let Some(dir) = self.0.parent() {
                let _ = std::fs::remove_dir_all(dir);
            }
        }
    }

    #[test]
    fn 掌握度读写_夹在零到五_覆盖旧值() {
        let db = TempDb::new("mastery");
        assert_eq!(load_mastery(&db.0, "ds.list").unwrap(), 0, "没记录按 0");
        save_mastery(&db.0, "ds.list", 3).unwrap();
        assert_eq!(load_mastery(&db.0, "ds.list").unwrap(), 3);
        save_mastery(&db.0, "ds.list", 99).unwrap();
        assert_eq!(load_mastery(&db.0, "ds.list").unwrap(), 5, "越界夹到上限");
        save_mastery(&db.0, "ds.list", -4).unwrap();
        assert_eq!(load_mastery(&db.0, "ds.list").unwrap(), 0, "越界夹到下限");
        assert_eq!(
            load_all_mastery(&db.0).unwrap().len(),
            1,
            "同一个知识点只有一行"
        );
    }

    #[test]
    fn 实验状态只认三种_脏值读出时归为tried() {
        let db = TempDb::new("lab");
        save_lab_status(&db.0, "lab.a", "done").unwrap();
        save_lab_status(&db.0, "lab.b", "started").unwrap();
        assert!(save_lab_status(&db.0, "lab.c", "passed").is_err());
        // 旧版本可能写进过别的值：读出时不把未知字符串交给界面。
        Connection::open(&db.0)
            .unwrap()
            .execute(
                "INSERT INTO lab_progress(lab_key, status) VALUES('lab.old', 'weird')",
                [],
            )
            .unwrap();
        let all = load_all_lab_status(&db.0).unwrap();
        assert_eq!(all["lab.a"], "done");
        assert_eq!(all["lab.b"], "started");
        assert_eq!(all["lab.old"], "tried");
        assert!(!all.contains_key("lab.c"), "非法状态不能落库");
    }

    #[test]
    fn 草稿与随堂选项_覆盖写_草稿可清除() {
        let db = TempDb::new("draft");
        save_lab_draft(&db.0, "lab.a", "int main(){}").unwrap();
        save_lab_draft(&db.0, "lab.a", "int main(){return 1;}").unwrap();
        assert_eq!(
            load_all_lab_drafts(&db.0).unwrap()["lab.a"],
            "int main(){return 1;}"
        );
        clear_lab_draft(&db.0, "lab.a").unwrap();
        assert!(load_all_lab_drafts(&db.0).unwrap().is_empty());
        save_quiz_picks(&db.0, "q.1", "[0,2]").unwrap();
        assert_eq!(load_all_quiz_picks(&db.0).unwrap()["q.1"], "[0,2]");
    }

    #[test]
    fn 早期只有passed列的库升级后补status并回填() {
        let db = TempDb::new("migrate");
        Connection::open(&db.0)
            .unwrap()
            .execute_batch(
                "CREATE TABLE lab_progress (lab_key TEXT PRIMARY KEY, passed INTEGER, updated_at TEXT);
                 INSERT INTO lab_progress(lab_key, passed) VALUES('lab.pass', 1), ('lab.try', 0);",
            )
            .unwrap();
        ensure_schema(&db.0).unwrap();
        let all = load_all_lab_status(&db.0).unwrap();
        assert_eq!(all["lab.pass"], "done");
        assert_eq!(all["lab.try"], "tried");
        ensure_schema(&db.0).unwrap(); // 幂等
    }
}
