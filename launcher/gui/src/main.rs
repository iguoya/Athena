//! Athena 跨平台启动器（macOS / Ubuntu / Windows）。
//!
//! 界面在 `ui/launcher.slint`，执行逻辑全在 `launcher`——这里只做三件事：
//! 定时把状态刷进界面、把点击转成一次 open/stop、把构建进度显示出来。
//! 这样它和终端的 `launcher`、macOS 菜单栏版走的是同一条执行路径。
//!
//! 常驻形态是托盘。关窗口、debug 构建、测试阶段都不能把进程带走——
//! 只用 `window.run()` 会在最后一扇窗藏起来时退出，托盘图标跟着没了。

#![windows_subsystem = "windows"]

mod icon;
mod tray;

use std::net::{Ipv4Addr, TcpListener, TcpStream};
use std::rc::Rc;
use std::sync::mpsc::{channel, Receiver, Sender};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use launcher_core::{discover, discover_in, paths, runner, App, ProcessSnapshot, RunState};
use slint::{Color, Model, ModelRc, SharedString, VecModel};

use crate::tray::{Action, Tray};

/// 本机回环上占一个端口：第二份启动器连上来，等于请第一份把窗口举到前面。
const SINGLETON_PORT: u16 = 47821;

slint::include_modules!();

