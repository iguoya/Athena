// Athena 线性代数（工）·视频课 — 独立壳：内容路径、进度库、播放窗格与播放桥（ADR 0182）。
// 课树与课堂脚本都在 content/，不进 Rust。

use serde::Serialize;
use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::{AppHandle, LogicalPosition, LogicalSize, Manager, State, Url, WebviewUrl};

struct AppState {
    content_root: PathBuf,
    /// 本应用自己的进度库：自建、自迁移，不依赖别的应用（主仓库 ADR 0037）。
    store_path: PathBuf,
    /// 播放窗格是否展开（窗口大小变化时按它重新排版）
    player_visible: Mutex<bool>,
    /// 播放桥最近一次上报与尚未被界面取走的事件。界面用 player_poll 取，不走前端事件 API：
    /// 应用清单一旦声明，plugin:event|listen 在 ui webview 里会被 ACL 拒绝（实测），轮询更简单也更稳。
    player: Mutex<PlayerState>,
}

#[derive(Default)]
struct PlayerState {
    last: Option<Value>,
    events: Vec<Value>,
}

#[derive(Clone, Serialize)]
struct AttemptRow {
    knowledge_id: String,
    item_id: String,
    correct: bool,
    answered_at: u64,
}

fn content_root() -> PathBuf {
    if let Ok(root) = std::env::var("ATHENA_LINEAR_ALGEBRA_VIDEO_ROOT") {
        return PathBuf::from(root).join("content");
    }
    // 发行包：按实际可执行文件找，不依赖编译机上烙进去的绝对路径。
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            let roots = [
                dir.to_path_buf(),
                dir.join(".."),
                // macOS .app：Tauri 把 ../content 打包到 Resources/_up_/content。
                dir.join("../Resources/_up_"),
            ];
            for root in roots {
                let candidate = root.join("content");
                if candidate.join("curriculum.json").is_file() {
                    return candidate;
                }
            }
        }
    }
    PathBuf::from("content")
}

/// 用户数据目录下本应用的目录（进度库、边看边标的记录都放这里，不进仓库；主仓库 ADR 0155）。
fn data_dir() -> PathBuf {
    // 目录名登记在 app.json 的 progress.dir，两处必须一致。
    dirs_next::data_dir().unwrap_or_else(|| PathBuf::from(".")).join("AthenaLinearAlgebraVideo")
}

fn store_path() -> PathBuf {
    data_dir().join("learning.db")
}

/// 内容 id 只允许字母数字与 . - _，防止界面传来的 id 钻出内容目录。
fn is_safe_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 128
        && !id.contains("..")
        && id.chars().all(|c| c.is_ascii_alphanumeric() || c == '.' || c == '-' || c == '_')
}

fn read_json(path: &Path) -> Result<Value, String> {
    let text = fs::read_to_string(path).map_err(|e| format!("读 {} 失败：{}", path.display(), e))?;
    serde_json::from_str(&text).map_err(|e| format!("{} 不是合法 JSON：{}", path.display(), e))
}

fn open_store(path: &Path) -> Result<rusqlite::Connection, String> {
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let conn = rusqlite::Connection::open(path).map_err(|e| e.to_string())?;
    // 与同步代理约定的事件表：只增不改，key = (knowledge_id, item_id, answered_at)（app.json 的 progress）。
    conn.execute(
        "CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            correct INTEGER NOT NULL,
            answered_at INTEGER NOT NULL
        )",
        [],
    )
    .map_err(|e| e.to_string())?;
    Ok(conn)
}

#[tauri::command]
fn get_curriculum(state: State<AppState>) -> Result<Value, String> {
    read_json(&state.content_root.join("curriculum.json"))
}

/// 一节课的课堂脚本（content/lessons/<id>.json）。
#[tauri::command]
fn get_lesson(state: State<AppState>, lesson_id: String) -> Result<Value, String> {
    if !is_safe_id(&lesson_id) {
        return Err(format!("非法课节引用：{lesson_id}"));
    }
    read_json(&state.content_root.join("lessons").join(format!("{lesson_id}.json")))
}

/// 只放行 https 外链（课程页、视频页）：内容文件里的链接不得借此打开本地路径或其他协议。
fn is_safe_url(url: &str) -> bool {
    url.starts_with("https://") && url.len() <= 2048 && !url.chars().any(|c| c.is_whitespace() || c.is_control())
}

#[tauri::command]
fn open_external(url: String) -> Result<(), String> {
    if !is_safe_url(&url) {
        return Err(format!("拒绝打开：{url}"));
    }
    tauri_plugin_opener::open_url(url, None::<&str>).map_err(|e| e.to_string())
}

