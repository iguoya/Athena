//! 状态栏托盘：启动器的常驻形态。
//!
//! 窗口只是可选的详细视图，真正一直在的是这个图标——点开就是应用列表，
//! 每个应用能直接打开或停止。三平台用同一套 API（tray-icon / muda），
//! 但有一处平台差异躲不掉：**Linux 的托盘必须活在 GTK 线程里**，
//! 而 Slint 的事件循环在主线程，所以那条路径要单开一个线程。
//!
//! 菜单是活的：仓库里新增、删除应用（ADR 0001 的清单热刷新）之后，
//! `rebuild()` 整条换掉——Windows / macOS 主线程直接换，Linux 把重建
//! 指令发给 GTK 线程，换完再把新的点击映射送回主线程。
//!
//! 点击事件走的是 muda 的全局 channel，任何线程都收得到，因此不管托盘
//! 建在哪个线程，主线程都能统一处理动作——这是这套库最省事的地方。

use std::cell::RefCell;
use std::collections::HashMap;
use std::sync::mpsc::{Receiver, Sender};

use muda::{CheckMenuItem, Menu, MenuEvent, MenuId, MenuItem, PredefinedMenuItem, Submenu};
use tray_icon::{
    Icon, MouseButton, MouseButtonState, TrayIcon, TrayIconBuilder, TrayIconEvent,
};

#[derive(Debug, Clone)]
pub enum Action {
    Open(String),
    Stop(String),
    Log(String),
    ShowWindow,
    Quit,
    /// 开机自启的勾选以注册表为准（系统实况，不自己记账）：收到就翻转它。
    ToggleAutostart,
}

/// 菜单里要跟着清单动态维护的部分：标题随状态变的父项、点击事件的映射。
pub(crate) struct WiringState {
    headings: Vec<Submenu>,
    actions: HashMap<MenuId, Action>,
}

struct Wiring {
    menu: Menu,
    state: WiringState,
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
    let _ = menu.append(&separator);

    // 开机自启每个系统各有一套机制（Windows 是 HKCU 的 Run 键），别的平台
    // 不假装支持（ADR 0047、0049）：菜单项只在 Windows 上出现。勾选状态从
    // 注册表现读——启动器不记自己的账，跟 ADR 0044「状态从系统实况读」同理。
    #[cfg(windows)]
    {
        let autostart = CheckMenuItem::new("开机自启", true, crate::autostart::is_enabled(), None);
        actions.insert(autostart.id().clone(), Action::ToggleAutostart);
        let _ = menu.append(&autostart);
    }

    let window = MenuItem::new("显示应用列表", true, None);
    let quit = MenuItem::new("退出启动器", true, None);
    actions.insert(window.id().clone(), Action::ShowWindow);
    actions.insert(quit.id().clone(), Action::Quit);
    let _ = menu.append_items(&[&window, &quit]);

    Wiring {
        menu,
        state: WiringState { headings, actions },
    }
}

/// 托盘图标：和标题栏、任务栏同一份虎头（build.rs 从 tiger.svg 裁出）。
fn icon() -> Option<Icon> {
    const SIZE: u32 = 64;
    let rgba = include_bytes!(concat!(env!("OUT_DIR"), "/tray-icon.rgba")).to_vec();
    Icon::from_rgba(rgba, SIZE, SIZE).ok()
}

/// 托盘的两种形态：句柄留在主线程（macOS / Windows），或者留在 GTK 线程（Linux）。
pub enum Tray {
    Local {
        icon: TrayIcon,
        wiring: RefCell<WiringState>,
    },
    /// Linux 专属形态：菜单活在 GTK 线程里，主线程只有指令 channel 和一份
    /// 点击映射。非 Linux 平台不会构造它，枚举分支照留——处理动作的代码
    /// 一份，不为平台裂成两套。
    #[cfg_attr(not(target_os = "linux"), allow(dead_code))]
    Remote {
        /// 主线程 → GTK 线程的指令。每类一条 channel：mpsc 取「最新一条」的
        /// 消费方式（`try_iter().last()`）只对单一类型成立，混在一条 channel
        /// 里会把别的指令吞掉。
        labels: Sender<Vec<String>>,
        rebuilds: Sender<Vec<(String, String)>>,
        tooltips: Sender<String>,
        /// GTK 线程重建完菜单，把新的点击映射送回主线程。
        rewired: Receiver<HashMap<MenuId, Action>>,
        actions: RefCell<HashMap<MenuId, Action>>,
    },
    /// 托盘建不起来（Linux 桌面没有状态栏区域是常事），窗口照常能用。
    Unavailable,
}

impl Tray {
    #[cfg(not(target_os = "linux"))]
    pub fn start(apps: &[(String, String)]) -> Self {
        let wiring = build(apps);
        // 左键唤出窗口、右键出菜单：测试阶段关了列表也要能从托盘把窗口叫回来。
        let _ = TrayIconEvent::receiver();
        let builder = TrayIconBuilder::new()
            .with_menu(Box::new(wiring.menu))
            .with_tooltip("Athena 启动器")
            .with_menu_on_left_click(false)
            .with_icon(icon().unwrap_or_else(|| {
                Icon::from_rgba(vec![0; 4], 1, 1).expect("空图标")
            }));
        match builder.build()
        {
            Ok(tray) => Tray::Local {
                icon: tray,
                wiring: RefCell::new(wiring.state),
            },
            Err(error) => {
                eprintln!("托盘没能建起来：{error}");
                Tray::Unavailable
            }
        }
    }