fn main() -> Result<(), Box<dyn std::error::Error>> {
    prefer_software_renderer();

    let Some(wake) = claim_singleton() else {
        // 已经有一份在托盘里：敲一下它，自己立刻退出，不要再开一个窗口。
        let _ = TcpStream::connect((Ipv4Addr::LOCALHOST, SINGLETON_PORT));
        return Ok(());
    };

    let Some(repo) = paths::locate_repo() else {
        eprintln!("找不到 Athena 仓库：设置 ATHENA_ROOT，或把启动器放在仓库里。");
        std::process::exit(1);
    };
    let apps: Arc<Vec<App>> = Arc::new(discover(&repo));
    if apps.is_empty() {
        eprintln!("{} 下没有找到任何 app.json", repo.join("apps").display());
        std::process::exit(1);
    }
    // 实践面板：跟学习应用区隔开的独立分区，数据源是 apps/practice/* 而
    // 不是 apps/*，复用同一套 discover_in()。这里可以为空——PocketCube
    // 之外还没有别的小项目时，界面按 practice-apps.length 隐藏整个分区。
    let practice_apps: Arc<Vec<App>> = Arc::new(discover_in(&repo.join("apps/practice")));
    // open/stop 按 id 找应用，两边的 app 都要能找到；tray 菜单仍然只列
    // 学习应用（apps），不把实践小项目也塞进去，两个界面各自的范围不同。
    let all_apps: Arc<Vec<App>> = Arc::new(
        apps.iter().chain(practice_apps.iter()).cloned().collect(),
    );

    // 常驻的是托盘，不是窗口：关掉窗口只是收起来，启动器还在状态栏待命。
    let tray = Rc::new(Tray::start(
        &apps
            .iter()
            .map(|app| (app.id.clone(), app.title.clone()))
            .collect::<Vec<_>>(),
    ));

    let window = LauncherWindow::new()?;
    window.set_ui_font(ui_font().into());
    {
        let handle = window.as_weak();
        window.window().on_close_requested(move || {
            if let Some(window) = handle.upgrade() {
                let _ = window.hide();
            }
            slint::CloseRequestResponse::HideWindow
        });
    }
    let entries: Rc<VecModel<AppEntry>> = Rc::new(VecModel::from(build_entries(&apps)));
    window.set_apps(ModelRc::from(entries.clone()));
    let practice_entries: Rc<VecModel<AppEntry>> =
        Rc::new(VecModel::from(build_entries(&practice_apps)));
    window.set_practice_apps(ModelRc::from(practice_entries.clone()));
    window.set_status("点一下就打开；已经在跑的只把窗口叫到前面。".into());
    window.set_links(ModelRc::new(VecModel::from(evolution_links(&apps))));

    // 构建输出从后台线程流回来：界面上要看得见"卡在哪一步"，
    // 沉默几十秒是"慢"的主观放大器。
    let (sender, receiver): (Sender<String>, Receiver<String>) = channel();
    let progress = Arc::new(Mutex::new(receiver));

    {
        let all_apps = all_apps.clone();
        let repo = repo.clone();
        let sender = sender.clone();
        window.on_open(move |id| open_app(&all_apps, id.as_str(), &repo, &sender));
    }

    {
        let all_apps = all_apps.clone();
        let sender = sender.clone();
        window.on_stop(move |id| stop_app(&all_apps, id.as_str(), &sender));
    }

    let clicks = slint::Timer::default();
    {
        let apps = apps.clone();
        let repo = repo.clone();
        let sender = sender.clone();
        let tray = tray.clone();
        let handle = window.as_weak();
        clicks.start(
            slint::TimerMode::Repeated,
            Duration::from_millis(200),
            move || {
                if wake.accept().is_ok() {
                    if let Some(window) = handle.upgrade() {
                        let _ = window.show();
                        bring_to_front();
                    }
                }
                for action in tray.drain() {
                    match action {
                        Action::Open(id) => open_app(&apps, &id, &repo, &sender),
                        Action::Stop(id) => stop_app(&apps, &id, &sender),
                        Action::Log(id) => {
                            let _ = sender.send(
                                paths::log_file(&id).display().to_string(),
                            );
                            open_log(&paths::log_file(&id));
                        }
                        Action::ShowWindow => {
                            if let Some(window) = handle.upgrade() {
                                let _ = window.show();
                                bring_to_front();
                            }
                        }
                        Action::Quit => slint::quit_event_loop().unwrap_or(()),
                    }
                }
            },
        );
    }

    // 状态从系统实况读，每两秒一次：应用被别处启动、崩溃、手动关掉，
    // 界面都跟得上，不靠启动器自己记账。
    let timer = slint::Timer::default();
    {
        let apps = apps.clone();
        let practice_apps = practice_apps.clone();
        let handle = window.as_weak();
        let progress = progress.clone();
        let tray = tray.clone();
        timer.start(
            slint::TimerMode::Repeated,
            Duration::from_secs(2),
            move || {
                let snapshot = ProcessSnapshot::take();
                let states: Vec<RunState> =
                    apps.iter().map(|app| snapshot.state(app)).collect();
                // 实践面板的状态刷新跟学习应用分开算：tray 只认识 apps，
                // 不该把 practice_apps 的状态也塞进 tray.update()。
                let practice_states: Vec<RunState> = practice_apps
                    .iter()
                    .map(|app| snapshot.state(app))
                    .collect();
                let latest = progress
                    .lock()
                    .ok()
                    .and_then(|receiver| receiver.try_iter().last());
                tray.update(
                    apps.iter()
                        .zip(&states)
                        .map(|(app, state)| match state {
                            RunState::Stopped => app.title.clone(),
                            other => format!("{} · {}", app.title, other.label()),
                        })
                        .collect(),
                );
                if let Some(window) = handle.upgrade() {
                    apply_states(&window.get_apps(), &states);
                    apply_states(&window.get_practice_apps(), &practice_states);
                    if let Some(line) = latest {
                        window.set_status(SharedString::from(line));
                    }
                }
            },
        );
    }

    // 启动时也要 activate：否则窗口留在启动它的那个 Space，屏幕上开着全屏
    // 应用时就像是没起来。事件循环必须用 until_quit：托盘走的是 tray-icon，
    // Slint 看不见它，最后一扇窗藏起来时普通 run() 会把进程结束掉。
    window.show()?;
    bring_to_front();
    slint::run_event_loop_until_quit()?;
    Ok(())
}

/// Windows 上 femtovg/OpenGL 在部分机器 `glGenBuffers` 没加载就崩。
/// 启动器只是一张列表，软件渲染够用；测试阶段更不能因为渲染后端把托盘带走。
fn prefer_software_renderer() {
    #[cfg(windows)]
    if std::env::var_os("SLINT_BACKEND").is_none() {
        std::env::set_var("SLINT_BACKEND", "winit-software");
    }
}

/// 占住回环端口。占不住说明已经有一份在跑，调用方去敲它然后退出。
fn claim_singleton() -> Option<TcpListener> {
    let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, SINGLETON_PORT)).ok()?;
    listener.set_nonblocking(true).ok()?;
    Some(listener)
}

