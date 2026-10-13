//! 学习进度同步代理（ADR 0155）：把各应用本地 SQLite 进度库与路由器上的 nas_admin 互推。
//!
//! 应用只管写自己的本地库，不知道同步的存在；这里读它们的库、按 `app.json` 里
//! `progress` 声明的规则合并。路由器不可达是常态而不是错误：同步失败只记日志，
//! 不打扰使用者，下次再来（同步状态不进任何界面，要排查用命令行）。
//!
//! 怎么识别「本地改过」而不要求应用改表结构：旁路库 `AthenaSync/state.db` 里记每一行
//! 上次见到的指纹与更新时间。扫描时指纹变了、行新出现、行不见了，就是本地改动，
//! 记成待推送。拉取别处的改动时直接写应用的库，并同步更新旁路库，免得又被当成本地改动推回去。
//!
//! 更新时间取库文件的修改时间而不是「扫描时的现在」：新机器第一次同步时，本地那份
//! 较旧的库不能以「刚改过」的名义盖掉中心里更新的进度。

use std::collections::{BTreeMap, HashMap, HashSet};
use std::io::Write as _;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use rusqlite::types::{Value as SqlValue, ValueRef};
use rusqlite::{params, params_from_iter, Connection, OpenFlags};
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};

use crate::manifest::{App, ProgressSpec, TableMode, TableSpec};
use crate::runner::{ProcessSnapshot, RunState};

const BATCH: usize = 500;
const DEFAULT_ENDPOINT: &str = "http://192.168.6.1:5000/api/progress/v1";

// ---------------------------------------------------------------- 配置与路径

/// `AthenaSync/config.json`：首次使用时自动写出默认值，之后可手改。
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// 按序尝试：先内网，再外网（Cloudflare 域名），哪个先通用哪个。
    pub endpoints: Vec<String>,
    /// 学习者编号（全局目录分配，ADR 0074）。
    pub user: u32,
    /// 设备名：合并时同一时刻的胜负靠它定，要在各台机器上互不相同。
    pub device: String,
}

pub fn sync_dir() -> Option<PathBuf> {
    dirs_next::data_dir().map(|dir| dir.join("AthenaSync"))
}

fn local_db_path(spec: &ProgressSpec) -> Option<PathBuf> {
    dirs_next::data_dir().map(|dir| dir.join(&spec.dir).join("learning.db"))
}

fn default_device() -> String {
    std::env::var("COMPUTERNAME")
        .or_else(|_| std::env::var("HOSTNAME"))
        .or_else(|_| std::env::var("HOST"))
        .unwrap_or_else(|_| "unknown-device".to_string())
}

pub fn load_config() -> Result<Config, String> {
    let dir = sync_dir().ok_or("找不到用户数据目录")?;
    let path = dir.join("config.json");
    if let Ok(text) = std::fs::read_to_string(&path) {
        return serde_json::from_str(&text).map_err(|e| format!("{} 读不动：{e}", path.display()));
    }
    let config = Config { endpoints: vec![DEFAULT_ENDPOINT.to_string()], user: 1, device: default_device() };
    std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    let text = serde_json::to_string_pretty(&config).map_err(|e| e.to_string())?;
    std::fs::write(&path, text).map_err(|e| e.to_string())?;
    Ok(config)
}

/// 同步日志：只追加，超过 1 MB 就换一份新的。写不进去也不报错——日志不能拖垮同步。
fn log(message: &str) {
    let Some(dir) = sync_dir() else { return };
    let _ = std::fs::create_dir_all(&dir);
    let path = dir.join("sync.log");
    if std::fs::metadata(&path).map(|m| m.len() > 1_000_000).unwrap_or(false) {
        let _ = std::fs::rename(&path, dir.join("sync.log.1"));
    }
    if let Ok(mut file) = std::fs::OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(file, "{} {message}", utc_stamp(SystemTime::now()));
    }
}

// ---------------------------------------------------------------- 时间

/// `2026-10-13T01:02:03.123Z`（UTC、毫秒）。格式固定，字符串比较就等于时间比较。
pub fn utc_stamp(time: SystemTime) -> String {
    let since = time.duration_since(UNIX_EPOCH).unwrap_or_default();
    let secs = since.as_secs() as i64;
    let (days, rem) = (secs.div_euclid(86_400), secs.rem_euclid(86_400));
    // 日数 → 公历日期（Howard Hinnant 的 civil_from_days）。
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let year = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let day = doy - (153 * mp + 2) / 5 + 1;
    let month = if mp < 10 { mp + 3 } else { mp - 9 };
    let year = if month <= 2 { year + 1 } else { year };
    format!(
        "{year:04}-{month:02}-{day:02}T{:02}:{:02}:{:02}.{:03}Z",
        rem / 3600,
        rem % 3600 / 60,
        rem % 60,
        since.subsec_millis()
    )
}

/// 库文件及其 WAL 里最晚的修改时间：这批改动不可能晚于它。
fn db_mtime(db: &Path) -> SystemTime {
    let wal = PathBuf::from(format!("{}-wal", db.display()));
    [db.to_path_buf(), wal]
        .iter()
        .filter_map(|p| std::fs::metadata(p).ok()?.modified().ok())
        .max()
        .unwrap_or_else(SystemTime::now)
}

// ---------------------------------------------------------------- 与服务端的约定

