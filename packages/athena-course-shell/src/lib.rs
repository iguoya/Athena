//! Athena 课程应用共用的壳（ADR 0161）：内容路径、进度库、C++ 即时编译运行。
//!
//! 数据结构、算法、408、组成原理、Linux、设计模式六个应用的 Tauri 壳原本是各抄一份的同一个
//! 模板，逐份之间只差应用名、环境变量名、数据目录名这几个字符串；抄出来的 bug 要修六遍，
//! 漏一遍就是潜伏的不一致。这里收成一份，各应用只传一份 [`ShellConfig`] 和自己的
//! `tauri::generate_context!()`（它读的是应用自己的 `tauri.conf.json` 与前端产物，必须在
//! 应用 crate 里展开）。
//!
//! 不依赖主程序头文件或 `athena.json`；与其他应用没有任何运行时耦合（ADR 0032、0062）。
//! 前端调用的命令名与参数不变，所以前端无须改动。

mod archive;
mod compiler;
pub mod store;

use serde::Serialize;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

/// 每个应用自己的那几个字符串。其余一切行为在所有应用里相同。
#[derive(Clone, Copy)]
pub struct ShellConfig {
    /// 进程名与二进制名，如 `athena-data-structures`；也用作临时目录前缀。
    pub binary: &'static str,
    /// 给人看的课程名，经 `get_app_info` 交给前端。
    pub title: &'static str,
    /// 强制指定应用根目录（含 `content/`）的环境变量，如 `ATHENA_DATA_STRUCTURES_ROOT`。
    pub root_env: &'static str,
    /// 用户数据目录下的进度库目录名，如 `AthenaDataStructures`。
    /// 必须与该应用 `app.json` 的 `progress.dir` 一致，启动器据此找库同步（ADR 0155）。
    pub data_dir: &'static str,
    /// 应用 crate 的版本，传 `env!("CARGO_PKG_VERSION")`——本 crate 自己的版本不是应用的版本。
    pub version: &'static str,
    /// 应用 crate 的 `env!("CARGO_MANIFEST_DIR")`：开发时 `src-tauri` 的上一级就是应用根。
    pub manifest_dir: &'static str,
}

struct AppState {
    content_root: PathBuf,
    /// 本应用自己的进度库：自建、自迁移，不依赖主程序是否跑过（ADR 0037）。
    store_path: PathBuf,
    title: &'static str,
    binary: &'static str,
}

type State<'a> = tauri::State<'a, Mutex<AppState>>;

#[derive(Clone, Serialize)]
struct AppInfo {
    title: String,
    content_root: String,
    store_path: String,
    compiler: String,
}

#[derive(Serialize)]
struct RunResult {
    ok: bool,
    compile_log: String,
    stdout: String,
    stderr: String,
    duration_ms: u128,
}

fn content_root(config: &ShellConfig) -> PathBuf {
    if let Ok(root) = std::env::var(config.root_env) {
        return PathBuf::from(root);
    }

    // 先按实际可执行文件找，避免发行包错误依赖编译机上由
    // CARGO_MANIFEST_DIR 烙进去的绝对源码路径。
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            let roots = [
                dir.to_path_buf(),
                dir.join(".."),
                // macOS .app：Tauri 把 ../content 打包到 Resources/_up_/content。
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

    // 开发：src-tauri 的上一级就是应用根。
    let dev = PathBuf::from(config.manifest_dir).join("..");
    dev.canonicalize().unwrap_or(dev)
}

fn own_store_path(config: &ShellConfig) -> PathBuf {
    // 进度库放用户数据目录，不进仓库（ADR 0155）：启动器的同步代理在能连上路由器时
    // 把它与中心库互推。目录名登记在 app.json 的 progress.dir，两处必须一致。
    let base = dirs_next::data_dir().unwrap_or_else(|| PathBuf::from("."));
    let dir = base.join(config.data_dir);
    let _ = fs::create_dir_all(&dir);
    dir.join("learning.db")
}

fn parse_cli(config: &ShellConfig) {
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            // 进度库不再共享（ADR 0037）。老版本主程序仍会传这个参数，
            // 为它退出会让用户只看到"点了没反应"，所以吃掉并记一行。
            "--store" => {
                let ignored = args.next().unwrap_or_default();
                eprintln!("已忽略 --store {ignored}：本应用使用自己的进度库");
            }
            "--help" | "-h" => {
                eprintln!(
                    "用法：{}\n\n\
                     进度写入本应用自己的库，完全独立运行。\n\
                     --store <路径> 仅为兼容旧版主程序而接受，会被忽略。",
                    config.binary
                );
                std::process::exit(0);
            }
            "--version" => {
                println!("{} {}", config.binary, config.version);
                std::process::exit(0);
            }
            other => {
                eprintln!("无法识别的参数：{other}");
                std::process::exit(2);
            }
        }
    }
}

