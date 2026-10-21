// 教程壳读某一章的源码、按白名单编译并启动窗口、把作答写入进度库。
// 学习者要改代码时，壳把那一章复制到 workspace/，用 VS 2022 打开副本。exercise/ 保持课程原件。
// 魔方和求解在 gtkmm 程序里，不在这个壳里。

use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use rusqlite::{params, Connection};

const CHAPTER_DIRS: &[&str] = &[
    "01-net",
    "02-turns",
    "03-layer",
    "04-orient",
    "05-permute",
    "06-solver",
    "07-optimal",
];

/// 每章一个窗口：运行 id 就是章节目录，对应 meson 编出的可执行文件。
const CHAPTERS: &[(&str, &str)] = &[
    ("01-net", "cube-01"),
    ("02-turns", "cube-02"),
    ("03-layer", "cube-03"),
    ("04-orient", "cube-04"),
    ("05-permute", "cube-05"),
    ("06-solver", "cube-06"),
    ("07-optimal", "cube-07"),
];

fn app_root() -> Result<PathBuf, String> {
    if let Ok(root) = std::env::var("ATHENA_POCKET_CUBE_SOLVER_ROOT") {
        let path = PathBuf::from(root);
        if path.join("app.json").is_file() {
            return Ok(path);
        }
    }
    let mut cursor = std::env::current_dir().map_err(|e| e.to_string())?;
    for _ in 0..6 {
        if cursor.join("app.json").is_file() && cursor.join("content").is_dir() {
            return Ok(cursor);
        }
        if !cursor.pop() {
            break;
        }
    }
    Err("找不到应用根目录（需要 app.json 和 content/）".into())
}

fn database_path() -> Result<PathBuf, String> {
    // 进度库放用户数据目录，不进仓库（ADR 0155）：启动器的同步代理在能连上路由器时
    // 把它与中心库互推。目录名登记在 app.json 的 progress.dir，两处必须一致。
    let dir = dirs_next::data_dir()
        .ok_or("找不到用户数据目录")?
        .join("AthenaPocketCubeSolver");
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    Ok(dir.join("learning.db"))
}

fn open_db() -> Result<Connection, String> {
    let conn = Connection::open(database_path()?).map_err(|e| e.to_string())?;
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_id TEXT NOT NULL,
            correct INTEGER NOT NULL,
            answered_at INTEGER NOT NULL
        );",
    )
    .map_err(|e| e.to_string())?;
    Ok(conn)
}

fn mingw_bin() -> Option<PathBuf> {
    let candidate = PathBuf::from(r"C:\msys64\mingw64\bin");
    if candidate.is_dir() {
        Some(candidate)
    } else {
        None
    }
}

fn with_toolchain(cmd: &mut Command) {
    if let Some(bin) = mingw_bin() {
        let old = std::env::var_os("PATH").unwrap_or_default();
        // mingw64 在前，编译器和 GTK 运行库用这一套。usr\bin 紧随其后：Meson 生成的
        // ninja 规则要用真正的 env.exe 包一层环境变量，本机 PATH 里同名的是一段
        // shell 脚本，Windows 直接 CreateProcess 会失败。
        let mut paths = vec![bin.clone()];
        let usr = bin
            .parent()
            .and_then(|root| root.parent())
            .map(|msys| msys.join("usr").join("bin"));
        if let Some(usr) = usr {
            if usr.is_dir() {
                paths.push(usr);
            }
        }
        paths.extend(std::env::split_paths(&old));
        if let Ok(joined) = std::env::join_paths(paths) {
            cmd.env("PATH", joined);
        }
        cmd.env(
            "PKG_CONFIG_PATH",
            bin.parent()
                .unwrap_or(Path::new("."))
                .join("lib")
                .join("pkgconfig"),
        );
    }
}