#[derive(Debug, Clone, Serialize)]
pub struct PushRow {
    pub tbl: String,
    pub pk: String,
    pub mode: String,
    pub stamp: String,
    #[serde(skip_serializing_if = "std::ops::Not::not")]
    pub deleted: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<Value>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PullRow {
    pub tbl: String,
    pub pk: String,
    #[serde(default)]
    pub data: Option<Value>,
    pub stamp: String,
    #[serde(default)]
    pub deleted: bool,
    pub device: String,
    #[allow(dead_code)]
    pub seq: i64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Page {
    pub rows: Vec<PullRow>,
    pub next: i64,
    pub more: bool,
}

/// 远端：生产里是 HTTP，测试里是内存里的假服务端。
pub trait Remote {
    fn push(&mut self, app: &str, device: &str, rows: &[PushRow]) -> Result<(), String>;
    fn pull(&mut self, app: &str, since: i64, limit: usize) -> Result<Page, String>;
}

pub struct HttpRemote {
    endpoints: Vec<String>,
    user: u32,
    agent: ureq::Agent,
    /// 上次成功的端点下标，下次先试它。
    active: usize,
}

impl HttpRemote {
    pub fn new(config: &Config) -> Self {
        let agent = ureq::AgentBuilder::new()
            .timeout_connect(Duration::from_secs(2))
            .timeout(Duration::from_secs(20))
            .build();
        Self { endpoints: config.endpoints.clone(), user: config.user, agent, active: 0 }
    }

    /// 按序试各端点：连不上就换下一个；连上了但服务端报错就如实返回，不换端点重试。
    fn call(&mut self, make: impl Fn(&ureq::Agent, &str, &str) -> Result<ureq::Response, ureq::Error>) -> Result<ureq::Response, String> {
        let user = self.user.to_string();
        let count = self.endpoints.len();
        let mut last = "没有配置任何端点".to_string();
        for offset in 0..count {
            let index = (self.active + offset) % count;
            match make(&self.agent, &self.endpoints[index], &user) {
                Ok(response) => {
                    self.active = index;
                    return Ok(response);
                }
                Err(ureq::Error::Status(code, response)) => {
                    let body = response.into_string().unwrap_or_default();
                    return Err(format!("服务端返回 {code}：{body}"));
                }
                Err(error) => last = format!("{}：{error}", self.endpoints[index]),
            }
        }
        Err(format!("路由器不可达（{last}）"))
    }
}

impl Remote for HttpRemote {
    fn push(&mut self, app: &str, device: &str, rows: &[PushRow]) -> Result<(), String> {
        let body = json!({ "app": app, "device": device, "rows": rows });
        self.call(|agent, base, user| {
            agent.post(&format!("{base}/push")).set("X-Athena-User", user).send_json(body.clone())
        })
        .map(|_| ())
    }

    fn pull(&mut self, app: &str, since: i64, limit: usize) -> Result<Page, String> {
        let response = self.call(|agent, base, user| {
            agent
                .get(&format!("{base}/pull"))
                .set("X-Athena-User", user)
                .query("app", app)
                .query("since", &since.to_string())
                .query("limit", &limit.to_string())
                .call()
        })?;
        response.into_json::<Page>().map_err(|e| format!("服务端响应读不懂：{e}"))
    }
}

// ---------------------------------------------------------------- 旁路状态库

#[derive(Debug, Clone)]
struct RowState {
    hash: i64,
    stamp: String,
    deleted: bool,
    synced: bool,
    data: Option<String>,
}

pub struct State {
    conn: Connection,
}

impl State {
    pub fn open(path: &Path) -> Result<Self, String> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
        let conn = Connection::open(path).map_err(|e| e.to_string())?;
        Self::init(conn)
    }

    #[cfg(test)]
    fn memory() -> Self {
        Self::init(Connection::open_in_memory().unwrap()).unwrap()
    }

    fn init(conn: Connection) -> Result<Self, String> {
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS row_state(
                app TEXT NOT NULL, tbl TEXT NOT NULL, pk TEXT NOT NULL,
                hash INTEGER NOT NULL, stamp TEXT NOT NULL,
                deleted INTEGER NOT NULL, synced INTEGER NOT NULL, data TEXT,
                PRIMARY KEY(app, tbl, pk));
             CREATE TABLE IF NOT EXISTS cursor(app TEXT PRIMARY KEY, since INTEGER NOT NULL);",
        )
        .map_err(|e| e.to_string())?;
        Ok(Self { conn })
    }

    fn get(&self, app: &str, tbl: &str, pk: &str) -> Result<Option<RowState>, String> {
        let mut stmt = self
            .conn
            .prepare_cached("SELECT hash, stamp, deleted, synced, data FROM row_state WHERE app=?1 AND tbl=?2 AND pk=?3")
            .map_err(|e| e.to_string())?;
        let mut rows = stmt.query(params![app, tbl, pk]).map_err(|e| e.to_string())?;
        match rows.next().map_err(|e| e.to_string())? {
            None => Ok(None),
            Some(r) => Ok(Some(RowState {
                hash: r.get(0).map_err(|e| e.to_string())?,
                stamp: r.get(1).map_err(|e| e.to_string())?,
                deleted: r.get::<_, i64>(2).map_err(|e| e.to_string())? != 0,
                synced: r.get::<_, i64>(3).map_err(|e| e.to_string())? != 0,
                data: r.get(4).map_err(|e| e.to_string())?,
            })),
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn put(&self, app: &str, tbl: &str, pk: &str, hash: i64, stamp: &str, deleted: bool, synced: bool, data: Option<&str>) -> Result<(), String> {
        self.conn
            .execute(
                "INSERT OR REPLACE INTO row_state(app, tbl, pk, hash, stamp, deleted, synced, data)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
                params![app, tbl, pk, hash, stamp, deleted as i64, synced as i64, data],
            )
            .map(|_| ())
            .map_err(|e| e.to_string())
    }

    fn live_keys(&self, app: &str, tbl: &str) -> Result<Vec<String>, String> {
        let mut stmt = self
            .conn
            .prepare("SELECT pk FROM row_state WHERE app=?1 AND tbl=?2 AND deleted=0")
            .map_err(|e| e.to_string())?;
        let keys = stmt
            .query_map(params![app, tbl], |r| r.get::<_, String>(0))
            .map_err(|e| e.to_string())?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| e.to_string())?;
        Ok(keys)
    }

    fn unsynced(&self, app: &str) -> Result<Vec<(String, String, RowState)>, String> {
        let mut stmt = self
            .conn
            .prepare("SELECT tbl, pk, hash, stamp, deleted, data FROM row_state WHERE app=?1 AND synced=0 ORDER BY stamp, tbl, pk")
            .map_err(|e| e.to_string())?;
        let rows = stmt
            .query_map(params![app], |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, String>(1)?,
                    RowState {
                        hash: r.get(2)?,
                        stamp: r.get(3)?,
                        deleted: r.get::<_, i64>(4)? != 0,
                        synced: false,
                        data: r.get(5)?,
                    },
                ))
            })
            .map_err(|e| e.to_string())?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| e.to_string())?;
        Ok(rows)
    }

    fn mark_synced(&self, app: &str, tbl: &str, pk: &str, hash: i64) -> Result<(), String> {
        // 只在指纹没变时标记：推送过程中本地又改了，这行仍应保持待推送。
        self.conn
            .execute(
                "UPDATE row_state SET synced=1 WHERE app=?1 AND tbl=?2 AND pk=?3 AND hash=?4",
                params![app, tbl, pk, hash],
            )
            .map(|_| ())
            .map_err(|e| e.to_string())
    }

    fn cursor(&self, app: &str) -> i64 {
        self.conn
            .query_row("SELECT since FROM cursor WHERE app=?1", params![app], |r| r.get(0))
            .unwrap_or(0)
    }

    fn set_cursor(&self, app: &str, since: i64) -> Result<(), String> {
        self.conn
            .execute("INSERT OR REPLACE INTO cursor(app, since) VALUES (?1, ?2)", params![app, since])
            .map(|_| ())
            .map_err(|e| e.to_string())
    }

    fn pending(&self, app: &str) -> i64 {
        self.conn
            .query_row("SELECT COUNT(*) FROM row_state WHERE app=?1 AND synced=0", params![app], |r| r.get(0))
            .unwrap_or(0)
    }
}