/// 前端传来的案例 id 与入口文件名是单段名字：只含字母、数字和 `._-`，不是 `.` / `..`。
/// 它们直接拼进 `content/cases/` 下的路径，而 `save_case_source` 是**写**文件——
/// 不校验，`entrypoint` 传 `../../..` 就能写到任何地方。
fn is_plain_segment(raw: &str) -> bool {
    !raw.is_empty()
        && raw != "."
        && raw != ".."
        && raw
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-' || c == '.')
}

fn case_path(root: &Path, case_id: &str, entrypoint: &str) -> Result<PathBuf, String> {
    if !is_plain_segment(case_id) || !is_plain_segment(entrypoint) {
        return Err(format!("非法案例引用：{case_id}/{entrypoint}"));
    }
    Ok(root.join("content/cases").join(case_id).join(entrypoint))
}

/// 把任意字符串收成可做路径一段的名字（用于临时目录，不是校验）。
fn safe_path_segment(raw: &str) -> String {
    let s: String = raw
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || c == '_' || c == '-' || c == '.' {
                c
            } else {
                '_'
            }
        })
        .collect();
    if s.is_empty() || s == "." || s == ".." {
        "_".into()
    } else {
        s
    }
}

fn detect_clang_format() -> String {
    for cand in ["clang-format", "clang-format-18", "clang-format-16", "clang-format-15"] {
        if Command::new(cand)
            .arg("--version")
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false)
        {
            return cand.to_string();
        }
    }
    String::new()
}

fn millis_now() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis()
}

fn store_path_of(state: &State<'_>) -> PathBuf {
    state.lock().unwrap().store_path.clone()
}

/// 交给 clang-format 排版。没装它就报错说清楚装什么——不自己实现一个劣化版
/// 缩进器顶替（主仓库 AGENTS.md 的基线：使用者是开发者，工具视为已装）。
#[tauri::command]
fn format_cpp(state: State<'_>, source: String) -> Result<String, String> {
    let tool = detect_clang_format();
    if tool.is_empty() {
        return Err(if cfg!(windows) {
            "没找到 clang-format。装 LLVM，或 MSYS2 后 \
             pacman -S mingw-w64-ucrt-x86_64-clang-tools-extra。"
        } else if cfg!(target_os = "macos") {
            "没找到 clang-format。brew install clang-format"
        } else {
            "没找到 clang-format。apt install clang-format 或 dnf install clang-tools-extra。"
        }
        .to_string());
    }
    let binary = state.lock().unwrap().binary;
    let work = std::env::temp_dir().join(format!("{binary}-fmt-{}", millis_now()));
    fs::create_dir_all(&work).map_err(|e| e.to_string())?;
    let src = work.join("main.cpp");
    fs::write(&src, &source).map_err(|e| format!("写入待格式化源码失败：{e}"))?;
    let out = Command::new(&tool)
        .args([
            "-style={BasedOnStyle: LLVM, IndentWidth: 4, UseTab: Never, ColumnLimit: 100}",
            src.to_str().unwrap_or(""),
        ])
        .output();
    let _ = fs::remove_dir_all(&work);
    match out {
        Ok(o) if o.status.success() => {
            let formatted = String::from_utf8_lossy(&o.stdout).to_string();
            if formatted.trim().is_empty() {
                Ok(source)
            } else {
                Ok(formatted)
            }
        }
        _ => Ok(source),
    }
}

#[tauri::command]
fn get_app_info(state: State<'_>) -> AppInfo {
    let s = state.lock().unwrap();
    AppInfo {
        title: s.title.into(),
        content_root: s.content_root.display().to_string(),
        store_path: s.store_path.display().to_string(),
        compiler: compiler::detect().map(|c| c.label()).unwrap_or_default(),
    }
}

