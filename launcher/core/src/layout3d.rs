//! 学习应用面板的 3D 星系布局（ADR 0125）：一恒星、多行星、多卫星。
//!
//! 纯函数：输入每个分组的卫星数，输出每条行星轨道的空间姿态、每颗行星的世界坐标，
//! 以及每颗卫星绕本组行星的轨道参数。界面只负责渲染，布局能脱离窗口做单元测试。
//!
//! 角色：恒星是绑定到中心的应用（`anchor: center`，没有就是占位的发光球）；
//! 每个分组是一颗行星，独占一条轨道，绑定了应用的分组（`anchor: group`）里那个应用
//! 就是行星本身；分组里的其余应用是卫星，围着本组行星转。
//!
//! 几何（开普勒式）：恒星位于每个椭圆轨道的**公共焦点**上；所有椭圆长轴同向
//! （沿世界 X，宽屏横向），半长轴逐环外推。卫星按环排在行星周围，环半径随序号
//! 外推，卫星多的组自动多开一环；相邻行星轨道的间距大于最大卫星壳的直径，
//! 邻轨的卫星壳互不相碰。

/// 每条椭圆轨道的姿态：半长轴、半短轴、焦点距（中心到恒星的偏移）、绕 X 倾角。
/// 椭圆中心在 (-c, 0, 0)，恒星（原点）即长轴上的近侧焦点。
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct OrbitSpec {
    pub a: f32,
    pub b: f32,
    pub c: f32,
    pub tilt: f32,
}

/// 一颗行星（一个分组）：所在轨道、轨道参数角（含环起始错位）与世界坐标。
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct PlanetNode {
    pub group: usize,
    /// 椭圆参数角：公转动画沿它加时间项，与静态坐标同一套正变换，t=0 时与布局完全重合。
    pub theta: f32,
    pub pos: [f32; 3],
}

/// 一颗卫星：围着本组行星转的环位、半径与起始角。
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct MoonNode {
    pub group: usize,
    /// 组内第几颗卫星。
    pub slot: usize,
    /// 第几环（0 最内）。
    pub ring: usize,
    /// 绕行星的轨道半径。
    pub radius: f32,
    /// 起始角（rad），同环均匀分布，环间错开。
    pub theta: f32,
}

#[derive(Debug, Clone, PartialEq)]
pub struct SystemLayout {
    pub orbits: Vec<OrbitSpec>,
    pub planets: Vec<PlanetNode>,
    pub moons: Vec<MoonNode>,
}

/// 恒星球半径（与前端渲染一致）。
pub const STAR_R: f32 = 92.0;
/// 相邻两条轨道上的卫星壳之间、近点卫星壳与恒星之间至少留的空隙。
const CLEARANCE: f32 = 30.0;
const ECC: f32 = 0.18; // 离心率：有椭圆感，同时邻轨最窄处（近点侧）仍有 1-e 的间距比
const TILT: f32 = 0.087; // ≈5°，贴近真实太阳系的近共面
const GOLDEN: f32 = 2.39996; // 黄金角：各环的起始角错开，不对齐

/// 行星球半径、卫星球半径（与前端渲染一致）。
pub const PLANET_R: f32 = 44.0;
pub const MOON_R: f32 = 18.0;
/// 最内环卫星轨道半径与环距；相邻两颗卫星的中心至少隔 `MOON_SLOT`。
const RING0_R: f32 = 80.0;
const RING_STEP: f32 = 38.0;
const MOON_SLOT: f32 = 50.0;

/// 第 `ring` 环的轨道半径。
pub fn ring_radius(ring: usize) -> f32 {
    RING0_R + ring as f32 * RING_STEP
}

fn ring_capacity(ring: usize) -> usize {
    ((std::f32::consts::TAU * ring_radius(ring) / MOON_SLOT).floor() as usize).max(1)
}

/// 卫星壳的外半径（含卫星球本身）：该组卫星最外环半径加卫星球半径。
pub fn shell_radius(moons: usize) -> f32 {
    if moons == 0 {
        return PLANET_R;
    }
    let mut ring = 0;
    let mut left = moons;
    while left > ring_capacity(ring) {
        left -= ring_capacity(ring);
        ring += 1;
    }
    ring_radius(ring) + MOON_R
}

/// 椭圆上参数角 θ 的点（世界坐标）：中心 (-c,0,0) 加半轴 (a,b)，绕 X 轴倾 tilt。
pub fn orbit_point(spec: &OrbitSpec, theta: f32) -> [f32; 3] {
    let (st, ct) = theta.sin_cos();
    let (sl, cl) = spec.tilt.sin_cos();
    let px = -spec.c + spec.a * ct;
    let pz0 = spec.b * st;
    [px, -pz0 * sl, pz0 * cl]
}

/// 第 g 条轨道的半长轴。共焦椭圆在近点侧最窄，邻轨间距 ≈ (1-e)·Δa，所以按
/// 「相邻两组的卫星壳外半径之和 + 空隙」除以 (1-e) 逐条外推；最内一条还要让近点处
/// 的卫星壳离开恒星。变间距让只有一两颗卫星的组不为大组的壳买单。
fn semi_major(moon_counts: &[usize], g: usize) -> f32 {
    let shell = |i: usize| shell_radius(moon_counts[i]);
    let mut a = (STAR_R + CLEARANCE + shell(0)) / (1.0 - ECC);
    for i in 1..=g {
        a += (shell(i - 1) + shell(i) + CLEARANCE) / (1.0 - ECC);
    }
    a
}

