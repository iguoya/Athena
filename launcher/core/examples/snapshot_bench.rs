//! 临时基准：量 ProcessSnapshot 的 take/refresh 与 states() 在本机的耗时。
//! 用完即删，不进提交。

use std::time::Instant;

fn main() {
    let repo = launcher_core::paths::locate_repo().expect("找不到仓库");
    let apps = launcher_core::discover(&repo);
    println!("{} 个学习应用", apps.len());
    let mut snapshot = launcher_core::ProcessSnapshot::take();
    for round in 0..6 {
        let t0 = Instant::now();
        snapshot.refresh();
        let t1 = Instant::now();
        let states = snapshot.states(&apps);
        let ready = states
            .iter()
            .filter(|state| **state == launcher_core::RunState::Ready)
            .count();
        println!(
            "第 {round} 轮：refresh() {:?}，states×{} {:?}，ready={ready}",
            t1 - t0,
            apps.len(),
            Instant::now() - t1
        );
        std::thread::sleep(std::time::Duration::from_secs(2));
    }
}
