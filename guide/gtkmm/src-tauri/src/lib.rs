// Athena GTKMM — 独立壳：内容路径、进度库、演示进程 spawn 与 JSON-RPC 转发。
// 不依赖主程序或其他应用。壳要薄：业务文案与课树不进 Rust（应用 ADR 0001）。

use serde::Serialize;
use serde_json::{json, Value};
use base64::Engine as _;
use std::collections::HashMap;
use std::ffi::OsString;
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::{AppHandle, Emitter, State};

struct AppState {
    content_root: PathBuf,
    /// 本应用自己的进度库：自建、自迁移，不依赖别的应用（ADR 0037、0053）。
    store_path: PathBuf,
    demos: Mutex<HashMap<String, Child>>,
}

#[derive(Clone, Serialize)]
struct LaunchResult {
    ok: bool,
    message: String,
}

#[derive(Clone, Serialize)]
struct AttemptRow {
    knowledge_id: String,
    item_id: String,
    correct: bool,
    answered_at: u64,
}

#[derive(Clone, Serialize)]
struct MyTranslationRow {
    sha: String,
    text: String,
    updated_at: u64,
}

#[derive(Clone, Serialize)]
struct SourceFile {
    path: String,
    content: String,
}

fn content_root() -> PathBuf {
    if let Ok(root) = std::env::var("ATHENA_GTKMM_ROOT") {
        return PathBuf::from(root).join("content");
    }

    // 先按实际可执行文件找，避免发行包错误依赖编译机上烙进去的绝对路径。
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

fn store_path() -> PathBuf {
    // 进度库放用户数据目录，不进仓库（ADR 0155）：启动器的同步代理在能连上路由器时
    // 把它与中心库互推。目录名登记在 app.json 的 progress.dir，两处必须一致。
    let base = dirs_next::data_dir().unwrap_or_else(|| PathBuf::from("."));
    base.join("AthenaGTKMM").join("learning.db")
}

fn read_content(root: &Path, name: &str) -> Result<Value, String> {
    let path = root.join(name);
    let text = fs::read_to_string(&path)
        .map_err(|error| format!("读 {} 失败：{}", path.display(), error))?;
    serde_json::from_str(&text).map_err(|error| format!("{} 不是合法 JSON：{}", name, error))
}

/// 演示产物命名规则与 scripts/check.py 的 check_native 一致：id 中的 `.` 换成 `-`。
fn demo_binary(app_root: &Path, demo_id: &str) -> PathBuf {
    let stem = demo_id.replace('.', "-");
    let base = app_root.join("build-native").join(&stem);
    if cfg!(windows) {
        let exe = base.with_extension("exe");
        if exe.is_file() {
            return exe;
        }
    }
    base
}

/// 从清单里找实体（演示与实验同表），返回 (id, source_dir)。
fn find_entity(manifest: &Value, demo_id: &str) -> Option<Value> {
    for kind in ["demos", "experiments"] {
        if let Some(items) = manifest.get(kind).and_then(|v| v.as_array()) {
            for entity in items {
                if entity.get("id").and_then(|v| v.as_str()) == Some(demo_id) {
                    return Some(entity.clone());
                }
            }
        }
    }
    None
}

/// 官方示例实体（content/demos.json 的 examples 数组，应用 ADR 0006）。
fn find_example(manifest: &Value, example_id: &str) -> Option<Value> {
    manifest
        .get("examples")?
        .as_array()?
        .iter()
        .find(|entity| entity.get("id").and_then(|v| v.as_str()) == Some(example_id))
        .cloned()
}

/// Windows 上 gtkmm-4.0 的 MSYS2 工具链（与 scripts/check.py 的
/// msys2_mingw64 同源）；非 Windows 返回 None，工具链走系统路径。
fn msys2_mingw64() -> Option<PathBuf> {
    for candidate in ["C:/msys64/mingw64", "D:/msys64/mingw64"] {
        let dir = PathBuf::from(candidate);
        if dir.join("bin").join("pkgconf.exe").is_file()
            && dir.join("lib").join("pkgconfig").join("gtkmm-4.0.pc").is_file()
        {
            return Some(dir);
        }
    }
    None
}

/// 原生命令的运行环境：Windows 下前置 MSYS2 mingw64（cmake 要找 ninja/gcc，
/// GTK 程序要找运行时 DLL），并指好 pkg-config；其他平台原样继承。
fn native_env(command: &mut Command) -> &mut Command {
    if let Some(mingw) = msys2_mingw64() {
        command
            .env("PATH", prepend_path(&mingw.join("bin")))
            .env("PKG_CONFIG_PATH", mingw.join("lib").join("pkgconfig"));
    }
    command
}

/// 把目录插到现有 PATH 最前（读注册表 PATH 太重，继承本进程 PATH 即够：
/// 壳由启动器从带完整工具链的 shell 拉起）。
fn prepend_path(dir: &Path) -> OsString {
    let existing = std::env::var_os("PATH").unwrap_or_default();
    let mut parts = vec![dir.to_path_buf()];
    parts.extend(std::env::split_paths(&existing));
    std::env::join_paths(parts).unwrap_or(existing)
}

/// 官方示例的编译：产物缺失时对 exercise 工程做 configure + 增量编译
/// （与 check.py 的 build-exercise 同一目录，编译一次两边复用）。
fn ensure_example_built(app_root: &Path, build_target: &str) -> Result<PathBuf, String> {
    let base = app_root.join("build-exercise").join(build_target);
    let binary = if cfg!(windows) {
        let exe = base.with_extension("exe");
        if exe.is_file() {
            return Ok(exe);
        }
        exe
    } else {
        base
    };

    let configure = native_env(
        Command::new("cmake")
            .args(["-G", "Ninja", "-S", "exercise", "-B", "build-exercise"])
            .current_dir(app_root),
    )
    .output()
    .map_err(|error| format!("找不到 cmake（{error}）——开发机应有完整工具链"))?;
    if !configure.status.success() {
        return Err(format!(
            "CMake configure 失败：{}",
            String::from_utf8_lossy(&configure.stderr)
        ));
    }
    let build = native_env(
        Command::new("cmake")
            .args(["--build", "build-exercise"])
            .current_dir(app_root),
    )
    .output()
    .map_err(|error| format!("运行 cmake 失败：{error}"))?;
    if !build.status.success() {
        return Err(format!(
            "示例编译失败：{}",
            String::from_utf8_lossy(&build.stderr)
        ));
    }
    if !binary.is_file() {
        return Err(format!("编译完成但产物缺失：{}", binary.display()));
    }
    Ok(binary)
}

fn init_store(path: &Path) -> rusqlite::Connection {
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let connection = rusqlite::Connection::open(path)
        .unwrap_or_else(|error| panic!("打开进度库 {} 失败：{}", path.display(), error));
    connection
        .execute(
            "CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                correct INTEGER NOT NULL,
                answered_at INTEGER NOT NULL
            )",
            [],
        )
        .expect("建 attempts 表失败");
    connection
        .execute(
            // 学习者自己的译文：按段落 sha 存（快照块的稳定标识），
            // 官方译文是内容、这里是个人产物，随进度库走（ADR 0037、0053）
            "CREATE TABLE IF NOT EXISTS my_translations (
                sha TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            )",
            [],
        )
        .expect("建 my_translations 表失败");
    connection
}

