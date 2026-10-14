// Athena 数据结构 — 壳本体在共用 crate（ADR 0161）；这里只给出本应用的几个名字。

use athena_course_shell::ShellConfig;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    athena_course_shell::run(
        ShellConfig {
            binary: "athena-data-structures",
            title: "数据结构与算法",
            root_env: "ATHENA_DATA_STRUCTURES_ROOT",
            // 与 app.json 的 progress.dir 一致，启动器据此找库同步（ADR 0155）。
            data_dir: "AthenaDataStructures",
            version: env!("CARGO_PKG_VERSION"),
            manifest_dir: env!("CARGO_MANIFEST_DIR"),
        },
        tauri::generate_context!(),
    );
}