// ---------------------------------------------------------------- 读本地表

struct TableInfo {
    cols: Vec<String>,
    key: Vec<String>,
}

fn quote(identifier: &str) -> String {
    format!("\"{}\"", identifier.replace('"', "\"\""))
}

fn valid_identifier(name: &str) -> bool {
    !name.is_empty() && name.chars().all(|c| c.is_ascii_alphanumeric() || c == '_')
}

/// 表不存在返回 `Ok(None)`（应用还没跑过、没建表），不是错误。
fn table_info(db: &Connection, tbl: &str, spec: &TableSpec) -> Result<Option<TableInfo>, String> {
    if !valid_identifier(tbl) {
        return Err(format!("表名「{tbl}」不合法"));
    }
    let mut stmt = db.prepare(&format!("PRAGMA table_info({})", quote(tbl))).map_err(|e| e.to_string())?;
    let columns: Vec<(String, i64)> = stmt
        .query_map([], |r| Ok((r.get::<_, String>(1)?, r.get::<_, i64>(5)?)))
        .map_err(|e| e.to_string())?
        .collect::<Result<_, _>>()
        .map_err(|e| e.to_string())?;
    if columns.is_empty() {
        return Ok(None);
    }
    let all_cols: Vec<String> = columns.iter().map(|(name, _)| name.clone()).collect();
    let mut primary: Vec<(String, i64)> = columns.iter().filter(|(_, pk)| *pk > 0).cloned().collect();
    primary.sort_by_key(|(_, pk)| *pk);
    let primary: Vec<String> = primary.into_iter().map(|(name, _)| name).collect();
    let key = if spec.key.is_empty() {
        primary.clone()
    } else {
        if let Some(missing) = spec.key.iter().find(|k| !all_cols.contains(k)) {
            return Err(format!("表 {tbl} 没有声明的键列 {missing}"));
        }
        spec.key.clone()
    };
    if key.is_empty() {
        return Err(format!("表 {tbl} 没有主键，app.json 的 progress.tables.{tbl}.key 必须写"));
    }
    // 业务键之外的主键列（典型是自增 id）只在本机有意义：各台机器的 id 会撞号，
    // 一旦随行传过去再写进来，`INSERT OR REPLACE` 会盖掉本机另一条记录。所以它既不读、
    // 不传，也不写，新行的 id 由本机自己的自增分配。
    let cols = all_cols.into_iter().filter(|c| key.contains(c) || !primary.contains(c)).collect();
    Ok(Some(TableInfo { cols, key }))
}

fn blob_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn hex_blob(text: &str) -> Vec<u8> {
    (0..text.len() / 2).filter_map(|i| u8::from_str_radix(&text[i * 2..i * 2 + 2], 16).ok()).collect()
}

fn to_json(value: ValueRef) -> Value {
    match value {
        ValueRef::Null => Value::Null,
        ValueRef::Integer(i) => json!(i),
        ValueRef::Real(f) => serde_json::Number::from_f64(f).map(Value::Number).unwrap_or(Value::Null),
        ValueRef::Text(t) => Value::String(String::from_utf8_lossy(t).into_owned()),
        ValueRef::Blob(b) => json!({ "$blob": blob_hex(b) }),
    }
}

fn to_sql(value: &Value) -> SqlValue {
    match value {
        Value::Null => SqlValue::Null,
        Value::Bool(b) => SqlValue::Integer(*b as i64),
        Value::Number(n) => match n.as_i64() {
            Some(i) => SqlValue::Integer(i),
            None => SqlValue::Real(n.as_f64().unwrap_or(0.0)),
        },
        Value::String(s) => SqlValue::Text(s.clone()),
        Value::Object(o) if o.len() == 1 && o.contains_key("$blob") => {
            SqlValue::Blob(hex_blob(o["$blob"].as_str().unwrap_or("")))
        }
        other => SqlValue::Text(other.to_string()),
    }
}

/// FNV-1a 64 位：跨版本、跨平台稳定（旁路库里存的指纹要在多次运行间可比）。
fn fingerprint(text: &str) -> i64 {
    let mut hash: u64 = 0xcbf2_9ce4_8422_2325;
    for byte in text.bytes() {
        hash ^= u64::from(byte);
        hash = hash.wrapping_mul(0x0000_0100_0000_01b3);
    }
    hash as i64
}

struct LocalRow {
    pk: String,
    hash: i64,
    data: Value,
}

fn row_object(info: &TableInfo, row: &rusqlite::Row) -> rusqlite::Result<Map<String, Value>> {
    let mut object = Map::new();
    for (index, col) in info.cols.iter().enumerate() {
        object.insert(col.clone(), to_json(row.get_ref(index)?));
    }
    Ok(object)
}

fn pk_of(info: &TableInfo, object: &Map<String, Value>) -> String {
    let key: Vec<&Value> = info.key.iter().map(|k| object.get(k).unwrap_or(&Value::Null)).collect();
    serde_json::to_string(&key).unwrap_or_default()
}

fn read_rows(db: &Connection, tbl: &str, info: &TableInfo) -> Result<Vec<LocalRow>, String> {
    let columns = info.cols.iter().map(|c| quote(c)).collect::<Vec<_>>().join(", ");
    let mut stmt = db.prepare(&format!("SELECT {columns} FROM {}", quote(tbl))).map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |r| row_object(info, r))
        .map_err(|e| e.to_string())?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())?;
    Ok(rows
        .into_iter()
        .map(|object| {
            let pk = pk_of(info, &object);
            let data = Value::Object(object);
            LocalRow { pk, hash: fingerprint(&data.to_string()), data }
        })
        .collect())
}