#[tauri::command]
fn get_curriculum(state: State<AppState>) -> Result<Value, String> {
    read_content(&state.content_root, "curriculum.json")
}

#[tauri::command]
fn get_manifest(state: State<AppState>) -> Result<Value, String> {
    read_content(&state.content_root, "demos.json")
}

/// 英译训练标注数据（content/vocab.json：难词表 + 句型表）。
#[tauri::command]
fn get_vocab(state: State<AppState>) -> Result<Value, String> {
    read_content(&state.content_root, "vocab.json")
}

/// 章/节 id 只会是官方 DocBook 的 xml:id（字母、数字、点、横线）。前端传来的 id 直接拼进
/// content/ 下的路径，所以先卡死字符集：`..`、路径分隔符、盘符和绝对路径都进不来
/// （`get_figure` 对图片引用做的是同一件事）。
fn is_safe_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 128
        && !id.contains("..")
        && id
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '.' || c == '-' || c == '_')
}

/// 官方节页的段落快照（content/chapters/<章>/<节>.json，原文+逐段中文，
/// 由 scripts/sync_upstream.py 生成——应用 ADR 0002 的段落级追踪）。
#[tauri::command]
fn get_page_content(state: State<AppState>, chapter_id: String, page_id: String) -> Result<String, String> {
    if !is_safe_id(&chapter_id) || !is_safe_id(&page_id) {
        return Err(format!("非法章节引用：{chapter_id}/{page_id}"));
    }
    let path = state
        .content_root
        .join("chapters")
        .join(&chapter_id)
        .join(format!("{page_id}.json"));
    fs::read_to_string(&path).map_err(|error| format!("读 {} 失败：{}", path.display(), error))
}

/// PO 翻译单元映射（content/po-units/<章>.json，scripts/align_po.py 生成——
/// 应用 ADR 0005：显示/自译/导出都以官网 PO 翻译单元为准）。章没有映射时
/// 返回 null（对齐是渐进的，前端按节兜底词数聚合）。
#[tauri::command]
fn get_po_units(state: State<AppState>, chapter_id: String) -> Result<Value, String> {
    if !is_safe_id(&chapter_id) {
        return Err(format!("非法章节引用：{chapter_id}"));
    }
    let path = state
        .content_root
        .join("po-units")
        .join(format!("{chapter_id}.json"));
    match fs::read_to_string(&path) {
        Ok(text) => {
            serde_json::from_str(&text).map_err(|error| format!("{} 不是合法 JSON：{}", path.display(), error))
        }
        Err(_) => Ok(Value::Null),
    }
}

