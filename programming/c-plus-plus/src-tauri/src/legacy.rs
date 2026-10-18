//! 从新壳启动 practice/cpp 已经编好的 gtkmm 窗口（本应用 ADR 0061，仓库 ADR 0141）。
//!
//! 只认仓库里那一个固定目录下的编译成果，不接受调用方传入的路径或参数。
//! Windows 上它链的是 MSYS2 mingw64 的 GTK，运行库不在 exe 旁边，所以要把
//! `C:\msys64\mingw64\bin` 放到 PATH 前面。系统 PATH 里的 Octave 也带一份 gcc，
//! 不能让它排在前面。

use std::ffi::OsStr;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;

const CANDIDATES: &[&str] = &[
    "build/athena-cpp.exe",
    "build/athena-cpp",
    "build/athena-c-plus-plus.exe",
    "build/athena-c-plus-plus",
    "build-windows-release/athena-cpp.exe",
    "build-windows-release/athena-c-plus-plus.exe",
    "build-release/athena-cpp",
    "build-release/athena-c-plus-plus",
];

/// 课程目录是 `programming/c-plus-plus`。旧工程固定在仓库的 `practice/cpp`。
pub fn project_dir(course_root: &Path) -> Result<PathBuf, String> {
    let course_root = course_root
        .canonicalize()
        .map_err(|_| "找不到课程目录".to_string())?;
    let repo = course_root
        .parent()
        .and_then(Path::parent)
        .ok_or_else(|| "课程目录不在仓库里".to_string())?;
    let project = repo.join("practice").join("cpp");
    let full = project.canonicalize().map_err(|_| missing_hint(&project))?;
    let in_practice = full
        .parent()
        .and_then(Path::file_name)
        .is_some_and(|name| name == OsStr::new("practice"));
    if !in_practice || full.file_name() != Some(OsStr::new("cpp")) {
        return Err("旧版窗口只能从 practice/cpp 启动".to_string());
    }
    Ok(full)
}

pub fn locate(root: &Path) -> Option<PathBuf> {
    let root = root.canonicalize().ok()?;
    for relative in CANDIDATES {
        let path = root.join(relative);
        if !path.is_file() {
            continue;
        }
        let full = path.canonicalize().ok()?;
        if full.starts_with(&root) {
            return Some(full);
        }
    }
    None
}

pub fn open(course_root: &Path) -> Result<String, String> {
    let root = project_dir(course_root)?;
    let binary = locate(&root).ok_or_else(|| missing_hint(&root))?;
    let mut cmd = Command::new(&binary);
    cmd.current_dir(&root)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .env("ATHENA_CPP_ROOT", &root);
    if let Some(runtime) = gtk_runtime_bin() {
        cmd.env("PATH", prepend_path(&runtime));
    }

    let mut child = cmd
        .spawn()
        .map_err(|error| format!("启动失败：{error}\n程序在 {}", binary.display()))?;
    thread::sleep(Duration::from_millis(500));
    match child.try_wait() {
        Ok(Some(status)) => Err(format!(
            "旧版窗口马上退出了（{status}）。\n{}",
            runtime_hint()
        )),
        Ok(None) => {
            thread::spawn(move || {
                let _ = child.wait();
            });
            Ok("已打开旧版窗口".to_string())
        }
        Err(error) => Err(error.to_string()),
    }
}

fn missing_hint(root: &Path) -> String {
    format!(
        "找不到旧版窗口程序。\n它应在 {}。\n在 practice/cpp 里用 MSYS2 mingw64 执行：\nmeson setup build --reconfigure\nmeson compile -C build",
        root.join("build/athena-cpp.exe").display()
    )
}

fn runtime_hint() -> &'static str {
    if cfg!(windows) {
        "需要 MSYS2 mingw64 的 GTK 运行库（C:\\msys64\\mingw64\\bin 里要有 libgtkmm-4.0-0.dll）。"
    } else {
        "需要本机已安装的 GTK4 / gtkmm4 运行库。"
    }
}

fn gtk_runtime_bin() -> Option<PathBuf> {
    if !cfg!(windows) {
        return None;
    }
    let bin = PathBuf::from(r"C:\msys64\mingw64\bin");
    if bin.join("libgtkmm-4.0-0.dll").is_file() {
        Some(bin)
    } else {
        None
    }
}

fn prepend_path(dir: &Path) -> std::ffi::OsString {
    let mut paths = vec![dir.to_path_buf()];
    if let Some(old) = std::env::var_os("PATH") {
        paths.extend(std::env::split_paths(&old));
    }
    std::env::join_paths(paths).unwrap_or_else(|_| dir.as_os_str().to_os_string())
}

#[cfg(test)]
mod tests {
    use super::locate;
    use std::fs;
    use std::path::Path;

    #[test]
    fn locate_only_accepts_the_meson_binary() {
        let root = std::env::temp_dir().join(format!("athena-legacy-{}", std::process::id()));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(root.join("build")).unwrap();
        let name = if cfg!(windows) {
            "athena-cpp.exe"
        } else {
            "athena-cpp"
        };
        fs::write(root.join("build").join(name), b"not a real exe").unwrap();
        fs::create_dir_all(root.join("elsewhere")).unwrap();
        fs::write(root.join("elsewhere").join(name), b"nope").unwrap();

        let found = locate(&root).unwrap();
        assert!(found.ends_with(Path::new("build").join(name)));
        let _ = fs::remove_dir_all(&root);
    }
}