fn read_one(db: &Connection, tbl: &str, info: &TableInfo, pk: &[Value]) -> Result<Option<LocalRow>, String> {
    let columns = info.cols.iter().map(|c| quote(c)).collect::<Vec<_>>().join(", ");
    let filter = info.key.iter().map(|k| format!("{} IS ?", quote(k))).collect::<Vec<_>>().join(" AND ");
    let mut stmt = db
        .prepare(&format!("SELECT {columns} FROM {} WHERE {filter}", quote(tbl)))
        .map_err(|e| e.to_string())?;
    let mut found = stmt
        .query_map(params_from_iter(pk.iter().map(to_sql)), |r| row_object(info, r))
        .map_err(|e| e.to_string())?;
    match found.next() {
        None => Ok(None),
        Some(object) => {
            let object = object.map_err(|e| e.to_string())?;
            let pk = pk_of(info, &object);
            let data = Value::Object(object);
            Ok(Some(LocalRow { pk, hash: fingerprint(&data.to_string()), data }))
        }
    }
}

// ---------------------------------------------------------------- 同步

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct Outcome {
    pub changed: usize,
    pub pushed: usize,
    pub pulled: usize,
    pub note: Option<String>,
}

/// 扫描本地库，把改动记成待推送。返回新发现的改动数。
fn scan(state: &State, app: &str, spec: &ProgressSpec, db: &Connection, stamp: &str) -> Result<usize, String> {
    let mut changed = 0;
    for (tbl, table) in &spec.tables {
        let Some(info) = table_info(db, tbl, table)? else { continue };
        let mut seen = HashSet::new();
        for row in read_rows(db, tbl, &info)? {
            let known = state.get(app, tbl, &row.pk)?;
            if known.as_ref().map_or(true, |k| k.hash != row.hash || k.deleted) {
                state.put(app, tbl, &row.pk, row.hash, stamp, false, false, Some(&row.data.to_string()))?;
                changed += 1;
            }
            seen.insert(row.pk);
        }
        // 事件表里的行不会被删除同步（事件只增不减）；可变表里消失的行记成删除。
        if table.mode == TableMode::Lww {
            for pk in state.live_keys(app, tbl)? {
                if !seen.contains(&pk) {
                    state.put(app, tbl, &pk, 0, stamp, true, false, None)?;
                    changed += 1;
                }
            }
        }
    }
    Ok(changed)
}

fn push_pending(state: &State, remote: &mut dyn Remote, device: &str, app: &str, spec: &ProgressSpec) -> Result<usize, String> {
    let pending: Vec<(String, String, RowState)> = state
        .unsynced(app)?
        .into_iter()
        .filter(|(tbl, _, _)| spec.tables.contains_key(tbl))
        .collect();
    let mut pushed = 0;
    for chunk in pending.chunks(BATCH) {
        let rows: Vec<PushRow> = chunk
            .iter()
            .map(|(tbl, pk, row)| PushRow {
                tbl: tbl.clone(),
                pk: pk.clone(),
                mode: match spec.tables[tbl].mode {
                    TableMode::Append => "append",
                    TableMode::Lww => "lww",
                }
                .to_string(),
                stamp: row.stamp.clone(),
                deleted: row.deleted,
                data: row.data.as_deref().and_then(|d| serde_json::from_str(d).ok()),
            })
            .collect();
        remote.push(app, device, &rows)?;
        for (tbl, pk, row) in chunk {
            state.mark_synced(app, tbl, pk, row.hash)?;
        }
        pushed += chunk.len();
    }
    Ok(pushed)
}

fn pull_and_apply(
    state: &State,
    remote: &mut dyn Remote,
    device: &str,
    app: &str,
    spec: &ProgressSpec,
    db: &Connection,
) -> Result<usize, String> {
    // 声明的表只要有一张本地还没建（应用没跑过），就整个先不拉：拉下来也写不进去，
    // 游标又不能前进，否则这些行永远丢了。应用第一次跑过之后下一轮自然补上。
    let mut infos: BTreeMap<&str, TableInfo> = BTreeMap::new();
    for (tbl, table) in &spec.tables {
        match table_info(db, tbl, table)? {
            Some(info) => {
                infos.insert(tbl.as_str(), info);
            }
            None => return Ok(0),
        }
    }
    let mut since = state.cursor(app);
    let mut applied = 0;
    loop {
        let page = remote.pull(app, since, BATCH)?;
        let tx = db.unchecked_transaction().map_err(|e| e.to_string())?;
        for row in &page.rows {
            if row.device == device {
                continue;
            }
            let Some(table) = spec.tables.get(&row.tbl) else { continue };
            if apply(state, app, db, &row.tbl, table, &infos[row.tbl.as_str()], row)? {
                applied += 1;
            }
        }
        tx.commit().map_err(|e| e.to_string())?;
        since = page.next;
        state.set_cursor(app, since)?;
        if !page.more {
            break;
        }
    }
    Ok(applied)
}

/// 把一行来自别处的记录落进本地库与旁路库。返回是否真的改了本地。
fn apply(state: &State, app: &str, db: &Connection, tbl: &str, table: &TableSpec, info: &TableInfo, row: &PullRow) -> Result<bool, String> {
    let pk: Vec<Value> = serde_json::from_str(&row.pk).map_err(|e| format!("主键串读不懂：{e}"))?;
    if pk.len() != info.key.len() {
        return Ok(false);
    }
    let known = state.get(app, tbl, &row.pk)?;
    match table.mode {
        TableMode::Append => {
            if known.is_some() || read_one(db, tbl, info, &pk)?.is_some() {
                // 已有就不动；本地原有的行第一次见到时也要登记，免得下一轮把它当本地新增推出去。
                if known.is_none() {
                    if let Some(local) = read_one(db, tbl, info, &pk)? {
                        state.put(app, tbl, &row.pk, local.hash, &row.stamp, false, true, Some(&local.data.to_string()))?;
                    }
                }
                return Ok(false);
            }
        }
        TableMode::Lww => {
            // 本地更新（时间更晚）的不被覆盖。推送先于拉取，走到这里本地的待推送行已经交给服务端裁决过。
            if known.as_ref().is_some_and(|k| k.stamp.as_str() > row.stamp.as_str()) {
                return Ok(false);
            }
        }
    }
    if row.deleted {
        let filter = info.key.iter().map(|k| format!("{} IS ?", quote(k))).collect::<Vec<_>>().join(" AND ");
        db.execute(&format!("DELETE FROM {} WHERE {filter}", quote(tbl)), params_from_iter(pk.iter().map(to_sql)))
            .map_err(|e| e.to_string())?;
        state.put(app, tbl, &row.pk, 0, &row.stamp, true, true, None)?;
        return Ok(true);
    }
    let Some(Value::Object(data)) = &row.data else { return Ok(false) };
    // 只写本地认识的列：对端版本更新、多出来的列直接忽略；键列以主键串为准。
    let mut values: Vec<(&String, SqlValue)> = Vec::new();
    for col in &info.cols {
        if let Some(position) = info.key.iter().position(|k| k == col) {
            values.push((col, to_sql(&pk[position])));
        } else if let Some(value) = data.get(col) {
            values.push((col, to_sql(value)));
        }
    }
    let columns = values.iter().map(|(c, _)| quote(c)).collect::<Vec<_>>().join(", ");
    let marks = vec!["?"; values.len()].join(", ");
    db.execute(
        &format!("INSERT OR REPLACE INTO {} ({columns}) VALUES ({marks})", quote(tbl)),
        params_from_iter(values.iter().map(|(_, v)| v)),
    )
    .map_err(|e| e.to_string())?;
    // 以写完之后本地真实的样子记指纹，而不是对端传来的 JSON：类型亲和、默认值都会让两者有出入。
    if let Some(local) = read_one(db, tbl, info, &pk)? {
        state.put(app, tbl, &row.pk, local.hash, &row.stamp, false, true, Some(&local.data.to_string()))?;
    }
    Ok(true)
}

