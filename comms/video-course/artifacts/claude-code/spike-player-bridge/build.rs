fn main() {
    // 自定义命令默认不对页面开放；给远程页面用的 bridge_report 要在应用清单里声明，
    // 才会生成可在 capability 里引用的 allow-bridge-report 权限。
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .app_manifest(tauri_build::AppManifest::new().commands(&["bridge_report"])),
    )
    .expect("tauri build failed");
}
