// Athena 计算机组成原理 — 壳本体在共用 crate（ADR 0157）；这里只给出本应用的几个名字。

use athena_course_shell::ShellConfig;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    athena_course_shell::run(
        ShellConfig {
            binary: "athena-organization",
            title: "计算机组成原理",
            root_env: "ATHENA_ORGANIZATION_ROOT",
            // 与 app.json 的 progress.dir 一致，启动器据此找库同步（ADR 0155）。
            data_dir: "AthenaOrganization",
            version: env!("CARGO_PKG_VERSION"),
            manifest_dir: env!("CARGO_MANIFEST_DIR"),
        },
        tauri::generate_context!(),
    );
}
