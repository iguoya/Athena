//! 开机自启（仅 Windows）。
//!
//! 每个系统各有一套自启机制，这里只做 Windows 的那一套：HKCU 的 `Run` 键。
//! macOS 要 LoginItems、Linux 要 XDG autostart 的 .desktop，机制和验证方式
//! 都不一样，按 ADR 0047、0049 的口径不假装支持——别的平台托盘菜单里根本
//! 不出现这一项（见 tray.rs 的条件编译）。
//!
//! 勾选状态以注册表为准，启动器不记自己的账：`is_enabled` 每次现读，托盘
//! 菜单重建时照它画勾。默认关——不先问就把启动器写进自启不是本分。

use std::path::PathBuf;

/// 注册表值名。写全名而不是叫 "Athena"：Run 键是用户级公共地界，
/// 名字要能让人一眼认出是谁写的、好手动删。
const VALUE_NAME: &str = "athena-launcher";

/// 当前可执行文件的全路径：自启要指的就是这一份，别的路径会绕过单实例。
fn exe_path() -> Result<PathBuf, String> {
    std::env::current_exe().map_err(|error| format!("拿不到自身路径：{error}"))
}

fn run_key() -> Result<winreg::RegKey, String> {
    use winreg::enums::HKEY_CURRENT_USER;
    winreg::RegKey::predef(HKEY_CURRENT_USER)
        .open_subkey_with_flags(r"Software\Microsoft\Windows\CurrentVersion\Run", winreg::enums::KEY_READ | winreg::enums::KEY_WRITE)
        .map_err(|error| format!("打不开注册表 Run 键：{error}"))
}

pub fn is_enabled() -> bool {
    run_key().is_ok_and(|key| key.get_value::<String, _>(VALUE_NAME).is_ok())
}

pub fn enable() -> Result<(), String> {
    let path = exe_path()?;
    let key = run_key()?;
    key.set_value(VALUE_NAME, &path.to_string_lossy().to_string())
        .map_err(|error| format!("写入自启失败：{error}"))
}

pub fn disable() -> Result<(), String> {
    let key = run_key()?;
    key.delete_value(VALUE_NAME)
        .map_err(|error| format!("删除自启失败：{error}"))
}

/// 勾选状态翻转：菜单点击的唯一动作，注册表是唯一的事实来源。
pub fn toggle() -> Result<bool, String> {
    if is_enabled() {
        disable()?;
        Ok(false)
    } else {
        enable()?;
        Ok(true)
    }
}
