//! 重负载缓存。清单只在打开窗口和手动「扫描应用」时重建；运行状态由窗口
//! 可见时的探测线程触发。两处都会进到这里。其中三样重负载只随盘上文件变化：
//! icon 的 resvg 渲染、全进程表快照、同心环底图位图。缓住它们，重复进来的
//! 同一份输入才不会把主进程重新打满。

use std::collections::HashMap;
use std::hash::{Hash, Hasher};
use std::path::{Path, PathBuf};
use std::sync::{LazyLock, Mutex};
use std::time::SystemTime;

use base64::Engine as _;
use launcher_core::manifest;
use launcher_core::mindmap::{self, MindMap};
use launcher_core::runner::{ProcessSnapshot, RunState};

struct CacheEntry {
    fingerprint: (SystemTime, u64),
    url: String,
}

static ICON_CACHE: LazyLock<Mutex<HashMap<PathBuf, CacheEntry>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));

/// icon.svg → 256px PNG 的 data URL，按 (mtime, len) 指纹缓存，图标文件改了
/// 才重渲染。不用 SVG data URL 直传：WebView2 里 `new Image()` 加载 SVG
/// data URL 的 onload 会悬挂（贴图永远停在 loading），而且用 core 的 resvg
/// 渲染位图，Fluent Emoji 的滤镜表现反而更有保障。
pub fn icon_data_url(path: &Path) -> Option<String> {
    let meta = std::fs::metadata(path).ok()?;
    let fingerprint = (meta.modified().ok()?, meta.len());
    if let Some(hit) = ICON_CACHE
        .lock()
        .unwrap_or_else(|p| p.into_inner())
        .get(path)
    {
        if hit.fingerprint == fingerprint {
            return Some(hit.url.clone());
        }
    }
    let tree = launcher_core::icons::load(path).ok()?;
    let pixmap = launcher_core::icons::render(&tree, 256).ok()?;
    let png = pixmap.encode_png().ok()?;
    let url = format!(
        "data:image/png;base64,{}",
        base64::engine::general_purpose::STANDARD.encode(png)
    );
    ICON_CACHE.lock().unwrap_or_else(|p| p.into_inner()).insert(
        path.to_path_buf(),
        CacheEntry {
            fingerprint,
            url: url.clone(),
        },
    );
    Some(url)
}

static SNAPSHOT: LazyLock<Mutex<Option<ProcessSnapshot>>> = LazyLock::new(|| Mutex::new(None));

/// 全部应用的运行状态。进程表全局只建一次，之后每轮增量刷新——runner 的
/// 注释写明常驻探测别每轮从零建表（本机全量一轮 0.5–6.6 秒），轮询路径同理。
/// 锁同时把并发的轮询请求串行化：命令慢于间隔时后来者排队，而不是把浪费翻倍。
pub fn states(apps: &[manifest::App]) -> Vec<RunState> {
    let mut guard = SNAPSHOT.lock().unwrap_or_else(|p| p.into_inner());
    match guard.as_mut() {
        None => *guard = Some(ProcessSnapshot::take()),
        Some(snapshot) => snapshot.refresh(),
    }
    let states = guard.as_ref().expect("上一行刚放入快照").states(apps);
    // 常驻时顺带做进度同步（ADR 0155）：节流、后台线程，不拖慢这条每 3 秒一次的轮询。
    launcher_core::progress_sync::tick(apps, &states);
    states
}

/// 同心环底图：PNG data URL 加摆放坐标。环是静态装饰，布局没变就复用上一张。
#[derive(Clone)]
pub struct RingsImage {
    pub data_url: String,
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

static RINGS_CACHE: LazyLock<Mutex<Option<(u64, RingsImage)>>> = LazyLock::new(|| Mutex::new(None));

pub fn rings_png(map: &MindMap, scale: f32) -> RingsImage {
    let fingerprint = layout_fingerprint(map, scale);
    let guard = RINGS_CACHE.lock().unwrap_or_else(|p| p.into_inner());
    if let Some((seen, image)) = guard.as_ref() {
        if *seen == fingerprint {
            return image.clone();
        }
    }
    drop(guard);
    let rendered = mindmap::rings_png(map, scale);
    let image = RingsImage {
        data_url: format!(
            "data:image/png;base64,{}",
            base64::engine::general_purpose::STANDARD.encode(rendered.png)
        ),
        x: rendered.x,
        y: rendered.y,
        width: rendered.width,
        height: rendered.height,
    };
    *RINGS_CACHE.lock().unwrap_or_else(|p| p.into_inner()) = Some((fingerprint, image.clone()));
    image
}

/// 布局指纹：环底图只由画布尺寸、环半径、组胶囊与节点位置决定，连线悬停态
/// 不参与。f32 不实现 Hash，逐个走 to_bits。
fn layout_fingerprint(map: &MindMap, scale: f32) -> u64 {
    let mut hasher = std::collections::hash_map::DefaultHasher::new();
    scale.to_bits().hash(&mut hasher);
    map.width.to_bits().hash(&mut hasher);
    map.height.to_bits().hash(&mut hasher);
    for ring in &map.rings {
        ring.0.to_bits().hash(&mut hasher);
        ring.1.to_bits().hash(&mut hasher);
    }
    for group in &map.groups {
        group.name.hash(&mut hasher);
        group.at.x.to_bits().hash(&mut hasher);
        group.at.y.to_bits().hash(&mut hasher);
        group.width.to_bits().hash(&mut hasher);
    }
    for node in &map.nodes {
        node.id.hash(&mut hasher);
        node.at.x.to_bits().hash(&mut hasher);
        node.at.y.to_bits().hash(&mut hasher);
        node.layer.hash(&mut hasher);
    }
    hasher.finish()
}
