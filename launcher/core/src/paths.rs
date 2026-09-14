//! 仓库、日志和共享构建缓存的位置。三平台各按各的惯例来。

use std::path::{Path, PathBuf};

/// 找到 Athena 仓库根。标志是 `apps/` 目录。
///
/// 顺序：显式环境变量 → 可执行文件往上找 → 当前目录往上找。
pub fn locate_repo() -> Option<PathBuf> {
    if let Ok(raw) = std::env::var("ATHENA_ROOT") {
        if let Some(found) = validate(Path::new(&raw)) {
            return Some(found);
        }
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(found) = climb(&exe) {
            return Some(found);
        }
    }
    if let Ok(cwd) = std::env::current_dir() {
        if let Some(found) = climb(&cwd.join("placeholder")) {
            return Some(found);
        }
    }
    None
}

fn climb(from: &Path) -> Option<PathBuf> {
    let mut cursor = from.parent();
    for _ in 0..8 {
        let current = cursor?;
        if let Some(found) = validate(current) {
            return Some(found);
        }
        cursor = current.parent();
    }
    None
}

fn validate(candidate: &Path) -> Option<PathBuf> {
    if candidate.join("apps").is_dir() {
        std::fs::canonicalize(candidate).ok()
    } else {
        None
    }
}

/// 各应用的启动日志。构建失败时第一眼看的就是它。
pub fn log_dir() -> PathBuf {
    let dir = if cfg!(target_os = "macos") {
        home().join("Library/Logs/Athena")
    } else if cfg!(target_os = "windows") {
        std::env::var_os("LOCALAPPDATA")
            .map(PathBuf::from)
            .unwrap_or_else(|| home().join("AppData/Local"))
            .join("Athena/logs")
    } else {
        std::env::var_os("XDG_STATE_HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|| home().join(".local/state"))
            .join("athena/logs")
    };
    let _ = std::fs::create_dir_all(&dir);
    dir
}

pub fn log_file(app_id: &str) -> PathBuf {
    log_dir().join(format!("{app_id}.log"))
}

/// 三个 Tauri 应用依赖完全相同，各编一份 target 是纯粹的重复（一份 2–4 GB）。
/// 指到同一个目录后，相同版本的依赖只编一次，第二、三个应用的首次构建几乎是白拿的。
/// 代价是 cargo 对 target 目录加文件锁，同时构建两个应用会串行等待。
pub fn shared_cargo_target(repo: &Path) -> PathBuf {
    let dir = repo.join(".cache/cargo-target");
    let _ = std::fs::create_dir_all(&dir);
    dir
}

fn home() -> PathBuf {
    #[cfg(windows)]
    {
        std::env::var_os("USERPROFILE")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("."))
    }
    #[cfg(not(windows))]
    {
        std::env::var_os("HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("."))
    }
}

/// 从桌面环境（菜单栏、快捷键、登录项）启动时 PATH 很短，node、cargo、meson、Qt
/// 往往都不在里面。这些补全过去散落在五份 dev 脚本里，现在只写一处。
pub fn extra_path_entries() -> Vec<PathBuf> {
    let mut entries: Vec<PathBuf> = Vec::new();
    if cfg!(target_os = "macos") {
        for raw in [
            "/opt/homebrew/bin",
            "/usr/local/bin",
            "/opt/homebrew/opt/qt@6/bin",
            "/usr/local/opt/qt@6/bin",
            "/usr/local/opt/node/bin",
        ] {
            entries.push(PathBuf::from(raw));
        }
    } else if cfg!(target_os = "windows") {
        // Windows 上工具链一般已经在 PATH 里；预留位置，需要时再补。
    } else {
        for raw in ["/usr/local/bin", "/usr/bin"] {
            entries.push(PathBuf::from(raw));
        }
        entries.push(home().join(".local/bin"));
    }
    entries.push(home().join(".cargo/bin"));
    entries.into_iter().filter(|path| path.is_dir()).collect()
}
