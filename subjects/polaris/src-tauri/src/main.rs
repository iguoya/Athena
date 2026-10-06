// 发行版在 Windows 上不弹出多余的控制台窗口。
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    athena_polaris_lib::run()
}
