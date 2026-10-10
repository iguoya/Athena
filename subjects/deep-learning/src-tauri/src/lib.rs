// Athena 深度学习与 PyTorch —— 独立壳。骨架阶段只有窗口与内容分发；
// 实验引擎（本机 python 子进程真跑）随内容填充期落地，命令一律白名单
// （仓库 ADR 0091 决策 3 同规）。

pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
