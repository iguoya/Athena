// Athena 网络与信息安全 —— 独立壳。骨架阶段只有窗口与内容分发；
// 实验引擎（Tokio 真 socket + RustCrypto 真算）随内容填充期落地，命令一律白名单
// （仓库 ADR 0091 决策 3、0103）。

pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
