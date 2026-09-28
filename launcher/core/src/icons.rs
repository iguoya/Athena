//! `launcher icons`：把各应用的 `icon.svg` 渲染成它在 `app.json` 里声明的位图。
//!
//! 图标只有一份源（ADR 0065）：启动器图块、窗口 / 任务栏、应用自己的界面都从
//! `icon.svg` 来。可平台图标位——`.ico`、`.icns`、Tauri 的一组 PNG、GTK 图标主题、
//! Flutter 资源——都要位图，而 Fluent Emoji 的 SVG 大量用滤镜，Qt SVG、GTK、
//! flutter_svg 各画各的。所以位图在这里用 resvg 一次渲染好、提交进各应用目录，
//! 应用构建时只读普通文件，不依赖启动器。
//!
//! 这里没有按应用写的分支：要哪些文件、多大，全由 `icon.renders` 声明。

use std::path::Path;

use resvg::tiny_skia::{Pixmap, Transform};
use resvg::usvg;

use crate::manifest::{App, RenderSpec};

/// `.ico` 里放的边长。20 / 40 是 Windows 125%、250% 缩放下任务栏实际取的尺寸，
/// 缺了它们系统会拿相邻尺寸缩放，小图标发糊。
const ICO_SIZES: [u32; 9] = [16, 20, 24, 32, 40, 48, 64, 128, 256];
/// `.icns` 能装的全部 PNG 尺寸（icns crate 按边长选 OSType）。
const ICNS_SIZES: [u32; 7] = [16, 32, 64, 128, 256, 512, 1024];

/// 一次运行的结果：写了几份、有几份和源不一致（`--check` 时只数不写）。
#[derive(Debug, Default)]
pub struct Report {
    pub written: usize,
    pub stale: usize,
    pub unchanged: usize,
}

/// 渲染 `apps` 里每个声明了 `icon.renders` 的应用。`check` 为真时不写文件，
/// 只把过期的列出来。每处理一个文件调一次 `line`，给终端输出用。
pub fn render_all(apps: &[App], check: bool, mut line: impl FnMut(&str)) -> Result<Report, String> {
    let mut report = Report::default();
    for app in apps {
        if app.icon_renders.is_empty() {
            continue;
        }
        let Some(source) = &app.icon_file else {
            return Err(format!("{}：声明了 icon.renders，却没有可读的 icon.file", app.id));
        };
        let tree = load(source)?;
        for (relative, spec) in &app.icon_renders {
            let target = app.dir.join(relative);
            let bytes = encode(&tree, *spec).map_err(|error| format!("{}：{relative}：{error}", app.id))?;
            let current = std::fs::read(&target).ok();
            if current.as_deref() == Some(bytes.as_slice()) {
                report.unchanged += 1;
                continue;
            }
            if check {
                report.stale += 1;
                line(&format!("过期  {}/{relative}", app.id));
                continue;
            }
            if let Some(parent) = target.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|error| format!("建不了 {}：{error}", parent.display()))?;
            }
            std::fs::write(&target, &bytes)
                .map_err(|error| format!("写不了 {}：{error}", target.display()))?;
            report.written += 1;
            line(&format!("写入  {}/{relative}", app.id));
        }
    }
    Ok(report)
}

pub fn load(path: &Path) -> Result<usvg::Tree, String> {
    let data = std::fs::read(path).map_err(|error| format!("读不到 {}：{error}", path.display()))?;
    usvg::Tree::from_data(&data, &usvg::Options::default())
        .map_err(|error| format!("{} 不是合法 SVG：{error}", path.display()))
}

