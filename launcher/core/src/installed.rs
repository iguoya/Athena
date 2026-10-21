//! 安装模式：应用装在哪（ADR 0173 决策 4）。
//!
//! 各平台的安装位置约定全关在这个模块里，别处不出现平台分支（根 AGENTS.md「跨平台」）。
//! 只认默认安装位置：用户把应用装到别处的，这里识别不了，启动器当作「未安装」并指路 Releases
//! ——如实降级，不假装能找到（ADR 0047）。

use std::path::{Path, PathBuf};

use crate::catalog::CatalogEntry;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Os {
    Windows,
    MacOs,
    Linux,
}

/// 探测需要的环境，抽出来是为了测试里能造假的目录与假的平台。
#[derive(Debug, Clone)]
pub struct Env {
    pub os: Os,
    pub local_app_data: Option<PathBuf>,
    pub program_files: Option<PathBuf>,
    pub home: Option<PathBuf>,
    pub path: Vec<PathBuf>,
}

impl Env {
    pub fn current() -> Env {
        let os = if cfg!(target_os = "windows") {
            Os::Windows
        } else if cfg!(target_os = "macos") {
            Os::MacOs
        } else {
            Os::Linux
        };
        Env {
            os,
            local_app_data: std::env::var_os("LOCALAPPDATA").map(PathBuf::from),
            program_files: std::env::var_os("ProgramFiles").map(PathBuf::from),
            home: dirs_next::home_dir(),
            path: std::env::var_os("PATH")
                .map(|raw| std::env::split_paths(&raw).collect())
                .unwrap_or_default(),
        }
    }
}

/// 安装模式能启动哪类应用：Tauri 应用（含拾阶）有统一的安装约定。驾考（Flutter 压缩包）、
/// 旧 cpp 窗口、c-gui-lab（Electron）没有，先显示、不启动（ADR 0173 决策 4）。
pub fn is_supported(kind: &str) -> bool {
    matches!(kind, "tauri" | "ascent")
}

/// 可执行文件的候选位置，按优先级。
pub fn candidates(entry: &CatalogEntry, env: &Env) -> Vec<PathBuf> {
    let (Some(binary), product) = (entry.main_binary.as_deref(), entry.product_name.as_deref()) else {
        return Vec::new();
    };
    let mut out = Vec::new();
    match env.os {
        Os::Windows => {
            let exe = format!("{binary}.exe");
            // Tauri 的 NSIS 默认每用户安装到 %LOCALAPPDATA%\<productName>；
            // 「为所有用户安装」落在 Program Files。
            if let Some(product) = product {
                if let Some(local) = &env.local_app_data {
                    out.push(local.join(product).join(&exe));
                    out.push(local.join("Programs").join(product).join(&exe));
                }
                if let Some(files) = &env.program_files {
                    out.push(files.join(product).join(&exe));
                }
            }
        }
        Os::MacOs => {
            if let Some(product) = product {
                let inside = |root: PathBuf| root.join(format!("{product}.app/Contents/MacOS/{binary}"));
                out.push(inside(PathBuf::from("/Applications")));
                if let Some(home) = &env.home {
                    out.push(inside(home.join("Applications")));
                }
            }
        }
        Os::Linux => {
            // deb 把主程序装进 /usr/bin；先看 PATH，再兜底 /usr/bin。
            for dir in &env.path {
                out.push(dir.join(binary));
            }
            out.push(Path::new("/usr/bin").join(binary));
        }
    }
    out
}

/// 第一个真实存在的候选。
pub fn locate(entry: &CatalogEntry, env: &Env) -> Option<PathBuf> {
    candidates(entry, env).into_iter().find(|path| path.is_file())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn entry() -> CatalogEntry {
        CatalogEntry {
            id: "snake".into(),
            title: "贪吃蛇".into(),
            summary: String::new(),
            symbol: "book".into(),
            letter: "蛇".into(),
            accent: "#000".into(),
            group: None,
            related: vec![],
            evolves_from: None,
            parent: None,
            also_under: vec![],
            also_in: vec![],
            hidden: false,
            lifecycle: "active".into(),
            kind: "tauri".into(),
            product_name: Some("贪吃蛇".into()),
            main_binary: Some("athena-snake".into()),
            identifier: None,
            progress: None,
            icon: None,
        }
    }

    fn env(os: Os, root: &Path) -> Env {
        Env {
            os,
            local_app_data: Some(root.join("Local")),
            program_files: Some(root.join("PF")),
            home: Some(root.join("home")),
            path: vec![root.join("bin")],
        }
    }

    #[test]
    fn 支持的类型() {
        assert!(is_supported("tauri") && is_supported("ascent"));
        for kind in ["driver", "cpp", "electron"] {
            assert!(!is_supported(kind), "{kind}");
        }
    }

    #[test]
    fn windows_候选与定位() {
        let dir = tempfile::tempdir().unwrap();
        let env = env(Os::Windows, dir.path());
        let list = candidates(&entry(), &env);
        assert_eq!(list[0], dir.path().join("Local/贪吃蛇/athena-snake.exe"));
        assert!(list.len() == 3);
        assert!(locate(&entry(), &env).is_none(), "什么都没装");
        let installed = dir.path().join("Local/贪吃蛇");
        std::fs::create_dir_all(&installed).unwrap();
        std::fs::write(installed.join("athena-snake.exe"), b"").unwrap();
        assert_eq!(locate(&entry(), &env), Some(installed.join("athena-snake.exe")));
    }

    #[test]
    fn macos_候选() {
        let dir = tempfile::tempdir().unwrap();
        let list = candidates(&entry(), &env(Os::MacOs, dir.path()));
        assert_eq!(list[0], PathBuf::from("/Applications/贪吃蛇.app/Contents/MacOS/athena-snake"));
        assert_eq!(list[1], dir.path().join("home/Applications/贪吃蛇.app/Contents/MacOS/athena-snake"));
    }

    #[test]
    fn linux_按_path_找() {
        let dir = tempfile::tempdir().unwrap();
        let env = env(Os::Linux, dir.path());
        std::fs::create_dir_all(dir.path().join("bin")).unwrap();
        std::fs::write(dir.path().join("bin/athena-snake"), b"").unwrap();
        assert_eq!(locate(&entry(), &env), Some(dir.path().join("bin/athena-snake")));
        assert_eq!(candidates(&entry(), &env).last().unwrap(), Path::new("/usr/bin/athena-snake"));
    }

    #[test]
    fn 缺二进制名就没有候选() {
        let mut e = entry();
        e.main_binary = None;
        let dir = tempfile::tempdir().unwrap();
        assert!(candidates(&e, &env(Os::Windows, dir.path())).is_empty());
    }
}
