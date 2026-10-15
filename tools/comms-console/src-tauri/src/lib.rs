// 协作观察台数据层（ADR 0166）：文件是唯一权威，PG 是投影，本应用只读。
//
// load_snapshot 的三级策略：
//   1. 读本地 comms/ 各舱（文件解析，纯函数，永远可用）；
//   2. 配了 DSN 就把本地文件 ingest 进路由器 PG（幂等，按内容哈希去重），
//      再从 PG 查询全量——别的机器投进来的协作史也能看到（多机汇聚）；
//   3. PG 不可达或未配置就降级用本地文件，界面标明数据来源。

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use serde::Serialize;

#[derive(Serialize, Clone)]
struct BayInfo {
    name: String,
    leader: String,
    agents: Vec<String>,
}

#[derive(Serialize, Clone)]
struct TaskEvent {
    at: String,
    actor: String,
    from_status: String,
    to_status: String,
    note: String,
}

#[derive(Serialize, Clone)]
struct TaskRow {
    bay: String,
    tid: String,
    title: String,
    owner: String,
    status: String,
    priority: String,
    depends: String,
    created: String,
    updated: String,
    body: String,
    events: Vec<TaskEvent>,
}

#[derive(Serialize, Clone)]
struct MsgRow {
    bay: String,
    msg_id: String,
    from_a: String,
    to_a: String,
    subject: String,
    created: String,
    thread: String,
    task: String,
    body: String,
}

#[derive(Serialize, Clone)]
struct ChatRow {
    bay: String,
    ts: String,
    sender: String,
    to_a: String,
    text: String,
    seq: i32,
}

#[derive(Serialize)]
struct Snapshot {
    source: String,
    note: String,
    bays: Vec<BayInfo>,
    tasks: Vec<TaskRow>,
    msgs: Vec<MsgRow>,
    chats: Vec<ChatRow>,
}

// ---------------------------------------------------------------- 本地定位

/// 仓库根：env 指定优先；否则从当前目录逐级向上找带 `comms/comms.py` 的目录
/// （dev 时进程 cwd 是 src-tauri，向上三四级必到仓库根）。
fn athena_root() -> Option<PathBuf> {
    if let Ok(v) = std::env::var("ATHENA_COMMS_CONSOLE_ROOT") {
        let p = PathBuf::from(v);
        if p.join("comms").is_dir() {
            return Some(p);
        }
    }
    let mut cur = std::env::current_dir().ok()?;
    loop {
        if cur.join("comms").join("comms.py").is_file() {
            return Some(cur);
        }
        if !cur.pop() {
            return None;
        }
    }
}

/// PG DSN：环境变量优先，其次用户数据目录 AthenaCommsConsole/pg.json 的 {"dsn": "..."}。
/// 都没有就是纯本地模式，不算错误。
fn pg_dsn() -> Option<String> {
    if let Ok(v) = std::env::var("ATHENA_COMMS_PG") {
        if !v.trim().is_empty() {
            return Some(v);
        }
    }
    let dir = dirs_next::data_dir()?.join("AthenaCommsConsole");
    let raw = std::fs::read_to_string(dir.join("pg.json")).ok()?;
    let v: serde_json::Value = serde_json::from_str(&raw).ok()?;
    v.get("dsn")?.as_str().map(String::from)
}

// ---------------------------------------------------------------- 文件解析

/// `---\nk: v\n---\n` front matter。
fn parse_front_matter(raw: &str) -> (BTreeMap<String, String>, String) {
    if let Some(rest) = raw.strip_prefix("---\n") {
        if let Some(end) = rest.find("\n---\n") {
            let mut meta = BTreeMap::new();
            for line in rest[..end].lines() {
                if let Some((k, v)) = line.split_once(':') {
                    meta.insert(k.trim().to_string(), v.trim().to_string());
                }
            }
            return (meta, rest[end + 5..].to_string());
        }
    }
    (BTreeMap::new(), raw.to_string())
}

