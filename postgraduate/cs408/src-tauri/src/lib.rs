// Athena 408 计算机学科专业基础 — 壳本体在共用 crate（ADR 0157）；这里只给出本应用的几个名字。

use athena_course_shell::ShellConfig;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    athena_course_shell::run(
        ShellConfig {
            binary: "athena-cs408",
            title: "408 计算机学科专业基础",
            root_env: "ATHENA_CS408_ROOT",
            // 与 app.json 的 progress.dir 一致，启动器据此找库同步（ADR 0155）。
            data_dir: "AthenaCs408",
            version: env!("CARGO_PKG_VERSION"),
            manifest_dir: env!("CARGO_MANIFEST_DIR"),
        },
        tauri::generate_context!(),
    );
}