// ---------------------------------------------------------------------------------------------
// 播放窗格与播放桥（ADR 0182 决策 3，播放页改用视频页见 ADR 0183）：B 站视频页作为主窗口的第二个 webview 停靠在右侧，
// 注入脚本 player_bridge.js 上报播放状态；页面只被放行 bridge_report 这一个命令（capabilities/player.json）。
// ---------------------------------------------------------------------------------------------

const PLAYER_BRIDGE_JS: &str = include_str!("player_bridge.js");
const PLAYER_FRACTION: f64 = 0.58;

/// B 站视频页（ADR 0183：外链播放器页面登录后也不允许切换清晰度，视频页可以）；bvid 与分集号来自课堂脚本，
/// 这里只拼 URL，且逐项校验字符，防止内容文件拼出别的地址。
fn player_url(bvid: &str, p: u32) -> Result<Url, String> {
    let ok = bvid.len() == 12 && bvid.starts_with("BV") && bvid.chars().all(|c| c.is_ascii_alphanumeric());
    if !ok || p == 0 || p > 1000 {
        return Err(format!("非法视频引用：{bvid} P{p}"));
    }
    Url::parse(&format!("https://www.bilibili.com/video/{bvid}/?p={p}")).map_err(|e| e.to_string())
}

fn layout(win: &tauri::Window, player_visible: bool) {
    let (Ok(size), Ok(sf)) = (win.inner_size(), win.scale_factor()) else { return };
    let (w, h) = (size.width as f64 / sf, size.height as f64 / sf);
    let pw = if player_visible { (w * PLAYER_FRACTION).max(480.0).min((w - 320.0).max(0.0)) } else { 0.0 };
    if let Some(ui) = win.get_webview("ui") {
        let _ = ui.set_position(LogicalPosition::new(0.0, 0.0));
        let _ = ui.set_size(LogicalSize::new(w - pw, h));
    }
    if let Some(pv) = win.get_webview("player") {
        if player_visible {
            let _ = pv.set_position(LogicalPosition::new(w - pw, 0.0));
            let _ = pv.set_size(LogicalSize::new(pw, h));
            let _ = pv.show();
        } else {
            let _ = pv.hide();
        }
    }
}

#[tauri::command]
fn player_load(app: AppHandle, bvid: String, p: u32) -> Result<(), String> {
    let url = player_url(&bvid, p)?;
    let pv = app.get_webview("player").ok_or("播放窗格未创建")?;
    pv.navigate(url).map_err(|e| e.to_string())
}

fn player_eval(app: &AppHandle, js: &str) -> Result<(), String> {
    let pv = app.get_webview("player").ok_or("播放窗格未创建")?;
    pv.eval(js).map_err(|e| e.to_string())
}

#[tauri::command]
fn player_seek(app: AppHandle, t: f64) -> Result<(), String> {
    if !t.is_finite() || !(0.0..=86400.0).contains(&t) {
        return Err("非法时间".into());
    }
    player_eval(&app, &format!("window.__athena&&window.__athena.seek({t})"))
}

/// 让播放桥立刻上报一次当前状态：界面 webview 晚于播放器页面加载时，错过了它的 ready 事件，靠这个补一次。
#[tauri::command]
fn player_ping(app: AppHandle) -> Result<(), String> {
    player_eval(&app, "window.__athena&&window.__athena.ping()")
}

#[tauri::command]
fn player_play(app: AppHandle) -> Result<(), String> {
    player_eval(&app, "window.__athena&&window.__athena.play()")
}

#[tauri::command]
fn player_pause(app: AppHandle) -> Result<(), String> {
    player_eval(&app, "window.__athena&&window.__athena.pause()")
}

/// 设置下一个暂停点（秒）；传负数表示清除。
#[tauri::command]
fn player_set_pause_point(app: AppHandle, t: f64) -> Result<(), String> {
    let arg = if t.is_finite() && t >= 0.0 { format!("{t}") } else { "null".to_string() };
    player_eval(&app, &format!("window.__athena&&window.__athena.setPausePoint({arg})"))
}

#[tauri::command]
fn player_set_visible(app: AppHandle, state: State<AppState>, visible: bool) -> Result<(), String> {
    *state.player_visible.lock().map_err(|e| e.to_string())? = visible;
    let win = app.get_window("main").ok_or("主窗口不存在")?;
    layout(&win, visible);
    Ok(())
}