/// 官方教程插图：读 content/ 下的图片文件，返回 data URL。
/// 图片与快照 JSON 走同一条 command 通道——开发模式不赌 vite 对仓库根的
/// 静态服务，发行包也不受资源目录在 webview HTTP 空间里的布局影响；
/// 这条链路在任何启动形态下（dev / build / 打包）行为都一致。
#[tauri::command]
fn get_figure(state: State<AppState>, image_ref: String) -> Result<String, String> {
    // 路径安全：只接受 content/ 内的相对引用，拒绝目录穿越、绝对路径与盘符
    if image_ref.is_empty()
        || image_ref.contains("..")
        || image_ref.contains('\\')
        || image_ref.starts_with('/')
        || image_ref.contains(':')
    {
        return Err(format!("非法图片引用：{image_ref}"));
    }
    let path = state.content_root.join(&image_ref);
    let bytes = fs::read(&path)
        .map_err(|error| format!("读 {} 失败：{}", path.display(), error))?;
    let mime = match path
        .extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.to_ascii_lowercase())
        .as_deref()
    {
        Some("png") => "image/png",
        Some("jpg" | "jpeg") => "image/jpeg",
        Some("gif") => "image/gif",
        Some("svg") => "image/svg+xml",
        Some("webp") => "image/webp",
        _ => return Err(format!("不支持的图片格式：{}", path.display())),
    };
    Ok(format!(
        "data:{mime};base64,{}",
        base64::engine::general_purpose::STANDARD.encode(bytes)
    ))
}

#[tauri::command]
fn record_attempt(
    state: State<AppState>,
    knowledge_id: String,
    item_id: String,
    correct: bool,
) -> Result<(), String> {
    let connection = rusqlite::Connection::open(&state.store_path)
        .map_err(|error| error.to_string())?;
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    connection
        .execute(
            "INSERT INTO attempts (knowledge_id, item_id, correct, answered_at) VALUES (?1, ?2, ?3, ?4)",
            rusqlite::params![knowledge_id, item_id, correct as i64, now],
        )
        .map_err(|error| error.to_string())?;
    Ok(())
}

