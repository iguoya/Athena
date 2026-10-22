fn main() {
    // 一旦声明应用清单，列出的命令才有 allow-* 权限可授；没列的命令会被拒（"not allowed. Command not found"）。
    // 所以这里列全部命令：界面 webview 拿到除 bridge_report 以外的全部，播放器页面只拿 bridge_report（capabilities/player.json，ADR 0182 决策 3）。
    tauri_build::try_build(tauri_build::Attributes::new().app_manifest(tauri_build::AppManifest::new().commands(&[
        "get_curriculum",
        "get_lesson",
        "open_external",
        "record_attempt",
        "get_attempts",
        "player_load",
        "player_seek",
        "player_ping",
        "player_poll",
        "player_play",
        "player_pause",
        "player_set_pause_point",
        "player_set_visible",
        "bridge_report",
        "open_login",
        "save_marks",
        "load_marks",
    ])))
    .expect("tauri build failed");
}
