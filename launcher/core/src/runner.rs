//! 执行清单里的 dev 声明：构建、启动、探测状态、停止、把窗口叫到前面。

use std::io::{BufRead, Read, Write};
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
    /// 给人看的一行字。措辞随时可能改，**不要拿它当跨进程的协议**。
    pub fn label(self) -> &'static str {
        match self {
            RunState::Stopped => "未运行",
            RunState::Starting => "启动中…",
            RunState::Ready => "运行中",
        }
    }

    /// 机器读的稳定标识。菜单栏版原来是把 label() 的中文反解析回枚举的，
    /// 这里改一个字那边就会静默把所有应用显示成"未运行"——接口钉在这一组
    /// 不会变的值上（ADR 0048）。
    pub fn key(self) -> &'static str {
        match self {
            RunState::Stopped => "stopped",
            RunState::Starting => "starting",
            RunState::Ready => "ready",
        }
    }
}

/// 一次性把全部进程读出来，再判断每个应用的状态：各应用只扫一遍进程表。
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
    fn is_busy(&self, app: &App) -> bool {
        self.system.processes().values().any(|process| {
            command_line_belongs_to(
                &app.dir,
                process.cmd().iter().map(|part| part.to_string_lossy()),
            )
        })
    }

    /// 就绪的判据只有一个：**窗口进程在**。
    ///
    /// dev server 通不算就绪——Tauri 的 vite 秒开，而 Rust 壳还要编几十秒，
    /// 这段时间里端口是通的但屏幕上什么都没有。http 探测只用来回答另一个问题：
    /// 窗口已经出来了，但页面是不是还没连上。
    pub fn state(&self, app: &App) -> RunState {
        let window_present = self.window_pid(app).is_some();
        // 窗口还没出来时不去连端口：停着的应用不该每两秒探一次 localhost。
        let http_up = match &app.dev.ready {
            ReadySpec::Http(url) if window_present => reachable(url),
            _ => false,
        };
        classify_run_state(
            window_present,
            self.is_busy(app),
            &app.dev.ready,
            http_up,
        )
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

/// 命令行里出现应用目录，才算这个构建进程属于它。
///
/// 末尾必须带分隔符：`apps/c` 是 `apps/cpp` 的前缀，少了它两个应用会互相误判。
fn command_line_belongs_to(
    dir: &Path,
    parts: impl IntoIterator<Item = impl AsRef<str>>,
) -> bool {
    let needle = format!("{}{}", dir.display(), std::path::MAIN_SEPARATOR);
    parts.into_iter().any(|part| part.as_ref().contains(&needle))
}

/// 窗口在不在、构建进程在不在、端口通不通，三者不能折成「有动静就算运行中」。
fn classify_run_state(
    window_present: bool,
    busy: bool,
    ready: &ReadySpec,
    http_up: bool,
) -> RunState {
    if window_present {
        return match ready {
            ReadySpec::Http(_) if !http_up => RunState::Starting,
            _ => RunState::Ready,
        };
    }
    if busy {
        RunState::Starting
    } else {
        RunState::Stopped
    }
}

fn emit(log: &mut impl Write, report: &mut impl FnMut(&str), line: &str) {
    let _ = writeln!(log, "{line}");
    report(line);
}

/// 跑完一步准备，把它的标准输出和标准错误按行写进日志，并交给 `report`。
fn run_prepare(
    mut command: Command,
    log: &mut impl Write,
    mut report: impl FnMut(&str),
) -> Result<std::process::ExitStatus, std::io::Error> {
    command.stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = command.spawn()?;
    let stdout = child.stdout.take().expect("stdout piped");
    let stderr = child.stderr.take().expect("stderr piped");
    let (sender, receiver) = std::sync::mpsc::channel();
    let err_sender = sender.clone();
    std::thread::spawn(move || forward_output(stdout, sender));
    std::thread::spawn(move || forward_output(stderr, err_sender));
    for line in receiver {
        emit(log, &mut report, &line);
    }
    child.wait()
}

/// 按字节读到换行再转成字符串。非法 UTF-8 换成替换符，不因此停掉后面的行。
fn forward_output(reader: impl Read, sender: std::sync::mpsc::Sender<String>) {
    let mut reader = std::io::BufReader::new(reader);
    let mut buffer = Vec::new();
    loop {
        buffer.clear();
        match reader.read_until(b'\n', &mut buffer) {
            Ok(0) => break,
            Ok(_) => {
                if buffer.last() == Some(&b'\n') {
                    buffer.pop();
                }
                if buffer.last() == Some(&b'\r') {
                    buffer.pop();
                }
                let line = String::from_utf8_lossy(&buffer).into_owned();
                if sender.send(line).is_err() {
                    break;
                }
            }
            Err(_) => break,
        }
    }
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

    emit(&mut log, &mut report, &format!("===== 启动 {} =====", app.id));

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
        emit(&mut log, &mut report, &format!("[准备] {label}"));
        // 准备步骤的原文也进同一份日志，并经 report 回到界面。
        // 继承父进程时，托盘没有控制台，cmake / cargo 的输出会丢。
        let status = run_prepare(command(app, repo, &step.run), &mut log, &mut report)
            .map_err(|error| format!("{label} 没能执行：{error}"))?;
        if !status.success() {
            let message = format!("{label} 失败（退出码 {:?}）", status.code());
            emit(&mut log, &mut report, &message);
            return Err(message);
        }
    }

    emit(
        &mut log,
        &mut report,
        &format!("[启动] {}", app.dev.run.join(" ")),
    );
    // 长驻命令的 stdin 不能继承编排器：`launcher open` 返回后父进程退出，
    // 子进程会读到 EOF。Flutter 的 resident runner 因此整段退出，启动器只能
    // 每次冷编译。接到 /dev/null，热重载由各应用自己的监视器负责。
    let stdout = log
        .try_clone()
        .map_err(|error| format!("日志复制失败：{error}"))?;
    let stderr = log
        .try_clone()
        .map_err(|error| format!("日志复制失败：{error}"))?;
    let mut spawning = command(app, repo, &app.dev.run);
    spawning
        .stdin(Stdio::null())
        .stdout(Stdio::from(stdout))
        .stderr(Stdio::from(stderr));

    // 长驻进程还要自立门户：留在调用者的进程组里，`launcher open` 一返回，
    // shell 收尾时按进程组清理就把应用一起带走了——终端里打开的应用活不过
    // 那条命令，而从菜单栏打开的能活，因为那边的调用者是常驻进程。终端入口
    // 是 README 明说支持的用法（ADR 0046），不能只在 GUI 下成立。
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        spawning.process_group(0);
    }

    let child = spawning
        .spawn()
        .map_err(|error| format!("{} 启动失败：{error}", app.title))?;
    Ok(child.id())
}