/// 任务正文「## 进展记录」下的流转行：`- [YYYY-MM-DD HH:MM] actor：old → new · note`
fn parse_events(body: &str) -> Vec<TaskEvent> {
    let mut out = Vec::new();
    let Some(idx) = body.find("## 进展记录") else {
        return out;
    };
    for line in body[idx..].lines() {
        let line = line.trim();
        let Some(rest) = line.strip_prefix("- [") else {
            continue;
        };
        let Some(close) = rest.find("]") else {
            continue;
        };
        let at = rest[..close].trim().to_string();
        let rest = rest[close + 1..].trim_start();
        let Some((actor, rest)) = rest.split_once('：') else {
            continue;
        };
        let (flow, note) = rest.split_once('·').unwrap_or((rest, ""));
        let mut it = flow.split('→').map(str::trim);
        let from_status = it.next().unwrap_or("").to_string();
        let to_status = it.next().unwrap_or("").to_string();
        if from_status.is_empty() && to_status.is_empty() {
            continue;
        }
        out.push(TaskEvent {
            at,
            actor: actor.trim().to_string(),
            from_status,
            to_status,
            note: note.trim().to_string(),
        });
    }
    out
}

fn list_bays(root: &Path) -> Vec<String> {
    let mut bays: Vec<String> = std::fs::read_dir(root.join("comms"))
        .into_iter()
        .flatten()
        .filter_map(Result::ok)
        .filter(|e| e.path().join("config.json").is_file())
        .filter_map(|e| e.file_name().into_string().ok())
        .collect();
    bays.sort();
    bays
}

fn parse_bay_config(root: &Path, bay: &str) -> Option<BayInfo> {
    let raw = std::fs::read_to_string(root.join("comms").join(bay).join("config.json")).ok()?;
    let v: serde_json::Value = serde_json::from_str(&raw).ok()?;
    Some(BayInfo {
        name: bay.to_string(),
        leader: v.get("leader")?.as_str()?.to_string(),
        agents: v
            .get("agents")?
            .as_array()?
            .iter()
            .filter_map(|x| x.as_str().map(String::from))
            .collect(),
    })
}

/// 从一个舱读全部任务 / 消息 / 即时消息。任何单文件解析失败都跳过——观察台
/// 宁可少显示一条也不因脏数据整体失败。
fn parse_bay_files(root: &Path, bay: &str) -> (Vec<TaskRow>, Vec<MsgRow>, Vec<ChatRow>) {
    let home = root.join("comms").join(bay);
    let mut tasks = Vec::new();
    if let Ok(dir) = std::fs::read_dir(home.join("tasks")) {
        for e in dir.flatten() {
            let path = e.path();
            if path.extension().and_then(|s| s.to_str()) != Some("md") {
                continue;
            }
            let Ok(raw) = std::fs::read_to_string(&path) else {
                continue;
            };
            let (meta, body) = parse_front_matter(&raw);
            if !meta.contains_key("id") {
                continue;
            }
            let get = |k: &str| meta.get(k).cloned().unwrap_or_default();
            let events = parse_events(&body);
            tasks.push(TaskRow {
                bay: bay.to_string(),
                tid: get("id"),
                title: get("title"),
                owner: get("owner"),
                status: get("status"),
                priority: get("priority"),
                depends: get("depends"),
                created: get("created"),
                updated: get("updated"),
                body,
                events,
            });
        }
    }
    let mut msgs = Vec::new();
    if let Ok(dir) = std::fs::read_dir(home.join("msgs")) {
        for e in dir.flatten() {
            let name = e.file_name().into_string().unwrap_or_default();
            if !name.ends_with(".md") {
                continue;
            }
            let Ok(raw) = std::fs::read_to_string(e.path()) else {
                continue;
            };
            let (meta, body) = parse_front_matter(&raw);
            if !meta.contains_key("from") {
                continue;
            }
            let get = |k: &str| meta.get(k).cloned().unwrap_or_default();
            // 文件名 20261015-182847__from__to__slug.md 的前 15 位就是消息 id（comms.py msg_id）。
            msgs.push(MsgRow {
                bay: bay.to_string(),
                msg_id: name.get(..15).unwrap_or(&name).to_string(),
                from_a: get("from"),
                to_a: get("to"),
                subject: get("subject"),
                created: get("created"),
                thread: get("thread"),
                task: get("task"),
                body,
            });
        }
    }
    let mut chats = Vec::new();
    if let Ok(dir) = std::fs::read_dir(home.join("chat")) {
        for e in dir.flatten() {
            let path = e.path();
            if path.extension().and_then(|s| s.to_str()) != Some("log") {
                continue;
            }
            let sender = path.file_stem().and_then(|s| s.to_str()).unwrap_or("");
            let Ok(raw) = std::fs::read_to_string(&path) else {
                continue;
            };
            for (i, line) in raw.lines().enumerate() {
                // 每行：YYYY-MM-DD HH:MM:SS|to|text
                let mut it = line.splitn(3, '|');
                let (Some(ts), Some(to), Some(text)) = (it.next(), it.next(), it.next()) else {
                    continue;
                };
                chats.push(ChatRow {
                    bay: bay.to_string(),
                    ts: ts.trim().to_string(),
                    sender: sender.to_string(),
                    to_a: to.trim().to_string(),
                    text: text.to_string(),
                    seq: i as i32,
                });
            }
        }
    }
    (tasks, msgs, chats)
}