fn run_tool(dir: &Path, program: &str, args: &[&str]) -> Result<String, String> {
    let mut cmd = Command::new(program);
    cmd.args(args).current_dir(dir);
    with_toolchain(&mut cmd);
    let output = cmd
        .output()
        .map_err(|e| format!("无法启动 {program}：{e}。Windows 上需要 MSYS2 mingw64 的 meson、blueprint-compiler 与 gtkmm"))?;
    let mut text = String::new();
    text.push_str(&String::from_utf8_lossy(&output.stdout));
    text.push_str(&String::from_utf8_lossy(&output.stderr));
    if !output.status.success() {
        let tail = text.chars().rev().take(2400).collect::<String>();
        let tail = tail.chars().rev().collect::<String>();
        return Err(format!("{program} 失败\n{tail}"));
    }
    Ok(text)
}

fn allowed_source(path: &Path) -> bool {
    match path.file_name().and_then(|name| name.to_str()) {
        Some("meson.build") => true,
        _ => matches!(
            path.extension().and_then(|ext| ext.to_str()),
            Some("cc" | "hh" | "h" | "blp" | "css" | "xml")
        ),
    }
}

#[tauri::command]
fn read_source(relative: String) -> Result<String, String> {
    if relative.contains("..") || relative.contains(':') {
        return Err("只允许读 exercise/ 下面的源文件".into());
    }
    let root = app_root()?;
    let exercise = root.join("exercise");
    let path = root.join(&relative);
    if !allowed_source(&path) {
        return Err("只读界面文件、样式、源码和 meson.build".into());
    }
    let canon = path.canonicalize().map_err(|e| e.to_string())?;
    let exercise = exercise.canonicalize().map_err(|e| e.to_string())?;
    if !canon.starts_with(&exercise) {
        return Err("只允许读 exercise/ 下面的源文件".into());
    }
    let bytes = fs::read(&canon).map_err(|e| e.to_string())?;
    if bytes.len() > 256 * 1024 {
        return Err("文件太大".into());
    }
    String::from_utf8(bytes).map_err(|e| e.to_string())
}

fn chapter_dir(chapter: &str) -> Result<&str, String> {
    CHAPTER_DIRS
        .iter()
        .copied()
        .find(|id| *id == chapter)
        .ok_or_else(|| "未知章节".to_string())
}

fn workspace_chapter(chapter: &str) -> Result<PathBuf, String> {
    Ok(app_root()?.join("workspace").join(chapter_dir(chapter)?))
}

fn copy_tree(src: &Path, dst: &Path) -> Result<(), String> {
    fs::create_dir_all(dst).map_err(|e| e.to_string())?;
    for entry in fs::read_dir(src).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        let name = entry.file_name();
        // 构建目录含本机绝对路径，复制过去会让 meson 编错地方。
        if name == "build" {
            continue;
        }
        let to = dst.join(&name);
        let kind = entry.file_type().map_err(|e| e.to_string())?;
        if kind.is_dir() {
            copy_tree(&entry.path(), &to)?;
        } else if kind.is_file() {
            fs::copy(entry.path(), &to).map_err(|e| e.to_string())?;
        }
    }
    Ok(())
}

fn ensure_workspace(chapter: &str) -> Result<PathBuf, String> {
    let src = app_root()?.join("exercise").join(chapter_dir(chapter)?);
    if !src.join("meson.build").is_file() {
        return Err(format!("{chapter} 没有 meson.build"));
    }
    let dst = workspace_chapter(chapter)?;
    if !dst.join("meson.build").is_file() {
        copy_tree(&src, &dst)?;
    }
    let props = dst.join("CppProperties.json");
    if !props.is_file() {
        fs::write(&props, CPP_PROPERTIES).map_err(|e| e.to_string())?;
    }
    Ok(dst)
}

