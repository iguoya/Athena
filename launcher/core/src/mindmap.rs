//! 学习应用面板的放射状思维导图布局（ADR 0083）。
//!
//! 纯函数：输入应用清单，输出每个节点、每个领域分组、同心圈和每条连线的坐标。
//! 界面只负责画，所以布局能脱离窗口做单元测试——「图块互相不重叠」「连线都落在画布里」
//! 这类性质靠测试守住，不靠看截图。
//!
//! 几何：画布中心是虎头；向外一圈放领域分组，再向外一圈（应用多了再加圈）放应用。
//! 每个分组分到一个扇区，扇区大小按组里的应用数加权，应用在自己的扇区里均匀散开。
//! 全自动，不存坐标；位置只由清单决定，所以换机器、新增应用都不用管。

use std::collections::HashSet;

use crate::manifest::App;

/// 一个图块的外框（与 `launcher.slint` 里的 `Tile` 同尺寸）。
pub const TILE_W: f32 = 116.0;
pub const TILE_H: f32 = 124.0;
/// 图标中心在图块里的位置：水平居中，距顶 38px。布局里的「节点坐标」指图标中心。
pub const ICON_CENTER_Y: f32 = 38.0;
/// 连线在图块外框之外收住（含标题和状态点）：收在图标边缘的话，线会从图标下面的标题文字上穿过去。
const TILE_PAD: f32 = 4.0;
/// 图块里「有东西」的范围，相对图标中心：左右取标题的宽度，上到图标顶，下到状态点底。
/// 图块外框（116×124）下面还留着一截空白，线收在那里会悬空。
const CONTENT_HALF_W: f32 = 54.0;
const CONTENT_ABOVE: f32 = 30.0;
const CONTENT_BELOW: f32 = 64.0;
/// 分组胶囊的高度（与 `launcher.slint` 里的 `GroupPill` 同高）；宽度按文字算，见 `pill_width`。
pub const PILL_H: f32 = 32.0;
/// 同一圈上相邻两个胶囊之间至少留的空隙。
const PILL_GAP: f32 = 8.0;
/// 中心虎头的半径。
pub const HUB_R: f32 = 46.0;

// 领域圈与第一圈应用的间距不能小于 ≈152：图块下半截（标题、状态点）悬在图标中心下方 86px，
// 斜上方的图块会压住同一角度上的领域胶囊。算法见测试「图块压住了分组」。
const GROUP_RADIUS: f32 = 105.0;
const FIRST_RING: f32 = 258.0;
// 圈与圈之间也要隔一个图块对角线（见 SLOT）：两圈上斜着相邻的图块，径向距离小于对角线就会重叠。
const RING_STEP: f32 = 172.0;
/// 同一圈上相邻两个图块的中心至少隔这么远。取图块对角线（√(116²+124²) ≈ 170）：
/// 图块是矩形，斜着挨在一起时，中心距小于对角线就可能重叠，光比「比宽度大」不够。
const SLOT: f32 = 171.0;
/// 画布在最外圈之外多留的边：图块下半截（标题、状态点）比图标中心低 86px。
const MARGIN: f32 = 92.0;

/// 领域颜色。按分组的出现顺序取，不按名字：启动器里没有按应用写的分支。
pub const PALETTE: [&str; 8] = [
    "#5468A4", "#0f766e", "#b7791f", "#7c3aed", "#c2570c", "#be185d", "#0369a1", "#4d7c0f",
];
const DEFAULT_GROUP: &str = "其他";

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Point {
    pub x: f32,
    pub y: f32,
}

impl Point {
    fn new(x: f32, y: f32) -> Self {
        Self { x, y }
    }
    fn from_polar(center: Point, radius: f32, angle: f32) -> Self {
        Self::new(center.x + radius * angle.cos(), center.y + radius * angle.sin())
    }
    fn minus(self, other: Point) -> Point {
        Point::new(self.x - other.x, self.y - other.y)
    }
    fn plus(self, other: Point) -> Point {
        Point::new(self.x + other.x, self.y + other.y)
    }
    fn scale(self, k: f32) -> Point {
        Point::new(self.x * k, self.y * k)
    }
    fn length(self) -> f32 {
        self.x.hypot(self.y)
    }
    fn unit(self) -> Point {
        let n = self.length();
        if n < 1e-6 {
            Point::new(0.0, 0.0)
        } else {
            self.scale(1.0 / n)
        }
    }
    /// 从 self 朝 other 走 distance 的位置。
    fn toward(self, other: Point, distance: f32) -> Point {
        self.plus(other.minus(self).unit().scale(distance))
    }
}

