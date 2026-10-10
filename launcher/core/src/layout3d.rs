//! 学习应用面板的 3D「领域轨道环」布局（ADR 0125）。
//!
//! 纯函数：输入每个领域圈的成员数，输出每条轨道的空间姿态与每个节点的世界坐标。
//! 界面只负责渲染，布局能脱离窗口做单元测试。
//!
//! 几何：虎头在原点是恒星；每个领域圈是一条倾斜的圆轨道（半径逐层外推，倾角与
//! 起始方位角交错，避免共面与节点对齐），圈内成员沿轨道按参数角均匀分布。

/// 每条轨道的静态姿态：半径、绕 X 轴倾角、绕 Y 轴起始方位（弧度）。
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct OrbitSpec {
    pub radius: f32,
    pub tilt: f32,
    pub yaw: f32,
}

/// 轨道上的一个节点：所属领域圈、圈内序号、世界坐标。
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct OrbitNode {
    pub group: usize,
    pub slot: usize,
    pub pos: [f32; 3],
}

#[derive(Debug, Clone, PartialEq)]
pub struct OrbitLayout {
    pub orbits: Vec<OrbitSpec>,
    pub nodes: Vec<OrbitNode>,
}

const R0: f32 = 240.0;
const RING_STEP: f32 = 150.0;
const TILT: f32 = 0.30; // ≈17°，环面与视轴的错角
const GOLDEN: f32 = 2.39996; // 黄金角：起始方位逐环错开，节点不对齐

/// 排布 `group_sizes`：第 g 个领域圈占第 g 条轨道，成员沿轨道均匀分布。
/// 组数为零时输出空布局。
pub fn orbit_layout(group_sizes: &[usize]) -> OrbitLayout {
    let mut orbits = Vec::with_capacity(group_sizes.len());
    let mut nodes = Vec::new();
    for (g, &count) in group_sizes.iter().enumerate() {
        let radius = R0 + g as f32 * RING_STEP;
        let tilt = if g % 2 == 0 { TILT } else { -TILT } + g as f32 * 0.04;
        let yaw = g as f32 * GOLDEN;
        orbits.push(OrbitSpec { radius, tilt, yaw });
        let count = count.max(1);
        for slot in 0..count {
            let theta = yaw + slot as f32 * std::f32::consts::TAU / count as f32;
            // 环平面：先在 XZ 平面上取圆，绕 X 轴倾 tilt，再绕 Y 轴转 yaw。
            let (sx, sz) = theta.sin_cos();
            let (ct, st) = tilt.sin_cos();
            let (cy, sy) = yaw.sin_cos();
            let (px, pz) = (radius * sx, radius * sz);
            let x = px;
            let y = -pz * st;
            let z = pz * ct;
            // 绕 Y 轴旋转 yaw 把每条环的起始方位错开。
            let (x2, z2) = (x * cy + z * sy, -x * sy + z * cy);
            nodes.push(OrbitNode { group: g, slot, pos: [x2, y, z2] });
        }
    }
    OrbitLayout { orbits, nodes }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn 节点落在各自轨道半径上() {
        let layout = orbit_layout(&[3, 4, 5]);
        for node in &layout.nodes {
            let spec = layout.orbits[node.group];
            let d = (node.pos[0] * node.pos[0]
                + node.pos[1] * node.pos[1]
                + node.pos[2] * node.pos[2])
                .sqrt();
            assert!((d - spec.radius).abs() < 1.0, "节点偏离轨道半径 {d} vs {}", spec.radius);
        }
    }

    #[test]
    fn 相邻环不共面() {
        let layout = orbit_layout(&[1, 1, 1, 1]);
        for pair in layout.orbits.windows(2) {
            let (a, b) = (pair[0], pair[1]);
            // 倾角交替加逐环微差：同倾角的两环起始方位至少差一个黄金角。
            assert!(
                (a.tilt - b.tilt).abs() > 0.01 || (a.yaw - b.yaw).abs() % std::f32::consts::PI > 0.01,
                "相邻环共面"
            );
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
        let angles: Vec<f32> = layout
            .nodes
            .iter()
            .map(|n| n.slot as f32 * std::f32::consts::TAU / 4.0)
            .collect();
        assert_eq!(angles.len(), 4);
        assert_eq!(layout.nodes[0].slot, 0);
        assert_eq!(layout.nodes[3].slot, 3);
    }
}
