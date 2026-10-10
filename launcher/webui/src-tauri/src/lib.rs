//! Athena 启动器 Web 前端（ADR 0125）。执行路径约定（ADR 0046）不变：
//! 清单、布局、状态、启动编排全部来自 launcher-core，这里只做类型转换与命令暴露。

use base64::Engine as _;
use launcher_core::paths;

/// 仓库定位一次、整个进程共享：locate_repo 每次都走盘上探测，没必要。
pub struct Repo(pub std::path::PathBuf);

#[derive(serde::Serialize)]
pub struct AppDto {
    id: String,
    title: String,
    summary: String,
    group: Option<String>,
    group_index: usize,
    letter: String,
    accent: String,
    /// icon.svg 的 data URL（骨架阶段每次 catalog 现读；体量大了换 fingerprint 缓存）。
    icon: Option<String>,
    /// runner::RunState::key()：stopped / starting / ready（跨进程契约，ADR 0048）。
    state: String,
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
    repo: String,
    apps: Vec<AppDto>,
    orbits: Vec<OrbitDto>,
}

/// icon.svg → 256px PNG 的 data URL。不用 SVG data URL 直传：WebView2 里
/// `new Image()` 加载 SVG data URL 的 onload 会悬挂（贴图永远停在 loading），
/// 而且用 core 的 resvg 渲染位图，Fluent Emoji 的滤镜表现反而更有保障。
fn icon_data_url(path: &std::path::Path) -> Option<String> {
    let tree = launcher_core::icons::load(path).ok()?;
    let pixmap = launcher_core::icons::render(&tree, 256).ok()?;
    let png = pixmap.encode_png().ok()?;
    Some(format!(
        "data:image/png;base64,{}",
        base64::engine::general_purpose::STANDARD.encode(png)
    ))
}

/// 命令集中在子模块：`generate_handler!` 的宏展开会引入与命令同名的辅助项，
/// 同模块里定义并引用会撞名（Tauri 2 的既知约束）。
pub mod commands {
    use super::{icon_data_url, AppDto, CatalogDto, OrbitDto, Repo};
    use launcher_core::{layout3d, manifest, mindmap, runner};
    use tauri::State;

