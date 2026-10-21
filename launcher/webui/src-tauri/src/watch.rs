//! 应用目录不自动侦察。进程起来时读一次；窗口开着时前端再读一次。
//! 之后只有使用者点「扫描应用」才重新扫各分组目录（含新加的目录）。
//!
//! 运行状态另算：窗口开着时对进程表，状态点变了才推。这不读应用目录，
//! 也不把新目录收进清单。窗口藏进托盘就停。

use std::collections::HashSet;
use std::sync::atomic::Ordering;
use std::sync::{Condvar, LazyLock, Mutex};
use std::time::Duration;

use launcher_core::{fingerprint, App};
use tauri::{AppHandle, Emitter, Manager};

use crate::cache;
use crate::resident;

const STATE_INTERVAL: Duration = Duration::from_secs(2);

static POKE: LazyLock<(Mutex<()>, Condvar)> = LazyLock::new(|| (Mutex::new(()), Condvar::new()));

struct CatalogCache {
    print: String,
    apps: Vec<App>,
}

static CATALOG: LazyLock<Mutex<CatalogCache>> = LazyLock::new(|| {
    Mutex::new(CatalogCache {
        print: String::new(),
        apps: Vec::new(),
    })
});

pub fn poke() {
    POKE.1.notify_all();
}

/// 一次完整读取之后记住清单，状态探测沿用这份，不再自己扫目录。
pub fn remember(apps: &[App]) {
    let mut guard = CATALOG.lock().unwrap_or_else(|p| p.into_inner());
    guard.print = fingerprint(apps);
    guard.apps = apps.to_vec();
}

#[derive(Clone, serde::Serialize)]
struct StateRow {
    id: String,
    state: String,
}

#[derive(Clone, serde::Serialize)]
pub struct Rescan {
    pub added: Vec<String>,
    pub removed: Vec<String>,
    pub total: usize,
    pub changed: bool,
}

pub fn start(app: AppHandle) {
    remember(&app.state::<crate::Ws>().0.apps());
    std::thread::spawn(move || state_loop(app));
}

/// 手动重扫应用目录。指纹没变就不换界面、不换托盘。
pub fn rescan(app: &AppHandle) -> Result<Rescan, String> {
    let apps = app.state::<crate::Ws>().0.apps();
    let fresh = fingerprint(&apps);
    let report = {
        let mut guard = CATALOG.lock().unwrap_or_else(|p| p.into_inner());
        let old_ids: HashSet<&str> = guard.apps.iter().map(|item| item.id.as_str()).collect();
        let new_ids: HashSet<&str> = apps.iter().map(|item| item.id.as_str()).collect();
        let added = apps
            .iter()
            .filter(|item| !old_ids.contains(item.id.as_str()))
            .map(|item| item.title.clone())
            .collect();
        let removed = guard
            .apps
            .iter()
            .filter(|item| !new_ids.contains(item.id.as_str()))
            .map(|item| item.title.clone())
            .collect();
        let changed = fresh != guard.print;
        guard.print = fresh;
        guard.apps = apps;
        Rescan {
            added,
            removed,
            total: guard.apps.iter().filter(|item| !item.hidden).count(),
            changed,
        }
    };
    if report.changed {
        let _ = app.emit("launcher://catalog-changed", ());
        if let Err(error) = resident::refresh_menu(app) {
            eprintln!("托盘菜单没能跟上清单：{error}");
        }
    }
    Ok(report)
}

fn state_loop(app: AppHandle) {
    let (lock, cv) = &*POKE;
    let mut last: Option<Vec<(String, String)>> = None;
    loop {
        let shown = app
            .try_state::<resident::Shown>()
            .map(|shown| shown.0.load(Ordering::SeqCst))
            .unwrap_or(false);
        if !shown {
            last = None;
            let guard = lock.lock().unwrap_or_else(|p| p.into_inner());
            drop(cv.wait(guard).unwrap_or_else(|p| p.into_inner()));
            continue;
        }
        let apps = CATALOG.lock().unwrap_or_else(|p| p.into_inner()).apps.clone();
        if !apps.is_empty() {
            let states = cache::states(&apps);
            let rows: Vec<StateRow> = apps
                .iter()
                .zip(states)
                .map(|(item, state)| StateRow {
                    id: item.id.clone(),
                    state: state.key().to_string(),
                })
                .collect();
            let sig: Vec<(String, String)> = rows.iter().map(|row| (row.id.clone(), row.state.clone())).collect();
            if last.as_ref() != Some(&sig) {
                last = Some(sig);
                let _ = app.emit("launcher://states", &rows);
            }
        }
        let guard = lock.lock().unwrap_or_else(|p| p.into_inner());
        drop(
            cv.wait_timeout(guard, STATE_INTERVAL)
                .unwrap_or_else(|p| p.into_inner()),
        );
    }
}
