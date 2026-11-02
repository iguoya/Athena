//! Athena 启动器 Web 前端（ADR 0125）。执行路径约定（ADR 0046）不变：
//! 清单、布局、状态、启动编排全部来自 launcher-core，这里只做类型转换与命令暴露。

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use launcher_core::Workspace;
use tauri::Manager;
use tauri_plugin_opener::OpenerExt;

mod app_icon;
mod cache;
mod resident;
mod watch;

/// 运行模式与仓库只定位一次、整个进程共享（ADR 0173）：找到仓库是仓库模式，找不到是安装模式，
/// 之后清单与启动都问它，webui 不自己判断模式。
pub struct Ws(pub Workspace);

/// 安装模式下没装（或这类应用不支持安装模式启动）时指路的地方。启动器不代装（ADR 0173 决策 4）。
const RELEASES_URL: &str = "https://github.com/iguoya/Athena/releases";

pub fn open_releases(app: &tauri::AppHandle) -> Result<(), String> {
    app.opener()
        .open_url(RELEASES_URL, None::<&str>)
        .map_err(|e| format!("打不开 Releases 页：{e}"))
}

#[derive(serde::Serialize)]
pub struct AppDto {
    id: String,
    title: String,
    summary: String,
    group: Option<String>,
    group_index: usize,
    letter: String,
    accent: String,
    /// 领域组色（同组同色，来自 mindmap 色板）：3D 行星的球面底色。
    #[serde(rename = "groupColor")]
    group_color: String,
    /// icon.svg 的 data URL（骨架阶段每次 catalog 现读；体量大了换 fingerprint 缓存）。
    icon: Option<String>,
    /// 学习生命周期（ADR 0139）：active / built / archived。3D 视图不含归档，
    /// built 在前端淡显。
    lifecycle: String,
    /// runner::RunState::key()：stopped / starting / ready（跨进程契约，ADR 0048）。
    state: String,
    /// 安装模式下是否已装（ADR 0173）；仓库模式为 null。未装的应用前端淡显，点击指路 Releases。
    installed: Option<bool>,
    /// 3D 轨道布局里的世界坐标。
    pos: [f32; 3],
    /// 公转动画参数：所在轨道下标与初始参数角（rad）。前端每帧
    /// theta = theta0 + omega·t 后套与布局相同的正变换得到当前位置。
    orbit: usize,
    theta: f32,
}

#[derive(serde::Serialize)]
pub struct OrbitDto {
    a: f32,
    b: f32,
    c: f32,
    tilt: f32,
}

#[derive(serde::Serialize)]
pub struct CatalogDto {
    /// 仓库路径；安装模式下为空串。
    repo: String,
    /// "repo" / "installed"（Mode::key）。
    mode: String,
    apps: Vec<AppDto>,
    orbits: Vec<OrbitDto>,
}

/// 命令集中在子模块：`generate_handler!` 的宏展开会引入与命令同名的辅助项，
/// 同模块里定义并引用会撞名（Tauri 2 的既知约束）。
pub mod commands {
    use super::cache;
    use super::{AppDto, CatalogDto, OrbitDto, Ws};
    use launcher_core::{layout3d, manifest, mindmap, runner, LaunchError};
    use tauri::State;

