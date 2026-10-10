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
}

#[derive(serde::Serialize)]
pub struct OrbitDto {
    radius: f32,
    tilt: f32,
    yaw: f32,
}

#[derive(serde::Serialize)]
pub struct CatalogDto {
    repo: String,
    apps: Vec<AppDto>,
    orbits: Vec<OrbitDto>,
}

fn icon_data_url(path: &std::path::Path) -> Option<String> {
    let bytes = std::fs::read(path).ok()?;
    Some(format!(
        "data:image/svg+xml;base64,{}",
        base64::engine::general_purpose::STANDARD.encode(bytes)
    ))
}

/// 命令集中在子模块：`generate_handler!` 的宏展开会引入与命令同名的辅助项，
/// 同模块里定义并引用会撞名（Tauri 2 的既知约束）。
pub mod commands {
    use super::{icon_data_url, AppDto, CatalogDto, OrbitDto, Repo};
    use launcher_core::{layout3d, manifest, runner};
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
                .unwrap_or(layout3d::OrbitNode { group: g, slot, pos: [0.0; 3] });
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
            });
        }

        Ok(CatalogDto {
            repo: repo.0.display().to_string(),
            orbits: layout
                .orbits
                .iter()
                .map(|o| OrbitDto { radius: o.radius, tilt: o.tilt, yaw: o.yaw })
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
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let repo = paths::locate_repo().expect("找不到 Athena 仓库：设置 ATHENA_ROOT，或把启动器放在仓库里");
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|_app, _args, _cwd| {}))
        .manage(Repo(repo))
        .invoke_handler(tauri::generate_handler![
            commands::catalog,
            commands::open_app,
            commands::stop_app
        ])
        .run(tauri::generate_context!())
        .expect("启动器窗口启动失败");
}
