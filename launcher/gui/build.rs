use std::path::Path;

fn main() {
    slint_build::compile("ui/launcher.slint").expect("Slint 界面编译失败");
    render_tray_icon();
}

/// 把 `assets/tray-icon.svg` 渲染成 64×64 的 RGBA 点阵交给托盘。
///
/// 放在构建期做：源文件保持成可编辑的 SVG，而运行时的二进制里只有一段裸像素，
/// 不必带 SVG 解析和 PNG 解码。
fn render_tray_icon() {
    let source = Path::new("assets/tray-icon.svg");
    println!("cargo:rerun-if-changed={}", source.display());

    let svg = std::fs::read(source).expect("读不到托盘图标");
    let options = resvg::usvg::Options::default();
    let tree = resvg::usvg::Tree::from_data(&svg, &options).expect("托盘图标不是有效的 SVG");

    const SIZE: u32 = 64;
    let size = tree.size();
    let scale = (SIZE as f32 / size.width()).min(SIZE as f32 / size.height());
    let transform = resvg::tiny_skia::Transform::from_scale(scale, scale).pre_translate(
        (SIZE as f32 / scale - size.width()) / 2.0,
        (SIZE as f32 / scale - size.height()) / 2.0,
    );

    let mut pixmap = resvg::tiny_skia::Pixmap::new(SIZE, SIZE).expect("分配位图失败");
    resvg::render(&tree, transform, &mut pixmap.as_mut());

    let out = Path::new(&std::env::var("OUT_DIR").expect("没有 OUT_DIR")).join("tray-icon.rgba");
    std::fs::write(out, pixmap.take()).expect("写不出托盘图标");
}
