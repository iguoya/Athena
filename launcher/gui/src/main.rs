//! Athena 跨平台启动器（macOS / Ubuntu / Windows）。
//!
//! 界面在 `ui/launcher.slint`，执行逻辑全在 `launcher`——这里只做四件事：
//! 监听清单文件的变化、定时把状态刷进界面、把点击转成一次 open/stop、把构建
//! 进度显示出来。这样它和终端的 `launcher`、macOS 菜单栏版走的是同一条执行路径。
//!
//! 清单是热的（ADR 0001）：仓库里新增、删除、修改 `app.json`，文件通知醒来，
//! 去抖一秒后重扫清单、比指纹，真的变了才重建界面与托盘。常驻形态是托盘。
//! 关窗口、debug 构建、测试阶段都不能把进程带走——只用 `window.run()` 会在
//! 最后一扇窗藏起来时退出，托盘图标跟着没了。

#![windows_subsystem = "windows"]

mod app_icon;
mod icon;
#[cfg(windows)]
mod autostart;
mod tray;

use std::cell::RefCell;
use std::net::{Ipv4Addr, TcpListener, TcpStream};
use std::path::PathBuf;
use std::rc::Rc;
use std::sync::mpsc::{channel, Receiver, Sender};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

use launcher_core::{
    discover_in, fingerprint, mindmap, paths, runner, App, ProcessSnapshot, RunState,
};
use slint::{Color, Model, ModelRc, SharedString, VecModel};

use crate::tray::{Action, Tray};

/// 本机回环上占一个端口：第二份启动器连上来，等于请第一份把窗口举到前面。
const SINGLETON_PORT: u16 = 47821;

/// 文件通知到重扫之间的静默窗：保存文件常是「写临时文件再改名」的原子替换，
/// 事件成串来，等它安静下来才重扫，一连串变更收敛成一次重建。
const RESCAN_QUIET: Duration = Duration::from_secs(1);

/// 文件通知的兜底节拍：个别环境（网络盘、事件缓冲溢出）监听会静默失效，
/// 每分钟摸一次底。重扫便宜、指纹没变就不动界面——这是保险丝，不是节拍。
const RESCAN_FALLBACK: Duration = Duration::from_secs(60);

slint::include_modules!();

/// 两个面板共用一份可热换的清单：学习应用、实践项目，外加 open/stop 查找用的
/// 合集。主线程独占——所有消费点（点击回调、定时器）都在主线程，`Rc` 就够，
/// 不必 `Arc`。
struct Catalog {
    /// 两个发现根，文件监听订阅它们就够了（`CatalogWatcher::resync` 用）。
    roots: Vec<PathBuf>,
    /// 面板可见的应用（`hidden` 已滤掉，ADR 0093）：思维导图的输入。
    visible: Vec<App>,
    /// 全量清单（含 hidden）：open/stop 按 id 找应用用——隐藏不是下线。
    all: Vec<App>,
}

impl Catalog {
    fn load(repo: &std::path::Path) -> Self {
        let mut everything = launcher_core::discover(repo);
        everything.extend(discover_in(&repo.join("practice")));
        let visible: Vec<App> = everything.iter().filter(|app| !app.hidden).cloned().collect();
        Self {
            roots: vec![repo.join("subjects"), repo.join("practice")],
            visible,
            all: everything,
        }
    }

    fn fingerprint(&self) -> String {
        fingerprint(&self.visible)
    }
}

/// 主线程递给探测线程的清单快照。指纹跟着走：探测结果按指纹对号入座，
/// 清单换岗瞬间产出的旧结果直接丢弃，状态点不会画错行。
type CatalogProbe = (Vec<App>, String);
/// 探测线程交回的一轮结果：指纹 + 可见应用的状态（ADR 0093：实践面板已并入）。
type CatalogStates = (String, Vec<RunState>);

/// 被动通知（ADR 0001）：订阅发现根和应用目录本身，`app.json`、`icon.svg`、
/// 应用目录的增删都会来一条事件。不递归订阅是刻意的——构建产物、教学内容的
/// 海量文件改动不在订阅范围里， Flutter 编一次 Windows 也不会吵醒启动器。
/// watcher 掉出作用域监听即停，所以整个留在 struct 里。
struct CatalogWatcher {
    watcher: notify::RecommendedWatcher,
    watched: Vec<PathBuf>,
}

