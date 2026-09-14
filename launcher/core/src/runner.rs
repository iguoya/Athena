//! 执行清单里的 dev 声明：构建、启动、探测状态、停止、把窗口叫到前面。

use std::io::Write;
use std::net::{SocketAddr, TcpStream, ToSocketAddrs};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::Duration;

use sysinfo::{ProcessRefreshKind, RefreshKind, System};

use crate::manifest::{App, ReadySpec};
use crate::paths;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RunState {
    /// 没起来。
    Stopped,
    /// 有属于它的进程在跑，但还没就绪——多半在 cargo / vite / cmake 那一段。
    Starting,
    /// 窗口进程在，且（有 dev server 的话）服务连得上。
    Ready,
}

impl RunState {
    pub fn label(self) -> &'static str {
        match self {
            RunState::Stopped => "未运行",
            RunState::Starting => "启动中…",
            RunState::Ready => "运行中",
        }
    }
}

/// 一次性把全部进程读出来，再判断每个应用的状态：五个应用只扫一遍进程表。
pub struct ProcessSnapshot {
    system: System,
}

impl ProcessSnapshot {
    pub fn take() -> Self {
        let system = System::new_with_specifics(
            RefreshKind::nothing().with_processes(ProcessRefreshKind::everything()),
        );
        Self { system }
    }

    /// 窗口进程：可执行文件落在应用自己的目录下。不靠进程名匹配——名字会改，
    /// 路径是它自己的。
    fn window_pid(&self, app: &App) -> Option<sysinfo::Pid> {
        let prefix = app.match_prefix();
        let binary = app.dev.binary.as_deref();
        self.system.processes().iter().find_map(|(pid, process)| {
            let exe = process.exe()?;
            let by_path = exe.starts_with(&prefix);
            let by_name = binary.is_some_and(|name| {
                exe.file_stem().is_some_and(|stem| stem == name)
            });
            (by_path || by_name).then_some(*pid)
        })
    }

    /// 构建期的那一串（npm、cargo、vite、ninja）：命令行里带着应用目录的路径。
    /// 末尾必须带分隔符：`apps/c` 是 `apps/cpp` 的前缀，少了它两个应用会互相误判。
    fn is_busy(&self, app: &App) -> bool {
        let needle = format!("{}{}", app.dir.display(), std::path::MAIN_SEPARATOR);
        self.system.processes().values().any(|process| {
            process
                .cmd()
                .iter()
                .any(|part| part.to_string_lossy().contains(&needle))
        })
    }

    /// 就绪的判据只有一个：**窗口进程在**。
    ///
    /// dev server 通不算就绪——Tauri 的 vite 秒开，而 Rust 壳还要编几十秒，
    /// 这段时间里端口是通的但屏幕上什么都没有。http 探测只用来回答另一个问题：
    /// 窗口已经出来了，但页面是不是还没连上。
    pub fn state(&self, app: &App) -> RunState {
        if self.window_pid(app).is_some() {
            return match &app.dev.ready {
                ReadySpec::Http(url) if !reachable(url) => RunState::Starting,
                _ => RunState::Ready,
            };
        }
        if self.is_busy(app) {
            RunState::Starting
        } else {
            RunState::Stopped
        }
    }

    pub fn pid_of(&self, app: &App) -> Option<u32> {
        self.window_pid(app).map(|pid| pid.as_u32())
    }
}

/// 只做连通性探测，不发 HTTP 请求：dev server 能接受连接就说明它起来了，
/// 这样也不用为一个探针引入 HTTP 客户端依赖。
fn reachable(url: &str) -> bool {
    let Some(authority) = url
        .split_once("//")
        .map(|(_, rest)| rest.split('/').next().unwrap_or(rest))
    else {
        return false;
    };
    let with_port = if authority.contains(':') {
        authority.to_string()
    } else {
        format!("{authority}:80")
    };
    let Ok(mut addresses) = with_port.to_socket_addrs() else {
        return false;
    };
    addresses.any(|address: SocketAddr| {
        TcpStream::connect_timeout(&address, Duration::from_millis(300)).is_ok()
    })
}

/// 构建并启动一个应用。`report` 收到的每一行同时写进日志文件。
///
/// 这个函数会阻塞到"长驻命令已经拉起来"为止——prepare 那几步（npm install、
/// meson compile、cargo）是同步跑完的，因为它们失败了就没必要继续。
pub fn launch(app: &App, repo: &Path, mut report: impl FnMut(&str)) -> Result<u32, String> {
    if !app.is_runnable() {
        return Err(format!(
            "{} 还没有在 app.json 里声明 dev.run，编排器不知道怎么启动它",
            app.title
        ));
    }

    let log_path = paths::log_file(&app.id);
    let mut log = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_path)
        .map_err(|error| format!("打不开日志 {}：{error}", log_path.display()))?;

    let mut say = |line: &str| {
        let _ = writeln!(log, "{line}");
        report(line);
    };
    say(&format!("===== 启动 {} =====", app.id));

    for step in &app.dev.prepare {
        if let Some(marker) = &step.when_missing {
            if app.dir.join(marker).exists() {
                continue;
            }
        }
        let label = step
            .label
            .clone()
            .unwrap_or_else(|| step.run.join(" "));
        say(&format!("[准备] {label}"));
        let status = command(app, repo, &step.run)
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            .status()
            .map_err(|error| format!("{label} 没能执行：{error}"))?;
        if !status.success() {
            let message = format!("{label} 失败（退出码 {:?}）", status.code());
            say(&message);
            return Err(message);
        }
    }

    say(&format!("[启动] {}", app.dev.run.join(" ")));
    let stdout = log
        .try_clone()
        .map_err(|error| format!("日志复制失败：{error}"))?;
    let stderr = log
        .try_clone()
        .map_err(|error| format!("日志复制失败：{error}"))?;
    let child = command(app, repo, &app.dev.run)
        .stdout(Stdio::from(stdout))
        .stderr(Stdio::from(stderr))
        .spawn()
        .map_err(|error| format!("{} 启动失败：{error}", app.title))?;
    Ok(child.id())
}

