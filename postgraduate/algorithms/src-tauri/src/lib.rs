// Athena 算法设计 — 壳本体在共用 crate（ADR 0161）；这里只给出本应用的几个名字。

use athena_course_shell::ShellConfig;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    athena_course_shell::run(
        ShellConfig {
            binary: "athena-algorithms",
            title: "算法设计",
            root_env: "ATHENA_ALGORITHMS_ROOT",
            // 与 app.json 的 progress.dir 一致，启动器据此找库同步（ADR 0155）。
            data_dir: "AthenaAlgorithms",
            version: env!("CARGO_PKG_VERSION"),
            manifest_dir: env!("CARGO_MANIFEST_DIR"),
        },
        tauri::generate_context!(),
    );
}