#[tauri::command]
fn load_curriculum(state: State<'_>) -> Result<serde_json::Value, String> {
    let s = state.lock().unwrap();
    let path = s.content_root.join("content/curriculum.json");
    let text =
        fs::read_to_string(&path).map_err(|e| format!("无法读取课表 {}: {e}", path.display()))?;
    let mut curriculum: serde_json::Value = serde_json::from_str(&text).map_err(|e| e.to_string())?;
    // 历史归档章节（ADR 0176）独立成 `content/archive.json`，启动时接在课表末尾：
    // 搬运旧仓库的条目很多，放进主课表会让 diff 和合并冲突都落在那份巨大的文件上，
    // 而且使用者日后要整体审视去留——删掉这一个文件，归档就整体消失，主课表毫发无损。
    let archive_path = s.content_root.join("content/archive.json");
    if archive_path.is_file() {
        let atext = fs::read_to_string(&archive_path)
            .map_err(|e| format!("无法读取归档 {}: {e}", archive_path.display()))?;
        let archive: serde_json::Value =
            serde_json::from_str(&atext).map_err(|e| format!("archive.json 格式错误：{e}"))?;
        merge_archive(&mut curriculum, archive)?;
    }
    Ok(curriculum)
}

/// 把 `archive.json` 里的 `chapters` 追加到课表 `chapters` 末尾；它若带 `tracks` 也一并并入
/// （归档章节用自己的轨道色，不占用主课表的轨道）。
fn merge_archive(curriculum: &mut serde_json::Value, archive: serde_json::Value) -> Result<(), String> {
    let extra = match archive.get("chapters") {
        Some(serde_json::Value::Array(a)) => a.clone(),
        _ => return Err("archive.json 缺少 chapters 数组".into()),
    };
    let extra_tracks = match archive.get("tracks") {
        Some(serde_json::Value::Array(a)) => a.clone(),
        _ => Vec::new(),
    };
    match curriculum.get_mut("chapters") {
        Some(serde_json::Value::Array(chs)) => chs.extend(extra),
        _ => return Err("课表缺少 chapters 数组".into()),
    }
    if !extra_tracks.is_empty() {
        if let Some(serde_json::Value::Array(ts)) = curriculum.get_mut("tracks") {
            ts.extend(extra_tracks);
        }
    }
    Ok(())
}

#[tauri::command]
fn load_case_source(state: State<'_>, case_id: String, entrypoint: String) -> Result<String, String> {
    let root = state.lock().unwrap().content_root.clone();
    let path = case_path(&root, &case_id, &entrypoint)?;
    fs::read_to_string(&path).map_err(|e| format!("{}: {e}", path.display()))
}

#[tauri::command]
fn save_case_source(
    state: State<'_>,
    case_id: String,
    entrypoint: String,
    source: String,
) -> Result<(), String> {
    let root = state.lock().unwrap().content_root.clone();
    let path = case_path(&root, &case_id, &entrypoint)?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    fs::write(&path, source).map_err(|e| e.to_string())
}

#[tauri::command]
fn compile_and_run(
    state: State<'_>,
    case_id: String,
    entrypoint: String,
    source: String,
) -> Result<RunResult, String> {
    // 用编辑器里的源码写到临时目录再编译，不要回写 content/cases/：
    // 开发时 Vite 会监视那些文件，一保存就整页刷新，看起来像「运行完跳回主页」。
    let compiler = compiler::detect().ok_or_else(|| compiler::install_hint().to_string())?;

    let case_seg = safe_path_segment(&case_id);
    let entry_seg = safe_path_segment(&entrypoint);
    let (binary, content_root) = {
        let s = state.lock().unwrap();
        (s.binary, s.content_root.clone())
    };
    let work = std::env::temp_dir().join(format!("{binary}-{case_seg}-{}", millis_now()));
    fs::create_dir_all(&work).map_err(|e| e.to_string())?;
    let src = work.join(&entry_seg);
    fs::write(&src, source).map_err(|e| format!("写入临时源码失败：{e}"))?;
    let obj = work.join(compiler.artifact_name());

    let started = SystemTime::now();
    // 案例共享头（如 algorithm_trace.hpp）放 content/cases/_shared；挂上 include
    // 路径后案例 `#include "algorithm_trace.hpp"` 即可用（ADR 0004）。
    let shared = content_root.join("content/cases/_shared");
    let include = shared.is_dir().then_some(shared.as_path());
    let compile = compiler
        .compile_command(&src, &obj, include)
        .output()
        .map_err(|e| format!("启动 {} 失败：{e}", compiler.label()))?;

    let mut compile_log = String::new();
    compile_log.push_str(&String::from_utf8_lossy(&compile.stderr));
    compile_log.push_str(&String::from_utf8_lossy(&compile.stdout));

    if !compile.status.success() {
        let _ = fs::remove_dir_all(&work);
        return Ok(RunResult {
            ok: false,
            compile_log,
            stdout: String::new(),
            stderr: String::new(),
            duration_ms: started.elapsed().unwrap_or_default().as_millis(),
        });
    }

    let run = Command::new(&obj)
        .current_dir(&work)
        .output()
        .map_err(|e| format!("运行失败：{e}"))?;
    let _ = fs::remove_dir_all(&work);

    let mut stdout = String::from_utf8_lossy(&run.stdout).to_string();
    let mut stderr = String::from_utf8_lossy(&run.stderr).to_string();
    // 限制输出体积，避免前端卡死
    const LIMIT: usize = 200_000;
    if stdout.len() > LIMIT {
        stdout.truncate(LIMIT);
        stdout.push_str("\n…（输出已截断）\n");
    }
    if stderr.len() > LIMIT {
        stderr.truncate(LIMIT);
        stderr.push_str("\n…（输出已截断）\n");
    }

    Ok(RunResult {
        ok: run.status.success(),
        compile_log,
        stdout,
        stderr,
        duration_ms: started.elapsed().unwrap_or_default().as_millis(),
    })
}