/// 补正机制：按 item_id 列表清除作答记录（重置某章/节的测验与自评）。
#[tauri::command]
fn reset_attempts(state: State<AppState>, item_ids: Vec<String>) -> Result<(), String> {
    let connection = rusqlite::Connection::open(&state.store_path)
        .map_err(|error| error.to_string())?;
    for item_id in &item_ids {
        connection
            .execute("DELETE FROM attempts WHERE item_id = ?1", rusqlite::params![item_id])
            .map_err(|error| error.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn get_attempts(state: State<AppState>) -> Result<Vec<AttemptRow>, String> {
    if !state.store_path.exists() {
        return Ok(vec![]);
    }
    let connection = rusqlite::Connection::open(&state.store_path)
        .map_err(|error| error.to_string())?;
    let mut statement = connection
        .prepare("SELECT knowledge_id, item_id, correct, answered_at FROM attempts ORDER BY id")
        .map_err(|error| error.to_string())?;
    let rows = statement
        .query_map([], |row| {
            Ok(AttemptRow {
                knowledge_id: row.get(0)?,
                item_id: row.get(1)?,
                correct: row.get::<_, i64>(2)? != 0,
                answered_at: row.get(3)?,
            })
        })
        .map_err(|error| error.to_string())?;
    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|error| error.to_string())
}

/// 学习者自译：保存一段自己的译文；text 为空即删除该条。
#[tauri::command]
fn save_my_translation(state: State<AppState>, sha: String, text: String) -> Result<(), String> {
    let connection = rusqlite::Connection::open(&state.store_path)
        .map_err(|error| error.to_string())?;
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    if text.trim().is_empty() {
        connection
            .execute("DELETE FROM my_translations WHERE sha = ?1", rusqlite::params![sha])
            .map_err(|error| error.to_string())?;
    } else {
        connection
            .execute(
                "INSERT INTO my_translations (sha, text, updated_at) VALUES (?1, ?2, ?3)
                 ON CONFLICT(sha) DO UPDATE SET text = ?2, updated_at = ?3",
                rusqlite::params![sha, text, now],
            )
            .map_err(|error| error.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn get_my_translations(state: State<AppState>) -> Result<Vec<MyTranslationRow>, String> {
    if !state.store_path.exists() {
        return Ok(vec![]);
    }
    let connection = rusqlite::Connection::open(&state.store_path)
        .map_err(|error| error.to_string())?;
    let mut statement = connection
        .prepare("SELECT sha, text, updated_at FROM my_translations ORDER BY updated_at")
        .map_err(|error| error.to_string())?;
    let rows = statement
        .query_map([], |row| {
            Ok(MyTranslationRow {
                sha: row.get(0)?,
                text: row.get(1)?,
                updated_at: row.get(2)?,
            })
        })
        .map_err(|error| error.to_string())?;
    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|error| error.to_string())
}

#[tauri::command]
fn launch_demo(app: AppHandle, state: State<AppState>, demo_id: String) -> LaunchResult {
    let Ok(manifest) = read_content(&state.content_root, "demos.json") else {
        return LaunchResult { ok: false, message: "读 demos.json 失败".into() };
    };
    if find_entity(&manifest, &demo_id).is_none() {
        return LaunchResult { ok: false, message: format!("清单里没有 {}", demo_id) };
    }
    // build-native 在应用根（check.py 的 CMake 输出目录）。
    let app_root = state
        .content_root
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_default();
    let binary = demo_binary(&app_root, &demo_id);
    if !binary.is_file() {
        return LaunchResult {
            ok: false,
            message: format!(
                "演示尚未编译：{} 不存在。先运行 python3 scripts/check.py 完成编译。",
                binary.display()
            ),
        };
    }

    let mut child = match Command::new(&binary)
        .arg("--demo-id")
        .arg(&demo_id)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
    {
        Ok(child) => child,
        Err(error) => {
            return LaunchResult { ok: false, message: format!("启动失败：{}", error) };
        }
    };

    // initialize：协议握手（应用 ADR 0001 决策 5）。
    if let Some(stdin) = child.stdin.as_mut() {
        let request = json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": { "demo_id": demo_id, "protocol_version": 1 }
        });
        let _ = writeln!(stdin, "{}", request);
    }

    // 上行事件转发给前端：每行一个 JSON-RPC 消息（NDJSON）。
    if let Some(stdout) = child.stdout.take() {
        let emitter = app.clone();
        let demo_id = demo_id.clone();
        thread::spawn(move || {
            for line in BufReader::new(stdout).lines() {
                let Ok(line) = line else { break };
                let Ok(message) = serde_json::from_str::<Value>(&line) else { continue };
                let method = message.get("method").and_then(|v| v.as_str()).unwrap_or("");
                let params = message.get("params").cloned().unwrap_or(json!({}));
                let _ = emitter.emit(
                    "demo-event",
                    serde_json::json!({ "demo_id": demo_id, "method": method, "params": params }),
                );
            }
        });
    }

    state.demos.lock().unwrap().insert(demo_id.clone(), child);
    LaunchResult { ok: true, message: format!("{} 已启动", demo_id) }
}

#[tauri::command]
fn stop_demo(state: State<AppState>, demo_id: String) -> Result<(), String> {
    if let Some(mut child) = state.demos.lock().unwrap().remove(&demo_id) {
        if let Some(stdin) = child.stdin.as_mut() {
            let _ = writeln!(stdin, r#"{{"jsonrpc":"2.0","id":2,"method":"shutdown"}}"#);
        }
        thread::spawn(move || {
            thread::sleep(std::time::Duration::from_millis(500));
            let _ = child.kill();
        });
    }
    Ok(())
}

/// 编译并运行官方示例（应用 ADR 0006）：原样代码没有 JSON-RPC 协议，
/// 壳只负责拉起独立窗口——不握手、不转发、不进程托管（Child 随手丢弃，
/// 不会杀掉进程）；工作目录设在示例源目录（button 示例从工作目录读 info.xpm）。
#[tauri::command]
fn launch_example(state: State<AppState>, example_id: String) -> LaunchResult {
    let manifest = match read_content(&state.content_root, "demos.json") {
        Ok(manifest) => manifest,
        Err(_) => return LaunchResult { ok: false, message: "读 demos.json 失败".into() },
    };
    let Some(entity) = find_example(&manifest, &example_id) else {
        return LaunchResult { ok: false, message: format!("清单里没有官方示例 {example_id}") };
    };
    let Some(build_target) = entity.get("build_target").and_then(|v| v.as_str()) else {
        return LaunchResult { ok: false, message: format!("{example_id}: 缺 build_target") };
    };
    let app_root = state
        .content_root
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_default();
    let binary = match ensure_example_built(&app_root, build_target) {
        Ok(binary) => binary,
        Err(message) => return LaunchResult { ok: false, message },
    };
    let source_dir = app_root.join(entity.get("source_dir").and_then(|v| v.as_str()).unwrap_or(""));
    let spawned = native_env(
        Command::new(&binary)
            .current_dir(&source_dir)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null()),
    )
    .spawn();
    match spawned {
        Ok(_) => LaunchResult { ok: true, message: format!("{example_id} 已启动") },
        Err(error) => LaunchResult { ok: false, message: format!("启动失败：{error}") },
    }
}

/// 官方示例源码（页内「查看源码」）：返回示例目录下源文件的相对路径与文本。
/// 代码是教材本身，逐字返回、不加工（应用 ADR 0002、0006）。
#[tauri::command]
fn read_example_sources(state: State<AppState>, example_id: String) -> Result<Vec<SourceFile>, String> {
    let manifest = read_content(&state.content_root, "demos.json")?;
    let Some(entity) = find_example(&manifest, &example_id) else {
        return Err(format!("清单里没有官方示例 {example_id}"));
    };
    let rel_dir = entity.get("source_dir").and_then(|v| v.as_str()).unwrap_or("");
    let app_root = state
        .content_root
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_default();
    let dir = app_root.join(rel_dir);
    let mut files: Vec<SourceFile> = Vec::new();
    let entries =
        fs::read_dir(&dir).map_err(|error| format!("读 {} 失败：{}", dir.display(), error))?;
    for entry in entries.flatten() {
        let path = entry.path();
        let ext = path
            .extension()
            .and_then(|ext| ext.to_str())
            .map(|ext| ext.to_ascii_lowercase())
            .unwrap_or_default();
        if !matches!(ext.as_str(), "cc" | "h" | "xpm") || !path.is_file() {
            continue;
        }
        let content = fs::read_to_string(&path)
            .map_err(|error| format!("读 {} 失败：{}", path.display(), error))?;
        files.push(SourceFile {
            path: format!(
                "{}/{}",
                rel_dir,
                path.file_name().and_then(|name| name.to_str()).unwrap_or("?")
            ),
            content,
        });
    }
    files.sort_by(|a, b| a.path.cmp(&b.path));
    Ok(files)
}

// —— 官方示例的工作区副本（应用 ADR 0009）——
// exercise/ 是禁止修改的镜像；「真实工程项目」的查看、编辑、运行发生在
// workspace/<示例 id>/ 的学习者副本上（与 exp.* 骨架副本同一约定：重置 =
// 删掉重拷，构建产物不入库）。副本由壳生成：官方文件原样 + 独立 CMake 工程
// + 按当前平台写好的 VS Code 配置（tasks/launch/IntelliSense）。

/// 工程内参与编译的源文件（.xpm 是运行时资源，不进 add_executable）。
fn example_build_sources(dir: &Path) -> Result<Vec<String>, String> {
    let mut names: Vec<String> = Vec::new();
    for entry in fs::read_dir(dir).map_err(|error| format!("读 {} 失败：{}", dir.display(), error))? {
        let path = entry.map_err(|error| error.to_string())?.path();
        let ext = path
            .extension()
            .and_then(|ext| ext.to_str())
            .map(|ext| ext.to_ascii_lowercase());
        if path.is_file() && matches!(ext.as_deref(), Some("cc" | "h")) {
            names.push(path.file_name().unwrap_or_default().to_string_lossy().into_owned());
        }
    }
    names.sort();
    Ok(names)
}

fn generated_cmake_lists(project: &str, sources: &[String]) -> String {
    let list = sources
        .iter()
        .map(|name| format!("\n    {name}"))
        .collect::<String>();
    format!(
        "cmake_minimum_required(VERSION 3.21)\n\
         project({project} CXX)\n\n\
         # 官方示例的学习者副本（应用 ADR 0009）：源文件来自 exercise/ 镜像原样，\n\
         # 本文件由壳生成——改坏了删掉副本目录，在课程里重新点「打开工作区」即可。\n\
         set(CMAKE_CXX_STANDARD 17)\n\
         set(CMAKE_CXX_STANDARD_REQUIRED ON)\n\n\
         find_package(PkgConfig REQUIRED)\n\
         pkg_check_modules(GTKMM4 REQUIRED IMPORTED_TARGET gtkmm-4.0)\n\n\
         set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${{CMAKE_BINARY_DIR}})\n\n\
         add_executable({project}{list})\n\
         target_link_libraries({project} PRIVATE PkgConfig::GTKMM4)\n"
    )
}

/// MSYS2 的 bin 目录（正斜杠，写进 JSON 配置：PATH 前缀、编译器与 gdb 的
/// 可执行路径都指这里——PATH 若指到 mingw64 根会漏掉全部 exe，cmake 会
/// 落到系统里别的 pkg-config，比如 GNU Octave 自带的那份）。非 Windows 返回 None。
fn msys2_bin_forward() -> Option<String> {
    msys2_mingw64().map(|dir| dir.join("bin").to_string_lossy().replace('\\', "/"))
}

fn vscode_tasks_json(target: &str, run_binary: &str) -> String {
    // Windows 需要 MSYS2 前缀（cmake 找 ninja/gcc、产物找 GTK DLL）；macOS/Linux
    // 的 pkg-config 与运行时走系统路径，不需要 env 覆盖。副本是本机个人区，
    // 按当前平台生成即可。
    let windows = cfg!(windows);
    let Some(msys) = msys2_bin_forward().filter(|_| windows) else {
        return serde_json::json!({
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "configure", "type": "shell", "command": "cmake",
                    "args": ["-G", "Ninja", "-S", ".", "-B", "build"],
                    "problemMatcher": []
                },
                {
                    "label": "build", "type": "shell", "command": "cmake",
                    "args": ["--build", "build"],
                    "group": { "kind": "build", "isDefault": true },
                    "dependsOn": "configure",
                    "problemMatcher": ["$gcc"]
                },
                {
                    "label": "run", "type": "shell",
                    "command": format!("./build/{run_binary}"),
                    "options": { "cwd": "${workspaceFolder}" },
                    "dependsOn": "build",
                    "problemMatcher": []
                }
            ]
        })
        .to_string();
    };
    let env_options = serde_json::json!({
        "env": {
            "PATH": format!("{msys};${{env:PATH}}"),
            "PKG_CONFIG_PATH": format!("{msys}/../lib/pkgconfig"),
        }
    });
    serde_json::json!({
        "version": "2.0.0",
        "tasks": [
            {
                "label": "configure", "type": "shell", "command": "cmake",
                "args": ["-G", "Ninja", "-S", ".", "-B", "build"],
                "options": env_options,
                "problemMatcher": []
            },
            {
                "label": "build", "type": "shell", "command": "cmake",
                "args": ["--build", "build"],
                "options": env_options,
                "group": { "kind": "build", "isDefault": true },
                "dependsOn": "configure",
                "problemMatcher": ["$gcc"]
            },
            {
                "label": "run", "type": "shell",
                "command": format!("./build/{run_binary}"),
                "options": {
                    "cwd": "${workspaceFolder}",
                    "env": { "PATH": format!("{msys};${{env:PATH}}") }
                },
                "dependsOn": "build",
                "problemMatcher": []
            }
        ]
    })
    .to_string()
}