    #[tauri::command]
    pub fn catalog(repo: State<Repo>) -> Result<CatalogDto, String> {
        let apps = manifest::discover(&repo.0);
        let visible: Vec<&manifest::App> = apps.iter().filter(|a| !a.hidden).collect();

        // 分组：领域名按首次出现序登记（与 core 的 mindmap 分组同规则），挂靠应用
        // （有 parent）骨架阶段同圈排布，挂靠语义的专门表达留待下一轮。
        let mut group_names: Vec<String> = Vec::new();
        let mut group_of: Vec<usize> = Vec::with_capacity(visible.len());
        for app in &visible {
            let name = app.group.clone().unwrap_or_else(|| "其他".into());
            let idx = match group_names.iter().position(|g| g == &name) {
                Some(i) => i,
                None => {
                    group_names.push(name);
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

        let snapshot = runner::ProcessSnapshot::take();
        let states = snapshot.states(&apps);

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
                .unwrap_or(layout3d::OrbitNode { group: g, slot, pos: [0.0; 3], theta: 0.0 });
            out.push(AppDto {
                id: app.id.clone(),
                title: app.title.clone(),
                summary: app.summary.clone(),
                group: Some(group_names[g].clone()),
                group_index: g,
                letter: app.letter.clone(),
                accent: app.accent.clone(),
                icon: app.icon_file.as_deref().and_then(icon_data_url),
                state: states[i].key().to_string(),
                pos: node.pos,
                orbit: node.group,
                theta: node.theta,
            });
        }

        Ok(CatalogDto {
            repo: repo.0.display().to_string(),
            orbits: layout
                .orbits
                .iter()
                .map(|o| OrbitDto { a: o.a, b: o.b, c: o.c, tilt: o.tilt })
                .collect(),
            apps: out,
        })
    }

    #[tauri::command]
    pub fn open_app(repo: State<Repo>, id: String) -> Result<(), String> {
        let apps = manifest::discover(&repo.0);
        let app = apps.iter().find(|a| a.id == id).ok_or_else(|| format!("清单里没有 {id}"))?;
        // launch 返回窗口进程 pid，前端只需要成败。
        runner::launch(app, &repo.0, |_| {}).map(|_| ())
    }

    #[tauri::command]
    pub fn stop_app(repo: State<Repo>, id: String) -> Result<(), String> {
        let apps = manifest::discover(&repo.0);
        let app = apps.iter().find(|a| a.id == id).ok_or_else(|| format!("清单里没有 {id}"))?;
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
        state: String,
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
        x0: f32, y0: f32,
        cx1: f32, cy1: f32,
        cx2: f32, cy2: f32,
        x1: f32, y1: f32,
        has_arrow: bool,
        ax: f32, ay: f32,
        bx: f32, by: f32,
        cx: f32, cy: f32,
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
    pub fn mindmap(repo: State<Repo>) -> Result<MindmapDto, String> {
        let apps = manifest::discover(&repo.0);
        let visible: Vec<manifest::App> = apps.iter().filter(|a| !a.hidden).cloned().collect();
        let map = mindmap::layout(&visible);

        let snapshot = runner::ProcessSnapshot::take();
        let states = snapshot.states(&apps);
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
                visible.iter().find(|a| a.id == node.id).expect("引用节点的 id 必有本体")
            });
            nodes.push(MindNodeDto {
                id: node.id.clone(),
                title: app.title.clone(),
                letter: app.letter.clone(),
                accent: app.accent.clone(),
                icon: app.icon_file.as_deref().and_then(icon_data_url),
                state: state_of_id(&node.id),
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
                    x0: l.from.x, y0: l.from.y,
                    cx1: l.c1.x, cy1: l.c1.y,
                    cx2: l.c2.x, cy2: l.c2.y,
                    x1: l.to.x, y1: l.to.y,
                    has_arrow: l.arrow.is_some(),
                    ax: arrow[0].x, ay: arrow[0].y,
                    bx: arrow[1].x, by: arrow[1].y,
                    cx: arrow[2].x, cy: arrow[2].y,
                    dashes: l.dashes.iter().map(|[p, q]| [p.x, p.y, q.x, q.y]).collect(),
                }
            })
            .collect();

        let rings = mindmap::rings_png(&map, 1.25);
        use base64::Engine as _;
        Ok(MindmapDto {
            width: map.width,
            height: map.height,
            center_x: map.center.x,
            center_y: map.center.y,
            nodes,
            groups,
            links,
            rings: format!(
                "data:image/png;base64,{}",
                base64::engine::general_purpose::STANDARD.encode(rings.png)
            ),
            rings_x: rings.x,
            rings_y: rings.y,
            rings_w: rings.width,
            rings_h: rings.height,
        })
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    use launcher_core::{manifest, runner};
    let repo = paths::locate_repo().expect("找不到 Athena 仓库：设置 ATHENA_ROOT，或把启动器放在仓库里");
    let repo_for_setup = repo.clone();

    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            // 第二实例被单例拦下时，把已有窗口叫到前台——这就是「再次双击没反应」的反面。
            if let Some(w) = tauri::Manager::get_webview_window(app, "main") {
                let _ = w.show();
                let _ = w.set_focus();
            }
        }))
        .manage(Repo(repo))
        .setup(move |app| {
            use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};
            use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
            use tauri::Manager;

            let handle = app.handle().clone();
            let repo = repo_for_setup.clone();

            // 托盘菜单：每个应用一个子菜单（打开/停止），加显示与退出。
            // 清单变化后的菜单重建骨架阶段先不做（重启启动器生效），热更新随后补。
            let apps = manifest::discover(&repo);
            let menu = Menu::new(&handle)?;
            for a in apps.iter().filter(|a| !a.hidden) {
                let sub = Submenu::with_id(&handle, format!("app:{}", a.id), &a.title, true)?;
                let open = MenuItem::with_id(
                    &handle,
                    format!("open:{}", a.id),
                    "打开",
                    true,
                    None::<&str>,
                )?;
                let stop = MenuItem::with_id(
                    &handle,
                    format!("stop:{}", a.id),
                    "停止",
                    true,
                    None::<&str>,
                )?;
                sub.append(&open)?;
                sub.append(&stop)?;
                menu.append(&sub)?;
            }
            menu.append(&PredefinedMenuItem::separator(&handle)?)?;
            let show = MenuItem::with_id(&handle, "show", "显示启动器", true, None::<&str>)?;
            menu.append(&show)?;
            let quit = MenuItem::with_id(&handle, "quit", "退出启动器", true, None::<&str>)?;
            menu.append(&quit)?;

            let _tray = TrayIconBuilder::with_id("main-tray")
                .icon(tauri::image::Image::from_bytes(include_bytes!(
                    "../icons/32x32.png"
                ))?)
                .tooltip("Athena 启动器")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| {
                    let id = event.id().as_ref().to_string();
                    let repo = paths::locate_repo().expect("找不到 Athena 仓库");
                    let (action, target) = if let Some(t) = id.strip_prefix("open:") {
                        ("open", t.to_string())
                    } else if let Some(t) = id.strip_prefix("stop:") {
                        ("stop", t.to_string())
                    } else if id == "show" {
                        if let Some(w) = tauri::Manager::get_webview_window(app, "main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                        return;
                    } else if id == "quit" {
                        app.exit(0);
                        return;
                    } else {
                        return;
                    };
                    // launch 会跑完整构建链（数十秒），绝不能堵在事件回调线程上。
                    let target = target.to_string();
                    let app_handle = app.clone();
                    tauri::async_runtime::spawn_blocking(move || {
                        let apps = manifest::discover(&repo);
                        let Some(app_cfg) = apps.iter().find(|a| a.id == target) else {
                            return;
                        };
                        let result = match action {
                            "open" => runner::launch(app_cfg, &repo, |_| {}).map(|_| ()),
                            _ => runner::stop(app_cfg),
                        };
                        if let Err(e) = result {
                            eprintln!("托盘动作 {action} {target} 失败：{e}");
                        }
                    });
                })
                .on_tray_icon_event(|tray, event| {
                    // 左键单击：唤起主窗口（常驻启动器的主入口）。
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(w) = tauri::Manager::get_webview_window(app, "main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                    }
                })
                .build(app)?;
            let _ = handle;

            // 常驻形态：关窗口 = 隐藏到托盘，退出走托盘菜单。
            let window = app.get_webview_window("main").expect("主窗口缺失");
            let window_for_event = window.clone();
            window.on_window_event(move |event| {
                if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                    api.prevent_close();
                    let _ = window_for_event.hide();
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::catalog,
            commands::mindmap,
            commands::open_app,
            commands::stop_app
        ])
        .run(tauri::generate_context!())
        .expect("启动器窗口启动失败");
}