/// 从图块中心（图标中心）朝 `toward` 射出的射线，与图块内容范围（外扩 `pad`）的交点。
/// 图块的标题和状态点挂在图标下面，所以范围不止图标那一小块。
fn clip_to_tile(center: Point, toward: Point, pad: f32) -> Point {
    let d = toward.minus(center);
    let half_w = CONTENT_HALF_W + pad;
    let above = CONTENT_ABOVE + pad;
    let below = CONTENT_BELOW + pad;
    let tx = if d.x > 0.0 { half_w / d.x } else if d.x < 0.0 { -half_w / d.x } else { f32::INFINITY };
    let ty = if d.y > 0.0 { below / d.y } else if d.y < 0.0 { -above / d.y } else { f32::INFINITY };
    let t = tx.min(ty);
    if t.is_finite() { center.plus(d.scale(t)) } else { center }
}

#[derive(Debug, Clone, PartialEq)]
pub struct GroupNode {
    pub name: String,
    pub color: &'static str,
    /// 胶囊中心。
    pub at: Point,
    /// 胶囊宽度：按名字的字数算，名字长一点不会被截断，名字短就不浪费地方。
    pub width: f32,
    pub apps: usize,
}

/// 胶囊宽度：汉字按 14px、其余按 8px 估（13px 字号），两边各留 14px。
pub fn pill_width(name: &str) -> f32 {
    let text: f32 = name.chars().map(|c| if c.is_ascii() { 8.0 } else { 14.0 }).sum();
    (text + 28.0).clamp(64.0, 150.0)
}

/// 两个胶囊（中心 a、b，宽 wa、wb）是否重叠，含间隙。
fn pills_overlap(a: Point, wa: f32, b: Point, wb: f32) -> bool {
    (a.x - b.x).abs() < (wa + wb) / 2.0 + PILL_GAP && (a.y - b.y).abs() < PILL_H + PILL_GAP
}