fn vscode_launch_json(run_binary: &str) -> String {
    let windows = cfg!(windows);
    let program = if windows {
        format!("${{workspaceFolder}}/build/{run_binary}.exe")
    } else {
        format!("${{workspaceFolder}}/build/{run_binary}")
    };
    // 双调试配置：学习者装了哪个调试扩展就能用哪个——cppdbg 走
    // ms-vscode.cpptools（Windows 用 MSYS2 gdb），lldb 走 vadimcn.vscode-lldb
    // （CodeLLDB，VS Code 对 C++ 的常见自动生成模板即它的格式）。
    // 两个都以「build」任务为先，PATH 都前置 MSYS2（GTK 的运行时 DLL）。
    let mut cppdbg = serde_json::json!({
        "name": "调试（C/C++ 扩展）",
        "type": "cppdbg",
        "request": "launch",
        "program": program,
        "cwd": "${workspaceFolder}",
        "preLaunchTask": "build",
    });
    let mut lldb = serde_json::json!({
        "name": "调试（CodeLLDB 扩展）",
        "type": "lldb",
        "request": "launch",
        "program": program,
        "cwd": "${workspaceFolder}",
        "preLaunchTask": "build",
    });
    if windows {
        let msys = msys2_bin_forward().unwrap_or_else(|| "C:/msys64/mingw64".into());
        cppdbg["MIMode"] = "gdb".into();
        cppdbg["miDebuggerPath"] = format!("{msys}/gdb.exe").into();
        cppdbg["environment"] = serde_json::json!([
            { "name": "PATH", "value": format!("{msys};${{env:PATH}}") }
        ]);
        lldb["env"] = serde_json::json!({ "PATH": format!("{msys};${{env:PATH}}") });
    }
    serde_json::json!({
        "version": "0.2.0",
        "configurations": [cppdbg, lldb]
    })
    .to_string()
}