/// 同步一个应用：扫描 → 推送 →（允许时）拉取。
pub fn sync_with(state: &State, remote: &mut dyn Remote, device: &str, app: &str, spec: &ProgressSpec, db_path: &Path, allow_pull: bool) -> Result<Outcome, String> {
    if !db_path.is_file() {
        return Ok(Outcome { note: Some("还没有本地库".into()), ..Outcome::default() });
    }
    let stamp = utc_stamp(db_mtime(db_path));
    let mut outcome = Outcome::default();
    {
        let reader = Connection::open_with_flags(db_path, OpenFlags::SQLITE_OPEN_READ_ONLY).map_err(|e| format!("打不开 {}：{e}", db_path.display()))?;
        outcome.changed = scan(state, app, spec, &reader, &stamp)?;
    }
    outcome.pushed = push_pending(state, remote, device, app, spec)?;
    if allow_pull {
        let writer = Connection::open(db_path).map_err(|e| e.to_string())?;
        writer.busy_timeout(Duration::from_secs(5)).map_err(|e| e.to_string())?;
        outcome.pulled = pull_and_apply(state, remote, device, app, spec, &writer)?;
    }
    Ok(outcome)
}

// ---------------------------------------------------------------- 对外入口

/// 旧位置（仓库里的 `<app>/progress/learning.db`，ADR 0053）→ 新位置（用户数据目录）。
/// 只在新位置还没有库时复制一次；旧文件原样留着，是否撤出 git 是后一步的事。
/// 必须赶在应用第一次用新路径之前：应用见不到库会自己建一个空的，之后就不会再搬了。
fn migrate_legacy(app: &App, spec: &ProgressSpec) {
    let Some(target) = local_db_path(spec) else { return };
    let legacy = app.dir.join("progress").join("learning.db");
    match copy_once(&legacy, &target) {
        Ok(true) => log(&format!("{} 旧进度库已搬到 {}", app.id, target.display())),
        Ok(false) => {}
        Err(error) => log(&format!("{} 旧进度库搬迁失败：{error}", app.id)),
    }
}

/// 目标不存在、来源存在时复制一次；返回是否复制了。
fn copy_once(legacy: &Path, target: &Path) -> std::io::Result<bool> {
    if target.exists() || !legacy.is_file() {
        return Ok(false);
    }
    if let Some(parent) = target.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::copy(legacy, target)?;
    Ok(true)
}

/// 同步一组声明了 `progress` 的应用。`may_pull` 回答「这个应用此刻能不能写它的库」：
/// 应用在跑就只推不拉，拉取要写它的库。
fn sync_apps(targets: &[&App], may_pull: &dyn Fn(&App) -> bool) -> Vec<(String, Result<Outcome, String>)> {
    if targets.is_empty() {
        return Vec::new();
    }
    // 先搬旧库，再碰网络：路由器不可达也不能耽误这一步。
    for app in targets {
        migrate_legacy(app, app.progress.as_ref().expect("调用方已过滤"));
    }
    let session = (|| -> Result<(Config, State), String> {
        let config = load_config()?;
        let dir = sync_dir().ok_or("找不到用户数据目录")?;
        Ok((config, State::open(&dir.join("state.db"))?))
    })();
    let (config, state) = match session {
        Ok(pair) => pair,
        Err(message) => return targets.iter().map(|app| (app.id.clone(), Err(message.clone()))).collect(),
    };
    let mut remote = HttpRemote::new(&config);
    targets
        .iter()
        .map(|app| {
            let spec = app.progress.as_ref().expect("调用方已过滤");
            let result = match local_db_path(spec) {
                None => Err("找不到用户数据目录".to_string()),
                Some(db) => sync_with(&state, &mut remote, &config.device, &app.id, spec, &db, may_pull(app)),
            };
            match &result {
                Ok(o) if o.changed + o.pushed + o.pulled > 0 => {
                    log(&format!("{} 同步完成：本地新改动 {}，推送 {}，拉取 {}", app.id, o.changed, o.pushed, o.pulled))
                }
                Ok(_) => {}
                Err(message) => log(&format!("{} 同步失败：{message}", app.id)),
            }
            (app.id.clone(), result)
        })
        .collect()
}

/// 同步全部（或指定的）声明了 `progress` 的应用，命令行用。
pub fn sync_all(apps: &[App], snapshot: &ProcessSnapshot, only: Option<&str>) -> Vec<(String, Result<Outcome, String>)> {
    let targets: Vec<&App> = apps
        .iter()
        .filter(|app| app.progress.is_some() && only.map_or(true, |id| id == app.id))
        .collect();
    sync_apps(&targets, &|app| snapshot.state(app) == RunState::Stopped)
}

/// 启动应用之前调用：此刻它没在跑，可以放心推拉。尽力而为，任何失败只记日志，绝不拦着启动。
pub fn before_launch(app: &App) {
    if app.progress.is_none() {
        return;
    }
    let snapshot = ProcessSnapshot::take();
    sync_apps(&[app], &|app| snapshot.state(app) == RunState::Stopped);
}

static LAST_TICK: Mutex<Option<HashMap<String, Instant>>> = Mutex::new(None);
const TICK_INTERVAL: Duration = Duration::from_secs(120);