/// 排布星系：第 g 个分组占第 g 条轨道，轨道上只有它一颗行星，`moon_counts[g]` 颗卫星围着它转。
/// 组数为零时输出空布局。
pub fn system_layout(moon_counts: &[usize]) -> SystemLayout {
    let mut orbits = Vec::with_capacity(moon_counts.len());
    let mut planets = Vec::with_capacity(moon_counts.len());
    let mut moons = Vec::new();
    for (g, &count) in moon_counts.iter().enumerate() {
        let a = semi_major(moon_counts, g);
        let b = a * (1.0 - ECC * ECC).sqrt();
        let c = a * ECC;
        let spec = OrbitSpec { a, b, c, tilt: TILT };
        let theta = g as f32 * GOLDEN;
        planets.push(PlanetNode { group: g, theta, pos: orbit_point(&spec, theta) });
        orbits.push(spec);

        // 卫星由内向外填环：一环装满再开下一环；每环内均匀分布，环间按黄金角错开。
        let mut slot = 0;
        let mut ring = 0;
        while slot < count {
            let take = ring_capacity(ring).min(count - slot);
            for i in 0..take {
                moons.push(MoonNode {
                    group: g,
                    slot: slot + i,
                    ring,
                    radius: ring_radius(ring),
                    theta: ring as f32 * GOLDEN + i as f32 * std::f32::consts::TAU / take as f32,
                });
            }
            slot += take;
            ring += 1;
        }
    }
    SystemLayout { orbits, planets, moons }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 恒星（原点）到行星的距离应等于焦点到该参数角椭圆点的解析距离
    /// d(θ) = a(1 - e·cosθ)——即恒星确实在焦点上。
    #[test]
    fn 恒星位于椭圆焦点() {
        let layout = system_layout(&[3, 4, 5]);
        for planet in &layout.planets {
            let spec = layout.orbits[planet.group];
            let d = (planet.pos[0].powi(2) + planet.pos[1].powi(2) + planet.pos[2].powi(2)).sqrt();
            let expected = spec.a * (1.0 - ECC * planet.theta.cos());
            assert!((d - expected).abs() < 2.0, "焦点距离 {d} 偏离解析式 {expected}");
        }
    }

    #[test]
    fn 近点处卫星壳不碰恒星() {
        let counts = [14, 1, 6];
        let layout = system_layout(&counts);
        for (g, spec) in layout.orbits.iter().enumerate() {
            let near = spec.a - spec.c;
            assert!(near - shell_radius(counts[g]) > STAR_R + CLEARANCE - 1.0, "第 {g} 轨近点太近");
        }
    }

    /// 邻轨上任意两点的最小距离要容得下两组卫星壳：沿椭圆密采样，不靠公式猜。
    #[test]
    fn 邻轨的卫星壳互不相碰() {
        let counts = [14, 1, 6, 1, 8];
        let layout = system_layout(&counts);
        let sample = |spec: &OrbitSpec| -> Vec<[f32; 3]> {
            (0..720).map(|i| orbit_point(spec, i as f32 / 720.0 * std::f32::consts::TAU)).collect()
        };
        for g in 0..counts.len() - 1 {
            let (p, q) = (sample(&layout.orbits[g]), sample(&layout.orbits[g + 1]));
            let min = p
                .iter()
                .flat_map(|x| q.iter().map(move |y| ((x[0] - y[0]).powi(2) + (x[2] - y[2]).powi(2)).sqrt()))
                .fold(f32::INFINITY, f32::min);
            let need = shell_radius(counts[g]) + shell_radius(counts[g + 1]);
            assert!(min >= need, "第 {g} 与 {} 轨最近 {min}，装不下两个壳 {need}", g + 1);
        }
    }

    #[test]
    fn 空清单输出空布局() {
        let layout = system_layout(&[]);
        assert!(layout.orbits.is_empty() && layout.planets.is_empty() && layout.moons.is_empty());
    }

    #[test]
    fn 每组一颗行星_卫星数与输入一致且按环填充() {
        let layout = system_layout(&[0, 2, 14]);
        assert_eq!(layout.planets.len(), 3);
        for (g, want) in [0usize, 2, 14].into_iter().enumerate() {
            assert_eq!(layout.moons.iter().filter(|m| m.group == g).count(), want);
        }
        // 14 颗装不下最内环，必须开第二环。
        assert!(layout.moons.iter().any(|m| m.group == 2 && m.ring == 1));
        // 同环相邻卫星弧距不小于 MOON_SLOT（不重叠）。
        for ring in 0..2 {
            let in_ring: Vec<_> = layout.moons.iter().filter(|m| m.group == 2 && m.ring == ring).collect();
            let r = ring_radius(ring);
            let chord = 2.0 * r * (std::f32::consts::PI / in_ring.len() as f32).sin();
            assert!(chord >= MOON_R * 2.0 + 4.0, "环 {ring} 的卫星挤在一起");
        }
    }

    #[test]
    fn 卫星槽位组内连续() {
        let layout = system_layout(&[5]);
        let mut slots: Vec<usize> = layout.moons.iter().map(|m| m.slot).collect();
        slots.sort();
        assert_eq!(slots, [0, 1, 2, 3, 4]);
    }
}