/// 历史归档案例（ADR 0176）：案例目录名必须以 `arc_` 开头，与课程实验的案例分开命名空间，
/// 免得归档的只读代码被当成可保存的实验。
fn archive_case_dir(root: &Path, case_id: &str) -> Result<PathBuf, String> {
    if !is_plain_segment(case_id) || !case_id.starts_with("arc_") {
        return Err(format!("非法归档案例：{case_id}"));
    }
    Ok(root.join("content/cases").join(case_id))
}

/// 读出归档案例的全部文本文件，前端用它画多文件代码视图与批注。
#[tauri::command]
fn load_case_files(state: State<'_>, case_id: String) -> Result<Vec<archive::CaseFile>, String> {
    let root = state.lock().unwrap().content_root.clone();
    let dir = archive_case_dir(&root, &case_id)?;
    if !dir.is_dir() {
        return Err(format!("找不到归档案例 {case_id}"));
    }
    Ok(archive::list_case_files(&dir))
}

/// 编译并运行归档案例的指定源文件（多文件、带超时、只读）。
#[tauri::command]
fn run_archive_case(
    state: State<'_>,
    case_id: String,
    sources: Vec<String>,
    std: Option<String>,
    stdin: Option<String>,
) -> Result<archive::ArchiveRun, String> {
    let (binary, root) = {
        let s = state.lock().unwrap();
        (s.binary, s.content_root.clone())
    };
    let dir = archive_case_dir(&root, &case_id)?;
    if sources.is_empty() || sources.len() > 64 {
        return Err("编译清单为空或过长".into());
    }
    if let Some(bad) = sources.iter().find(|s| !archive::is_safe_rel_path(s, is_plain_segment)) {
        return Err(format!("非法源文件路径：{bad}"));
    }
    let work = std::env::temp_dir().join(format!("{binary}-{}-{}", safe_path_segment(&case_id), millis_now()));
    let shared = root.join("content/cases/_shared");
    let include = shared.is_dir().then_some(shared.as_path());
    archive::run_case(&dir, &work, &sources, std.as_deref(), stdin.as_deref(), include, archive::RUN_TIMEOUT)
}

#[tauri::command]
fn load_mastery(state: State<'_>, topic_id: String) -> Result<i32, String> {
    store::load_mastery(&store_path_of(&state), &topic_id)
}

#[tauri::command]
fn save_mastery(state: State<'_>, topic_id: String, mastery: i32) -> Result<(), String> {
    store::save_mastery(&store_path_of(&state), &topic_id, mastery)
}

#[tauri::command]
fn load_all_mastery(state: State<'_>) -> Result<std::collections::HashMap<String, i32>, String> {
    store::load_all_mastery(&store_path_of(&state))
}

#[tauri::command]
fn save_lab_status(state: State<'_>, lab_key: String, status: String) -> Result<(), String> {
    store::save_lab_status(&store_path_of(&state), &lab_key, &status)
}

#[tauri::command]
fn load_all_lab_status(
    state: State<'_>,
) -> Result<std::collections::HashMap<String, String>, String> {
    store::load_all_lab_status(&store_path_of(&state))
}