/// 启动器常驻时周期性调用（前端轮询状态时顺带）：对没在跑、且距上次同步够久的应用，
/// 在后台线程里做一轮同步，调用本身立即返回。路由器不可达时同样受间隔限制，
/// 不会每次轮询都去撞超时。`states` 与 `apps` 一一对应。
pub fn tick(apps: &[App], states: &[RunState]) {
    let due: Vec<App> = {
        let mut guard = LAST_TICK.lock().unwrap_or_else(|e| e.into_inner());
        let map = guard.get_or_insert_with(HashMap::new);
        let mut due = Vec::new();
        for (app, state) in apps.iter().zip(states) {
            if app.progress.is_none() || *state != RunState::Stopped {
                continue;
            }
            if map.get(&app.id).map_or(true, |at| at.elapsed() >= TICK_INTERVAL) {
                map.insert(app.id.clone(), Instant::now());
                due.push(app.clone());
            }
        }
        due
    };
    if due.is_empty() {
        return;
    }
    std::thread::spawn(move || {
        let refs: Vec<&App> = due.iter().collect();
        // 排队期间应用可能被打开了：此刻再确认一次，别写正在运行的应用的库。
        let snapshot = ProcessSnapshot::take();
        sync_apps(&refs, &|app| snapshot.state(app) == RunState::Stopped);
    });
}

/// 每个声明了 `progress` 的应用一行：本地行数、待推送数、游标。给命令行排查用。
pub fn status(apps: &[App]) -> Vec<String> {
    let mut lines = Vec::new();
    let state = sync_dir().and_then(|dir| State::open(&dir.join("state.db")).ok());
    for app in apps.iter().filter(|a| a.progress.is_some()) {
        let spec = app.progress.as_ref().expect("已过滤");
        let db = local_db_path(spec);
        let present = db.as_ref().is_some_and(|p| p.is_file());
        let (pending, cursor) = state.as_ref().map_or((0, 0), |s| (s.pending(&app.id), s.cursor(&app.id)));
        lines.push(format!(
            "{:<18} 本地库 {:<4} 待推送 {:<4} 游标 {}",
            app.id,
            if present { "有" } else { "无" },
            pending,
            cursor
        ));
    }
    lines
}

/// 备份：把本地库与中心库各导出成一份文本快照（JSON），存到 `dir` 下带时间戳的子目录，不进 git。
pub fn backup(apps: &[App], dir: &Path) -> Result<PathBuf, String> {
    let target = dir.join(utc_stamp(SystemTime::now()).replace(':', "-"));
    std::fs::create_dir_all(&target).map_err(|e| e.to_string())?;
    let config = load_config()?;
    let mut remote = HttpRemote::new(&config);
    let mut remote_error: Option<String> = None;
    for app in apps.iter().filter(|a| a.progress.is_some()) {
        let spec = app.progress.as_ref().expect("已过滤");
        if let Some(db_path) = local_db_path(spec).filter(|p| p.is_file()) {
            let db = Connection::open_with_flags(&db_path, OpenFlags::SQLITE_OPEN_READ_ONLY).map_err(|e| e.to_string())?;
            let mut tables = Map::new();
            for (tbl, table) in &spec.tables {
                if let Some(info) = table_info(&db, tbl, table)? {
                    let rows: Vec<Value> = read_rows(&db, tbl, &info)?.into_iter().map(|r| r.data).collect();
                    tables.insert(tbl.clone(), Value::Array(rows));
                }
            }
            write_json(&target.join(format!("{}.local.json", app.id)), &Value::Object(tables))?;
        }
        if remote_error.is_none() {
            let mut all = Vec::new();
            let mut since = 0;
            loop {
                match remote.pull(&app.id, since, BATCH) {
                    Ok(page) => {
                        for r in &page.rows {
                            all.push(json!({"tbl": r.tbl, "pk": r.pk, "data": r.data, "stamp": r.stamp, "deleted": r.deleted, "device": r.device}));
                        }
                        since = page.next;
                        if !page.more {
                            break;
                        }
                    }
                    Err(message) => {
                        remote_error = Some(message);
                        break;
                    }
                }
            }
            if remote_error.is_none() {
                write_json(&target.join(format!("{}.central.json", app.id)), &Value::Array(all))?;
            }
        }
    }
    match remote_error {
        None => Ok(target),
        Some(message) => Err(format!("本地库已备份到 {}，但中心库没拉到：{message}", target.display())),
    }
}

fn write_json(path: &Path, value: &Value) -> Result<(), String> {
    let text = serde_json::to_string_pretty(value).map_err(|e| e.to_string())?;
    std::fs::write(path, text).map_err(|e| format!("写 {} 失败：{e}", path.display()))
}