fn vscode_intellisense_json() -> String {
    let mut config = serde_json::json!({
        "name": "gtkmm",
        "includePath": ["${workspaceFolder}/**"],
        "cStandard": "c17",
        "cppStandard": "c++17",
    });
    if let Some(msys) = msys2_bin_forward().filter(|_| cfg!(windows)) {
        config["compilerPath"] = format!("{msys}/g++.exe").into();
    }
    serde_json::json!({ "version": 4, "configurations": [config] }).to_string()
}

fn workspace_readme(example_id: &str, source_dir: &str, target: &str) -> String {
    format!(
        "# {example_id} — 官方示例的学习者副本\n\n\
        来自 `exercise/{source_dir}`（官方 `examples/book/` 的逐字镜像，版本随\n\
        `upstream.json` 钉点）；`CMakeLists.txt` 与 `.vscode/` 由课程壳生成。\n\
        这里是学习者的地盘，随便改；想回到官方原样，删掉整个目录后在课程里\n\
        重新点「打开工作区」。\n\n\
        ## 构建与运行\n\n\
        命令行（Windows 在 MSYS2 MINGW64 Shell 里；macOS/Linux 直接用）：\n\n\
        ```sh\n\
        cmake -G Ninja -S . -B build\n\
        cmake --build build\n\
        ./build/{target}\n\
        ```\n\n\
        VS Code：`Ctrl+Shift+B` 构建默认任务；任务「run」构建并运行（窗口从\n\
        本目录启动——button 示例从工作目录读 `info.xpm`）。「调试官方示例」\n\
        （F5）需要 C/C++ 扩展（ms-vscode.cpptools），未装也能用任务构建运行。\n"
    )
}

/// 生成（或复用）工作区副本，返回副本目录。
///
/// 源文件只在首次（CMakeLists 缺失 = 副本未初始化）从镜像复制，之后不动——
/// 那是学习者改代码的地方；`.vscode/` 三件与 README 是壳的生成物，**缺失
/// 即补**（已有则不动，尊重对配置本身的修改）。半成品副本（如手工建的、
/// 只带 VS Code 自动生成坏模板的）点一次「打开工作区」即被补全。
fn materialize_workspace(app_root: &Path, entity: &Value) -> Result<PathBuf, String> {
    let example_id = entity.get("id").and_then(|v| v.as_str()).unwrap_or("");
    let source_rel = entity
        .get("source_dir")
        .and_then(|v| v.as_str())
        .ok_or_else(|| format!("{example_id}: 缺 source_dir"))?;
    let target = entity
        .get("build_target")
        .and_then(|v| v.as_str())
        .ok_or_else(|| format!("{example_id}: 缺 build_target"))?;
    let source_dir = app_root.join(source_rel);
    let workspace_dir = app_root.join("workspace").join(example_id.replace('.', "-"));

    if !workspace_dir.join("CMakeLists.txt").is_file() {
        fs::create_dir_all(&workspace_dir)
            .map_err(|error| format!("建 {} 失败：{}", workspace_dir.display(), error))?;
        // 官方源文件原样复制（镜像 → 副本，一层目录，无子目录）
        for entry in
            fs::read_dir(&source_dir).map_err(|error| format!("读 {} 失败：{}", source_dir.display(), error))?
        {
            let from = entry.map_err(|error| error.to_string())?.path();
            if from.is_file() {
                let to = workspace_dir.join(from.file_name().unwrap_or_default());
                fs::copy(&from, &to).map_err(|error| {
                    format!("复制 {} 失败：{}", from.display(), error)
                })?;
            }
        }
        let sources = example_build_sources(&workspace_dir)?;
        if sources.is_empty() {
            return Err(format!("{source_rel}: 镜像目录里没有可编译的源文件"));
        }
        fs::write(
            workspace_dir.join("CMakeLists.txt"),
            generated_cmake_lists(target, &sources),
        )
        .map_err(|error| error.to_string())?;
    }
    ensure_generated_file(
        &workspace_dir,
        ".vscode",
        "tasks.json",
        &vscode_tasks_json(target, target),
    )?;
    ensure_generated_file(
        &workspace_dir,
        ".vscode",
        "launch.json",
        &vscode_launch_json(target),
    )?;
    ensure_generated_file(
        &workspace_dir,
        ".vscode",
        "c_cpp_properties.json",
        &vscode_intellisense_json(),
    )?;
    ensure_generated_file(
        &workspace_dir,
        "",
        "README.md",
        &workspace_readme(example_id, source_rel, target),
    )?;
    Ok(workspace_dir)
}

