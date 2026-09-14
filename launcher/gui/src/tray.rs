//! 状态栏托盘：启动器的常驻形态。
//!
//! 窗口只是可选的详细视图，真正一直在的是这个图标——点开就是应用列表，
//! 每个应用能直接打开或停止。三平台用同一套 API（tray-icon / muda），
//! 但有一处平台差异躲不掉：**Linux 的托盘必须活在 GTK 线程里**，
//! 而 Slint 的事件循环在主线程，所以那条路径要单开一个线程。
//!
//! 菜单点击事件走的是 muda 的全局 channel，任何线程都收得到，因此不管托盘
//! 建在哪个线程，主线程都能统一处理动作——这是这套库最省事的地方。

use std::collections::HashMap;
use std::sync::mpsc::Sender;

use muda::{Menu, MenuEvent, MenuId, MenuItem, PredefinedMenuItem, Submenu};
use tray_icon::{Icon, TrayIcon, TrayIconBuilder};

#[derive(Debug, Clone)]
pub enum Action {
    Open(String),
    Stop(String),
    Log(String),
    ShowWindow,
    Quit,
}

struct Wiring {
    menu: Menu,
    /// 每个应用的父项：文本会随状态变，"C++ 教程 · 运行中"。
    headings: Vec<Submenu>,
    actions: HashMap<MenuId, Action>,
}

fn build(apps: &[(String, String)]) -> Wiring {
    let menu = Menu::new();
    let mut headings = Vec::new();
    let mut actions = HashMap::new();

    for (id, title) in apps {
        let open = MenuItem::new("打开", true, None);
        let stop = MenuItem::new("停止", true, None);
        let log = MenuItem::new("查看启动日志", true, None);
        actions.insert(open.id().clone(), Action::Open(id.clone()));
        actions.insert(stop.id().clone(), Action::Stop(id.clone()));
        actions.insert(log.id().clone(), Action::Log(id.clone()));

        let heading = Submenu::with_items(title, true, &[&open, &stop, &log])
            .expect("托盘菜单构建失败");
        let _ = menu.append(&heading);
        headings.push(heading);
    }

    let separator = PredefinedMenuItem::separator();
    let window = MenuItem::new("显示应用列表", true, None);
    let quit = MenuItem::new("退出启动器", true, None);
    actions.insert(window.id().clone(), Action::ShowWindow);
    actions.insert(quit.id().clone(), Action::Quit);
    let _ = menu.append_items(&[&separator, &window, &quit]);

    Wiring {
        menu,
        headings,
        actions,
    }
}

/// 托盘图标，由 `assets/tray-icon.svg` 在构建期渲染而来（见 build.rs）。
/// 换图标就是换那个 SVG，这里不用动。
fn icon() -> Option<Icon> {
    const SIZE: u32 = 64;
    let rgba = include_bytes!(concat!(env!("OUT_DIR"), "/tray-icon.rgba")).to_vec();
    Icon::from_rgba(rgba, SIZE, SIZE).ok()
}

/// 托盘的两种形态：句柄留在主线程（macOS / Windows），或者留在 GTK 线程（Linux）。
pub enum Tray {
    Local {
        _icon: TrayIcon,
        headings: Vec<Submenu>,
        actions: HashMap<MenuId, Action>,
    },
    Remote {
        labels: Sender<Vec<String>>,
        actions: HashMap<MenuId, Action>,
    },
    /// 托盘建不起来（Linux 桌面没有状态栏区域是常事），窗口照常能用。
    Unavailable,
}

impl Tray {
    #[cfg(not(target_os = "linux"))]
    pub fn start(apps: &[(String, String)]) -> Self {
        let wiring = build(apps);
        let builder = TrayIconBuilder::new()
            .with_menu(Box::new(wiring.menu))
            .with_tooltip("Athena 启动器")
            .with_icon(icon().unwrap_or_else(|| {
                Icon::from_rgba(vec![0; 4], 1, 1).expect("空图标")
            }));
        match builder.build()
        {
            Ok(tray) => Tray::Local {
                _icon: tray,
                headings: wiring.headings,
                actions: wiring.actions,
            },
            Err(error) => {
                eprintln!("托盘没能建起来：{error}");
                Tray::Unavailable
            }
        }
    }

    /// Linux：GTK 对象不能跨线程，所以托盘整体留在自己的线程里，
    /// 主线程只通过 channel 推送新的标签文本。
    #[cfg(target_os = "linux")]
    pub fn start(apps: &[(String, String)]) -> Self {
        let apps = apps.to_vec();
        let wiring_actions = build(&apps).actions;
        let (labels, updates) = std::sync::mpsc::channel::<Vec<String>>();

        std::thread::spawn(move || {
            if gtk::init().is_err() {
                eprintln!("GTK 起不来，托盘不可用；窗口照常能用。");
                return;
            }
            let wiring = build(&apps);
            let tray = TrayIconBuilder::new()
                .with_menu(Box::new(wiring.menu))
                .with_tooltip("Athena 启动器")
                .with_icon(icon().expect("托盘图标"))
                .build();
            if let Err(error) = &tray {
                eprintln!("托盘没能建起来：{error}");
                return;
            }
            let headings = wiring.headings;
            gtk::glib::timeout_add_local(std::time::Duration::from_millis(500), move || {
                if let Some(texts) = updates.try_iter().last() {
                    for (heading, text) in headings.iter().zip(texts) {
                        heading.set_text(text);
                    }
                }
                gtk::glib::ControlFlow::Continue
            });
            gtk::main();
        });

        Tray::Remote {
            labels,
            actions: wiring_actions,
        }
    }

    /// 把每个应用当前的状态写进它在菜单里的标题。
    pub fn update(&self, texts: Vec<String>) {
        match self {
            Tray::Local { headings, .. } => {
                for (heading, text) in headings.iter().zip(texts) {
                    heading.set_text(text);
                }
            }
            Tray::Remote { labels, .. } => {
                let _ = labels.send(texts);
            }
            Tray::Unavailable => {}
        }
    }

    /// 取出攒下的点击。菜单事件是全局 channel，托盘建在哪个线程都收得到。
    pub fn drain(&self) -> Vec<Action> {
        let actions = match self {
            Tray::Local { actions, .. } | Tray::Remote { actions, .. } => actions,
            Tray::Unavailable => return Vec::new(),
        };
        MenuEvent::receiver()
            .try_iter()
            .filter_map(|event| actions.get(&event.id).cloned())
            .collect()
    }
}