fn local_snapshot() -> Option<Snapshot> {
    let root = athena_root()?;
    let mut bays = Vec::new();
    let mut tasks = Vec::new();
    let mut msgs = Vec::new();
    let mut chats = Vec::new();
    for bay in list_bays(&root) {
        if let Some(info) = parse_bay_config(&root, &bay) {
            bays.push(info);
        }
        let (t, m, c) = parse_bay_files(&root, &bay);
        tasks.extend(t);
        msgs.extend(m);
        chats.extend(c);
    }
    Some(Snapshot {
        source: "files".into(),
        note: "本地文件".into(),
        bays,
        tasks,
        msgs,
        chats,
    })
}

// ---------------------------------------------------------------- PG 投影

const SCHEMA: &str = "
CREATE TABLE IF NOT EXISTS bays (
  name text PRIMARY KEY, leader text NOT NULL, agents text NOT NULL);
CREATE TABLE IF NOT EXISTS tasks (
  bay text NOT NULL, tid text NOT NULL, title text NOT NULL, owner text NOT NULL,
  status text NOT NULL, priority text NOT NULL, depends text NOT NULL DEFAULT '',
  created text NOT NULL, updated text NOT NULL, body text NOT NULL,
  PRIMARY KEY (bay, tid));
CREATE TABLE IF NOT EXISTS task_events (
  bay text NOT NULL, tid text NOT NULL, seq int NOT NULL,
  at text NOT NULL, actor text NOT NULL,
  from_status text NOT NULL, to_status text NOT NULL, note text NOT NULL DEFAULT '',
  PRIMARY KEY (bay, tid, seq));
CREATE TABLE IF NOT EXISTS msgs (
  bay text NOT NULL, msg_id text NOT NULL, from_a text NOT NULL, to_a text NOT NULL,
  subject text NOT NULL, created text NOT NULL, thread text NOT NULL DEFAULT '',
  task text NOT NULL DEFAULT '', body text NOT NULL,
  PRIMARY KEY (bay, msg_id));
CREATE TABLE IF NOT EXISTS chats (
  bay text NOT NULL, sender text NOT NULL, seq int NOT NULL,
  ts text NOT NULL, to_a text NOT NULL, text_ text NOT NULL,
  PRIMARY KEY (bay, sender, seq));
CREATE TABLE IF NOT EXISTS sync_files (
  bay text NOT NULL, relpath text NOT NULL, sha text NOT NULL, synced_at text NOT NULL,
  PRIMARY KEY (bay, relpath));
";