/// 副本里壳生成物的落盘：子目录不存在先建；文件已存在则不动。
fn ensure_generated_file(
    workspace_dir: &Path,
    subdir: &str,
    name: &str,
    content: &str,
) -> Result<(), String> {
    let dir = if subdir.is_empty() {
        workspace_dir.to_path_buf()
    } else {
        workspace_dir.join(subdir)
    };
    fs::create_dir_all(&dir).map_err(|error| error.to_string())?;
    let path = dir.join(name);
    if !path.is_file() {
        fs::write(&path, content).map_err(|error| {
            format!("写 {} 失败：{}", path.display(), error)
        })?;
    }
    Ok(())
}

/// 找 VS Code 的启动入口：PATH 里的 `code`，或 Windows 常见安装位置的 code.cmd。
fn find_vscode() -> Option<PathBuf> {
    if let Some(path_var) = std::env::var_os("PATH") {
        let exe_names: &[&str] = if cfg!(windows) {
            &["code.cmd", "code"]
        } else {
            &["code"]
        };
        for dir in std::env::split_paths(&path_var) {
            for name in exe_names {
                let candidate = dir.join(name);
                if candidate.is_file() {
                    return Some(candidate);
                }
            }
        }
    }
    if cfg!(windows) {
        let mut roots = vec![std::env::var_os("LOCALAPPDATA").map(PathBuf::from)];
        roots.push(Some(PathBuf::from("C:/Program Files")));
        roots.push(Some(PathBuf::from("C:/Program Files (x86)")));
        for root in roots.into_iter().flatten() {
            let candidate = root
                .join("Programs")
                .join("Microsoft VS Code")
                .join("bin")
                .join("code.cmd");
            if candidate.is_file() {
                return Some(candidate);
            }
            let system = root.join("Microsoft VS Code").join("bin").join("code.cmd");
            if system.is_file() {
                return Some(system);
            }
        }
    }
    if cfg!(target_os = "macos") {
        let candidate = PathBuf::from(
            "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
        );
        if candidate.is_file() {
            return Some(candidate);
        }
    }
    None
}

/// 打开官方示例的工作区副本（VS Code）：副本不存在时从 exercise/ 镜像生成
/// （源文件原样 + 独立 CMake 工程 + 本机配套的 VS Code 配置）；已存在则直接
/// 打开，不覆盖个人改动。绑定 VS Code 探测失败时给具体指引。
#[tauri::command]
fn open_example_workspace(state: State<AppState>, example_id: String) -> LaunchResult {
    let manifest = match read_content(&state.content_root, "demos.json") {
        Ok(manifest) => manifest,
        Err(_) => return LaunchResult { ok: false, message: "读 demos.json 失败".into() },
    };
    let Some(entity) = find_example(&manifest, &example_id) else {
        return LaunchResult { ok: false, message: format!("清单里没有官方示例 {example_id}") };
    };
    let app_root = state
        .content_root
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_default();
    // 副本已存在时 materialize_workspace 原样返回，不覆盖个人改动（重置 =
    // 删掉副本目录后在课程里重新点「打开工作区」，与 exp.* 骨架副本同约定）
    let workspace_dir = match materialize_workspace(&app_root, &entity) {
        Ok(dir) => dir,
        Err(message) => return LaunchResult { ok: false, message },
    };

    let Some(code) = find_vscode() else {
        return LaunchResult {
            ok: false,
            message: format!(
                "副本已生成在 {}，但找不到 VS Code——请安装并勾选「添加到 PATH」\
                 （或把 code 命令放进 PATH）后重试。",
                workspace_dir.display()
            ),
        };
    };

    let mut command = if cfg!(windows) {
        let mut command = Command::new("cmd");
        command.arg("/C").arg(&code);
        command
    } else {
        Command::new(&code)
    };
    command.arg(&workspace_dir).stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null());
    match command.spawn() {
        Ok(_) => LaunchResult {
            ok: true,
            message: format!("{} 已在 VS Code 打开（工作区副本）", example_id),
        },
        Err(error) => LaunchResult { ok: false, message: format!("启动 VS Code 失败：{error}") },
    }
}