fn visual_studio_2022() -> Result<PathBuf, String> {
    if !cfg!(windows) {
        return Err("在 VS 2022 中打开只提供给 Windows。".into());
    }
    let vswhere = PathBuf::from(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe");
    if vswhere.is_file() {
        let output = Command::new(&vswhere)
            .args(["-latest", "-version", "[17.0,18.0)", "-property", "productPath"])
            .output()
            .map_err(|e| format!("无法运行 vswhere：{e}"))?;
        if output.status.success() {
            let text = String::from_utf8_lossy(&output.stdout);
            let path = text.lines().next().unwrap_or("").trim();
            if !path.is_empty() && Path::new(path).is_file() {
                return Ok(PathBuf::from(path));
            }
        }
    }
    for edition in ["Community", "Professional", "Enterprise"] {
        let candidate = PathBuf::from(format!(
            r"C:\Program Files\Microsoft Visual Studio\2022\{edition}\Common7\IDE\devenv.exe"
        ));
        if candidate.is_file() {
            return Ok(candidate);
        }
    }
    Err("没有找到 Visual Studio 2022。安装 VS 2022 后再打开这一章。".into())
}

/// 给 VS 2022「打开文件夹」用的智能感知路径。只写进工作副本，不进课程原件。
const CPP_PROPERTIES: &str = r#"{
  "configurations": [
    {
      "name": "MSYS2 mingw64",
      "intelliSenseMode": "windows-gcc-x64",
      "compilerPath": "C:/msys64/mingw64/bin/g++.exe",
      "cppStandard": "c++20",
      "includePath": [
        "${workspaceRoot}",
        "${workspaceRoot}/..",
        "C:/msys64/mingw64/include/gtkmm-4.0",
        "C:/msys64/mingw64/lib/gtkmm-4.0/include",
        "C:/msys64/mingw64/include/glibmm-2.68",
        "C:/msys64/mingw64/lib/glibmm-2.68/include",
        "C:/msys64/mingw64/include/giomm-2.68",
        "C:/msys64/mingw64/lib/giomm-2.68/include",
        "C:/msys64/mingw64/include/gtk-4.0",
        "C:/msys64/mingw64/include/glib-2.0",
        "C:/msys64/mingw64/lib/glib-2.0/include",
        "C:/msys64/mingw64/include/cairo",
        "C:/msys64/mingw64/include/pango-1.0",
        "C:/msys64/mingw64/include/pangomm-2.48",
        "C:/msys64/mingw64/lib/pangomm-2.48/include",
        "C:/msys64/mingw64/include/sigc++-3.0",
        "C:/msys64/mingw64/lib/sigc++-3.0/include",
        "C:/msys64/mingw64/include/gdk-pixbuf-2.0",
        "C:/msys64/mingw64/include/graphene-1.0",
        "C:/msys64/mingw64/lib/graphene-1.0/include",
        "C:/msys64/mingw64/include"
      ]
    }
  ]
}
"#;

#[tauri::command]
fn workspace_present(chapter: String) -> Result<bool, String> {
    Ok(workspace_chapter(&chapter)?.join("meson.build").is_file())
}

#[tauri::command]
fn open_in_visual_studio(chapter: String) -> Result<String, String> {
    let dir = ensure_workspace(&chapter)?;
    let devenv = visual_studio_2022()?;
    Command::new(&devenv)
        .arg(&dir)
        .spawn()
        .map_err(|e| format!("工作副本已备好，但没有启动 VS 2022：{e}"))?;
    Ok("已在 VS 2022 中打开这一章的工作副本。改的是 workspace 里的文件，课程原件不动。编译仍用这一页的运行按钮。".into())
}

#[tauri::command]
fn restore_workspace(chapter: String) -> Result<String, String> {
    let dir = workspace_chapter(&chapter)?;
    if dir.exists() {
        fs::remove_dir_all(&dir).map_err(|e| {
            format!("还原失败，工作副本可能正被 VS 2022 占用：{e}")
        })?;
    }
    Ok("这一章的工作副本已删掉。下次在 VS 2022 中打开会重新从课程原件复制。".into())
}