    #[tauri::command]
    pub fn catalog(ws: State<Ws>) -> Result<CatalogDto, String> {
        let apps = ws.0.apps();
        crate::watch::remember(&apps);
        // 归档（ADR 0139）与隐藏（ADR 0093）都不进 3D 视图；归档在思维导图可开关查看。
        let visible: Vec<&manifest::App> = apps
            .iter()
            .filter(|a| !a.hidden && a.lifecycle != manifest::Lifecycle::Archived)
            .collect();

        // 分组：领域名按首次出现序登记（与 core 的 mindmap 分组同规则），挂靠应用
        // （有 parent）骨架阶段同圈排布，挂靠语义的专门表达留待下一轮。
        let mut group_names: Vec<String> = Vec::new();
        let mut group_colors: Vec<String> = Vec::new();
        let mut group_of: Vec<usize> = Vec::with_capacity(visible.len());
        for app in &visible {
            let name = app.group.clone().unwrap_or_else(|| "其他".into());
            let idx = match group_names.iter().position(|g| g == &name) {
                Some(i) => i,
                None => {
                    group_names.push(name.clone());
                    // 组色按组序取 mindmap 色板（与 mindmap::layout 同规则），同组同色。
                    group_colors.push(
                        launcher_core::mindmap::PALETTE
                            [(group_names.len() - 1) % launcher_core::mindmap::PALETTE.len()]
                        .to_string(),
                    );
                    group_names.len() - 1
                }
            };
            group_of.push(idx);
        }
        let sizes: Vec<usize> = {
            let mut v = vec![0usize; group_names.len()];
            for &g in &group_of {
                v[g] += 1;
            }
            v
        };
        let layout = layout3d::orbit_layout(&sizes);

        let states = cache::states(&apps);

        // 组内成员按清单序占位：第 g 组的第 k 个成员落轨道 g 的第 k 个节点。
        let mut cursor = vec![0usize; group_names.len()];
        let mut out = Vec::with_capacity(visible.len());
        for (i, app) in visible.iter().enumerate() {
            let g = group_of[i];
            let slot = cursor[g];
            cursor[g] += 1;
            let node = layout
                .nodes
                .iter()
                .find(|n| n.group == g && n.slot == slot)
                .copied()
                .unwrap_or(layout3d::OrbitNode {
                    group: g,
                    slot,
                    pos: [0.0; 3],
                    theta: 0.0,
                });
            out.push(AppDto {
                id: app.id.clone(),
                title: app.title.clone(),
                summary: app.summary.clone(),
                group: Some(group_names[g].clone()),
                group_index: g,
                group_color: group_colors[g].clone(),
                letter: app.letter.clone(),
                accent: app.accent.clone(),
                icon: app
                    .icon_file
                    .as_deref()
                    .and_then(cache::icon_data_url)
                    .or_else(|| app.embedded_icon.clone()),
                lifecycle: app.lifecycle.key().to_string(),
                state: states[i].key().to_string(),
                installed: app.install.as_ref().map(|install| install.installed),
                pos: node.pos,
                orbit: node.group,
                theta: node.theta,
            });
        }

        Ok(CatalogDto {
            repo: ws.0.repo().map(|path| path.display().to_string()).unwrap_or_default(),
            mode: ws.0.mode().key().to_string(),
            orbits: layout
                .orbits
                .iter()
                .map(|o| OrbitDto {
                    a: o.a,
                    b: o.b,
                    c: o.c,
                    tilt: o.tilt,
                })
                .collect(),
            apps: out,
        })
    }

    // ---- 主窗口可见性：托盘常驻时前端整体挂起（轮询与 3D 帧循环都停）----

    /// 前端启动时主动问一次初始状态；此后的变化走 resident 发的
    /// `launcher://visibility` 事件。启动器大部分时间藏在托盘，挂起后
    /// 常驻损耗只剩进程本身的内存。
    #[tauri::command]
    pub fn main_window_visible(app: tauri::AppHandle) -> bool {
        use tauri::Manager;
        app.get_webview_window("main")
            .and_then(|w| w.is_visible().ok())
            .unwrap_or(false)
    }

    #[tauri::command]
    pub fn open_app(handle: tauri::AppHandle, ws: State<Ws>, id: String) -> Result<(), String> {
        let apps = ws.0.apps();
        let app = apps
            .iter()
            .find(|a| a.id == id)
            .ok_or_else(|| format!("清单里没有 {id}"))?;
        // launch 返回窗口进程 pid，前端只需要成败。没装、不支持是安装模式的指路情形：
        // 打开 Releases 页，不算错误（ADR 0173 决策 4）。
        match ws.0.launch(app, |_| {}) {
            Ok(_) => Ok(()),
            Err(LaunchError::NotInstalled | LaunchError::Unsupported(_)) => super::open_releases(&handle),
            Err(other) => Err(other.to_string()),
        }
    }

    #[tauri::command]
    pub fn stop_app(ws: State<Ws>, id: String) -> Result<(), String> {
        let apps = ws.0.apps();
        let app = apps
            .iter()
            .find(|a| a.id == id)
            .ok_or_else(|| format!("清单里没有 {id}"))?;
        runner::stop(app)
    }

    // ---- 2D 椭圆思维导图（gui 版构图的 Web 移植，布局仍是 core 的 mindmap::layout）----

    #[derive(serde::Serialize)]
    pub struct MindNodeDto {
        id: String,
        title: String,
        letter: String,
        accent: String,
        icon: Option<String>,
        /// 学习生命周期（ADR 0139）：前端按 built / archived 淡显。
        lifecycle: String,
        state: String,
        /// 安装模式下是否已装（ADR 0173）；仓库模式为 null。
        installed: Option<bool>,
        reference: bool,
        x: f32,
        y: f32,
    }