/// 按清单组装一条命令：工作目录是应用自己的目录，环境变量分三层——
/// 继承的、编排器统一注入的（PATH、共享 cargo 缓存）、应用自己声明的。
fn command(app: &App, repo: &Path, argv: &[String]) -> Command {
    let program = &argv[0];
    // 相对路径按应用目录解析，`build/athena-c` 这种写法才能直接用。
    let resolved = if program.contains('/') || program.contains('\\') {
        app.dir.join(program)
    } else {
        PathBuf::from(program)
    };

    let mut command = Command::new(resolved);
    command.args(&argv[1..]);
    command.current_dir(&app.dir);

    let mut path = std::env::var_os("PATH")
        .map(|value| std::env::split_paths(&value).collect::<Vec<_>>())
        .unwrap_or_default();
    for entry in paths::extra_path_entries() {
        if !path.contains(&entry) {
            path.insert(0, entry);
        }
    }
    if let Ok(joined) = std::env::join_paths(path) {
        command.env("PATH", joined);
    }

    if std::env::var_os("CARGO_TARGET_DIR").is_none() {
        command.env("CARGO_TARGET_DIR", paths::shared_cargo_target(repo));
    }

    for (key, value) in &app.dev.env {
        if let Some(resolved) = value.resolve(&app.dir) {
            command.env(key, resolved);
        }
    }
    command
}

/// 停止：先关窗口进程，再收掉构建期留下的那一串。
pub fn stop(app: &App) -> Result<(), String> {
    let snapshot = ProcessSnapshot::take();
    let mut stopped = false;
    if let Some(pid) = snapshot.pid_of(app) {
        kill(pid);
        stopped = true;
    }
    let needle = format!("{}{}", app.dir.display(), std::path::MAIN_SEPARATOR);
    for (pid, process) in snapshot.system.processes() {
        if process
            .cmd()
            .iter()
            .any(|part| part.to_string_lossy().contains(&needle))
        {
            kill(pid.as_u32());
            stopped = true;
        }
    }
    if stopped {
        Ok(())
    } else {
        Err(format!("{} 本来就没在运行", app.title))
    }
}

fn kill(pid: u32) {
    #[cfg(windows)]
    {
        let _ = Command::new("taskkill")
            .args(["/PID", &pid.to_string(), "/T", "/F"])
            .status();
    }
    #[cfg(not(windows))]
    {
        let _ = Command::new("kill").arg(pid.to_string()).status();
    }
}

/// 把已经在跑的窗口叫到前面。
///
/// 这是三平台差距最大的一件事：macOS 有正经 API（这里借 osascript 用），
/// X11 靠 wmctrl/xdotool，**Wayland 出于安全根本不允许别的进程抢焦点**——
/// 那种情况下只能由应用自己响应"再启动一次"来 present 自己的窗口。
pub fn activate(app: &App) -> Result<(), String> {
    let snapshot = ProcessSnapshot::take();
    let Some(pid) = snapshot.pid_of(app) else {
        return Err(format!("{} 没有在运行的窗口", app.title));
    };

    if cfg!(target_os = "macos") {
        let script = format!(
            "tell application \"System Events\" to set frontmost of \
             (first process whose unix id is {pid}) to true"
        );
        return Command::new("osascript")
            .args(["-e", &script])
            .status()
            .map_err(|error| format!("osascript 没能执行：{error}"))
            .and_then(|status| {
                status
                    .success()
                    .then_some(())
                    .ok_or_else(|| "系统没让我们切换窗口".to_string())
            });
    }

    if cfg!(target_os = "linux") {
        if std::env::var_os("WAYLAND_DISPLAY").is_some() {
            return Err(format!(
                "{} 已经在运行，但 Wayland 不允许别的程序抢焦点，请自己切过去",
                app.title
            ));
        }
        for tool in ["wmctrl", "xdotool"] {
            let args: Vec<String> = match tool {
                "wmctrl" => vec!["-ia".into(), pid.to_string()],
                _ => vec![
                    "search".into(),
                    "--pid".into(),
                    pid.to_string(),
                    "windowactivate".into(),
                ],
            };
            if Command::new(tool)
                .args(&args)
                .status()
                .map(|status| status.success())
                .unwrap_or(false)
            {
                return Ok(());
            }
        }
        return Err(format!("{} 已经在运行，但没找到 wmctrl / xdotool", app.title));
    }

    Err(format!("{} 已经在运行", app.title))
}