fn encode(tree: &usvg::Tree, spec: RenderSpec) -> Result<Vec<u8>, String> {
    match spec {
        RenderSpec::Png(size) => render(tree, size)?
            .encode_png()
            .map_err(|error| format!("PNG 编码失败：{error}")),
        RenderSpec::Ico => {
            let mut dir = ico::IconDir::new(ico::ResourceType::Icon);
            for size in ICO_SIZES {
                let image = ico::IconImage::from_rgba_data(size, size, straight_rgba(render(tree, size)?));
                // 每一帧都存 PNG：体积小，且 Windows Vista 起全认；BMP 帧在 256 以下
                // 会被 ico crate 选上，alpha 边缘在深色任务栏上有毛边。
                let entry = ico::IconDirEntry::encode_as_png(&image)
                    .map_err(|error| format!("ICO 帧 {size} 编码失败：{error}"))?;
                dir.add_entry(entry);
            }
            let mut out = Vec::new();
            dir.write(&mut out).map_err(|error| format!("ICO 写出失败：{error}"))?;
            Ok(out)
        }
        RenderSpec::Icns => {
            let mut family = icns::IconFamily::new();
            for size in ICNS_SIZES {
                let image = icns::Image::from_data(
                    icns::PixelFormat::RGBA,
                    size,
                    size,
                    straight_rgba(render(tree, size)?),
                )
                .map_err(|error| format!("ICNS 帧 {size}：{error}"))?;
                family
                    .add_icon(&image)
                    .map_err(|error| format!("ICNS 帧 {size} 编码失败：{error}"))?;
            }
            let mut out = Vec::new();
            family.write(&mut out).map_err(|error| format!("ICNS 写出失败：{error}"))?;
            Ok(out)
        }
    }
}

/// 按边长 `size` 渲染，SVG 等比缩放后居中。每个尺寸都从矢量直接画，
/// 不从大图缩小——16px 的任务栏图标这样才不糊。
pub fn render(tree: &usvg::Tree, size: u32) -> Result<Pixmap, String> {
    let mut pixmap = Pixmap::new(size, size).ok_or_else(|| format!("分配不了 {size}×{size} 位图"))?;
    let source = tree.size();
    let scale = (size as f32 / source.width()).min(size as f32 / source.height());
    let transform = Transform::from_scale(scale, scale).pre_translate(
        (size as f32 / scale - source.width()) / 2.0,
        (size as f32 / scale - source.height()) / 2.0,
    );
    resvg::render(tree, transform, &mut pixmap.as_mut());
    Ok(pixmap)
}

/// tiny-skia 是预乘 alpha；ICO、ICNS 要直通 RGBA。
fn straight_rgba(pixmap: Pixmap) -> Vec<u8> {
    let mut data = pixmap.take();
    for pixel in data.chunks_exact_mut(4) {
        let alpha = pixel[3] as u32;
        if alpha == 0 || alpha == 255 {
            continue;
        }
        for channel in &mut pixel[..3] {
            *channel = ((*channel as u32 * 255 + alpha / 2) / alpha).min(255) as u8;
        }
    }
    data
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tree() -> usvg::Tree {
        let svg = br##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="4" y="4" width="24" height="24" rx="6" fill="#39f"/></svg>"##;
        usvg::Tree::from_data(svg, &usvg::Options::default()).unwrap()
    }

    #[test]
    fn png_has_requested_size() {
        let bytes = encode(&tree(), RenderSpec::Png(48)).unwrap();
        assert_eq!(&bytes[..8], b"\x89PNG\r\n\x1a\n");
        // IHDR 紧跟签名：宽、高各 4 字节大端。
        assert_eq!(u32::from_be_bytes(bytes[16..20].try_into().unwrap()), 48);
        assert_eq!(u32::from_be_bytes(bytes[20..24].try_into().unwrap()), 48);
    }

    #[test]
    fn ico_carries_every_taskbar_size() {
        let bytes = encode(&tree(), RenderSpec::Ico).unwrap();
        let dir = ico::IconDir::read(std::io::Cursor::new(bytes)).unwrap();
        let mut sizes: Vec<u32> = dir.entries().iter().map(|entry| entry.width()).collect();
        sizes.sort();
        assert_eq!(sizes, ICO_SIZES.to_vec());
    }

    #[test]
    fn rendering_is_deterministic() {
        // `--check` 靠逐字节比较判断过期，同一份 SVG 两次渲染必须一模一样。
        assert_eq!(encode(&tree(), RenderSpec::Icns).unwrap(), encode(&tree(), RenderSpec::Icns).unwrap());
    }
}
