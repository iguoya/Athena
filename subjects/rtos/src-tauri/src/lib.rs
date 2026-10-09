// Athena 实时操作系统（RTOS） —— 独立壳。骨架阶段只有窗口与内容分发；
// 实验引擎（FreeRTOS 真板观测 / QEMU 交叉编译 / 线程级模拟）随内容填充期
// 落地，命令一律白名单（仓库 ADR 0091 决策 3、0106）。

pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
