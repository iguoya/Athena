//! 学习应用面板的放射状思维导图布局（ADR 0083；椭圆分层几何见 launcher ADR 0002）。
//!
//! 纯函数：输入应用清单，输出每个节点、每个领域分组、同心椭圆和每条连线的坐标。
//! 界面只负责画，所以布局能脱离窗口做单元测试——「图块互相不重叠」「连线都落在画布里」
//! 这类性质靠测试守住，不靠看截图。
//!
//! 几何：画布中心是虎头；向外一层放领域分组，再向外放应用。同心圈是**椭圆**而不是
//! 正圆——屏幕大多是横向长方形的，正圆画布越滚越大，四角和左右全在滚动区外浪费；
//! 长轴沿横向的椭圆把内容铺进屏幕真正看得到的地方。每层应用沿椭圆弧按弧长均匀排开。
//! 分层按「径向深度需求」贪心：挂靠者的子节点要在成员层外再占一层，子节点多的组
//! 放最内层，整体的径向深度才最小，画布才最紧。
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

/// 椭圆长短轴之比。16:10 是主流屏幕的横向形态，正圆（1:1）对宽屏最不友好。
const ASPECT: f32 = 1.6;
/// 领域胶囊层的起始短半轴：胶囊外推的起点，装不下会沿椭圆向外长。
const PILL_B: f32 = 132.0;
// 应用层与胶囊层、层与层之间的间距要隔一个图块对角线（见 SLOT）：两层上斜着相邻的
// 图块，层距小于对角线就会重叠。
const LAYER_GAP: f32 = 172.0;
/// 内层短半轴的下限：图块下半截（标题、状态点）悬在图标中心下方 86px，斜上方的图块
/// 会压住同一角度上的领域胶囊，所以应用内层与胶囊层至少隔 ≈152px。
const INNER_B_MIN: f32 = 258.0;
/// 同一层上相邻两个图块的中心至少隔这么远。取图块对角线（√(116²+124²) ≈ 170）：
/// 图块是矩形，斜着挨在一起时，中心距小于对角线就可能重叠，光比「比宽度大」不够。
const SLOT: f32 = 171.0;
/// 画布在内容包围盒之外多留的边。
const MARGIN: f32 = 10.0;
/// 分层装填时每层只承诺 97% 的周长：切扇区、弧长均匀化都有数值余量，压满边界上
/// 浮点误差会挤掉一块的间隙。
const LAYER_BUDGET: f32 = 0.97;

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

/// 中心在原点的椭圆：一层应用的轨道。`a` 是长半轴（横向）、`b` 是短半轴（纵向）。
#[derive(Debug, Clone, Copy, PartialEq)]
struct Ellipse {
    a: f32,
    b: f32,
}

