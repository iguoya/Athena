//! 运行模式（ADR 0173）：找到仓库就是仓库模式，找不到就是安装模式。
//!
//! 前端（CLI、webui）只跟 `Workspace` 说话——拿清单、启动——不自己判断「现在是哪种模式」。
//! 仓库模式的行为一字不改，全部委托给原来的 `discover_all` 与 `runner`。

use std::path::{Path, PathBuf};

use crate::catalog;
use crate::installed::{self, Env};
use crate::manifest::{self, App};
use crate::paths;
use crate::runner;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    Repo,
    Installed,
}

impl Mode {
    /// 机器读的稳定标识（出现在 `list --json` 里）。
    pub fn key(self) -> &'static str {
        match self {
            Mode::Repo => "repo",
            Mode::Installed => "installed",
        }
    }
}

/// 安装模式下「打开」失败的原因。前端据此决定指路还是报错。
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LaunchError {
    /// 没装（或装在非默认位置）：前端灰态并指路 Releases。
    NotInstalled,
    /// 这类应用安装模式暂不支持启动（异构栈）：同样指路 Releases，但提示不同。
    Unsupported(String),
    Failed(String),
}

impl std::fmt::Display for LaunchError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LaunchError::NotInstalled => write!(f, "未安装：到 Releases 页下载安装包"),
            LaunchError::Unsupported(kind) => {
                write!(f, "安装模式暂不支持启动这类应用（{kind}）：到 Releases 页下载安装包")
            }
            LaunchError::Failed(message) => write!(f, "{message}"),
        }
    }
}

impl From<String> for LaunchError {
    fn from(message: String) -> Self {
        LaunchError::Failed(message)
    }
}

pub struct Workspace {
    repo: Option<PathBuf>,
    env: Env,
}

impl Workspace {
    pub fn locate() -> Workspace {
        Workspace { repo: paths::locate_repo(), env: Env::current() }
    }

    /// 测试与特殊入口用：显式指定仓库与探测环境。
    pub fn new(repo: Option<PathBuf>, env: Env) -> Workspace {
        Workspace { repo, env }
    }

    pub fn repo(&self) -> Option<&Path> {
        self.repo.as_deref()
    }

    pub fn mode(&self) -> Mode {
        if self.repo.is_some() {
            Mode::Repo
        } else {
            Mode::Installed
        }
    }

    /// 全部应用。仓库模式现扫 `app.json`；安装模式取内嵌清单并探测安装位置。
    pub fn apps(&self) -> Vec<App> {
        match &self.repo {
            Some(repo) => manifest::discover_all(repo),
            None => catalog::into_apps(catalog::load_embedded(), |entry| installed::locate(entry, &self.env)),
        }
    }

    /// 启动一个应用，返回窗口进程 pid。
    pub fn launch(&self, app: &App, report: impl FnMut(&str)) -> Result<u32, LaunchError> {
        match (&self.repo, &app.install) {
            (_, Some(install)) => launch_installed(app, install),
            (Some(repo), None) => runner::launch(app, repo, report).map_err(LaunchError::from),
            (None, None) => Err(LaunchError::Failed(format!("{} 没有安装信息，无法启动", app.title))),
        }
    }
}

fn launch_installed(app: &App, install: &manifest::Install) -> Result<u32, LaunchError> {
    if !install.supported {
        return Err(LaunchError::Unsupported(install.kind.clone()));
    }
    let Some(exe) = &install.exe else {
        return Err(LaunchError::NotInstalled);
    };
    // 已经在跑就只把窗口叫到前面，绝不起第二份（同 CLI 的 open）。
    let snapshot = runner::ProcessSnapshot::take();
    if snapshot.state(app) != runner::RunState::Stopped {
        let _ = runner::activate(app);
        return Ok(snapshot.pid_of(app).unwrap_or(0));
    }
    // 启动前先对一遍进度，与仓库模式的 runner::launch 同一约定（ADR 0155）：尽力而为。
    crate::progress_sync::before_launch(app);
    let mut command = std::process::Command::new(exe);
    if let Some(dir) = exe.parent() {
        command.current_dir(dir);
    }
    command
        .stdin(std::process::Stdio::null())
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn()
        .map(|child| child.id())
        .map_err(|e| LaunchError::Failed(format!("启动 {} 失败：{e}", exe.display())))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::installed::Os;

    fn env() -> Env {
        Env { os: Os::Linux, local_app_data: None, program_files: None, home: None, path: vec![] }
    }

    #[test]
    fn 找不到仓库就是安装模式() {
        let workspace = Workspace::new(None, env());
        assert_eq!(workspace.mode(), Mode::Installed);
        assert_eq!(workspace.mode().key(), "installed");
        let apps = workspace.apps();
        assert!(!apps.is_empty(), "内嵌清单不该是空的");
        assert!(apps.iter().all(|app| app.install.is_some()));
        assert!(apps.iter().all(|app| app.embedded_icon.is_some() || app.icon_file.is_none()));
    }

    #[test]
    fn 有仓库就是仓库模式() {
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
        let workspace = Workspace::new(Some(root.canonicalize().unwrap()), env());
        assert_eq!(workspace.mode(), Mode::Repo);
        let apps = workspace.apps();
        assert!(apps.iter().all(|app| app.install.is_none()), "仓库模式不带安装信息");
    }

    #[test]
    fn 未安装与不支持的返回明确结果() {
        let workspace = Workspace::new(None, env());
        let apps = workspace.apps();
        let tauri = apps.iter().find(|app| app.install.as_ref().is_some_and(|i| i.supported)).expect("有 Tauri 应用");
        match workspace.launch(tauri, |_| {}) {
            Err(LaunchError::NotInstalled) => {}
            other => panic!("没装的应该是 NotInstalled，实际 {other:?}"),
        }
        let other = apps.iter().find(|app| app.install.as_ref().is_some_and(|i| !i.supported));
        if let Some(app) = other {
            assert!(matches!(workspace.launch(app, |_| {}), Err(LaunchError::Unsupported(_))));
        }
    }
}