/// 打开一个应用：已经在跑就把窗口叫到前面，没跑才构建并启动。
/// 托盘菜单和窗口里的点击走的是同一条路径。
fn open_app(apps: &[App], id: &str, repo: &std::path::Path, sender: &Sender<String>) {
    let Some(app) = apps.iter().find(|app| app.id == id) else {
        return;
    };
    if ProcessSnapshot::take().state(app) != RunState::Stopped {
        if let Err(message) = runner::activate(app) {
            let _ = sender.send(message);
        }
        return;
    }
    let _ = sender.send(format!("正在启动 {}…", app.title));
    let app = app.clone();
    let repo = repo.to_path_buf();
    let sender = sender.clone();
    std::thread::spawn(move || {
        if let Err(message) = runner::launch(&app, &repo, |line| {
            let _ = sender.send(trim(line));
        }) {
            let _ = sender.send(message);
        }
    });
}

fn stop_app(apps: &[App], id: &str, sender: &Sender<String>) {
    let Some(app) = apps.iter().find(|app| app.id == id) else {
        return;
    };
    let message = match runner::stop(app) {
        Ok(()) => format!("已停止 {}", app.title),
        Err(message) => message,
    };
    let _ = sender.send(message);
}

/// 用系统默认程序打开日志文件。
///
/// 以前这里按平台分叉成 open / explorer / xdg-open。打开一个文件是每个桌面
/// 系统都有的标准动作，交给把这层差异吃掉的库就行，不该在业务代码里留三条
/// 分支（ADR 0047）——而且手写的那版还漏了 xdg-open 缺席时的回退。
fn open_log(path: &std::path::Path) {
    let _ = opener::open(path);
}

/// 学科之间的历史演进关系（目前只有 C → C++）。
///
/// 只给出"谁从谁长出来"，具体画在哪由界面按当前列数算——窗口可以拉大，
/// 位置随时在变。只记真实存在的演进关系：算法、英语、数学各自独立，
/// 为了画面对称去连不存在的关系，是把装饰当成信息。
fn evolution_links(apps: &[App]) -> Vec<LinkSpec> {
    apps.iter()
        .enumerate()
        .filter_map(|(index, app)| {
            let origin = app.evolves_from.as_ref()?;
            let from = apps.iter().position(|other| &other.id == origin)?;
            Some(LinkSpec {
                from: from as i32,
                to: index as i32,
            })
        })
        .collect()
}

/// 应用自带的图标，按图块里的显示尺寸渲染（乘 2 供高分屏用）。
fn tile_icon(app: &App) -> Option<slint::Image> {
    icon::render(app.icon_file.as_ref()?, 60)
}

/// 学习应用面板和实践面板共用同一套图块数据构造，只是喂的 `apps` 来源
/// 不同（`discover(repo)` vs `discover_in(repo/apps/practice)）。
fn build_entries(apps: &[App]) -> Vec<AppEntry> {
    apps.iter()
        .map(|app| AppEntry {
            id: app.id.as_str().into(),
            title: app.title.as_str().into(),
            letter: app.letter.as_str().into(),
            accent: parse_color(&app.accent, &app.id).into(),
            icon: tile_icon(app).unwrap_or_default(),
            has_icon: tile_icon(app).is_some(),
            state: RunState::Stopped.label().into(),
            tint: Color::from_rgb_u8(0x8a, 0x8a, 0x8e).into(),
            running: false,
        })
        .collect()
}

/// 把一轮状态探测结果写回某个面板的图块模型；学习应用面板和实践面板各调
/// 一次，探测到的 `states` 顺序必须跟建模型时的 `apps` 顺序一致。
fn apply_states(model: &ModelRc<AppEntry>, states: &[RunState]) {
    for (index, state) in states.iter().enumerate() {
        if let Some(mut entry) = model.row_data(index) {
            entry.state = state.label().into();
            entry.tint = tint(*state).into();
            entry.running = *state != RunState::Stopped;
            model.set_row_data(index, entry);
        }
    }
}