fn content_sha(bytes: &[u8]) -> String {
    use sha2::Digest;
    let digest = sha2::Sha256::digest(bytes);
    let mut out = String::new();
    for b in digest {
        out.push_str(&format!("{b:02x}"));
    }
    out
}

type Apply = dyn Fn(&mut postgres::Client) -> Result<(), String>;

/// 以「舱 + 相对路径」为单位同步一个文件：内容哈希没变就跳过，变了就整文件重写。
fn sync_file(
    client: &mut postgres::Client,
    bay: &str,
    relpath: &str,
    bytes: &[u8],
    apply: &Apply,
) -> Result<(), String> {
    let sha = content_sha(bytes);
    let known: Option<String> = client
        .query_opt(
            "SELECT sha FROM sync_files WHERE bay=$1 AND relpath=$2",
            &[&bay, &relpath],
        )
        .map_err(|e| e.to_string())?
        .and_then(|r| r.get(0));
    if known.as_deref() == Some(sha.as_str()) {
        return Ok(());
    }
    apply(client)?;
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
        .to_string();
    client
        .execute(
            "INSERT INTO sync_files (bay, relpath, sha, synced_at) VALUES ($1,$2,$3,$4)
             ON CONFLICT (bay, relpath) DO UPDATE SET sha=$3, synced_at=$4",
            &[&bay, &relpath, &sha, &now],
        )
        .map_err(|e| e.to_string())?;
    Ok(())
}

