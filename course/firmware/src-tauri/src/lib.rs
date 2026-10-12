// Athena 嵌入式程序设计 —— 独立壳。骨架阶段只有窗口与内容分发；
// 实验引擎（gcc 真编译 + 位级可视化）随内容填充期落地，命令一律白名单
// （仓库 ADR 0091 决策 3、0103）。

pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