    #[derive(serde::Serialize)]
    pub struct MindGroupDto {
        name: String,
        color: String,
        x: f32,
        y: f32,
        w: f32,
    }

    #[derive(serde::Serialize)]
    pub struct MindLinkDto {
        kind: i32,
        /// 带 alpha 的完整色值（#rrggbbaa），虚线态。
        color: String,
        /// 悬停点亮时的实线色。
        hot: String,
        a: i32,
        b: i32,
        x0: f32,
        y0: f32,
        cx1: f32,
        cy1: f32,
        cx2: f32,
        cy2: f32,
        x1: f32,
        y1: f32,
        has_arrow: bool,
        ax: f32,
        ay: f32,
        bx: f32,
        by: f32,
        cx: f32,
        cy: f32,
        dashes: Vec<[f32; 4]>,
    }

    #[derive(serde::Serialize)]
    pub struct MindmapDto {
        width: f32,
        height: f32,
        center_x: f32,
        center_y: f32,
        nodes: Vec<MindNodeDto>,
        groups: Vec<MindGroupDto>,
        links: Vec<MindLinkDto>,
        /// 同心环底图 PNG 的 data URL 与摆放位置。
        rings: String,
        rings_x: f32,
        rings_y: f32,
        rings_w: f32,
        rings_h: f32,
    }

    /// gui 里按连线种类定的透明度（映射表随 gui 冻结迁来，ADR 0127）。
    fn link_alpha(kind: mindmap::LinkKind) -> (i32, u8) {
        match kind {
            mindmap::LinkKind::Branch => (1, 0x88),
            mindmap::LinkKind::Evolves => (2, 0xff),
            mindmap::LinkKind::Related => (3, 0xc0),
            mindmap::LinkKind::Attach => (4, 0x4d),
            mindmap::LinkKind::Reference => (5, 0x2e),
        }
    }

    #[tauri::command]
    pub fn rescan_apps(app: tauri::AppHandle) -> Result<crate::watch::Rescan, String> {
        crate::watch::rescan(&app)
    }

    #[tauri::command]
    pub fn mindmap(ws: State<Ws>, include_archived: Option<bool>) -> Result<MindmapDto, String> {
        let apps = ws.0.apps();
        crate::watch::remember(&apps);
        // 归档默认不呈现（ADR 0139）；「显示归档」开关打开时以淡显节点进来。
        let include_archived = include_archived.unwrap_or(false);
        let visible: Vec<manifest::App> = apps
            .iter()
            .filter(|a| {
                !a.hidden && (include_archived || a.lifecycle != manifest::Lifecycle::Archived)
            })
            .cloned()
            .collect();
        let map = mindmap::layout(&visible);

        let states = cache::states(&apps);
        let state_of_id = |id: &str| -> String {
            apps.iter()
                .position(|a| a.id == id)
                .map(|i| states[i].key().to_string())
                .unwrap_or_else(|| "stopped".into())
        };

        let mut nodes = Vec::new();
        for (i, node) in map.nodes.iter().enumerate() {
            // 引用节点排在全部本体之后，id 与某个本体应用相同：显示同应用的图标与状态。
            let app = visible.get(i).unwrap_or_else(|| {
                visible
                    .iter()
                    .find(|a| a.id == node.id)
                    .expect("引用节点的 id 必有本体")
            });
            nodes.push(MindNodeDto {
                id: node.id.clone(),
                title: app.title.clone(),
                letter: app.letter.clone(),
                accent: app.accent.clone(),
                icon: app
                    .icon_file
                    .as_deref()
                    .and_then(cache::icon_data_url)
                    .or_else(|| app.embedded_icon.clone()),
                lifecycle: app.lifecycle.key().to_string(),
                state: state_of_id(&node.id),
                installed: app.install.as_ref().map(|install| install.installed),
                reference: node.reference,
                x: node.at.x,
                y: node.at.y,
            });
        }

        let groups: Vec<MindGroupDto> = map
            .groups
            .iter()
            .map(|g| MindGroupDto {
                name: g.name.clone(),
                color: g.color.to_string(),
                x: g.at.x,
                y: g.at.y,
                w: g.width,
            })
            .collect();

        let links: Vec<MindLinkDto> = map
            .links
            .iter()
            .map(|l| {
                let (kind, alpha) = link_alpha(l.kind);
                let base = l.color.trim_start_matches('#');
                let arrow = l.arrow.unwrap_or([l.to; 3]);
                MindLinkDto {
                    kind,
                    color: format!("#{base}{alpha:02x}"),
                    hot: format!("#{base}f0"),
                    a: l.ends.0 as i32,
                    b: l.ends.1 as i32,
                    x0: l.from.x,
                    y0: l.from.y,
                    cx1: l.c1.x,
                    cy1: l.c1.y,
                    cx2: l.c2.x,
                    cy2: l.c2.y,
                    x1: l.to.x,
                    y1: l.to.y,
                    has_arrow: l.arrow.is_some(),
                    ax: arrow[0].x,
                    ay: arrow[0].y,
                    bx: arrow[1].x,
                    by: arrow[1].y,
                    cx: arrow[2].x,
                    cy: arrow[2].y,
                    dashes: l.dashes.iter().map(|[p, q]| [p.x, p.y, q.x, q.y]).collect(),
                }
            })
            .collect();

        let rings = cache::rings_png(&map, 1.25);
        Ok(MindmapDto {
            width: map.width,
            height: map.height,
            center_x: map.center.x,
            center_y: map.center.y,
            nodes,
            groups,
            links,
            rings: rings.data_url,
            rings_x: rings.x,
            rings_y: rings.y,
            rings_w: rings.width,
            rings_h: rings.height,
        })
    }
}