// ---------------------------------------------------------------- 测试

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;
    use std::rc::Rc;
    use std::cell::RefCell;

    /// 内存里的假服务端：规则与 nas_admin/progress_api/store.py 一致。
    #[derive(Default)]
    struct FakeServer {
        rows: BTreeMap<(String, String, String), (PullRow, String)>, // key -> (行, mode)
        seq: i64,
        down: bool,
    }

    #[derive(Clone)]
    struct FakeRemote(Rc<RefCell<FakeServer>>);

    impl Remote for FakeRemote {
        fn push(&mut self, app: &str, device: &str, rows: &[PushRow]) -> Result<(), String> {
            let mut s = self.0.borrow_mut();
            if s.down {
                return Err("路由器不可达".into());
            }
            for r in rows {
                let key = (app.to_string(), r.tbl.clone(), r.pk.clone());
                let take = match s.rows.get(&key) {
                    None => true,
                    Some((cur, _)) => r.mode != "append" && (r.stamp.as_str(), device) > (cur.stamp.as_str(), cur.device.as_str()),
                };
                if take {
                    s.seq += 1;
                    let seq = s.seq;
                    s.rows.insert(
                        key,
                        (
                            PullRow { tbl: r.tbl.clone(), pk: r.pk.clone(), data: r.data.clone(), stamp: r.stamp.clone(), deleted: r.deleted, device: device.to_string(), seq },
                            r.mode.clone(),
                        ),
                    );
                }
            }
            Ok(())
        }

        fn pull(&mut self, app: &str, since: i64, limit: usize) -> Result<Page, String> {
            let s = self.0.borrow();
            if s.down {
                return Err("路由器不可达".into());
            }
            let mut found: Vec<PullRow> = s.rows.iter().filter(|(k, (r, _))| k.0 == app && r.seq > since).map(|(_, (r, _))| r.clone()).collect();
            found.sort_by_key(|r| r.seq);
            let more = found.len() > limit;
            found.truncate(limit);
            let next = found.last().map_or(since, |r| r.seq);
            Ok(Page { rows: found, next, more })
        }
    }

    fn spec() -> ProgressSpec {
        let mut tables = BTreeMap::new();
        tables.insert("mastery".to_string(), TableSpec { mode: TableMode::Lww, key: vec![] });
        tables.insert("attempts".to_string(), TableSpec { mode: TableMode::Append, key: vec!["qid".into(), "at".into()] });
        ProgressSpec { dir: "athena-test".into(), tables }
    }

    struct Device {
        dir: tempfile::TempDir,
        state: State,
        name: &'static str,
    }

    impl Device {
        fn new(name: &'static str) -> Self {
            let dir = tempfile::tempdir().unwrap();
            let db = Connection::open(dir.path().join("learning.db")).unwrap();
            db.execute_batch(
                "CREATE TABLE mastery(topic TEXT PRIMARY KEY, level INTEGER, note TEXT);
                 CREATE TABLE attempts(id INTEGER PRIMARY KEY AUTOINCREMENT, qid TEXT, at TEXT, ok INTEGER);",
            )
            .unwrap();
            Self { dir, state: State::memory(), name }
        }
        fn db(&self) -> Connection {
            Connection::open(self.dir.path().join("learning.db")).unwrap()
        }
        fn path(&self) -> PathBuf {
            self.dir.path().join("learning.db")
        }
        fn sync(&self, remote: &FakeRemote, pull: bool) -> Result<Outcome, String> {
            let mut r = remote.clone();
            sync_with(&self.state, &mut r, self.name, "demo", &spec(), &self.path(), pull)
        }
        fn level(&self, topic: &str) -> Option<i64> {
            self.db().query_row("SELECT level FROM mastery WHERE topic=?1", [topic], |r| r.get(0)).ok()
        }
        fn attempts(&self) -> i64 {
            self.db().query_row("SELECT COUNT(*) FROM attempts", [], |r| r.get(0)).unwrap()
        }
    }

    fn remote() -> FakeRemote {
        FakeRemote(Rc::new(RefCell::new(FakeServer::default())))
    }

    /// 对着真实的 nas_admin 进度接口走一遍（HTTP 序列化、服务端合并规则都是真的）。
    /// 手动跑：先在本机起接口并设 ATHENA_E2E_ENDPOINT，再 `cargo test -- --ignored e2e`。
    #[test]
    #[ignore = "需要本机起 nas_admin 的进度接口"]
    fn e2e_对真实服务端() {
        let Ok(endpoint) = std::env::var("ATHENA_E2E_ENDPOINT") else { return };
        let config = Config { endpoints: vec![endpoint], user: 77, device: "pc-a".into() };
        let (a, b) = (Device::new("pc-a"), Device::new("pc-b"));
        let mut ra = HttpRemote::new(&config);
        let mut rb = HttpRemote::new(&config);
        a.db().execute("INSERT INTO mastery VALUES('c.1', 3, '中文备注')", []).unwrap();
        a.db().execute("INSERT INTO attempts(qid, at, ok) VALUES('q1', 't1', 1)", []).unwrap();
        let out = sync_with(&a.state, &mut ra, "pc-a", "e2e", &spec(), &a.path(), true).unwrap();
        assert_eq!(out.pushed, 2);
        let out = sync_with(&b.state, &mut rb, "pc-b", "e2e", &spec(), &b.path(), true).unwrap();
        assert_eq!(out.pulled, 2);
        assert_eq!(b.level("c.1"), Some(3));
        let note: String = b.db().query_row("SELECT note FROM mastery WHERE topic='c.1'", [], |r| r.get(0)).unwrap();
        assert_eq!(note, "中文备注");
        // b 改、a 拉回
        std::thread::sleep(Duration::from_millis(30));
        b.db().execute("UPDATE mastery SET level=8 WHERE topic='c.1'", []).unwrap();
        sync_with(&b.state, &mut rb, "pc-b", "e2e", &spec(), &b.path(), true).unwrap();
        sync_with(&a.state, &mut ra, "pc-a", "e2e", &spec(), &a.path(), true).unwrap();
        assert_eq!(a.level("c.1"), Some(8));
        // 服务端校验失败要如实报错
        let mut bad = HttpRemote::new(&Config { user: 0, ..config.clone() });
        assert!(bad.pull("e2e", 0, 10).is_err());
    }

    #[test]
    fn 旧库只在新位置没有时搬一次() {
        let dir = tempfile::tempdir().unwrap();
        let legacy = dir.path().join("repo").join("learning.db");
        let target = dir.path().join("data").join("athena-x").join("learning.db");
        std::fs::create_dir_all(legacy.parent().unwrap()).unwrap();
        std::fs::write(&legacy, b"old").unwrap();
        assert!(copy_once(&legacy, &target).unwrap());
        assert_eq!(std::fs::read(&target).unwrap(), b"old");
        // 新位置已有（应用之后写过）就不能再被旧文件覆盖。
        std::fs::write(&target, b"new").unwrap();
        assert!(!copy_once(&legacy, &target).unwrap());
        assert_eq!(std::fs::read(&target).unwrap(), b"new");
        // 没有旧库也不报错。
        assert!(!copy_once(&dir.path().join("none.db"), &dir.path().join("t2.db")).unwrap());
    }

    #[test]
    fn 时间戳格式() {
        assert_eq!(utc_stamp(UNIX_EPOCH), "1970-01-01T00:00:00.000Z");
        assert_eq!(utc_stamp(UNIX_EPOCH + Duration::from_millis(1_760_317_323_123)), "2025-10-13T01:02:03.123Z");
        assert_eq!(utc_stamp(UNIX_EPOCH + Duration::from_secs(951_782_400)), "2000-02-29T00:00:00.000Z");
    }

    #[test]
    fn 本地改动推上去另一台拉下来() {
        let server = remote();
        let a = Device::new("pc-a");
        let b = Device::new("pc-b");
        a.db().execute("INSERT INTO mastery VALUES('c.1', 3, 'hi')", []).unwrap();
        a.db().execute("INSERT INTO attempts(qid, at, ok) VALUES('q1', 't1', 1)", []).unwrap();
        let out = a.sync(&server, true).unwrap();
        assert_eq!((out.changed, out.pushed), (2, 2));

        let out = b.sync(&server, true).unwrap();
        assert_eq!(out.pulled, 2);
        assert_eq!(b.level("c.1"), Some(3));
        assert_eq!(b.attempts(), 1);
    }

    #[test]
    fn 拉下来的行不会被当成本地改动再推回去() {
        let server = remote();
        let a = Device::new("pc-a");
        let b = Device::new("pc-b");
        a.db().execute("INSERT INTO mastery VALUES('c.1', 3, NULL)", []).unwrap();
        a.sync(&server, true).unwrap();
        b.sync(&server, true).unwrap();
        let again = b.sync(&server, true).unwrap();
        assert_eq!((again.changed, again.pushed, again.pulled), (0, 0, 0));
    }

    #[test]
    fn 可变记录新者胜() {
        let server = remote();
        let a = Device::new("pc-a");
        let b = Device::new("pc-b");
        a.db().execute("INSERT INTO mastery VALUES('c.1', 1, NULL)", []).unwrap();
        a.sync(&server, true).unwrap();
        b.sync(&server, true).unwrap();
        // b 随后改成 5。库文件的修改时间天然晚于 a 的那次，所以 b 的更晚。
        std::thread::sleep(Duration::from_millis(20));
        b.db().execute("UPDATE mastery SET level=5 WHERE topic='c.1'", []).unwrap();
        b.sync(&server, true).unwrap();
        a.sync(&server, true).unwrap();
        assert_eq!(a.level("c.1"), Some(5));
    }

    #[test]
    fn 事件取并集且不重复() {
        let server = remote();
        let a = Device::new("pc-a");
        let b = Device::new("pc-b");
        a.db().execute("INSERT INTO attempts(qid, at, ok) VALUES('q1', 't1', 1)", []).unwrap();
        b.db().execute("INSERT INTO attempts(qid, at, ok) VALUES('q1', 't1', 1)", []).unwrap(); // 同一条事件两边都有
        b.db().execute("INSERT INTO attempts(qid, at, ok) VALUES('q2', 't2', 0)", []).unwrap();
        a.sync(&server, true).unwrap();
        b.sync(&server, true).unwrap();
        a.sync(&server, true).unwrap();
        assert_eq!(a.attempts(), 2);
        assert_eq!(b.attempts(), 2);
    }

    #[test]
    fn 自增id撞号时不会覆盖本地另一条记录() {
        let server = remote();
        let a = Device::new("pc-a");
        let b = Device::new("pc-b");
        // 两边各自的第 1 条记录自增 id 都是 1，但内容不同。
        a.db().execute("INSERT INTO attempts(qid, at, ok) VALUES('qa', 't1', 1)", []).unwrap();
        b.db().execute("INSERT INTO attempts(qid, at, ok) VALUES('qb', 't2', 0)", []).unwrap();
        a.sync(&server, true).unwrap();
        b.sync(&server, true).unwrap();
        a.sync(&server, true).unwrap();
        for device in [&a, &b] {
            let qids: Vec<String> = device
                .db()
                .prepare("SELECT qid FROM attempts ORDER BY qid")
                .unwrap()
                .query_map([], |r| r.get(0))
                .unwrap()
                .collect::<Result<_, _>>()
                .unwrap();
            assert_eq!(qids, vec!["qa", "qb"], "{}", device.name);
        }
    }

    #[test]
    fn 删除会同步() {
        let server = remote();
        let a = Device::new("pc-a");
        let b = Device::new("pc-b");
        a.db().execute("INSERT INTO mastery VALUES('c.1', 1, NULL)", []).unwrap();
        a.sync(&server, true).unwrap();
        b.sync(&server, true).unwrap();
        assert_eq!(b.level("c.1"), Some(1));
        std::thread::sleep(Duration::from_millis(20));
        a.db().execute("DELETE FROM mastery WHERE topic='c.1'", []).unwrap();
        a.sync(&server, true).unwrap();
        b.sync(&server, true).unwrap();
        assert_eq!(b.level("c.1"), None);
    }

    #[test]
    fn 路由器不可达时本地照常_状态保持待推送() {
        let server = remote();
        server.0.borrow_mut().down = true;
        let a = Device::new("pc-a");
        a.db().execute("INSERT INTO mastery VALUES('c.1', 2, NULL)", []).unwrap();
        assert!(a.sync(&server, true).is_err());
        assert_eq!(a.state.pending("demo"), 1);
        // 恢复之后补发。
        server.0.borrow_mut().down = false;
        let out = a.sync(&server, true).unwrap();
        assert_eq!(out.pushed, 1);
        assert_eq!(a.state.pending("demo"), 0);
    }

    #[test]
    fn 不拉取时不写应用的库() {
        let server = remote();
        let a = Device::new("pc-a");
        let b = Device::new("pc-b");
        a.db().execute("INSERT INTO mastery VALUES('c.1', 3, NULL)", []).unwrap();
        a.sync(&server, true).unwrap();
        let out = b.sync(&server, false).unwrap();
        assert_eq!(out.pulled, 0);
        assert_eq!(b.level("c.1"), None);
        assert_eq!(b.state.cursor("demo"), 0); // 游标不动，下次拉得到
    }

    #[test]
    fn 新机器较旧的本地库不覆盖中心里更新的进度() {
        let server = remote();
        let old = Device::new("pc-old");
        old.db().execute("INSERT INTO mastery VALUES('c.1', 1, NULL)", []).unwrap();
        std::thread::sleep(Duration::from_millis(30));
        let fresh = Device::new("pc-new");
        fresh.db().execute("INSERT INTO mastery VALUES('c.1', 9, NULL)", []).unwrap();
        fresh.sync(&server, true).unwrap(); // 中心里是较新的 9
        old.sync(&server, true).unwrap(); // 较旧的库首次同步：它的 1 不能盖掉 9
        assert_eq!(old.level("c.1"), Some(9));
    }

    #[test]
    fn 没有主键又没声明键列的表报错() {
        let dir = tempfile::tempdir().unwrap();
        let db = Connection::open(dir.path().join("x.db")).unwrap();
        db.execute_batch("CREATE TABLE loose(a TEXT, b TEXT)").unwrap();
        let err = table_info(&db, "loose", &TableSpec { mode: TableMode::Append, key: vec![] }).err().unwrap();
        assert!(err.contains("没有主键"), "{err}");
    }

    #[test]
    fn 表还没建时不拉取也不前进游标() {
        let server = remote();
        let a = Device::new("pc-a");
        a.db().execute("INSERT INTO mastery VALUES('c.1', 3, NULL)", []).unwrap();
        a.sync(&server, true).unwrap();
        let dir = tempfile::tempdir().unwrap();
        Connection::open(dir.path().join("learning.db")).unwrap(); // 空库，没有任何表
        let fresh = State::memory();
        let mut r = server.clone();
        let out = sync_with(&fresh, &mut r, "pc-b", "demo", &spec(), &dir.path().join("learning.db"), true).unwrap();
        assert_eq!(out.pulled, 0);
        assert_eq!(fresh.cursor("demo"), 0);
    }
}