/// 播放桥上报（由播放器页面调用，capabilities/player.json 只放行这一个命令）：转发给界面 webview。
#[tauri::command]
fn bridge_report(state: State<AppState>, ev: String, t: f64, paused: bool, duration: f64, note: String) {
    let msg = serde_json::json!({ "ev": ev, "t": t, "paused": paused, "duration": duration, "note": note });
    if let Ok(mut p) = state.player.lock() {
        // tick 只更新「最近状态」，不入事件队列（队列只留 ready/pause/pausepoint 这类离散事件，且有上限）
        if ev != "tick" {
            if p.events.len() >= 64 {
                p.events.remove(0);
            }
            p.events.push(msg.clone());
        }
        p.last = Some(msg);
    }
}

/// 界面轮询：返回播放桥最近一次上报，并取走离散事件队列。
#[tauri::command]
fn player_poll(state: State<AppState>) -> Value {
    let Ok(mut p) = state.player.lock() else { return Value::Null };
    serde_json::json!({ "last": p.last.clone(), "events": std::mem::take(&mut p.events) })
}

/// 登录 B 站：把右侧播放窗格临时导航到 B 站**官方**登录页，使用者在窗格里自己扫码或输入账号；登录完成后点「回到视频」再载入播放器。
/// 不另开窗口：实测从同步命令里创建新 webview 窗口，在 Windows 上会得到一个永远空白的窗口（about:blank）。
/// 登录状态存在本应用自己的 webview 数据目录，播放窗格共用；应用不读取、不保存账号与密码（ADR 0182 决策 4）。
/// 登录页不在 capabilities 放行的域名里，页面调不了任何应用命令。
#[tauri::command]
fn player_open_login(app: AppHandle, state: State<AppState>) -> Result<(), String> {
    let url = Url::parse("https://passport.bilibili.com/login").map_err(|e| e.to_string())?;
    // 播放窗格被收起时，登录前先展开，否则使用者看不到登录页
    *state.player_visible.lock().map_err(|e| e.to_string())? = true;
    if let Some(win) = app.get_window("main") {
        layout(&win, true);
    }
    let pv = app.get_webview("player").ok_or("播放窗格未创建")?;
    pv.navigate(url).map_err(|e| e.to_string())
}

/// 「边看边标」的记录：课堂脚本的时间戳由使用者边看边按键产生，先存本机，确认后再写进内容文件。
#[tauri::command]
fn save_marks(lesson_id: String, marks: Value) -> Result<(), String> {
    if !is_safe_id(&lesson_id) {
        return Err(format!("非法课节引用：{lesson_id}"));
    }
    let dir = data_dir().join("marks");
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    let text = serde_json::to_string_pretty(&marks).map_err(|e| e.to_string())?;
    fs::write(dir.join(format!("{lesson_id}.json")), text).map_err(|e| e.to_string())
}

#[tauri::command]
fn load_marks(lesson_id: String) -> Result<Value, String> {
    if !is_safe_id(&lesson_id) {
        return Err(format!("非法课节引用：{lesson_id}"));
    }
    let path = data_dir().join("marks").join(format!("{lesson_id}.json"));
    if !path.is_file() {
        return Ok(Value::Null);
    }
    read_json(&path)
}

#[tauri::command]
fn record_attempt(state: State<AppState>, knowledge_id: String, item_id: String, correct: bool) -> Result<(), String> {
    let conn = open_store(&state.store_path)?;
    let now = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    conn.execute(
        "INSERT INTO attempts (knowledge_id, item_id, correct, answered_at) VALUES (?1, ?2, ?3, ?4)",
        rusqlite::params![knowledge_id, item_id, correct as i64, now],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_attempts(state: State<AppState>) -> Result<Vec<AttemptRow>, String> {
    let conn = open_store(&state.store_path)?;
    let mut stmt = conn
        .prepare("SELECT knowledge_id, item_id, correct, answered_at FROM attempts ORDER BY answered_at, id")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok(AttemptRow {
                knowledge_id: row.get(0)?,
                item_id: row.get(1)?,
                correct: row.get::<_, i64>(2)? != 0,
                answered_at: row.get(3)?,
            })
        })
        .map_err(|e| e.to_string())?;
    rows.collect::<Result<Vec<_>, _>>().map_err(|e| e.to_string())
}

