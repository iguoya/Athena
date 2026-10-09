//! 进度库:作答记录是唯一的事实来源(ADR 0052)。
//!
//! 掌握率、连对、今日战绩都是查询时由 attempts 派生的量,库里不存
//! 「掌握度」字段——存了就有绕过作答直接改掌握度的后门。

use rusqlite::{params, Connection, OptionalExtension};
use serde::Serialize;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

pub struct Store {
    conn: Mutex<Connection>,
}

#[derive(Serialize)]
pub struct AttemptRecorded {
    pub id: i64,
    pub answered_at: i64,
}

#[derive(Serialize)]
pub struct KpSummary {
    pub kp_id: String,
    pub total: i64,
    pub correct: i64,
    pub last_at: i64,
    /// 最近一次作答往前连续答对的次数;从没答过是 0。
    pub streak: i64,
}

#[derive(Serialize)]
pub struct TodayStats {
    pub date: String,
    pub answered: i64,
    pub correct: i64,
}

fn store_path() -> PathBuf {
    // 开发工作树:exe 从 cargo 的 target/ 下跑,进度随仓库走(ADR 0053),
    // 换机器 clone 下来战绩还在。发行包:内容已打进前端 bundle,exe 旁没有
    // 仓库标记,写系统数据目录。
    let in_dev_tree = std::env::current_exe()
        .ok()
        .map(|exe| exe.components().any(|c| c.as_os_str() == "target"))
        .unwrap_or(false);
    let dir = if in_dev_tree {
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..").join("progress")
    } else {
        dirs_next::data_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join("AthenaSoftwareDesigner")
    };
    let _ = std::fs::create_dir_all(&dir);
    dir.join("learning.db")
}

fn init_schema(conn: &Connection) -> rusqlite::Result<()> {
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT NOT NULL,
            chapter_id TEXT NOT NULL,
            kp_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            correct INTEGER NOT NULL,
            mode TEXT NOT NULL DEFAULT 'chapter',
            answered_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_attempts_kp ON attempts(kp_id, id DESC);
        CREATE INDEX IF NOT EXISTS idx_attempts_time ON attempts(answered_at);
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );",
    )
}

impl Store {
    pub fn open() -> Result<Self, rusqlite::Error> {
        Self::open_at(&store_path())
    }

    pub fn open_at(path: &Path) -> Result<Self, rusqlite::Error> {
        let conn = Connection::open(path)?;
        init_schema(&conn)?;
        Ok(Self { conn: Mutex::new(conn) })
    }

    #[cfg(test)]
    fn open_memory() -> Result<Self, rusqlite::Error> {
        let conn = Connection::open_in_memory()?;
        init_schema(&conn)?;
        Ok(Self { conn: Mutex::new(conn) })
    }

    pub fn record_attempt(
        &self,
        course: &str,
        chapter_id: &str,
        kp_id: &str,
        question_id: &str,
        correct: bool,
        mode: &str,
    ) -> Result<AttemptRecorded, rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        let answered_at = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_millis() as i64)
            .unwrap_or_default();
        conn.execute(
            "INSERT INTO attempts (course, chapter_id, kp_id, question_id, correct, mode, answered_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![course, chapter_id, kp_id, question_id, correct as i64, mode, answered_at],
        )?;
        Ok(AttemptRecorded { id: conn.last_insert_rowid(), answered_at })
    }

    /// 按知识点聚合。streak 在 Rust 侧数:该知识点最近作答往前连续答对的
    /// 次数,一条答错即停。SQL 窗口函数能写,但边界(错在哪停)可读性远
    /// 不如一个十行循环。
    pub fn attempts_summary(&self) -> Result<Vec<KpSummary>, rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT kp_id, COUNT(*), SUM(correct), MAX(answered_at)
             FROM attempts GROUP BY kp_id ORDER BY MAX(answered_at) DESC",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, i64>(1)?,
                row.get::<_, i64>(2)?,
                row.get::<_, i64>(3)?,
            ))
        })?;
        let mut out = Vec::new();
        for row in rows {
            let (kp_id, total, correct, last_at) = row?;
            let streak = {
                let mut stmt = conn.prepare(
                    "SELECT correct FROM attempts WHERE kp_id = ?1 ORDER BY id DESC LIMIT 100",
                )?;
                let mut streak = 0i64;
                let mut rows = stmt.query([kp_id.as_str()])?;
                while let Some(row) = rows.next()? {
                    if row.get::<_, i64>(0)? == 1 {
                        streak += 1;
                    } else {
                        break;
                    }
                }
                streak
            };
            out.push(KpSummary { kp_id, total, correct, last_at, streak });
        }
        Ok(out)
    }

    pub fn today_stats(&self) -> Result<TodayStats, rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        // 本地时区的「今天」:作答都发生在本机,按本机日界算每日目标才符合直觉。
        let date: String = conn.query_row(
            "SELECT strftime('%Y-%m-%d', 'now', 'localtime')",
            [],
            |row| row.get(0),
        )?;
        let mut stmt = conn.prepare(
            "SELECT COUNT(*), COALESCE(SUM(correct), 0) FROM attempts
             WHERE strftime('%Y-%m-%d', answered_at / 1000.0, 'unixepoch', 'localtime') = ?1",
        )?;
        let (answered, correct) = stmt.query_row([&date], |row| {
            Ok((row.get::<_, i64>(0)?, row.get::<_, i64>(1)?))
        })?;
        Ok(TodayStats { date, answered, correct })
    }

    pub fn get_setting(&self, key: &str) -> Result<Option<String>, rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        conn.query_row(
            "SELECT value FROM app_settings WHERE key = ?1",
            [key],
            |row| row.get(0),
        )
        .optional()
    }

    pub fn set_setting(&self, key: &str, value: &str) -> Result<(), rusqlite::Error> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO app_settings (key, value) VALUES (?1, ?2)
             ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            params![key, value],
        )?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn store() -> Store {
        Store::open_memory().expect("in-memory store")
    }

    #[test]
    fn schema_is_idempotent() {
        let path = std::env::temp_dir().join(format!("softdesign-test-{}.db", std::process::id()));
        let _ = std::fs::remove_file(&path);
        {
            let s = Store::open_at(&path).expect("open");
            s.record_attempt("cs", "c1", "kp1", "q1", true, "chapter").unwrap();
        }
        // 旧库上再开一次:建表语句全部 IF NOT EXISTS,升级路径不走迁移框架。
        let s = Store::open_at(&path).expect("reopen");
        assert_eq!(s.attempts_summary().unwrap().len(), 1);
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn summary_counts_and_streak_stop_at_first_wrong() {
        let s = store();
        let rec = |correct: bool| {
            s.record_attempt("cs", "c1", "kp1", "q", correct, "chapter").unwrap();
        };
        rec(true);
        rec(true);
        rec(false);
        rec(true);
        let summary = s.attempts_summary().unwrap();
        assert_eq!(summary.len(), 1);
        let kp = &summary[0];
        assert_eq!((kp.total, kp.correct, kp.streak), (4, 3, 1));
    }

    #[test]
    fn settings_roundtrip() {
        let s = store();
        assert_eq!(s.get_setting("goal").unwrap(), None);
        s.set_setting("goal", "esd-2027").unwrap();
        s.set_setting("goal", "esd-2026").unwrap();
        assert_eq!(s.get_setting("goal").unwrap().as_deref(), Some("esd-2026"));
    }
}