#[derive(Debug, Clone, PartialEq)]
pub struct AppNode {
    pub id: String,
    /// `groups` 的下标。
    pub group: usize,
    /// 图标中心。
    pub at: Point,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LinkKind {
    /// 虎头 → 领域。
    Hub,
    /// 领域 → 应用。
    Branch,
    /// 谁从谁长出来：带箭头。
    Evolves,
    /// 相关：无向，不带箭头。
    Related,
    /// 挂靠：parent → 子应用，有向带箭头（ADR 0092）。
    Attach,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Link {
    pub kind: LinkKind,
    pub color: &'static str,
    pub from: Point,
    pub c1: Point,
    pub c2: Point,
    pub to: Point,
    /// 箭头三角形的三个顶点，尖端在 `to`；只有 `Evolves` 有。
    pub arrow: Option<[Point; 3]>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct MindMap {
    pub width: f32,
    pub height: f32,
    pub center: Point,
    /// 同心圈半径，只用来画「空间感」，没有信息。
    pub rings: Vec<f32>,
    pub groups: Vec<GroupNode>,
    /// 与输入的应用同序。
    pub nodes: Vec<AppNode>,
    pub links: Vec<Link>,
}

/// 把应用清单排成放射状思维导图。
///
/// 带 `parent` 的应用是挂靠节点（ADR 0092）：不占领域扇区，画在挂靠者外一圈，
/// 用有向实线连过去；parent 的 id 解析不到就忽略挂靠，回普通布局（与 related 同规）。
pub fn layout(apps: &[App]) -> MindMap {
    let index_of = |id: &str| apps.iter().position(|app| app.id == id);
    let attached_to: Vec<Option<usize>> = apps
        .iter()
        .map(|app| app.parent.as_deref().and_then(index_of))
        .collect();

    // 1. 分组：按首次出现的顺序，省略 group 的归「其他」。挂靠节点不占扇区，
    // 但领域归属沿用挂靠者的（画布上它们贴着挂靠者）。
    let mut group_names: Vec<String> = Vec::new();
    let mut group_of: Vec<usize> = Vec::with_capacity(apps.len());
    for app in apps {
        let name = app
            .group
            .as_deref()
            .map(str::trim)
            .filter(|name| !name.is_empty())
            .unwrap_or(DEFAULT_GROUP)
            .to_string();
        let index = match group_names.iter().position(|existing| *existing == name) {
            Some(index) => index,
            None => {
                group_names.push(name);
                group_names.len() - 1
            }
        };
        group_of.push(index);
    }
    for (i, target) in attached_to.iter().enumerate() {
        if let Some(p) = target {
            group_of[i] = group_of[*p];
        }
    }
    let group_count = group_names.len();
    let members: Vec<Vec<usize>> = (0..group_count)
        .map(|g| {
            (0..apps.len())
                .filter(|&i| attached_to[i].is_none() && group_of[i] == g)
                .collect()
        })
        .collect();

    // 2. 扇区：按组里的应用数加权，从正上方顺时针排。
    let total: f32 = members.iter().map(|m| m.len().max(1) as f32).sum::<f32>().max(1.0);
    let mut sector_start = -std::f32::consts::FRAC_PI_2;
    let mut sectors: Vec<(f32, f32)> = Vec::with_capacity(group_count); // (起点, 宽度)
    for m in &members {
        let width = std::f32::consts::TAU * (m.len().max(1) as f32) / total;
        sectors.push((sector_start, width));
        sector_start += width;
    }

    // 2.5 领域圈的半径：从 GROUP_RADIUS 起，胶囊两两重叠就整圈往外推 4px，直到互不重叠
    // （相邻的单应用领域各占一个小扇区，中心靠得近，胶囊就会叠在一起）。
    // 第一圈应用必须离领域圈至少 153px，所以跟着外移。
    let widths: Vec<f32> = group_names.iter().map(|name| pill_width(name)).collect();
    let mut group_radius = GROUP_RADIUS;
    let origin = Point::new(0.0, 0.0);
    loop {
        let spots: Vec<Point> = sectors
            .iter()
            .map(|&(start, width)| Point::from_polar(origin, group_radius, start + width / 2.0))
            .collect();
        let crowded = (0..spots.len())
            .any(|i| (i + 1..spots.len()).any(|j| pills_overlap(spots[i], widths[i], spots[j], widths[j])));
        if !crowded || group_radius > 600.0 {
            break;
        }
        group_radius += 4.0;
    }
    let first_ring = FIRST_RING.max(group_radius + 153.0);

    // 3. 先算每个组需要几圈，才知道画布多大（中心坐标取决于画布）。
    let mut ring_of: Vec<usize> = vec![0; apps.len()];
    let mut slot_in_ring: Vec<(usize, usize)> = vec![(0, 0); apps.len()]; // (本圈序号, 本圈个数)
    let mut max_ring = 0usize;
    for (g, m) in members.iter().enumerate() {
        let (_, width) = sectors[g];
        let mut placed = 0;
        let mut ring = 0;
        while placed < m.len() {
            let radius = first_ring + RING_STEP * ring as f32;
            let capacity = capacity(width, radius);
            let take = capacity.min(m.len() - placed);
            for (k, &app_index) in m[placed..placed + take].iter().enumerate() {
                ring_of[app_index] = ring;
                slot_in_ring[app_index] = (k, take);
            }
            placed += take;
            max_ring = max_ring.max(ring);
            ring += 1;
        }
    }
    // 挂靠层的半径在 center 定下来之前就得算——挂靠节点贴在挂靠者外一圈，
    // 画布要为它们多留一整圈。
    let attach_ring_needed = apps
        .iter()
        .any(|app| app.parent.is_some());
    let outer = if apps.is_empty() {
        group_radius
    } else {
        first_ring + RING_STEP * (max_ring as f32 + if attach_ring_needed { 1.0 } else { 0.0 })
    };
    let extent = outer + MARGIN;
    let center = Point::new(extent, extent);

    // 4. 放置分组与应用。
    let groups: Vec<GroupNode> = group_names
        .iter()
        .enumerate()
        .map(|(g, name)| {
            let (start, width) = sectors[g];
            GroupNode {
                name: name.clone(),
                color: PALETTE[g % PALETTE.len()],
                at: Point::from_polar(center, group_radius, start + width / 2.0),
                width: widths[g],
                apps: members[g].len(),
            }
        })
        .collect();
    // 普通节点位置：领域扇区内按圈铺。
    let mut node_at: Vec<Point> = vec![Point::new(0.0, 0.0); apps.len()];
    for (i, _) in apps.iter().enumerate() {
        if attached_to[i].is_some() {
            continue;
        }
        let g = group_of[i];
        let (start, width) = sectors[g];
        let (k, count) = slot_in_ring[i];
        let angle = start + (k as f32 + 0.5) * width / count as f32;
        let radius = first_ring + RING_STEP * ring_of[i] as f32;
        node_at[i] = Point::from_polar(center, radius, angle);
    }

    // 挂靠节点位置：挂靠者外一圈，在挂靠者的角度两侧均分。相邻子节点的角距按
    // 同圈弦长 ≥ SLOT 反解，图块不会叠在一起。
    let mut attach_at: Vec<Option<Point>> = vec![None; apps.len()];
    let mut attach_radii: Vec<f32> = Vec::new();
    let mut children_of: Vec<Vec<usize>> = vec![Vec::new(); apps.len()];
    for (i, target) in attached_to.iter().enumerate() {
        if let Some(p) = target {
            children_of[*p].push(i);
        }
    }
    for (p, children) in children_of.iter().enumerate() {
        if children.is_empty() || attached_to[p].is_some() {
            continue; // 空挂靠者跳过；链式挂靠（挂靠者自己也被挂）当前数据没有。
        }
        let radius = first_ring + RING_STEP * (ring_of[p] as f32 + 1.0);
        let (start, width) = sectors[group_of[p]];
        let (k, count) = slot_in_ring[p];
        let parent_angle = start + (k as f32 + 0.5) * width / count as f32;
        let spread = (SLOT / radius).asin().max(0.12);
        let span = spread * (children.len() as f32 - 1.0);
        for (k, &child) in children.iter().enumerate() {
            attach_at[child] = Some(Point::from_polar(center, radius, parent_angle - span / 2.0 + spread * k as f32));
        }
        attach_radii.push(radius);
    }

    let nodes: Vec<AppNode> = apps
        .iter()
        .enumerate()
        .map(|(i, app)| AppNode {
            id: app.id.clone(),
            group: group_of[i],
            at: match attach_at[i] {
                Some(at) => at,
                None => node_at[i],
            },
        })
        .collect();

    let mut rings = vec![group_radius];
    if !apps.is_empty() {
        rings.extend((0..=max_ring).map(|r| first_ring + RING_STEP * r as f32));
        let mut extra: Vec<f32> = attach_radii
            .iter()
            .filter(|r| **r > outer)
            .copied()
            .collect();
        extra.sort_by(|a, b| a.partial_cmp(b).unwrap());
        extra.dedup();
        rings.extend(extra);
    }

    // 5. 连线。
    let mut links: Vec<Link> = Vec::new();
    for group in &groups {
        links.push(straight(
            LinkKind::Hub,
            group.color,
            center.toward(group.at, HUB_R),
            group.at.toward(center, PILL_H / 2.0 + 4.0),
        ));
    }
    for node in &nodes {
        let group = &groups[node.group];
        links.push(straight(
            LinkKind::Branch,
            group.color,
            group.at.toward(node.at, PILL_H / 2.0 + 4.0),
            clip_to_tile(node.at, group.at, TILE_PAD),
        ));
    }
    for (i, _) in apps.iter().enumerate() {
        if let (Some(p), Some(at)) = (&attached_to[i], attach_at[i]) {
            links.push(curved(
                LinkKind::Attach,
                groups[group_of[i]].color,
                node_at[*p],
                at,
                center,
                0.14,
                true,
            ));
        }
    }
    let mut drawn: HashSet<(usize, usize)> = HashSet::new();
    for (to, app) in apps.iter().enumerate() {
        if let Some(from) = app.evolves_from.as_deref().and_then(index_of) {
            if from != to {
                drawn.insert((from.min(to), from.max(to)));
                links.push(curved(LinkKind::Evolves, "#6b7280", nodes[from].at, nodes[to].at, center, 0.22, true));
            }
        }
    }
    for (a, app) in apps.iter().enumerate() {
        for related in &app.related {
            let Some(b) = index_of(related) else { continue };
            if a == b || !drawn.insert((a.min(b), a.max(b))) {
                continue;
            }
            links.push(curved(LinkKind::Related, "#b6bcc6", nodes[a].at, nodes[b].at, center, 0.18, false));
        }
    }

    MindMap { width: extent * 2.0, height: extent * 2.0, center, rings, groups, nodes, links }
}

/// 一个扇区（宽度 width，弧度）在半径 radius 的圈上最多放几个图块。
/// n 个图块把扇区等分成 n 份、各占中间，相邻两个中心的弦长是 2·R·sin(w/2n)，要不小于 SLOT。
fn capacity(width: f32, radius: f32) -> usize {
    let mut n = 1usize;
    while n < 64 {
        let next = n + 1;
        if 2.0 * radius * (width / (2.0 * next as f32)).sin() >= SLOT {
            n = next;
        } else {
            break;
        }
    }
    n
}

fn straight(kind: LinkKind, color: &'static str, from: Point, to: Point) -> Link {
    Link {
        kind,
        color,
        from,
        c1: from.plus(to.minus(from).scale(1.0 / 3.0)),
        c2: from.plus(to.minus(from).scale(2.0 / 3.0)),
        to,
        arrow: None,
    }
}

/// 两个应用之间的弧线：弯向远离中心的一侧，免得穿过虎头和内圈的分组。
fn curved(kind: LinkKind, color: &'static str, a: Point, b: Point, center: Point, bulge: f32, arrow: bool) -> Link {
    let from = clip_to_tile(a, b, TILE_PAD);
    let to = clip_to_tile(b, a, TILE_PAD + if arrow { 4.0 } else { 0.0 });
    let mid = from.plus(to).scale(0.5);
    let chord = to.minus(from);
    let mut outward = mid.minus(center).unit();
    if outward.length() < 1e-3 {
        // 两端正好隔着中心：任选弦的一侧法线。
        outward = Point::new(-chord.y, chord.x).unit();
    }
    let control = mid.plus(outward.scale(chord.length() * bulge * 2.0));
    let c1 = from.plus(control.minus(from).scale(2.0 / 3.0));
    let c2 = to.plus(control.minus(to).scale(2.0 / 3.0));
    let arrow = arrow.then(|| {
        let direction = to.minus(c2).unit();
        let normal = Point::new(-direction.y, direction.x);
        let tip = to.plus(direction.scale(6.0));
        let base = to.minus(direction.scale(8.0));
        [tip, base.plus(normal.scale(6.0)), base.minus(normal.scale(6.0))]
    });
    Link { kind, color, from, c1, c2, to, arrow }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::manifest::{discover, DevSpec};
    use std::path::PathBuf;

    fn app(id: &str, group: Option<&str>, evolves: Option<&str>, related: &[&str]) -> App {
        App {
            id: id.to_string(),
            title: id.to_string(),
            summary: String::new(),
            symbol: "book".to_string(),
            letter: "A".to_string(),
            accent: "#5A6270".to_string(),
            icon_file: None,
            icon_renders: Vec::new(),
            dir: PathBuf::new(),
            dev: DevSpec::default(),
            evolves_from: evolves.map(str::to_string),
            group: group.map(str::to_string),
            related: related.iter().map(|s| s.to_string()).collect(),
            parent: None,
            hidden: false,
        }
    }

    /// 图块的外框（左、上、右、下）。
    fn tile_box(node: &AppNode) -> (f32, f32, f32, f32) {
        (node.at.x - TILE_W / 2.0, node.at.y - ICON_CENTER_Y, node.at.x + TILE_W / 2.0, node.at.y - ICON_CENTER_Y + TILE_H)
    }
    fn pill_box(group: &GroupNode) -> (f32, f32, f32, f32) {
        (group.at.x - group.width / 2.0, group.at.y - PILL_H / 2.0, group.at.x + group.width / 2.0, group.at.y + PILL_H / 2.0)
    }
    fn overlap(a: (f32, f32, f32, f32), b: (f32, f32, f32, f32)) -> bool {
        a.0 < b.2 && b.0 < a.2 && a.1 < b.3 && b.1 < a.3
    }

    fn assert_clean(map: &MindMap) {
        let tiles: Vec<_> = map.nodes.iter().map(tile_box).collect();
        for (i, a) in tiles.iter().enumerate() {
            assert!(a.0 >= 0.0 && a.1 >= 0.0 && a.2 <= map.width && a.3 <= map.height, "图块 {i} 出了画布");
            for (j, b) in tiles.iter().enumerate().skip(i + 1) {
                assert!(!overlap(*a, *b), "图块 {i} 与 {j} 重叠");
            }
            for (g, group) in map.groups.iter().enumerate() {
                assert!(!overlap(*a, pill_box(group)), "图块 {i} 压住了分组 {g}");
            }
        }
        for (i, group) in map.groups.iter().enumerate() {
            let p = pill_box(group);
            assert!(p.0 >= 0.0 && p.1 >= 0.0 && p.2 <= map.width && p.3 <= map.height);
            for (j, other) in map.groups.iter().enumerate().skip(i + 1) {
                assert!(!overlap(p, pill_box(other)), "分组 {i}（{}）与 {j}（{}）的胶囊重叠", group.name, other.name);
            }
        }
        for link in &map.links {
            for end in [link.from, link.to] {
                for (i, node) in map.nodes.iter().enumerate() {
                    let inside = (end.x - node.at.x).abs() < CONTENT_HALF_W
                        && end.y > node.at.y - CONTENT_ABOVE
                        && end.y < node.at.y + CONTENT_BELOW;
                    assert!(!inside, "连线端点钻进了图块 {i} 的内容范围（会压住标题）");
                }
            }
            for point in [link.from, link.c1, link.c2, link.to] {
                assert!(point.x.is_finite() && point.y.is_finite());
                assert!(point.x >= 0.0 && point.y >= 0.0 && point.x <= map.width && point.y <= map.height, "连线出了画布");
            }
        }
    }

    #[test]
    fn 每个应用一个节点且与输入同序() {
        let apps = vec![app("a", Some("甲"), None, &[]), app("b", Some("乙"), None, &[]), app("c", Some("甲"), None, &[])];
        let map = layout(&apps);
        assert_eq!(map.nodes.iter().map(|n| n.id.as_str()).collect::<Vec<_>>(), ["a", "b", "c"]);
        assert_clean(&map);
    }

    #[test]
    fn 分组按首次出现排_没写_group_的归其他() {
        let apps = vec![app("a", Some("乙"), None, &[]), app("b", None, None, &[]), app("c", Some("乙"), None, &[]), app("d", Some("  "), None, &[])];
        let map = layout(&apps);
        assert_eq!(map.groups.iter().map(|g| g.name.as_str()).collect::<Vec<_>>(), ["乙", "其他"]);
        assert_eq!(map.groups.iter().map(|g| g.apps).collect::<Vec<_>>(), [2, 2]);
        assert_eq!(map.nodes.iter().map(|n| n.group).collect::<Vec<_>>(), [0, 1, 0, 1]);
    }

    #[test]
    fn 演进线带箭头_相关线不带且无向去重() {
        let apps = vec![
            app("c", Some("语言"), None, &[]),
            app("cpp", Some("语言"), Some("c"), &["c", "dsa"]), // 与 c 已有演进线，不再画相关线
            app("dsa", Some("数理"), None, &["cpp", "ghost", "dsa"]), // 对 cpp 的相关只算一条；ghost 与自指忽略
        ];
        let map = layout(&apps);
        let kinds = |k: LinkKind| map.links.iter().filter(|l| l.kind == k).count();
        assert_eq!(kinds(LinkKind::Evolves), 1);
        assert_eq!(kinds(LinkKind::Related), 1);
        assert_eq!(kinds(LinkKind::Hub), 2);
        assert_eq!(kinds(LinkKind::Branch), 3);
        let evolves = map.links.iter().find(|l| l.kind == LinkKind::Evolves).unwrap();
        assert!(evolves.arrow.is_some());
        assert!(map.links.iter().filter(|l| l.kind != LinkKind::Evolves).all(|l| l.arrow.is_none()));
        assert_clean(&map);
    }

    #[test]
    fn 一个组应用很多时加外圈而不重叠() {
        let apps: Vec<App> = (0..14).map(|i| app(&format!("a{i}"), Some("大组"), None, &[])).collect();
        let map = layout(&apps);
        assert!(map.rings.len() > 2, "应用多了应该有外圈");
        assert_clean(&map);
        // 另加几个小组，扇区比例变化后仍然不重叠
        let mut more = apps;
        more.extend((0..3).map(|i| app(&format!("b{i}"), Some("小组"), None, &[])));
        more.push(app("solo", Some("独行"), None, &[]));
        assert_clean(&layout(&more));
    }

    #[test]
    fn 很多单应用的领域挨在一起时胶囊不重叠() {
        // 每个领域一个应用：扇区都是最小的，胶囊最容易叠在一起；名字长短不一
        let names = ["编程语言", "英语", "数理基础与方法", "图谱", "考试", "算法", "Tools", "其它领域"];
        let apps: Vec<App> = names.iter().enumerate().map(|(i, n)| app(&format!("a{i}"), Some(n), None, &[])).collect();
        assert_clean(&layout(&apps));
        // 再多几个
        let many: Vec<App> = (0..12).map(|i| app(&format!("m{i}"), Some(&format!("领域{i}")), None, &[])).collect();
        assert_clean(&layout(&many));
    }

    #[test]
    fn 空清单和单个应用也能排() {
        let empty = layout(&[]);
        assert!(empty.nodes.is_empty() && empty.groups.is_empty() && empty.links.is_empty());
        assert!(empty.width > 0.0);
        let one = layout(&[app("only", None, None, &[])]);
        assert_eq!(one.nodes.len(), 1);
        assert_clean(&one);
    }

    #[test]
    fn 挂靠节点画在挂靠者外一圈且带有向线() {
        let mut softcert = app("softcert", Some("软考"), None, &[]);
        let mut dsa = app("dsa", Some("算法"), None, &[]);
        dsa.parent = Some("softcert".to_string());
        let mut ghost = app("ghost", Some("算法"), None, &[]);
        ghost.parent = Some("不存在的应用".to_string()); // 解析不到：回普通布局
        let map = layout(&[softcert.clone(), dsa, ghost]);
        let at = |id: &str| map.nodes.iter().find(|n| n.id == id).unwrap().at;
        let (p, c) = (at("softcert"), at("dsa"));
        // 挂靠节点在挂靠者外一圈：径向距离正好是 RING_STEP。
        assert!((p.minus(c).length() - RING_STEP).abs() < 1.0, "挂靠者到挂靠节点的径向距离应为 RING_STEP");
        assert!(map.links.iter().any(|l| l.kind == LinkKind::Attach && l.arrow.is_some()));
        // ghost 的 parent 解析不到：作为普通节点进了领域圈。
        assert!(map.groups.iter().any(|g| g.name == "算法"));
        assert_clean(&map);
        let _ = softcert;
    }

    #[test]
    fn 布局是确定的() {
        let apps = vec![app("a", Some("甲"), None, &["b"]), app("b", Some("乙"), Some("a"), &[])];
        assert_eq!(layout(&apps), layout(&apps));
    }

    /// 拿仓库里真实的应用清单排一遍：新增应用或改 group 之后，这里先报错，不用等看截图。
    #[test]
    fn 仓库里的真实清单排得干净() {
        let repo = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..").join("..");
        let apps = discover(&repo);
        if apps.is_empty() {
            return; // 不在完整仓库里（例如单独打包的 crate）
        }
        let map = layout(&apps);
        assert_eq!(map.nodes.len(), apps.len());
        assert_clean(&map);
    }
}
