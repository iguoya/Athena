//! 仓库、日志和共享构建缓存的位置。三平台各按各的惯例来。

use std::path::{Path, PathBuf};

/// 找到 Athena 仓库根。标志是 `subjects/` 目录。
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
    if candidate.join("subjects").is_dir() {
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
pub fn extra_path_entries(app: &crate::manifest::App) -> Vec<PathBuf> {
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
        // `subjects/cpp` 的 GTK4/gtkmm 走 MSYS2 UCRT64（g++、pkg-config、ninja、
        // blueprint-compiler 全在这个前缀下）；这套工具链不在 Windows 默认 PATH
        // 里，从菜单栏托盘或普通终端启动时摸不到，meson 要么报找不到
        // pkg-config，要么误捡系统装的 MSVC cl.exe，把 build/ 配置成不兼容的
        // 工具链（gtkmm 是 MinGW ABI，跟 MSVC 不兼容）。`scripts/package_windows.py`
        // 打包时已经认定 `C:\msys64\ucrt64\bin` 是这套工具链的位置，这里补上同一个
        // 路径，让开发态启动也稳定找到它。
        //
        // 只给用 Meson 的应用注入（目前是 subjects/cpp 和 practice/
        // 下的 GTK4 小项目）：`subjects/c`、`subjects/polaris` 是 Qt + MSVC，一旦这个
        // 目录下的 g++/gcc 对它们也可见，CMake 的 Ninja 生成器会优先在 PATH
        // 里找到 MinGW 编译器而不是走 vswhere 探测 MSVC——实测触发过这个
        // 问题：Qt 官方安装器的 Qt6 是 MSVC ABI 编的，链接期全是
        // `undefined reference`。不同工具链不共用 PATH，各应用只看见自己
        // 需要的那一套（用户反馈：同一个 app 不同工具链要分开，这里是同一
        // 台机器不同 app 的工具链要分开，同一条原则）。
        //
        // 按 app_id 列白名单撑不住以后 practice/ 下继续加 GTK4 小项目
        // （每加一个都要回来改这里），改成按 app.json 的 dev.prepare 是否
        // 真的调用 meson 判断——用什么构建系统这件事已经写在清单里了，
        // 不用另外维护一份重复的名单。
        let uses_meson = app
            .dev
            .prepare
            .iter()
            .any(|step| step.run.first().map(String::as_str) == Some("meson"));
        if uses_meson {
            entries.push(PathBuf::from(r"C:\msys64\ucrt64\bin"));
        }
        // `subjects/c` 的 Qt Quick / QML 走官方 Qt 安装器的 MSVC kit：CMake 能找到它是
        // 因为 app.json 的 CMAKE_PREFIX_PATH 指了路，但可执行文件运行时还要在 PATH
        // 里找到 Qt6Core.dll 等运行库，装好编译不代表能跑。官方安装器把版本号写进
        // 路径（不像 Homebrew 那样有个不随版本变的符号链接），升级 Qt 版本后要跟着
        // 改这里——这是该装法本身的限制，不是能绕开的兜底。
        entries.push(PathBuf::from(r"C:\Qt\6.8.1\msvc2022_64\bin"));
    } else {
        for raw in ["/usr/local/bin", "/usr/bin"] {
            entries.push(PathBuf::from(raw));
        }
        entries.push(home().join(".local/bin"));
    }
    entries.push(home().join(".cargo/bin"));
    // 驾考学习用 Flutter。官方默认装在 ~/flutter，桌面启动器的 PATH 里没有它。
    entries.push(home().join("flutter/bin"));
    entries.push(home().join("development/flutter/bin"));
    entries.into_iter().filter(|path| path.is_dir()).collect()
}