pub fn run() {
    let content_root = content_root();
    let store = store_path();
    let state = AppState {
        content_root: content_root.clone(),
        store_path: store.clone(),
        demos: Mutex::new(HashMap::new()),
    };
    let _ = init_store(&store);

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(state)
        .invoke_handler(tauri::generate_handler![
            get_curriculum,
            get_manifest,
            get_page_content,
            get_po_units,
            get_figure,
            get_vocab,
            record_attempt,
            reset_attempts,
            get_attempts,
            save_my_translation,
            get_my_translations,
            launch_demo,
            stop_demo,
            launch_example,
            read_example_sources,
            open_example_workspace
        ])
        .run(tauri::generate_context!())
        .expect("error while running athena-gtkmm");
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::Value;

    #[test]
    fn content_ids_reject_path_tricks() {
        for ok in ["chapter-basics", "sec-gtkmm", "changes-gtkmm4", "a.b_c-1"] {
            assert!(is_safe_id(ok), "{ok} 应当合法");
        }
        for bad in ["", "..", "../x", "a/b", "a\\b", "/etc/passwd", "C:x", "a..b", "x y"] {
            assert!(!is_safe_id(bad), "{bad} 应当被拒绝");
        }
        assert!(!is_safe_id(&"a".repeat(129)), "过长的 id 应当被拒绝");
    }

    /// 在临时根里摆一个假镜像目录 + 实体，生成副本并验证内容。
    /// 只测生成逻辑本身；MSYS2 探测结果因机器而异，配置只断言「合法 JSON +
    /// 关键结构」，不断言平台相关字段。
    #[test]
    fn workspace_copy_is_complete_and_configs_parse() {
        let root = std::env::temp_dir().join(format!(
            "athena-gtkmm-test-{}",
            SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()
        ));
        let source_dir = root.join("exercise/buttons/button");
        fs::create_dir_all(&source_dir).unwrap();
        fs::write(source_dir.join("buttons.h"), "#pragma once\n").unwrap();
        fs::write(source_dir.join("buttons.cc"), "#include \"buttons.h\"\n").unwrap();
        fs::write(source_dir.join("main.cc"), "int main() { return 0; }\n").unwrap();
        fs::write(source_dir.join("info.xpm"), "/* xpm */\n").unwrap();

        let entity = serde_json::json!({
            "id": "example.buttons.button",
            "source_dir": "exercise/buttons/button",
            "build_target": "example-buttons-button",
        });
        let workspace_dir =
            materialize_workspace(&root, &entity).expect("materialize_workspace 失败");
        assert_eq!(
            workspace_dir,
            root.join("workspace").join("example-buttons-button")
        );

        // 源文件（含 xpm 资源）逐个复制到位
        for name in ["buttons.h", "buttons.cc", "main.cc", "info.xpm"] {
            assert!(workspace_dir.join(name).is_file(), "缺 {name}");
        }
        // CMakeLists：target 与参与编译的源文件都在，xpm 不进编译清单
        let cmake = fs::read_to_string(workspace_dir.join("CMakeLists.txt")).unwrap();
        assert!(cmake.contains("project(example-buttons-button CXX)"));
        assert!(cmake.contains("add_executable(example-buttons-button"));
        for name in ["buttons.cc", "buttons.h", "main.cc"] {
            assert!(cmake.contains(name), "CMakeLists 缺 {name}");
        }
        assert!(!cmake.contains("info.xpm"), "xpm 不应进 add_executable");

        // .vscode 三件：合法 JSON + 任务齐全 + 调试配置指向产物
        let tasks: Value = serde_json::from_str(
            &fs::read_to_string(workspace_dir.join(".vscode/tasks.json")).unwrap(),
        )
        .unwrap();
        let labels: Vec<&str> = tasks["tasks"]
            .as_array()
            .unwrap()
            .iter()
            .map(|t| t["label"].as_str().unwrap())
            .collect();
        assert_eq!(labels, ["configure", "build", "run"]);
        assert!(tasks["tasks"][1]["group"]["isDefault"] == true);
        assert!(tasks["tasks"][2]["command"]
            .as_str()
            .unwrap()
            .contains("example-buttons-button"));

        let launch: Value = serde_json::from_str(
            &fs::read_to_string(workspace_dir.join(".vscode/launch.json")).unwrap(),
        )
        .unwrap();
        let configs = launch["configurations"].as_array().unwrap();
        assert_eq!(configs.len(), 2, "应有 cppdbg 与 CodeLLDB 两个调试配置");
        for config in configs {
            assert!(config["program"].as_str().unwrap().contains("example-buttons-button"));
            assert_eq!(config["preLaunchTask"], "build");
        }
        assert_eq!(configs[0]["type"], "cppdbg");
        assert_eq!(configs[1]["type"], "lldb");

        serde_json::from_str::<Value>(
            &fs::read_to_string(workspace_dir.join(".vscode/c_cpp_properties.json")).unwrap(),
        )
        .expect("c_cpp_properties.json 不是合法 JSON");

        assert!(workspace_dir.join("README.md").is_file());

        fs::remove_dir_all(&root).unwrap();
    }
}
