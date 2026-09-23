//! 把应用自带的 SVG 图标渲染成界面能用的位图。
//!
//! 图标放在各应用自己的目录里（`subjects/<id>/icon.svg`），由 `app.json` 指名。
//! 启动器不认识谁是谁——新增一个应用，自带一张图标就显示得出来。
//!
//! 启动器自己的标志来自 `assets/tiger.svg`，构建期裁出虎头：
//! - 标题栏：`Window.icon` → `assets/tiger-mark.png`
//! - 托盘：`tray-icon.rgba`
//! - 任务栏 / exe：多尺寸 `.ico`
//! 三处同源，不要另做一张。

use std::path::Path;

use slint::{Image, Rgba8Pixel, SharedPixelBuffer};

/// 渲染成边长 `size` 的位图。图标本身是纯白的，配 `accent` 底色显示，
/// 所以这里不处理颜色。读不到或不是合法 SVG 时返回 None，界面退回显示文字。
pub fn render(path: &Path, size: u32) -> Option<Image> {
    let svg = std::fs::read(path).ok()?;
    let tree = resvg::usvg::Tree::from_data(&svg, &resvg::usvg::Options::default()).ok()?;

    let source = tree.size();
    let scale = (size as f32 / source.width()).min(size as f32 / source.height());
    let transform = resvg::tiny_skia::Transform::from_scale(scale, scale).pre_translate(
        (size as f32 / scale - source.width()) / 2.0,
        (size as f32 / scale - source.height()) / 2.0,
    );

    let mut pixmap = resvg::tiny_skia::Pixmap::new(size, size)?;
    resvg::render(&tree, transform, &mut pixmap.as_mut());

    let mut buffer = SharedPixelBuffer::<Rgba8Pixel>::new(size, size);
    buffer
        .make_mut_bytes()
        .copy_from_slice(pixmap.data());
    Some(Image::from_rgba8_premultiplied(buffer))
}