/// 把本地 comms/ 各舱 upsert 进 PG。任何错误向上返回，由调用方降级。
fn ingest(client: &mut postgres::Client, root: &Path) -> Result<(), String> {
    client.batch_execute(SCHEMA).map_err(|e| e.to_string())?;
    for bay in list_bays(root) {
        let home = root.join("comms").join(&bay);
        if let Some(info) = parse_bay_config(root, &bay) {
            let bytes = std::fs::read(home.join("config.json")).unwrap_or_default();
            let agents = info.agents.join(",");
            let (leader, name) = (info.leader.clone(), info.name.clone());
            sync_file(client, &bay, "config.json", &bytes, &move |c| {
                c.execute(
                    "INSERT INTO bays (name, leader, agents) VALUES ($1,$2,$3)
                     ON CONFLICT (name) DO UPDATE SET leader=$2, agents=$3",
                    &[&name, &leader, &agents],
                )
                .map(|_| ())
                .map_err(|e| e.to_string())
            })?;
        }
        if let Ok(dir) = std::fs::read_dir(home.join("tasks")) {
            for e in dir.flatten() {
                let path = e.path();
                if path.extension().and_then(|s| s.to_str()) != Some("md") {
                    continue;
                }
                let bytes = match std::fs::read(&path) {
                    Ok(b) => b,
                    Err(_) => continue,
                };
                let raw = String::from_utf8_lossy(&bytes).into_owned();
                let (meta, body) = parse_front_matter(&raw);
                if !meta.contains_key("id") {
                    continue;
                }
                let get = |k: &str| meta.get(k).cloned().unwrap_or_default();
                let rel = match path.strip_prefix(&home) {
                    Ok(p) => p.to_string_lossy().into_owned(),
                    Err(_) => continue,
                };
                let (tid, title, owner, status, priority, depends, created, updated, body2, bay2) = (
                    get("id"),
                    get("title"),
                    get("owner"),
                    get("status"),
                    get("priority"),
                    get("depends"),
                    get("created"),
                    get("updated"),
                    body.clone(),
                    bay.clone(),
                );
                let events = parse_events(&body);
                sync_file(client, &bay, &rel, &bytes, &move |c| {
                    let mut tx = c.transaction().map_err(|e| e.to_string())?;
                    tx.execute("DELETE FROM task_events WHERE bay=$1 AND tid=$2", &[&bay2, &tid])
                        .map_err(|e| e.to_string())?;
                    tx.execute("DELETE FROM tasks WHERE bay=$1 AND tid=$2", &[&bay2, &tid])
                        .map_err(|e| e.to_string())?;
                    tx.execute(
                        "INSERT INTO tasks (bay, tid, title, owner, status, priority, depends, created, updated, body)
                         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
                        &[&bay2, &tid, &title, &owner, &status, &priority, &depends, &created, &updated, &body2],
                    )
                    .map_err(|e| e.to_string())?;
                    for (i, ev) in events.iter().enumerate() {
                        tx.execute(
                            "INSERT INTO task_events (bay, tid, seq, at, actor, from_status, to_status, note)
                             VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
                            &[&bay2, &tid, &(i as i32), &ev.at, &ev.actor, &ev.from_status, &ev.to_status, &ev.note],
                        )
                        .map_err(|e| e.to_string())?;
                    }
                    tx.commit().map_err(|e| e.to_string())
                })?;
            }
        }
        if let Ok(dir) = std::fs::read_dir(home.join("msgs")) {
            for e in dir.flatten() {
                let name = e.file_name().into_string().unwrap_or_default();
                if !name.ends_with(".md") {
                    continue;
                }
                let bytes = match std::fs::read(e.path()) {
                    Ok(b) => b,
                    Err(_) => continue,
                };
                let raw = String::from_utf8_lossy(&bytes).into_owned();
                let (meta, body) = parse_front_matter(&raw);
                if !meta.contains_key("from") {
                    continue;
                }
                let get = |k: &str| meta.get(k).cloned().unwrap_or_default();
                let (msg_id, from_a, to_a, subject, created, thread, task, body2, bay2) = (
                    name.get(..15).unwrap_or(&name).to_string(),
                    get("from"),
                    get("to"),
                    get("subject"),
                    get("created"),
                    get("thread"),
                    get("task"),
                    body,
                    bay.clone(),
                );
                sync_file(client, &bay, &format!("msgs/{name}"), &bytes, &move |c| {
                    c.execute(
                        "INSERT INTO msgs (bay, msg_id, from_a, to_a, subject, created, thread, task, body)
                         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                         ON CONFLICT (bay, msg_id) DO UPDATE SET from_a=$3, to_a=$4, subject=$5,
                           created=$6, thread=$7, task=$8, body=$9",
                        &[&bay2, &msg_id, &from_a, &to_a, &subject, &created, &thread, &task, &body2],
                    )
                    .map(|_| ())
                    .map_err(|e| e.to_string())
                })?;
            }
        }
        if let Ok(dir) = std::fs::read_dir(home.join("chat")) {
            for e in dir.flatten() {
                let path = e.path();
                if path.extension().and_then(|s| s.to_str()) != Some("log") {
                    continue;
                }
                let sender = path.file_stem().and_then(|s| s.to_str()).unwrap_or("").to_string();
                let bytes = match std::fs::read(&path) {
                    Ok(b) => b,
                    Err(_) => continue,
                };
                let raw = String::from_utf8_lossy(&bytes).into_owned();
                let rows: Vec<(i32, String, String, String)> = raw
                    .lines()
                    .enumerate()
                    .filter_map(|(i, line)| {
                        let mut it = line.splitn(3, '|');
                        let (ts, to, text) = (it.next()?, it.next()?, it.next()?);
                        Some((i as i32, ts.trim().to_string(), to.trim().to_string(), text.to_string()))
                    })
                    .collect();
                let rel = format!("chat/{sender}.log");
                let bay2 = bay.clone();
                sync_file(client, &bay, &rel, &bytes, &move |c| {
                    let mut tx = c.transaction().map_err(|e| e.to_string())?;
                    tx.execute("DELETE FROM chats WHERE bay=$1 AND sender=$2", &[&bay2, &sender])
                        .map_err(|e| e.to_string())?;
                    for (seq, ts, to, text) in &rows {
                        tx.execute(
                            "INSERT INTO chats (bay, sender, seq, ts, to_a, text_) VALUES ($1,$2,$3,$4,$5,$6)",
                            &[&bay2, &sender, seq, ts, to, text],
                        )
                        .map_err(|e| e.to_string())?;
                    }
                    tx.commit().map_err(|e| e.to_string())
                })?;
            }
        }
    }
    Ok(())
}