#[tauri::command]
fn save_lab_draft(state: State<'_>, lab_key: String, source: String) -> Result<(), String> {
    store::save_lab_draft(&store_path_of(&state), &lab_key, &source)
}

#[tauri::command]
fn load_all_lab_drafts(
    state: State<'_>,
) -> Result<std::collections::HashMap<String, String>, String> {
    store::load_all_lab_drafts(&store_path_of(&state))
}

#[tauri::command]
fn clear_lab_draft(state: State<'_>, lab_key: String) -> Result<(), String> {
    store::clear_lab_draft(&store_path_of(&state), &lab_key)
}

#[tauri::command]
fn save_quiz_picks(state: State<'_>, quiz_key: String, picks: String) -> Result<(), String> {
    store::save_quiz_picks(&store_path_of(&state), &quiz_key, &picks)
}

#[tauri::command]
fn load_all_quiz_picks(
    state: State<'_>,
) -> Result<std::collections::HashMap<String, String>, String> {
    store::load_all_quiz_picks(&store_path_of(&state))
}

/// 应用入口：解析命令行、备好进度库、起窗口。`context` 必须是应用自己的
/// `tauri::generate_context!()`。
pub fn run(config: ShellConfig, context: tauri::Context) {
    parse_cli(&config);
    let store_path = own_store_path(&config);
    let _ = store::ensure_schema(&store_path);
    let _ = writeln!(std::io::stderr(), "进度写入 {}", store_path.display());

    let state = AppState {
        content_root: content_root(&config),
        store_path,
        title: config.title,
        binary: config.binary,
    };

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .manage(Mutex::new(state))
        .invoke_handler(tauri::generate_handler![
            get_app_info,
            load_curriculum,
            load_case_source,
            save_case_source,
            compile_and_run,
            load_case_files,
            run_archive_case,
            format_cpp,
            load_mastery,
            save_mastery,
            load_all_mastery,
            save_lab_status,
            load_all_lab_status,
            save_lab_draft,
            load_all_lab_drafts,
            clear_lab_draft,
            save_quiz_picks,
            load_all_quiz_picks
        ])
        .run(context)
        .unwrap_or_else(|e| panic!("error while running {}: {e}", config.binary));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn 案例引用只认单段安全名字() {
        for ok in ["main.cpp", "list-basic", "a_b.c", "_shared"] {
            assert!(is_plain_segment(ok), "{ok} 应当合法");
        }
        for bad in ["", ".", "..", "../x", "a/b", "a\\b", "/etc/passwd", "C:x", "a b", "中文"] {
            assert!(!is_plain_segment(bad), "{bad:?} 应当被拒绝");
        }
    }

    #[test]
    fn 案例路径拒绝穿越_写文件的入口尤其不能放过() {
        let root = Path::new("/app");
        assert_eq!(
            case_path(root, "list-basic", "main.cpp").unwrap(),
            Path::new("/app/content/cases/list-basic/main.cpp")
        );
        assert!(case_path(root, "..", "main.cpp").is_err());
        assert!(case_path(root, "list-basic", "../../../etc/cron.d/x").is_err());
        assert!(case_path(root, "list-basic", "/tmp/x").is_err());
    }

    #[test]
    fn 归档章节接在课表末尾() {
        let mut cur = serde_json::json!({"chapters": [{"id": "a"}]});
        merge_archive(&mut cur, serde_json::json!({"chapters": [{"id": "archive"}]})).unwrap();
        assert_eq!(cur["chapters"][1]["id"], "archive");
        assert!(merge_archive(&mut cur, serde_json::json!({})).is_err());
        let mut bad = serde_json::json!({});
        assert!(merge_archive(&mut bad, serde_json::json!({"chapters": []})).is_err());
    }

    #[test]
    fn 归档案例只认_arc_前缀且不穿越() {
        let root = Path::new("/app");
        assert_eq!(
            archive_case_dir(root, "arc_dp_adapter").unwrap(),
            Path::new("/app/content/cases/arc_dp_adapter")
        );
        for bad in ["adapter_demo", "arc_../x", "..", "arc_a/b", ""] {
            assert!(archive_case_dir(root, bad).is_err(), "{bad:?} 应被拒绝");
        }
    }

    #[test]
    fn 临时目录名收成安全的一段() {
        assert_eq!(safe_path_segment("list-basic"), "list-basic");
        assert_eq!(safe_path_segment("a/b c"), "a_b_c");
        assert_eq!(safe_path_segment(".."), "_");
        assert_eq!(safe_path_segment(""), "_");
    }
}
