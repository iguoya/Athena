use std::path::Path;

fn main() {
    slint_build::compile("ui/launcher.slint").expect("Slint 界面编译失败");
    render_tray_icon();
}

/// 把 `assets/tiger.svg` 渲染成 64×64 的 RGBA 点阵交给托盘。
///
/// 那是一整只侧身老虎（Athena 早期欢迎页的主视觉，2026-08-30 随欢迎页一起删掉，
/// 这里从 git 历史里取回来）。整只缩到菜单栏的 22pt 只剩一条糊掉的色块，所以
/// 只取头部那一块：改 viewBox 式的裁剪，靠变换矩阵完成，仓库里仍然只存一份原图。
///
/// 放在构建期做：源文件保持成可编辑的 SVG，运行时的二进制里只有一段裸像素，
/// 不必带 SVG 解析和 PNG 解码。
fn render_tray_icon() {
    let source = Path::new("assets/tiger.svg");
    println!("cargo:rerun-if-changed={}", source.display());

    let svg = std::fs::read(source).expect("读不到托盘图标");
    let options = resvg::usvg::Options::default();
    let tree = resvg::usvg::Tree::from_data(&svg, &options).expect("托盘图标不是有效的 SVG");

    const SIZE: u32 = 64;
    // 原图 800×800 里虎头所在的方框，试出来的构图。收得比"整个头"更紧一些：
    // 菜单栏只有 22pt 高，留白越多脸越小，认不出是什么。
    const CROP: (f32, f32, f32) = (573.0, 212.0, 182.0);

    let scale = SIZE as f32 / CROP.2;
    let transform = resvg::tiny_skia::Transform::from_scale(scale, scale)
        .pre_translate(-CROP.0, -CROP.1);

    let mut pixmap = resvg::tiny_skia::Pixmap::new(SIZE, SIZE).expect("分配位图失败");
    resvg::render(&tree, transform, &mut pixmap.as_mut());

    let out = Path::new(&std::env::var("OUT_DIR").expect("没有 OUT_DIR")).join("tray-icon.rgba");
    std::fs::write(out, pixmap.take()).expect("写不出托盘图标");
}
