use std::path::Path;

use resvg::tiny_skia::{Pixmap, Transform};
use resvg::usvg;

fn main() {
    // 先渲虎头位图，再编 Slint：Window.icon 要引用 build 写出的 PNG。
    let svg_path = Path::new(env!("CARGO_MANIFEST_DIR")).join("assets/tiger.svg");
    println!("cargo:rerun-if-changed={}", svg_path.display());
    let tree = load_tiger(&svg_path);
    let crop = head_crop(&tree);

    write_icon("tray-icon.rgba", render_crop(&tree, crop, 64));
    write_icon("window-icon.rgba", render_crop(&tree, crop, 256));
    write_window_png(&tree, crop);

    #[cfg(target_os = "windows")]
    embed_windows_icon(&tree, crop);

    slint_build::compile("ui/launcher.slint").expect("Slint 界面编译失败");
}

fn load_tiger(path: &Path) -> usvg::Tree {
    let data = std::fs::read(path).unwrap_or_else(|err| panic!("读不到 {}：{err}", path.display()));
    usvg::Tree::from_data(&data, &usvg::Options::default())
        .unwrap_or_else(|err| panic!("{} 不是合法 SVG：{err}", path.display()))
}

fn write_icon(name: &str, pixmap: Pixmap) {
    let out = Path::new(&std::env::var("OUT_DIR").expect("没有 OUT_DIR")).join(name);
    std::fs::write(out, straight_rgba(pixmap)).expect("写不出图标");
}

/// 给 Slint `Window.icon` 用：@image-url 要能在编译期读到的真实文件。
/// 写到 assets/，跟 tiger.svg 同源裁切，标题栏才能跟托盘 / 任务栏对上。
fn write_window_png(tree: &usvg::Tree, crop: Crop) {
    let pixmap = render_crop(tree, crop, 256);
    let rgba = straight_rgba(pixmap);
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("assets/tiger-mark.png");
    write_png(&path, 256, 256, &rgba);
}

fn write_png(path: &Path, width: u32, height: u32, rgba: &[u8]) {
    // 最小 PNG 编码器：不引额外依赖。Slint 认 PNG；RGBA 直通。
    let mut encoder = png::Encoder::new(
        std::fs::File::create(path).expect("写不出 tiger-mark.png"),
        width,
        height,
    );
    encoder.set_color(png::ColorType::Rgba);
    encoder.set_depth(png::BitDepth::Eight);
    let mut writer = encoder.write_header().expect("PNG 头写失败");
    writer.write_image_data(rgba).expect("PNG 像素写失败");
}

/// SVG 用户坐标里的正方形裁剪框（tiger.svg 的 viewBox 是 800×800）。
#[derive(Clone, Copy)]
struct Crop {
    x: f32,
    y: f32,
    size: f32,
}

/// 先按不透明像素框出整只虎，再取**朝向一侧的头部正方形**。
/// 这张 Illustrator 图是侧身朝右：头在包围盒右端，不是顶上——按「取顶部」会裁到肋部斑纹。
fn head_crop(tree: &usvg::Tree) -> Crop {
    const WORK: u32 = 400;
    let mut pixmap = Pixmap::new(WORK, WORK).expect("分配位图失败");
    let src = tree.size();
    let scale = (WORK as f32 / src.width()).min(WORK as f32 / src.height());
    resvg::render(tree, Transform::from_scale(scale, scale), &mut pixmap.as_mut());

    let Some((min_x, min_y, max_x, max_y)) = opaque_bounds(&pixmap) else {
        return Crop {
            x: 0.0,
            y: 0.0,
            size: src.width().min(src.height()),
        };
    };

    let width = (max_x - min_x + 1) as f32;
    let height = (max_y - min_y + 1) as f32;
    // 脸在右上：正方形贴着眼鼻与耳，左侧少带肩背。
    let side = (height * 0.48).min(width * 0.28);
    let head_cx = min_x as f32 + width * 0.88;
    let head_cy = min_y as f32 + height * 0.26;
    let x = (head_cx - side * 0.52).max(0.0);
    let y = (head_cy - side * 0.45).max(0.0);
    let size = side.min((WORK as f32 - x).min(WORK as f32 - y));

    Crop {
        x: x / scale,
        y: y / scale,
        size: size / scale,
    }
}

fn opaque_bounds(pixmap: &Pixmap) -> Option<(u32, u32, u32, u32)> {
    let width = pixmap.width();
    let height = pixmap.height();
    let data = pixmap.data();
    let mut min_x = width;
    let mut min_y = height;
    let mut max_x = 0u32;
    let mut max_y = 0u32;
    for y in 0..height {
        for x in 0..width {
            let alpha = data[((y * width + x) * 4 + 3) as usize];
            if alpha <= 12 {
                continue;
            }
            min_x = min_x.min(x);
            min_y = min_y.min(y);
            max_x = max_x.max(x);
            max_y = max_y.max(y);
        }
    }
    (min_x <= max_x).then_some((min_x, min_y, max_x, max_y))
}

fn render_crop(tree: &usvg::Tree, crop: Crop, size: u32) -> Pixmap {
    let mut pixmap = Pixmap::new(size, size).expect("分配位图失败");
    let scale = size as f32 / crop.size;
    let transform = Transform::from_scale(scale, scale).pre_translate(-crop.x, -crop.y);
    resvg::render(tree, transform, &mut pixmap.as_mut());
    pixmap
}

/// tiny_skia 是预乘 alpha；托盘、winit、ICO、PNG 都要直通 RGBA。
fn straight_rgba(pixmap: Pixmap) -> Vec<u8> {
    let mut data = pixmap.take();
    for pixel in data.chunks_exact_mut(4) {
        let alpha = pixel[3] as u32;
        if alpha == 0 || alpha == 255 {
            continue;
        }
        pixel[0] = ((pixel[0] as u32 * 255 + alpha / 2) / alpha).min(255) as u8;
        pixel[1] = ((pixel[1] as u32 * 255 + alpha / 2) / alpha).min(255) as u8;
        pixel[2] = ((pixel[2] as u32 * 255 + alpha / 2) / alpha).min(255) as u8;
    }
    data
}

/// 同一份虎头打成多分辨率 `.ico`，编进 exe。标题栏走 Window.icon，
/// 任务栏 / 资源管理器认资源段，两边像素来源相同。
#[cfg(target_os = "windows")]
fn embed_windows_icon(tree: &usvg::Tree, crop: Crop) {
    let mut icon_dir = ico::IconDir::new(ico::ResourceType::Icon);
    for size in [16u32, 24, 32, 48, 64, 128, 256] {
        let pixmap = render_crop(tree, crop, size);
        let image = ico::IconImage::from_rgba_data(size, size, straight_rgba(pixmap));
        icon_dir.add_entry(ico::IconDirEntry::encode(&image).expect("编码 ICO 帧失败"));
    }

    let out_dir = std::env::var("OUT_DIR").expect("没有 OUT_DIR");
    let ico_path = Path::new(&out_dir).join("app.ico");
    let file = std::fs::File::create(&ico_path).expect("写不出 app.ico");
    icon_dir.write(file).expect("写 ICO 失败");

    winresource::WindowsResource::new()
        .set_icon(ico_path.to_str().expect("OUT_DIR 路径含非 UTF-8 字符"))
        .compile()
        .expect("把图标编译进 exe 资源段失败");
}