    /// Linux：GTK 对象不能跨线程，所以托盘整体留在自己的线程里，
    /// 主线程只通过 channel 推送指令。
    #[cfg(target_os = "linux")]
    pub fn start(apps: &[(String, String)]) -> Self {
        let apps = apps.to_vec();
        // 主线程手里留一份启动时的映射兜底：GTK 线程重建完成前的点击仍能认。
        let actions = build(&apps).state.actions;
        let (labels, labels_rx) = std::sync::mpsc::channel::<Vec<String>>();
        let (rebuilds, rebuilds_rx) = std::sync::mpsc::channel::<Vec<(String, String)>>();
        let (tooltips, tooltips_rx) = std::sync::mpsc::channel::<String>();
        let (rewire_tx, rewire_rx) = std::sync::mpsc::channel::<HashMap<MenuId, Action>>();

        std::thread::spawn(move || {
            if gtk::init().is_err() {
                eprintln!("GTK 起不来，托盘不可用；窗口照常能用。");
                return;
            }
            let wiring = build(&apps);
            let _ = TrayIconEvent::receiver();
            let tray = TrayIconBuilder::new()
                .with_menu(Box::new(wiring.menu))
                .with_tooltip("Athena 启动器")
                .with_menu_on_left_click(false)
                .with_icon(icon().expect("托盘图标"))
                .build();
            if let Err(error) = &tray {
                eprintln!("托盘没能建起来：{error}");
                return;
            }
            let tray = tray.expect("托盘刚建好");
            let state = std::cell::RefCell::new(wiring.state);
            gtk::glib::timeout_add_local(std::time::Duration::from_millis(500), move || {
                if let Some(texts) = labels_rx.try_iter().last() {
                    for (heading, text) in state.borrow().headings.iter().zip(texts) {
                        heading.set_text(text);
                    }
                }
                if let Some(apps) = rebuilds_rx.try_iter().last() {
                    let wiring = build(&apps);
                    tray.set_menu(Some(Box::new(wiring.menu)));
                    let _ = rewire_tx.send(wiring.state.actions);
                    state.borrow_mut().headings = wiring.state.headings;
                }
                if let Some(text) = tooltips_rx.try_iter().last() {
                    let _ = tray.set_tooltip(Some(text));
                }
                gtk::glib::ControlFlow::Continue
            });
            gtk::main();
        });

        Tray::Remote {
            labels,
            rebuilds,
            tooltips,
            rewired: rewire_rx,
            actions: RefCell::new(actions),
        }
    }

    /// 清单变了：整条菜单换掉。正在显示的菜单不受影响，下次点开就是新的。
    pub fn rebuild(&self, apps: &[(String, String)]) {
        match self {
            Tray::Local { icon, wiring } => {
                let fresh = build(apps);
                icon.set_menu(Some(Box::new(fresh.menu)));
                *wiring.borrow_mut() = fresh.state;
            }
            Tray::Remote { rebuilds, .. } => {
                let _ = rebuilds.send(apps.to_vec());
            }
            Tray::Unavailable => {}
        }
    }

    /// 把每个应用当前的状态写进它在菜单里的标题。
    pub fn update(&self, texts: Vec<String>) {
        match self {
            Tray::Local { wiring, .. } => {
                for (heading, text) in wiring.borrow().headings.iter().zip(texts) {
                    heading.set_text(text);
                }
            }
            Tray::Remote { labels, .. } => {
                let _ = labels.send(texts);
            }
            Tray::Unavailable => {}
        }
    }

    /// 托盘悬浮提示：顺带报「多少个应用、几个在跑」，清单热刷新的窗口之一。
    pub fn set_tooltip(&self, text: &str) {
        match self {
            Tray::Local { icon, .. } => {
                let _ = icon.set_tooltip(Some(text));
            }
            Tray::Remote { tooltips, .. } => {
                let _ = tooltips.send(text.to_string());
            }
            Tray::Unavailable => {}
        }
    }

    /// 取出攒下的点击。菜单事件是全局 channel，托盘建在哪个线程都收得到。
    pub fn drain(&self) -> Vec<Action> {
        let mut out = Vec::new();
        match self {
            Tray::Local { wiring, .. } => {
                let actions = &wiring.borrow().actions;
                out.extend(drain_menu(actions));
            }
            Tray::Remote { rewired, actions, .. } => {
                // GTK 线程重建过菜单的话，先换成最新的点击映射——
                // 换菜单和换映射不是同一瞬间，这里补齐时间差。
                if let Some(fresh) = rewired.try_iter().last() {
                    *actions.borrow_mut() = fresh;
                }
                out.extend(drain_menu(&actions.borrow()));
            }
            Tray::Unavailable => {}
        }
        for event in TrayIconEvent::receiver().try_iter() {
            match event {
                TrayIconEvent::DoubleClick { .. } => out.push(Action::ShowWindow),
                TrayIconEvent::Click {
                    button: MouseButton::Left,
                    button_state: MouseButtonState::Up,
                    ..
                } => out.push(Action::ShowWindow),
                _ => {}
            }
        }
        out
    }
}

fn drain_menu(actions: &HashMap<MenuId, Action>) -> Vec<Action> {
    MenuEvent::receiver()
        .try_iter()
        .filter_map(|event| actions.get(&event.id).cloned())
        .collect()
}