impl CatalogWatcher {
    /// 事件不分种类：任何一条都只意味着「清单可能变了」，主线程去抖后重扫、
    /// 比指纹，自会分辨真假。
    fn new(sender: Sender<()>) -> notify::Result<Self> {
        let watcher = notify::recommended_watcher(
            move |event: Result<notify::Event, notify::Error>| {
                if event.is_ok() {
                    let _ = sender.send(());
                }
            },
        )?;
        Ok(Self {
            watcher,
            watched: Vec::new(),
        })
    }

    /// 订阅集合对齐当前清单：发现根 + 每个应用目录。只在差集上动手——
    /// 重复 watch 和 unwatch 不存在的路径都会报错。
    fn resync(&mut self, catalog: &Catalog) {
        use notify::Watcher;
        let mut wanted = catalog.roots.clone();
        wanted.extend(catalog.all.iter().map(|app| app.dir.clone()));

        for path in &self.watched {
            if !wanted.contains(path) {
                let _ = self.watcher.unwatch(path);
            }
        }
        for path in &wanted {
            if !self.watched.contains(path)
                && self.watcher.watch(path, notify::RecursiveMode::NonRecursive).is_ok()
            {
                self.watched.push(path.clone());
            }
        }
        self.watched.retain(|path| wanted.contains(path));
    }
}

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
    // 实践面板：跟学习应用区隔开的独立分区，数据源是 practice/* 而
    // 不是 subjects/*，复用同一套 discover_in()。这里可以为空——PocketCube
    // 之外还没有别的小项目时，界面按 practice-apps.length 隐藏整个分区。
    // open/stop 按 id 找应用，两边的 app 都要能找到；tray 菜单仍然只列
    // 学习应用（subjects），不把实践小项目也塞进去，两个界面各自的范围不同。
    let catalog = Rc::new(RefCell::new(Catalog::load(&repo)));
    if catalog.borrow().visible.is_empty() {
        eprintln!(
            "{} 下没有找到任何 app.json",
            repo.join("subjects").display()
        );
        std::process::exit(1);
    }

    // 文件监听建不起来就如实降级：界面照常用，只是清单不再自动刷新。
    let (watcher_tx, watcher_rx) = channel();
    let mut watcher = match CatalogWatcher::new(watcher_tx) {
        Ok(watcher) => Some(watcher),
        Err(error) => {
            eprintln!("文件监听建不起来，清单不再自动刷新：{error}");
            None
        }
    };

    let tray = Rc::new(Tray::start(
        &catalog
            .borrow()
            .visible
            .iter()
            .map(|app| (app.id.clone(), app.title.clone()))
            .collect::<Vec<_>>(),
    ));

    app_icon::prepare();
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
    window.set_status("点一下就打开；已经在跑的只把窗口叫到前面。".into());
    // 启动铺界面和热刷新铺界面走同一个入口，两条路径铺出来的东西没有差别。
    apply_catalog(&window, &tray, &catalog.borrow());
    let mut fingerprint = catalog.borrow().fingerprint();
    if let Some(watcher) = watcher.as_mut() {
        watcher.resync(&catalog.borrow());
    }

    // 构建输出从后台线程流回来：界面上要看得见"卡在哪一步"，
    // 沉默几十秒是"慢"的主观放大器。
    let (sender, receiver): (Sender<String>, Receiver<String>) = channel();
    let progress = Arc::new(Mutex::new(receiver));

    // 状态探测放后台线程：一轮快则几百毫秒、慢则数秒（Windows 读进程命令行
    // 是固有成本），留在主线程就是周期性「未响应」。探测慢半拍无所谓，状态
    // 点晚几秒变色而已。清单热换后把新清单递过去，探测自动跟着走。
    let (probe_tx, probe_rx) = channel::<CatalogProbe>();
    let (states_tx, states_rx) = channel::<CatalogStates>();
    {
        let initial = {
            let catalog = catalog.borrow();
            (catalog.visible.clone(), catalog.fingerprint())
        };
        std::thread::spawn(move || {
            let mut snapshot = ProcessSnapshot::take();
            let mut current = initial;
            loop {
                while let Ok(fresh) = probe_rx.try_recv() {
                    current = fresh;
                }
                snapshot.refresh();
                let states = snapshot.states(&current.0);
                let _ = states_tx.send((current.1.clone(), states));
                std::thread::sleep(Duration::from_secs(2));
            }
        });
    }

    {
        let catalog = catalog.clone();
        let repo = repo.clone();
        let sender = sender.clone();
        window.on_open(move |id| {
            open_app(catalog.borrow().all.as_slice(), id.as_str(), &repo, &sender)
        });
    }

    {
        let catalog = catalog.clone();
        let sender = sender.clone();
        window.on_stop(move |id| {
            stop_app(catalog.borrow().all.as_slice(), id.as_str(), &sender)
        });
    }

    let clicks = slint::Timer::default();
    {
        let catalog = catalog.clone();
        let repo = repo.clone();
        let sender = sender.clone();
        let tray = tray.clone();
        let handle = window.as_weak();
        let probe_tx = probe_tx.clone();
        let mut dirty_since: Option<Instant> = None;
        let mut last_scan = Instant::now();
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
                // 清单热刷新（ADR 0001）：文件通知只标「可能变了」，静默一秒
                // 才重扫；重扫完比指纹，真的变了才重建界面与托盘。
                if watcher_rx.try_iter().count() > 0 {
                    dirty_since = Some(Instant::now());
                }
                let dirty_settled =
                    dirty_since.is_some_and(|since| since.elapsed() >= RESCAN_QUIET);
                let fallback_due =
                    dirty_since.is_none() && last_scan.elapsed() >= RESCAN_FALLBACK;
                if dirty_settled || fallback_due {
                    dirty_since = None;
                    last_scan = Instant::now();
                    reload_if_changed(
                        &repo, &catalog, &mut fingerprint, &handle, &tray, watcher.as_mut(),
                        &probe_tx,
                    );
                }
                for action in tray.drain() {
                    match action {
                        Action::Open(id) => {
                            open_app(catalog.borrow().all.as_slice(), &id, &repo, &sender)
                        }
                        Action::Stop(id) => {
                            stop_app(catalog.borrow().all.as_slice(), &id, &sender)
                        }
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
                        #[cfg(windows)]
                        Action::ToggleAutostart => {
                            match autostart::toggle() {
                                Ok(true) => {
                                    let _ = sender.send("已开启开机自启".into());
                                }
                                Ok(false) => {
                                    let _ = sender.send("已关闭开机自启".into());
                                }
                                Err(message) => {
                                    let _ = sender.send(message);
                                }
                            }
                            // 勾选状态以注册表为准，翻转之后重画菜单把它画准。
                            tray.rebuild(
                                &catalog
                                    .borrow()
                                    .visible
                                    .iter()
                                    .map(|app| (app.id.clone(), app.title.clone()))
                                    .collect::<Vec<_>>(),
                            );
                        }
                        #[cfg(not(windows))]
                        Action::ToggleAutostart => {}
                    }
                }
            },
        );
    }

    // 界面从后台探测线程收状态，每两秒看一眼最新一批：应用被别处启动、
    // 崩溃、手动关掉，界面都跟得上，不靠启动器自己记账。
    let timer = slint::Timer::default();
    {
        let catalog = catalog.clone();
        let handle = window.as_weak();
        let progress = progress.clone();
        let tray = tray.clone();
        let mut last_tooltip = String::new();
        timer.start(
            slint::TimerMode::Repeated,
            Duration::from_secs(2),
            move || {
                let latest = progress
                    .lock()
                    .ok()
                    .and_then(|receiver| receiver.try_iter().last());
                // 只要与当前清单对上号的结果：清单换岗瞬间的旧批次直接丢弃。
                let print_now = catalog.borrow().fingerprint();
                let Some((_, states)) = states_rx
                    .try_iter()
                    .last()
                    .filter(|(print, _)| *print == print_now)
                else {
                    if let Some(line) = latest {
                        if let Some(window) = handle.upgrade() {
                            window.set_status(SharedString::from(line));
                        }
                    }
                    return;
                };
                let catalog = catalog.borrow();
                tray.update(
                    catalog
                        .visible
                        .iter()
                        .zip(&states)
                        .map(|(app, state)| match state {
                            RunState::Stopped => app.title.clone(),
                            other => format!("{} · {}", app.title, other.label()),
                        })
                        .collect(),
                );
                // 悬浮提示顺带报家底：面板上多少个应用、几个在跑。变了才动托盘。
                let running = states
                    .iter()
                    .filter(|state| **state != RunState::Stopped)
                    .count();
                let tooltip = format!(
                    "Athena · {} 个应用 · {} 个在跑",
                    catalog.visible.len(),
                    running
                );
                if tooltip != last_tooltip {
                    tray.set_tooltip(&tooltip);
                    last_tooltip = tooltip;
                }
                if let Some(window) = handle.upgrade() {
                    apply_states(&window.get_apps(), &states);
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
    // 底层窗口要等事件循环转起来才拿得到，所以排进循环的第一拍。
    {
        let handle = window.as_weak();
        slint::invoke_from_event_loop(move || {
            if let Some(window) = handle.upgrade() {
                app_icon::install(window.window());
            }
        })?;
    }
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

/// 把一份清单铺进界面与托盘：两个图块模型、思维导图、托盘菜单。启动铺界面
/// 和热刷新铺界面走同一个入口，两条路径铺出来的东西没有差别（ADR 0001）。
fn apply_catalog(window: &LauncherWindow, tray: &Tray, catalog: &Catalog) {
    let map = mindmap::layout(&catalog.visible);
    window.set_apps(ModelRc::from(Rc::new(VecModel::from(map_entries(
        &catalog.visible,
        &map,
    )))));
    // 实践面板已取消（ADR 0093）：practice 应用按 parent 声明画进思维导图的
    // 挂靠层，网格永远置空——slint 按 length 显隐，整块分区自然不再出现。
    window.set_practice_apps(ModelRc::from(Rc::new(VecModel::from(Vec::<AppEntry>::new()))));
    set_mind_map(window, &map);
    tray.rebuild(
        &catalog
            .visible
            .iter()
            .map(|app| (app.id.clone(), app.title.clone()))
            .collect::<Vec<_>>(),
    );
}

/// 重扫一遍清单：指纹没变就什么都不动，变了才整条重建界面、托盘和订阅集合。
/// 文件通知与兜底节拍都汇到这里，没有变化的重扫对界面完全不可见。
fn reload_if_changed(
    repo: &std::path::Path,
    catalog: &Rc<RefCell<Catalog>>,
    fingerprint: &mut String,
    handle: &slint::Weak<LauncherWindow>,
    tray: &Tray,
    watcher: Option<&mut CatalogWatcher>,
    probe_tx: &Sender<CatalogProbe>,
) {
    let fresh = Catalog::load(repo);
    let fresh_print = fresh.fingerprint();
    if fresh_print == *fingerprint {
        return;
    }
    // 探测线程用克隆对号入座；本体先写回指纹再换清单。
    *fingerprint = fresh_print.clone();
    *catalog.borrow_mut() = fresh;
    // 给探测线程递新清单：状态判定自动跟着走，指纹让旧批次作废。
    let _ = probe_tx.send((catalog.borrow().visible.clone(), fresh_print));
    if let Some(window) = handle.upgrade() {
        apply_catalog(&window, tray, &catalog.borrow());
    }
    if let Some(watcher) = watcher {
        watcher.resync(&catalog.borrow());
    }
}

/// 把 core 算好的思维导图布局原样填进界面（ADR 0083）。
///
/// 位置、分组、连线和同心圈都在 `launcher_core::mindmap` 里算，那里有单元测试；
/// 这里不做任何几何，只做类型转换。
fn set_mind_map(window: &LauncherWindow, map: &mindmap::MindMap) {
    let positions: Vec<NodePos> = map
        .nodes
        .iter()
        .map(|node| NodePos { x: node.at.x, y: node.at.y })
        .collect();
    let groups: Vec<GroupSpec> = map
        .groups
        .iter()
        .map(|group| GroupSpec {
            name: group.name.as_str().into(),
            color: parse_color(group.color, "思维导图"),
            x: group.at.x,
            y: group.at.y,
            w: group.width,
        })
        .collect();
    let links: Vec<MapLink> = map.links.iter().map(map_link).collect();
    // 界面从外到内叠着画椭圆（外层先铺底），布局给的是从内到外，这里反转。
    let rings: Vec<RingSpec> = map
        .rings
        .iter()
        .rev()
        .map(|(a, b)| RingSpec { rx: *a, ry: *b })
        .collect();
    window.set_positions(ModelRc::new(VecModel::from(positions)));
    window.set_groups(ModelRc::new(VecModel::from(groups)));
    window.set_map_links(ModelRc::new(VecModel::from(links)));
    window.set_rings(ModelRc::new(VecModel::from(rings)));
    window.set_map_width(map.width);
    window.set_map_height(map.height);
    window.set_center_x(map.center.x);
    window.set_center_y(map.center.y);
}

/// 一条连线：几何照搬布局，透明度按种类定——虎头到领域的最淡，演进线不透明，
/// 相关线比分支略深，免得和分支线混成一片。
fn map_link(link: &mindmap::Link) -> MapLink {
    let (kind, alpha) = match link.kind {
        mindmap::LinkKind::Hub => (0, 0x66),
        mindmap::LinkKind::Branch => (1, 0x88),
        mindmap::LinkKind::Evolves => (2, 0xff),
        mindmap::LinkKind::Related => (3, 0xc0),
        mindmap::LinkKind::Attach => (4, 0xe6),
        // 引用挂靠比主挂靠淡一档：一眼分得出哪条是本体、哪条是引用（ADR 0116）。
        mindmap::LinkKind::Reference => (5, 0x8c),
    };
    let base = parse_color(link.color, "思维导图");
    let [a, b, c] = link.arrow.unwrap_or([link.to; 3]);
    MapLink {
        kind,
        color: Color::from_argb_u8(alpha, base.red(), base.green(), base.blue()),
        x0: link.from.x,
        y0: link.from.y,
        cx1: link.c1.x,
        cy1: link.c1.y,
        cx2: link.c2.x,
        cy2: link.c2.y,
        x1: link.to.x,
        y1: link.to.y,
        has_arrow: link.arrow.is_some(),
        ax: a.x,
        ay: a.y,
        bx: b.x,
        by: b.y,
        cx: c.x,
        cy: c.y,
    }
}

/// 应用自带的图标，按图块里的显示尺寸（56px）渲染，乘 2 供高分屏用。
fn tile_icon(app: &App) -> Option<slint::Image> {
    icon::render(app.icon_file.as_ref()?, 112)
}

/// 思维导图的图块与 `map.nodes` 一一对应：本体按清单顺序在前，引用节点在后（ADR 0116）。
/// 引用节点复制本体的图块数据——同一个应用、同一个图标，点开和停止用的也是同一个 id。
fn map_entries(apps: &[App], map: &mindmap::MindMap) -> Vec<AppEntry> {
    let mut entries = build_entries(apps);
    let references: Vec<AppEntry> = map.nodes[apps.len()..]
        .iter()
        .filter_map(|node| entries.iter().find(|entry| entry.id.as_str() == node.id).cloned())
        .collect();
    entries.extend(references);
    entries
}

/// 学习应用面板和实践面板共用同一套图块数据构造，只是喂的 `apps` 来源
/// 不同（`discover(repo)` vs `discover_in(repo/practice)）。
fn build_entries(apps: &[App]) -> Vec<AppEntry> {
    apps.iter()
        .map(|app| (app, tile_icon(app)))
        .map(|(app, icon)| AppEntry {
            id: app.id.as_str().into(),
            title: app.title.as_str().into(),
            letter: app.letter.as_str().into(),
            accent: parse_color(&app.accent, &app.id).into(),
            has_icon: icon.is_some(),
            icon: icon.unwrap_or_default(),
            tint: Color::from_rgb_u8(0x8a, 0x8a, 0x8e).into(),
            running: false,
        })
        .collect()
}

/// 把一轮状态探测结果写回某个面板的图块模型；学习应用面板和实践面板各调
/// 一次，探测到的 `states` 顺序必须跟建模型时的 `apps` 顺序一致。
///
/// 运行/未运行不写进模型里的文字字段——文字改成图块下方常驻的状态点，
/// 颜色由 `tint` 算好（绿/橙/灰）；`running` 只管停止按钮。图标本身不随
/// 状态变化（ADR 0065）。
fn apply_states(model: &ModelRc<AppEntry>, states: &[RunState]) {
    // 模型末尾的引用节点（ADR 0116）没有自己的探测结果，按 id 跟本体同步。
    let mut by_id: Vec<(SharedString, RunState)> = Vec::with_capacity(states.len());
    for index in 0..model.row_count() {
        let Some(mut entry) = model.row_data(index) else { continue };
        let state = match states.get(index) {
            Some(state) => {
                by_id.push((entry.id.clone(), *state));
                *state
            }
            None => match by_id.iter().find(|(id, _)| *id == entry.id) {
                Some((_, state)) => *state,
                None => continue,
            },
        };
        entry.tint = tint(state).into();
        entry.running = state != RunState::Stopped;
        model.set_row_data(index, entry);
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
        // 更饱和一点：运行态绿/橙要跳出来，别跟未运行灰混成一片。
        RunState::Ready => Color::from_rgb_u8(0x00, 0xe6, 0x76),
        RunState::Starting => Color::from_rgb_u8(0xff, 0xb0, 0x20),
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