/// 界面默认字体：必须覆盖简体中文。
///
/// Slint 的缺字回退按系统字体枚举顺序走。英文 Windows 上 Yu Gothic（日文）
/// 往往排在微软雅黑前面，于是「语」「习」「结」这类简体独有的字画不出来，
/// 标题变成「C 言程」「英 学」。点名一款带 GB 字形的 UI 字体，回退就不会
/// 先落到日文或繁体上。
fn ui_font() -> &'static str {
    #[cfg(windows)]
    {
        let fonts = std::env::var_os("WINDIR")
            .map(std::path::PathBuf::from)
            .unwrap_or_else(|| std::path::PathBuf::from(r"C:\Windows"))
            .join("Fonts");
        // YaHei UI 和 YaHei 都在 msyh.ttc 里；UI 那个度量更适合界面。
        if fonts.join("msyh.ttc").is_file() {
            return "Microsoft YaHei UI";
        }
        if fonts.join("NotoSansSC-VF.ttf").is_file() {
            return "Noto Sans SC";
        }
        if fonts.join("simhei.ttf").is_file() {
            return "SimHei";
        }
        "Segoe UI"
    }
    #[cfg(target_os = "macos")]
    {
        "PingFang SC"
    }
    #[cfg(not(any(windows, target_os = "macos")))]
    {
        "Noto Sans CJK SC"
    }
}

/// 把启动器自己拉到前台。
///
/// macOS 上光 show() 不够：窗口留在它最初出现的那个 Space，屏幕上正开着全屏
/// 应用时就等于没反应。activate 之后系统才会把焦点交给它。
#[cfg(target_os = "macos")]
fn bring_to_front() {
    use objc2_app_kit::NSApplication;
    use objc2_foundation::MainThreadMarker;

    if let Some(marker) = MainThreadMarker::new() {
        let application = NSApplication::sharedApplication(marker);
        #[allow(deprecated)]
        application.activateIgnoringOtherApps(true);
    }
}

#[cfg(not(target_os = "macos"))]
fn bring_to_front() {}

/// app.json 里的 `icon.accent`（`#RRGGBB`）。
///
/// 解析不了仍然退回中性灰——一个手滑的色值不该让启动器起不来——但**要把是谁、
/// 哪个值出的问题打出来**。静默吞掉的话，界面上只是多一块莫名其妙的灰，没人会
/// 想到去查 app.json 里少打了一位。
///
/// 整体解析，不再逐通道 `unwrap_or`：三个通道只坏一个时混出来的颜色似是而非，
/// 比纯灰更难察觉。`is_ascii` 是切片前的必要检查，否则多字节字符会在
/// `&hex[0..2]` 上 panic。
fn parse_color(text: &str, app_id: &str) -> Color {
    let hex = text.trim_start_matches('#');
    if hex.len() == 6 && hex.is_ascii() {
        if let (Ok(r), Ok(g), Ok(b)) = (
            u8::from_str_radix(&hex[0..2], 16),
            u8::from_str_radix(&hex[2..4], 16),
            u8::from_str_radix(&hex[4..6], 16),
        ) {
            return Color::from_rgb_u8(r, g, b);
        }
    }
    eprintln!("{app_id}：icon.accent「{text}」不是 #RRGGBB，暂用中性灰");
    Color::from_rgb_u8(0x5a, 0x62, 0x70)
}

fn tint(state: RunState) -> Color {
    match state {
        RunState::Ready => Color::from_rgb_u8(0x34, 0xc7, 0x59),
        RunState::Starting => Color::from_rgb_u8(0xff, 0x9f, 0x0a),
        RunState::Stopped => Color::from_rgb_u8(0x8a, 0x8a, 0x8e),
    }
}

/// 构建工具爱用回车和 ANSI 颜色画进度条，直接塞进界面会是一团乱码。
fn trim(line: &str) -> String {
    let visible = line.rsplit('\r').next().unwrap_or(line);
    let mut out = String::with_capacity(visible.len());
    let mut chars = visible.chars();
    while let Some(character) = chars.next() {
        if character == '\u{1b}' {
            for escape in chars.by_ref() {
                if escape.is_ascii_alphabetic() {
                    break;
                }
            }
            continue;
        }
        out.push(character);
    }
    out.trim().chars().take(90).collect()
}