pub fn run() {
    let state = AppState { content_root: content_root(), store_path: store_path(), player_visible: Mutex::new(true), player: Mutex::new(PlayerState::default()) };
    let _ = open_store(&state.store_path);
    tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_opener::init())
        .manage(state)
        .setup(|app| {
            // 一个窗口、两个 webview：左边应用界面，右边 B 站播放器（可收起）。窗口由 Rust 创建，不在 tauri.conf.json 里声明。
            let win = tauri::window::WindowBuilder::new(app, "main")
                .title("线性代数（工）·视频课")
                .inner_size(1500.0, 900.0)
                .min_inner_size(900.0, 600.0)
                .maximized(true)
                .build()?;
            let ui = tauri::webview::WebviewBuilder::new("ui", WebviewUrl::App("index.html".into()));
            win.add_child(ui, LogicalPosition::new(0.0, 0.0), LogicalSize::new(800.0, 900.0))?;
            let first = player_url("BV1dr4y1n7vA", 3).expect("内置视频引用合法");
            let pv = tauri::webview::WebviewBuilder::new("player", WebviewUrl::External(first))
                .initialization_script(PLAYER_BRIDGE_JS);
            win.add_child(pv, LogicalPosition::new(800.0, 0.0), LogicalSize::new(700.0, 900.0))?;
            layout(&win, true);
            let handle = app.handle().clone();
            win.on_window_event(move |ev| {
                if let tauri::WindowEvent::Resized(_) = ev {
                    if let (Some(w), Some(st)) = (handle.get_window("main"), handle.try_state::<AppState>()) {
                        let vis = st.player_visible.lock().map(|g| *g).unwrap_or(true);
                        layout(&w, vis);
                    }
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_curriculum,
            get_lesson,
            open_external,
            record_attempt,
            get_attempts,
            player_load,
            player_seek,
            player_ping,
            player_poll,
            player_play,
            player_pause,
            player_set_pause_point,
            player_set_visible,
            bridge_report,
            player_open_login,
            save_marks,
            load_marks
        ])
        .run(tauri::generate_context!())
        .expect("error while running athena-linear-algebra-video");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn content_ids_reject_path_tricks() {
        for ok in ["p003", "a.b_c-1"] {
            assert!(is_safe_id(ok), "{ok} 应当合法");
        }
        for bad in ["", "..", "../x", "a/b", "a\\b", "/etc/passwd", "C:x", "a..b", "x y"] {
            assert!(!is_safe_id(bad), "{bad} 应当被拒绝");
        }
        assert!(!is_safe_id(&"a".repeat(129)), "过长的 id 应当被拒绝");
    }

    #[test]
    fn external_links_must_be_https() {
        assert!(is_safe_url("https://www.bilibili.com/video/BV1dr4y1n7vA"));
        for bad in ["http://x.org", "file:///C:/x", "javascript:alert(1)", "https://a b", "https://a\nb", ""] {
            assert!(!is_safe_url(bad), "{bad} 应当被拒绝");
        }
    }

    #[test]
    fn player_url_only_builds_the_official_video_page() {
        let u = player_url("BV1dr4y1n7vA", 3).unwrap();
        assert_eq!(u.host_str(), Some("www.bilibili.com"));
        assert!(u.path().starts_with("/video/BV1dr4y1n7vA") && u.query() == Some("p=3"));
        for (b, p) in [("BV1dr4y1n7v", 3), ("XX1dr4y1n7vA", 3), ("BV1dr4y1n7vA&x=1", 3), ("BV1dr4y1n7vA", 0), ("BV1dr4y1n7vA", 1001)] {
            assert!(player_url(b, p).is_err(), "{b} P{p} 应当被拒绝");
        }
    }

    #[test]
    fn attempts_roundtrip_in_answer_order() {
        let dir = std::env::temp_dir().join(format!("athena-lavideo-test-{}", std::process::id()));
        let path = dir.join("learning.db");
        let conn = open_store(&path).unwrap();
        // 后入库但答题时间更早的记录（同步拉回的旧记录）必须排在前面：「最近一次」按 answered_at 认。
        conn.execute("INSERT INTO attempts (knowledge_id,item_id,correct,answered_at) VALUES ('k','i',1,200)", []).unwrap();
        conn.execute("INSERT INTO attempts (knowledge_id,item_id,correct,answered_at) VALUES ('k','i',0,100)", []).unwrap();
        let mut stmt = conn.prepare("SELECT answered_at FROM attempts ORDER BY answered_at, id").unwrap();
        let got: Vec<u64> = stmt.query_map([], |r| r.get(0)).unwrap().map(|x| x.unwrap()).collect();
        assert_eq!(got, vec![100, 200]);
        let _ = std::fs::remove_dir_all(&dir);
    }
}