fn autostart_plugin() -> tauri::plugin::TauriPlugin<tauri::Wry> {
    let mut builder = tauri_plugin_autostart::Builder::new()
        .app_name("athena-launcher")
        .args([resident::AUTOSTART_ARG]);
    // LaunchAgent 指向当前可执行文件。开发二进制不是 .app，登录项那条路走不通。
    #[cfg(target_os = "macos")]
    {
        builder = builder.macos_launcher(tauri_plugin_autostart::MacosLauncher::LaunchAgent);
    }
    builder.build()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // 找到仓库是仓库模式；找不到不再是错误，而是安装模式（ADR 0173）。
    let workspace = Workspace::locate();
    let quitting = Arc::new(AtomicBool::new(false));
    let quitting_for_run = Arc::clone(&quitting);

    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            // 第二实例被单例拦下时，把已有窗口叫到前台。
            resident::show_main(app);
        }))
        .plugin(autostart_plugin())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .manage(Ws(workspace))
        .manage(resident::Shown(Arc::new(AtomicBool::new(
            !resident::launched_hidden(),
        ))))
        .manage(resident::TraySlot(std::sync::Mutex::new(None)))
        .setup(move |app| {
            let window = app.get_webview_window("main").expect("主窗口缺失");
            app_icon::install(&window);
            // 注册项指向的二进制可能已过期，每次启动都对一遍（幂等）。
            resident::heal_autostart(app.handle());
            let hidden = resident::launched_hidden();
            if !hidden {
                let _ = window.show();
                let _ = window.set_focus();
            }
            match resident::install(app.handle(), &window, quitting) {
                Ok(icon) => {
                    *app.state::<resident::TraySlot>().0.lock().unwrap_or_else(|p| p.into_inner()) =
                        Some(icon);
                }
                Err(error) => {
                    eprintln!("托盘没能建起来，窗口照常能用：{error}");
                    if hidden {
                        let _ = window.show();
                        let _ = window.set_focus();
                        resident::note_visibility(app.handle(), true);
                    }
                }
            }
            // 应用目录不自动侦察。这里只起运行状态探测；扫新目录走 rescan_apps。
            watch::start(app.handle().clone());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::catalog,
            commands::mindmap,
            commands::main_window_visible,
            commands::open_app,
            commands::stop_app,
            commands::rescan_apps
        ])
        .build(tauri::generate_context!())
        .expect("启动器窗口启动失败")
        .run(move |app, event| match event {
            // Cmd+Q 一类的系统退出先到这里。关窗口走的是 CloseRequested，不会进这条。
            tauri::RunEvent::ExitRequested { .. } => {
                quitting_for_run.store(true, Ordering::SeqCst);
            }
            // Reopen 只在 macOS 的 RunEvent 里存在：点 Dock 图标且没有可见窗口时把主窗口叫回来。
            #[cfg(target_os = "macos")]
            tauri::RunEvent::Reopen {
                has_visible_windows: false,
                ..
            } => resident::show_main(app),
            _ => {}
        });
}