impl Ellipse {
    fn new(b: f32) -> Self {
        Self { a: b * ASPECT, b }
    }
    /// 向外长一层（层距沿两个轴各长 `LAYER_GAP`，保证斜着相邻的两层图块错不开对角线）。
    fn next_layer(&self) -> Self {
        Self { a: self.a + LAYER_GAP, b: self.b + LAYER_GAP }
    }
    fn at(&self, t: f32) -> Point {
        Point::new(self.a * t.cos(), self.b * t.sin())
    }
    /// 周长，Ramanujan 近似：与精确椭圆周长差不到万分之一，对布局绰绰有余。
    fn perimeter(&self) -> f32 {
        let (a, b) = (self.a, self.b);
        std::f32::consts::PI * (3.0 * (a + b) - ((3.0 * a + b) * (a + 3.0 * b)).sqrt())
    }
    /// 参数角从 `t0` 走到 `t1`（必须递增）扫过的弧长。数值弦长和：步进足够密时
    /// 与真弧长差远小于 1px。
    fn arc_len(&self, t0: f32, t1: f32) -> f32 {
        let n = 96;
        let mut sum = 0.0;
        let mut prev = self.at(t0);
        for i in 1..=n {
            let p = self.at(t0 + (t1 - t0) * i as f32 / n as f32);
            sum += p.minus(prev).length();
            prev = p;
        }
        sum
    }
    /// 从参数角 `t0` 出发沿参数递增方向走 `dist` 弧长，返回到达的参数角。
    fn walk(&self, t0: f32, dist: f32) -> f32 {
        let step = 0.008; // ≈0.46°；最内层一步的弦长 1–3px，弧长误差可忽略
        let mut t = t0;
        let mut left = dist;
        while left > 0.0 {
            let chord = self.at(t + step).minus(self.at(t)).length();
            if chord >= left {
                return t + step * (left / chord);
            }
            left -= chord;
            t += step;
        }
        t
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
    /// 所在的应用层：0 是最内层，挂靠节点与引用节点比挂靠者/被引用圈深一层。
    pub layer: usize,
    /// 引用节点（ADR 0116）：`also_under` 给同一个应用生成的又一个图块，
    /// 点开是同一个应用；排在全部本体节点之后。
    pub reference: bool,
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
    /// 引用挂靠：also_under 的挂靠者 → 引用节点，有向带箭头，比挂靠线淡（ADR 0116）。
    Reference,
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
    /// 同心椭圆（长半轴、短半轴，相对 center），只用来画「空间感」，没有信息。
    pub rings: Vec<(f32, f32)>,
    pub groups: Vec<GroupNode>,
    /// 前 `apps.len()` 个是本体节点，与输入的应用同序；其后是引用节点（ADR 0116）。
    pub nodes: Vec<AppNode>,
    pub links: Vec<Link>,
}

/// 把应用清单排成放射状思维导图。
///
/// 带 `parent` 的应用是挂靠节点（ADR 0092）：不占领域扇区，画在挂靠者外一圈，
/// 用有向实线连过去；parent 的 id 解析不到就忽略挂靠，回普通布局（与 related 同规）。
/// `also_under` 列出的挂靠者底下再各放一个引用节点（ADR 0116），与挂靠节点同圈排布；
/// `also_in` 列出的领域圈里再各放一个引用节点（ADR 0117），与圈内成员同圈排布。
pub fn layout(apps: &[App]) -> MindMap {
    let index_of = |id: &str| apps.iter().position(|app| app.id == id);
    let raw_targets: Vec<Option<usize>> = apps
        .iter()
        .map(|app| app.parent.as_deref().and_then(index_of))
        .collect();
    // 挂靠深度为一层（ADR 0095）：挂靠者自己也被挂时，解析回退普通布局，
    // 链式挂靠不再往下铺。
    let attached_to: Vec<Option<usize>> = raw_targets
        .iter()
        .enumerate()
        .map(|(i, target)| match target {
            Some(p) if raw_targets[*p].is_none() => Some(*p),
            _ => None,
        })
        .collect();

    // 引用挂靠（ADR 0116）：每条有效的 also_under 生成一个引用节点，节点下标排在本体之后。
    // 解析不到、指向自己、与主挂靠重复、目标自己也是挂靠节点（深度一层）的都忽略。
    let mut references: Vec<(usize, usize)> = Vec::new(); // (应用, 挂靠者)
    for (i, app) in apps.iter().enumerate() {
        for target in &app.also_under {
            let Some(t) = index_of(target) else { continue };
            if t == i || attached_to[i] == Some(t) || raw_targets[t].is_some() || references.contains(&(i, t)) {
                continue;
            }
            references.push((i, t));
        }
    }

    // 1. 分组：按首次出现的顺序，省略 group 的归「其他」。领域胶囊只由普通成员
    // 登记——挂靠节点不占扇区，画布上贴着挂靠者外一圈，领域归属沿用挂靠者；
    // 它自带的 group 若也照登记（数据库、算法这些子课程组全是挂靠者），内环会
    // 留下一批没有任何节点连出来的空胶囊。
    let mut group_names: Vec<String> = Vec::new();
    let mut group_of: Vec<usize> = vec![0; apps.len()];
    for (i, app) in apps.iter().enumerate() {
        if attached_to[i].is_some() {
            continue;
        }
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
        group_of[i] = index;
    }
    for (i, target) in attached_to.iter().enumerate() {
        if let Some(p) = target {
            group_of[i] = group_of[*p];
        }
    }
    let group_count = group_names.len();
    let mut members: Vec<Vec<usize>> = (0..group_count)
        .map(|g| {
            (0..apps.len())
                .filter(|&i| attached_to[i].is_none() && group_of[i] == g)
                .collect()
        })
        .collect();

    // 领域圈引用（ADR 0117）：also_in 的每个有效领域多一个引用节点，当作圈内成员排在本组
    // 末尾，节点下标排在挂靠引用之后。领域名不存在、与本体所在领域相同的忽略。
    // 下文 members、ring_of、slot_in_ring、node_at 存的都是节点下标，不只是应用下标。
    let group_ref_base = apps.len() + references.len();
    let mut group_refs: Vec<(usize, usize)> = Vec::new(); // (应用, 领域)
    for (i, app) in apps.iter().enumerate() {
        for name in &app.also_in {
            let Some(g) = group_names.iter().position(|existing| existing == name.trim()) else { continue };
            if g == group_of[i] || group_refs.contains(&(i, g)) {
                continue;
            }
            members[g].push(group_ref_base + group_refs.len());
            group_refs.push((i, g));
        }
    }
    let node_count = group_ref_base + group_refs.len();

    // 2. 分层装填：每层是一条同心椭圆轨道，容量是它的周长（打 97% 折扣留数值余量）。
    //    一层的轨道被两种块共享——本层成员组的图块，和内一层挂靠者的子节点——所以
    //    组的「份额」取大者：自己的成员排开要的弧长，与（若有挂靠子节点）子节点排开
    //    要的弧长按内外两层周长比折算回来的量。装填顺序：有子节点的组先占内层——
    //    挂靠层要在成员层外再占一层，径向深度最大的组放最里面，整体层数才最少；
    //    同为无子（或有子）的组按弧长需求降序。稳定排序保持同需求的组按首次出现序，
    //    布局由清单顺序唯一决定。
    let mut children_count: Vec<usize> = vec![0; apps.len()];
    for target in attached_to.iter().flatten() {
        children_count[*target] += 1;
    }
    for &(_, t) in &references {
        children_count[t] += 1;
    }
    // 引用节点（下标 ≥ apps.len()）没有子节点。
    let kids_of = |g: usize| -> usize {
        members[g].iter().map(|&i| children_count.get(i).copied().unwrap_or(0)).sum()
    };
    let mut layers: Vec<Ellipse> = vec![Ellipse::new((PILL_B + 153.0).max(INNER_B_MIN))];
    let mut layer_load: Vec<f32> = vec![0.0];
    let mut ring_layer: Vec<usize> = vec![0; group_count];
    let mut order: Vec<usize> = (0..group_count).collect();
    order.sort_by(|&x, &y| {
        let share = |g: usize| -> f32 {
            let member = members[g].len().max(1) as f32 * SLOT;
            let kids = kids_of(g);
            if kids == 0 {
                return member;
            }
            // 子节点层比成员层周长大，折算回本层；扇区要同时容得下两层。
            let layer = layers[0];
            let ratio = layer.perimeter() / layer.next_layer().perimeter();
            member.max(kids as f32 * SLOT * ratio)
        };
        (kids_of(y) > 0).cmp(&(kids_of(x) > 0)).then_with(|| share(y).total_cmp(&share(x)))
    });
    for &g in &order {
        let kids = kids_of(g);
        let mut k = 0;
        loop {
            while k >= layers.len() {
                layers.push(layers[layers.len() - 1].next_layer());
                layer_load.push(0.0);
            }
            let member = members[g].len().max(1) as f32 * SLOT * 1.001;
            let need = if kids == 0 {
                member
            } else {
                let ratio = layers[k].perimeter() / layers[k].next_layer().perimeter();
                member.max(kids as f32 * SLOT * ratio)
            };
            if layer_load[k] + need <= layers[k].perimeter() * LAYER_BUDGET {
                layer_load[k] += need;
                ring_layer[g] = k;
                if kids > 0 {
                    while k + 1 >= layers.len() {
                        layers.push(layers[layers.len() - 1].next_layer());
                        layer_load.push(0.0);
                    }
                    layer_load[k + 1] += kids as f32 * SLOT;
                }
                break;
            }
            k += 1;
        }
    }

    // 3. 每层切扇区：层的可用周长按占用者的份额切弧段，从正上方顺时针铺。占用者
    //    两种——本层成员组（成员弧段），和内一层有子节点的挂靠者（子节点弧段）。
    //    份额沿用装填时的算法，保证装填时承诺过的空间在角度上真拿得到。
    let mut member_sector: Vec<(f32, f32)> = vec![(0.0, 0.0); group_count];
    let mut child_sector: Vec<Option<(f32, f32)>> = vec![None; group_count];
    for (k, layer) in layers.iter().enumerate() {
        let mut occupants: Vec<(usize, f32)> = Vec::new();
        for &g in &order {
            let kids = kids_of(g);
            if ring_layer[g] == k {
                let member = members[g].len().max(1) as f32 * SLOT;
                let need = if kids == 0 {
                    member
                } else {
                    member.max(kids as f32 * SLOT * layer.perimeter() / layer.next_layer().perimeter())
                };
                occupants.push((g, need));
            } else if ring_layer[g] + 1 == k && kids > 0 {
                occupants.push((g, kids as f32 * SLOT));
            }
        }
        let total: f32 = occupants.iter().map(|(_, s)| *s).sum::<f32>().max(1e-6);
        let budget = layer.perimeter() * LAYER_BUDGET;
        let mut t = -std::f32::consts::FRAC_PI_2;
        for (g, s) in occupants {
            let t1 = layer.walk(t, budget * s / total);
            if ring_layer[g] == k {
                member_sector[g] = (t, t1);
            }
            if ring_layer[g] + 1 == k && kids_of(g) > 0 {
                child_sector[g] = Some((t, t1));
            }
            t = t1;
        }
    }

    // 4. 领域胶囊：胶囊层是所有组共享的一条椭圆轨道，而各应用层的扇区是各层
    //    独立切的——不同层两组的中点角可能撞在一起，照中点角放胶囊就会永远
    //    重叠。所以胶囊按「自己组成员扇区的中点角」排序后，沿轨道等弧长安放：
    //    顺序与组方向一致、相邻必隔一个最宽胶囊加间隙。装不下就把椭圆按比例
    //    放大，同时抬高内层下限（保持长短轴比例），层距不小于 ≈152。
    let mut pill = Ellipse { a: PILL_B * ASPECT, b: PILL_B };
    let widths: Vec<f32> = group_names.iter().map(|name| pill_width(name)).collect();
    let mut by_angle: Vec<usize> = (0..group_count).collect();
    by_angle.sort_by(|&x, &y| {
        let mx = (member_sector[x].0 + member_sector[x].1) / 2.0;
        let my = (member_sector[y].0 + member_sector[y].1) / 2.0;
        mx.total_cmp(&my)
    });
    let need = group_count as f32 * (widths.iter().copied().fold(0.0, f32::max) + PILL_GAP);
    while pill.perimeter() < need {
        pill = Ellipse { a: pill.a + 8.0 * ASPECT, b: pill.b + 8.0 };
    }
    let want = (pill.b + 153.0).max(INNER_B_MIN);
    if layers[0].b < want {
        let lift = want - layers[0].b;
        for layer in &mut layers {
            *layer = Ellipse { a: layer.a + lift * ASPECT, b: layer.b + lift };
        }
    }
    let pill_angle: Vec<f32> = (0..group_count)
        .map(|i| {
            let t0 = -std::f32::consts::FRAC_PI_2;
            pill.walk(t0, pill.perimeter() * (i as f32 + 0.5) / group_count as f32)
        })
        .collect();
    let pill_of = |g: usize| -> f32 {
        let slot = by_angle.iter().position(|&x| x == g).unwrap();
        pill_angle[slot]
    };

    // 5. 放置。所有点先在「中心为原点」的坐标系里摆，最后按内容包围盒整体平移。
    //    成员块在组的成员扇区里按弧长均分；一组装不下一层（清单大到组比内层还大）
    //    时整组外推一层——同组即兄弟（ADR 0101），兄弟必须同层，外推到头才接受
    //    同组拆层。
    let mut node_at: Vec<Point> = vec![Point::new(0.0, 0.0); node_count];
    let mut node_theta: Vec<f32> = vec![0.0; node_count];
    let mut node_layer: Vec<usize> = vec![0; node_count];
    for (g, m) in members.iter().enumerate() {
        let (t0, t1) = member_sector[g];
        let mut placed = 0;
        let mut k = ring_layer[g];
        while placed < m.len() {
            while k >= layers.len() {
                layers.push(layers[layers.len() - 1].next_layer());
                layer_load.push(0.0);
            }
            let layer = layers[k];
            let seg = layer.arc_len(t0, t1);
            let take = (((seg / SLOT).floor() as usize).max(1)).min(m.len() - placed);
            let per = seg / take as f32;
            for (i, &node) in m[placed..placed + take].iter().enumerate() {
                let t = layer.walk(t0, per * (i as f32 + 0.5));
                node_at[node] = layer.at(t);
                node_theta[node] = t;
                node_layer[node] = k;
            }
            placed += take;
            k += 1;
        }
    }

    // 挂靠节点与引用节点：挂在挂靠者外一层（层距沿两轴各长 LAYER_GAP），围着挂靠
    // 者的角度按弧长对称展开。相邻子节点的弧距不小于 SLOT；扇区装不下一整排时压
    // 等距居中——宁可排得密一点，也不铺进隔壁扇区（ADR 0116 决策 6）。独子也偏开
    // 一个身位——正后方会让父、子、连线三点一条直线。
    let mut attach_at: Vec<Option<Point>> = vec![None; node_count];
    let mut attach_layer: Vec<usize> = vec![0; node_count];
    let mut children_of: Vec<Vec<usize>> = vec![Vec::new(); apps.len()];
    for (i, target) in attached_to.iter().enumerate() {
        if let Some(p) = target {
            children_of[*p].push(i);
        }
    }
    // 引用节点和挂靠节点一起在挂靠者外一层展开，排在真挂靠的子节点之后。
    for (k, &(_, t)) in references.iter().enumerate() {
        children_of[t].push(apps.len() + k);
    }
    for (p, children) in children_of.iter().enumerate() {
        if children.is_empty() || attached_to[p].is_some() {
            continue; // 空挂靠者跳过；链式挂靠（挂靠者自己也被挂）当前数据没有。
        }
        let g = group_of[p];
        let layer = layers[ring_layer[g]].next_layer();
        let (t0, t1) = child_sector[g].unwrap_or(member_sector[g]);
        let seg = layer.arc_len(t0, t1);
        let n = children.len() as f32;
        let gap = if n > 1.0 && n * SLOT > seg { seg / (n + 1.0) } else { SLOT };
        let parent_s = layer.arc_len(t0, node_theta[p]);
        let span = gap * (n - 1.0);
        let (lo, hi) = (gap / 2.0, (seg - gap / 2.0).max(gap / 2.0));
        let first = if span > hi - lo {
            (lo + hi) / 2.0 - span / 2.0 // 装不下一整排：居中，两边均摊
        } else {
            (parent_s - span / 2.0).clamp(lo, hi)
        };
        for (k, &child) in children.iter().enumerate() {
            let t = layer.walk(t0, first + gap * k as f32);
            attach_at[child] = Some(layer.at(t));
            attach_layer[child] = ring_layer[g] + 1;
        }
    }

    // 6. 领域胶囊与应用分组。
    let groups: Vec<GroupNode> = group_names
        .iter()
        .enumerate()
        .map(|(g, name)| GroupNode {
            name: name.clone(),
            color: PALETTE[g % PALETTE.len()],
            at: pill.at(pill_of(g)),
            width: widths[g],
            apps: members[g].len(),
        })
        .collect();

    // 7. 画布：内容包围盒加边。上下不对称——图块的标题、状态点垂在图标中心下方，
    //    上缘只到图标顶——两边分别留 MARGIN。摆完再整体平移进画布。
    let mut min_x = f32::INFINITY;
    let mut max_x = f32::NEG_INFINITY;
    let mut min_y = f32::INFINITY;
    let mut max_y = f32::NEG_INFINITY;
    for p in node_at.iter().chain(attach_at.iter().flatten()).chain(groups.iter().map(|g| &g.at)) {
        min_x = min_x.min(p.x);
        max_x = max_x.max(p.x);
        min_y = min_y.min(p.y);
        max_y = max_y.max(p.y);
    }
    if !min_x.is_finite() {
        // 空清单：画布只剩胶囊层的内容感。
        min_x = -pill.a; max_x = pill.a; min_y = -pill.b; max_y = pill.b;
    }
    // 虎头在原点，也必须在画布里——内容可能全在一侧（比如只有一个应用）。
    min_x = min_x.min(-HUB_R);
    max_x = max_x.max(HUB_R);
    min_y = min_y.min(-HUB_R);
    max_y = max_y.max(HUB_R);
    min_x -= TILE_W / 2.0 + MARGIN;
    max_x += TILE_W / 2.0 + MARGIN;
    min_y -= ICON_CENTER_Y + MARGIN;
    max_y += TILE_H - ICON_CENTER_Y + MARGIN;
    let center = Point::new(-min_x, -min_y);
    for p in &mut node_at {
        *p = p.plus(center);
    }
    for at in attach_at.iter_mut().flatten() {
        *at = at.plus(center);
    }
    let mut groups: Vec<GroupNode> = groups.into_iter().map(|mut g| { g.at = g.at.plus(center); g }).collect();

    let mut nodes: Vec<AppNode> = apps
        .iter()
        .enumerate()
        .map(|(i, app)| AppNode {
            id: app.id.clone(),
            group: group_of[i],
            at: match attach_at[i] {
                Some(at) => at,
                None => node_at[i],
            },
            layer: if attached_to[i].is_some() { attach_layer[i] } else { node_layer[i] },
            reference: false,
        })
        .collect();
    nodes.extend(references.iter().enumerate().map(|(k, &(i, t))| AppNode {
        id: apps[i].id.clone(),
        group: group_of[t],
        at: attach_at[apps.len() + k].unwrap_or(node_at[t]),
        layer: attach_layer[apps.len() + k],
        reference: true,
    }));
    nodes.extend(group_refs.iter().enumerate().map(|(k, &(i, g))| AppNode {
        id: apps[i].id.clone(),
        group: g,
        at: node_at[group_ref_base + k],
        layer: node_layer[group_ref_base + k],
        reference: true,
    }));

    // 同心椭圆：胶囊层加每一条应用轨道，从内到外。
    let mut rings: Vec<(f32, f32)> = vec![(pill.a, pill.b)];
    rings.extend(layers.iter().map(|l| (l.a, l.b)));

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
    for (i, node) in nodes.iter().enumerate() {
        // 挂靠节点只画父应用来的挂靠线（ADR 0092），不画领域分支线——
        // 它的 group 沿用挂靠者，若不跳过会多出一条领域胶囊连过来的假分支。引用节点同理。
        if node.reference || attached_to[i].is_some() {
            continue;
        }
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
    for (k, &(_, t)) in references.iter().enumerate() {
        if let Some(at) = attach_at[apps.len() + k] {
            links.push(curved(LinkKind::Reference, groups[group_of[t]].color, node_at[t], at, center, 0.14, true));
        }
    }
    // 领域圈引用：从领域胶囊连过来，种类是引用，比分支线淡（ADR 0117）。
    for (k, &(_, g)) in group_refs.iter().enumerate() {
        let at = node_at[group_ref_base + k];
        links.push(straight(
            LinkKind::Reference,
            groups[g].color,
            groups[g].at.toward(at, PILL_H / 2.0 + 4.0),
            clip_to_tile(at, groups[g].at, TILE_PAD),
        ));
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

    MindMap { width: max_x - min_x, height: max_y - min_y, center, rings, groups, nodes, links }
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
            also_under: Vec::new(),
            also_in: Vec::new(),
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
        // 大组装不下内层时整组外推(兄弟同层,ADR 0101),而不是把后排兄弟拆到内层。
        assert!(
            map.rings.len() >= 3,
            "大组应外推一层轨道,实际只有胶囊层和一条应用层"
        );
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
        let node_of = |id: &str| map.nodes.iter().find(|n| n.id == id).unwrap();
        let (p, c) = (node_of("softcert").at, node_of("dsa").at);
        // 挂靠节点在挂靠者外一层:层序号差 1。
        assert_eq!(
            node_of("dsa").layer,
            node_of("softcert").layer + 1,
            "挂靠节点应在挂靠者外一层"
        );
        // 但不与挂靠者径向共线:独子也偏开一个身位,父、子、连线不排成一条直线。
        assert!(
            p.minus(c).length() > 1.0,
            "挂靠节点不应与挂靠者径向共线"
        );
        assert!(map.links.iter().any(|l| l.kind == LinkKind::Attach && l.arrow.is_some()));
        // 挂靠节点没有领域分支线:softcert 与 ghost 是普通成员(2 条),dsa 只有挂靠线。
        assert_eq!(
            map.links.iter().filter(|l| l.kind == LinkKind::Branch).count(),
            2,
            "挂靠节点不应有领域胶囊连来的分支线"
        );
        // ghost 的 parent 解析不到：作为普通节点进了领域圈。
        assert!(map.groups.iter().any(|g| g.name == "算法"));
        assert_clean(&map);
        let _ = softcert;
    }

    #[test]
    fn 挂靠节点的组名不生成空分组() {
        // 子课程的 group 与挂靠者不同：照登记的话内环会出现没有任何节点的胶囊。
        let hub = app("hub", Some("大类"), None, &[]);
        let mut sub = app("sub", Some("子课程组"), None, &[]);
        sub.parent = Some("hub".to_string());
        let map = layout(&[hub, sub]);
        assert_eq!(map.groups.len(), 1, "挂靠节点自带的组名不该留在领域圈上");
        assert_eq!(map.groups[0].name, "大类");
        assert_eq!(map.groups[0].apps, 1);
        // 领域归属仍沿用挂靠者：着色跟大类走。
        assert_eq!(map.nodes.iter().find(|n| n.id == "sub").unwrap().group, 0);
        assert_clean(&map);
    }

    #[test]
    fn 链式挂靠的孙节点回退普通布局() {
        let mut a = app("a", Some("甲"), None, &[]);
        let mut b = app("b", Some("甲"), None, &[]);
        let mut c = app("c", Some("甲"), None, &[]);
        b.parent = Some("a".to_string());
        c.parent = Some("b".to_string()); // 挂靠者自己也被挂：一层封顶，c 回普通布局
        let map = layout(&[a, b, c]);
        let c_node = map.nodes.iter().find(|n| n.id == "c").unwrap();
        // 回退后的 c 不在画布原点，且没有指向它的挂靠线。
        assert!(c_node.at.x > 0.0 && c_node.at.y > 0.0);
        assert!(!map.links.iter().any(|l| l.kind == LinkKind::Attach
            && (l.to == c_node.at || l.from == c_node.at)));
        assert!(map.links.iter().any(|l| l.kind == LinkKind::Attach)); // a→b 这条还在
        assert_clean(&map);
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
        let mut apps = discover(&repo);
        if apps.is_empty() {
            return; // 不在完整仓库里（例如单独打包的 crate）
        }
        // 与 GUI 排的是同一份：subjects 加 practice，去掉隐藏的（ADR 0093）。
        apps.extend(crate::manifest::discover_in(&repo.join("practice")));
        apps.retain(|app| !app.hidden);
        let map = layout(&apps);
        assert_eq!(map.nodes.iter().filter(|n| !n.reference).count(), apps.len());
        assert_clean(&map);
    }

    #[test]
    fn 领域圈引用当圈内成员排_无效领域忽略() {
        let a = app("a", Some("甲"), None, &[]);
        let b = app("b", Some("乙"), None, &[]);
        let mut c = app("c", Some("甲"), None, &[]);
        // 乙有效；甲是本体所在领域、丙不存在、乙重复一次——只留一个乙。
        c.also_in = ["乙", "甲", "丙", "乙"].iter().map(|s| s.to_string()).collect();
        let mut d = app("d", Some("甲"), None, &[]);
        d.parent = Some("a".to_string());
        // 挂靠节点的领域沿用挂靠者（甲），所以甲忽略；乙有效。
        d.also_in = vec!["甲".to_string(), "乙".to_string()];
        let map = layout(&[a, b, c, d]);

        let ids: Vec<_> = map.nodes.iter().map(|n| (n.id.as_str(), n.reference)).collect();
        assert_eq!(ids, [("a", false), ("b", false), ("c", false), ("d", false), ("c", true), ("d", true)]);
        let yi = map.groups.iter().position(|g| g.name == "乙").unwrap();
        assert!(map.nodes[4..].iter().all(|n| n.group == yi));
        assert_eq!(map.groups[yi].apps, 3, "两个引用节点算进乙圈的成员");
        // 引用节点与 b 同层（同一条椭圆轨道）。
        assert_eq!(map.nodes[4].layer, map.nodes[1].layer);
        // 领域胶囊连向引用节点的是引用线，不是分支线：分支线只有 a、b、c 三条。
        assert_eq!(map.links.iter().filter(|l| l.kind == LinkKind::Reference).count(), 2);
        assert_eq!(map.links.iter().filter(|l| l.kind == LinkKind::Branch).count(), 3);
        assert_clean(&map);
    }

    #[test]
    fn 引用挂靠给同一应用多一个图块_无效引用忽略() {
        let a = app("a", Some("甲"), None, &[]);
        let b = app("b", Some("乙"), None, &[]);
        let mut c = app("c", Some("甲"), None, &[]);
        c.parent = Some("a".to_string());
        // b 有效；a 与主挂靠重复、ghost 解析不到、c 指向自己、b 重复一次——都只留一个 b。
        c.also_under = ["b", "a", "ghost", "c", "b"].iter().map(|s| s.to_string()).collect();
        let mut d = app("d", Some("甲"), None, &[]);
        d.parent = Some("a".to_string());
        d.also_under = vec!["c".to_string()]; // c 自己是挂靠节点：深度一层，忽略
        let mut e = app("e", Some("甲"), None, &[]);
        e.also_under = vec!["b".to_string()]; // 没有主挂靠的普通成员也能被引用到别处
        let map = layout(&[a, b, c, d, e]);

        let ids: Vec<_> = map.nodes.iter().map(|n| (n.id.as_str(), n.reference)).collect();
        assert_eq!(ids, [("a", false), ("b", false), ("c", false), ("d", false), ("e", false), ("c", true), ("e", true)]);
        // 引用节点着挂靠者的色，连线是单独的引用种类且带箭头。
        assert!(map.nodes[5..].iter().all(|n| n.group == map.nodes[1].group));
        let refs: Vec<_> = map.links.iter().filter(|l| l.kind == LinkKind::Reference).collect();
        assert_eq!(refs.len(), 2);
        assert!(refs.iter().all(|l| l.arrow.is_some()));
        assert_eq!(map.links.iter().filter(|l| l.kind == LinkKind::Attach).count(), 2);
        // 本体 e 仍在自己的领域里有分支线；引用节点没有分支线。
        assert_eq!(map.links.iter().filter(|l| l.kind == LinkKind::Branch).count(), 3);
        assert_clean(&map);
    }
}
