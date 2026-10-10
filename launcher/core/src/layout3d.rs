//! 学习应用面板的 3D「领域轨道环」布局（ADR 0125）。
//!
//! 纯函数：输入每个领域圈的成员数，输出每条轨道的空间姿态与每个节点的世界坐标。
//! 界面只负责渲染，布局能脱离窗口做单元测试。
//!
//! 几何（开普勒式）：虎头是恒星，位于每个椭圆轨道的**公共焦点**上；所有椭圆
//! 长轴同向（沿世界 X，宽屏横向），半长轴逐环外推，倾角交替微差避免共面。
//! 行星沿参数角均匀布点。

/// 每条椭圆轨道的姿态：半长轴、半短轴、焦点距（中心到恒星的偏移）、绕 X 倾角。
/// 椭圆中心在 (-c, 0, 0)，恒星（原点）即长轴上的近侧焦点。
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct OrbitSpec {
    pub a: f32,
    pub b: f32,
    pub c: f32,
    pub tilt: f32,
}

/// 轨道上的一个节点：所属领域圈、圈内序号、世界坐标与轨道参数角。
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct OrbitNode {
    pub group: usize,
    pub slot: usize,
    pub pos: [f32; 3],
    /// 椭圆参数角（含环起始错位）：公转动画沿它加时间项，与静态坐标同一套
    /// 正变换，t=0 时与布局完全重合。
    pub theta: f32,
}

#[derive(Debug, Clone, PartialEq)]
pub struct OrbitLayout {
    pub orbits: Vec<OrbitSpec>,
    pub nodes: Vec<OrbitNode>,
}

const A0: f32 = 300.0;
const A_STEP: f32 = 170.0;
const ECC: f32 = 0.3; // 离心率：椭圆感明显又不至于近点撞恒星
const TILT: f32 = 0.087; // ≈5°，贴近真实太阳系的近共面（各环再按序微差）
const GOLDEN: f32 = 2.39996; // 黄金角：各环的行星起始角错开，不对齐

/// 椭圆上参数角 θ 的点（世界坐标）：中心 (-c,0,0) 加半轴 (a,b)，绕 X 轴倾 tilt。
pub fn orbit_point(spec: &OrbitSpec, theta: f32) -> [f32; 3] {
    let (st, ct) = theta.sin_cos();
    let (sl, cl) = spec.tilt.sin_cos();
    let px = -spec.c + spec.a * ct;
    let pz0 = spec.b * st;
    [px, -pz0 * sl, pz0 * cl]
}

/// 排布 `group_sizes`：第 g 个领域圈占第 g 条轨道，成员沿参数角均匀分布。
/// 组数为零时输出空布局。
pub fn orbit_layout(group_sizes: &[usize]) -> OrbitLayout {
    let mut orbits = Vec::with_capacity(group_sizes.len());
    let mut nodes = Vec::new();
    for (g, &count) in group_sizes.iter().enumerate() {
        let a = A0 + g as f32 * A_STEP;
        let b = a * (1.0 - ECC * ECC).sqrt();
        let c = a * ECC;
        let tilt = if g % 2 == 0 { TILT } else { -TILT } + g as f32 * 0.012;
        let spec = OrbitSpec { a, b, c, tilt };
        let count = count.max(1);
        let start = g as f32 * GOLDEN;
        for slot in 0..count {
            let theta = start + slot as f32 * std::f32::consts::TAU / count as f32;
            let pos = orbit_point(&spec, theta);
            nodes.push(OrbitNode { group: g, slot, pos, theta });
        }
        orbits.push(spec);
    }
    OrbitLayout { orbits, nodes }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 恒星（原点）到节点的距离应等于焦点到该参数角椭圆点的解析距离
    /// d(θ) = a(1 - e·cosθ)（参数角形式；真近点角的开普勒式与之等价）——
    /// 即恒星确实在焦点上。
    #[test]
    fn 恒星位于椭圆焦点() {
        let layout = orbit_layout(&[3, 4, 5]);
        for node in &layout.nodes {
            let spec = layout.orbits[node.group];
            let d = (node.pos[0] * node.pos[0]
                + node.pos[1] * node.pos[1]
                + node.pos[2] * node.pos[2])
                .sqrt();
            let expected = spec.a * (1.0 - ECC * node.theta.cos());
            assert!(
                (d - expected).abs() < 2.0,
                "焦点距离 {d} 偏离解析式 {expected}"
            );
        }
    }

    #[test]
    fn 椭圆中心随半长轴外推且近点不撞恒星() {
        let layout = orbit_layout(&[1, 1]);
        for spec in &layout.orbits {
            // 中心 (-c,0,0)：近焦点 = a - c = a(1-e)。
            assert!((spec.c - spec.a * ECC).abs() < 1.0);
            assert!(spec.a - spec.c > 150.0, "近点不能撞恒星");
        }
    }

    #[test]
    fn 空清单输出空布局() {
        let layout = orbit_layout(&[]);
        assert!(layout.orbits.is_empty() && layout.nodes.is_empty());
    }

    #[test]
    fn 同组成员按序均匀分布() {
        let layout = orbit_layout(&[4]);
        assert_eq!(layout.nodes.len(), 4);
        assert_eq!(layout.nodes[0].slot, 0);
        assert_eq!(layout.nodes[3].slot, 3);
    }
}
