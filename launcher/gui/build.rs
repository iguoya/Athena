use std::path::Path;

use resvg::tiny_skia::{Pixmap, Transform};
use resvg::usvg;

fn main() {
    // 先渲虎头位图，再编 Slint：Window.icon 要引用 build 写出的 PNG。
    // tiger.svg 本身就是完整的方形图标（Fluent 虎头，ADR 0065），不再裁切。
    let svg_path = Path::new(env!("CARGO_MANIFEST_DIR")).join("assets/tiger.svg");
    println!("cargo:rerun-if-changed={}", svg_path.display());
    let tree = load_tiger(&svg_path);

    write_icon("tray-icon.rgba", render(&tree, 64));
    write_icon("window-icon.rgba", render(&tree, 256));
    write_window_png(&tree);
    // Dock 图标：macOS 裸二进制没有 bundle，运行时用 NSImage 读这张 PNG。
    let dock = render(&tree, 512).encode_png().expect("PNG 编码失败");
    std::fs::write(
        Path::new(&std::env::var("OUT_DIR").expect("没有 OUT_DIR")).join("dock-icon.png"),
        dock,
    )
    .expect("写不出 dock-icon.png");

    #[cfg(target_os = "windows")]
    embed_windows_icon(&tree);

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
/// 写到 assets/，跟托盘 / 任务栏同一份 tiger.svg，标题栏才对得上。
fn write_window_png(tree: &usvg::Tree) {
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("assets/tiger-mark.png");
    let png = render(tree, 256).encode_png().expect("PNG 编码失败");
    std::fs::write(&path, png).expect("写不出 tiger-mark.png");
}

/// 按边长 `size` 渲染，等比缩放后居中。每个尺寸都从矢量直接画，16px 托盘图才不糊。
fn render(tree: &usvg::Tree, size: u32) -> Pixmap {
    let mut pixmap = Pixmap::new(size, size).expect("分配位图失败");
    let source = tree.size();
    let scale = (size as f32 / source.width()).min(size as f32 / source.height());
    let transform = Transform::from_scale(scale, scale).pre_translate(
        (size as f32 / scale - source.width()) / 2.0,
        (size as f32 / scale - source.height()) / 2.0,
    );
    resvg::render(tree, transform, &mut pixmap.as_mut());
    pixmap
}

/// tiny_skia 是预乘 alpha；托盘、winit、ICO 都要直通 RGBA。
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
fn embed_windows_icon(tree: &usvg::Tree) {
    let mut icon_dir = ico::IconDir::new(ico::ResourceType::Icon);
    for size in [16u32, 20, 24, 32, 40, 48, 64, 128, 256] {
        let image = ico::IconImage::from_rgba_data(size, size, straight_rgba(render(tree, size)));
        icon_dir.add_entry(ico::IconDirEntry::encode_as_png(&image).expect("编码 ICO 帧失败"));
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