fn run_chapter_sync(id: String) -> Result<String, String> {
    let (dir_name, exe_name) = CHAPTERS
        .iter()
        .find(|(key, _)| *key == id)
        .copied()
        .ok_or("未知章节")?;
    let workspace = app_root()?.join("workspace").join(dir_name);
    let from_workspace = workspace.join("meson.build").is_file();
    let dir = if from_workspace {
        workspace
    } else {
        app_root()?.join("exercise").join(dir_name)
    };
    if !dir.join("meson.build").is_file() {
        return Err(format!("{dir_name} 没有 meson.build"));
    }
    if !dir.join("build").join("build.ninja").is_file() {
        run_tool(&dir, "meson", &["setup", "build"])?;
    }
    run_tool(&dir, "meson", &["compile", "-C", "build"])?;
    let exe = if cfg!(windows) {
        dir.join("build").join(format!("{exe_name}.exe"))
    } else {
        dir.join("build").join(exe_name)
    };
    let mut cmd = Command::new(&exe);
    with_toolchain(&mut cmd);
    cmd.spawn()
        .map_err(|e| format!("编译过了，但启动 {} 失败：{e}", exe.display()))?;
    let where_from = if from_workspace { "工作副本" } else { "课程原件" };
    Ok(format!("已启动 {exe_name}（{where_from}）"))
}

#[tauri::command]
async fn run_chapter(id: String) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || run_chapter_sync(id))
        .await
        .map_err(|e| e.to_string())?
}

/// 每道题只看最近一次作答。答对的 id 交给界面，用来把整章标绿。
#[tauri::command]
fn passed_questions() -> Result<Vec<String>, String> {
    let conn = open_db()?;
    let mut stmt = conn
        .prepare(
            // 「最近一次」按作答时间认，同一秒再按行号：同步拉回的旧记录入库晚、id 更大，
            // 按 id 认会把别的设备昨天的答错当成最近一次，盖掉本机刚答对的（ADR 0155）。
            "SELECT DISTINCT a.function_id FROM attempts a
             WHERE a.correct = 1
               AND NOT EXISTS (SELECT 1 FROM attempts b
                               WHERE b.function_id = a.function_id
                                 AND (b.answered_at > a.answered_at
                                      OR (b.answered_at = a.answered_at AND b.id > a.id)))",
        )
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| row.get(0))
        .map_err(|e| e.to_string())?;
    rows.collect::<Result<Vec<String>, _>>()
        .map_err(|e| e.to_string())
}

#[tauri::command]
fn record_attempt(function_id: String, correct: bool) -> Result<(), String> {
    if !function_id.starts_with("cube.") || function_id.len() > 80 {
        return Err("知识点 id 必须以 cube. 开头".into());
    }
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_secs() as i64;
    let conn = open_db()?;
    conn.execute(
        "INSERT INTO attempts (function_id, correct, answered_at) VALUES (?1, ?2, ?3)",
        params![function_id, correct as i64, now],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_unknown_chapter() {
        assert!(chapter_dir("01-net").is_ok());
        assert!(chapter_dir(r"..\exercise").is_err());
    }

    #[test]
    fn copy_skips_build_dir() {
        let src = app_root().unwrap().join("exercise").join("01-net");
        let dst = std::env::temp_dir().join("athena-cube-copy-test");
        let _ = fs::remove_dir_all(&dst);
        copy_tree(&src, &dst).unwrap();
        assert!(dst.join("meson.build").is_file());
        assert!(dst.join("ui").join("window.blp").is_file());
        assert!(!dst.join("build").exists());
        fs::remove_dir_all(&dst).unwrap();
    }
}

pub fn run() {
    tauri::Builder::default()
    .plugin(tauri_plugin_updater::Builder::new().build())
    .plugin(tauri_plugin_process::init())
        .invoke_handler(tauri::generate_handler![
            read_source,
            run_chapter,
            record_attempt,
            passed_questions,
            workspace_present,
            open_in_visual_studio,
            restore_workspace
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