/// 按清单组装一条命令：工作目录是应用自己的目录，环境变量分三层——
/// 继承的、编排器统一注入的（PATH、共享 cargo 缓存）、应用自己声明的。
fn command(app: &App, repo: &Path, argv: &[String]) -> Command {
    let program = &argv[0];

    // PATH 先补齐再用：从桌面环境启动时它很短，下面解析程序名靠的也是这一份。
    let mut path = std::env::var_os("PATH")
        .map(|value| std::env::split_paths(&value).collect::<Vec<_>>())
        .unwrap_or_default();
    for entry in paths::extra_path_entries(app) {
        if !path.contains(&entry) {
            path.insert(0, entry);
        }
    }
    let joined = std::env::join_paths(&path).ok();

    // 相对路径按应用目录解析，`build/athena-c` 这种写法才能直接用。
    let resolved = if program.contains('/') || program.contains('\\') {
        app.dir.join(program)
    } else {
        // 裸名交给 which 解析。Windows 上 npm 实际是 npm.cmd，而 CreateProcess
        // 只会替没有扩展名的程序补 .exe，直接拿裸名 spawn 会报"找不到程序"——
        // 三个 Tauri 应用的 dev.run 全在这上面。which 按各平台自己的规则查找
        // （Windows 走 PATHEXT），不必自己写平台分支（ADR 0047）。
        which::which_in(program, joined.clone(), &app.dir)
            .unwrap_or_else(|_| PathBuf::from(program))
    };

    let mut command = Command::new(resolved);
    command.args(&argv[1..]);
    command.current_dir(&app.dir);

    // 编排器自己是 GUI 子系统、没有控制台；它拉起的子进程只要是控制台子
    // 系统的程序（cmake、ninja、meson、python……几乎所有构建工具都是），
    // Windows 就会当场新分配一个控制台窗口，一闪一闪地冒出来——prepare
    // 里每一步都会冒一个，构建完了才消失。CREATE_NO_WINDOW 让子进程直接
    // 不分配控制台，stdout/stderr 走的是下面重定向的管道/文件句柄，不需要
    // 控制台也能正常工作；对最终要跑起来的 GUI 应用本身同样适用——不管它
    // 自己编译成的是不是控制台子系统，都不会再弹窗口。
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        command.creation_flags(CREATE_NO_WINDOW);
    }

    if let Some(joined) = joined {
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
    for (pid, process) in snapshot.system.processes() {
        if command_line_belongs_to(
            &app.dir,
            process.cmd().iter().map(|part| part.to_string_lossy()),
        ) {
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
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        let _ = Command::new("taskkill")
            .args(["/PID", &pid.to_string(), "/T", "/F"])
            .creation_flags(CREATE_NO_WINDOW)
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

    activate_windows(pid, &app.title)
}

/// Windows：按 pid 找到它的可见顶层窗口，还原并提到最前。
///
/// 没有跨平台库能做这件事——把别人的窗口抢到前台，各系统的策略本就不同
/// （Wayland 干脆禁止）。所以这里是 ADR 0047 说的「这个平台真的提供了别处没有
/// 的能力」那一类，分支关在本函数内。
///
/// SetForegroundWindow 有前台锁：调用方不在前台时系统可能只闪任务栏图标而不
/// 真正切换。启动器自己此刻通常是前台（用户刚点了它），所以一般能成；不成也
/// 只是少切一次窗口，不影响别的。
#[cfg(windows)]
fn activate_windows(pid: u32, title: &str) -> Result<(), String> {
    use windows::core::BOOL;
    use windows::Win32::Foundation::{HWND, LPARAM};
    use windows::Win32::UI::WindowsAndMessaging::{
        EnumWindows, GetWindowThreadProcessId, IsIconic, IsWindowVisible, SetForegroundWindow,
        ShowWindow, SW_RESTORE,
    };

    struct Hunt {
        pid: u32,
        found: Option<HWND>,
    }

    // 回调里只做筛选：属于目标进程、且是可见的顶层窗口。找到就停止枚举。
    unsafe extern "system" fn visit(hwnd: HWND, lparam: LPARAM) -> BOOL {
        let hunt = unsafe { &mut *(lparam.0 as *mut Hunt) };
        let mut owner = 0u32;
        unsafe { GetWindowThreadProcessId(hwnd, Some(&mut owner)) };
        if owner == hunt.pid && unsafe { IsWindowVisible(hwnd) }.as_bool() {
            hunt.found = Some(hwnd);
            return BOOL(0); // 停止枚举
        }
        BOOL(1) // 继续找下一个
    }

    let mut hunt = Hunt { pid, found: None };
    // EnumWindows 在回调返回 FALSE 时整体返回 Err，那正是「已找到」的正常路径，
    // 所以这里不看它的返回值，只看 hunt.found。
    let _ = unsafe { EnumWindows(Some(visit), LPARAM(&mut hunt as *mut Hunt as isize)) };

    let Some(hwnd) = hunt.found else {
        return Err(format!("{title} 已经在运行，但没找到它的窗口"));
    };
    unsafe {
        if IsIconic(hwnd).as_bool() {
            let _ = ShowWindow(hwnd, SW_RESTORE);
        }
        if SetForegroundWindow(hwnd).as_bool() {
            Ok(())
        } else {
            Err(format!("{title} 已经在运行，但系统没让我们切换窗口"))
        }
    }
}

#[cfg(not(windows))]
fn activate_windows(_pid: u32, title: &str) -> Result<(), String> {
    Err(format!("{title} 已经在运行"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn c_directory_does_not_claim_cpp_command() {
        let apps = PathBuf::from("repo").join("apps");
        let c_dir = apps.join("c");
        let cpp_command = apps.join("cpp").join("src-tauri").display().to_string();
        assert!(
            !command_line_belongs_to(&c_dir, [cpp_command.as_str()]),
            "apps/c 不能因为字符串前缀吃掉 apps/cpp"
        );
        let own = c_dir.join("node_modules").display().to_string();
        assert!(command_line_belongs_to(&c_dir, [own.as_str()]));
    }

    #[test]
    fn open_port_without_window_is_not_ready() {
        let http = ReadySpec::Http("http://127.0.0.1:1420".into());
        assert_eq!(
            classify_run_state(false, true, &http, true),
            RunState::Starting
        );
        assert_eq!(
            classify_run_state(false, false, &http, true),
            RunState::Stopped
        );
        assert_eq!(
            classify_run_state(true, false, &http, false),
            RunState::Starting
        );
        assert_eq!(
            classify_run_state(true, false, &http, true),
            RunState::Ready
        );
        assert_eq!(
            classify_run_state(true, false, &ReadySpec::Process, false),
            RunState::Ready
        );
    }

    #[test]
    fn prepare_output_reaches_the_log_and_the_report() {
        let mut command = Command::new(if cfg!(windows) { "cmd" } else { "echo" });
        if cfg!(windows) {
            command.args(["/c", "echo prepare-line"]);
            #[cfg(windows)]
            {
                use std::os::windows::process::CommandExt;
                command.creation_flags(0x0800_0000);
            }
        } else {
            command.arg("prepare-line");
        }
        let mut log = Vec::new();
        let mut reported = Vec::new();
        let status = run_prepare(command, &mut log, |line| reported.push(line.to_string()))
            .expect("准备步骤要能跑起来");
        assert!(status.success());
        let text = String::from_utf8(log).expect("日志是 UTF-8");
        assert!(text.contains("prepare-line"), "{text}");
        assert!(reported.iter().any(|line| line.contains("prepare-line")));
    }
}