fn query_pg(client: &mut postgres::Client) -> Result<Snapshot, String> {
    let mut bays = Vec::new();
    for r in client
        .query("SELECT name, leader, agents FROM bays", &[])
        .map_err(|e| e.to_string())?
    {
        let agents: String = r.get(2);
        bays.push(BayInfo {
            name: r.get(0),
            leader: r.get(1),
            agents: agents.split(',').filter(|s| !s.is_empty()).map(String::from).collect(),
        });
    }
    let mut tasks = Vec::new();
    for r in client
        .query(
            "SELECT bay, tid, title, owner, status, priority, depends, created, updated, body FROM tasks",
            &[],
        )
        .map_err(|e| e.to_string())?
    {
        let (bay, tid) = (r.get::<_, String>(0), r.get::<_, String>(1));
        let mut events = Vec::new();
        for er in client
            .query(
                "SELECT at, actor, from_status, to_status, note FROM task_events
                 WHERE bay=$1 AND tid=$2 ORDER BY seq",
                &[&bay, &tid],
            )
            .map_err(|e| e.to_string())?
        {
            events.push(TaskEvent {
                at: er.get(0),
                actor: er.get(1),
                from_status: er.get(2),
                to_status: er.get(3),
                note: er.get(4),
            });
        }
        tasks.push(TaskRow {
            bay,
            tid,
            title: r.get(2),
            owner: r.get(3),
            status: r.get(4),
            priority: r.get(5),
            depends: r.get(6),
            created: r.get(7),
            updated: r.get(8),
            body: r.get(9),
            events,
        });
    }
    let mut msgs = Vec::new();
    for r in client
        .query(
            "SELECT bay, msg_id, from_a, to_a, subject, created, thread, task, body FROM msgs",
            &[],
        )
        .map_err(|e| e.to_string())?
    {
        msgs.push(MsgRow {
            bay: r.get(0),
            msg_id: r.get(1),
            from_a: r.get(2),
            to_a: r.get(3),
            subject: r.get(4),
            created: r.get(5),
            thread: r.get(6),
            task: r.get(7),
            body: r.get(8),
        });
    }
    let mut chats = Vec::new();
    for r in client
        .query("SELECT bay, sender, seq, ts, to_a, text_ FROM chats", &[])
        .map_err(|e| e.to_string())?
    {
        chats.push(ChatRow {
            bay: r.get(0),
            sender: r.get(1),
            seq: r.get(2),
            ts: r.get(3),
            to_a: r.get(4),
            text: r.get(5),
        });
    }
    Ok(Snapshot {
        source: "pg".into(),
        note: "中心库（路由器 PostgreSQL 投影，多机汇聚）".into(),
        bays,
        tasks,
        msgs,
        chats,
    })
}

fn load_inner() -> Snapshot {
    let Some(local) = local_snapshot() else {
        return Snapshot {
            source: "none".into(),
            note: "没找到仓库（comms/ 目录）；设 ATHENA_COMMS_CONSOLE_ROOT 指到仓库根".into(),
            bays: vec![],
            tasks: vec![],
            msgs: vec![],
            chats: vec![],
        };
    };
    let Some(dsn) = pg_dsn() else {
        return local;
    };
    let attempt = || -> Result<Snapshot, String> {
        let mut client = postgres::Client::connect(&dsn, postgres::NoTls).map_err(|e| e.to_string())?;
        let root = athena_root().ok_or("仓库根不可见")?;
        ingest(&mut client, &root)?;
        query_pg(&mut client)
    };
    match attempt() {
        Ok(snap) => snap,
        Err(e) => {
            let mut s = local;
            s.note = format!("本地文件（中心库不可用：{e}）");
            s
        }
    }
}

#[tauri::command(async)]
fn load_snapshot() -> Result<Snapshot, String> {
    Ok(load_inner())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![load_snapshot])
        .run(tauri::generate_context!())
        .expect("error while running athena-comms-console");
}
